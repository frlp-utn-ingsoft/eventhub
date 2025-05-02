from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def count_unread_notifications(notifications_dict):
    unread_count = sum(1 for notification in notifications_dict.values() if not notification.is_read)
    return unread_count