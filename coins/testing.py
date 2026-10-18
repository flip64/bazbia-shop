"""Fixture helper: create usable tagged images and explicitly publish a listing."""


def publish_fixture(listing):
    from products.models import ProductVariantImage
    from .models import CoinImageDetail, CoinPackVariant
    from .services import set_publication

    targets = [(None, "obverse"), (None, "reverse")]
    if isinstance(listing, CoinPackVariant):
        targets = [(None, "pack")]
        for item in listing.items.all():
            targets.extend([(item, "obverse"), (item, "reverse")])
    for item, side in targets:
        if not CoinImageDetail.objects.filter(
            image__variant_id=listing.variant_id, view_type=side, pack_item=item
        ).exists():
            image = ProductVariantImage.objects.create(
                variant_id=listing.variant_id,
                source_url="https://example.com/fixture.jpg",
            )
            CoinImageDetail.objects.create(image=image, view_type=side, pack_item=item)
    set_publication(listing, True)
