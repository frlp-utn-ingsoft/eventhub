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
    path('event/<int:event_id>/comments/add/', views.comment_create, name='comment_add'),
     path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path(
        "events/comments/",
        views.organizer_comments,
        name="organizer_comments"
    ),
    path('comment/<int:pk>/hard-delete/', views.comment_hard_delete, name='comment_hard_delete'),

]
