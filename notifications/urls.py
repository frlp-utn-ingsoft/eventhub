from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("manage/", views.manage_notifications, name="manage_notifications"),
    path("create/", views.create_notification, name="create_notification"),
    path("<int:pk>/edit/", views.edit_notification, name="edit_notification"),
    path("<int:pk>/delete/", views.delete_notification, name="delete_notification"),
    path("", views.user_notifications, name="user_notifications"),
    path("<int:pk>/mark-read/", views.mark_notification_read, name="mark_read"),
    path("mark-all-read/", views.mark_all_notifications_read, name="mark_all_read"),
]