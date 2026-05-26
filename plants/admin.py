from django.contrib import admin
from .models import Plant

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'family', 'genus', 'barcode')
    search_fields = ('name', 'scientific_name', 'family', 'genus', 'barcode')
