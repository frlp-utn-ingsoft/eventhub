from django.contrib import admin
from .models import Event, Category, Rating, Comment, Notification, User, Venue

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'scheduled_at', 'created_at')
    list_filter = ('scheduled_at', 'created_at', 'categories')
    search_fields = ('title', 'description')
    filter_horizontal = ('categories', 'attendees')
    date_hierarchy = 'scheduled_at'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('event__title', 'user__username', 'comment')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'text', 'user__username', 'event__title')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'priority', 'created_at', 'is_read')
    list_filter = ('priority', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'event__title')
    filter_horizontal = ('users',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_organizer', 'is_staff')
    list_filter = ('is_organizer', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'adress', 'capacity')
    search_fields = ('name', 'adress') 