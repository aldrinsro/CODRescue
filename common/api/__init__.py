"""
Module d'APIs réutilisables pour la gestion des commandes.

Ce module fournit des endpoints API génériques pour :
- Gestion des articles (liste, variantes, rafraîchissement)
- Gestion des remises (application, retrait, aperçu)

@version 1.0
@author YZ-RESCUE
"""

from .article_api import (
    api_articles_disponibles,
    get_article_variants,
    rafraichir_articles_section,
)

from .remise_api import (
    appliquer_remise_panier,
    retirer_remise_panier,
    calculer_remise_panier_preview,
)

__all__ = [
    # Article APIs
    'api_articles_disponibles',
    'get_article_variants',
    'rafraichir_articles_section',

    # Remise APIs
    'appliquer_remise_panier',
    'retirer_remise_panier',
    'calculer_remise_panier_preview',
]
