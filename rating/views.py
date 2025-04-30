from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RatingForm
from .models import Rating
from app.models import Event

def ratingCreateView(request, pk):
    user = request.user
    event = get_object_or_404(Event, pk=pk)

    if not user.is_authenticated:
        return redirect("events")

    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = user
            rating.event = event
            rating.save()
            return redirect("/events/"+str(event.pk)+"/")
    else:
        form = RatingForm()

    return render(request, "rating/rating_form.html", {"form": form, "event": event})

@login_required
def ratingDeleteView(request, pk):
    user = request.user
    rating = get_object_or_404(Rating, pk=pk)

    if not (user == rating.user or (user.is_organizer and user == rating.event.organizer)):
        return redirect("events")
    
    if request.method == "POST":
        rating.delete()
        return redirect("/events/"+str(rating.event.pk)+"/")
    return render(request, "rating/rating_confirm_delete.html", {"rating": rating})

@login_required
def ratingUpdateView(request, pk):
    user = request.user
    rating = get_object_or_404(Rating, pk=pk)

    if not (user == rating.user or (user.is_organizer and user == rating.event.organizer)):
        return redirect("events")
    
    if request.method == "POST":
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            form.save()
            return redirect("/events/"+str(rating.event.pk)+"/")
    else:
        form = RatingForm(instance=rating)
    return render(request, "rating/rating_form.html", {"form": form, "rating": rating})
