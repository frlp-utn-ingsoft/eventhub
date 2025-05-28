import pytest
from app.models import RefundRequest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestRefundRequestModel:
    def test_prevent_duplicate_active_refund_request(self):
        user = User.objects.create_user(username="testuser", password="testpass")

        # Primera solicitud activa (aprobación pendiente)
        RefundRequest.objects.create(
            ticket_code="ABC123",
            reason="First request",
            user=user,
            approved=None
        )

        # Intentar crear otra solicitud activa
        success, result = RefundRequest.new(
            ticket_code="XYZ789",
            reason="Second request",
            user=user
        )

        assert success is False

        # Verificación solo si result es un diccionario de errores
        if isinstance(result, dict):
            assert "__all__" in result
            assert "Ya tienes una solicitud de reembolso activa." in result["__all__"]
        else:
            pytest.fail("Expected a dict of errors but got something else")
