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
   try:
    if instance.image:
        instance.image.delete(save=False)
   except: 
    pass

@receiver(post_delete, sender=ProductImage)
def delete_product_image(sender, instance, **kwargs):
   try: 
    if instance.image:
        instance.image.delete(save=False)
   except: 
      pass 

def cleanup_variant_image_file(storage, name):
    """Delete only after commit, and retain files shared with the coin catalog."""
    from django.apps import apps
    from django.db import transaction

    def cleanup():
        if ProductVariantImage.objects.filter(image=name).exists():
            return
        if apps.is_installed("coins"):
            CatalogImage = apps.get_model("coins", "CoinCatalogImage")
            if CatalogImage.objects.filter(image=name).exists():
                return
        storage.delete(name)

    transaction.on_commit(cleanup)


@receiver(post_delete, sender=ProductVariantImage)
def delete_variant_image(sender, instance, **kwargs):
    if instance.image:
        cleanup_variant_image_file(instance.image.storage, instance.image.name)


@receiver(post_delete, sender=ProductVideo)
def delete_product_video(sender, instance, **kwargs):
   try:  
    if instance.video:
        instance.video.delete(save=False)
   except:
     pass 