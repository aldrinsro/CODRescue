import json
from django import template

register = template.Library()

@register.filter
def parse_json(json_string):
    """Parse a JSON string and return the Python object"""
    try:
        return json.loads(json_string)
    except (ValueError, TypeError):
        return {}
