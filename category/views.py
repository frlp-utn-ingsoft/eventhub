# category/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Category
from .forms  import CategoryForm


class CategoryCreateView(CreateView):
    model         = Category
    form_class    = CategoryForm
    template_name = "category/category_form.html"
    success_url   = reverse_lazy("category:list")


class CategoryListView(ListView):
    model         = Category
    template_name = "category/category_list.html"
    paginate_by   = 10
    ordering      = ["name"]


class CategoryUpdateView(UpdateView):
    model         = Category
    form_class    = CategoryForm
    template_name = "category/category_form.html"
    success_url   = reverse_lazy("category:list")


class CategoryDeleteView(DeleteView):
    model         = Category
    template_name = "category/category_confirm_delete.html"
    success_url   = reverse_lazy("category:list")
