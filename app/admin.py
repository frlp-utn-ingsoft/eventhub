
from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'text', 'created_at')  
    list_filter = ('event', 'user')  
    search_fields = ('title', 'text', 'user__username', 'event__title')  
    ordering = ('-created_at',)  