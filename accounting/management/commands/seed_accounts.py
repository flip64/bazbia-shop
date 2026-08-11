from django.core.management.base import BaseCommand

from accounting.models import Account


class Command(BaseCommand):
    help = "ایجاد حساب‌های پایه حسابداری فروشگاه بازبیا"

    def handle(self, *args, **options):

        accounts = [
            # =================================================
            # دارایی‌ها
            # =================================================
            {
                "code": "1",
                "name": "دارایی‌ها",
                "account_type": Account.Type.ASSET,
                "parent": None,
                "allow_posting": False,
            },
            {
                "code": "110",
                "name": "وجوه نقد، بانک و درگاه‌ها",
                "account_type": Account.Type.ASSET,
                "parent": "1",
                "allow_posting": False,
            },
            {
                "code": "1101",
                "name": "صندوق",
                "account_type": Account.Type.ASSET,
                "parent": "110",
                "allow_posting": True,
            },
            {
                "code": "1102",
                "name": "حساب‌های بانکی",
                "account_type": Account.Type.ASSET,
                "parent": "110",
                "allow_posting": False,
            },
            {
                "code": "1103",
                "name": "درگاه‌های پرداخت",
                "account_type": Account.Type.ASSET,
                "parent": "110",
                "allow_posting": False,
            },
            {
                "code": "110301",
                "name": "زرین‌پال",
                "account_type": Account.Type.ASSET,
                "parent": "1103",
                "allow_posting": True,
            },

            {
                "code": "120",
                "name": "موجودی کالا",
                "account_type": Account.Type.ASSET,
                "parent": "1",
                "allow_posting": False,
            },
            {
                "code": "1201",
                "name": "موجودی انبار بازبیا",
                "account_type": Account.Type.ASSET,
                "parent": "120",
                "allow_posting": True,
            },

            {
                "code": "130",
                "name": "حساب‌های دریافتنی",
                "account_type": Account.Type.ASSET,
                "parent": "1",
                "allow_posting": True,
            },

            # =================================================
            # بدهی‌ها
            # =================================================
            {
                "code": "2",
                "name": "بدهی‌ها",
                "account_type": Account.Type.LIABILITY,
                "parent": None,
                "allow_posting": False,
            },
            {
                "code": "210",
                "name": "حساب‌های پرداختنی",
                "account_type": Account.Type.LIABILITY,
                "parent": "2",
                "allow_posting": False,
            },
            {
                "code": "2101",
                "name": "بدهی به تأمین‌کنندگان",
                "account_type": Account.Type.LIABILITY,
                "parent": "210",
                "allow_posting": True,
            },
            {
                "code": "220",
                "name": "وجوه قابل استرداد به مشتریان",
                "account_type": Account.Type.LIABILITY,
                "parent": "2",
                "allow_posting": True,
            },

            # =================================================
            # سرمایه
            # =================================================
            {
                "code": "3",
                "name": "سرمایه",
                "account_type": Account.Type.EQUITY,
                "parent": None,
                "allow_posting": False,
            },
            {
                "code": "3101",
                "name": "سرمایه مالک",
                "account_type": Account.Type.EQUITY,
                "parent": "3",
                "allow_posting": True,
            },

            # =================================================
            # درآمدها
            # =================================================
            {
                "code": "4",
                "name": "درآمدها",
                "account_type": Account.Type.INCOME,
                "parent": None,
                "allow_posting": False,
            },
            {
                "code": "4101",
                "name": "فروش کالا",
                "account_type": Account.Type.INCOME,
                "parent": "4",
                "allow_posting": True,
            },
            {
                "code": "4102",
                "name": "درآمد ارسال",
                "account_type": Account.Type.INCOME,
                "parent": "4",
                "allow_posting": True,
            },

            # =================================================
            # هزینه‌ها
            # =================================================
            {
                "code": "5",
                "name": "هزینه‌ها",
                "account_type": Account.Type.EXPENSE,
                "parent": None,
                "allow_posting": False,
            },
            {
                "code": "5101",
                "name": "بهای تمام‌شده کالای فروش‌رفته",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5201",
                "name": "هزینه بسته‌بندی",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5202",
                "name": "هزینه ارسال",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5203",
                "name": "کارمزد درگاه پرداخت",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5204",
                "name": "هزینه تبلیغات",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5205",
                "name": "هزینه سرور و دامنه",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
            {
                "code": "5299",
                "name": "سایر هزینه‌ها",
                "account_type": Account.Type.EXPENSE,
                "parent": "5",
                "allow_posting": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for data in accounts:
            parent_code = data.pop("parent")

            parent = None

            if parent_code:
                parent = Account.objects.get(
                    code=parent_code,
                )

            account, created = Account.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "account_type": data["account_type"],
                    "parent": parent,
                    "allow_posting": data["allow_posting"],
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"ایجاد شد: {account}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    f"بروزرسانی شد: {account}"
                )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "عملیات تکمیل شد. "
                    f"ایجاد: {created_count} | "
                    f"بروزرسانی: {updated_count}"
                )
            )
        )