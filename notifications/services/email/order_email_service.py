import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def format_price(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value or 0)


def get_customer_info(order):
    user = order.user

    full_name = (
        user.get_full_name().strip()
        if hasattr(user, "get_full_name")
        else ""
    )

    if not full_name:
        full_name = getattr(user, "username", "") or "-"

    phone = "-"

    try:
        customer = user.customer_profile
        phone = customer.phone or "-"
    except Exception:
        pass

    return full_name, phone


def get_address_data(order):
    snapshot = order.shipping_address_snapshot or {}

    recipient_name = snapshot.get("recipient_name", "")
    recipient_phone = snapshot.get("recipient_phone", "")
    province = snapshot.get("province", "")
    city = snapshot.get("city", "")
    address = snapshot.get("address", "")
    postal_code = snapshot.get("postal_code", "")

    if not snapshot and order.shipping_address:
        obj = order.shipping_address

        recipient_name = obj.recipient_name
        recipient_phone = obj.recipient_phone
        province = obj.province
        city = obj.city
        address = obj.address
        postal_code = obj.postal_code

    address_parts = [
        province,
        city,
        address,
    ]

    full_address = "، ".join(
        part for part in address_parts if part
    )

    return {
        "recipient_name": recipient_name or "-",
        "recipient_phone": recipient_phone or "-",
        "address": full_address or "-",
        "postal_code": postal_code or "-",
    }


def send_paid_order_email(order_id, payment_id):
    """
    ارسال ایمیل اطلاع‌رسانی به مدیر فروشگاه
    فقط پس از پرداخت موفق سفارش.
    """

    try:
        from orders.models import Order
        from payments.models import Payment

        order = (
            Order.objects
            .select_related(
                "user",
                "shipping_address",
            )
            .prefetch_related(
                "items__variant__product",
                "items__variant__attributes__attribute",
            )
            .get(pk=order_id)
        )

        payment = Payment.objects.get(
            pk=payment_id
        )

        if payment.status != Payment.Status.SUCCESSFUL:
            logger.warning(
                "Paid order email skipped because payment "
                "is not successful. payment_id=%s",
                payment_id,
            )
            return False

        if order.status != Order.STATUS_PAID:
            logger.warning(
                "Paid order email skipped because order "
                "is not paid. order_id=%s",
                order_id,
            )
            return False

        customer_name, customer_phone = (
            get_customer_info(order)
        )

        address_data = get_address_data(order)

        item_rows = []
        text_items = []

        for item in order.items.all():
            variant = item.variant

            product_name = (
                variant.product.name
                if variant and variant.product
                else "-"
            )

            attributes = []

            if variant:
                for attr_value in variant.attributes.all():
                    attributes.append(
                        f"{attr_value.attribute.name}: "
                        f"{attr_value.value}"
                    )

            attribute_text = (
                " - " + "، ".join(attributes)
                if attributes
                else ""
            )

            item_total = item.price * item.quantity

            item_rows.append(
                f"""
                <tr>
                    <td style="padding:10px;border:1px solid #ddd;">
                        {product_name}{attribute_text}
                    </td>

                    <td style="padding:10px;border:1px solid #ddd;text-align:center;">
                        {item.quantity}
                    </td>

                    <td style="padding:10px;border:1px solid #ddd;text-align:center;">
                        {format_price(item.price)}
                    </td>

                    <td style="padding:10px;border:1px solid #ddd;text-align:center;">
                        {format_price(item_total)}
                    </td>
                </tr>
                """
            )

            text_items.append(
                f"- {product_name}{attribute_text} "
                f"× {item.quantity} = "
                f"{format_price(item_total)} تومان"
            )

        paid_at = payment.paid_at

        if paid_at:
            paid_at = timezone.localtime(
                paid_at
            ).strftime("%Y/%m/%d - %H:%M")
        else:
            paid_at = "-"

        admin_order_url = (
            f"https://backend.bazbia.ir/"
            f"admin/orders/order/{order.id}/change/"
        )

        subject = (
            f"✅ سفارش #{order.id} با موفقیت پرداخت شد"
        )

        text_body = f"""
سفارش جدید در فروشگاه بازبیا با موفقیت پرداخت شد.

شماره سفارش: {order.id}

مشتری:
نام: {customer_name}
موبایل: {customer_phone}

تحویل گیرنده:
{address_data["recipient_name"]}
{address_data["recipient_phone"]}

آدرس:
{address_data["address"]}

کد پستی:
{address_data["postal_code"]}

محصولات:
{chr(10).join(text_items)}

جمع کالاها:
{format_price(order.items_total)} تومان

هزینه ارسال:
{format_price(order.shipping_cost)} تومان

تخفیف:
{format_price(order.discount_amount)} تومان

مبلغ نهایی:
{format_price(order.total_price)} تومان

اطلاعات پرداخت:

درگاه:
{payment.gateway}

Authority:
{payment.authority or "-"}

کد پیگیری:
{payment.tracking_code or "-"}

شماره مرجع:
{payment.reference_id or "-"}

زمان پرداخت:
{paid_at}

مشاهده سفارش:
{admin_order_url}
""".strip()

        html_body = f"""
        <div dir="rtl"
             style="
                font-family:Tahoma,Arial,sans-serif;
                max-width:750px;
                margin:auto;
                background:#f5f5f5;
                padding:20px;
             ">

            <div style="
                background:#ffffff;
                border-radius:12px;
                padding:25px;
            ">

                <h2 style="
                    margin-top:0;
                    color:#198754;
                ">
                    ✅ سفارش جدید پرداخت شد
                </h2>

                <p>
                    سفارش
                    <strong>#{order.id}</strong>
                    با موفقیت پرداخت شده است.
                </p>

                <hr>

                <h3>اطلاعات مشتری</h3>

                <p>
                    <strong>نام:</strong>
                    {customer_name}
                </p>

                <p>
                    <strong>موبایل:</strong>
                    {customer_phone}
                </p>

                <h3>اطلاعات ارسال</h3>

                <p>
                    <strong>تحویل‌گیرنده:</strong>
                    {address_data["recipient_name"]}
                </p>

                <p>
                    <strong>تلفن تحویل‌گیرنده:</strong>
                    {address_data["recipient_phone"]}
                </p>

                <p>
                    <strong>آدرس:</strong>
                    {address_data["address"]}
                </p>

                <p>
                    <strong>کد پستی:</strong>
                    {address_data["postal_code"]}
                </p>

                <p>
                    <strong>روش ارسال:</strong>
                    {order.shipping_method_title or order.shipping_method_code or "-"}
                </p>

                <h3>محصولات سفارش</h3>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                ">

                    <thead>
                        <tr style="background:#eeeeee;">
                            <th style="padding:10px;border:1px solid #ddd;">
                                محصول
                            </th>

                            <th style="padding:10px;border:1px solid #ddd;">
                                تعداد
                            </th>

                            <th style="padding:10px;border:1px solid #ddd;">
                                قیمت واحد
                            </th>

                            <th style="padding:10px;border:1px solid #ddd;">
                                مجموع
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {"".join(item_rows)}
                    </tbody>

                </table>

                <h3>مبالغ</h3>

                <p>
                    جمع کالاها:
                    <strong>
                        {format_price(order.items_total)}
                        تومان
                    </strong>
                </p>

                <p>
                    هزینه ارسال:
                    <strong>
                        {format_price(order.shipping_cost)}
                        تومان
                    </strong>
                </p>

                <p>
                    تخفیف:
                    <strong>
                        {format_price(order.discount_amount)}
                        تومان
                    </strong>
                </p>

                <p style="font-size:18px;">
                    مبلغ نهایی:
                    <strong style="color:#198754;">
                        {format_price(order.total_price)}
                        تومان
                    </strong>
                </p>

                <hr>

                <h3>اطلاعات پرداخت</h3>

                <p>
                    <strong>درگاه:</strong>
                    {payment.gateway or "-"}
                </p>

                <p>
                    <strong>Authority:</strong>
                    {payment.authority or "-"}
                </p>

                <p>
                    <strong>کد پیگیری:</strong>
                    {payment.tracking_code or "-"}
                </p>

                <p>
                    <strong>شماره مرجع:</strong>
                    {payment.reference_id or "-"}
                </p>

                <p>
                    <strong>زمان پرداخت:</strong>
                    {paid_at}
                </p>

                <div style="
                    margin-top:30px;
                    text-align:center;
                ">
                    <a
                        href="{admin_order_url}"
                        style="
                            background:#198754;
                            color:#ffffff;
                            padding:12px 22px;
                            text-decoration:none;
                            border-radius:8px;
                            display:inline-block;
                        "
                    >
                        مشاهده سفارش در مدیریت
                    </a>
                </div>

            </div>
        </div>
        """

        recipient = settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )

        email.attach_alternative(
            html_body,
            "text/html",
        )

        email.send(
            fail_silently=False
        )

        logger.info(
            "Paid order email sent successfully. "
            "order_id=%s payment_id=%s",
            order.id,
            payment.id,
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send paid order email. "
            "order_id=%s payment_id=%s",
            order_id,
            payment_id,
        )

        return False
