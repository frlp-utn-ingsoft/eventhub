from django.db import models

from django.conf import settings 
from django.utils import timezone

# Aclaración: agrego un atributo y modifico uno existente -> status reemplaza a approved ya que 
# en la imagen se observa que puede tener valor pendiente, aprobado o rechazado.
# Agrego detalle ya que se observa en la imagen pero no estaba en el diagrama.

OPCIONES = [
    ('pending', 'Pendiente'),
    ('approved', 'Aprobado'),
    ('rejected', 'Rechazado'),
]

class Refund(models.Model):
    user = models.ForeignKey("app.User", on_delete=models.CASCADE, related_name='refunds')

    status = models.CharField(
        max_length=15, 
        choices=OPCIONES,
        default='pending'
    )

    approval_date = models.DateField(
        null=True,    
        blank=True   
    )

    ticket_code = models.TextField()
    reason = models.TextField()
    detail = models.TextField(
        blank=True,   
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True) 
        
    def __str__(self):
        return f"{self.user.username} – {self.ticket_code}"