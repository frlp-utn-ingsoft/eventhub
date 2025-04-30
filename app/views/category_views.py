from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from app.models import Category

@login_required
def category_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("name")
        description = request.POST.get("description")
        if id is None:
            Category.new(title, description, is_active=True)
        else:
            category = get_object_or_404(Category, pk=id)
            category.update(title, description, request.user, is_active=True)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # refresh last screen
