"""Resolve public coin destinations once per product response, using sale rules."""
from urllib.parse import quote


class ProductStorefrontMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        product = getattr(instance, "product", instance)
        target = self._destinations().get(product.pk)
        data["storefront"] = target
        if target and "variants" in data:
            by_id = {str(row["id"]): row for row in data["variants"]}
            data["variants"] = [by_id[key] for key in target["variants"] if key in by_id]
            if data["variants"]:
                primary = data["variants"][0]
                data["price"] = primary["price"]
                data["discount_price"] = primary["discount_price"]
                data["in_stock"] = any(row["stock"] > 0 for row in data["variants"])
                if "quantity" in data:
                    data["quantity"] = sum(row["stock"] for row in data["variants"])
                images = primary.get("images", [])
                image = next((row for row in images if row["is_main"]), None) or next(iter(images), None)
                if image and "thumb" in data:
                    data["thumb"] = image["image"] or image["source_url"]
        return data

    def _destinations(self):
        cache_owner = self.parent if getattr(self.parent, "many", False) else self
        if hasattr(cache_owner, "_coin_destinations"):
            return cache_owner._coin_destinations
        items = getattr(cache_owner, "instance", None)
        if items is None:
            items = [self.instance] if self.instance is not None else []
        elif not getattr(cache_owner, "many", False):
            items = [items]
        ids = [getattr(item, "product", item).pk for item in items]
        from .models import CoinSpecimen, CoinPackVariant
        from .api.views import sales

        result = {}
        for model, kind in ((CoinSpecimen, "coin"), (CoinPackVariant, "pack")):
            rows = sales(model.objects.filter(variant__product_id__in=ids))
            rows = rows.order_by("-available_stock", "variant_id")
            if kind == "coin":
                rows = rows.select_related("issue__coin_type", "variant__product")
            else:
                rows = rows.select_related("pack__product", "variant__product")
            for row in rows:
                slug = row.issue.coin_type.slug if kind == "coin" else row.pack.product.slug
                path = "/coins/" if kind == "coin" else "/coin-packs/"
                url = path + quote(slug, safe="") + "?variant=" + str(row.variant_id)
                if kind == "coin":
                    url += "&issue=" + str(row.issue_id)
                target = result.setdefault(row.variant.product_id, {
                    "kind": kind, "url": url, "variants": {}
                })
                target["variants"][str(row.variant_id)] = url
        cache_owner._coin_destinations = result
        return result
