from django.test import TestCase, Client
from django.urls import reverse

class CoreTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
