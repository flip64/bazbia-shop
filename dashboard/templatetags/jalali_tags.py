import jdatetime

from django import template
from django.utils import timezone


register = template.Library()


@register.filter(name="jalali_date")
def jalali_date(value, date_format="%Y/%m/%d"):
    """
    تبدیل Date یا DateTime میلادی به تاریخ شمسی.

    استفاده:
    {{ order.created_at|jalali_date }}
    """

    if not value:
        return ""

    try:
        if hasattr(value, "hour"):
            value = timezone.localtime(value)

        jalali_value = jdatetime.datetime.fromgregorian(
            datetime=value
        )

        return jalali_value.strftime(date_format)

    except (TypeError, ValueError, AttributeError):
        return value


@register.filter(name="jalali_datetime")
def jalali_datetime(
    value,
    date_format="%Y/%m/%d - %H:%M",
):
    """
    تبدیل DateTime میلادی به تاریخ و ساعت شمسی.

    استفاده:
    {{ order.created_at|jalali_datetime }}
    """

    if not value:
        return ""

    try:
        value = timezone.localtime(value)

        jalali_value = jdatetime.datetime.fromgregorian(
            datetime=value
        )

        return jalali_value.strftime(date_format)

    except (TypeError, ValueError, AttributeError):
        return value
