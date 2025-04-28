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
    ticket_code = models.CharField(max_length=10,unique=True) #codigo unico del ticket
    quantity = models.IntegerField(default=1) #cantidad de tickets 
    type = models.CharField(
        max_length=12,
        choices=TipoTicket.choices,
        default=TipoTicket.GENERAL) #tipo de ticket, por defecto es general
    
    
    def __str__(self):
        return (
            self.user.username 
            + " - " 
            + self.event.title 
            + " - " 
            + self.ticket_code
        )