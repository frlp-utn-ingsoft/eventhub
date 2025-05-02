from django.db import models
from django.utils import timezone

from app.models import User


class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', 'Alta'),
        ('MEDIUM', 'Media'),
        ('LOW', 'Baja'),
    ]

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notifications',
        verbose_name="Creador"
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='LOW', verbose_name="Prioridad")

    recipients = models.ManyToManyField(
        User,
        through='UserNotificationStatus',
        related_name='received_notifications',
        verbose_name="Destinatarios",
        blank=False
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"


class UserNotificationStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False, verbose_name="Leído")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de lectura")

    class Meta:
        unique_together = ('user', 'notification')
        ordering = ['notification__created_at']
        verbose_name = "Estado de Notificación de Usuario"
        verbose_name_plural = "Estados de Notificaciones de Usuarios"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()

    def __str__(self):
        return f"{self.user.username} - {self.notification.title} ({'Leído' if self.is_read else 'No leído'})"