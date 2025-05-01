# category/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Category
from .forms import CategoryForm

@login_required
def category_list(request):
    if not request.user.is_organizer:
        return redirect("events")

    categories = Category.objects.all().order_by("name")
    return render(request, "category/category_list.html", {"object_list": categories})


@login_required
def category_create(request):
    if not request.user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("category:list")
    else:
        form = CategoryForm()

    return render(request, "category/category_form.html", {"form": form})


@login_required
def category_update(request, pk):
    if not request.user.is_organizer:
        return redirect("events")

    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("category:list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "category/category_form.html", {"form": form})


@login_required
def category_delete(request, pk):
    if not request.user.is_organizer:
        return redirect("events")

    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        return redirect("category:list")

    return render(request, "category/category_confirm_delete.html", {"object": category})