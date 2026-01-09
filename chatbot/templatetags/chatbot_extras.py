"""
Template tags personnalisés pour le chatbot.
"""
from django import template

register = template.Library()


@register.filter
def interface_label(interface_type):
    """Retourne le libellé français de l'interface."""
    labels = {
        'CONFIRMATION': 'Confirmation',
        'PREPARATION': 'Préparation',
        'LOGISTIQUE': 'Logistique',
        'SUPERVISION': 'Supervision',
        'ADMIN': 'Administration',
    }
    return labels.get(interface_type, 'Non définie')


@register.filter
def interface_icon(interface_type):
    """Retourne l'icône associée à l'interface."""
    icons = {
        'CONFIRMATION': '✓',
        'PREPARATION': '📦',
        'LOGISTIQUE': '🚚',
        'SUPERVISION': '📊',
        'ADMIN': '⚙️',
    }
    return icons.get(interface_type, '💬')


@register.filter
def interface_color(interface_type):
    """Retourne la couleur associée à l'interface."""
    colors = {
        'CONFIRMATION': '#4CAF50',  # Vert
        'PREPARATION': '#FF9800',   # Orange
        'LOGISTIQUE': '#2196F3',    # Bleu
        'SUPERVISION': '#9C27B0',   # Violet
        'ADMIN': '#607D8B',         # Gris-bleu
    }
    return colors.get(interface_type, '#4CAF50')
