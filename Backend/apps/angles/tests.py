from unittest.mock import patch

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse

from apps.angles.models import AngleGeneration, PRAngle
from apps.angles.services import AngleProviderRateLimited, GeminiAngleProvider, InvalidAngles, validate_angles
from apps.clients.models import Client
from apps.extraction.models import ExtractionConfirmation, OpportunityExtraction
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore
from apps.users.models import User


class FakeProvider:
    last_context = None

    def generate(self, context):
        self.last_context = context
        facts = context["allowed_facts"]
        return {"angles": [
            {"title": "Funding announcement", "summary": "A funding story grounded in the recorded round.", "potential_score": 90, "potential_level": "HIGH", "rationale": "The score indicates a timely business hook.", "target_audience": ["Business media"], "media_categories": ["Business"], "key_message": "The recorded funding event is a timely story hook.", "supporting_facts": [facts[0]], "required_evidence": ["Official funding confirmation"], "risks": ["Similar announcements may compete for attention."], "missing_information": []},
            {"title": "Founder perspective", "summary": "An interview-led perspective grounded in spokesperson availability.", "potential_score": 65, "potential_level": "MEDIUM", "rationale": "An available spokesperson can add a human perspective.", "target_audience": ["Technology media"], "media_categories": ["Technology"], "key_message": "An available spokesperson can discuss the recorded opportunity.", "supporting_facts": [facts[-1]], "required_evidence": ["A clear founder point of view"], "risks": ["The narrative needs a distinct point of view."], "missing_information": ["A named spokesperson"]},
        ]}, "test-model"


class FakeExtractionProvider:
    def extract(self, briefing):
        return {"fields": {"company_name": {"value": "Angle Co", "confidence": 1, "source_text": "Brief", "extraction_status": "extracted"}}}, "test-extraction-model"


class AngleApiTests(TestCase):
    def setUp(self):
        self.http = HttpClient(enforce_csrf_checks=True)
        self.owner = User.objects.create_user(email="angles@example.com", name="Angles", password="Pass-123456!")
        client = Client.objects.create(company_name="Angle Co", industry="AI", location="Dubai", website="https://angles.example", description="AI", company_size="11-50", created_by=self.owner)
        self.opportunity = Opportunity.objects.create(client=client, created_by=self.owner, title="Funding", client_briefing="Brief", funding_amount="5000000", founder_available=True)
        extraction = OpportunityExtraction.objects.create(opportunity=self.opportunity, provider="gemini", model_identifier="model", extracted_data={})
        ExtractionConfirmation.objects.create(extraction=extraction, confirmed_by=self.owner, decisions={"funding_amount": {"action": "accepted", "value": 5000000}, "founder_available_for_interview": {"action": "accepted", "value": True}})
        self.score = OpportunityScore.objects.create(opportunity=self.opportunity, overall_score=85, potential="HIGH", newsworthiness_score=90, media_appeal_score=80, timeliness_score=90, credibility_score=70, audience_interest_score=80, metadata={"dimensions": {}})

    def headers(self):
        response = self.http.get(reverse("api:csrf")); return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    @patch("apps.api.views.get_provider", return_value=FakeExtractionProvider())
    @patch("apps.api.views.get_angle_provider", return_value=FakeProvider())
    def test_generation_persists_versioned_grounded_angles(self, provider, extraction_provider):
        self.http.force_login(self.owner)
        url = reverse("api:opportunity-angles-generate", args=[self.opportunity.pk])
        first = self.http.post(url, **self.headers())
        second = self.http.post(url, **self.headers())
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 201)
        self.assertEqual(AngleGeneration.objects.count(), 2); self.assertEqual(PRAngle.objects.count(), 4)
        self.assertEqual(self.http.get(reverse("api:opportunity-angles", args=[self.opportunity.pk])).json()["data"]["angles"][0]["generation_id"], 2)
        self.assertEqual(OpportunityScore.objects.get(pk=self.score.pk).overall_score, 85)
        context = provider.return_value.last_context
        self.assertEqual(context["opportunity_score"]["overall_score"], 85)
        self.assertIn("score_explanation", context)

    @patch("apps.api.views.get_provider", return_value=FakeExtractionProvider())
    @patch("apps.api.views.get_angle_provider", return_value=FakeProvider())
    def test_manually_entered_structured_data_can_generate_without_extraction_confirmation(self, provider, extraction_provider):
        self.http.force_login(self.owner)
        ExtractionConfirmation.objects.all().delete()
        response = self.http.post(reverse("api:opportunity-angles-generate", args=[self.opportunity.pk]), **self.headers())
        self.assertEqual(response.status_code, 201)

    @patch("apps.api.views.get_provider", return_value=FakeExtractionProvider())
    @patch("apps.api.views.get_angle_provider", return_value=FakeProvider())
    def test_gemini_angles_do_not_require_a_deterministic_score(self, provider, extraction_provider):
        self.http.force_login(self.owner)
        OpportunityScore.objects.all().delete()
        response = self.http.post(reverse("api:opportunity-angles-generate", args=[self.opportunity.pk]), **self.headers())
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(AngleGeneration.objects.latest("id").score)


class AngleValidationTests(TestCase):
    def test_unsupported_fact_is_rejected(self):
        response = {"angles": [{"title": "One", "summary": "Summary", "potential_score": 80, "potential_level": "HIGH", "rationale": "Reason", "target_audience": [], "media_categories": [], "key_message": "Message", "supporting_facts": [{"fact": "customers: 1000", "source_field": "customer_count"}], "required_evidence": [], "risks": [], "missing_information": []}, {"title": "Two", "summary": "Summary", "potential_score": 60, "potential_level": "MEDIUM", "rationale": "Reason", "target_audience": [], "media_categories": [], "key_message": "Message", "supporting_facts": [{"fact": "customers: 1000", "source_field": "customer_count"}], "required_evidence": [], "risks": [], "missing_information": []}]}
        with self.assertRaises(InvalidAngles): validate_angles(response, [{"fact": "customer_count: 120", "source_field": "customer_count"}])

    def test_supporting_facts_with_only_whitespace_differences_are_canonicalized(self):
        response = {"angles": [{"title": "One", "summary": "Summary", "potential_score": 80, "potential_level": "HIGH", "rationale": "Reason", "target_audience": [], "media_categories": [], "key_message": "Message", "supporting_facts": [{"fact": "customer_count:   120", "source_field": "customer_count"}], "required_evidence": [], "risks": [], "missing_information": []}, {"title": "Two", "summary": "Summary", "potential_score": 60, "potential_level": "MEDIUM", "rationale": "Reason", "target_audience": [], "media_categories": [], "key_message": "Message", "supporting_facts": [{"fact": "customer_count: 120", "source_field": "customer_count"}], "required_evidence": [], "risks": [], "missing_information": []}]}
        cleaned = validate_angles(response, [{"fact": "customer_count: 120", "source_field": "customer_count"}])
        self.assertEqual(cleaned[0]["supporting_facts"][0]["fact"], "customer_count: 120")

    @patch("apps.angles.services.urlopen")
    def test_http_429_has_a_clear_rate_limit_error(self, request):
        from urllib.error import HTTPError
        request.side_effect = HTTPError("https://example.test", 429, "Too Many Requests", {}, None)
        with self.settings(GEMINI_API_KEY="test"):
            with self.assertRaises(AngleProviderRateLimited): GeminiAngleProvider().generate({})
