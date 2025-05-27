from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class CronometroVisibilityUnitTest(TestCase):
    def test_usuario_participante_ve_cronometro(self):
        user = User.objects.create(username="invitado", is_organizer=False)
        self.assertFalse(user.is_organizer)

    def test_usuario_organizador_no_ve_cronometro(self):
        user = User.objects.create(username="organizador", is_organizer=True)
        self.assertTrue(user.is_organizer)
