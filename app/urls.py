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
    path("notification/", views.notification_list, name="notification"),
    path('notification/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notification/<int:pk>/edit/', views.notification_edit, name='notification_edit'),
    path('notification/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    path("notification/create", views.notification_create, name="notification_create"),
]
