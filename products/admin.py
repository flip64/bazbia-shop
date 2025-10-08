from django.contrib import admin
from .models import (
    Product, ProductImage, ProductSpecification, ProductVariant,
    ProductVideo, Category, SpecialProduct, Attribute, AttributeValue
)

# ===========================
# Category Admin
# ===========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ('parent',)

# ===========================
# Product Admin
# ===========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_active', 'quantity', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}

# ===========================
# ProductSpecification Admin
# ===========================
@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value')
    search_fields = ('product__name', 'name', 'value')

# ===========================
# Attribute & AttributeValue Admin
# ===========================
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'attribute')
    search_fields = ('value', 'attribute__name')
    list_filter = ('attribute',)

# ===========================
# ProductVariant Admin
# ===========================
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'get_attributes', 'stock', 'low_stock_threshold', 'price', 'discount_price')
    search_fields = ('product__name', 'sku')
    list_filter = ('product',)
    filter_horizontal = ('attributes',)

    def get_attributes(self, obj):
        return ", ".join([f"{attr.attribute.name}: {attr.value}" for attr in obj.attributes.all()])
    get_attributes.short_description = "Attributes"

# ===========================
# ProductImage Admin
# ===========================
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'source_url', 'image')
    search_fields = ('product__name',)
    list_filter = ('is_main',)

# ===========================
# ProductVideo Admin
# ===========================
@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ('product', 'caption', 'video')
    search_fields = ('product__name', 'caption')

# ===========================
# SpecialProduct Admin
# ===========================
@admin.register(SpecialProduct)
class SpecialProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'start_date', 'end_date', 'is_active')
    search_fields = ('product__name', 'title')
    list_filter = ('is_active',)
