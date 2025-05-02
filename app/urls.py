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
    path("event/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("ubicaciones/", views.venue_list, name="venue_list"),  # Ruta para la lista de ubicaciones
    path("ubicaciones/nueva/", views.venue_form, name="venue_form"),  # Ruta para crear una ubicación
    path("ubicaciones/<int:id>/editar/", views.venue_form, name="venue_form"),  # Ruta para editar una ubicación
    path("ubicaciones/<int:id>/", views.venue_detail, name="venue_detail"),  # Ruta para ver detalles de una ubicación
    path("ubicaciones/<int:id>/eliminar/", views.venue_delete, name="venue_delete"),  # Ruta para eliminar una ubicación

    path('tickets/', views.ticket_list, name='ticket_list'),
    path("tickets/create/<int:event_id>/", views.ticket_create, name="ticket_create"),
    path('tickets/<int:pk>/edit/', views.ticket_update, name='ticket_update'),
    path('tickets/<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    path("categories/", views.categories, name="categories"),
    path("categories/create/", views.category_form, name="category_form"), 
    path("categories/<int:id>/edit/", views.category_form, name="category_edit"),
    path("categories/<int:id>/", views.category_detail, name="category_detail"),
    path("categories/<int:id>/delete/", views.category_delete, name="category_delete"),
    path("notifications/", views.NotificationList.as_view(),            name="notifications_list"),
    path("notifications/new/", views.NotificationCreate.as_view(),      name="notifications_create"),
    path("notifications/<int:pk>/edit/", views.NotificationUpdate.as_view(), name="notifications_edit"),
    path("notifications/<int:pk>/delete/", views.NotificationDelete.as_view(), name="notifications_delete"),
    path("notifications/<int:pk>/read/", views.NotificationMarkRead.as_view(), name="notifications_read"),
    path("notifications/dropdown/", views.NotificationDropdown.as_view(), name="notifications_dropdown"),
    path("ratings/<int:rating_id>/delete/", views.rating_delete, name="rating_delete"),
    path("refunds/", views.my_refund_requests, name="my_refund_requests"),
    path("refunds/new/", views.new_refund_request, name="create_refund_request"),
    path('refunds/<int:id>/edit/', views.edit_refund_request, name='edit_refund_request'),
    path("refunds/<int:id>/delete/", views.refund_request_delete, name="delete_refund_request"),
    path("refunds/<int:id>/", views.refund_detail,name="refund_detail"),
    path("refunds/manage/", views.manage_refund_requests, name="manage_refund_requests"),
    path("refunds/<int:id>/approve/", views.approve_refund_request, name="approve_refund_request"),
    path("refunds/<int:id>/reject/", views.reject_refund_request, name="reject_refund_request"),
]
