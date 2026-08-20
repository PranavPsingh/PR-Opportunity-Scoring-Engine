from collections.abc import Callable
from functools import wraps

from django.http import HttpRequest, JsonResponse

from services.api_responses import error


def api_login_required(view: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """Return a JSON 401 response rather than redirecting API callers to a login page."""

    @wraps(view)
    def wrapped_view(request: HttpRequest, *args, **kwargs) -> JsonResponse:
        if not request.user.is_authenticated:
            return error("authentication_required", "Authentication is required.", status=401)
        return view(request, *args, **kwargs)

    return wrapped_view


def api_admin_required(view: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """Restrict administrative APIs to users with the Pathos admin role."""

    @wraps(view)
    def wrapped_view(request: HttpRequest, *args, **kwargs) -> JsonResponse:
        if not request.user.is_authenticated:
            return error("authentication_required", "Authentication is required.", status=401)
        if request.user.role != "admin":
            return error("admin_required", "Administrator access is required.", status=403)
        return view(request, *args, **kwargs)

    return wrapped_view
