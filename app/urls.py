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
    path("events/<int:event_id>/comments/", views.comments, name="comments"),
    path("events/<int:event_id>/comments/<int:comment_id>/", views.comment_detail, name="comment_detail"),
    path("events/<int:event_id>/comments/create/", views.comment_form, name="comment_form"),
    path("events/<int:event_id>/comments/<int:comment_id>/edit/", views.comment_edit, name="comment_edit"),
    path("events/<int:event_id>/comments/<int:comment_id>/delete/", views.comment_delete, name="comment_delete")
]
