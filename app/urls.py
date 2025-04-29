from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("venues/", views.venues, name="venues"),
    path("venues/create/", views.venue_form, name="venue_form"),
    path("venues/<int:id>/edit/", views.venue_form, name="venue_edit"),
    path("venues/<int:id>/", views.venue_detail, name="venue_detail"),
    path("venues/<int:id>/delete/", views.venue_delete, name="venue_delete"),
    path("categories/", views.venues, name="categories"),
    path("categories/create/", views.category_form, name="category_form"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("refunds/", views.My_refunds, name="my_refunds"),
    path("refunds/new/", views.Refund_create, name="refund_create"),
    path("refunds/<int:id>/edit/", views.Refund_edit, name="refund_edit"),
    path("refunds/<int:id>/delete/", views.Refund_delete, name="refund_delete"),
    path("organizer/refund/", views.RefundRequestsAdminView.as_view(), name="refunds_admin"),
    path("organizer/refund/aprobar/<int:pk>/", views.approve_refund_request, name="refund_approve"),
    path("organizer/refund/rechazar/<int:pk>/", views.reject_refund_request, name="refund_reject"),
    path('events/<int:event_id>/rate/', views.create_rating, name='create_rating'),
    path('editar_rating/<int:rating_id>/', views.editar_rating, name='editar_rating'),
    path('eliminar_rating/<int:rating_id>/', views.eliminar_rating, name='eliminar_rating'),
]
