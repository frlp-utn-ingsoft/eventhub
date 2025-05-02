from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("categories/create/", views.category_form, name="category_form"),
    path("venues/create/", views.venue_form, name="venue_form"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("notification/", views.notification_list, name="notification"),
    path('notification/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notification/<int:pk>/edit/', views.notification_edit, name='notification_edit'),
    path('notification/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    path('notification/mark-as-read/<int:pk>/', views.notification_mark_as_read, name='notification_mark_as_read'),
    path('notification/mark-all-as-read/', views.notification_mark_all_as_read, name='notification_mark_all_as_read'),
    path("notification/create", views.notification_create, name="notification_create"),
    path("refunds/", views.My_refunds, name="my_refunds"),
    path("refunds/new/", views.Refund_create, name="refund_create"),
    path("refunds/<int:id>/edit/", views.Refund_edit, name="refund_edit"),
    path("refunds/<int:id>/delete/", views.Refund_delete, name="refund_delete"),
    path("organizer/refund/", views.RefundRequestsAdminView.as_view(), name="refunds_admin"),
    path("organizer/refund/aprobar/<int:pk>/", views.approve_refund_request, name="refund_approve"),
    path("organizer/refund/rechazar/<int:pk>/", views.reject_refund_request, name="refund_reject"),
]
