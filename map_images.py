import os
import django
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herbarium_project.settings')
django.setup()

from plants.models import Plant

def map_images(base_folder):
    if not os.path.exists(base_folder):
        print(f"Folder {base_folder} does not exist.")
        return

    count = 0
    for root, dirs, files in os.walk(base_folder):
        for image_name in files:
            if not image_name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
                
            barcode = os.path.splitext(image_name)[0].strip()
            
            try:
                # Extract only digits from the image name
                import re
                digits = re.sub(r'\D', '', barcode)
                
                # Find the plant that contains exactly these digits
                plant = Plant.objects.filter(barcode__contains=digits).first()
                
                if plant:
                    image_path = os.path.join(root, image_name)
                    with open(image_path, 'rb') as f:
                        plant.image.save(image_name, File(f), save=True)
                    count += 1
                    if count % 100 == 0:
                        print(f"Mapped and compressed {count} images...")
                else:
                    print(f"No plant found matching digits: '{digits}'")
            except Exception as e:
                print(f"Error processing {image_name}: {e}")
                
    print(f"Finished! Successfully mapped and compressed {count} images.")

if __name__ == '__main__':
    map_images('plant_images')
