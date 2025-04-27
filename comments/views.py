from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from .forms import CommentForm
from .models import Comment
from app.models import Event

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "comments/comment_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.event = get_object_or_404(Event, pk=self.kwargs["event_pk"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("event_detail", kwargs={"id": self.object.event.pk})


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "comments/comment_form.html"

    def test_func(self):
        return self.request.user == self.get_object().user

    def get_success_url(self):
        return reverse("event_detail", kwargs={"id": self.object.event.pk})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = "comments/comment_confirm_delete.html"

    def test_func(self):
        comment = self.get_object()
        return (
            self.request.user == comment.user
            or (self.request.user.is_organizer and
                self.request.user == comment.event.organizer)
        )

    def get_success_url(self):
        return reverse("event_detail", kwargs={"id": self.get_object().event.pk})
