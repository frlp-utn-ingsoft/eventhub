from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("categories/create/", views.category_form, name="category_form"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("refunds/", views.My_refunds, name="my_refunds"),
    path("refunds/new/", views.Refund_create, name="refund_create"),
    path("refunds/<int:id>/edit/", views.Refund_edit, name="refund_edit"),
    path("refunds/<int:id>/delete/", views.Refund_delete, name="refund_delete"),
]
