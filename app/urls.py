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
    path("venues/", views.venues, name="venues"),
    path("venues/create", views.venue_form,{"id": None},  name="venue_form"),
    path("venues/<int:id>/edit", views.venue_form, name="venue_form"),
    path("venues/<int:id>/delete", views.venue_delete, name="venue_delete"),
    path("venues/<int:id>/", views.venue_detail, name="venue_detail"),
    path("categories/", views.categories, name="categories"),
    path("categories/create/", views.category_form, name="category_create"),
    path("categories/<int:id>/edit/", views.category_form, name="category_update"),
    path("categories/<int:id>/delete/", views.category_delete, name="category_delete"),
    path("categories/<int:id>/", views.category_detail, name="category_detail"),
    path("events/<int:event_id>/rate/", views.rating_create_or_update, name="rating_create_or_update"),
    path("ratings/<int:id>/delete/", views.rating_delete, name="rating_delete"),
]
