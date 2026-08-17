import logging
from typing import Any

import requests
from django.conf import settings

from .exceptions import (
    SMSConfigurationError,
    SMSSendError,
)


logger = logging.getLogger(__name__)


class SMSIRService:
    VERIFY_URL = "https://api.sms.ir/v1/send/verify"

    def __init__(self) -> None:
        self.api_key = settings.SMS_IR_API_KEY

        self.otp_template_id = (
            settings.SMS_IR_OTP_TEMPLATE_ID
        )

        self.otp_parameter = (
            settings.SMS_IR_OTP_PARAMETER
        )

        self.timeout = settings.SMS_REQUEST_TIMEOUT

        self._validate_settings()

    def _validate_settings(self) -> None:
        if not self.api_key:
            raise SMSConfigurationError(
                "مقدار SMS_IR_API_KEY تنظیم نشده است."
            )

    @staticmethod
    def normalize_mobile(phone: str) -> str:
        """
        تبدیل شماره موبایل به فرمت قابل قبول SMS.ir.
        """

        mobile = str(phone).strip()

        mobile = (
            mobile
            .replace(" ", "")
            .replace("-", "")
        )

        if mobile.startswith("+98"):
            return "0" + mobile[3:]

        if mobile.startswith("98"):
            return "0" + mobile[2:]

        if (
            mobile.startswith("9")
            and len(mobile) == 10
        ):
            return "0" + mobile

        return mobile

    def send_otp(
        self,
        phone: str,
        code: str,
    ) -> dict[str, Any]:
        return self.send_template(
            phone=phone,
            template_id=self.otp_template_id,
            parameters={
                self.otp_parameter: str(code),
            },
        )

    def send_template(
        self,
        *,
        phone: str,
        template_id: int,
        parameters: dict[str, object],
    ) -> dict[str, Any]:
        """
        ارسال قالب Verify با پارامترهای دلخواه SMS.ir.
        """

        if not template_id:
            raise SMSConfigurationError(
                "شناسه قالب پیامک تنظیم نشده است."
            )

        mobile = self.normalize_mobile(phone)

        payload = {
            "mobile": mobile,
            "templateId": int(template_id),
            "parameters": [
                {
                    "name": str(name),
                    "value": str(value),
                }
                for name, value
                in parameters.items()
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": self.api_key,
        }

        try:
            response = requests.post(
                self.VERIFY_URL,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

        except requests.Timeout as exc:
            logger.exception(
                "SMS.ir request timed out for mobile=%s",
                mobile,
            )

            raise SMSSendError(
                "زمان اتصال به سامانه پیامک "
                "به پایان رسید."
            ) from exc

        except requests.RequestException as exc:
            logger.exception(
                "SMS.ir connection error for mobile=%s",
                mobile,
            )

            raise SMSSendError(
                "ارتباط با سامانه پیامک برقرار نشد."
            ) from exc

        try:
            response_data = response.json()

        except ValueError:
            response_data = {
                "raw_response": response.text,
            }

        if not response.ok:
            logger.error(
                "SMS.ir send failed. "
                "mobile=%s status=%s response=%s",
                mobile,
                response.status_code,
                response_data,
            )

            raise SMSSendError(
                "ارسال پیامک با خطا مواجه شد."
            )

        logger.info(
            "SMS.ir template sent successfully. "
            "mobile=%s response=%s",
            mobile,
            response_data,
        )

        return response_data
