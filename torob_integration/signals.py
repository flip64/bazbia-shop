from django.db.models.signals import post_save
from django.dispatch import receiver

from products.models import ProductVariant
from torob_integration.models import TorobVariantConfig


@receiver(post_save, sender=ProductVariant)
def create_torob_config_for_variant(sender, instance, created, **kwargs):
    if created:
        TorobVariantConfig.objects.get_or_create(
            variant=instance,
        )
