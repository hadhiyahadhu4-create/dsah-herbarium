import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herbarium_project.settings')
django.setup()

from plants.models import Plant

def import_data(file_path):
    print("Deleting all current data...")
    count, _ = Plant.objects.all().delete()
    print(f"Deleted {count} existing records.")

    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.upper()
    df = df.fillna('')
    
    plants_to_create = []
    
    for index, row in df.iterrows():
        raw_name = str(row.get('PLANT NAME WITH AUTHOR CITATION', '')).strip()
        name_parts = raw_name.split(',', 1)
        name = name_parts[0].strip()
        author = name_parts[1].strip() if len(name_parts) > 1 else ''

        raw_date = row.get('DATE OF COLLECTION', '')
        if hasattr(raw_date, 'strftime'):
            date_str = raw_date.strftime('%Y-%m-%d')
        else:
            date_str = str(raw_date).strip()

        locality = str(row.get('LOCALITY', '')).strip()
        state = str(row.get('STATE', '')).strip()
        if state:
            locality = f"{locality}, {state}" if locality else state

        barcode = str(row.get('BARCODE', '')).strip()

        if barcode:
            plant = Plant(
                name=name,
                scientific_name=name,
                author=author,
                family=str(row.get('FAMILY', '')).strip(),
                genus=str(row.get('GENUS', '')).strip(),
                collection_number=str(row.get('COLLECTION NUMBER', '')).strip(),
                collector=str(row.get('COLLECTOR', '')).strip(),
                date_of_collection=date_str,
                locality=locality,
                district=str(row.get('DISTRICT', '')).strip(),
                country=str(row.get('COUNTRY', '')).strip(),
                altitude=str(row.get('ALTITUDE', '')).strip(),
                habit=str(row.get('HABIT', '')).strip(),
                habitat=str(row.get('HABITAT', '')).strip(),
                barcode=barcode
            )
            plants_to_create.append(plant)
            
    if plants_to_create:
        Plant.objects.bulk_create(plants_to_create, ignore_conflicts=True)
        print(f"Successfully processed {len(plants_to_create)} records (duplicates skipped).")
    else:
        print("No valid new records found to import.")

if __name__ == '__main__':
    import_data('new_data.xlsx')
