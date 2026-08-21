import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from apps.clients.models import Client
from apps.extraction.models import ExtractionConfirmation, OpportunityExtraction
from apps.extraction.services import ExtractionError, FIELD_NAMES, apply_confirmed_values, get_provider, validate_extraction
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore
from apps.scoring.services import ScoringService
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


CLIENT_FIELDS = ("company_name", "industry", "location", "website", "description", "company_size")


def serialize_client(client: Client) -> dict[str, object]:
    return {
        "id": client.pk,
        "company_name": client.company_name,
        "industry": client.industry,
        "location": client.location,
        "website": client.website,
        "description": client.description,
        "company_size": client.company_size,
        "created_by": serialize_user(client.created_by) if client.created_by else None,
        "authorized_consultant_ids": list(client.authorized_consultants.values_list("id", flat=True)),
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }


def accessible_clients(request: HttpRequest):
    return accessible_clients_for_user(request.user)


def accessible_clients_for_user(user: User):
    clients = Client.objects.select_related("created_by").prefetch_related("authorized_consultants")
    if user.role == User.Role.ADMIN:
        return clients
    return clients.filter(created_by=user) | clients.filter(authorized_consultants=user)


def serialize_opportunity(opportunity: Opportunity) -> dict[str, object]:
    return {
        "id": opportunity.pk, "client_id": opportunity.client_id,
        "client_name": opportunity.client.company_name if hasattr(opportunity, "client") else None,
        "title": opportunity.title, "description": opportunity.description, "story_type": opportunity.story_type,
        "funding_amount": str(opportunity.funding_amount) if opportunity.funding_amount is not None else None,
        "funding_stage": opportunity.funding_stage, "founder_available": opportunity.founder_available,
        "product_launched": opportunity.product_launched,
        "product_launch_date": opportunity.product_launch_date.isoformat() if opportunity.product_launch_date else None,
        "customer_count": opportunity.customer_count, "revenue_information": opportunity.revenue_information,
        "geographic_relevance": opportunity.geographic_relevance, "target_audience": opportunity.target_audience,
        "supporting_information": opportunity.supporting_information, "client_briefing": opportunity.client_briefing,
        "status": opportunity.status, "created_by": serialize_user(opportunity.created_by) if opportunity.created_by else None,
        "created_at": opportunity.created_at.isoformat(), "updated_at": opportunity.updated_at.isoformat(),
    }


def serialize_extraction(extraction: OpportunityExtraction) -> dict[str, object]:
    confirmation = getattr(extraction, "confirmation", None)
    return {
        "id": extraction.pk, "opportunity_id": extraction.opportunity_id, "provider": extraction.provider,
        "model_identifier": extraction.model_identifier, "status": extraction.status,
        "fields": extraction.extracted_data, "created_at": extraction.created_at.isoformat(),
        "confirmation": None if confirmation is None else {
            "confirmed_by": serialize_user(confirmation.confirmed_by) if confirmation.confirmed_by else None,
            "decisions": confirmation.decisions, "confirmed_at": confirmation.confirmed_at.isoformat(),
        },
    }


def serialize_score(score: OpportunityScore) -> dict[str, object]:
    return {
        "id": score.pk, "opportunity_id": score.opportunity_id, "overall_score": score.overall_score,
        "potential": score.potential, "newsworthiness_score": score.newsworthiness_score,
        "media_appeal_score": score.media_appeal_score, "timeliness_score": score.timeliness_score,
        "credibility_score": score.credibility_score, "audience_interest_score": score.audience_interest_score,
        "scoring_version": score.scoring_version, "scored_at": score.scored_at.isoformat(),
        "scored_by": serialize_user(score.scored_by) if score.scored_by else None, "metadata": score.metadata,
    }


def accessible_opportunity(request: HttpRequest, opportunity_id: int) -> Opportunity | None:
    try:
        return Opportunity.objects.select_related("client", "created_by").filter(client__in=accessible_clients(request)).distinct().get(pk=opportunity_id)
    except Opportunity.DoesNotExist:
        return None


OPPORTUNITY_TEXT_FIELDS = ("description", "story_type", "funding_stage", "revenue_information", "geographic_relevance", "target_audience", "supporting_information")


def opportunity_from_payload(payload: dict[str, object], *, created_by: User, existing: Opportunity | None = None) -> tuple[Opportunity | None, JsonResponse | None]:
    field_errors: dict[str, list[str]] = {}
    client_id = payload.get("client_id")
    title = required_string(payload, "title")
    briefing = payload.get("client_briefing")
    if not isinstance(client_id, int): field_errors["client_id"] = ["A client is required."]
    if not title: field_errors["title"] = ["This field is required."]
    if not isinstance(briefing, str) or not briefing.strip(): field_errors["client_briefing"] = ["This field is required."]
    client = None
    if isinstance(client_id, int):
        try: client = accessible_clients_for_user(created_by).distinct().get(pk=client_id)
        except Client.DoesNotExist: field_errors["client_id"] = ["Client not found or not authorized."]
    status = payload.get("status", Opportunity.Status.DRAFT)
    if not isinstance(status, str) or status not in Opportunity.Status.values: field_errors["status"] = ["Choose a valid status."]
    values: dict[str, object] = {"title": title, "client_briefing": briefing, "status": status}
    for field in OPPORTUNITY_TEXT_FIELDS:
        value = payload.get(field, "")
        if not isinstance(value, str): field_errors[field] = ["Provide text."]
        else: values[field] = value
    for field in ("founder_available", "product_launched"):
        value = payload.get(field)
        if value is not None and not isinstance(value, bool): field_errors[field] = ["Provide true, false, or null."]
        else: values[field] = value
    for field in ("funding_amount", "customer_count", "product_launch_date"):
        value = payload.get(field)
        if value in (None, ""): values[field] = None
        else: values[field] = value
    if field_errors: return None, error("validation_error", "Please correct the highlighted fields.", details=field_errors)
    opportunity = existing or Opportunity(created_by=created_by)
    assert client is not None
    opportunity.client = client
    for field, value in values.items(): setattr(opportunity, field, value)
    try: opportunity.full_clean()
    except ValidationError as exc: return None, error("validation_error", "Please correct the highlighted fields.", details=exc.message_dict)
    return opportunity, None


@require_http_methods(["GET", "POST"])
@api_login_required
def opportunities(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        queryset = Opportunity.objects.select_related("client", "created_by").filter(client__in=accessible_clients(request)).distinct()
        client_id = request.GET.get("client_id")
        if client_id:
            if not client_id.isdigit(): return error("validation_error", "client_id must be an integer.", details={"client_id": ["Provide a valid client ID."]})
            queryset = queryset.filter(client_id=int(client_id))
        return success({"opportunities": [serialize_opportunity(item) for item in queryset]})
    payload, response = parse_json_body(request)
    if response: return response
    assert payload is not None
    opportunity, response = opportunity_from_payload(payload, created_by=request.user)
    if response: return response
    assert opportunity is not None
    opportunity.save()
    return success({"opportunity": serialize_opportunity(Opportunity.objects.select_related("client", "created_by").get(pk=opportunity.pk))}, status=201)


@require_http_methods(["GET", "PUT", "DELETE"])
@api_login_required
def opportunity_detail(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None: return error("opportunity_not_found", "Opportunity not found.", status=404)
    if request.method == "GET": return success({"opportunity": serialize_opportunity(opportunity)})
    if request.method == "DELETE": opportunity.delete(); return success({"message": "Opportunity deleted."})
    payload, response = parse_json_body(request)
    if response: return response
    assert payload is not None
    updated, response = opportunity_from_payload(payload, created_by=request.user, existing=opportunity)
    if response: return response
    assert updated is not None
    updated.save()
    return success({"opportunity": serialize_opportunity(Opportunity.objects.select_related("client", "created_by").get(pk=updated.pk))})


@require_POST
@api_login_required
def extract_opportunity_information(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None:
        return error("opportunity_not_found", "Opportunity not found.", status=404)
    if not opportunity.client_briefing.strip():
        return error("missing_briefing", "A client briefing is required before extraction.", status=400)
    try:
        result, model_identifier = get_provider().extract(opportunity.client_briefing)
        fields = validate_extraction(result, opportunity.client_briefing)
    except ExtractionError as exc:
        return error(exc.code, exc.message, status=504 if exc.code == "ai_provider_timeout" else 502)
    extraction = OpportunityExtraction.objects.create(opportunity=opportunity, provider="gemini", model_identifier=model_identifier, extracted_data=fields)
    return success({"extraction": serialize_extraction(extraction)}, status=201)


@require_GET
@api_login_required
def latest_opportunity_extraction(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None:
        return error("opportunity_not_found", "Opportunity not found.", status=404)
    extraction = OpportunityExtraction.objects.filter(opportunity=opportunity).select_related("confirmation__confirmed_by").first()
    return success({"extraction": serialize_extraction(extraction) if extraction else None})


@require_POST
@api_login_required
def confirm_opportunity_extraction(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None:
        return error("opportunity_not_found", "Opportunity not found.", status=404)
    payload, response = parse_json_body(request)
    if response: return response
    assert payload is not None
    extraction_id, decisions = payload.get("extraction_id"), payload.get("decisions")
    if not isinstance(extraction_id, int) or not isinstance(decisions, dict) or set(decisions) != set(FIELD_NAMES):
        return error("validation_error", "Provide decisions for every extracted field.", details={"decisions": ["All extraction fields are required."]})
    try:
        extraction = OpportunityExtraction.objects.get(pk=extraction_id, opportunity=opportunity)
    except OpportunityExtraction.DoesNotExist:
        return error("extraction_not_found", "Extraction result not found.", status=404)
    if ExtractionConfirmation.objects.filter(extraction=extraction).exists():
        return error("extraction_already_confirmed", "This extraction has already been confirmed.", status=409)
    stored_decisions: dict[str, dict[str, object]] = {}
    for field in FIELD_NAMES:
        decision = decisions[field]
        if not isinstance(decision, dict) or set(decision) != {"action", "value"} or decision["action"] not in {"accepted", "edited", "rejected"}:
            return error("validation_error", "Each decision must be accepted, edited, or rejected.", details={"decisions": [f"Invalid decision for {field}."]})
        source = extraction.extracted_data[field]
        if decision["action"] == "accepted":
            value = source["value"]
        elif decision["action"] == "rejected":
            value = None
        else:
            value = decision["value"]
            if value is None:
                return error("validation_error", "Edited values cannot be empty.", details={"decisions": [f"Provide an edited value for {field}."]})
        stored_decisions[field] = {"action": decision["action"], "value": value}
    apply_confirmed_values(opportunity, stored_decisions)
    confirmation = ExtractionConfirmation.objects.create(extraction=extraction, confirmed_by=request.user, decisions=stored_decisions)
    extraction = OpportunityExtraction.objects.select_related("confirmation__confirmed_by").get(pk=extraction.pk)
    return success({"extraction": serialize_extraction(extraction), "opportunity": serialize_opportunity(Opportunity.objects.select_related("client", "created_by").get(pk=opportunity.pk))})


@require_http_methods(["GET", "POST"])
@api_login_required
def opportunity_score(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    """Read the latest score or persist a new immutable score version."""
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None:
        return error("opportunity_not_found", "Opportunity not found.", status=404)
    if request.method == "GET":
        latest = OpportunityScore.objects.filter(opportunity=opportunity).select_related("scored_by").first()
        return success({"score": serialize_score(latest) if latest else None})
    result = ScoringService(opportunity).score()
    dimensions = result["dimensions"]
    score = OpportunityScore.objects.create(
        opportunity=opportunity, scored_by=request.user, overall_score=result["overall_score"], potential=result["potential"],
        newsworthiness_score=dimensions["newsworthiness"]["score"], media_appeal_score=dimensions["media_appeal"]["score"],
        timeliness_score=dimensions["timeliness"]["score"], credibility_score=dimensions["credibility"]["score"],
        audience_interest_score=dimensions["audience_interest"]["score"], scoring_version=result["scoring_version"], metadata=result,
    )
    return success({"score": serialize_score(score)}, status=201)


@require_GET
@api_login_required
def opportunity_score_history(request: HttpRequest, opportunity_id: int) -> JsonResponse:
    opportunity = accessible_opportunity(request, opportunity_id)
    if opportunity is None:
        return error("opportunity_not_found", "Opportunity not found.", status=404)
    scores = OpportunityScore.objects.filter(opportunity=opportunity).select_related("scored_by")
    return success({"scores": [serialize_score(score) for score in scores]})


def client_from_payload(payload: dict[str, object], *, created_by: User, existing: Client | None = None) -> tuple[Client | None, list[int] | None, JsonResponse | None]:
    field_errors: dict[str, list[str]] = {}
    values: dict[str, str] = {}
    for field in CLIENT_FIELDS:
        value = required_string(payload, field)
        if not value:
            field_errors[field] = ["This field is required."]
        else:
            values[field] = value
            if field == "website":
                try:
                    URLValidator()(value)
                except ValidationError:
                    field_errors[field] = ["Enter a valid URL."]

    consultant_ids = payload.get("authorized_consultant_ids")
    if consultant_ids is not None and (not isinstance(consultant_ids, list) or any(not isinstance(item, int) for item in consultant_ids)):
        field_errors["authorized_consultant_ids"] = ["Provide a list of consultant IDs."]
        consultant_ids = None
    if field_errors:
        return None, None, error("validation_error", "Please correct the highlighted fields.", details=field_errors)

    client = existing or Client(created_by=created_by)
    for field, value in values.items():
        setattr(client, field, value)
    try:
        client.full_clean()
    except ValidationError as exc:
        return None, None, error("validation_error", "Please correct the highlighted fields.", details=exc.message_dict)
    return client, consultant_ids, None


def authorized_consultants(ids: list[int]) -> tuple[object | None, JsonResponse | None]:
    consultants = User.objects.filter(pk__in=ids, role=User.Role.CONSULTANT)
    if consultants.count() != len(set(ids)):
        return None, error("validation_error", "Please correct the highlighted fields.", details={"authorized_consultant_ids": ["Each ID must identify a consultant."]})
    return consultants, None


@require_http_methods(["GET", "POST"])
@api_login_required
def clients(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        queryset = accessible_clients(request).distinct()
        for param, field in (("search", "company_name"), ("industry", "industry"), ("location", "location"), ("company_size", "company_size")):
            value = request.GET.get(param, "").strip()
            if value:
                lookup = "company_name__icontains" if param == "search" else f"{field}__iexact"
                queryset = queryset.filter(**{lookup: value})
        return success({"clients": [serialize_client(client) for client in queryset]})

    payload, response = parse_json_body(request)
    if response:
        return response
    assert payload is not None
    client, consultant_ids, response = client_from_payload(payload, created_by=request.user)
    if response:
        return response
    assert client is not None
    if consultant_ids is not None:
        if request.user.role != User.Role.ADMIN:
            return error("admin_required", "Administrator access is required to assign consultants.", status=403)
        consultants, response = authorized_consultants(consultant_ids)
        if response:
            return response
    client.save()
    if consultant_ids is not None:
        client.authorized_consultants.set(consultants)
    return success({"client": serialize_client(client)}, status=201)


@require_http_methods(["GET", "PUT", "DELETE"])
@api_login_required
def client_detail(request: HttpRequest, client_id: int) -> JsonResponse:
    try:
        client = accessible_clients(request).distinct().get(pk=client_id)
    except Client.DoesNotExist:
        return error("client_not_found", "Client not found.", status=404)

    if request.method == "GET":
        return success({"client": serialize_client(client)})
    if request.method == "DELETE":
        client.delete()
        return success({"message": "Client deleted."})

    payload, response = parse_json_body(request)
    if response:
        return response
    assert payload is not None
    updated_client, consultant_ids, response = client_from_payload(payload, created_by=request.user, existing=client)
    if response:
        return response
    assert updated_client is not None
    if consultant_ids is not None:
        if request.user.role != User.Role.ADMIN:
            return error("admin_required", "Administrator access is required to assign consultants.", status=403)
        consultants, response = authorized_consultants(consultant_ids)
        if response:
            return response
    updated_client.save()
    if consultant_ids is not None:
        updated_client.authorized_consultants.set(consultants)
    return success({"client": serialize_client(updated_client)})


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
