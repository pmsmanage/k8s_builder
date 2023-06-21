from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


# tests will fail if there was no user with the following username and password!
USERNAME = "test-user"
PASSWORD = '123'


def test_login():
    url = reverse('login')
    response = APIClient().post(url, data={'username': USERNAME, 'password': PASSWORD})
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.json()


def test_login_wrong_password():
    url = reverse('login')
    response = APIClient().post(url, data={'username': USERNAME, 'password': PASSWORD+'1'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_refresh_token_login():
    url = reverse('login')
    response = APIClient().post(url, data={'username': USERNAME, 'password': PASSWORD})
    assert response.status_code == status.HTTP_200_OK
    refresh_token = response.json()['refresh_token']
    url = reverse('refresh-token')
    response = APIClient().post(url, data={'refresh_token': refresh_token})
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.json()


def test_logout():
    url = reverse('login')
    response = APIClient().post(url, data={'username': USERNAME, 'password': PASSWORD})
    assert response.status_code == status.HTTP_200_OK

    url = reverse('logout')
    refresh_token = response.json()['refresh_token']
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.json()['access_token'])
    response = api_client.post(url, data={'refresh_token': refresh_token})
    assert response.status_code == status.HTTP_200_OK

    url = reverse('refresh-token')
    response = APIClient().post(url, data={'refresh_token': refresh_token})
    print(response.json())
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_access_without_login():
    url = reverse('excel-yaml')
    response = APIClient().post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

