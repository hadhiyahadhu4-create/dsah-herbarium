from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('search/', views.search_plants),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('api/suggest/', views.suggest, name='suggest'),
    path('api/plant/<int:pk>/', views.plant_detail, name='plant_detail'),
]
