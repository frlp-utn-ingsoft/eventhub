from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RatingForm
from .models import Rating
from app.models import Event

@login_required
def ratingCreateView(request, id):
    user = request.user
    event = get_object_or_404(Event, id=id)

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