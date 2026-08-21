import json
from datetime import date, timedelta
from decimal import Decimal

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore
from apps.scoring.services import ScoringService
from apps.users.models import User


class ScoringServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="scorer@example.com", name="Scorer", password="Pass-123456!")
        client = Client.objects.create(company_name="NexaMind", industry="AI", location="Dubai", website="https://nexa.example", description="AI", company_size="11-50", created_by=user)
        self.opportunity = Opportunity.objects.create(client=client, created_by=user, title="NexaMind $5M Series A funding", story_type="Funding", funding_amount=Decimal("5000000"), funding_stage="Series A", founder_available=True, product_launched=True, product_launch_date=date.today(), customer_count=120, revenue_information="$4.2M ARR and 85% YoY growth", geographic_relevance="Dubai, UAE and GCC expansion", target_audience="Enterprise technology and business press", supporting_information="Investor confirmation, named customer testimonial, independent research report, official press release", client_briefing="Dubai AI startup launching this month; 35% reduction in manual processing. Founder available for interview.")

    def test_dimensions_are_explainable_and_deterministic(self):
        first = ScoringService(self.opportunity, today=date.today()).score()
        second = ScoringService(self.opportunity, today=date.today()).score()
        self.assertEqual(first, second)
        self.assertEqual(first["scoring_version"], "v1")
        self.assertGreater(first["dimensions"]["newsworthiness"]["score"], 0)
        self.assertTrue(first["dimensions"]["credibility"]["positive_factors"])

    def test_exact_weighted_calculation_and_thresholds(self):
        dimensions = {"newsworthiness": {"score": 80}, "media_appeal": {"score": 70}, "timeliness": {"score": 90}, "credibility": {"score": 60}, "audience_interest": {"score": 80}}
        service = ScoringService(self.opportunity)
        self.assertEqual(service.calculate_overall_score(dimensions), 77)
        self.assertEqual(service.potential_for(80), "HIGH")
        self.assertEqual(service.potential_for(79), "MEDIUM")
        self.assertEqual(service.potential_for(59), "LOW")

    def test_missing_information_is_not_treated_as_a_negative_fact(self):
        self.opportunity.funding_amount = None; self.opportunity.customer_count = None; self.opportunity.product_launch_date = None
        result = ScoringService(self.opportunity, today=date.today()).score()
        self.assertIn("funding_amount", result["dimensions"]["newsworthiness"]["missing_information"])
        self.assertIn("announcement_or_launch_date", result["dimensions"]["timeliness"]["missing_information"])

    def test_old_and_upcoming_dates_have_explicit_timeliness_signals(self):
        self.opportunity.product_launch_date = date.today() - timedelta(days=31)
        old = ScoringService(self.opportunity, today=date.today()).calculate_timeliness()
        self.assertTrue(any(item["impact"] < 0 for item in old["negative_factors"]))
        self.opportunity.product_launch_date = date.today() + timedelta(days=20)
        upcoming = ScoringService(self.opportunity, today=date.today()).calculate_timeliness()
        self.assertTrue(any("upcoming" in item["factor"].lower() for item in upcoming["positive_factors"]))


class ScoringApiTests(TestCase):
    def setUp(self):
        self.http = HttpClient(enforce_csrf_checks=True)
        self.owner = User.objects.create_user(email="owner@example.com", name="Owner", password="Pass-123456!")
        other = User.objects.create_user(email="other-score@example.com", name="Other", password="Pass-123456!")
        client = Client.objects.create(company_name="ScoreCo", industry="Technology", location="Dubai", website="https://score.example", description="Technology", company_size="11-50", created_by=self.owner)
        self.opportunity = Opportunity.objects.create(client=client, title="Funding", client_briefing="Brief", created_by=self.owner, funding_amount=Decimal("5000000"))
        self.other = other

    def headers(self):
        response = self.http.get(reverse("api:csrf")); return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def test_score_persists_history_and_requires_access(self):
        self.http.force_login(self.other)
        url = reverse("api:opportunity-score", args=[self.opportunity.pk])
        self.assertEqual(self.http.post(url, **self.headers()).status_code, 404)
        self.http.force_login(self.owner)
        one = self.http.post(url, **self.headers())
        two = self.http.post(url, **self.headers())
        self.assertEqual(one.status_code, 201); self.assertEqual(two.status_code, 201)
        self.assertEqual(OpportunityScore.objects.filter(opportunity=self.opportunity).count(), 2)
        history = self.http.get(reverse("api:opportunity-score-history", args=[self.opportunity.pk]))
        self.assertEqual(len(history.json()["data"]["scores"]), 2)
        self.assertEqual(one.json()["data"]["score"]["overall_score"], two.json()["data"]["score"]["overall_score"])
