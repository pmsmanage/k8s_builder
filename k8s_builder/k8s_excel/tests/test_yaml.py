import pandas as pd
from io import BytesIO
from django.urls import reverse
from .fixtures import auth_api
import pytest
from rest_framework import status
from openpyxl import Workbook
import yaml
from deepdiff import diff
import os
import ast

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def get_excel_file(data):
    df = pd.DataFrame(data)
    workbook = Workbook()
    sheet = workbook.active
    for index, row in df.iterrows():
        sheet.append(row.tolist())
    excel_data = BytesIO()
    workbook.save(excel_data)
    excel_data.seek(0)
    return excel_data


@pytest.mark.django_db
def test_excel_simple(auth_api):
    data = {'name': ['name', 'Mongo'], 'replicas': ['replicas', '1'], 'port': ['port', '80']}
    url = reverse('excel-yaml')
    response = auth_api.post(url, data={'namespace': 'django-test', 'excel_file': get_excel_file(data)})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_excel_invalid_port(auth_api):
    data = {'name': ['name', 'Mongo'], 'replicas': ['replicas', '1'], 'port': ['port', 'uu']}
    url = reverse('excel-yaml')
    response = auth_api.post(url, data={'namespace': 'django-test', 'excel_file': get_excel_file(data)})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_excel(auth_api):
    data = {'name': ['name', 'Mongo'],
            'replicas': ['replicas', '1'],
            'port': ['port', '27017'],
            'service': ['service', '27017'],
            'env': ['env', "MONGO_INITDB_ROOT_USERNAME:mongo-configmap.mongo-root-username=username,"
                           " MONGO_INITDB_ROOT_PASSWORD:mongo-secret.mongo-root-password=password,"
                           " MONGO_INITDB_ROOT_PASSWORD2=mongo-secret.mongo-root-password,"
                           " MONGO_INITDB_ROOT_USERNAME2=username"]}
    url = reverse('excel-yaml')
    response = auth_api.post(url, data={'namespace': 'django-test', 'excel_file': get_excel_file(data)})
    assert response.status_code == status.HTTP_200_OK

    with open(str(str(DIR_PATH)+r'\template_test_yaml1.yaml')) as file:
        template_obj = list(yaml.load_all(file, Loader=yaml.FullLoader))
    # comparing the result yaml with the template (they should be identical)
    assert not diff.DeepDiff(ast.literal_eval(response.content.decode("UTF-8"))['yaml_file'], template_obj, ignore_order=True)


@pytest.mark.django_db  # it shouldn't use db but if it failed and pass db may be used
def test_invalid_namespace(auth_api):
    data = {'name': ['name', 'Mongo'], 'replicas': ['replicas', '1'], 'port': ['port', '80']}
    url = reverse('excel-yaml')
    response = auth_api.post(url, data={'namespace': '_django-test', 'excel_file': get_excel_file(data)})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'invalid namespace' in response.content.decode("UTF-8")

    # not allowed namespace
    response = auth_api.post(url, data={'namespace': 'dev1', 'excel_file': get_excel_file(data)})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "user don't have permissions to change on the namespace" in response.content.decode("UTF-8")

