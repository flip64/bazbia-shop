import hmac
import io
import json

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.logging_config import get_logger
from rubika_integration.services import RubikaAPIError, RubikaClient


logger = get_logger(__name__)

ALLOWED_MANAGEMENT_COMMANDS = {
    "send_rubika_product",
    "send_random_rubika_product",
}
HELP_TEXT = (
    "کنترل ارسال محصول به کانال روبیکا\n\n"
    "/random - ارسال یک محصول تصادفی\n"
    "/product 2163 - ارسال محصول با شناسه مشخص\n"
    "/id - نمایش شناسه کاربری روبیکا"
)


def _is_admin(user_id):
    return str(user_id) in settings.RUBIKA_ADMIN_USER_IDS


def _run_management_command(command_name, **options):
    """فقط management commandهای از پیش تعیین‌شده را اجرا می‌کند."""
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


def _send_result(client, chat_id, user_id, command_name, **options):
    logger.info(
        "درخواست اجرای دستور از ربات روبیکا | command=%s | user_id=%s",
        command_name,
        user_id,
    )
    try:
        result = _run_management_command(command_name, **options)
    except CommandError as exc:
        logger.warning(
            "اجرای دستور ربات روبیکا ناموفق بود | command=%s | error=%s",
            command_name,
            exc,
        )
        client.send_message(chat_id, f"❌ اجرای دستور ناموفق بود:\n{exc}")
        return
    except Exception:
        logger.exception("اجرای دستور ربات روبیکا ناموفق بود | command=%s", command_name)
        client.send_message(chat_id, "❌ خطای داخلی هنگام اجرای دستور رخ داد.")
        return

    logger.info(
        "دستور ربات روبیکا اجرا شد | command=%s | user_id=%s",
        command_name,
        user_id,
    )
    client.send_message(chat_id, f"✅ {result[-3500:]}")


def _handle_new_message(client, update):
    chat_id = update.get("chat_id")
    message = update.get("new_message") or {}
    user_id = message.get("sender_id")
    text = (message.get("text") or "").strip()
    if not chat_id or not user_id or not text:
        return

    command, *arguments = text.split()
    command = command.split("@", 1)[0].lower()

    if command == "/id":
        client.send_message(chat_id, f"شناسه کاربری شما: {user_id}")
        return

    if not _is_admin(user_id):
        logger.warning("تلاش غیرمجاز در ربات روبیکا | user_id=%s", user_id)
        client.send_message(
            chat_id,
            f"⛔ دسترسی ندارید.\nشناسه کاربری شما: {user_id}",
        )
        return

    if command in {"/start", "/help", "/panel"}:
        client.send_message(chat_id, HELP_TEXT)
        return

    if command in {"/random", "/send_random_rubika_product"}:
        _send_result(
            client,
            chat_id,
            user_id,
            "send_random_rubika_product",
            exclude_days=settings.RUBIKA_RANDOM_EXCLUDE_DAYS,
        )
        return

    if command in {"/product", "/send_product", "/send_rubika_product"}:
        if len(arguments) != 1 or not arguments[0].isdigit():
            client.send_message(chat_id, "فرمت درست: /product 2163")
            return
        _send_result(
            client,
            chat_id,
            user_id,
            "send_rubika_product",
            product_id=int(arguments[0]),
        )
        return

    client.send_message(chat_id, HELP_TEXT)


def _deduplication_key(update):
    message = update.get("new_message") or update.get("updated_message") or {}
    unique_id = message.get("message_id") or update.get("removed_message_id")
    unique_id = unique_id or update.get("update_time")
    if unique_id is None:
        return None
    return f"rubika-webhook:{update.get('type', 'unknown')}:{update.get('chat_id')}:{unique_id}"


@csrf_exempt
@require_POST
def rubika_webhook(request, secret):
    configured_secret = settings.RUBIKA_WEBHOOK_SECRET
    if not configured_secret or not hmac.compare_digest(
        secret.encode(),
        configured_secret.encode(),
    ):
        return HttpResponseNotFound()

    try:
        payload = json.loads(request.body)
    except (TypeError, ValueError, UnicodeDecodeError):
        return JsonResponse({"status": "ERROR", "error": "invalid json"}, status=400)

    update = payload.get("update", payload) if isinstance(payload, dict) else {}
    cache_key = _deduplication_key(update)
    if cache_key and not cache.add(cache_key, True, timeout=24 * 60 * 60):
        return JsonResponse({"status": "OK", "duplicate": True})

    try:
        if update.get("type") == "NewMessage":
            _handle_new_message(RubikaClient(), update)
    except RubikaAPIError:
        logger.exception("پاسخ‌گویی ربات روبیکا ناموفق بود.")
    except Exception:
        logger.exception("پردازش وب‌هوک روبیکا ناموفق بود.")

    return JsonResponse({"status": "OK"})
