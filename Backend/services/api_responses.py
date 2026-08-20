from typing import Any

from django.http import JsonResponse


def success(data: Any, *, status: int = 200) -> JsonResponse:
    """Return the standard successful API envelope."""
    return JsonResponse({"status": "ok", "data": data}, status=status)


def error(
    code: str,
    message: str,
    *,
    status: int = 400,
    details: dict[str, Any] | None = None,
) -> JsonResponse:
    """Return the standard error envelope for future API views."""
    error_body: dict[str, Any] = {"code": code, "message": message}
    if details:
        error_body["details"] = details
    return JsonResponse({"status": "error", "error": error_body}, status=status)
