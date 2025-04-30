from django.urls import include, path
from .views import ratingCreateView

app_name = "rating"

urlpatterns = [
    path("event/<int:id>/add/", ratingCreateView, name="rating_add"),
]