from django.contrib import admin

from .models import (
    ProductReview,
    ProductQuestion,
    ProductAnswer,
)


# =========================================================
# Product Review Admin
# =========================================================
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "user",
        "rating",
        "is_verified_purchase",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "rating",
        "is_verified_purchase",
        "created_at",
    )

    search_fields = (
        "product__name",
        "user__username",
        "title",
        "body",
    )

    readonly_fields = (
        "is_verified_purchase",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "product",
        "user",
    )


# =========================================================
# Product Question Admin
# =========================================================
@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "user",
        "short_body",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "product__name",
        "user__username",
        "body",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "product",
        "user",
    )

    @admin.display(description="سؤال")
    def short_body(self, obj):
        if len(obj.body) <= 80:
            return obj.body

        return f"{obj.body[:80]}..."


# =========================================================
# Product Answer Admin
# =========================================================
@admin.register(ProductAnswer)
class ProductAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "user",
        "short_body",
        "is_verified_purchase",
        "is_official",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "is_verified_purchase",
        "is_official",
        "created_at",
    )

    search_fields = (
        "question__body",
        "question__product__name",
        "user__username",
        "body",
    )

    readonly_fields = (
        "is_verified_purchase",
        "is_official",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "question",
        "question__product",
        "user",
    )

    @admin.display(description="پاسخ")
    def short_body(self, obj):
        if len(obj.body) <= 80:
            return obj.body

        return f"{obj.body[:80]}..."