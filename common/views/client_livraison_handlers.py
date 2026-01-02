"""
================================================================================
MODULE GLOBAL: Handlers pour la Gestion Client et Livraison
================================================================================

Ce module fournit des handlers réutilisables pour la gestion des informations
client et de livraison dans les commandes via AJAX.

Fonctionnalités:
- Sauvegarde des informations client (nom, prénom, téléphone)
- Sauvegarde des informations de livraison (ville, adresse)
- Activation/désactivation des frais de livraison
- Recalcul automatique des totaux

Utilisation:
    from common.views.client_livraison_handlers import (
        handle_save_client_info,
        handle_save_livraison,
        handle_toggle_frais_livraison
    )

    # Dans votre vue
    if action == 'save_client_info':
        return handle_save_client_info(request, commande, operateur)

@version 1.0
@author YZ-RESCUE
"""

from django.http import JsonResponse


def handle_save_client_info(request, commande, operateur=None):
    """
    Handler générique pour la sauvegarde des informations du client via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'save_client_info':
        >>>     return handle_save_client_info(request, commande, operateur)
    """
    # ========== 1. RÉCUPÉRATION DES DONNÉES ==========
    nom = request.POST.get('nom', '').strip()
    prenom = request.POST.get('prenom', '').strip()
    telephone = request.POST.get('telephone', '').strip()

    print(f"👤 Sauvegarde infos client: {prenom} {nom}, Tel: {telephone}")

    try:
        # ========== 2. MISE À JOUR DU CLIENT ==========
        client = commande.client
        client.nom = nom
        client.prenom = prenom
        client.numero_tel = telephone
        client.save()

        # ========== 3. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Informations client sauvegardées avec succès'
        })

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des infos client: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_save_livraison(request, commande, operateur=None):
    """
    Handler générique pour la sauvegarde des informations de livraison via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'save_livraison':
        >>>     return handle_save_livraison(request, commande, operateur)
    """
    from parametre.models import Ville

    # ========== 1. RÉCUPÉRATION DES DONNÉES ==========
    ville_id = request.POST.get('ville_livraison')
    adresse = request.POST.get('adresse_livraison', '').strip()

    print(f"🚚 Sauvegarde livraison: Ville ID={ville_id}, Adresse={adresse[:50] if adresse else 'N/A'}")

    try:
        # ========== 2. MISE À JOUR DE LA VILLE ==========
        if ville_id:
            try:
                nouvelle_ville = Ville.objects.get(id=ville_id)
                commande.ville = nouvelle_ville
            except Ville.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Ville de livraison invalide'
                })

        # ========== 3. MISE À JOUR DE L'ADRESSE ==========
        commande.adresse = adresse

        # ========== 4. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()

        # ========== 5. SAUVEGARDE ==========
        commande.save()

        # ========== 6. PRÉPARATION DU MESSAGE DE SUCCÈS ==========
        elements_sauvegardes = []
        if ville_id:
            elements_sauvegardes.append(f"ville: {commande.ville.nom}")
        if adresse:
            elements_sauvegardes.append(f"adresse: {adresse[:50]}{'...' if len(adresse) > 50 else ''}")

        if elements_sauvegardes:
            message = f"Informations de livraison sauvegardées ({', '.join(elements_sauvegardes)})"
        else:
            message = 'Section livraison validée'

        # ========== 7. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': message,
            'ville_nom': commande.ville.nom if commande.ville else None,
            'region_nom': commande.ville.region.nom_region if commande.ville and commande.ville.region else None,
            'frais_livraison': commande.montant_frais_livraison,
            'adresse': adresse,
            'nouveau_total': commande.total_cmd,
            'sous_total_articles': commande.sous_total_articles
        })

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de la livraison: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_toggle_frais_livraison(request, commande, operateur=None):
    """
    Handler générique pour l'activation/désactivation des frais de livraison via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'toggle_frais_livraison':
        >>>     return handle_toggle_frais_livraison(request, commande, operateur)
    """
    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    nouveau_statut = request.POST.get('frais_livraison_actif') == 'true'
    ancien_statut = commande.frais_livraison

    print(f"💰 Toggle frais de livraison: {ancien_statut} → {nouveau_statut}")

    try:
        # ========== 2. MISE À JOUR DU STATUT ==========
        commande.frais_livraison = nouveau_statut
        commande.save()

        # ========== 3. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()

        # ========== 4. PRÉPARATION DU MESSAGE ET DES INFOS D'AFFICHAGE ==========
        if nouveau_statut:
            message = "Frais de livraison activés et inclus dans le total"
            statut_display = "Activés"
            couleur = "green"
        else:
            message = "Frais de livraison désactivés et retirés du total"
            statut_display = "Désactivés"
            couleur = "gray"

        # ========== 5. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': message,
            'nouveau_statut': nouveau_statut,
            'statut_display': statut_display,
            'couleur': couleur,
            'total_commande': float(commande.total_cmd),
            'frais_livraison_ville': float(commande.montant_frais_livraison),
            'ancien_statut': ancien_statut
        })

    except Exception as e:
        print(f"❌ Erreur lors du toggle des frais de livraison: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


__all__ = [
    'handle_save_client_info',
    'handle_save_livraison',
    'handle_toggle_frais_livraison',
]
