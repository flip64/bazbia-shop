import hmac
import io
import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bale_integration.services.bale_client import BaleAPIError, BaleClient


logger = logging.getLogger(__name__)

RANDOM_CALLBACK = "command:send_random_bale_product"
ALLOWED_MANAGEMENT_COMMANDS = {
    "send_bale_product",
    "send_random_bale_product",
}
HELP_TEXT = (
    "کنترل ارسال محصول به کانال بله\n\n"
    "/random - اجرای send_random_bale_product\n"
    "/product 2163 - اجرای send_bale_product\n"
    "/id - نمایش شناسه کاربری بله"
)
RANDOM_KEYBOARD = {
    "inline_keyboard": [[
        {
            "text": "🎲 ارسال محصول تصادفی",
            "callback_data": RANDOM_CALLBACK,
        }
    ]]
}


def _is_admin(user_id):
    return str(user_id) in settings.BALE_ADMIN_USER_IDS


def _run_management_command(command_name, **options):
    """فقط یکی از دستورهای از قبل تعیین‌شده جنگو را اجرا می‌کند."""
    if command_name not in ALLOWED_MANAGEMENT_COMMANDS:
        raise CommandError("اجرای این management command مجاز نیست.")
    output = io.StringIO()
    call_command(
        command_name,
        stdout=output,
        stderr=output,
        no_color=True,
        **options,
    )
    return output.getvalue().strip() or "دستور با موفقیت اجرا شد."


def _send_result(client, chat_id, command_name, **options):
    try:
        result = _run_management_command(command_name, **options)
    except CommandError as exc:
        client.send_message(chat_id, f"❌ اجرای دستور ناموفق بود:\n{exc}")
        return
    except Exception:
        logger.exception(
            "اجرای دستور ربات بله ناموفق بود: %s",
            command_name,
        )
        client.send_message(
            chat_id,
            "❌ خطای داخلی هنگام اجرای دستور رخ داد.",
        )
        return

    client.send_message(chat_id, f"✅ {result[-3500:]}")


def _handle_message(client, message):
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None or user_id is None or not text:
        return

    command, *arguments = text.split()
    command = command.split("@", 1)[0].lower()

    if command == "/id":
        client.send_message(chat_id, f"شناسه کاربری شما: {user_id}")
        return

    if not _is_admin(user_id):
        client.send_message(
            chat_id,
            f"⛔ دسترسی ندارید.\nشناسه کاربری شما: {user_id}",
        )
        return

    if command in {"/start", "/help", "/panel"}:
        client.send_message(chat_id, HELP_TEXT, reply_markup=RANDOM_KEYBOARD)
        return

    if command in {"/random", "/send_random_bale_product"}:
        _send_result(
            client,
            chat_id,
            "send_random_bale_product",
            exclude_days=settings.BALE_RANDOM_EXCLUDE_DAYS,
        )
        return

    if command in {"/product", "/send_product", "/send_bale_product"}:
        if len(arguments) != 1 or not arguments[0].isdigit():
            client.send_message(chat_id, "فرمت درست: /product 2163")
            return
        _send_result(
            client,
            chat_id,
            "send_bale_product",
            product_id=int(arguments[0]),
        )
        return

    client.send_message(chat_id, HELP_TEXT, reply_markup=RANDOM_KEYBOARD)


def _handle_callback(client, callback_query):
    callback_id = callback_query.get("id")
    user_id = callback_query.get("from", {}).get("id")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    data = callback_query.get("data")
    if callback_id is None or user_id is None or chat_id is None:
        return

    if not _is_admin(user_id):
        client.answer_callback_query(callback_id, "دسترسی ندارید.")
        return

    if data != RANDOM_CALLBACK:
        client.answer_callback_query(callback_id, "دستور ناشناخته است.")
        return

    client.answer_callback_query(callback_id, "در حال اجرای دستور...")
    _send_result(
        client,
        chat_id,
        "send_random_bale_product",
        exclude_days=settings.BALE_RANDOM_EXCLUDE_DAYS,
    )


@csrf_exempt
@require_POST
def bale_webhook(request, secret):
    configured_secret = settings.BALE_WEBHOOK_SECRET
    if not configured_secret or not hmac.compare_digest(
        secret.encode(),
        configured_secret.encode(),
    ):
        return HttpResponseNotFound()

    try:
        update = json.loads(request.body)
    except (TypeError, ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    update_id = update.get("update_id")
    if update_id is not None:
        cache_key = f"bale-webhook-update:{update_id}"
        if not cache.add(cache_key, True, timeout=24 * 60 * 60):
            return JsonResponse({"ok": True, "duplicate": True})

    try:
        client = BaleClient()
        if "message" in update:
            _handle_message(client, update["message"])
        elif "callback_query" in update:
            _handle_callback(client, update["callback_query"])
    except BaleAPIError:
        logger.exception("پاسخ‌گویی ربات بله ناموفق بود.")
    except Exception:
        logger.exception("پردازش وب‌هوک بله ناموفق بود.")

    return JsonResponse({"ok": True})
