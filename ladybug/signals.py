from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

from .models import *

def delete_image_file(sender, instance, **kwargs):
    if hasattr(instance, 'image'):
        image_field = getattr(instance, 'image')
        if image_field and hasattr(image_field, 'path') and os.path.isfile(image_field.path):
            os.remove(image_field.path)

for model in [Fabric, Pattern, Product, CarouselImage, ProductImage, PatternImage, FabricImage, MeasurementField,
              Category, ProductReview, cardImages]:
    post_delete.connect(delete_image_file, sender=model)

