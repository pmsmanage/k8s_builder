import yaml
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import YamlLog
from .serializers import ExcelToK8sSerializer
import subprocess
from django.contrib.auth.models import User
import re


class ExcelToYamlView(APIView):
    def post(self, request):
        namespace = request.data.pop('namespace', [None])
        namespace = namespace[0]
        if namespace is not None and not re.fullmatch(r'^[a-z0-9]([a-z0-9\-]{,251}[a-z0-9])?', namespace):
            return Response({'error': 'invalid namespace'}, status=400)
        if namespace is None and 'default' not in [x.strip() for x in request.keycloak_namespace.split(',')]:
            return Response({'error': "user don't have permissions to change on the namespace"}, status=400)
        elif namespace is not None and namespace not in [x.strip() for x in request.keycloak_namespace.split(',')]:
            return Response({'error': "user don't have permissions to change on the namespace"}, status=400)
        serializer = ExcelToK8sSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.process(serializer.validated_data['excel_file'])

            with open(r"k8s_excel/data.yaml", 'w') as file:
                for i, obj in enumerate(result):
                    yaml.dump(obj, file, explicit_start=i > 0)
            command = ["kubectl", "apply", "-f", r"k8s_excel/data.yaml"]
            if namespace:
                command.append('-n')
                command.append(namespace)
            command_output = subprocess.run(command, capture_output=True, text=True)
            user, _ = User.objects.get_or_create(username=request.keycloak_username)
            if namespace is None:
                namespace = 'default'
            YamlLog.objects.create(input_data=serializer.validated_data['excel_file'].to_csv(index=False),
                                   yaml_objects=result,
                                   created_by=user,
                                   namespace=namespace,
                                   output=command_output)
            if command_output.returncode == 0:
                return Response({'output': command_output.stdout.splitlines(), 'yaml_file': result}, status=200)
            else:
                return Response({'error': {'details': 'error when applying the yaml file',
                                           'value': command_output.stderr.splitlines(),
                                           'yaml_file': result}}, status=400)
        return Response(data=serializer.errors, status=400)
