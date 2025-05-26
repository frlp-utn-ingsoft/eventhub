from django.contrib.auth.models import User
from app.models import Event, Rating

def test_rating_average_calculation():
    organizer = User.objects.create_user(username="organizer", password="pass")
    event = Event.objects.create(title="Evento Test", organizer=organizer)

    Rating.objects.create(
        evento=event, usuario=organizer,
        titulo="Muy Bueno", calificacion=5, texto="El evento estuvo muy interesante"
    )

    Rating.objects.create(
        evento=event, usuario=User.objects.create_user(username="user2", password="pass"),
        titulo="No me intereso", calificacion=3, texto="El evento estuvo bien, pero puede mejorar"
    )

    Rating.objects.create(
        evento=event, usuario=User.objects.create_user(username="user3", password="pass"),
        titulo="Malo", calificacion=1, texto="No me gusto nada"
    )

    average = event.rating_average
    assert round(average, 1) == 3.0
