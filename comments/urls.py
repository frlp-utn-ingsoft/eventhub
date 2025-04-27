from django.urls import path
from .views import CommentCreateView, CommentUpdateView, CommentDeleteView

app_name = "comments"

urlpatterns = [
    path("events/<int:event_pk>/comments/add/", CommentCreateView.as_view(),
         name="comment_add"),
    path("comments/<int:pk>/edit/", CommentUpdateView.as_view(),
         name="comment_edit"),
    path("comments/<int:pk>/delete/", CommentDeleteView.as_view(),
         name="comment_delete"),
]
