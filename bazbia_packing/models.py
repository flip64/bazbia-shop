# bazbiapacking/models.py
from django.db import models

class ShippingBox(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="نام بسته پستی")
    length = models.FloatField(help_text="طول بسته به سانتیمتر")
    width = models.FloatField(help_text="عرض بسته به سانتیمتر")
    height = models.FloatField(help_text="ارتفاع بسته به سانتیمتر")
    max_weight = models.FloatField(help_text="حداکثر وزن مجاز به گرم", default=0)
    carton_weight = models.FloatField(help_text="وزن خود کارتن به گرم", default=0)
    carton_type = models.CharField(max_length=50, help_text="نوع کارتن (مثلاً استاندارد ایران)", default="استاندارد")

    def volume(self):
        """حجم بسته به سانتیمتر مکعب"""
        return self.length * self.width * self.height

    def __str__(self):
        return (
            f"{self.name} ({self.length}x{self.width}x{self.height} cm, "
            f"max {self.max_weight} g, carton {self.carton_weight} g, type: {self.carton_type})"
        )
