from keycloak import KeycloakOpenID
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response


class LoginView(APIView):
    def post(self, request):
        keycloak_openid = KeycloakOpenID(server_url=settings.KEYCLOAK_SERVER_URL,
                                         realm_name=settings.KEYCLOAK_REALM,
                                         client_id=settings.KEYCLOAK_CLIENT_ID,
                                         client_secret_key=settings.KEYCLOAK_CLIENT_SECRET)
        try:
            token = keycloak_openid.token(request.POST['username'], request.POST['password'])
            return Response(data=token, status=200)
        except Exception as e:
            return Response(data=str(e), status=400)


class RefreshTokenView(APIView):
    def post(self, request):
        keycloak_openid = KeycloakOpenID(server_url=settings.KEYCLOAK_SERVER_URL,
                                         realm_name=settings.KEYCLOAK_REALM,
                                         client_id=settings.KEYCLOAK_CLIENT_ID,
                                         client_secret_key=settings.KEYCLOAK_CLIENT_SECRET)
        try:
            token = keycloak_openid.refresh_token(request.POST['refresh_token'])

            return Response(data=token, status=200)
        except Exception as e:
            return Response(data=str(e), status=400)


class LogoutView(APIView):
    def post(self, request):
        keycloak_openid = KeycloakOpenID(server_url=settings.KEYCLOAK_SERVER_URL,
                                         realm_name=settings.KEYCLOAK_REALM,
                                         client_id=settings.KEYCLOAK_CLIENT_ID,
                                         client_secret_key=settings.KEYCLOAK_CLIENT_SECRET)
        keycloak_openid.logout(request.POST['refresh_token'])
        return Response(status=200)
