from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from bale_integration.services.bale_client import BaleAPIError, BaleClient
from bale_integration.services.daily_product import build_product_post


@override_settings(
    BALE_BOT_TOKEN="test-token",
    BALE_FRONTEND_URL="https://bazbia.ir",
    BALE_BACKEND_URL="https://backend.bazbia.ir",
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
