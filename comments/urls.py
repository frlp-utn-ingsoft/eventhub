from django.urls import path
from .views import commentCreateView, commentUpdateView, commentDeleteView, commentDetailView, commentListView

app_name = "comments"

urlpatterns = [
    path("events/<int:id>/add/", commentCreateView,
         name="comment_add"),
    path("<int:id>/edit/", commentUpdateView,
         name="comment_edit"),
    path("<int:id>/delete/", view=commentDeleteView,
         name="comment_delete"),
    path("<int:id>/", commentDetailView, name="comment_detail"),
    path("", view=commentListView, name="comment_list"),
]
