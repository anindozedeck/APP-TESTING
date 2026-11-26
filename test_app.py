import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import Day20_exercise


class ReplyAppTests(unittest.TestCase):
    def setUp(self):
        self.api_key_env = patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
        self.api_key_env.start()
        self.addCleanup(self.api_key_env.stop)
        self.network_mock = patch("Day20_exercise.urlopen")
        self.network_mock.start()
        self.addCleanup(self.network_mock.stop)
        Day20_exercise.app.config.update(TESTING=True)
        self.client = Day20_exercise.app.test_client()

    @staticmethod
    def provider_response(body):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = body
        return response

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generate reply", response.data)
        self.assertIn(b'id="reply-form"', response.data)
        self.assertIn(b'id="complaint"', response.data)
        self.assertIn(b'maxlength="4000"', response.data)
        self.assertIn(b'id="copy-button"', response.data)

    def test_rejects_empty_complaint(self):
        for complaint in ("", " ", "\t\n"):
            with self.subTest(complaint=repr(complaint)):
                response = self.client.post("/api/reply", json={"complaint": complaint})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_rejects_oversized_complaint(self):
        response = self.client.post("/api/reply", json={"complaint": "x" * 4001})
        self.assertEqual(response.status_code, 400)
        self.assertIn("4,000", response.get_json()["error"])

    def test_accepts_complaint_at_character_limit(self):
        draft = "Please share your order details."
        mocked_response = self.provider_response(
            json.dumps({"content": [{"type": "text", "text": draft}]}).encode("utf-8")
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), patch(
            "Day20_exercise.urlopen", return_value=mocked_response
        ) as mocked_urlopen:
            response = self.client.post("/api/reply", json={"complaint": "x" * 4000})

        self.assertEqual(response.status_code, 200)
        sent_body = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent_body["messages"][0]["content"], "x" * 4000)

    def test_rejects_non_json_and_malformed_json(self):
        non_json = self.client.post(
            "/api/reply",
            data='{"complaint":"A complaint"}',
            content_type="text/plain",
        )
        malformed_json = self.client.post(
            "/api/reply",
            data="{not valid JSON",
            content_type="application/json",
        )

        self.assertEqual(non_json.status_code, 415)
        self.assertIn("error", non_json.get_json())
        self.assertEqual(malformed_json.status_code, 400)
        self.assertIn("error", malformed_json.get_json())

    def test_rejects_non_object_payloads_and_invalid_complaint_types(self):
        invalid_payloads = (
            [],
            "complaint",
            {},
            {"complaint": None},
            {"complaint": 1},
            {"complaint": True},
            {"complaint": []},
            {"complaint": {}},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/reply", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

        null_payload = self.client.post(
            "/api/reply",
            data="null",
            content_type="application/json",
        )
        self.assertEqual(null_payload.status_code, 400)
        self.assertIn("error", null_payload.get_json())

    def test_rejects_payload_over_http_limit_as_json(self):
        response = self.client.post(
            "/api/reply",
            json={"complaint": "x" * (16 * 1024)},
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("error", response.get_json())

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""})
    @patch("Day20_exercise.urlopen")
    def test_reports_missing_api_key_without_calling_provider(self, mocked_urlopen):
        response = self.client.post("/api/reply", json={"complaint": "My delivery is late."})

        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.get_json()["error"])
        mocked_urlopen.assert_not_called()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.urlopen")
    def test_combines_only_nonempty_text_content_blocks(self, mocked_urlopen):
        mocked_urlopen.return_value = self.provider_response(
            json.dumps(
                {
                    "content": [
                        {"type": "tool_use", "id": "tool", "input": {}},
                        {"type": "text", "text": "  First sentence. "},
                        None,
                        {"type": "text", "text": "Second sentence.  "},
                        {"type": "text", "text": " "},
                        {"type": "text", "text": 12},
                    ]
                }
            ).encode("utf-8")
        )

        response = self.client.post("/api/reply", json={"complaint": "My order is late."})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"reply": "First sentence. Second sentence."})

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.urlopen")
    def test_returns_service_error_for_invalid_or_empty_provider_responses(self, mocked_urlopen):
        invalid_responses = (
            b"not JSON",
            b"\xff",
            json.dumps([]).encode("utf-8"),
            json.dumps({"content": None}).encode("utf-8"),
            json.dumps({"content": []}).encode("utf-8"),
            json.dumps({"content": [{"type": "text", "text": "  "}]}).encode("utf-8"),
        )
        for body in invalid_responses:
            with self.subTest(body=body):
                mocked_urlopen.return_value = self.provider_response(body)
                response = self.client.post(
                    "/api/reply",
                    json={"complaint": "My order is late."},
                )
                self.assertEqual(response.status_code, 503)
                self.assertIn("error", response.get_json())

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.time.sleep")
    @patch("Day20_exercise.urlopen")
    def test_retries_transient_network_errors(self, mocked_urlopen, mocked_sleep):
        provider_response = unittest.mock.MagicMock()
        provider_response.__enter__.return_value.read.return_value = json.dumps(
            {"content": [{"type": "text", "text": "We are sorry. Please share the relevant details."}]}
        ).encode("utf-8")
        mocked_urlopen.side_effect = [URLError("temporarily unavailable"), provider_response]

        response = self.client.post("/api/reply", json={"complaint": "My delivery is late."})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mocked_urlopen.call_count, 2)
        mocked_sleep.assert_called_once_with(0.5)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.time.sleep")
    @patch("Day20_exercise.urlopen")
    def test_retries_transient_http_errors(self, mocked_urlopen, mocked_sleep):
        provider_response = self.provider_response(
            json.dumps(
                {"content": [{"type": "text", "text": "Please share your order details."}]}
            ).encode("utf-8")
        )
        for status in (408, 429, 500):
            with self.subTest(status=status):
                mocked_urlopen.reset_mock()
                mocked_urlopen.side_effect = [
                    HTTPError(Day20_exercise.ANTHROPIC_API_URL, status, "Transient", {}, None),
                    provider_response,
                ]
                mocked_sleep.reset_mock()

                response = self.client.post(
                    "/api/reply",
                    json={"complaint": "My order is late."},
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(mocked_urlopen.call_count, 2)
                mocked_sleep.assert_called_once_with(0.5)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.time.sleep")
    @patch("Day20_exercise.urlopen", side_effect=URLError("temporarily unavailable"))
    def test_returns_service_error_after_all_network_retries(self, mocked_urlopen, mocked_sleep):
        response = self.client.post("/api/reply", json={"complaint": "My delivery is late."})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(mocked_urlopen.call_count, Day20_exercise.MAX_RETRIES)
        self.assertEqual(
            [call.args[0] for call in mocked_sleep.call_args_list],
            [0.5, 1.0],
        )

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.urlopen")
    def test_does_not_retry_permanent_http_error(self, mocked_urlopen):
        mocked_urlopen.side_effect = HTTPError(
            Day20_exercise.ANTHROPIC_API_URL,
            400,
            "Bad Request",
            {},
            None,
        )

        response = self.client.post("/api/reply", json={"complaint": "My delivery is late."})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(mocked_urlopen.call_count, 1)

    @patch.dict(
        os.environ,
        {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "   "},
    )
    @patch("Day20_exercise.urlopen")
    def test_blank_model_setting_falls_back_to_default(self, mocked_urlopen):
        provider_response = unittest.mock.MagicMock()
        provider_response.__enter__.return_value.read.return_value = json.dumps(
            {"content": [{"type": "text", "text": "Please share the booking details."}]}
        ).encode("utf-8")
        mocked_urlopen.return_value = provider_response

        response = self.client.post("/api/reply", json={"complaint": "The booking was wrong."})

        self.assertEqual(response.status_code, 200)
        request = mocked_urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], Day20_exercise.DEFAULT_MODEL)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.urlopen")
    def test_generates_reply_for_different_business_complaints(self, mocked_urlopen):
        complaints = [
            "I ordered a kettle from your shop last week and it arrived broken.",
            "My parcel was meant to arrive yesterday, but the courier never came.",
            "The Airbnb room was not clean when we checked in, and we had to wait outside.",
        ]
        drafts = [
            "We're sorry the kettle arrived damaged. Please share your order details so we can review this and advise on the next step.",
            "We apologize that your parcel did not arrive as expected. Please send your tracking number so we can look into it and update you.",
            "We're sorry the room was not ready for you. Please share your booking details so we can understand what happened and discuss the next step.",
        ]

        for complaint, draft in zip(complaints, drafts):
            provider_response = unittest.mock.MagicMock()
            provider_response.__enter__.return_value.read.return_value = json.dumps(
                {"content": [{"type": "text", "text": draft}]}
            ).encode("utf-8")
            mocked_urlopen.return_value = provider_response

            response = self.client.post("/api/reply", json={"complaint": complaint})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {"reply": draft})

        self.assertEqual(mocked_urlopen.call_count, 3)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("Day20_exercise.urlopen")
    def test_trims_whitespace_before_sending_complaint(self, mocked_urlopen):
        mocked_urlopen.return_value = self.provider_response(
            json.dumps(
                {"content": [{"type": "text", "text": "Please share your order details."}]}
            ).encode("utf-8")
        )

        response = self.client.post(
            "/api/reply",
            json={"complaint": "  My order is late.  "},
        )

        self.assertEqual(response.status_code, 200)
        sent_body = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent_body["messages"][0]["content"], "My order is late.")


if __name__ == "__main__":
    unittest.main()
