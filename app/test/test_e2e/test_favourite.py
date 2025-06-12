import pytest
from django.utils import timezone
from app.models import Event,User
from playwright.sync_api import sync_playwright

@pytest.mark.django_db
def test_toggle_favorite(live_server):
    # Crear usuarios
    user = User.objects.create_user(username='prueba', password='12345678')
    organizer = User.objects.create_user(username='organizador', password='87654321', is_organizer=True)

    # Crear evento
    event = Event.objects.create(
        title='Evento de prueba',
        description='Descripción',
        scheduled_at=timezone.now() + timezone.timedelta(days=1),
        organizer=organizer,
        status='active',
        venue=None,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login
        page.goto(f'{live_server.url}/accounts/login/')
        page.fill('input[name="username"]', 'prueba')
        page.fill('input[name="password"]', '12345678')
        page.click('button:has-text("Iniciar sesión")')

        # Esperar a que redirija a /events/
        page.wait_for_url(f'{live_server.url}/events/', timeout=10000)

        # Buscar fila del evento por título
        row = page.locator(f'tr:has-text("{event.title}")')
        favorite_button = row.locator('form.favourite-form button')

        # Validar que el botón está en estado "no favorito" (clase btn-outline-warning)
        btn_class = favorite_button.get_attribute('class')
        assert 'btn-outline-warning' in btn_class

        # Click para marcar favorito
        favorite_button.click()

        # Esperar recarga o actualización (ajustar según implementación)
        page.wait_for_load_state('networkidle')  # Espera que termine carga red

        # Re-obtener botón para verificar cambio
        row = page.locator(f'tr:has-text("{event.title}")')
        favorite_button = row.locator('form.favourite-form button')
        btn_class_after = favorite_button.get_attribute('class')

        # Validar que el botón cambió a "favorito" (clase btn-warning)
        assert 'btn-warning' in btn_class_after

        browser.close()
