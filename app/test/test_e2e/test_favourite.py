from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import time
from django.contrib.auth import get_user_model
from django.utils import timezone
from app.models import Event  # ajusta 'app' por el nombre correcto de tu app

User = get_user_model()

class TestFavoritosE2E(unittest.TestCase):

    def setUp(self):
        # Usuario con el que se hace login
        self.test_user, created = User.objects.get_or_create(
            username='Prueba',
            defaults={
                'email': 'prueba@example.com',
                'is_organizer': False,
            }
        )
        if created:
            self.test_user.set_password('12345678')
            self.test_user.save()

        # Usuario organizador distinto para el evento
        self.organizer_user, created = User.objects.get_or_create(
            username='Organizador',
            defaults={
                'email': 'organizador@example.com',
                'is_organizer': True,
            }
        )
        if created:
            self.organizer_user.set_password('87654321')
            self.organizer_user.save()

        # Crear un evento asociado al organizador, no al usuario de prueba
        self.test_event, created = Event.objects.get_or_create(
            title='Evento de prueba',
            defaults={
                'description': 'Descripción del evento de prueba',
                'scheduled_at': timezone.now() + timezone.timedelta(days=1),
                'organizer': self.organizer_user,
                'status': 'active',
                'venue': None,
            }
        )

        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.base_url = "http://127.0.0.1:8000"

    def tearDown(self):
        # Para observar la última pantalla si hay error
        time.sleep(5)
        self.driver.quit()

        # Limpieza de datos creados
        if hasattr(self, 'test_event'):
            self.test_event.delete()
        if hasattr(self, 'test_user'):
            self.test_user.delete()
        if hasattr(self, 'organizer_user'):
            self.organizer_user.delete()

    def login(self):
        self.driver.get(f"{self.base_url}/accounts/login")
        try:
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.driver.find_element(By.NAME, "password")

            username_input.send_keys("Prueba")
            password_input.send_keys("12345678")

            password_input.submit()

            # Confirmamos que se logueó correctamente
            self.wait.until(EC.url_contains("/events"))

        except Exception as e:
            print("❌ Error en login:", e)
            print("URL actual:", self.driver.current_url)
            time.sleep(10)
            raise

    def esperar_cambio_clase(self, obtener_boton_fn, clase_anterior, timeout=10):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda d: obtener_boton_fn().get_attribute("class") != clase_anterior)

    def test_marcar_y_desmarcar_favorito(self):
        driver = self.driver
        wait = self.wait

        try:
            self.login()
            driver.get(f"{self.base_url}/events")
            print("🔄 Cargando lista de eventos...")
            print("URL actual:", driver.current_url)

            def obtener_boton_favorito():
                filas_eventos = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table tbody tr")))
                assert len(filas_eventos) > 0, "No hay filas en la tabla"

                primera_fila = filas_eventos[0]
                form_favorito = primera_fila.find_element(By.CSS_SELECTOR, "form.favourite-form")
                boton_favorito = form_favorito.find_element(By.CSS_SELECTOR, "button.btn-warning, button.btn-outline-warning")
                return boton_favorito

            # Estado inicial
            boton_favorito = obtener_boton_favorito()
            clase_inicial = boton_favorito.get_attribute("class")
            print("⭐ Clase inicial del botón:", clase_inicial)

            # Click para marcar como favorito
            boton_favorito.click()
            self.esperar_cambio_clase(obtener_boton_favorito, clase_inicial)

            boton_favorito = obtener_boton_favorito()
            clase_despues_click = boton_favorito.get_attribute("class")
            print("🌟 Clase después de marcar favorito:", clase_despues_click)
            self.assertNotEqual(clase_inicial, clase_despues_click)

            # Click para desmarcar favorito
            boton_favorito.click()
            self.esperar_cambio_clase(obtener_boton_favorito, clase_despues_click)

            boton_favorito = obtener_boton_favorito()
            clase_final = boton_favorito.get_attribute("class")
            print("🔁 Clase final (debería ser igual a inicial):", clase_final)
            self.assertEqual(clase_final, clase_inicial)

            print("✅ Test de favoritos completado con éxito")

        except Exception as e:
            print("❌ Error durante el test:", e)
            print("URL actual:", driver.current_url)
            time.sleep(10)
            raise


if __name__ == "__main__":
    unittest.main()
