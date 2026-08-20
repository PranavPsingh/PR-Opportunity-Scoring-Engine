import json

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse

from apps.clients.models import Client
from apps.users.models import User


class ClientsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = HttpClient(enforce_csrf_checks=True)
        self.admin = User.objects.create_user(email="admin@example.com", name="Admin", password="Pass-123456!")
        self.admin.role = User.Role.ADMIN
        self.admin.is_staff = True
        self.admin.save()
        self.consultant = User.objects.create_user(email="consultant@example.com", name="Consultant", password="Pass-123456!")
        self.other_consultant = User.objects.create_user(email="other@example.com", name="Other", password="Pass-123456!")
        self.payload = {"company_name": "Northstar Health", "industry": "Healthcare", "location": "London", "website": "https://northstar.example.com", "description": "A growing health technology company.", "company_size": "51-200"}

    def csrf_headers(self) -> dict[str, str]:
        response = self.client.get(reverse("api:csrf"))
        return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def authenticate(self, user: User) -> None:
        self.client.force_login(user)

    def json_request(self, method: str, url: str, payload: dict | None = None):
        return getattr(self.client, method)(url, data=json.dumps(payload or {}), content_type="application/json", **self.csrf_headers())

    def test_authenticated_consultant_can_create_and_read_own_client(self) -> None:
        self.authenticate(self.consultant)
        response = self.json_request("post", reverse("api:clients"), self.payload)
        self.assertEqual(response.status_code, 201)
        client = Client.objects.get()
        self.assertEqual(client.created_by, self.consultant)
        self.assertEqual(response.json()["data"]["client"]["company_name"], self.payload["company_name"])
        self.assertEqual(self.client.get(reverse("api:clients")).json()["data"]["clients"][0]["id"], client.pk)

    def test_url_and_required_field_validation(self) -> None:
        self.authenticate(self.consultant)
        payload = {**self.payload, "website": "not-a-url", "industry": ""}
        response = self.json_request("post", reverse("api:clients"), payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")
        self.assertIn("website", response.json()["error"]["details"])
        self.assertIn("industry", response.json()["error"]["details"])

    def test_consultant_cannot_read_or_update_unassigned_client(self) -> None:
        client = Client.objects.create(created_by=self.other_consultant, **self.payload)
        self.authenticate(self.consultant)
        url = reverse("api:client-detail", args=[client.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.json_request("put", url, self.payload).status_code, 404)

    def test_admin_can_assign_consultant_and_consultant_can_then_access_client(self) -> None:
        self.authenticate(self.admin)
        response = self.json_request("post", reverse("api:clients"), {**self.payload, "authorized_consultant_ids": [self.consultant.pk]})
        self.assertEqual(response.status_code, 201)
        client_id = response.json()["data"]["client"]["id"]
        self.client.force_login(self.consultant)
        self.assertEqual(self.client.get(reverse("api:client-detail", args=[client_id])).status_code, 200)

    def test_admin_can_filter_and_delete_any_client(self) -> None:
        Client.objects.create(created_by=self.consultant, **self.payload)
        Client.objects.create(created_by=self.other_consultant, **{**self.payload, "company_name": "Beacon Finance", "industry": "Finance"})
        self.authenticate(self.admin)
        response = self.client.get(f"{reverse('api:clients')}?search=beacon&industry=Finance")
        self.assertEqual(len(response.json()["data"]["clients"]), 1)
        client_id = response.json()["data"]["clients"][0]["id"]
        self.assertEqual(self.json_request("delete", reverse("api:client-detail", args=[client_id])).status_code, 200)
        self.assertFalse(Client.objects.filter(pk=client_id).exists())
