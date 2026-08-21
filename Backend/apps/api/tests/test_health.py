from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_returns_successful_response(self) -> None:
        response = self.client.get(reverse("api:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["data"]["service"], "backend")

    def test_versioned_health_check_returns_successful_response(self) -> None:
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_cors_preflight_allows_authenticated_mutations(self) -> None:
        response = self.client.options(
            "/api/v1/opportunities/1/strengthening/1/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="PATCH",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken",
        )

        self.assertEqual(response.status_code, 204)
        self.assertIn("PATCH", response["Access-Control-Allow-Methods"])
        self.assertIn("X-CSRFToken", response["Access-Control-Allow-Headers"])
