from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary is None:
        return 0
    try:
        # Convert string key to int if needed
        if isinstance(key, str):
            key = int(key)
        return dictionary.get(key, 0)
    except (ValueError, TypeError, AttributeError):
        return 0
