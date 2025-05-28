import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import RefundRequest

User = get_user_model()

@pytest.mark.django_db
def test_refund_creation_block_if_pending(client):
    user = User.objects.create_user(username="testuser", password="pass")
    client.force_login(user)

    # Crear una solicitud pendiente
    RefundRequest.objects.create(
        user=user,
        ticket_code="TICKET123",
        reason="Motivo original",
        approved=None  # solicitud pendiente
    )

    # Intentar crear una segunda solicitud
    url = reverse('create_refund')
    data = {
        'ticket_code': 'TICKET456',
        'reason': 'Otro motivo'
    }
    client.post(url, data)

    # Verificar que solo hay una solicitud en la base
    assert RefundRequest.objects.filter(user=user).count() == 1
