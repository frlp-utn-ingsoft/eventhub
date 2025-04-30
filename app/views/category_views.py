from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from app.models import Category

@login_required
def category_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        category_id = request.POST.get("id")
        title = request.POST.get("name")
        description = request.POST.get("description")

        if category_id is None:
            success, data = Category.new(title, description, is_active=True)
            if not success:
                categories = Category.objects.all()
                return render(
                    request,
                    "app/category/categories.html",
                    {
                        "errors": data,
                        "category": category, 
                        "user_is_organizer": request.user.is_organizer, 
                        "categories": categories
                    },
                )
        else:
            category = get_object_or_404(Category, pk=category_id)
            category.update(title, description, is_active=True)
        return redirect("categories")
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # refresh last screen


@login_required
def categories(request):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    categories = Category.objects.all()
    return render(
        request,
        "app/category/categories.html",
        {"categories": categories},
    )

@login_required
def category_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        event = get_object_or_404(Category, pk=id)
        event.delete()
        return redirect("categories")

    return redirect("events")
