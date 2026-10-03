import json
from io import BytesIO
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from PIL import Image

from rubika_integration.services import RubikaAPIError, RubikaClient


def api_response(data, status="OK"):
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"status": status, "data": data}
    return response


def jpeg_bytes():
    output = BytesIO()
    Image.new("RGB", (20, 10), "red").save(output, format="JPEG")
    return output.getvalue()


@override_settings(RUBIKA_BOT_TOKEN="test-token")
class RubikaClientTests(SimpleTestCase):
    @patch("rubika_integration.services.rubika_client.requests.post")
    def test_send_message_uses_official_v3_endpoint(self, post):
        post.return_value = api_response({"message_id": "12345"})

        result = RubikaClient().send_message("c0-channel", "test")

        self.assertEqual(result["message_id"], "12345")
        self.assertEqual(
            post.call_args.args[0],
            "https://botapi.rubika.ir/v3/test-token/sendMessage",
        )
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"chat_id": "c0-channel", "text": "test"},
        )

    @patch("rubika_integration.services.rubika_client.requests.get")
    @patch("rubika_integration.services.rubika_client.requests.post")
    def test_send_product_uploads_image_then_sends_file(self, post, get):
        image_response = Mock()
        image_response.ok = True
        image_response.status_code = 200
        image_response.content = jpeg_bytes()
        image_response.headers = {"Content-Type": "image/jpeg"}
        get.return_value = image_response
        post.side_effect = [
            api_response({"upload_url": "https://upload.rubika.test/file"}),
            api_response({"file_id": "file-1"}),
            api_response({"message_id": "message-1"}),
        ]

        result = RubikaClient().send_product(
            "c0-channel",
            "https://backend.bazbia.ir/media/product.jpg",
            "محصول آزمایشی",
            "https://bazbia.ir/product/test",
        )

        self.assertEqual(result["message_id"], "message-1")
        self.assertEqual(post.call_count, 3)
        self.assertEqual(
            post.call_args_list[0].args[0],
            "https://botapi.rubika.ir/v3/test-token/requestSendFile",
        )
        self.assertEqual(
            post.call_args_list[1].args[0],
            "https://upload.rubika.test/file",
        )
        filename, uploaded_content, content_type = post.call_args_list[1].kwargs[
            "files"
        ]["file"]
        self.assertEqual(filename, "product.jpg")
        self.assertEqual(content_type, "image/jpeg")
        self.assertTrue(uploaded_content.startswith(b"\xff\xd8"))
        self.assertEqual(
            post.call_args_list[2].kwargs["json"]["file_id"],
            "file-1",
        )
        self.assertIn(
            "https://bazbia.ir/product/test",
            post.call_args_list[2].kwargs["json"]["text"],
        )

    @patch("rubika_integration.services.rubika_client.requests.post")
    def test_api_error_is_raised(self, post):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {
            "status": "ERROR",
            "status_det": "INVALID_AUTH",
        }
        post.return_value = response

        with self.assertRaisesMessage(RubikaAPIError, "INVALID_AUTH"):
            RubikaClient().get_me()

    @patch("rubika_integration.services.rubika_client.requests.post")
    def test_status_is_used_when_api_omits_error_description(self, post):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {"status": "INVALID_ACCESS"}
        post.return_value = response

        with self.assertRaisesMessage(RubikaAPIError, "INVALID_ACCESS"):
            RubikaClient().get_me()

    @patch("rubika_integration.services.rubika_client.requests.post")
    def test_update_endpoint_uses_receive_update(self, post):
        post.return_value = api_response({})

        RubikaClient().update_endpoint(
            "https://backend.bazbia.ir/api/rubika/webhook/secret/"
        )

        self.assertEqual(
            post.call_args.args[0],
            "https://botapi.rubika.ir/v3/test-token/updateBotEndpoints",
        )
        self.assertEqual(post.call_args.kwargs["json"]["type"], "ReceiveUpdate")


@override_settings(
    RUBIKA_BOT_TOKEN="test-token",
    RUBIKA_WEBHOOK_SECRET="test-secret-long-enough-123",
    RUBIKA_ADMIN_USER_IDS=("u-admin",),
    RUBIKA_RANDOM_EXCLUDE_DAYS=30,
)
class RubikaWebhookTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def _post_update(self, update, secret="test-secret-long-enough-123"):
        return self.client.post(
            f"/api/rubika/webhook/{secret}/",
            data=json.dumps(update),
            content_type="application/json",
        )

    @staticmethod
    def _message_update(text, message_id="message-1", user_id="u-admin"):
        return {
            "type": "NewMessage",
            "chat_id": "b-private-chat",
            "new_message": {
                "message_id": message_id,
                "text": text,
                "sender_type": "User",
                "sender_id": user_id,
            },
        }

    @patch("rubika_integration.views.call_command")
    @patch("rubika_integration.views.RubikaClient")
    def test_random_command_runs_only_allowed_management_command(
        self,
        client_class,
        call_command_mock,
    ):
        response = self._post_update(self._message_update("/random"))

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_called_once()
        self.assertEqual(
            call_command_mock.call_args.args[0],
            "send_random_rubika_product",
        )
        self.assertEqual(call_command_mock.call_args.kwargs["exclude_days"], 30)
        client_class.return_value.send_message.assert_called_once()

    @patch("rubika_integration.views.call_command")
    @patch("rubika_integration.views.RubikaClient")
    def test_product_command_passes_numeric_product_id(
        self,
        client_class,
        call_command_mock,
    ):
        response = self._post_update(
            self._message_update("/product 4206", message_id="message-2")
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_called_once()
        self.assertEqual(call_command_mock.call_args.args[0], "send_rubika_product")
        self.assertEqual(call_command_mock.call_args.kwargs["product_id"], 4206)
        client_class.return_value.send_message.assert_called_once()

    @patch("rubika_integration.views.call_command")
    @patch("rubika_integration.views.RubikaClient")
    def test_unauthorized_user_cannot_run_command(
        self,
        client_class,
        call_command_mock,
    ):
        response = self._post_update(
            self._message_update(
                "/random",
                message_id="message-3",
                user_id="u-other",
            )
        )

        self.assertEqual(response.status_code, 200)
        call_command_mock.assert_not_called()
        client_class.return_value.send_message.assert_called_once_with(
            "b-private-chat",
            "⛔ دسترسی ندارید.\nشناسه کاربری شما: u-other",
        )

    @patch("rubika_integration.views.call_command")
    @patch("rubika_integration.views.RubikaClient")
    def test_duplicate_message_is_not_executed_twice(
        self,
        client_class,
        call_command_mock,
    ):
        update = self._message_update("/random", message_id="message-4")

        first = self._post_update(update)
        second = self._post_update(update)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.json(), {"status": "OK", "duplicate": True})
        self.assertEqual(call_command_mock.call_count, 1)
        client_class.return_value.send_message.assert_called_once()

    @patch("rubika_integration.views.call_command")
    def test_wrong_webhook_secret_is_rejected(self, call_command_mock):
        response = self._post_update(
            self._message_update("/random", message_id="message-5"),
            secret="wrong-secret",
        )

        self.assertEqual(response.status_code, 404)
        call_command_mock.assert_not_called()
