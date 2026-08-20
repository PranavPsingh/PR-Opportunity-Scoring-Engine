import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from apps.users.models import User
from services.api_responses import error
from services.api_responses import success
from services.health import get_health_status

from .authentication import api_admin_required, api_login_required


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """Expose a small, unauthenticated readiness endpoint for infrastructure."""
    return success(get_health_status())


def serialize_user(user: User) -> dict[str, str | int]:
    """Return the safe user DTO used by authentication endpoints."""
    return {"id": user.pk, "name": user.name, "email": user.email, "role": user.role}


def parse_json_body(request: HttpRequest) -> tuple[dict[str, object] | None, JsonResponse | None]:
    try:
        payload = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return None, error("invalid_json", "Request body must be valid JSON.")
    if not isinstance(payload, dict):
        return None, error("invalid_payload", "Request body must be a JSON object.")
    return payload, None


def required_string(payload: dict[str, object], field: str) -> str | None:
    value = payload.get(field)
    return value.strip() if isinstance(value, str) and value.strip() else None


def csrf_failure(request: HttpRequest, reason: str = "") -> JsonResponse:
    return error("csrf_failed", "CSRF verification failed. Refresh the page and try again.", status=403)


@ensure_csrf_cookie
@require_GET
def csrf(request: HttpRequest) -> JsonResponse:
    return success({"csrfToken": get_token(request)})


@require_POST
def register(request: HttpRequest) -> JsonResponse:
    payload, response = parse_json_body(request)
    if response:
        return response
    assert payload is not None

    name = required_string(payload, "name")
    email = required_string(payload, "email")
    password = required_string(payload, "password")
    field_errors: dict[str, list[str]] = {}
    if not name:
        field_errors["name"] = ["Name is required."]
    if not email:
        field_errors["email"] = ["Email is required."]
    if not password:
        field_errors["password"] = ["Password is required."]
    if field_errors:
        return error("validation_error", "Please correct the highlighted fields.", details=field_errors)

    if User.objects.filter(email__iexact=email).exists():
        return error("email_in_use", "An account with this email already exists.", status=409)

    candidate = User(email=email.lower(), name=name)
    try:
        candidate.full_clean(exclude=["password"])
        validate_password(password, candidate)
    except ValidationError as exc:
        return error("validation_error", "Please correct the highlighted fields.", details=exc.message_dict if hasattr(exc, "message_dict") else {"password": list(exc.messages)})
    user = User.objects.create_user(email=email, name=name, password=password)
    login(request, user)
    return success({"user": serialize_user(user)}, status=201)


@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    payload, response = parse_json_body(request)
    if response:
        return response
    assert payload is not None

    email = required_string(payload, "email")
    password = required_string(payload, "password")
    if not email or not password:
        return error("invalid_credentials", "Email and password are required.", status=400)

    user = authenticate(request, username=email.lower(), password=password)
    if user is None:
        return error("invalid_credentials", "Email or password is incorrect.", status=401)
    login(request, user)
    return success({"user": serialize_user(user)})


@require_POST
@api_login_required
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return success({"message": "You have been logged out."})


@require_GET
@api_login_required
def current_user(request: HttpRequest) -> JsonResponse:
    return success({"user": serialize_user(request.user)})


@require_GET
@api_login_required
def protected_example(request: HttpRequest) -> JsonResponse:
    """A protected route that future domain endpoints can use as a reference."""
    return success({"message": "Authenticated access granted."})


@require_GET
@api_admin_required
def users_list(request: HttpRequest) -> JsonResponse:
    users = User.objects.all()
    return success({"users": [serialize_user(user) for user in users]})


@require_POST
@api_admin_required
def change_user_role(request: HttpRequest, user_id: int) -> JsonResponse:
    if user_id == request.user.pk:
        return error("cannot_change_own_role", "You cannot change your own role.", status=400)

    payload, response = parse_json_body(request)
    if response:
        return response
    assert payload is not None
    role = required_string(payload, "role")
    if role not in User.Role.values:
        return error("validation_error", "Role must be consultant or admin.", details={"role": ["Choose a valid role."]})

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error("user_not_found", "User not found.", status=404)

    if user.role == User.Role.ADMIN and role == User.Role.CONSULTANT:
        other_active_admins = User.objects.filter(role=User.Role.ADMIN, is_active=True).exclude(pk=user.pk)
        if not other_active_admins.exists():
            return error("last_admin", "At least one active administrator must remain.", status=400)

    user.role = role
    user.is_staff = role == User.Role.ADMIN
    user.save(update_fields=["role", "is_staff", "updated_at"])
    return success({"user": serialize_user(user)})


@require_POST
@api_admin_required
def delete_user(request: HttpRequest, user_id: int) -> JsonResponse:
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return error("user_not_found", "User not found.", status=404)

    other_active_admins = User.objects.filter(role=User.Role.ADMIN, is_active=True).exclude(pk=user.pk)
    if user.role == User.Role.ADMIN and user.is_active and not other_active_admins.exists():
        return error("last_admin", "The last active administrator cannot be deleted.", status=400)
    if user.pk == request.user.pk and not other_active_admins.exists():
        return error("cannot_delete_own_last_admin", "You cannot delete your account without another active administrator.", status=400)

    user.delete()
    return success({"message": "User deleted."})
