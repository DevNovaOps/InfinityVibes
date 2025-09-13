from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import VendorDis
from .utils import get_image_embedding

@receiver(post_save, sender=VendorDis)
def generate_embedding(sender, instance, created, **kwargs):
    """
    Automatically generate and save an embedding whenever
    a VendorDis object with an image is created (or updated without embedding).
    """
    if instance.image and not instance.embedding:
        try:
            embedding = get_image_embedding(instance.image.path)
            if embedding:
                instance.embedding = embedding
                instance.save(update_fields=["embedding"])
                print("✅ Embedding saved for:", instance.vendor.business_name)
        except Exception as e:
            print("❌ Error generating embedding:", e)
