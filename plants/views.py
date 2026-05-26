from django.shortcuts import render
from django.http import JsonResponse
from .models import Plant

def home(request):
    return render(request, 'index.html', {
        'total_specimens': Plant.objects.count(),
        'total_families': 124,
        'total_genus': 226,
    })

def search_plants(request):
    barcode = request.GET.get('barcode', '').strip()
    scientific_name = request.GET.get('scientific_name', '').strip()
    family = request.GET.get('family', '').strip()
    collector = request.GET.get('collector', '').strip()
    region = request.GET.get('region', '').strip()
    year = request.GET.get('year', '').strip()

    plants = Plant.objects.all()

    if barcode:
        plants = plants.filter(barcode__icontains=barcode)
    if scientific_name:
        plants = plants.filter(scientific_name__icontains=scientific_name)
    if family:
        plants = plants.filter(family__icontains=family)
    if collector:
        plants = plants.filter(collector__icontains=collector)
    if region:
        plants = plants.filter(district__icontains=region) | plants.filter(country__icontains=region)
    if year:
        plants = plants.filter(date_of_collection__icontains=year)

    data = []
    for p in plants[:50]:
        data.append({
            'id': p.id,
            'barcode': p.barcode,
            'scientific_name': p.scientific_name,
            'name': p.name,
            'family': p.family,
            'collector': p.collector,
            'district': p.district,
            'locality': p.locality,
            'date_of_collection': p.date_of_collection
        })

    return JsonResponse({'data': data})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def suggest(request):
    import re
    field = request.GET.get('field', '').strip()
    q = request.GET.get('q', '').strip()
    data = []
    
    if field and q:
        if field == 'barcode':
            items = Plant.objects.filter(barcode__icontains=q).values_list('barcode', flat=True).distinct()[:12]
            data = sorted(list(items))
        elif field == 'scientific_name':
            items = Plant.objects.filter(scientific_name__icontains=q).values_list('scientific_name', flat=True).distinct()[:12]
            data = sorted(list(items))
        elif field == 'family':
            items = Plant.objects.filter(family__icontains=q).values_list('family', flat=True).distinct()[:12]
            data = sorted(list(items))
        elif field == 'collector':
            items = Plant.objects.filter(collector__icontains=q).values_list('collector', flat=True).distinct()[:12]
            data = sorted(list(items))
        elif field == 'region':
            # Region matches district or country
            items_dist = Plant.objects.filter(district__icontains=q).values_list('district', flat=True).distinct()[:8]
            items_country = Plant.objects.filter(country__icontains=q).values_list('country', flat=True).distinct()[:8]
            items = set(list(items_dist) + list(items_country))
            if '' in items:
                items.remove('')
            data = sorted(list(items))
        elif field == 'year':
            items = Plant.objects.filter(date_of_collection__icontains=q).values_list('date_of_collection', flat=True).distinct()[:12]
            raw_list = list(items)
            try:
                # Sort numerically by extracting digits
                data = sorted(raw_list, key=lambda x: int(re.sub(r'\D', '', x)) if re.sub(r'\D', '', x) else 9999)
            except Exception:
                data = sorted(raw_list)
                
    return JsonResponse(data, safe=False)

def plant_detail(request, pk):
    try:
        p = Plant.objects.get(pk=pk)
        data = {
            'id': p.id,
            'barcode': p.barcode,
            'scientific_name': p.scientific_name,
            'name': p.name,
            'family': p.family,
            'genus': p.genus,
            'collector': p.collector,
            'collection_number': p.collection_number,
            'date_of_collection': p.date_of_collection,
            'locality': p.locality,
            'district': p.district,
            'country': p.country,
            'habitat': p.habitat,
            'description': p.description,
            'image': p.image.url if p.image else ''
        }
        return JsonResponse(data)
    except Plant.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
