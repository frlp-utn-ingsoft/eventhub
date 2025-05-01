from django.urls import path

from . import views

app_name = "refunds"

urlpatterns = [
    path("add/", views.refundCreateView, name="refund_add"),
    path("list/",views.refundListView,name="refund_list"),
]