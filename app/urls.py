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

    
    path("events/<int:id>/ratings/create/", views.rating_create, name="rating_create"),
    path("events/<int:id>/ratings/<int:rating_id>/delete/", views.rating_delete, name="rating_delete"),

  
    path("venues/", views.venue_list, name="venue_list"),
    path("venues/nuevo/", views.create_venue, name="create_venue"),
    path("venues/<int:venue_id>/editar/", views.edit_venue, name="edit_venue"),
    path("venues/<int:venue_id>/eliminar/", views.delete_venue, name="delete_venue"),
    path('venues/<int:id>/', views.venue_detail, name='venue_detail'),

]

