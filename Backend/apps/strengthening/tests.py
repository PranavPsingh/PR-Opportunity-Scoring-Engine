import json
from decimal import Decimal

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore
from apps.scoring.services import ScoringService

from .models import StoryStrengtheningAnalysis, StoryStrengtheningRecommendation


class StoryStrengtheningTests(TestCase):
    def setUp(self) -> None:
        self.http = HttpClient(enforce_csrf_checks=True)
        from apps.users.models import User

        self.user = User.objects.create_user(email="consultant@example.com", name="Consultant", password="Pass-123456!")
        self.other = User.objects.create_user(email="other@example.com", name="Other", password="Pass-123456!")
        self.client_record = Client.objects.create(
            company_name="Northstar", industry="AI", location="Dubai", website="https://northstar.example.com",
            description="AI company", company_size="51-200", created_by=self.user,
        )
        self.opportunity = Opportunity.objects.create(
            client=self.client_record, title="Series A funding", client_briefing="Dubai AI startup with 120 enterprise customers.",
            description="Raised funding for an AI product.", funding_amount=Decimal("5000000"), funding_stage="Series A",
            founder_available=True, product_launched=True, customer_count=120, target_audience="Enterprise buyers",
            created_by=self.user,
        )
        result = ScoringService(self.opportunity).score()
        self.score = OpportunityScore.objects.create(
            opportunity=self.opportunity, scored_by=self.user, overall_score=result["overall_score"], potential=result["potential"],
            newsworthiness_score=result["dimensions"]["newsworthiness"]["score"], media_appeal_score=result["dimensions"]["media_appeal"]["score"],
            timeliness_score=result["dimensions"]["timeliness"]["score"], credibility_score=result["dimensions"]["credibility"]["score"],
            audience_interest_score=result["dimensions"]["audience_interest"]["score"], metadata=result,
        )

    def csrf_headers(self) -> dict[str, str]:
        response = self.http.get(reverse("api:csrf"))
        return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def test_analysis_is_grounded_and_versioned(self) -> None:
        from .services import analyze_story

        analysis = analyze_story(self.opportunity, score=self.score, angles=[])
        recommendation = analysis.recommendations.filter(title="Add independent customer evidence").get()
        self.assertEqual(recommendation.title, "Add independent customer evidence")
        self.assertEqual(recommendation.affected_dimension, "Credibility")
        self.assertEqual(recommendation.severity, "HIGH")
        self.assertIn("Customer testimonial", recommendation.required_evidence)
        self.assertNotIn("Emirates", recommendation.recommendation)
        self.assertEqual(StoryStrengtheningAnalysis.objects.count(), 1)

        second = analyze_story(self.opportunity, score=self.score, angles=[])
        self.assertNotEqual(second.pk, analysis.pk)
        self.assertEqual(StoryStrengtheningAnalysis.objects.count(), 2)

    def test_api_requires_score_and_authorization(self) -> None:
        self.http.force_login(self.other)
        response = self.http.get(reverse("api:opportunity-strengthening", args=[self.opportunity.pk]))
        self.assertEqual(response.status_code, 404)

        self.http.force_login(self.user)
        response = self.http.post(
            reverse("api:opportunity-strengthening-analyze", args=[self.opportunity.pk]),
            data=json.dumps({}), content_type="application/json", **self.csrf_headers(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["analysis"]["progress"]["total"], 2)

    def test_status_update_and_progress(self) -> None:
        from .services import analyze_story

        analysis = analyze_story(self.opportunity, score=self.score, angles=[])
        recommendation = analysis.recommendations.first()
        self.http.force_login(self.user)
        response = self.http.patch(
            reverse("api:opportunity-strengthening-detail", args=[self.opportunity.pk, recommendation.pk]),
            data=json.dumps({"status": StoryStrengtheningRecommendation.Status.COMPLETED}),
            content_type="application/json", **self.csrf_headers(),
        )
        self.assertEqual(response.status_code, 200)
        recommendation.refresh_from_db()
        self.assertEqual(recommendation.status, StoryStrengtheningRecommendation.Status.COMPLETED)
        self.assertEqual(response.json()["data"]["recommendation"]["status"], "COMPLETED")

    def test_analysis_does_not_modify_score(self) -> None:
        before = self.score.metadata
        from .services import analyze_story

        analyze_story(self.opportunity, score=self.score, angles=[])
        self.score.refresh_from_db()
        self.assertEqual(self.score.metadata, before)
