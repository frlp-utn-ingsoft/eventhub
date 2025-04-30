from django.urls import path
from .views import ratingCreateView, ratingDeleteView, ratingUpdateView

app_name = "rating"

urlpatterns = [
    path("<int:pk>/add/", ratingCreateView, name="rating_add"),
    path("<int:pk>/delete/", ratingDeleteView, name="rating_delete"),
    path("<int:pk>/update/", ratingUpdateView, name="rating_update"),
]