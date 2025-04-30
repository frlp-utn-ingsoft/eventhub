from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("app/events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path('categories/', views.list_categories, name='list_categories'),
    path('categories/create/', views.category_form, name='category_form'),
    path('categories/<int:id>/update/', views.category_form, name='update_category'),
    path('categories/<int:id>/delete/', views.delete_category, name='delete_category'),
   # path("categories/<int:id>/", views.category_detail, name="category_detail"),


]
