import os
import re
import sys
import zipfile
import shutil
import pandas as pd
import django
from django.core.files import File

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herbarium_project.settings')
django.setup()

from plants.models import Plant

def clean_digits(barcode_str):
    """Extract only digits from a string and return as an integer. Returns None if no digits found."""
    digits = re.sub(r'\D', '', str(barcode_str))
    return int(digits) if digits else None

def run_import_pipeline(excel_path=None, zip_path=None, clear_db=True):
    print("=" * 60)
    print("         HERBARIUM DATA & IMAGE IMPORT PIPELINE         ")
    print("=" * 60)
    
    # 1. Auto-detect files if paths are not provided
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not excel_path:
        xlsx_files = []
        for r, d, files in os.walk(current_dir):
            for f in files:
                if f.endswith('.xlsx') and not f.startswith('~$'):
                    xlsx_files.append(os.path.join(r, f))
                    
        if len(xlsx_files) == 1:
            excel_path = xlsx_files[0]
            print(f"Auto-detected Excel file: {os.path.basename(excel_path)}")
        elif len(xlsx_files) > 1:
            preferred = 'new_data.xlsx'
            found_pref = [p for p in xlsx_files if os.path.basename(p) == preferred]
            if found_pref:
                excel_path = found_pref[0]
                print(f"Auto-detected preferred Excel file: {preferred}")
            else:
                excel_path = xlsx_files[0]
                print(f"Auto-detected first Excel file: {os.path.basename(xlsx_files[0])} (Multiple found)")
        else:
            print("Error: No Excel (.xlsx) file found in the project directory!")
            return

    if not zip_path:
        zip_files = []
        for r, d, files in os.walk(current_dir):
            for f in files:
                if f.endswith('.zip'):
                    zip_files.append(os.path.join(r, f))
                    
        if len(zip_files) == 1:
            zip_path = zip_files[0]
            print(f"Auto-detected ZIP archive: {os.path.basename(zip_path)}")
        elif len(zip_files) > 1:
            preferred = 'plant_images.zip'
            found_pref = [z for z in zip_files if os.path.basename(z) == preferred]
            if found_pref:
                zip_path = found_pref[0]
                print(f"Auto-detected preferred ZIP archive: {preferred}")
            else:
                zip_path = zip_files[0]
                print(f"Auto-detected first ZIP archive: {os.path.basename(zip_files[0])} (Multiple found)")
        else:
            print("Warning: No images ZIP archive (.zip) found. Images will not be imported.")

    # 2. Clear Database if requested
    if clear_db:
        print("\n[1/5] Clearing all existing database records...")
        count, _ = Plant.objects.all().delete()
        print(f"      Deleted {count} existing records successfully.")
    else:
        print("\n[1/5] Skipping database clear. Appending new records.")

    # 3. Read & Import Excel Records
    print("\n[2/5] Reading and importing Excel data...")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"      Error reading Excel file: {e}")
        return

    # Standardize column names to uppercase for robust matching
    df.columns = df.columns.str.upper().str.strip()
    df = df.fillna('')

    plants_to_create = []
    skipped_rows = 0
    total_rows = len(df)

    print(f"      Processing {total_rows} rows from Excel...")
    for index, row in df.iterrows():
        # Clean and split Name and Author from column
        raw_name = str(row.get('PLANT NAME WITH AUTHOR CITATION', row.get('SPECIES NAME', row.get('NAME', '')))).strip()
        if not raw_name:
            skipped_rows += 1
            continue

        name_parts = raw_name.split(',', 1)
        name = name_parts[0].strip()
        author = name_parts[1].strip() if len(name_parts) > 1 else ''

        # Handle Date conversion
        raw_date = row.get('DATE OF COLLECTION', '')
        if hasattr(raw_date, 'strftime'):
            date_str = raw_date.strftime('%Y-%m-%d')
        else:
            date_str = str(raw_date).strip()

        # Handle Locality & State joining
        locality = str(row.get('LOCALITY', '')).strip()
        state = str(row.get('STATE', '')).strip()
        if state:
            locality = f"{locality}, {state}" if locality else state

        barcode = str(row.get('BARCODE', '')).strip()
        if not barcode:
            skipped_rows += 1
            continue

        # Map to Plant Model Instance
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
        # bulk_create is extremely fast for 8000+ records
        # ignore_conflicts=True skips duplicates if barcode unique constraint is violated
        created_plants = Plant.objects.bulk_create(plants_to_create, ignore_conflicts=True)
        print(f"      Successfully imported {Plant.objects.count()} records.")
        if skipped_rows:
            print(f"      Skipped {skipped_rows} invalid rows (missing name or barcode).")
    else:
        print("      Error: No valid new records found in Excel.")
        return

    # 4. Detect or Extract Images Folder
    image_folder_path = None
    is_temp_extract = False
    
    if zip_path:
        print("\n[3/5] Extracting ZIP images to temporary folder...")
        temp_extract_dir = os.path.join(current_dir, 'temp_plant_images')
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        os.makedirs(temp_extract_dir)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            print("      Extraction completed successfully.")
            image_folder_path = temp_extract_dir
            is_temp_extract = True
        except Exception as e:
            print(f"      Error extracting ZIP file: {e}")
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            return
    else:
        print("\n[3/5] No ZIP archive found. Scanning recursively for pre-extracted images directory...")
        exclude_dirs = {'plants', 'static', 'templates', 'staticfiles', '.venv', 'venv', 'env', '__pycache__', '.git'}
        detected_folders = []
        for r, d, files in os.walk(current_dir):
            # Check if this folder or its parents should be excluded
            parts = r.replace(current_dir, '').split(os.sep)
            if any(part in exclude_dirs for part in parts if part):
                continue
            # If this folder contains actual image files, it's a strong candidate!
            img_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if len(img_files) > 10:
                detected_folders.append((r, len(img_files)))
                
        if detected_folders:
            # Sort by number of images descending to get the largest repository
            detected_folders.sort(key=lambda x: x[1], reverse=True)
            image_folder_path = detected_folders[0][0]
            print(f"      Auto-detected images folder: {os.path.relpath(image_folder_path, current_dir)} ({detected_folders[0][1]} images found)")
        else:
            print("      Warning: No extracted images folder or ZIP archive detected. Images will not be imported.")
            image_folder_path = None

    # 5. Precise In-Memory Image Mapping
    if image_folder_path:
        print("\n[4/5] Pre-computing precise barcode lookup tables...")
        # Create fast dictionaries for O(1) matching:
        # A map of full lowercase barcode -> Plant
        barcode_to_plant = {}
        # A map of exact digit value -> list of Plants (handles leading zeroes, STC10 vs 10)
        digits_to_plants = {}

        all_plants = Plant.objects.all()
        for p in all_plants:
            bc = p.barcode.strip()
            barcode_to_plant[bc.lower()] = p
            
            d_val = clean_digits(bc)
            if d_val is not None:
                if d_val not in digits_to_plants:
                    digits_to_plants[d_val] = []
                digits_to_plants[d_val].append(p)

        print("      Running exact mapping and resizing...")
        mapped_count = 0
        unmapped_files = []
        ambiguous_files = []
        error_count = 0
        
        # Scan images
        for root, dirs, files in os.walk(image_folder_path):
            for filename in files:
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    continue

                image_name_raw = os.path.splitext(filename)[0].strip()
                
                # Step 5a: Try direct exact match on barcode (case-insensitive)
                plant = barcode_to_plant.get(image_name_raw.lower())
                
                # Step 5b: Try matching exact numeric digit values if no direct match
                if not plant:
                    img_digit_val = clean_digits(image_name_raw)
                    if img_digit_val is not None:
                        matches = digits_to_plants.get(img_digit_val, [])
                        if len(matches) == 1:
                            plant = matches[0]
                        elif len(matches) > 1:
                            # Ambiguous match (multiple plants share this digit ID)
                            ambiguous_files.append((filename, [p.barcode for p in matches]))
                            continue
                
                if plant:
                    try:
                        image_path = os.path.join(root, filename)
                        with open(image_path, 'rb') as f:
                            # Django model auto-compresses to WebP and resizes on save()!
                            plant.image.save(filename, File(f), save=True)
                        mapped_count += 1
                        if mapped_count % 100 == 0:
                            print(f"      Successfully mapped and compressed {mapped_count} images...")
                    except Exception as e:
                        print(f"      Error processing image {filename}: {e}")
                        error_count += 1
                else:
                    unmapped_files.append(filename)

        print(f"      Finished image mapping.")
        print(f"      Successful: {mapped_count} images.")
        if error_count:
            print(f"      Errors: {error_count} images.")
        if unmapped_files:
            print(f"      Unmapped files: {len(unmapped_files)} (no matching database barcode)")
        if ambiguous_files:
            print(f"      Ambiguous files: {len(ambiguous_files)} (multiple candidate database barcodes)")

        # 6. Clean up temporary extraction workspace (ONLY if it was dynamically extracted from a ZIP)
        if is_temp_extract and os.path.exists(image_folder_path):
            print("\n[5/5] Cleaning up temporary workspace...")
            try:
                shutil.rmtree(image_folder_path)
                print("      Temporary files cleared cleanly.")
            except Exception as e:
                print(f"      Warning: Clean up encountered an issue: {e}")
        else:
            print("\n[5/5] Cleanup not required (using pre-extracted folder).")
    else:
        print("\n[4/5] Skipping image mapping (No ZIP archive or pre-extracted folder found).")
        print("\n[5/5] Workspace cleanup not required.")

    # Final Report
    print("=" * 60)
    print("                     IMPORT SUMMARY                     ")
    print("=" * 60)
    print(f"  Total Imported Database Records: {Plant.objects.count()}")
    if image_folder_path:
        print(f"  Successfully Mapped Images:     {mapped_count}")
        print(f"  Unmapped Images:                {len(unmapped_files)}")
        print(f"  Ambiguous Matches:              {len(ambiguous_files)}")
    print("=" * 60)
    print("Pipeline executed successfully! All files are thoroughly aligned.")
    print("=" * 60)

if __name__ == '__main__':
    run_import_pipeline()
