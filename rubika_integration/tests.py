from io import BytesIO
from unittest.mock import Mock, patch

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
