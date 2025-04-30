
from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event', 'created_at')  # Campos visibles en la lista
    list_filter = ('event', 'user')  # Filtros laterales
    search_fields = ('title', 'text', 'user__username', 'event__title')  # Campos para búsqueda
    ordering = ('-created_at',)  # Orden por defecto (más recientes primero)