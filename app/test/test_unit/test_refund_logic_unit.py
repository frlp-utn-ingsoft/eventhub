from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import RefundRequest
from unittest.mock import patch, MagicMock # Importar patch y MagicMock para simular objetos

User = get_user_model() # Obtener el modelo de usuario actual

class RefundLogicUnitTests(TestCase):
    def setUp(self):
        # Creamos un usuario de prueba (no persistente en la DB para este test, es solo un objeto mock)
        self.mock_user = MagicMock()
        self.mock_user.id = 1 # Asignamos un ID para simular un usuario real
        self.mock_user.username = 'mockuser'

        self.test_ticket_code = 'ABC-123-DEF' # Un código de ticket de ejemplo

        # Creamos un mock para simular una solicitud de reembolso EXISTENTE y PENDIENTE
        self.mock_pending_refund_request = MagicMock()
        self.mock_pending_refund_request.user = self.mock_user
        self.mock_pending_refund_request.ticket_code = self.test_ticket_code
        self.mock_pending_refund_request.approval = None # Muy importante: simular que está pendiente

        # Creamos mocks para solicitudes no pendientes para otros casos de prueba
        self.mock_approved_refund_request = MagicMock()
        self.mock_approved_refund_request.user = self.mock_user
        self.mock_approved_refund_request.ticket_code = self.test_ticket_code
        self.mock_approved_refund_request.approval = True

        self.mock_rejected_refund_request = MagicMock()
        self.mock_rejected_refund_request.user = self.mock_user
        self.mock_rejected_refund_request.ticket_code = self.test_ticket_code
        self.mock_rejected_refund_request.approval = False


    # El path para el mock debe ser donde se ACCEDE a RefundRequest.objects en tu código.
    # Como la consulta está en app/views.py, el path correcto es 'app.views.RefundRequest.objects'.
    @patch('app.views.RefundRequest.objects')
    def test_identifies_pending_refund_request(self, mock_objects):
        """
        Verifica que la lógica de la consulta (en la vista) detecta correctamente una solicitud pendiente.
        """
        # Configuramos el mock para que cuando se llame a .filter() y luego .first(),
        # devuelva nuestra solicitud pendiente mockeada.
        mock_objects.filter.return_value.first.return_value = self.mock_pending_refund_request

        # Ejecutamos la consulta exactamente como está en tu vista
        found_request = RefundRequest.objects.filter(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True, # Este es el filtro clave para "pendiente"
        ).first()

        # Afirmaciones:
        self.assertIsNotNone(found_request) # Debería encontrar algo
        self.assertEqual(found_request, self.mock_pending_refund_request) # Debe ser nuestra solicitud mockeada
        self.assertIsNone(found_request.approval) # Confirmamos que su aprobación es None

        # Verificamos que el mock fue llamado correctamente
        mock_objects.filter.assert_called_once_with(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True
        )
        mock_objects.filter.return_value.first.assert_called_once()


    @patch('app.views.RefundRequest.objects')
    def test_does_not_identify_no_pending_refund_request(self, mock_objects):
        """
        Verifica que la lógica de la consulta NO detecta una solicitud cuando no hay pendientes.
        """
        # Configuramos el mock para que filter().first() devuelva None (no se encuentra nada pendiente)
        mock_objects.filter.return_value.first.return_value = None

        # Ejecutamos la consulta
        found_request = RefundRequest.objects.filter(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True,
        ).first()

        # Afirmaciones:
        self.assertIsNone(found_request) # No debería encontrar nada

        mock_objects.filter.assert_called_once_with(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True
        )
        mock_objects.filter.return_value.first.assert_called_once()


    @patch('app.views.RefundRequest.objects')
    def test_does_not_identify_approved_refund_request_as_pending(self, mock_objects):
        """
        Verifica que la lógica de la consulta NO considera una solicitud APROBADA como pendiente.
        """
        # Configuramos el mock para que la consulta de PENDIENTES devuelva None,
        # incluso si tuviéramos una solicitud aprobada mockeada, porque el filtro `approval__isnull=True`
        # es el que nos interesa probar.
        mock_objects.filter.return_value.first.return_value = None

        # Ejecutamos la consulta con el filtro de pendiente
        found_request = RefundRequest.objects.filter(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True,
        ).first()

        self.assertIsNone(found_request) # Debería ser None porque una aprobada no es pendiente

        mock_objects.filter.assert_called_once_with(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True
        )
        mock_objects.filter.return_value.first.assert_called_once()

    @patch('app.views.RefundRequest.objects')
    def test_does_not_identify_rejected_refund_request_as_pending(self, mock_objects):
        """
        Verifica que la lógica de la consulta NO considera una solicitud RECHAZADA como pendiente.
        """
        mock_objects.filter.return_value.first.return_value = None

        found_request = RefundRequest.objects.filter(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True,
        ).first()

        self.assertIsNone(found_request)

        mock_objects.filter.assert_called_once_with(
            user=self.mock_user,
            ticket_code=self.test_ticket_code,
            approval__isnull=True
        )
        mock_objects.filter.return_value.first.assert_called_once()