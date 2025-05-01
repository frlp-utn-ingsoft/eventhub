from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm
from .models import Comment
from app.models import Event
    
def commentCreateView(request, id):
    user = request.user
    event = get_object_or_404(Event, id=id)

    if not user.is_authenticated:
        return redirect("events")

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = user
            comment.event = event
            comment.save()
            return redirect("/events/"+str(event.pk)+"/")
    else:
        form = CommentForm()

    return render(request, "comments/comment_form.html", {"form": form, "event": event})


@login_required
def commentUpdateView(request, id):
    user = request.user
    comment = get_object_or_404(Comment, id=id)

    if not (user == comment.user or (user.is_organizer and user == comment.event.organizer)):
        return redirect("events")

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect("/events/"+str(comment.event.id)+"/")
    else:
        form = CommentForm(instance=comment)

    return render(request, "comments/comment_form.html", {"form": form, "comment": comment})

@login_required 
def commentDeleteView(request, id):
    user = request.user
    comment = get_object_or_404(Comment, id=id)
    
    if not (user == comment.user or (user.is_organizer and user == comment.event.organizer)):
        return redirect("events")
    
    if request.method == "POST":
        comment.delete()
        return redirect("/events/"+str(comment.event.id)+"/")
    return render(request, "comments/comment_confirm_delete.html", {"comment": comment})
    
def commentListView(request):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    comments = Comment.objects.filter(event__organizer=user).order_by("created_at")
    return render(request, "comments/comment_list.html", {"comments": comments})

@login_required  
def commentDetailView(request, id):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    comment = get_object_or_404(Comment, id=id)
    return render(request, "comments/comment_detail.html", {"comment": comment})
