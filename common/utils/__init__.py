"""
Module d'utilitaires réutilisables pour la gestion des commandes.

Ce module fournit des fonctions utilitaires pour :
- Gestion du compteur upsell
- Calcul des prix
- Gestion des remises
"""

from .upsell_utils import *
from .prix_utils import *

__all__ = [
    'determiner_type_prix_gele',
    'mettre_a_jour_types_prix_gele_upsell',
    'recalculer_remises_apres_changement_compteur',
    'recalculer_compteur_upsell',
]
