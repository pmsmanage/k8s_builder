import pytest
from django.urls import reverse
from rest_framework.test import APIClient

USERNAME = "test-user"
PASSWORD = '123'


@pytest.fixture
def auth_api():
    url = reverse('login')
    api_client = APIClient()

    response = api_client.post(url, data={'username': USERNAME, 'password': PASSWORD})
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.json()['access_token'])
    return api_client
