from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from telegram_integration.services import TelegramAPIError, TelegramClient


@override_settings(TELEGRAM_BOT_TOKEN="test-token")
class TelegramClientTests(SimpleTestCase):
    @patch("telegram_integration.services.telegram_client.requests.post")
    def test_send_photo_returns_result(self, post):
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "ok": True,
            "result": {"message_id": 12},
        }
        post.return_value = response

        result = TelegramClient().send_photo(
            "@bazbia",
            "https://example.com/photo.jpg",
            "test",
            "https://bazbia.ir/product/test",
        )

        self.assertEqual(result["message_id"], 12)

    @patch("telegram_integration.services.telegram_client.requests.post")
    def test_api_error_is_raised(self, post):
        response = Mock()
        response.ok = False
        response.json.return_value = {
            "ok": False,
            "description": "not enough rights",
        }
        post.return_value = response

        with self.assertRaisesMessage(TelegramAPIError, "not enough rights"):
            TelegramClient().send_message("@bazbia", "test")
