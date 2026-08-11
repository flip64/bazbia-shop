from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounting.models import (
    Account,
    FiscalPeriod,
    JournalEntry,
)
from accounting.services.journal_service import JournalService

from orders.models import Order


class SalesAccountingService:
    """
    سرویس ثبت حسابداری فروش سفارش.

    مسئولیت این سرویس:
    - جلوگیری از ثبت سند تکراری
    - پیدا کردن دوره مالی
    - خواندن مبالغ قطعی Order
    - ساخت سند فروش
    - ثبت نهایی سند توسط JournalService
    """

    SALES_ACCOUNT_CODE = "4101"
    SHIPPING_INCOME_ACCOUNT_CODE = "4102"
    SALES_DISCOUNT_ACCOUNT_CODE = "4103"

    REFERENCE_TYPE = "order"

    @staticmethod
    def _money(value) -> Decimal:
        """
        تبدیل مطمئن مبلغ به Decimal.
        """

        if value is None:
            return Decimal("0")

        return Decimal(str(value))

    @classmethod
    def _get_account(
        cls,
        code: str,
    ) -> Account:
        """
        دریافت یک حساب عملیاتی معتبر.
        """

        try:
            account = Account.objects.get(
                code=code,
            )
        except Account.DoesNotExist:
            raise ValidationError(
                f"حساب حسابداری با کد {code} پیدا نشد."
            )

        if not account.is_active:
            raise ValidationError(
                f"حساب {account.name} غیرفعال است."
            )

        if not account.allow_posting:
            raise ValidationError(
                (
                    f"حساب {account.name} یک حساب گروهی است "
                    "و امکان ثبت سند روی آن وجود ندارد."
                )
            )

        return account

    @staticmethod
    def _get_fiscal_period(
        entry_date,
    ) -> FiscalPeriod:
        """
        پیدا کردن دوره مالی مربوط به تاریخ سند.
        """

        period = (
            FiscalPeriod.objects
            .filter(
                start_date__lte=entry_date,
                end_date__gte=entry_date,
            )
            .first()
        )

        if period is None:
            raise ValidationError(
                (
                    "برای تاریخ این فروش هیچ دوره مالی "
                    "تعریف نشده است."
                )
            )

        if period.is_closed:
            raise ValidationError(
                "دوره مالی مربوط به این فروش بسته شده است."
            )

        return period

    @classmethod
    def _get_existing_entry(
        cls,
        order: Order,
    ):
        """
        جلوگیری از ثبت دوباره سند فروش یک سفارش.

        callback درگاه ممکن است بیش از یک بار فراخوانی شود،
        بنابراین عملیات باید idempotent باشد.
        """

        return (
            JournalEntry.objects
            .filter(
                entry_type=JournalEntry.Type.SALE,
                reference_type=cls.REFERENCE_TYPE,
                reference_id=order.pk,
            )
            .order_by("pk")
            .first()
        )

    @classmethod
    @transaction.atomic
    def create_for_paid_order(
        cls,
        *,
        order: Order,
        payment_account: Account,
        entry_date=None,
    ) -> JournalEntry:
        """
        ساخت سند حسابداری برای سفارش پرداخت‌شده.

        مثال:

        کالاها:        500,000
        ارسال:          50,000
        تخفیف:          20,000
        پرداخت نهایی:  530,000

        بدهکار:
            زرین‌پال        530,000
            تخفیفات فروش     20,000

        بستانکار:
            فروش کالا       500,000
            درآمد ارسال      50,000
        """

        # سفارش را Lock می‌کنیم تا دو callback همزمان
        # برای یک سفارش دو سند ایجاد نکنند.
        order = (
            Order.objects
            .select_for_update()
            .get(pk=order.pk)
        )

        # -------------------------------------------------
        # جلوگیری از سند تکراری
        # -------------------------------------------------

        existing_entry = cls._get_existing_entry(
            order
        )

        if existing_entry is not None:
            return existing_entry

        # -------------------------------------------------
        # فقط سفارش پرداخت‌شده باید سند فروش بخورد
        # -------------------------------------------------

        if order.status != Order.STATUS_PAID:
            raise ValidationError(
                (
                    f"سفارش #{order.pk} هنوز پرداخت‌شده نیست "
                    "و سند فروش برای آن قابل ثبت نیست."
                )
            )

        # -------------------------------------------------
        # حساب دریافت وجه
        # -------------------------------------------------

        if payment_account is None:
            raise ValidationError(
                "حساب دریافت وجه مشخص نشده است."
            )

        if not payment_account.is_active:
            raise ValidationError(
                "حساب دریافت وجه غیرفعال است."
            )

        if not payment_account.allow_posting:
            raise ValidationError(
                "امکان ثبت سند روی حساب دریافت وجه وجود ندارد."
            )

        # -------------------------------------------------
        # مبالغ قطعی سفارش
        # -------------------------------------------------

        items_total = cls._money(
            order.items_total
        )

        shipping_cost = cls._money(
            order.shipping_cost
        )

        discount_amount = cls._money(
            order.discount_amount
        )

        total_price = cls._money(
            order.total_price
        )

        if items_total < 0:
            raise ValidationError(
                "مبلغ کالاهای سفارش نمی‌تواند منفی باشد."
            )

        if shipping_cost < 0:
            raise ValidationError(
                "هزینه ارسال نمی‌تواند منفی باشد."
            )

        if discount_amount < 0:
            raise ValidationError(
                "مبلغ تخفیف نمی‌تواند منفی باشد."
            )

        if total_price <= 0:
            raise ValidationError(
                "مبلغ نهایی سفارش باید بزرگ‌تر از صفر باشد."
            )

        # -------------------------------------------------
        # کنترل سازگاری اعداد سفارش
        # -------------------------------------------------

        calculated_total = (
            items_total
            + shipping_cost
            - discount_amount
        )

        if calculated_total < 0:
            calculated_total = Decimal("0")

        if calculated_total != total_price:
            raise ValidationError(
                (
                    "مبالغ سفارش با مبلغ نهایی سازگار نیستند. "
                    f"مبلغ محاسبه‌شده: {calculated_total:,} - "
                    f"مبلغ ثبت‌شده سفارش: {total_price:,}"
                )
            )

        # -------------------------------------------------
        # حساب‌ها
        # -------------------------------------------------

        sales_account = cls._get_account(
            cls.SALES_ACCOUNT_CODE
        )

        shipping_income_account = None

        if shipping_cost > 0:
            shipping_income_account = cls._get_account(
                cls.SHIPPING_INCOME_ACCOUNT_CODE
            )

        discount_account = None

        if discount_amount > 0:
            discount_account = cls._get_account(
                cls.SALES_DISCOUNT_ACCOUNT_CODE
            )

        # -------------------------------------------------
        # تاریخ و دوره مالی
        # -------------------------------------------------

        if entry_date is None:
            entry_date = timezone.localdate()

        fiscal_period = cls._get_fiscal_period(
            entry_date
        )

        # -------------------------------------------------
        # ردیف‌های سند
        # -------------------------------------------------

        lines = []

        # مبلغی که از مشتری دریافت شده
        lines.append(
            JournalService.debit_line(
                account=payment_account,
                amount=total_price,
                description=(
                    f"دریافت وجه سفارش #{order.pk}"
                ),
            )
        )

        # تخفیف فروش
        if discount_amount > 0:
            lines.append(
                JournalService.debit_line(
                    account=discount_account,
                    amount=discount_amount,
                    description=(
                        f"تخفیف سفارش #{order.pk}"
                    ),
                )
            )

        # فروش کالا
        if items_total > 0:
            lines.append(
                JournalService.credit_line(
                    account=sales_account,
                    amount=items_total,
                    description=(
                        f"فروش کالای سفارش #{order.pk}"
                    ),
                )
            )

        # درآمد ارسال
        if shipping_cost > 0:
            lines.append(
                JournalService.credit_line(
                    account=shipping_income_account,
                    amount=shipping_cost,
                    description=(
                        f"هزینه ارسال سفارش #{order.pk}"
                    ),
                )
            )

        # -------------------------------------------------
        # ساخت و ثبت نهایی سند
        # -------------------------------------------------

        entry = JournalService.create_entry(
            fiscal_period=fiscal_period,
            entry_type=JournalEntry.Type.SALE,
            date=entry_date,
            description=(
                f"فروش سفارش #{order.pk}"
            ),
            reference_type=cls.REFERENCE_TYPE,
            reference_id=order.pk,
            lines=lines,
            auto_post=True,
        )

        return entry