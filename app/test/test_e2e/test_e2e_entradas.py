from django.test import TestCase
from django.urls import reverse
from app.models import User

class EventHubLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="usuario_test", password="contraseña_test")

    def test_login_redirects_to_events(self):
        login_url = reverse('login')  # o la URL que uses para login, puede ser '/accounts/login/'
        home_url = '/'       # o el nombre del path que quieras verificar

        # Hacer POST al login con las credenciales
        response = self.client.post(login_url, {
            'username': 'usuario_test',
            'password': 'contraseña_test',
        })

        # Verificar que redirige a /
        self.assertRedirects(response, home_url)