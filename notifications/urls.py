from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    #urls para gestion (creador)
    path('manage/', views.notification_management, name='notification_management'),
    path('create/', views.create_notification, name='create_notification'),
    path('edit/<int:pk>/', views.edit_notification, name='edit_notification'),
    path('delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    
    #url para ver los detalles de una notificacion creada
    path('<int:pk>/', views.view_notification, name='view_notification'),

    #urls para visualizacion (destinatario)
    path('my-notifications/', views.user_notifications, name='user_notifications'),
    
    #url para ver los detalles de una notif desde el estado del usuario
    path('detail/<int:pk>/', views.notification_detail, name='notification_detail'),
    
    path('mark-read/<int:pk>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
]
