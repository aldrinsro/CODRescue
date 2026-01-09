"""
Module de vues réutilisables pour la gestion des commandes.

Ce module fournit des vues génériques et réutilisables pour la modification
et la gestion des commandes à travers différentes applications.

@version 1.0
@author YZ-RESCUE
"""

from .article_handlers import (
    handle_add_article,
    handle_delete_article,
    handle_update_quantity,
)

from .client_livraison_handlers import (
    handle_save_client_info,
    handle_save_livraison,
    handle_toggle_frais_livraison,
)

from .operation_handlers import (
    handle_update_operation,
    handle_create_operation,
    handle_delete_operation,
)

__all__ = [
    # Article Handlers
    'handle_add_article',
    'handle_delete_article',
    'handle_update_quantity',

    # Client & Livraison Handlers
    'handle_save_client_info',
    'handle_save_livraison',
    'handle_toggle_frais_livraison',

    # Operation Handlers
    'handle_update_operation',
    'handle_create_operation',
    'handle_delete_operation',
]
