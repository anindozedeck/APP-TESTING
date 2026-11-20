import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import Day20_exercise


class ReplyAppTests(unittest.TestCase):
    def setUp(self):
        Day20_exercise.app.config.update(TESTING=True)
        self.client = Day20_exercise.app.test_client()

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generate reply", response.data)

    def test_rejects_empty_complaint(self):
        response = self.client.post("/api/reply", json={"complaint": "  "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_rejects_oversized_complaint(self):
        response = self.client.post("/api/reply", json={"complaint": "x" * 4001})
        self.assertEqual(response.status_code, 400)

    def test_rejects_payload_over_http_limit_as_json(self):
        response = self.client.post(
            "/api/reply",
            json={"complaint": "x" * (16 * 1024)},
        )
        self.assertEqual(response.status_code, 413)
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


if __name__ == "__main__":
    unittest.main()
