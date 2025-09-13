import json
import html
from django import template

register = template.Library()

@register.filter
def decode_unicode_json(value):
    """
    Décode les séquences Unicode dans un JSON et retourne une chaîne lisible
    """
    if not value:
        return value
    
    try:
        # Si c'est un JSON, le parser et le reformater
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            data = json.loads(value)
            # Formater le JSON de manière lisible
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
            return formatted
        else:
            # Si ce n'est pas un JSON, décoder les séquences Unicode
            return value.encode().decode('unicode_escape')
    except (json.JSONDecodeError, UnicodeDecodeError):
        # En cas d'erreur, retourner la valeur originale
        return value

@register.filter
def format_operation_conclusion(value):
    """
    Formate la conclusion d'une opération pour un affichage lisible
    """
    if not value:
        return "-"
    
    try:
        # Si c'est un JSON, le parser et formater
        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
            data = json.loads(value)
            
            # Formater selon le type d'opération
            if isinstance(data, dict):
                if 'ancien_etat' in data and 'nouvel_etat' in data:
                    # Opération de changement d'état
                    return f"État changé de '{data['ancien_etat']}' vers '{data['nouvel_etat']}'"
                elif 'commentaire' in data:
                    return data['commentaire']
                else:
                    # Autres types de JSON
                    return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            # Si ce n'est pas un JSON, retourner tel quel
            return value
    except (json.JSONDecodeError, UnicodeDecodeError):
        # En cas d'erreur, retourner la valeur originale
        return value
