"""
Utilitaires spécifiques au module commande.

Ce module importe les fonctions génériques depuis common.date_utils
et fournit des wrappers spécifiques pour le modèle Commande.
"""

from django.db.models import QuerySet

from common.date_utils import search_by_date, try_parse_date, parse_date_input
from .models import Commande

# Réexporter les fonctions génériques pour la rétrocompatibilité
_try_parse_date = try_parse_date
_parse_date_input = parse_date_input


def search_commandes_by_date(date_input: str, field: str = 'date_creation') -> QuerySet:
    """Retourne un QuerySet de Commande filtré par date.

    Cette fonction est un wrapper autour de la fonction générique search_by_date
    spécifiquement pour le modèle Commande.

    Args:
        date_input: Chaîne représentant une date, une plage ou une expression naturelle
        field: Nom du champ du modèle à filtrer (défaut: 'date_creation')

    Returns:
        QuerySet Django filtré (non-évalué)

    Examples:
        >>> search_commandes_by_date('2025-11-12')
        >>> search_commandes_by_date('12/11/2025')
        >>> search_commandes_by_date('2025-11-01 - 2025-11-10')
        >>> search_commandes_by_date('2025-11')  # mois complet
        >>> search_commandes_by_date('cette semaine')
        >>> search_commandes_by_date('7 derniers jours')
    """
    return search_by_date(Commande, date_input, field)
