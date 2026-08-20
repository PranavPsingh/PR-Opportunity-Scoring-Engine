import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.users.models import User


class AuthenticationApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            email="consultant@example.com",
            name="Casey Consultant",
            password="A-secure-password-123!",
        )

    def csrf_headers(self) -> dict[str, str]:
        response = self.client.get(reverse("api:csrf"))
        self.assertEqual(response.status_code, 200)
        return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def post(self, url_name: str, payload: dict[str, str]):
        return self.client.post(
            reverse(f"api:{url_name}"),
            data=json.dumps(payload),
            content_type="application/json",
            **self.csrf_headers(),
        )

    def test_successful_registration_hashes_password_and_returns_safe_user(self) -> None:
        response = self.post(
            "register",
            {"name": "New Consultant", "email": "new@example.com", "password": "A-secure-password-123!"},
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.check_password("A-secure-password-123!"))
        self.assertNotEqual(user.password, "A-secure-password-123!")
        self.assertEqual(response.json()["data"]["user"]["role"], User.Role.CONSULTANT)
        self.assertNotIn("password", response.json()["data"]["user"])

    def test_successful_login_creates_session(self) -> None:
        response = self.post("login", {"email": self.user.email, "password": "A-secure-password-123!"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["user"]["name"], self.user.name)
        self.assertIn("sessionid", response.cookies)

    def test_invalid_credentials_are_rejected(self) -> None:
        response = self.post("login", {"email": self.user.email, "password": "wrong-password"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "invalid_credentials")

    def test_protected_endpoint_requires_authentication(self) -> None:
        response = self.client.get(reverse("api:current-user"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_authenticated_user_can_access_protected_endpoint(self) -> None:
        self.post("login", {"email": self.user.email, "password": "A-secure-password-123!"})
        response = self.client.get(reverse("api:current-user"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["user"]["email"], self.user.email)

    def test_logout_invalidates_session(self) -> None:
        self.post("login", {"email": self.user.email, "password": "A-secure-password-123!"})
        response = self.post("logout", {})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("api:current-user")).status_code, 401)

    def test_mutating_auth_routes_require_csrf_token(self) -> None:
        response = self.client.post(
            reverse("api:login"),
            data=json.dumps({"email": self.user.email, "password": "A-secure-password-123!"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
