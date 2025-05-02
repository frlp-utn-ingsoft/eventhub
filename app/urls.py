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
     path("events/<int:event_id>/purchase/", views.ticket_purchase, name="ticket_purchase"),
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:ticket_id>/update/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:ticket_id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("tickets/<int:ticket_id>/use/", views.ticket_use, name="ticket_use"),
    path('organizer/tickets/', views.organizer_tickets, name='organizer_tickets'),
    path('organizer/tickets/<int:event_id>/', views.organizer_tickets, name='organizer_tickets_event'),
]
