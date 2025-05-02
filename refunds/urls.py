from django.urls import path
from . import views

app_name = "refunds"

urlpatterns = [
    path("add/", views.refundCreateView, name="refund_add"),
    path("edit/<int:refund_id>/", views.refundCreateView, name="refund_edit"),
    path("", views.refundListView, name="refund_list"),
    path("<int:id>/delete/", views.refundDeleteView, name="refunds_delete"),
    path("<int:id>/confirm_action/", views.refundConfirmActionView, name="refunds_confirm_action"),
]
