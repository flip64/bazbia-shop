from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from accounting.models import (
    Account,
    FiscalPeriod,
    JournalEntry,
)
from accounting.services.journal_service import (
    JournalService,
)

from orders.models import (
    Order,
    OrderItemCostAllocation,
)


class SalesAccountingService:
    """
    سرویس ثبت حسابداری فروش سفارش.

    مسئولیت‌ها:
    - جلوگیری از ثبت سند تکراری
    - بررسی پرداخت‌شدن سفارش
    - پیدا کردن دوره مالی
    - ثبت درآمد فروش
    - ثبت درآمد ارسال
    - ثبت تخفیف
    - محاسبه بهای تمام‌شده واقعی
    - تفکیک بهای کالای انبار داخلی و تأمین‌کننده
    - ساخت و ثبت نهایی سند حسابداری
    """

    # =====================================================
    # حساب‌های درآمد
    # =====================================================

    SALES_ACCOUNT_CODE = "4101"
    SHIPPING_INCOME_ACCOUNT_CODE = "4102"
    SALES_DISCOUNT_ACCOUNT_CODE = "4103"

    # =====================================================
    # حساب‌های بهای تمام‌شده و موجودی
    # =====================================================

    COGS_ACCOUNT_CODE = "5101"

    INTERNAL_INVENTORY_ACCOUNT_CODE = "1201"

    SUPPLIER_PAYABLE_ACCOUNT_CODE = "2101"

    # =====================================================
    # Reference
    # =====================================================

    REFERENCE_TYPE = "order"

    # =====================================================
    # ابزارهای عمومی
    # =====================================================

    @staticmethod
    def _money(value) -> Decimal:
        """
        تبدیل امن مبلغ به Decimal بدون اعشار.

        چون سیستم مالی بازبیا فعلاً با واحد پول صحیح
        و decimal_places=0 کار می‌کند.
        """

        if value is None:
            return Decimal("0")

        return Decimal(
            str(value)
        ).quantize(
            Decimal("1")
        )

    # =====================================================
    # دریافت حساب
    # =====================================================

    @classmethod
    def _get_account(
        cls,
        code: str,
    ) -> Account:
        """
        دریافت حساب عملیاتی معتبر.
        """

        try:
            account = Account.objects.get(
                code=code,
            )

        except Account.DoesNotExist:
            raise ValidationError(
                (
                    "حساب حسابداری با کد "
                    f"{code} پیدا نشد."
                )
            )

        if not account.is_active:
            raise ValidationError(
                (
                    f"حساب {account.name} "
                    "غیرفعال است."
                )
            )

        if not account.allow_posting:
            raise ValidationError(
                (
                    f"حساب {account.name} "
                    "یک حساب گروهی است و "
                    "امکان ثبت سند روی آن "
                    "وجود ندارد."
                )
            )

        return account

    # =====================================================
    # دوره مالی
    # =====================================================

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
            .order_by("start_date")
            .first()
        )

        if period is None:
            raise ValidationError(
                (
                    "برای تاریخ این فروش "
                    "هیچ دوره مالی تعریف نشده است."
                )
            )

        if period.is_closed:
            raise ValidationError(
                (
                    "دوره مالی مربوط به "
                    "این فروش بسته شده است."
                )
            )

        return period

    # =====================================================
    # سند موجود
    # =====================================================

    @classmethod
    def _get_existing_entry(
        cls,
        order: Order,
    ):
        """
        جلوگیری از ثبت دوباره سند.

        Callback درگاه ممکن است بیش از یک بار
        اجرا شود، بنابراین عملیات باید idempotent باشد.
        """

        return (
            JournalEntry.objects
            .filter(
                entry_type=(
                    JournalEntry.Type.SALE
                ),
                reference_type=(
                    cls.REFERENCE_TYPE
                ),
                reference_id=order.pk,
            )
            .order_by("pk")
            .first()
        )

    # =====================================================
    # اعتبارسنجی حساب دریافت وجه
    # =====================================================

    @staticmethod
    def _validate_payment_account(
        payment_account: Account,
    ) -> None:
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
                (
                    "امکان ثبت سند روی "
                    "حساب دریافت وجه وجود ندارد."
                )
            )

    # =====================================================
    # محاسبه بهای تمام‌شده
    # =====================================================

    @classmethod
    def _calculate_costs(
        cls,
        *,
        order: Order,
    ) -> tuple[Decimal, Decimal]:
        """
        محاسبه بهای تمام‌شده سفارش بر اساس
        OrderItemCostAllocation.

        خروجی:

        (
            internal_cost,
            supplier_cost,
        )

        internal_cost:
            کالایی که از InventoryLotهای
            انبار داخلی تأمین شده است.

        supplier_cost:
            کالایی که مستقیماً از SupplierOffer
            تأمین شده است.
        """

        order_items = list(
            order.items.all()
        )

        if not order_items:
            raise ValidationError(
                (
                    f"سفارش #{order.pk} "
                    "هیچ آیتمی ندارد."
                )
            )

        allocations = list(
            OrderItemCostAllocation.objects
            .filter(
                order_item__order=order,
            )
            .select_related(
                "order_item",
                "inventory_lot",
                "supplier",
                "supplier_offer",
            )
            .order_by(
                "order_item_id",
                "id",
            )
        )

        # -------------------------------------------------
        # باید تمام آیتم‌های سفارش Allocation داشته باشند
        # -------------------------------------------------

        allocations_by_item = {}

        for allocation in allocations:
            allocations_by_item.setdefault(
                allocation.order_item_id,
                [],
            ).append(
                allocation
            )

        internal_cost = Decimal("0")
        supplier_cost = Decimal("0")

        for order_item in order_items:
            item_allocations = (
                allocations_by_item.get(
                    order_item.pk,
                    [],
                )
            )

            if not item_allocations:
                raise ValidationError(
                    (
                        "بهای تمام‌شده "
                        f"OrderItem #{order_item.pk} "
                        "ثبت نشده است."
                    )
                )

            allocated_quantity = sum(
                int(allocation.quantity)
                for allocation
                in item_allocations
            )

            order_quantity = int(
                order_item.quantity
            )

            if (
                allocated_quantity
                != order_quantity
            ):
                raise ValidationError(
                    (
                        "تعداد تخصیص بهای "
                        "OrderItem "
                        f"#{order_item.pk} "
                        "با تعداد سفارش برابر نیست. "
                        f"تعداد سفارش: {order_quantity} - "
                        "تعداد تخصیص‌یافته: "
                        f"{allocated_quantity}"
                    )
                )

            for allocation in item_allocations:
                quantity = int(
                    allocation.quantity
                )

                if quantity <= 0:
                    raise ValidationError(
                        (
                            "تعداد Allocation "
                            f"#{allocation.pk} "
                            "نامعتبر است."
                        )
                    )

                if allocation.unit_cost is None:
                    raise ValidationError(
                        (
                            "قیمت خرید Allocation "
                            f"#{allocation.pk} "
                            "مشخص نشده است."
                        )
                    )

                unit_cost = cls._money(
                    allocation.unit_cost
                )

                if unit_cost < 0:
                    raise ValidationError(
                        (
                            "قیمت خرید Allocation "
                            f"#{allocation.pk} "
                            "نمی‌تواند منفی باشد."
                        )
                    )

                allocation_cost = (
                    unit_cost
                    * Decimal(quantity)
                )

                # =========================================
                # انبار داخلی
                # =========================================

                if (
                    allocation.source_type
                    ==
                    OrderItemCostAllocation
                    .SOURCE_INTERNAL
                ):
                    if (
                        allocation.inventory_lot_id
                        is None
                    ):
                        raise ValidationError(
                            (
                                "Allocation داخلی "
                                f"#{allocation.pk} "
                                "InventoryLot ندارد."
                            )
                        )

                    internal_cost += (
                        allocation_cost
                    )

                # =========================================
                # تأمین‌کننده
                # =========================================

                elif (
                    allocation.source_type
                    ==
                    OrderItemCostAllocation
                    .SOURCE_SUPPLIER
                ):
                    if (
                        allocation.supplier_offer_id
                        is None
                    ):
                        raise ValidationError(
                            (
                                "Allocation تأمین‌کننده "
                                f"#{allocation.pk} "
                                "SupplierOffer ندارد."
                            )
                        )

                    supplier_cost += (
                        allocation_cost
                    )

                # =========================================
                # Source نامعتبر
                # =========================================

                else:
                    raise ValidationError(
                        (
                            "نوع منبع Allocation "
                            f"#{allocation.pk} "
                            "نامعتبر است."
                        )
                    )

        return (
            internal_cost.quantize(
                Decimal("1")
            ),
            supplier_cost.quantize(
                Decimal("1")
            ),
        )

    # =====================================================
    # ثبت فروش
    # =====================================================

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
        ساخت سند کامل فروش سفارش پرداخت‌شده.

        مثال:

        فروش کالا:
            500,000

        ارسال:
             50,000

        تخفیف:
             20,000

        پرداخت:
            530,000

        بهای کالای داخلی:
            200,000

        بهای کالای تأمین‌کننده:
            100,000


        سند:

        بدهکار:
            زرین‌پال                   530,000
            تخفیفات فروش               20,000
            بهای تمام‌شده             300,000

        بستانکار:
            فروش کالا                 500,000
            درآمد ارسال                50,000
            موجودی داخلی              200,000
            بدهی به تأمین‌کنندگان     100,000
        """

        # -------------------------------------------------
        # Lock سفارش
        # -------------------------------------------------

        order = (
            Order.objects
            .select_for_update()
            .prefetch_related(
                "items",
            )
            .get(
                pk=order.pk
            )
        )

        # -------------------------------------------------
        # جلوگیری از ثبت سند تکراری
        # -------------------------------------------------

        existing_entry = (
            cls._get_existing_entry(
                order
            )
        )

        if existing_entry is not None:
            return existing_entry

        # -------------------------------------------------
        # فقط سفارش پرداخت‌شده
        # -------------------------------------------------

        if (
            order.status
            != Order.STATUS_PAID
        ):
            raise ValidationError(
                (
                    f"سفارش #{order.pk} "
                    "هنوز پرداخت‌شده نیست و "
                    "سند فروش برای آن "
                    "قابل ثبت نیست."
                )
            )

        # -------------------------------------------------
        # حساب دریافت وجه
        # -------------------------------------------------

        cls._validate_payment_account(
            payment_account
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
                (
                    "مبلغ کالاهای سفارش "
                    "نمی‌تواند منفی باشد."
                )
            )

        if shipping_cost < 0:
            raise ValidationError(
                (
                    "هزینه ارسال "
                    "نمی‌تواند منفی باشد."
                )
            )

        if discount_amount < 0:
            raise ValidationError(
                (
                    "مبلغ تخفیف "
                    "نمی‌تواند منفی باشد."
                )
            )

        if total_price <= 0:
            raise ValidationError(
                (
                    "مبلغ نهایی سفارش باید "
                    "بزرگ‌تر از صفر باشد."
                )
            )

        # -------------------------------------------------
        # کنترل مبلغ نهایی سفارش
        # -------------------------------------------------

        calculated_total = (
            items_total
            + shipping_cost
            - discount_amount
        )

        if calculated_total < 0:
            calculated_total = (
                Decimal("0")
            )

        if (
            calculated_total
            != total_price
        ):
            raise ValidationError(
                (
                    "مبالغ سفارش با مبلغ "
                    "نهایی سازگار نیستند. "
                    "مبلغ محاسبه‌شده: "
                    f"{calculated_total:,} - "
                    "مبلغ ثبت‌شده سفارش: "
                    f"{total_price:,}"
                )
            )

        # -------------------------------------------------
        # محاسبه بهای تمام‌شده
        # -------------------------------------------------

        (
            internal_cost,
            supplier_cost,
        ) = cls._calculate_costs(
            order=order
        )

        total_cogs = (
            internal_cost
            + supplier_cost
        )

        # -------------------------------------------------
        # حساب‌های فروش
        # -------------------------------------------------

        sales_account = (
            cls._get_account(
                cls.SALES_ACCOUNT_CODE
            )
        )

        shipping_income_account = None

        if shipping_cost > 0:
            shipping_income_account = (
                cls._get_account(
                    cls
                    .SHIPPING_INCOME_ACCOUNT_CODE
                )
            )

        discount_account = None

        if discount_amount > 0:
            discount_account = (
                cls._get_account(
                    cls
                    .SALES_DISCOUNT_ACCOUNT_CODE
                )
            )

        # -------------------------------------------------
        # حساب‌های بهای تمام‌شده
        # -------------------------------------------------

        cogs_account = None
        inventory_account = None
        supplier_payable_account = None

        if total_cogs > 0:
            cogs_account = (
                cls._get_account(
                    cls.COGS_ACCOUNT_CODE
                )
            )

        if internal_cost > 0:
            inventory_account = (
                cls._get_account(
                    cls
                    .INTERNAL_INVENTORY_ACCOUNT_CODE
                )
            )

        if supplier_cost > 0:
            supplier_payable_account = (
                cls._get_account(
                    cls
                    .SUPPLIER_PAYABLE_ACCOUNT_CODE
                )
            )

        # -------------------------------------------------
        # تاریخ و دوره مالی
        # -------------------------------------------------

        if entry_date is None:
            entry_date = (
                timezone.localdate()
            )

        fiscal_period = (
            cls._get_fiscal_period(
                entry_date
            )
        )

        # -------------------------------------------------
        # خطوط سند
        # -------------------------------------------------

        lines = []

        # =================================================
        # بخش درآمد فروش
        # =================================================

        # دریافت وجه از مشتری
        lines.append(
            JournalService.debit_line(
                account=payment_account,
                amount=total_price,
                description=(
                    "دریافت وجه سفارش "
                    f"#{order.pk}"
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
                        "تخفیف فروش سفارش "
                        f"#{order.pk}"
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
                        "فروش کالای سفارش "
                        f"#{order.pk}"
                    ),
                )
            )

        # درآمد ارسال
        if shipping_cost > 0:
            lines.append(
                JournalService.credit_line(
                    account=(
                        shipping_income_account
                    ),
                    amount=shipping_cost,
                    description=(
                        "درآمد ارسال سفارش "
                        f"#{order.pk}"
                    ),
                )
            )

        # =================================================
        # بخش بهای تمام‌شده
        # =================================================

        # کل بهای تمام‌شده بدهکار می‌شود
        if total_cogs > 0:
            lines.append(
                JournalService.debit_line(
                    account=cogs_account,
                    amount=total_cogs,
                    description=(
                        "بهای تمام‌شده "
                        f"سفارش #{order.pk}"
                    ),
                )
            )

        # موجودی داخلی مصرف‌شده
        if internal_cost > 0:
            lines.append(
                JournalService.credit_line(
                    account=inventory_account,
                    amount=internal_cost,
                    description=(
                        "خروج موجودی داخلی "
                        "برای سفارش "
                        f"#{order.pk}"
                    ),
                )
            )

        # خرید/تعهد نسبت به تأمین‌کنندگان
        if supplier_cost > 0:
            lines.append(
                JournalService.credit_line(
                    account=(
                        supplier_payable_account
                    ),
                    amount=supplier_cost,
                    description=(
                        "بدهی تأمین‌کننده بابت "
                        f"سفارش #{order.pk}"
                    ),
                )
            )

        # -------------------------------------------------
        # ثبت سند
        # -------------------------------------------------

        entry = (
            JournalService.create_entry(
                fiscal_period=(
                    fiscal_period
                ),
                entry_type=(
                    JournalEntry.Type.SALE
                ),
                date=entry_date,
                description=(
                    "فروش و بهای تمام‌شده "
                    f"سفارش #{order.pk}"
                ),
                reference_type=(
                    cls.REFERENCE_TYPE
                ),
                reference_id=order.pk,
                lines=lines,
                auto_post=True,
            )
        )

        return entry
