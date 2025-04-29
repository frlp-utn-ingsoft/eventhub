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
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/crear/', views.category_form, name='category_form'),
    path('categorias/<int:id>/editar/', views.edit_category, name='category_edit'),
    path('categorias/<int:id>/delete/', views.category_delete, name='category_delete'),
    path('notificaciones/crear/', views.notification_form,name= 'create_notification'),
    path('notificaciones/', views.notification, name='notification'),
    path('notificaciones/<int:id>/detalle', views.notification_detail,name='notification_detail'),
    path('notificaciones/<int:id>/editar', views.notification_form,name= 'notification_edit'),
    path('notificaciones/<int:id>/eliminar', views.notification_delete, name='notification_delete'),
    path('notifications/visualizacion', views.user_notifications, name='user_notifications'),
    path('notifications/mark_read/<int:id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark_all_read/', views.mark_notification_read, name='mark_all_read'),
]
