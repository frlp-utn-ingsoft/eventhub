from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

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

    ## Refunds
    path("refunds/", views.my_refund_requests, name="my_refund_requests"),
    path("refunds/new/", views.new_refund_request, name="create_refund_request"),
    path('refunds/<int:id>/edit/', views.edit_refund_request, name='edit_refund_request'),
    path("refunds/<int:id>/delete/", views.refund_request_delete, name="delete_refund_request"),
    path("refunds/<int:id>/", views.refund_detail,name="refund_detail"),
    path("refunds/manage/", views.manage_refund_requests, name="manage_refund_requests"),
    path("refunds/<int:id>/approve/", views.approve_refund_request, name="approve_refund_request"),
    path("refunds/<int:id>/reject/", views.reject_refund_request, name="reject_refund_request"),
]
