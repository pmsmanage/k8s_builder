from rest_framework import serializers
import pandas as pd
import yaml
import math
import base64
import copy

DEPLOYMENT_TEMPLATE_PATH = r'k8s_excel/yaml_templates/deployment_template.yaml'
SERVICE_TEMPLATE_PATH = r'k8s_excel/yaml_templates/service_template.yaml'
CONFIGMAP_TEMPLATE_PATH = r'k8s_excel/yaml_templates/configmap_template.yaml'
CONFIGMAP_ELEMENT_TEMPLATE_PATH = r'k8s_excel/yaml_templates/configmap_element_template.yaml'
SECRET_TEMPLATE_PATH = r'k8s_excel/yaml_templates/secret_template.yaml'
SECRET_ELEMENT_TEMPLATE_PATH = r'k8s_excel/yaml_templates/secret_element_template.yaml'

with open(DEPLOYMENT_TEMPLATE_PATH) as file:
    DEPLOYMENT_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)

with open(SERVICE_TEMPLATE_PATH) as file:
    SERVICE_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)

with open(CONFIGMAP_TEMPLATE_PATH) as file:
    CONFIGMAP_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)

with open(CONFIGMAP_ELEMENT_TEMPLATE_PATH) as file:
    CONFIGMAP_ELEMENT_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)

with open(SECRET_TEMPLATE_PATH) as file:
    SECRET_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)

with open(SECRET_ELEMENT_TEMPLATE_PATH) as file:
    SECRET_ELEMENT_TEMPLATE = yaml.load(file, Loader=yaml.FullLoader)


class ExcelToK8sSerializer(serializers.Serializer):
    excel_file = serializers.FileField()

    def validate_excel_file(self, value):
        try:
            dataframe = pd.read_excel(value)
        except ValueError:
            raise serializers.ValidationError('file must be excel')
        except Exception as e:
            raise serializers.ValidationError(str(e))
        if 'name' not in dataframe or 'port' not in dataframe or 'replicas' not in dataframe:
            raise serializers.ValidationError("columns names aren't correct")
        return dataframe

    def process(self, dataframe):
        volumes = {}
        results_list=[]
        for index, row in dataframe.iterrows():
            try:
                if int(row['replicas']) < 0 or int(row['port']) < 0:
                    raise ValueError()
            except ValueError:
                raise serializers.ValidationError(f'Error in line {index + 1} number of replicas and port must be a positive int')
            name = row['name'].lower()
            if 'image' in row and not (isinstance(row['image'], float) and math.isnan(row['image'])):
                image = row['image']
            else:
                image = name
            dep_obj = self.deployment_yaml(name, image, int(row['replicas']), int(row['port']))
            results_list.append(dep_obj)
            if 'service' in row and not math.isnan(row['service']):
                results_list.append(self.service_yaml(name, int(row['service']), int(row['port'])))
            if 'env' in row and not (isinstance(row['env'], float) and math.isnan(row['env'])):
                if not isinstance(dep_obj, str):
                    __class__.env_yaml(dep_obj, row['env'], volumes)
        for item in volumes:
            results_list.append(volumes[item])
        return results_list

    @staticmethod
    def deployment_yaml(name, image, replicas, port):
        yaml_ob = copy.deepcopy(DEPLOYMENT_TEMPLATE)
        yaml_ob['metadata']['name'] = f"{name}-deployment"
        yaml_ob['metadata']['labels']['app'] = name
        yaml_ob['spec']['replicas'] = replicas
        yaml_ob['spec']['selector']['matchLabels']['app'] = name
        yaml_ob['spec']['template']['metadata']['labels']['app'] = name
        yaml_ob['spec']['template']['spec']['containers'][0]['name'] = name
        yaml_ob['spec']['template']['spec']['containers'][0]['image'] = image
        yaml_ob['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort'] = port

        return yaml_ob

    @staticmethod
    def service_yaml(name, port, target_port):
        yaml_ob = copy.deepcopy(SERVICE_TEMPLATE)
        yaml_ob['metadata']['name'] = f'{name}-service'
        yaml_ob['spec']['selector']['app'] = name
        yaml_ob['spec']['ports'][0]['port'] = port
        yaml_ob['spec']['ports'][0]['targetPort'] = target_port
        return yaml_ob

    @staticmethod
    def env_yaml(yaml_obj, env_string, volumes):
        def configmap_env(_env_name, _env_volume, _env_volume_key, _env_value):
            configmap_element_ob = copy.deepcopy(CONFIGMAP_ELEMENT_TEMPLATE)
            configmap_element_ob['name'] = _env_name
            configmap_element_ob['valueFrom']['configMapKeyRef']['name'] = _env_volume
            configmap_element_ob['valueFrom']['configMapKeyRef']['key'] = _env_volume_key
            if _env_volume not in volumes:
                configmap_ob = copy.deepcopy(CONFIGMAP_TEMPLATE)
                configmap_ob['data'].pop('placeholder', None)
                configmap_ob['metadata']['name'] = _env_volume
                configmap_ob['data'][_env_volume_key] = _env_value
                volumes[_env_volume] = configmap_ob
            else:
                if _env_value is not None or _env_volume_key not in volumes[_env_volume]['data']:
                    volumes[_env_volume]['data'][_env_volume_key] = _env_value
            return configmap_element_ob

        def secret_env(_env_name, _env_volume, _env_volume_key, _env_value):
            secret_element_ob = copy.deepcopy(SECRET_ELEMENT_TEMPLATE)
            secret_element_ob['name'] = _env_name
            secret_element_ob['valueFrom']['secretKeyRef']['name'] = _env_volume
            secret_element_ob['valueFrom']['secretKeyRef']['key'] = _env_volume_key
            if _env_volume not in volumes:
                secret_ob = copy.deepcopy(SECRET_TEMPLATE)
                secret_ob['data'].pop('placeholder', None)
                secret_ob['metadata']['name'] = _env_volume
                if _env_value is None:
                    secret_ob['data'][_env_volume_key] = _env_value
                else:
                    secret_ob['data'][_env_volume_key] = secret_encode(_env_value)
                volumes[_env_volume] = secret_ob
            else:
                if _env_value is not None:
                    volumes[_env_volume]['data'][_env_volume_key] = secret_encode(_env_value)
                elif _env_volume_key not in volumes[_env_volume]['data']:
                    volumes[_env_volume]['data'][_env_volume_key] = None
            return secret_element_ob

        def secret_encode(value):
            return str(base64.b64encode(value.encode("ascii")), 'utf-8')

        env_obj_list = yaml_obj['spec']['template']['spec']['containers'][0].get('env', [])
        env_string = env_string.replace(' ', '')
        env_string_list = env_string.split(',')
        for env_item in env_string_list:
            env_name = None
            env_volume = None
            env_volume_key = None
            env_value = None
            if env_item.find('=') == -1 or (env_item.find('=') > env_item.find(':') > 0):
                i = env_item.find(':')
                if i+1 == len(env_item):
                    raise serializers.ValidationError('invalid env structure')
                env_name = env_item[:i]
                env_item = env_item[i+1:]

                if env_item.find('=') > 0:
                    i = env_item.find('=')
                    if i + 1 == len(env_item):
                        raise serializers.ValidationError('invalid env structure')
                    env_value = env_item[i + 1:]
                    env_item = env_item[:i]

                i = env_item.find('.')
                if i == -1 or i+1 == len(env_item):
                    raise serializers.ValidationError('invalid env structure')
                env_volume = env_item[:i]
                env_volume_key = env_item[i + 1:]
            else:
                i = env_item.find('=')
                if i == -1:
                    raise serializers.ValidationError('invalid env structure')
                env_name = env_item[:i]
                env_value = env_item[i + 1:]

            if env_volume is not None:
                if 'configmap' in env_volume.lower():
                    env_obj_list.append(configmap_env(env_name, env_volume, env_volume_key, env_value))
                elif 'secret' in env_volume.lower():
                    env_obj_list.append(secret_env(env_name, env_volume, env_volume_key, env_value))
                else:
                    raise serializers.ValidationError('volume name must include one of the supported volume names')
            else:
                env_obj_list.append({'name': env_name, 'value': env_value})
        yaml_obj['spec']['template']['spec']['containers'][0]['env'] = env_obj_list
