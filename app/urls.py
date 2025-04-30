from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("tickets/", views.tickets, name="tickets"),
    path("tickets/create/", views.ticket_form, name="ticket_form"),
    path("tickets/<int:id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:id>/update/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("ticket_types/", views.ticket_types, name="ticket_types"),
    path("ticket_types/create/", views.ticket_type_form, name="ticket_type_form"),
    path("ticket_types/<int:id>/edit/", views.ticket_type_form, name="ticket_type_edit"),
    path("ticket_types/<int:id>/delete/", views.ticket_type_delete, name="ticket_type_delete"),
]
