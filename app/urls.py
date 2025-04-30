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
    path('tickets/', views.ticket_list, name='ticket_list'),
    path("tickets/create/<int:event_id>/", views.ticket_create, name="ticket_create"),
    path('tickets/<int:pk>/edit/', views.ticket_update, name='ticket_update'),
    path('tickets/<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
]
