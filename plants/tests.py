from django.test import TestCase, Client
from .models import Plant

class PlantModelTest(TestCase):
    def setUp(self):
        Plant.objects.create(
            name="Test Plant",
            scientific_name="Testus plantus",
            family="TestFamily",
            genus="TestGenus",
            barcode="DSAH0001"
        )

    def test_plant_creation(self):
        plant = Plant.objects.get(barcode="DSAH0001")
        self.assertEqual(plant.name, "Test Plant")
        self.assertEqual(plant.family, "TestFamily")
        self.assertEqual(str(plant), "Test Plant")

class PlantViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        Plant.objects.create(
            name="Searchable Plant",
            scientific_name="Searchus plantus",
            family="SearchFamily",
            genus="SearchGenus",
            barcode="DSAH0002",
            locality="Test Region",
            date_of_collection="2026"
        )

    def test_home_page_loads_correctly(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_about_page_loads_correctly(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_contact_page_loads_correctly(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')

    def test_search_api_returns_json(self):
        response = self.client.get('/search/?barcode=DSAH0002')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue('data' in data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['barcode'], 'DSAH0002')

    def test_autocomplete_suggest_api(self):
        response = self.client.get('/api/suggest/?field=family&q=SearchFamily')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0], "SearchFamily")
