from keycloak import KeycloakOpenID
from django.conf import settings
from keycloak.exceptions import KeycloakError
from django.http import JsonResponse
from rest_framework import status


class KeycloakMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.keycloak_openid = KeycloakOpenID(server_url=settings.KEYCLOAK_SERVER_URL,
                                              realm_name=settings.KEYCLOAK_REALM,
                                              client_id=settings.KEYCLOAK_CLIENT_ID,
                                              client_secret_key=settings.KEYCLOAK_CLIENT_SECRET)

    def __call__(self, request):
        if not (request.path.startswith('/login') or request.path.startswith('/admin')):
            token = self._get_access_token(request)
            if token is None:
                return JsonResponse(data={'error': 'login required'}, status=status.HTTP_401_UNAUTHORIZED)
            if token:
                try:
                    userinfo = self.keycloak_openid.userinfo(token=token)
                except KeycloakError as e:
                    return JsonResponse(data={'error': {'type': str(type(e))}}, status=403)
                except Exception as e:
                    return JsonResponse(data={'error': 'login error'}, status=403)
                request.keycloak_username = userinfo['preferred_username']
                request.keycloak_namespace = userinfo.get('namespace-allowed', 'default')
                print(userinfo)
        response = self.get_response(request)
        return response

    def _get_access_token(self, request):
        authorization_header = request.headers.get('Authorization')
        if authorization_header:
            token_type, _, access_token = authorization_header.partition(' ')
            if token_type.lower() == 'bearer':
                return access_token
        return None
