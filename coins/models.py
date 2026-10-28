"""Collector catalog and ready-made packs; prices/stock belong to products."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, F


class Calendar(models.TextChoices):
    GREGORIAN = "gregorian", "میلادی"
    SOLAR_HIJRI = "solar_hijri", "هجری شمسی"
    LUNAR_HIJRI = "lunar_hijri", "هجری قمری"
    IMPERIAL_IRAN = "imperial_iran", "شاهنشاهی ایران"
    REGNAL = "regnal", "سال سلطنت"
    OTHER = "other", "سایر"


class Finish(models.TextChoices):
    UNKNOWN = "unknown", "نامشخص"
    STANDARD = "standard", "معمولی"
    BU = "bu", "BU"
    PROOF = "proof", "Proof"
    REVERSE_PROOF = "reverse_proof", "Reverse Proof"
    SPECIMEN = "specimen", "Specimen"


class Condition(models.TextChoices):
    UNKNOWN = "unknown", "ارزیابی نشده"
    POOR = "poor", "ضعیف"
    FAIR = "fair", "Fair"
    AG = "ag", "AG"
    G = "g", "G"
    VG = "vg", "VG"
    F = "f", "F"
    VF = "vf", "VF"
    XF = "xf", "XF / EF"
    AU = "au", "AU"
    UNC = "unc", "UNC"


class SaleMode(models.TextChoices):
    UNIQUE = "unique", "نمونه اختصاصی با عکس واقعی"
    SIMILAR = "similar", "چند نمونه مشابه"


def measure(label):
    return models.DecimalField(
        label,
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )


class ValidatedModel(models.Model):
    """Normal saves validate relations too; bulk/update bypass Django validation."""

    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("زمان تغییر", auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from .guards import inventory_write
        from django.db import router

        using = kwargs.get("using") or router.db_for_write(type(self), instance=self)
        ids = [self.variant_id] if hasattr(self, "variant_id") else []
        if self._meta.model_name == "coinpackitem" and self.pack_variant_id:
            ids.append(self.pack_variant.variant_id)
        if self._meta.model_name == "coinimagedetail" and self.image_id:
            ids.append(self.image.variant_id)
        with inventory_write(ids, using, force=bool(ids)):
            self.full_clean()
            return super().save(*args, **kwargs)


class NamedModel(ValidatedModel):
    name = models.CharField("نام فارسی", max_length=160)
    name_en = models.CharField("نام انگلیسی", max_length=160, blank=True)
    slug = models.SlugField("نامک", max_length=180, unique=True)
    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        abstract = True
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class CoinIssuer(NamedModel):
    country_code = models.CharField("کد کشور (اختیاری)", max_length=3, blank=True)
    is_historical = models.BooleanField("قلمرو تاریخی", default=False)

    class Meta(NamedModel.Meta):
        verbose_name = "کشور یا قلمرو"
        verbose_name_plural = "کشورها و قلمروها"


class HistoricalPeriod(NamedModel):
    issuer = models.ForeignKey(
        CoinIssuer,
        on_delete=models.PROTECT,
        related_name="periods",
        verbose_name="صادرکننده",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
        verbose_name="دوره والد",
    )
    # Signed years support BC. These bounds are Gregorian, not coin inscriptions.
    start_year = models.IntegerField(
        "شروع میلادی (منفی: پیش از میلاد)", null=True, blank=True
    )
    end_year = models.IntegerField("پایان میلادی", null=True, blank=True)

    class Meta(NamedModel.Meta):
        verbose_name = "دوره تاریخی"
        verbose_name_plural = "دوره‌های تاریخی"
        constraints = [
            models.CheckConstraint(
                condition=Q(start_year__isnull=True)
                | Q(end_year__isnull=True)
                | Q(end_year__gte=F("start_year")),
                name="coin_period_year_order",
            )
        ]

    def clean(self):
        super().clean()
        if self.parent_id:
            seen = {self.pk} if self.pk else set()
            ancestor = self.parent
            while ancestor:
                if ancestor.pk in seen:
                    raise ValidationError({"parent": "دوره والد نباید چرخه ایجاد کند."})
                seen.add(ancestor.pk)
                if ancestor.issuer_id != self.issuer_id:
                    raise ValidationError(
                        {"parent": "صادرکننده دوره والد باید یکسان باشد."}
                    )
                ancestor = ancestor.parent if ancestor.parent_id else None
        if self.pk and self.children.exclude(issuer_id=self.issuer_id).exists():
            raise ValidationError({"issuer": "صادرکننده دوره‌های فرزند متفاوت است."})
        if self.pk and self.coin_types.exclude(issuer_id=self.issuer_id).exists():
            raise ValidationError({"issuer": "صادرکننده سکه‌های این دوره متفاوت است."})


class CoinRuler(NamedModel):
    periods = models.ManyToManyField(
        HistoricalPeriod, blank=True, related_name="rulers", verbose_name="دوره‌ها"
    )

    class Meta(NamedModel.Meta):
        verbose_name = "حاکم"
        verbose_name_plural = "حاکمان"


class CoinCurrency(NamedModel):
    # Shared and historical currencies need not be confined to one territory.
    issuers = models.ManyToManyField(
        CoinIssuer,
        blank=True,
        related_name="currencies",
        verbose_name="کشورها یا قلمروهای استفاده‌کننده",
    )
    code = models.CharField("کد", max_length=12, blank=True)
    symbol = models.CharField("نماد", max_length=20, blank=True)

    class Meta(NamedModel.Meta):
        verbose_name = "واحد پول"
        verbose_name_plural = "واحدهای پول"


class CoinMaterial(NamedModel):
    symbol = models.CharField("نماد فلز", max_length=20, blank=True)

    class Meta(NamedModel.Meta):
        verbose_name = "فلز یا آلیاژ"
        verbose_name_plural = "فلزها و آلیاژها"


class CoinMint(NamedModel):
    issuer = models.ForeignKey(
        CoinIssuer,
        on_delete=models.PROTECT,
        related_name="mints",
        verbose_name="کشور یا قلمرو",
    )
    city = models.CharField("شهر", max_length=120, blank=True)

    class Meta(NamedModel.Meta):
        verbose_name = "ضرابخانه"
        verbose_name_plural = "ضرابخانه‌ها"


class CoinTheme(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = "موضوع"
        verbose_name_plural = "موضوع‌ها"


class CoinType(ValidatedModel):
    class Kind(models.TextChoices):
        CIRCULATION = "circulation", "رایج"
        COMMEMORATIVE = "commemorative", "یادبود"
        COLLECTOR = "collector", "کلکسیونی"
        PATTERN = "pattern", "آزمایشی"
        TOKEN = "token", "ژتون"
        OTHER = "other", "سایر"

    class Construction(models.TextChoices):
        UNKNOWN = "unknown", "نامشخص"
        SOLID = "solid", "یکپارچه / آلیاژی"
        BIMETAL = "bimetal", "بای‌متال (دوفلزی)"
        MULTIPART = "multipart", "چندبخشی"
        PLATED = "plated", "روکش‌دار"
        CLAD = "clad", "لایه‌ای"

    class Shape(models.TextChoices):
        UNKNOWN = "unknown", "نامشخص"
        ROUND = "round", "گرد"
        POLYGON = "polygon", "چندضلعی"
        SQUARE = "square", "مربع"
        RECTANGLE = "rectangle", "مستطیل"
        OVAL = "oval", "بیضی"
        SCALLOPED = "scalloped", "موج‌دار"
        IRREGULAR = "irregular", "نامنظم"
        OTHER = "other", "سایر"

    class Edge(models.TextChoices):
        UNKNOWN = "unknown", "نامشخص"
        PLAIN = "plain", "صاف"
        REEDED = "reeded", "شیاردار"
        LETTERED = "lettered", "نوشته‌دار"
        MIXED = "mixed", "ترکیبی"
        OTHER = "other", "سایر"

    is_published = models.BooleanField(
        "انتشار در کاتالوگ", default=False, db_index=True
    )
    introduction = models.TextField("معرفی کوتاه", blank=True)
    story = models.TextField(
        "داستان سکه",
        blank=True,
        help_text="متن ساده؛ تیتر با ## و فهرست با - در ابتدای خط",
    )
    story_sources = models.TextField("منابع داستان", blank=True)
    name = models.CharField("عنوان کاتالوگی", max_length=200)
    slug = models.SlugField("نامک", max_length=180, unique=True)
    issuer = models.ForeignKey(
        CoinIssuer,
        on_delete=models.PROTECT,
        related_name="coin_types",
        verbose_name="صادرکننده",
    )
    period = models.ForeignKey(
        HistoricalPeriod,
        on_delete=models.PROTECT,
        related_name="coin_types",
        null=True,
        blank=True,
        verbose_name="دوره",
    )
    ruler = models.ForeignKey(
        CoinRuler, on_delete=models.PROTECT, null=True, blank=True, verbose_name="حاکم"
    )
    currency = models.ForeignKey(
        CoinCurrency,
        on_delete=models.PROTECT,
        related_name="coin_types",
        null=True,
        blank=True,
        verbose_name="واحد پول",
    )
    face_value = models.DecimalField(
        "ارزش اسمی",
        max_digits=16,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    denomination_label = models.CharField("عنوان ارزش اسمی", max_length=100, blank=True)
    issue_kind = models.CharField(
        "نوع انتشار", max_length=20, choices=Kind.choices, default=Kind.CIRCULATION
    )
    calendar = models.CharField(
        "تقویم تولید",
        max_length=20,
        choices=Calendar.choices,
        default=Calendar.GREGORIAN,
    )
    calendar_notes = models.CharField("توضیح تقویم یا مبدأ", max_length=160, blank=True)
    year_start = models.IntegerField(
        "شروع تولید در تقویم انتخابی", null=True, blank=True
    )
    year_end = models.IntegerField(
        "پایان تولید در تقویم انتخابی", null=True, blank=True
    )
    construction = models.CharField(
        "ساختار",
        max_length=20,
        choices=Construction.choices,
        default=Construction.UNKNOWN,
    )
    shape = models.CharField(
        "شکل", max_length=20, choices=Shape.choices, default=Shape.UNKNOWN
    )
    shape_notes = models.CharField("توضیح شکل", max_length=160, blank=True)
    side_count = models.PositiveSmallIntegerField(
        "تعداد ضلع", null=True, blank=True, validators=[MinValueValidator(3)]
    )
    has_hole = models.BooleanField("سوراخ مرکزی", null=True, blank=True)
    weight_g = measure("وزن استاندارد (گرم)")
    diameter_mm = measure("قطر استاندارد (میلی‌متر)")
    width_mm = measure("عرض (میلی‌متر)")
    height_mm = measure("طول (میلی‌متر)")
    thickness_mm = measure("ضخامت (میلی‌متر)")
    edge_type = models.CharField(
        "نوع لبه", max_length=20, choices=Edge.choices, default=Edge.UNKNOWN
    )
    edge_inscription = models.TextField("نوشته لبه", blank=True)
    edge_notes = models.TextField("شرح لبه", blank=True)
    alignment_degrees = models.PositiveSmallIntegerField(
        "زاویه دو روی سکه", null=True, blank=True, validators=[MaxValueValidator(359)]
    )
    obverse_description = models.TextField("شرح رو", blank=True)
    obverse_inscription = models.TextField("نوشته رو", blank=True)
    obverse_designer = models.CharField("طراح رو", max_length=160, blank=True)
    reverse_description = models.TextField("شرح پشت", blank=True)
    reverse_inscription = models.TextField("نوشته پشت", blank=True)
    reverse_designer = models.CharField("طراح پشت", max_length=160, blank=True)
    languages = models.CharField("زبان نوشته‌ها", max_length=160, blank=True)
    themes = models.ManyToManyField(
        CoinTheme, blank=True, related_name="coin_types", verbose_name="موضوع‌ها"
    )
    series_name = models.CharField("مجموعه یا سری", max_length=160, blank=True)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "نوع سکه"
        verbose_name_plural = "انواع سکه"
        ordering = ["name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(year_start__isnull=True)
                | Q(year_end__isnull=True)
                | Q(year_end__gte=F("year_start")),
                name="coin_type_year_order",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.period_id and self.period.issuer_id != self.issuer_id:
            raise ValidationError({"period": "دوره باید متعلق به صادرکننده باشد."})
        if self.pk:
            for issue in self.issues.all():
                if issue.calendar != self.calendar:
                    raise ValidationError(
                        {"calendar": "ابتدا تقویم نوبت‌های ضرب مرتبط را اصلاح کنید."}
                    )
                if issue.year is not None and (
                    (self.year_start is not None and issue.year < self.year_start)
                    or (self.year_end is not None and issue.year > self.year_end)
                ):
                    raise ValidationError(
                        "بازه تولید نباید نوبت‌های ضرب ثبت‌شده را خارج کند."
                    )
                if (
                    issue.pack_items.exclude(
                        pack_variant__pack__issuer_id=self.issuer_id
                    )
                    .exclude(pack_variant__pack__issuer__isnull=True)
                    .exists()
                ):
                    raise ValidationError(
                        {"issuer": "صادرکننده با پک‌های مرتبط ناسازگار است."}
                    )


class CoinCompositionPart(ValidatedModel):
    class Part(models.TextChoices):
        BODY = "body", "بدنه"
        CENTER = "center", "مرکز"
        RING = "ring", "حلقه"
        COATING = "coating", "روکش"
        LAYER = "layer", "لایه"
        OTHER = "other", "سایر"

    coin_type = models.ForeignKey(
        CoinType,
        on_delete=models.CASCADE,
        related_name="composition_parts",
        verbose_name="نوع سکه",
    )
    part = models.CharField("بخش", max_length=20, choices=Part.choices)
    position = models.PositiveSmallIntegerField(
        "شماره بخش یا لایه", default=1, validators=[MinValueValidator(1)]
    )
    material = models.ForeignKey(
        CoinMaterial, on_delete=models.PROTECT, verbose_name="جنس"
    )
    fineness = models.DecimalField(
        "عیار بین صفر و یک",
        max_digits=6,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00001")),
            MaxValueValidator(Decimal("1")),
        ],
    )
    notes = models.TextField("شرح ترکیب", blank=True)

    class Meta:
        verbose_name = "ترکیب فلزی"
        verbose_name_plural = "ترکیب‌های فلزی"
        constraints = [
            models.UniqueConstraint(
                fields=["coin_type", "part", "position"],
                name="coin_composition_part_unique",
            )
        ]

    def __str__(self):
        return f"{self.coin_type} / {self.get_part_display()} / {self.material}"


class CoinIssue(ValidatedModel):
    class DateStatus(models.TextChoices):
        KNOWN = "known", "سال مشخص"
        UNDATED = "undated", "بدون تاریخ"
        ILLEGIBLE = "illegible", "ناخوانا"
        UNKNOWN = "unknown", "نامشخص"

    coin_type = models.ForeignKey(
        CoinType,
        on_delete=models.PROTECT,
        related_name="issues",
        verbose_name="نوع سکه",
    )
    year = models.IntegerField("سال در تقویم سکه", null=True, blank=True, db_index=True)
    calendar = models.CharField(
        "تقویم", max_length=20, choices=Calendar.choices, default=Calendar.GREGORIAN
    )
    date_status = models.CharField(
        "وضعیت تاریخ",
        max_length=20,
        choices=DateStatus.choices,
        default=DateStatus.KNOWN,
    )
    date_inscription = models.CharField("متن تاریخ روی سکه", max_length=120, blank=True)
    gregorian_year_start = models.IntegerField(
        "ابتدای معادل میلادی", null=True, blank=True
    )
    gregorian_year_end = models.IntegerField(
        "انتهای معادل میلادی", null=True, blank=True
    )
    mint = models.ForeignKey(
        CoinMint,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="ضرابخانه",
    )
    mint_mark = models.CharField("علامت ضرابخانه", max_length=50, blank=True)
    variety_code = models.CharField("کد گونه", max_length=80, blank=True)
    variety_description = models.TextField("تفاوت گونه", blank=True)
    description = models.TextField("داستان و توضیحات این نوبت ضرب", blank=True)
    finish = models.CharField(
        "پرداخت ضرب", max_length=20, choices=Finish.choices, default=Finish.UNKNOWN
    )
    mintage = models.PositiveBigIntegerField(
        "تیراژ", null=True, blank=True, validators=[MinValueValidator(1)]
    )
    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "نوبت یا گونه ضرب"
        verbose_name_plural = "نوبت‌ها و گونه‌های ضرب"
        indexes = [
            models.Index(fields=["calendar", "year"], name="coin_issue_calendar_year")
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(date_status="known", year__isnull=False)
                    | (~Q(date_status="known") & Q(year__isnull=True))
                ),
                name="coin_issue_date_consistent",
            ),
            models.CheckConstraint(
                condition=Q(gregorian_year_start__isnull=True)
                | Q(gregorian_year_end__isnull=True)
                | Q(gregorian_year_end__gte=F("gregorian_year_start")),
                name="coin_issue_greg_year_order",
            ),
        ]

    def __str__(self):
        return f"{self.coin_type} / {self.year if self.year is not None else self.get_date_status_display()} / {self.mint_mark} {self.variety_code} {self.get_finish_display()}"

    def clean(self):
        super().clean()
        if self.coin_type_id:
            coin = self.coin_type
            if self.calendar != coin.calendar:
                raise ValidationError({"calendar": "تقویم باید با نوع سکه یکسان باشد."})
            if self.year is not None and (
                (coin.year_start is not None and self.year < coin.year_start)
                or (coin.year_end is not None and self.year > coin.year_end)
            ):
                raise ValidationError(
                    {"year": "سال خارج از بازه تولید این نوع سکه است."}
                )
            duplicate = CoinIssue.objects.filter(
                coin_type_id=self.coin_type_id,
                year=self.year,
                calendar=self.calendar,
                date_status=self.date_status,
                mint_id=self.mint_id,
                mint_mark=self.mint_mark,
                variety_code=self.variety_code,
                finish=self.finish,
            ).exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError(
                    "این نوبت ضرب قبلاً ثبت شده است؛ از همان رکورد استفاده کنید."
                )
        if self.pk:
            for item in self.pack_items.select_related("pack_variant__pack"):
                item.validate_issue(self)


class CoinCatalogReference(ValidatedModel):
    coin_type = models.ForeignKey(
        CoinType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="references",
        verbose_name="نوع سکه",
    )
    issue = models.ForeignKey(
        CoinIssue,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="references",
        verbose_name="نوبت ضرب",
    )
    catalog = models.CharField("مرجع (KM، UC و...)", max_length=80)
    number = models.CharField("شماره مرجع", max_length=100)
    url = models.URLField("لینک", max_length=500, blank=True)
    notes = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "مرجع کاتالوگی"
        verbose_name_plural = "مراجع کاتالوگی"
        constraints = [
            models.CheckConstraint(
                condition=Q(coin_type__isnull=False, issue__isnull=True)
                | Q(coin_type__isnull=True, issue__isnull=False),
                name="coin_reference_one_target",
            ),
            models.UniqueConstraint(
                fields=["coin_type", "catalog", "number"],
                name="coin_type_reference_unique",
            ),
            models.UniqueConstraint(
                fields=["issue", "catalog", "number"],
                name="coin_issue_reference_unique",
            ),
        ]

    def __str__(self):
        return f"{self.catalog} #{self.number}"


class CoinSpecimen(ValidatedModel):
    catalog_link = models.BooleanField(default=False, editable=False)

    is_published = models.BooleanField(
        "منتشرشده برای فروش", default=False, db_index=True
    )
    issue = models.ForeignKey(
        CoinIssue,
        on_delete=models.PROTECT,
        related_name="specimens",
        verbose_name="نوبت ضرب",
    )
    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="coin_specimen",
        verbose_name="واریانت فروش",
    )
    sale_mode = models.CharField(
        "نحوه عرضه", max_length=20, choices=SaleMode.choices, default=SaleMode.UNIQUE
    )
    condition_grade = models.CharField(
        "حفظ‌شدگی", max_length=20, choices=Condition.choices, default=Condition.UNKNOWN
    )
    condition_notes = models.TextField("توضیح حفظ‌شدگی", blank=True)
    cleaned = models.BooleanField("تمیزشده", null=True, blank=True)
    scratched = models.BooleanField("خط‌وخش", null=True, blank=True)
    corroded = models.BooleanField("خوردگی", null=True, blank=True)
    edge_damaged = models.BooleanField("ضربه لبه", null=True, blank=True)
    holed = models.BooleanField("سوراخ‌شده پس از ضرب", null=True, blank=True)
    bent = models.BooleanField("خمیدگی", null=True, blank=True)
    repaired = models.BooleanField("تعمیرشده", null=True, blank=True)
    defect_notes = models.TextField("شرح ایرادها", blank=True)
    patina_description = models.TextField("پتینه", blank=True)
    mint_error_description = models.TextField("خطای ضرب", blank=True)
    authenticity_notes = models.TextField("شرح بررسی اصالت", blank=True)
    grading_company = models.CharField("مؤسسه ارزیابی", max_length=100, blank=True)
    certification_number = models.CharField("شماره گواهی", max_length=100, blank=True)
    certification_url = models.URLField("لینک بررسی گواهی", max_length=500, blank=True)
    grading_designation = models.CharField(
        "عنوان درجه گواهی (MS، PF و...)", max_length=30, blank=True
    )
    numeric_grade = models.PositiveSmallIntegerField(
        "درجه عددی (۱ تا ۷۰)",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(70)],
    )
    measured_weight_g = measure("وزن اندازه‌گیری‌شده (گرم)")
    measured_diameter_mm = measure("قطر اندازه‌گیری‌شده (میلی‌متر)")
    measured_thickness_mm = measure("ضخامت اندازه‌گیری‌شده (میلی‌متر)")
    storage_location = models.CharField("محل نگهداری", max_length=160, blank=True)
    packaging = models.CharField("بسته‌بندی", max_length=160, blank=True)

    class Meta:
        verbose_name = "نمونه سکه قابل فروش"
        verbose_name_plural = "نمونه‌های سکه قابل فروش"

    def __str__(self):
        return f"{self.variant.sku} / {self.issue}"

    def clean(self):
        super().clean()
        if self.is_published:
            from .services import readiness_errors

            errors = readiness_errors(self)
            if errors:
                raise ValidationError({"is_published": errors})
        if self.variant_id:
            if CoinPackVariant.objects.filter(variant_id=self.variant_id).exists():
                raise ValidationError({"variant": "این واریانت متعلق به پک است."})
            if CoinPack.objects.filter(product_id=self.variant.product_id).exists():
                raise ValidationError(
                    {"variant": "محصول پک نباید برای سکه تکی استفاده شود."}
                )
            if self.sale_mode == SaleMode.UNIQUE and self.variant.stock > 1:
                raise ValidationError(
                    {"sale_mode": "موجودی نمونه اختصاصی نباید بیشتر از یک باشد."}
                )
        if (
            self.certification_number
            or self.numeric_grade is not None
            or self.grading_designation
        ) and not self.grading_company:
            raise ValidationError(
                {"grading_company": "مؤسسه صادرکننده درجه یا گواهی را مشخص کنید."}
            )
        if self.sale_mode == SaleMode.SIMILAR and self.certification_number:
            raise ValidationError(
                {"sale_mode": "نمونه دارای گواهی اختصاصی باید تکی باشد."}
            )


class CoinPack(ValidatedModel):
    """Ready-made stock only. Items describe contents, not live loose-coin stock."""

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="coin_pack",
        verbose_name="محصول پک",
    )
    year = models.IntegerField("سال پک", db_index=True)
    calendar = models.CharField(
        "تقویم", max_length=20, choices=Calendar.choices, default=Calendar.SOLAR_HIJRI
    )
    calendar_notes = models.CharField("توضیح تقویم", max_length=160, blank=True)
    issuer = models.ForeignKey(
        CoinIssuer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="packs",
        verbose_name="صادرکننده (خالی: چند کشور)",
    )
    is_complete = models.BooleanField("مجموعه کامل طبق تعریف", default=False)
    completeness_scope = models.TextField(
        "تعریف مجموعه کامل",
        blank=True,
        help_text="مثلاً تمام ارزش‌های اسمی رایج این کشور در این سال؛ واریته‌ها شامل هستند یا خیر.",
    )
    packaging = models.CharField("نوع بسته‌بندی", max_length=160, blank=True)
    description = models.TextField("توضیحات پک", blank=True)

    class Meta:
        verbose_name = "پک سکه آماده"
        verbose_name_plural = "پک‌های سکه آماده"
        constraints = [
            models.CheckConstraint(
                condition=Q(is_complete=False) | ~Q(completeness_scope=""),
                name="coin_pack_complete_scope",
            )
        ]

    def __str__(self):
        return str(self.product)

    def clean(self):
        super().clean()
        if self.is_complete and not self.completeness_scope.strip():
            raise ValidationError(
                {"completeness_scope": "تعریف مجموعه کامل الزامی است."}
            )
        if (
            self.product_id
            and CoinSpecimen.objects.filter(
                variant__product_id=self.product_id
            ).exists()
        ):
            raise ValidationError({"product": "این محصول دارای نمونه سکه تکی است."})
        if self.pk:
            for pv in self.pack_variants.select_related("variant"):
                if pv.variant.product_id != self.product_id:
                    raise ValidationError(
                        {"product": "واریانت‌های پک به محصول قبلی متصل هستند."}
                    )
            for item in CoinPackItem.objects.filter(
                pack_variant__pack=self
            ).select_related("issue__coin_type"):
                item.validate_issue(item.issue, pack=self)


class CoinPackVariant(ValidatedModel):
    is_published = models.BooleanField(
        "منتشرشده برای فروش", default=False, db_index=True
    )
    pack = models.ForeignKey(
        CoinPack,
        on_delete=models.PROTECT,
        related_name="pack_variants",
        verbose_name="پک",
    )
    variant = models.OneToOneField(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="coin_pack_variant",
        verbose_name="واریانت فروش پک",
    )
    sale_mode = models.CharField(
        "نحوه عرضه", max_length=20, choices=SaleMode.choices, default=SaleMode.SIMILAR
    )
    condition_notes = models.TextField("شرح کیفیت اجزای این نسخه", blank=True)
    storage_location = models.CharField("محل نگهداری", max_length=160, blank=True)
    packaging_notes = models.TextField("تفاوت بسته‌بندی این نسخه", blank=True)

    class Meta:
        verbose_name = "نسخه قابل فروش پک"
        verbose_name_plural = "نسخه‌های قابل فروش پک"

    @property
    def coin_count(self):
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    def __str__(self):
        return f"{self.variant.sku} / {self.pack}"

    def clean(self):
        super().clean()
        if self.is_published:
            from .services import readiness_errors

            errors = readiness_errors(self)
            if errors:
                raise ValidationError({"is_published": errors})
        if (
            self.pack_id
            and self.variant_id
            and self.variant.product_id != self.pack.product_id
        ):
            raise ValidationError(
                {"variant": "واریانت باید متعلق به محصول همین پک باشد."}
            )
        if (
            self.variant_id
            and CoinSpecimen.objects.filter(variant_id=self.variant_id).exists()
        ):
            raise ValidationError({"variant": "این واریانت به سکه تکی متصل است."})
        if (
            self.variant_id
            and self.sale_mode == SaleMode.UNIQUE
            and self.variant.stock > 1
        ):
            raise ValidationError(
                {"sale_mode": "موجودی پک اختصاصی نباید بیشتر از یک باشد."}
            )
        if self.pk and self.pack_id:
            for item in self.items.select_related("issue__coin_type"):
                item.validate_issue(item.issue, pack=self.pack)


class CoinPackItem(ValidatedModel):
    pack_variant = models.ForeignKey(
        CoinPackVariant,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="نسخه پک",
    )
    issue = models.ForeignKey(
        CoinIssue,
        on_delete=models.PROTECT,
        related_name="pack_items",
        verbose_name="سکه داخل پک",
    )
    quantity = models.PositiveSmallIntegerField(
        "تعداد در هر پک", default=1, validators=[MinValueValidator(1)]
    )
    condition_grade = models.CharField(
        "حفظ‌شدگی این جزء",
        max_length=20,
        choices=Condition.choices,
        default=Condition.UNKNOWN,
    )
    notes = models.TextField("شرح کیفیت و ایرادهای این جزء", blank=True)
    position = models.PositiveSmallIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "جزء پک"
        verbose_name_plural = "اجزای پک"
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["pack_variant", "issue"], name="coin_pack_issue_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="coin_pack_item_positive"
            ),
        ]

    def __str__(self):
        return f"{self.issue} × {self.quantity}"

    def validate_issue(self, issue, pack=None):
        pack = pack or self.pack_variant.pack
        if (
            issue.date_status != CoinIssue.DateStatus.KNOWN
            or issue.year != pack.year
            or issue.calendar != pack.calendar
        ):
            raise ValidationError(
                {"issue": "سال و تقویم سکه باید دقیقاً با پک یکسان باشد."}
            )
        if pack.issuer_id and issue.coin_type.issuer_id != pack.issuer_id:
            raise ValidationError({"issue": "صادرکننده سکه با پک یکسان نیست."})

    def clean(self):
        super().clean()
        if self.pack_variant_id and self.pack_variant.assemblies.exists():
            previous = (
                type(self).objects.filter(pk=self.pk).first() if self.pk else None
            )
            if previous is None or any(
                getattr(previous, key) != getattr(self, key)
                for key in (
                    "pack_variant_id",
                    "issue_id",
                    "quantity",
                    "condition_grade",
                    "notes",
                )
            ):
                raise ValidationError(
                    "محتویات نسخه‌ای که پک آن آماده شده قابل تغییر نیست؛ نسخه جدید بسازید."
                )

        # Inline forms may hold an unsaved parent object with no primary key yet.
        has_parent = self.pack_variant_id or "pack_variant" in self._state.fields_cache
        if has_parent and self.issue_id:
            self.validate_issue(self.issue)


class CoinImageDetail(ValidatedModel):
    """Use the existing product variant image; no duplicate file storage."""

    class View(models.TextChoices):
        OBVERSE = "obverse", "روی سکه"
        REVERSE = "reverse", "پشت سکه"
        EDGE = "edge", "لبه"
        DETAIL = "detail", "جزئیات یا ایراد"
        PACK = "pack", "نمای پک"
        CERTIFICATE = "certificate", "گواهی"

    image = models.OneToOneField(
        "products.ProductVariantImage",
        on_delete=models.CASCADE,
        related_name="coin_detail",
        verbose_name="تصویر واریانت",
    )
    view_type = models.CharField("نمای تصویر", max_length=20, choices=View.choices)
    pack_item = models.ForeignKey(
        CoinPackItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="image_details",
        verbose_name="جزء پک (اختیاری)",
    )
    caption = models.CharField("شرح", max_length=255, blank=True)
    position = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "مشخصات تصویر سکه یا پک"
        verbose_name_plural = "مشخصات تصاویر سکه و پک"
        ordering = ["position", "pk"]

    def __str__(self):
        return self.get_view_type_display()

    def clean(self):
        super().clean()
        if self.image_id:
            variant_id = self.image.variant_id
            if not (
                CoinSpecimen.objects.filter(variant_id=variant_id).exists()
                or CoinPackVariant.objects.filter(variant_id=variant_id).exists()
            ):
                raise ValidationError(
                    {"image": "تصویر باید متعلق به یک سکه یا پک ثبت‌شده باشد."}
                )
            if (
                self.pack_item_id
                and self.pack_item.pack_variant.variant_id != variant_id
            ):
                raise ValidationError(
                    {"pack_item": "جزء پک باید متعلق به واریانت تصویر باشد."}
                )


class PackAssembly(ValidatedModel):
    """Immutable audit event for moving loose internal inventory into ready packs."""

    request_key = models.CharField("کلید یکتای عملیات", max_length=100, unique=True)
    payload_hash = models.CharField(max_length=64, editable=False)
    pack_variant = models.ForeignKey(
        CoinPackVariant, on_delete=models.PROTECT, related_name="assemblies"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_cost = models.DecimalField(max_digits=16, decimal_places=0)
    contents_snapshot = models.JSONField(default=dict)
    output_lots = models.ManyToManyField(
        "inventory.InventoryLot", related_name="coin_assemblies"
    )

    class Meta:
        verbose_name = "عملیات آماده‌سازی پک"
        verbose_name_plural = "عملیات آماده‌سازی پک"


class PackAssemblyAllocation(ValidatedModel):
    assembly = models.ForeignKey(
        PackAssembly, on_delete=models.PROTECT, related_name="allocations"
    )
    item = models.ForeignKey(CoinPackItem, on_delete=models.PROTECT)
    source_variant = models.ForeignKey(
        "products.ProductVariant", on_delete=models.PROTECT
    )
    source_lot = models.ForeignKey("inventory.InventoryLot", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=14, decimal_places=0)

    class Meta:
        verbose_name = "مصرف سکه برای پک"
        verbose_name_plural = "مصرف سکه برای پک"


class CoinCatalogImage(ValidatedModel):
    coin_type = models.ForeignKey(
        CoinType,
        on_delete=models.CASCADE,
        related_name="catalog_images",
        verbose_name="نوع سکه",
    )
    issue = models.ForeignKey(
        CoinIssue,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="catalog_images",
        verbose_name="نوبت ضرب (اختیاری)",
    )
    image = models.ImageField(
        "تصویر مرجع", upload_to="coins/catalog/%Y/%m/", blank=True
    )
    source_url = models.URLField("نشانی تصویر", blank=True)
    view_type = models.CharField(
        "نما",
        max_length=20,
        choices=[
            ("obverse", "رو"),
            ("reverse", "پشت"),
            ("edge", "لبه"),
            ("detail", "جزئیات"),
        ],
        default="obverse",
    )
    caption = models.CharField("عنوان تصویر", max_length=250, blank=True)
    credit = models.CharField("منبع یا صاحب تصویر", max_length=250, blank=True)
    position = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["position", "pk"]
        verbose_name = "تصویر مرجع کاتالوگ"
        verbose_name_plural = "تصاویر مرجع کاتالوگ"

    def clean(self):
        super().clean()
        if not self.image and not self.source_url:
            raise ValidationError("فایل تصویر یا نشانی آن را وارد کنید.")
        if self.issue_id and self.issue.coin_type_id != self.coin_type_id:
            raise ValidationError({"issue": "نوبت ضرب متعلق به این سکه نیست."})

    def __str__(self):
        return self.caption or str(self.coin_type)
