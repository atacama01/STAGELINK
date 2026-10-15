"""
Uniform error shape (service.md section 9):

    {"error": {"code": "...", "message": "...", "fields": {...}}}
"""

from rest_framework.views import exception_handler

STATUS_CODES = {
    400: "invalid_input",
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    fields = {}
    message = ""

    if isinstance(detail, dict):
        message = _stringify(detail.pop("detail", "")) if "detail" in detail else ""
        fields = {key: _stringify(value) for key, value in detail.items()}
    elif isinstance(detail, list):
        message = _stringify(detail)

    if not message and fields:
        message = "Invalid input."

    response.data = {
        "error": {
            "code": STATUS_CODES.get(response.status_code, "error"),
            "message": message,
            "fields": fields,
        }
    }
    return response


def _stringify(value):
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)