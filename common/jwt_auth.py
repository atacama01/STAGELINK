"""
Local JWT validation (service.md section 2).

Identity & Profiles issues tokens; this service only verifies them. Tokens are
validated with the shared secret (HS256) or the shared public key (RS256),
chosen by JWT_ALGORITHM. The exact claim names are a team decision
(project.md item 2); the defaults below are placeholders to confirm with
Identity & Profiles before Milestone 2.
"""

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


# Claim names, to be confirmed with Identity & Profiles.
CLAIM_USER_ID = "user_id"
CLAIM_ROLE = "role"

ROLES = ("STUDENT", "COMPANY", "SUPERVISOR", "UNIVERSITY_ADMIN", "PLATFORM_ADMIN")


class AuthenticatedUser:
    """Identity carried by a valid access token. Not a database user."""

    def __init__(self, user_id, role):
        self.id = user_id
        self.role = role

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.role}:{self.id}"


class JWTAuthentication(BaseAuthentication):
    """Validates the Bearer access token on every protected request."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise AuthenticationFailed("Malformed Authorization header.")
        return self._authenticate_token(parts[1]), None

    def _authenticate_token(self, token):
        key = self._verification_key()
        try:
            payload = jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Access token has expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid access token.")

        user_id = payload.get(CLAIM_USER_ID)
        role = payload.get(CLAIM_ROLE)
        if not user_id or role not in ROLES:
            raise AuthenticationFailed("Access token is missing required claims.")
        return AuthenticatedUser(user_id=str(user_id), role=role)

    @staticmethod
    def _verification_key():
        if settings.JWT_ALGORITHM == "HS256":
            if not settings.JWT_SECRET:
                raise AuthenticationFailed("JWT validation is not configured.")
            return settings.JWT_SECRET
        if settings.JWT_ALGORITHM == "RS256":
            if not settings.JWT_PUBLIC_KEY:
                raise AuthenticationFailed("JWT validation is not configured.")
            return settings.JWT_PUBLIC_KEY
        raise AuthenticationFailed("Unsupported JWT algorithm.")

    def authenticate_header(self, request):
        return self.keyword
