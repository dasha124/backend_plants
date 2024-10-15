from datetime import datetime, timezone

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

KEY = settings.JWT["SIGNING_KEY"]
ALGORITHM = settings.JWT["ALGORITHM"]
ACCESS_TOKEN_LIFETIME = settings.JWT["ACCESS_TOKEN_LIFETIME"]
REFRESH_TOKEN_LIFETIME = settings.JWT["REFRESH_TOKEN_LIFETIME"]


def create_access_token(user_id):
    # Create initial payload
    payload = {
        "token_type": "access",
        "exp": datetime.now(tz=timezone.utc) + ACCESS_TOKEN_LIFETIME,
        "iat": datetime.now(tz=timezone.utc),
    }
    # Add given arguments to payload
    payload["user_id"] = user_id
    # Create Token
    token = jwt.encode(payload, KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(user_id):
    payload = {
        "token_type": "refresh",
        "exp": datetime.now(tz=timezone.utc) + REFRESH_TOKEN_LIFETIME,
        "iat": datetime.now(tz=timezone.utc),
    }
    # Add given arguments to payload
    payload["user_id"] = user_id
    # Create token
    token = jwt.encode(payload, KEY, ALGORITHM)
    return token

def set_access_token_cookie(response, access_token):
    response.set_cookie('access_token', access_token, expires=ACCESS_TOKEN_LIFETIME, httponly=False)

def set_refresh_token_cookie(response, refresh_token):
    response.set_cookie('refresh_token', refresh_token, expires=REFRESH_TOKEN_LIFETIME, httponly=False)


def get_jwt_payload(token):
    if isinstance(token, str):
        token = token.encode('utf-8')

    payload = jwt.decode(token, KEY, algorithms=['HS256'])
    return payload


def get_access_token(request):
    token = request.COOKIES.get('access_token')
    if token is None:
        token = request.data.get('access_token')
    if token is None:
        authorization_header = request.headers.get("Authorization")
        if authorization_header and authorization_header.lower().startswith("bearer "):
            token = authorization_header[len("bearer "):]
        else:
            token = authorization_header
    return token

