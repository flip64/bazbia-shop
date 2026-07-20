# -*- coding: utf-8 -*-

import logging
import os
import re
import sys
import uuid

from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any


# شناسه اجرای فعلی
_current_run_id: ContextVar[str] = ContextVar(
    "current_run_id",
    default="-",
)


# اطلاعات حساسی که نباید داخل لاگ ذخیره شوند
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "secret",
    "cookie",
    "session",
    "sessionid",
}


def get_base_dir() -> Path:
    """
    مسیر ریشه پروژه را برمی‌گرداند.

    در صورت آماده بودن Django از BASE_DIR تنظیمات استفاده می‌کند.
    در غیر این صورت مسیر پروژه را از محل همین فایل پیدا می‌کند.
    """

    try:
        from django.conf import settings

        if settings.configured and hasattr(settings, "BASE_DIR"):
            return Path(settings.BASE_DIR)

    except Exception:
        pass

    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

APPLICATION_LOG_FILE = LOG_DIR / "application.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"


def generate_run_id(prefix: str = "run") -> str:
    """
    یک شناسه کوتاه برای هر اجرای عملیات تولید می‌کند.

    نمونه:
        supplier-4f8a21d3
    """

    unique_part = uuid.uuid4().hex[:8]

    return f"{prefix}-{unique_part}"


def set_run_id(run_id: str) -> None:
    """
    شناسه اجرای فعلی را تنظیم می‌کند.
    """

    _current_run_id.set(str(run_id))


def get_run_id() -> str:
    """
    شناسه اجرای فعلی را برمی‌گرداند.
    """

    return _current_run_id.get()


def clear_run_id() -> None:
    """
    شناسه اجرای فعلی را پاک می‌کند.
    """

    _current_run_id.set("-")


def _mask_sensitive_value(value: Any) -> Any:
    """
    مقادیر حساس را در دیکشنری، لیست و رشته مخفی می‌کند.
    """

    if isinstance(value, dict):
        cleaned_data = {}

        for key, item_value in value.items():
            normalized_key = str(key).lower()

            if normalized_key in SENSITIVE_KEYS:
                cleaned_data[key] = "***"
            else:
                cleaned_data[key] = _mask_sensitive_value(item_value)

        return cleaned_data

    if isinstance(value, list):
        return [
            _mask_sensitive_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            _mask_sensitive_value(item)
            for item in value
        )

    if isinstance(value, str):
        cleaned_value = value

        patterns = [
            r"(?i)(password\s*[=:]\s*)[^\s,]+",
            r"(?i)(token\s*[=:]\s*)[^\s,]+",
            r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,]+",
            r"(?i)(authorization\s*[=:]\s*)[^\s,]+",
            r"(?i)(cookie\s*[=:]\s*)[^\s,]+",
        ]

        for pattern in patterns:
            cleaned_value = re.sub(
                pattern,
                r"\1***",
                cleaned_value,
            )

        return cleaned_value

    return value


class RunIdFilter(logging.Filter):
    """
    فیلتر اضافه‌کردن run_id به رکورد لاگ.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = get_run_id()
        return True


class SensitiveDataFilter(logging.Filter):
    """
    اطلاعات حساس را قبل از ثبت لاگ مخفی می‌کند.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _mask_sensitive_value(record.msg)

        if record.args:
            record.args = _mask_sensitive_value(record.args)

        return True


class MaxLevelFilter(logging.Filter):
    """
    اجازه ثبت پیام‌ها تا سطح مشخص‌شده را می‌دهد.

    برای جلوگیری از نمایش دوباره خطاها در کنسول استفاده می‌شود.
    """

    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


def _get_formatter() -> logging.Formatter:
    """
    قالب استاندارد لاگ پروژه.
    """

    return logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "run_id=%(run_id)s | "
            "%(name)s | "
            "%(filename)s:%(lineno)d | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _add_common_filters(
    handler: logging.Handler,
) -> None:
    """
    فیلترهای مشترک را به handler اضافه می‌کند.
    """

    handler.addFilter(RunIdFilter())
    handler.addFilter(SensitiveDataFilter())


def _create_application_handler() -> TimedRotatingFileHandler:
    """
    فایل application.log را مدیریت می‌کند.

    هر شب فایل را می‌چرخاند و لاگ‌های ۳۰ روز گذشته را نگه می‌دارد.
    """

    handler = TimedRotatingFileHandler(
        filename=APPLICATION_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        delay=True,
    )

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(_get_formatter())

    _add_common_filters(handler)

    return handler


def _create_error_handler() -> TimedRotatingFileHandler:
    """
    فقط خطاهای ERROR و CRITICAL را در errors.log ثبت می‌کند.
    """

    handler = TimedRotatingFileHandler(
        filename=ERROR_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=60,
        encoding="utf-8",
        delay=True,
    )

    handler.setLevel(logging.ERROR)
    handler.setFormatter(_get_formatter())

    _add_common_filters(handler)

    return handler


def _create_console_handler() -> logging.StreamHandler:
    """
    پیام‌ها را در ترمینال نمایش می‌دهد.
    """

    handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(logging.INFO)
    handler.setFormatter(_get_formatter())

    _add_common_filters(handler)

    return handler


def configure_logging(
    level: int | str | None = None,
) -> None:
    """
    سیستم لاگ مرکزی پروژه را فقط یک‌بار تنظیم می‌کند.
    """

    root_logger = logging.getLogger()

    if getattr(root_logger, "_bazbia_logging_configured", False):
        return

    if level is None:
        level = os.getenv(
            "BAZBIA_LOG_LEVEL",
            "INFO",
        ).upper()

    root_logger.setLevel(level)

    application_handler = _create_application_handler()
    error_handler = _create_error_handler()
    console_handler = _create_console_handler()

    root_logger.addHandler(application_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    root_logger._bazbia_logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    لاگر مربوط به هر ماژول را برمی‌گرداند.

    استفاده:
        logger = get_logger(__name__)
    """

    configure_logging()

    return logging.getLogger(name)
