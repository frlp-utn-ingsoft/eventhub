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
    path("notifications/", views.NotificationList.as_view(),            name="notifications_list"),
    path("notifications/new/", views.NotificationCreate.as_view(),      name="notifications_create"),
    path("notifications/<int:pk>/edit/", views.NotificationUpdate.as_view(), name="notifications_edit"),
    path("notifications/<int:pk>/delete/", views.NotificationDelete.as_view(), name="notifications_delete"),
    path("notifications/<int:pk>/read/", views.NotificationMarkRead.as_view(), name="notifications_read"),
]
