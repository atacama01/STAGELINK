"""
Service-to-service authentication for /api/internal/ endpoints (service.md
section 5). Offers & Applications calls these with a shared token; the token
is compared in constant time so the comparison itself leaks nothing.
"""

import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission

HEADER_NAME = "X-Service-Token"


class IsInternalService(BasePermission):
    """Allows the request only when the shared service token matches."""

    message = "Missing or invalid service token."

    def has_permission(self, request, view):
        expected = settings.INTERNAL_SERVICE_TOKEN
        if not expected:
            return False
        provided = request.headers.get(HEADER_NAME, "")
        return hmac.compare_digest(provided, expected)
