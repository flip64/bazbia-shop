class SMSServiceError(Exception):
    """خطای عمومی سرویس پیامک."""


class SMSConfigurationError(SMSServiceError):
    """تنظیمات سرویس پیامک ناقص است."""


class SMSSendError(SMSServiceError):
    """ارسال پیامک ناموفق بوده است."""
