import json

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore
from apps.users.models import User


class OpportunitiesApiTests(TestCase):
    def setUp(self) -> None:
        self.client = HttpClient(enforce_csrf_checks=True)
        self.admin = User.objects.create_user(email="admin@example.com", name="Admin", password="Pass-123456!", role=User.Role.ADMIN, is_staff=True)
        self.consultant = User.objects.create_user(email="consultant@example.com", name="Consultant", password="Pass-123456!")
        self.other = User.objects.create_user(email="other@example.com", name="Other", password="Pass-123456!")
        self.client_record = Client.objects.create(company_name="Northstar", industry="AI", location="Dubai", website="https://northstar.example.com", description="AI company", company_size="51-200", created_by=self.consultant)
        self.payload = {"client_id": self.client_record.pk, "title": "Series A funding", "description": "Raised funding.", "story_type": "Funding", "funding_amount": "5000000", "funding_stage": "Series A", "founder_available": True, "product_launched": True, "product_launch_date": "2026-08-01", "customer_count": 120, "revenue_information": "Profitable", "geographic_relevance": "UAE and Saudi Arabia", "target_audience": "Business press", "supporting_information": "Investor announcement", "client_briefing": "Original client email, preserved exactly.", "status": "draft"}

    def csrf_headers(self) -> dict[str, str]:
        response = self.client.get(reverse("api:csrf"))
        return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def request_json(self, method: str, url: str, payload: dict | None = None):
        return getattr(self.client, method)(url, data=json.dumps(payload or {}), content_type="application/json", **self.csrf_headers())

    def test_creation_retrieval_update_and_briefing_preservation(self) -> None:
        self.client.force_login(self.consultant)
        response = self.request_json("post", reverse("api:opportunities"), self.payload)
        self.assertEqual(response.status_code, 201)
        opportunity_id = response.json()["data"]["opportunity"]["id"]
        opportunity = Opportunity.objects.get(pk=opportunity_id)
        self.assertEqual(opportunity.client, self.client_record)
        self.assertEqual(opportunity.client_briefing, self.payload["client_briefing"])
        self.assertEqual(self.client.get(reverse("api:opportunity-detail", args=[opportunity_id])).status_code, 200)
        response = self.request_json("put", reverse("api:opportunity-detail", args=[opportunity_id]), {**self.payload, "title": "Updated funding"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Opportunity.objects.get(pk=opportunity_id).title, "Updated funding")
        self.assertEqual(self.request_json("delete", reverse("api:opportunity-detail", args=[opportunity_id])).status_code, 200)

    def test_client_filter_status_and_authorization(self) -> None:
        opportunity = Opportunity.objects.create(client=self.client_record, title="Launch", client_briefing="Brief", created_by=self.consultant, status=Opportunity.Status.READY_FOR_ANALYSIS)
        self.client.force_login(self.consultant)
        response = self.client.get(f"{reverse('api:opportunities')}?client_id={self.client_record.pk}")
        self.assertEqual(response.json()["data"]["opportunities"][0]["status"], Opportunity.Status.READY_FOR_ANALYSIS)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("api:opportunity-detail", args=[opportunity.pk])).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("api:opportunity-detail", args=[opportunity.pk])).status_code, 200)

    def test_validation_requires_client_title_and_briefing(self) -> None:
        self.client.force_login(self.consultant)
        response = self.request_json("post", reverse("api:opportunities"), {"client_id": self.client_record.pk, "title": "", "client_briefing": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["error"]["details"])
        self.assertIn("client_briefing", response.json()["error"]["details"])

    def test_dashboard_summary_aggregates_latest_scores_filters_and_sorts(self) -> None:
        high = Opportunity.objects.create(client=self.client_record, title="High story", client_briefing="Brief", created_by=self.consultant, status=Opportunity.Status.ANALYZED)
        low = Opportunity.objects.create(client=self.client_record, title="Draft story", client_briefing="Brief", created_by=self.consultant, status=Opportunity.Status.DRAFT)
        OpportunityScore.objects.create(opportunity=high, overall_score=88, potential="HIGH", newsworthiness_score=88, media_appeal_score=88, timeliness_score=88, credibility_score=88, audience_interest_score=88, scored_by=self.consultant)
        OpportunityScore.objects.create(opportunity=low, overall_score=22, potential="LOW", newsworthiness_score=22, media_appeal_score=22, timeliness_score=22, credibility_score=22, audience_interest_score=22, scored_by=self.consultant)
        self.client.force_login(self.consultant)

        response = self.client.get(reverse("api:dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        summary = response.json()["data"]["summary"]
        self.assertEqual(summary["total_opportunities"], 2)
        self.assertEqual(summary["potential_counts"], {"HIGH": 1, "MEDIUM": 0, "LOW": 1})
        self.assertEqual(summary["average_score"], 55.0)
        self.assertEqual(summary["requiring_attention"], 1)
        self.assertEqual(summary["top_opportunities"][0]["title"], "High story")
        self.assertEqual(len(summary["trends"]), 1)
        filtered = self.client.get(f"{reverse('api:dashboard-summary')}?potential=HIGH").json()["data"]["summary"]
        self.assertEqual(filtered["total_opportunities"], 1)
        self.assertEqual(filtered["top_opportunities"][0]["title"], "High story")

    def test_dashboard_summary_requires_authentication_and_supports_empty_history(self) -> None:
        self.assertEqual(self.client.get(reverse("api:dashboard-summary")).status_code, 401)
        self.client.force_login(self.consultant)
        summary = self.client.get(reverse("api:dashboard-summary")).json()["data"]["summary"]
        self.assertEqual(summary["total_opportunities"], 0)
        self.assertIsNone(summary["average_score"])
        self.assertEqual(summary["trends"], [])
