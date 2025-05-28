import os
import django

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventhub.settings')
django.setup()

from app.models import Venue, Category, Notification, Event, User, Ticket, Rating, Comment, RefundRequest
from django.utils import timezone
from datetime import datetime

def seed():
    # Venue
    success, newVenue=Venue.new(
        name="Movistar Arena",
        adress="Humboldt 450",
        city="Cdad. Autónoma de Buenos Aires",
        capacity=15000,
        contact="https://www.movistararena.com.ar/"
    )
    print("Datos de 'Venue' sembrados exitosamente")

    # Category
    success,newCategory=Category.new(
        name="Pop",
        description="Género musical popular caracterizado por canciones con melodías y ritmos marcados, a menudo con instrumentos eléctricos y amplificación, y dirigido a un público amplio.", 
        is_active=True
    )
    print("Datos de 'Category' sembrados exitosamente")

    # User
    newUser = User.objects.create_user(
        email="organizer@example.com",
        username="organizer",
        password="organizer",
        is_organizer=True
    )
    print("Datos de 'Usuario Organizador' sembrados exitosamente")

    # User
    newNormieUser = User.objects.create_user(
        email="normie@example.com",
        username="normie",
        password="normie",
        is_organizer=False
    )
    print("Datos de 'Usuario Normal' sembrados exitosamente")

    # Event
    event_date = timezone.make_aware(
        datetime(2025, 5, 16, 0, 0),
        timezone.get_current_timezone()
    )

    newEvent=Event.objects.create(
        title="Reik",
        description="La banda mexicana formada por Jesús Navarro, Julio Ramírez y Bibi Marín regresa al país en el marco de su gira mundial 'Panorama Tour'",
        scheduled_at=event_date,
        organizer=newUser,
        venue=newVenue,
        category=newCategory,
    )
   
    # Notification
    Notification.objects.create(
        title="Quedan 24hs para que comience el evento. No te lo pierdas!",
        message="No dejes pasar esta oportunidad única de vivir una experiencia increíble. ¡Prepárate, ajusta tu agenda y nos vemos allí!",
        priority="MEDIUM",
        created_at=timezone.now(),
    )
    print("Datos de 'Notification' sembrados exitosamente")   

    # Ticket
    success, newTicket=Ticket.new(
        quantity=1,
        type="VIP",
        event=newEvent,
        user=newNormieUser
    )
    print("Datos de 'Ticket' sembrados exitosamente")

    # Rating.new(
    #    
    # )
    # print("Datos de 'Rating' sembrados exitosamente")
    
    # Comment
    Comment.new(
        title="Buenisima banda", 
        text="Reik es mi corazón <3, cada canción me lleva a momentos inolvidables. ¡Eternamente fan!",
        event=newEvent,
        user=newUser
    )
    print("Datos de 'Comment' sembrados exitosamente")


    # RefundRequest
    RefundRequest.objects.create(
        ticket_code=newTicket.ticket_code,
        reason="unable_to_attend",
        additional_details="Lamento faltar al concierto. Es el cumple de mi primito y prometí ayudarle. Sé que el show será increíble.",
        accepted_policy=True,
        approval=False,
        approval_date=timezone.now(),
        user=newNormieUser
    )


if __name__ == '__main__':
    print("Sembrando datos...")
    seed()
    print("¡Listo!")