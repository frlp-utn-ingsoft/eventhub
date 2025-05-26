import uuid  #importamos la libreria uuid para generar el ticket_code

from django.db import models


class Ticket(models.Model):
    class TipoTicket(models.TextChoices): #mi enumerativa
        GENERAL = "General"
        VIP = "VIP"
        
    user = models.ForeignKey(
        "app.user",
        on_delete=models.CASCADE,
        related_name="tickets")

    event = models.ForeignKey(
        "app.event",
        on_delete=models.CASCADE,
        related_name="tickets")
    
    buy_date = models.DateTimeField(auto_now_add=True) #al crear el ticket se guarda la fecha y hora
    ticket_code = models.CharField(max_length=10, unique=True, blank=True) #codigo unico del ticket
    quantity = models.IntegerField(default=1) #cantidad de tickets 
    type = models.CharField(
        max_length=12,
        choices=TipoTicket.choices,
        default=TipoTicket.GENERAL) #tipo de ticket, por defecto es general
    
    class Meta:
        #esto asegura que solo pueda existir UN ticket por usuario y evento
        unique_together = ('user', 'event')
    
    def save(self, *args, **kwargs): #sobreescribimos el metodo save para generar el ticket_code
        #generar ticket_code solo si es un objeto nuevo o si está vacío
        if not self.ticket_code:
            self.ticket_code = str(uuid.uuid4()).upper()[:10]
        super().save(*args, **kwargs) #llamamos al metodo save de la clase padre
    
    def __str__(self):
        return (
            self.user.username 
            + " - " 
            + self.event.title 
            + " - " 
            + self.ticket_code
        )