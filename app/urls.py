from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    #accounts
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    #Events
    path("events/", views.events, name="events"),
    
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    #Notifications
    path("notifications/",views.notifications, name = "notifications"),
    path("notifications/<int:id>/delete/",views.notification_delete, name = "notification_delete"),
    path("notifications/<int:notification_id>/read/", views.is_read, name="is_read"),
    path("notificacions/allread/", views.all_is_read, name="all_is_read"),
    path("notificacions/create/", views.notification_create, name="notification_create"),
    path("notificacions/<int:id>/", views.notification_update, name="notification_update"),
    #tickets
    path('tickets/', views.ticket_list, name="ticket_list"),
    path('tickets/<int:event_id>/create/', views.ticket_create, name="ticket_create"),
    path('tickets/<int:ticket_id>/edit/', views.ticket_update, name="ticket_update"),
    path('tickets/<int:ticket_id>/delete/', views.ticket_delete, name="ticket_delete"),
    #rating
    path('ratings/<int:rating_id>/edit/', views.rating_edit, name='rating_edit'),
    path('ratings/<int:rating_id>/delete/', views.rating_delete, name='rating_delete'),
    #Comentario
    path('organizator_comment/', views.comentarios_organizador, name='organizator_comment'),
    path('eliminar_comentario/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('edit_comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    #RefundRequest
    path('refunds/', views.refund_list, name='refund_list'),
    path('refunds/<int:refund_id>/approve/', views.approve_refund, name='approve_refund'),
    path('refunds/<int:refund_id>/reject/', views.reject_refund, name='reject_refund'),
    path('refunds/<int:refund_id>/delete/', views.delete_refund, name='delete_refund'),
    path('refunds/create/', views.create_refund, name='create_refund'),
    path('refunds/<int:refund_id>/update/', views.refund_update, name='refund_update'),
    path("mis-reembolsos/", views.user_refund_list, name="user_refund_list"),

    #Category
   
    
    path('categories/', views.list_categories, name='list_categories'),
    path('categories/create/', views.category_form, name='category_form'),
    path('categories/<int:id>/update/', views.category_form, name='update_category'),
    path('categories/<int:id>/delete/', views.delete_category, name='delete_category'),
    #Venue
    path('venues/', views.venue_list, name='venue_list'),
    path('venues/create/', views.venue_create, name='venue_create'),
    path('venues/<int:venue_id>/edit/', views.venue_update, name='venue_edit'),
    path('venues/<int:venue_id>/delete/', views.venue_delete, name='venue_delete'),

]

