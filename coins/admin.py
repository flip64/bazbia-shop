from django.contrib import admin
from . import models as m


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 50
    show_full_result_count = False
    save_on_top = True
    readonly_fields = ("created_at", "updated_at")


class NamedAdmin(BaseAdmin):
    search_fields = ("name", "name_en", "slug")
    list_display = ("name", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_en",)}


for model in (
    m.CoinIssuer,
    m.CoinMaterial,
    m.CoinMint,
    m.HistoricalPeriod,
    m.CoinTheme,
):
    admin.site.register(model, NamedAdmin)


@admin.register(m.CoinCurrency)
class CurrencyAdmin(NamedAdmin):
    autocomplete_fields = ("issuers",)


@admin.register(m.CoinRuler)
class RulerAdmin(NamedAdmin):
    filter_horizontal = ("periods",)


class CompositionInline(admin.TabularInline):
    model = m.CoinCompositionPart
    extra = 0
    autocomplete_fields = ("material",)


@admin.register(m.CoinType)
class TypeAdmin(BaseAdmin):
    search_fields = ("name", "slug", "denomination_label", "issuer__name")
    list_display = ("name", "issuer", "period", "construction", "shape")
    list_filter = ("issuer", "issue_kind", "construction", "shape", "calendar")
    autocomplete_fields = ("issuer", "period", "ruler", "currency", "themes")
    inlines = (CompositionInline,)


@admin.register(m.CoinIssue)
class IssueAdmin(BaseAdmin):
    search_fields = ("coin_type__name", "date_inscription", "mint_mark", "variety_code")
    list_display = ("coin_type", "year", "calendar", "mint", "mint_mark", "finish")
    list_filter = ("calendar", "date_status", "finish", "mint")
    autocomplete_fields = ("coin_type", "mint")


@admin.register(m.CoinCompositionPart)
class CompositionAdmin(BaseAdmin):
    search_fields = ("coin_type__name", "material__name")
    autocomplete_fields = ("coin_type", "material")


@admin.register(m.CoinCatalogReference)
class ReferenceAdmin(BaseAdmin):
    search_fields = ("catalog", "number", "coin_type__name", "issue__coin_type__name")
    autocomplete_fields = ("coin_type", "issue")


@admin.register(m.CoinSpecimen)
class SpecimenAdmin(BaseAdmin):
    search_fields = ("variant__sku", "variant__product__name", "certification_number")
    list_display = ("variant", "issue", "condition_grade", "sale_mode")
    list_filter = ("sale_mode", "condition_grade", "cleaned", "corroded")
    autocomplete_fields = ("issue", "variant")


@admin.register(m.CoinPack)
class PackAdmin(BaseAdmin):
    search_fields = ("product__name", "product__slug")
    list_display = ("product", "year", "calendar", "issuer", "is_complete")
    list_filter = ("calendar", "issuer", "is_complete")
    autocomplete_fields = ("product", "issuer")


class PackItemInline(admin.TabularInline):
    model = m.CoinPackItem
    extra = 0
    autocomplete_fields = ("issue",)


@admin.register(m.CoinPackVariant)
class PackVariantAdmin(BaseAdmin):
    search_fields = ("variant__sku", "pack__product__name")
    list_display = ("variant", "pack", "sale_mode", "coin_count")
    autocomplete_fields = ("pack", "variant")
    inlines = (PackItemInline,)


@admin.register(m.CoinPackItem)
class PackItemAdmin(BaseAdmin):
    search_fields = ("pack_variant__variant__sku", "issue__coin_type__name")
    autocomplete_fields = ("pack_variant", "issue")


@admin.register(m.CoinImageDetail)
class ImageDetailAdmin(BaseAdmin):
    search_fields = ("caption", "image__variant__sku")
    list_filter = ("view_type",)
    # ProductVariantImage is not registered in the existing admin.
    raw_id_fields = ("image",)
    autocomplete_fields = ("pack_item",)
