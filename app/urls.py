from django.contrib.auth.views import LogoutView
from django.urls import path
from django.contrib import admin

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path('locations/new/', views.create_location, name='create_location'),
    path('locations/', views.list_locations, name='locations_list'),
    path('locations/<int:location_id>/edit/', views.update_location, name='update_location'),
    path('locations/<int:location_id>/delete/', views.delete_location, name='delete_location'),
    path('categories', views.list_categories, name='categories_list'),
    path('categories/new', views.manage_category, name='create_category'),
    path('categories/<int:category_id>/edit/', views.manage_category, name='update_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/<int:notification_id>/edit/', views.create_notification, name='edit_notification'),
    path('notifications/', views.list_notifications, name='list_notifications'),
    path('notifications/<int:notification_user_id>/mark_read/', views.read_notification, name='read_notification'),
    path('notifications/mark_read_all/', views.read_all_notifications, name='read_all_notifications'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/detail/', views.detail_comment, name='detail_comment'),
    path("tickets/buy", views.buy_ticket, name='buy_ticket'),
    path("tickets/", views.tickets_list, name="tickets_list"),
    path('tickets/<str:ticket_code>/delete/', views.delete_ticket, name='delete_ticket'),
    path('tickets/<str:ticket_code>/edit/', views.update_ticket, name='update_ticket'),
    path('tickets/buy/<int:event_id>/', views.buy_ticket_from_event, name='buy_ticket_from_event'),
    path('organizer/tickets/', views.organizer_tickets_list, name='organizer_ticket_list'),


]
