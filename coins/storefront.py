"""Resolve public coin destinations once per product response, using sale rules."""
from urllib.parse import quote


class ProductStorefrontMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        product = getattr(instance, "product", instance)
        target = self._destinations().get(product.pk)
        data["storefront"] = target
        if target and target.get("label") and "name" in data:
            year = target.get("year")
            data["name"] = target["label"] + (f" · {year}" if year is not None else "")
        if target and target.get("catalog_only"):
            for key in ("price", "discount_price"):
                if key in data:
                    data[key] = None
            if "in_stock" in data:
                data["in_stock"] = False
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
                rows = rows.select_related("issue__coin_type__issuer", "variant__product")
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
                if kind == "coin":
                    target.setdefault("year", row.issue.year)
                    target.setdefault("issuer", row.issue.coin_type.issuer.name)
                    target.setdefault("label", row.issue.coin_type.name)
        # Catalog connections still have one canonical page when no public sale exists.
        links = CoinSpecimen.objects.filter(
            variant__product_id__in=ids, variant__product__is_active=True,
            issue__coin_type__is_published=True,
        ).select_related("issue__coin_type__issuer").order_by("pk")
        for row in links:
            coin = row.issue.coin_type
            result.setdefault(row.variant.product_id, {
                "kind": "coin",
                "url": "/coins/" + quote(coin.slug, safe="") + "?issue=" + str(row.issue_id),
                "variants": {}, "catalog_only": True,
                "year": row.issue.year, "issuer": coin.issuer.name, "label": coin.name,
            })
        cache_owner._coin_destinations = result
        return result
