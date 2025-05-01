from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("<int:id>/", views.compra, name="compra"),
    path("eliminacion/", views.eliminacion, name="eliminacion"),
]           