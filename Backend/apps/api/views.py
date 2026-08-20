from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from services.api_responses import success
from services.health import get_health_status


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Expose a small, unauthenticated readiness endpoint for infrastructure."""
    return success(get_health_status())
