from django.contrib.auth.views import LogoutView
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("events/<int:id>/buy-ticket/", views.buy_ticket, name="buy_ticket"),
    path("tickets/", views.tickets, name="tickets"),
    path("tickets/<int:id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("tickets/<int:id>/edit/", views.ticket_edit, name="ticket_edit"),
    path("events/<int:id>/comment/", views.add_comment, name="add_comment"),
    path("events/<int:id>/comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("events/<int:id>/comment/<int:comment_id>/update/", views.update_comment, name="update_comment"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),
    path("notifications/<int:id>/edit/", views.notification_edit, name="notification_edit"),
    path("notifications/<int:id>/", views.notification_detail, name="notification_detail"),
    path("notifications/<int:id>/delete/", views.notification_delete, name="notification_delete"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
    path('notifications/mark_all_read/', views.mark_all_notifications_read, name='notification_mark_all_read'),
    path("categories/", views.categories, name="categories"),
    path("categories/create/", views.category_form, name="category_form"),
    path("categories/<int:category_id>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:category_id>/delete/", views.category_delete, name="category_delete"),
]
