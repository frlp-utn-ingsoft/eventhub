import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Comment


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    comments = event.comments.all().order_by("-created_at") # type: ignore
    return render(request, "app/event_detail.html", {"event": event, "user_is_organizer": request.user == event.organizer, "comments": comments})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )

###################################################################################

@login_required
def comments(request):
    if not request.user.is_organizer:
        return redirect("events")

    comments = Comment.objects.filter(event__organizer=request.user).order_by("-created_at")
    return render(
        request,
        "app/comments/comments.html",
        {"comments": comments, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def comment_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    comments = Comment.objects.filter(event=event).order_by('-created_at')
    return render(
        request,
        "app/comments/comment_list.html",
        {"comments": comments, "user": request.user, "user_is_organizer": request.user == event.organizer, "event": event}
    )
 

@login_required
def comment_detail(request, comment_id):
    if not request.user.is_organizer:
        return redirect("events")
    comment = get_object_or_404(Comment, pk=comment_id)
    return render(request, "app/comments/comment_detail.html", {"comment": comment})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.user != request.user and comment.event.organizer != request.user:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.method == "POST":
        next_url = request.POST.get("next")
        comment.delete()
        return redirect(next_url)

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def comment_form(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")

        success, result = Comment.new(title, text, request.user, event)

        if success:
            return redirect("event_detail", id=event_id)
        else:
            return render(
                request,
                "app/event_detail.html",{
                    "errors": result,
                    "event": event,
                    "comment": {
                        "title": title,
                        "text": text
                },
                "comments": event.comments.all() # type: ignore
                }
            )
        
    return redirect("event_detail", id=event_id)

@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.user != request.user and comment.event.organizer != request.user:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        next_url = request.POST.get("next")
        
        success, result = comment.update(title, text)

        if success:
            if next_url:
                return redirect(next_url)
            
            if comment.user == comment.event.organizer:
                return redirect("comments")
            else:
                return redirect("event_detail", id=comment.event.pk)
        else:
            return render(request, "app/comments/comment_edit.html", {
                "comment": {
                    "id": comment.pk,
                    "title": title,
                    "text": text,
                    "user": comment.user,
                    "event": comment.event
                },
                "errors": result,
                "next_url": next_url
            })
    
    next_url = request.GET.get("next", "/")
    return render(request, "app/comments/comment_edit.html", {
        "comment": comment,
        "next_url": next_url
    })