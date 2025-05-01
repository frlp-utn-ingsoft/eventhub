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
    path('refund_request/', views.refund_request, name='refund_request'),
    path('my_refunds/', views.my_refunds, name='my_refunds'),
    path('manage_refunds/', views.manage_refunds, name='manage_refunds'),
    path('refund_detail/<int:id>/', views.refund_detail, name='refund_detail'),
    path('edit_refund/<int:id>/', views.edit_refund, name='edit_refund'),    
]
