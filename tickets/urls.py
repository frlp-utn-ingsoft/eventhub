from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("tickets/", views.tickets, name="tickets"),
]