import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from bale_integration.services.bale_client import BaleAPIError, BaleClient
from products.services.social_product_post import build_product_post


@override_settings(
    BALE_BOT_TOKEN="test-token",
    BALE_FRONTEND_URL="https://bazbia.ir",
    BALE_BACKEND_URL="https://backend.bazbia.ir",
    SOCIAL_FRONTEND_URL="https://bazbia.ir",
    SOCIAL_BACKEND_URL="https://backend.bazbia.ir",
)
class BaleClientTests(SimpleTestCase):
    @patch("bale_integration.services.bale_client.requests.post")
    def test_send_message_returns_result(self, post):
        response = Mock()
        response.ok = True
        response.json.return_value = {
            "ok": True,
            "result": {"message_id": 12},
        }
        post.return_value = response

        result = BaleClient().send_message("@bazbia", "test")

        self.assertEqual(result["message_id"], 12)
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"chat_id": "@bazbia", "text": "test"},
        )

    @patch("bale_integration.services.bale_client.requests.post")
    def test_send_message_accepts_inline_keyboard(self, post):
        response = Mock()
        response.ok = True
        response.json.return_value = {"ok": True, "result": {"message_id": 13}}
        post.return_value = response
        keyboard = {"inline_keyboard": [[{"text": "ارسال", "callback_data": "run"}]]}

        BaleClient().send_message(123, "test", reply_markup=keyboard)

        self.assertEqual(post.call_args.kwargs["json"]["reply_markup"], keyboard)

    @patch("bale_integration.services.bale_client.requests.post")
    def test_api_error_is_raised(self, post):
        response = Mock()
        response.ok = False
        response.json.return_value = {
            "ok": False,
            "description": "not enough rights",
        }
        post.return_value = response

        with self.assertRaisesMessage(BaleAPIError, "not enough rights"):
            BaleClient().send_message("@bazbia", "test")

    def test_product_post_contains_price_and_url(self):
        product = SimpleNamespace(
            name="محصول آزمایشی",
            slug="test-product",
            description="<p>توضیحات محصول</p>",
        )
        variant = SimpleNamespace(
            price=100000,
            discount_price=90000,
        )
        image_file = SimpleNamespace(url="/media/product_images/test.jpg")
        image = SimpleNamespace(image=image_file, source_url=None)

        photo, caption, url = build_product_post(product, [variant], image)

        self.assertEqual(
            photo,
            "https://backend.bazbia.ir/media/product_images/test.jpg",
        )
        self.assertIn("90,000 تومان", caption)
        self.assertIn("دارای تخفیف", caption)
        self.assertEqual(url, "https://bazbia.ir/product/test-product")


@override_settings(
    BALE_BOT_TOKEN="test-token",
    BALE_WEBHOOK_SECRET="test-secret",
    BALE_ADMIN_USER_IDS=("1001",),
    BALE_RANDOM_EXCLUDE_DAYS=30,
)
class BaleWebhookTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def _post_update(self, update):
        return self.client.post(
            "/api/bale/webhook/test-secret/",
            data=json.dumps(update),
            content_type="application/json",
        )

    @patch("bale_integration.views.call_command")
    @patch("bale_integration.views.BaleClient")
    def test_random_command_only_calls_random_management_command(
        self,
        bale_client_class,
        call_command_mock,
    ):
        response = self._post_update(
            {
                "update_id": 101,
                "message": {
                    "text": "/random",
                    "chat": {"id": 2001},
                    "from": {"id": 1001},
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_called_once()
        self.assertEqual(call_command_mock.call_args.args[0], "send_random_bale_product")
        self.assertEqual(call_command_mock.call_args.kwargs["exclude_days"], 30)
        bale_client_class.return_value.send_message.assert_called_once()

    @patch("bale_integration.views.call_command")
    @patch("bale_integration.views.BaleClient")
    def test_product_command_passes_numeric_product_id(
        self,
        bale_client_class,
        call_command_mock,
    ):
        response = self._post_update(
            {
                "update_id": 102,
                "message": {
                    "text": "/product 2163",
                    "chat": {"id": 2001},
                    "from": {"id": 1001},
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_called_once()
        self.assertEqual(call_command_mock.call_args.args[0], "send_bale_product")
        self.assertEqual(call_command_mock.call_args.kwargs["product_id"], 2163)
        bale_client_class.return_value.send_message.assert_called_once()

    @patch("bale_integration.views.call_command")
    @patch("bale_integration.views.BaleClient")
    def test_unauthorized_user_cannot_run_command(
        self,
        bale_client_class,
        call_command_mock,
    ):
        response = self._post_update(
            {
                "update_id": 103,
                "message": {
                    "text": "/random",
                    "chat": {"id": 2002},
                    "from": {"id": 9999},
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_not_called()
        bale_client_class.return_value.send_message.assert_called_once_with(
            2002,
            "⛔ دسترسی ندارید.\nشناسه کاربری شما: 9999",
        )

    @patch("bale_integration.views.call_command")
    @patch("bale_integration.views.BaleClient")
    def test_random_button_calls_random_management_command(
        self,
        bale_client_class,
        call_command_mock,
    ):
        response = self._post_update(
            {
                "update_id": 104,
                "callback_query": {
                    "id": "callback-1",
                    "data": "command:send_random_bale_product",
                    "from": {"id": 1001},
                    "message": {"chat": {"id": 2001}},
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_called_once()
        self.assertEqual(call_command_mock.call_args.args[0], "send_random_bale_product")
        bale_client_class.return_value.answer_callback_query.assert_called_once_with(
            "callback-1",
            "در حال اجرای دستور...",
        )

    @patch("bale_integration.views.call_command")
    def test_wrong_webhook_secret_is_rejected(self, call_command_mock):
        response = self.client.post(
            "/api/bale/webhook/wrong-secret/",
            data=json.dumps({"update_id": 105}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        call_command_mock.assert_not_called()
