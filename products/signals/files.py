from django.db.models.signals import post_delete
from django.dispatch import receiver

from products.models import (
    Category,
    ProductImage,
    ProductVariantImage,
    ProductVideo,
)


@receiver(post_delete, sender=Category)
def delete_category_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=ProductImage)
def delete_product_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=ProductVariantImage)
def delete_variant_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=ProductVideo)
def delete_product_video(sender, instance, **kwargs):
    if instance.video:
        instance.video.delete(save=False)