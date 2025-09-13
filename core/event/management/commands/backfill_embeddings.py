from django.core.management.base import BaseCommand
from event.models import VendorDis
from event.utils import get_image_embedding

class Command(BaseCommand):
    help = "Generate embeddings for vendors that don't have them yet"

    def handle(self, *args, **kwargs):
        vendors = VendorDis.objects.filter(image__isnull=False)
        total = vendors.count()
        updated = 0
        self.stdout.write(f"Found {total} vendors with images")

        for v in vendors:
            if not v.embedding or len(v.embedding) == 0:
                self.stdout.write(f"⚡ Processing: {v.vendor.business_name}")
                try:
                    embedding = get_image_embedding(v.image.path)
                    if embedding is not None and len(embedding) > 0:
                        v.embedding = embedding
                        v.save(update_fields=["embedding"])
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Saved embedding for {v.vendor.business_name}"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"❌ No embedding generated for {v.vendor.business_name}"
                        ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Failed for {v.vendor.business_name}: {e}"
                    ))

        self.stdout.write(self.style.SUCCESS(f"✨ Backfilled {updated} vendors"))
