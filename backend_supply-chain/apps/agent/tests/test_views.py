from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AgentEndpointTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="analyst", password="test-password")
        self.client.force_authenticate(self.user)

    @patch("apps.agent.views.explain_bottlenecks")
    def test_explain_endpoint_passes_supported_filters_and_refresh(self, explain):
        explain.return_value = {"source": "template", "explanation": None, "evidence": None}

        response = self.client.post(
            "/api/v1/agent/bottlenecks/explain/?refresh=true",
            {"date_min": "2026-01-01", "region": "Europe", "marche": "ignored"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        explain.assert_called_once_with(
            {"date_min": "2026-01-01", "region": "Europe"},
            force=True,
        )

    @patch("apps.agent.views.run_agent")
    def test_chat_endpoint_returns_agent_response(self, run_agent):
        run_agent.return_value = {"source": "llm", "answer": "Le taux est de 10 %.", "trace": []}

        response = self.client.post(
            "/api/v1/agent/chat/",
            {
                "question": "Quel est le taux de retard ?",
                "history": [{"role": "user", "content": "Bonjour"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["answer"], "Le taux est de 10 %.")
        run_agent.assert_called_once_with(
            [{"role": "user", "content": "Bonjour"}],
            "Quel est le taux de retard ?",
        )

    def test_chat_endpoint_validates_question(self):
        response = self.client.post("/api/v1/agent/chat/", {"question": ""}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("question", response.data)

    def test_agent_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)

        explain = self.client.post("/api/v1/agent/bottlenecks/explain/", {}, format="json")
        chat = self.client.post(
            "/api/v1/agent/chat/",
            {"question": "Quel est le taux de retard ?"},
            format="json",
        )

        self.assertEqual(explain.status_code, 401)
        self.assertEqual(chat.status_code, 401)
