from django.db import models
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class Plant(models.Model):
    name = models.CharField(max_length=150, db_index=True)
    scientific_name = models.CharField(max_length=200)
    family = models.CharField(max_length=150, db_index=True)
    genus = models.CharField(max_length=150, db_index=True)
    barcode = models.CharField(max_length=100, unique=True)
    
    # Extended Metadata
    author = models.CharField(max_length=150, blank=True, null=True)
    collection_number = models.CharField(max_length=100, blank=True, null=True)
    collector = models.CharField(max_length=150, blank=True, null=True)
    date_of_collection = models.CharField(max_length=100, blank=True, null=True) # Using CharField for flexible date strings from excel
    locality = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=150, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    altitude = models.CharField(max_length=100, blank=True, null=True)
    habit = models.CharField(max_length=200, blank=True, null=True)
    habitat = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='plants/')

    def save(self, *args, **kwargs):
        # Automatically compress new images to WebP to keep file sizes ~30KB with high quality
        if self.image and not self.image.name.endswith('.webp'):
            img = Image.open(self.image)
            
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            # Resize image to max 800px width/height while maintaining aspect ratio
            max_size = (800, 800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as WebP
            output = BytesIO()
            # method=6 is highest compression effort for better quality/size ratio
            img.save(output, format='WEBP', quality=75, method=6)
            output.seek(0)
            
            # Update the image field with the new compressed WebP file
            file_name = self.image.name.split('.')[0]
            if '/' in file_name or '\\' in file_name:
                file_name = file_name.replace('\\', '/').split('/')[-1]
                
            self.image = InMemoryUploadedFile(
                output, 'ImageField', 
                f"{file_name}.webp", 
                'image/webp', 
                sys.getsizeof(output), None
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
