from django.utils.timezone import now
from app.models import RefundRequest, User
from .base import BaseE2ETest
from playwright.sync_api import expect  # type: ignore

class RefundE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.user = self.create_test_user()

        RefundRequest.objects.create(
            user=self.user,
            ticket_code="33cf3697-81e5-420f-ac9a-2374e3fb1f61",
            reason='Solicitud pendiente',
            approved=None,
            created_at=now()
        )

    def test_no_permitir_crear_solicitud_si_hay_pendiente(self):
        self.login_user("usuario_test", "password123")

        self.page.goto(f"{self.live_server_url}/mis-reembolsos/")

        # Verificamos que aparezca el mensaje de advertencia
        expect(self.page.locator("text=Ya tienes una solicitud de reembolso pendiente. Debes esperar a que sea procesada antes de solicitar otra.")).to_be_visible()

        # Verificamos que el botón para crear una nueva solicitud no esté visible
        expect(self.page.locator("text=Solicitar nuevo reembolso")).not_to_be_visible()

        # Verificamos que no haya más de una solicitud
        assert RefundRequest.objects.filter(user=self.user).count() == 1
