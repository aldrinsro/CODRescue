"""
================================================================================
MODULE GLOBAL: Handlers pour la Gestion des Opérations
================================================================================

Ce module fournit des handlers réutilisables pour la gestion des opérations
associées aux commandes via AJAX.

Fonctionnalités:
- Création d'opérations
- Modification d'opérations existantes
- Suppression d'opérations
- Validation des types d'opérations

Utilisation:
    from common.views.operation_handlers import (
        handle_create_operation,
        handle_update_operation,
        handle_delete_operation
    )

    # Dans votre vue
    if action == 'create_operation':
        return handle_create_operation(request, commande, operateur)

@version 1.0
@author YZ-RESCUE
"""

from django.http import JsonResponse


def handle_update_operation(request, commande, operateur=None):
    """
    Handler générique pour la mise à jour d'une opération existante via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'update_operation':
        >>>     return handle_update_operation(request, commande, operateur)
    """
    from commande.models import Operation
    import logging

    logger = logging.getLogger(__name__)

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    operation_id = request.POST.get('operation_id')
    nouveau_commentaire = request.POST.get('nouveau_commentaire', '').strip()

    print(f"🔄 Mise à jour opération {operation_id} pour commande {commande.id}")
    print(f"📝 Nouveau commentaire: '{nouveau_commentaire}'")

    if not operation_id or not nouveau_commentaire:
        print(f"❌ Données manquantes - operation_id: '{operation_id}', commentaire: '{nouveau_commentaire}'")
        return JsonResponse({
            'success': False,
            'error': 'ID opération et commentaire requis'
        })

    try:
        # ========== 2. RÉCUPÉRATION DE L'OPÉRATION ==========
        try:
            operation = Operation.objects.get(id=operation_id, commande=commande)
        except Operation.DoesNotExist:
            print(f"❌ Opération {operation_id} introuvable pour commande {commande.id}")
            return JsonResponse({
                'success': False,
                'error': 'Opération introuvable'
            })

        # ========== 3. SAUVEGARDE DE L'ANCIEN COMMENTAIRE ==========
        ancien_commentaire = operation.conclusion
        print(f"📋 Ancien commentaire: '{ancien_commentaire}'")

        # ========== 4. MISE À JOUR DE L'OPÉRATION ==========
        operation.conclusion = nouveau_commentaire
        if operateur:
            operation.operateur = operateur  # Mettre à jour l'opérateur qui modifie
        operation.save()

        print(f"✅ Opération {operation_id} sauvegardée en base de données")

        # ========== 5. VÉRIFICATION POST-SAUVEGARDE ==========
        operation_verif = Operation.objects.get(id=operation_id)
        print(f"🔍 Vérification en base: conclusion = '{operation_verif.conclusion}'")

        # ========== 6. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Opération mise à jour avec succès',
            'operation_id': operation_id,
            'nouveau_commentaire': nouveau_commentaire,
            'ancien_commentaire': ancien_commentaire,
            'debug_info': {
                'verification_conclusion': operation_verif.conclusion,
                'total_operations': Operation.objects.filter(commande=commande).count()
            }
        })

    except Exception as e:
        print(f"❌ Erreur mise à jour opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_create_operation(request, commande, operateur=None):
    """
    Handler générique pour la création d'une nouvelle opération via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel mais recommandé)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'create_operation':
        >>>     return handle_create_operation(request, commande, operateur)
    """
    from commande.models import Operation

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    type_operation = request.POST.get('type_operation')
    commentaire = request.POST.get('commentaire', '').strip()

    print(f"🆕 Création nouvelle opération pour commande {commande.id}")
    print(f"📝 Type: '{type_operation}', Commentaire: '{commentaire}'")

    if not type_operation or not commentaire:
        print(f"❌ Données manquantes - type: '{type_operation}', commentaire: '{commentaire}'")
        return JsonResponse({
            'success': False,
            'error': 'Type d\'opération et commentaire requis'
        })

    try:
        # ========== 2. VALIDATION DU TYPE D'OPÉRATION ==========
        allowed_types = {choice[0] for choice in Operation.TYPE_OPERATION_CHOICES}
        if type_operation not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': "Type d'opération non autorisé"
            })

        # ========== 3. CRÉATION DE LA NOUVELLE OPÉRATION ==========
        nouvelle_operation = Operation.objects.create(
            type_operation=type_operation,
            conclusion=commentaire,
            commande=commande,
            operateur=operateur
        )

        print(f"✅ Nouvelle opération créée avec ID: {nouvelle_operation.id}")

        # ========== 4. VÉRIFICATION POST-CRÉATION ==========
        toutes_operations = Operation.objects.filter(commande=commande)
        print(f"📊 {toutes_operations.count()} opération(s) totales pour cette commande")

        # ========== 5. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Nouvelle opération créée avec succès',
            'operation_id': nouvelle_operation.id,
            'type_operation': nouvelle_operation.type_operation,
            'commentaire': nouvelle_operation.conclusion,
            'debug_info': {
                'total_operations': toutes_operations.count(),
                'operation_date': nouvelle_operation.date_operation.strftime('%d/%m/%Y %H:%M')
            }
        })

    except Exception as e:
        print(f"❌ Erreur création opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_delete_operation(request, commande, operateur=None):
    """
    Handler générique pour la suppression d'une opération via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'delete_operation':
        >>>     return handle_delete_operation(request, commande, operateur)
    """
    from commande.models import Operation
    import logging

    logger = logging.getLogger(__name__)

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    operation_id = request.POST.get('operation_id')

    print(f"🗑️ Suppression opération {operation_id} pour commande {commande.id}")

    if not operation_id:
        print(f"❌ Données manquantes - operation_id: '{operation_id}'")
        return JsonResponse({
            'success': False,
            'error': 'ID opération requis'
        })

    try:
        # ========== 2. RÉCUPÉRATION DE L'OPÉRATION ==========
        try:
            operation = Operation.objects.get(
                id=operation_id,
                commande=commande
            )
            print(f"✅ Opération {operation_id} trouvée: {operation.type_operation}")
        except Operation.DoesNotExist:
            print(f"❌ Opération {operation_id} introuvable pour commande {commande.id}")
            return JsonResponse({
                'success': False,
                'error': 'Opération introuvable'
            })

        # ========== 3. SAUVEGARDE DES INFORMATIONS AVANT SUPPRESSION ==========
        operation_info = {
            'id': operation.id,
            'type_operation': operation.type_operation,
            'conclusion': operation.conclusion,
            'date_operation': operation.date_operation.strftime('%d/%m/%Y %H:%M')
        }

        print(f"📋 Informations de l'opération à supprimer:")
        print(f"   - Type: {operation_info['type_operation']}")
        print(f"   - Conclusion: {operation_info['conclusion']}")
        print(f"   - Date: {operation_info['date_operation']}")

        # ========== 4. SUPPRESSION DE L'OPÉRATION ==========
        operation.delete()
        print(f"✅ Opération {operation_id} supprimée avec succès")

        # ========== 5. VÉRIFICATION POST-SUPPRESSION ==========
        operations_restantes = Operation.objects.filter(commande=commande)
        print(f"📊 {operations_restantes.count()} opération(s) restante(s) pour cette commande")

        # ========== 6. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': f'Opération {operation_info["type_operation"]} supprimée avec succès',
            'operation_deleted': operation_info,
            'debug_info': {
                'total_operations_restantes': operations_restantes.count(),
            }
        })

    except Exception as e:
        print(f"❌ Erreur suppression opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


__all__ = [
    'handle_update_operation',
    'handle_create_operation',
    'handle_delete_operation',
]
