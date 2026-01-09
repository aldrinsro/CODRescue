"""
================================================================================
MODULE GLOBAL: API pour la Gestion des Remises Personnalisées
================================================================================

Ce module fournit des APIs réutilisables pour la gestion des remises personnalisées
sur les paniers de commandes via AJAX.

Fonctionnalités:
- Application de remises personnalisées (pourcentage ou montant fixe)
- Retrait de remises existantes
- Calcul d'aperçu de remise sans application

Utilisation:
    from common.api.remise_api import (
        appliquer_remise_panier,
        retirer_remise_panier,
        calculer_remise_panier_preview
    )

    # Dans votre urls.py
    path('api/panier/<int:panier_id>/appliquer-remise/', appliquer_remise_panier),
    path('api/panier/<int:panier_id>/retirer-remise/', retirer_remise_panier),
    path('api/panier/<int:panier_id>/preview-remise/', calculer_remise_panier_preview),

@version 1.0
@author YZ-RESCUE
"""

from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
import json


def appliquer_remise_panier(request, panier_id, operateur=None):
    """
    Applique une remise personnalisée sur un panier spécifique.

    La remise est calculée sur le sous_total du panier (pas sur prix_panier).
    Cette fonction crée une RemisePanier et recalcule automatiquement les totaux.

    Args:
        request: L'objet HttpRequest contenant les données POST (JSON)
        panier_id: L'ID du panier sur lequel appliquer la remise
        operateur: L'opérateur effectuant l'action (optionnel)

    Paramètres attendus (POST JSON):
        - type_remise: 'POURCENTAGE' ou 'MONTANT_FIXE'
        - valeur_remise: La valeur de la remise (pourcentage ou montant en DH)
        - raison_remise: (optionnel) Motif de la remise

    Returns:
        JsonResponse avec:
        {
            'success': True,
            'message': str,
            'data': {
                'panier_id': int,
                'sous_total_original': float,
                'montant_remise': float,
                'nouveau_sous_total': float,
                'nouveau_total_commande': float,
                'type_remise': str,
                'valeur_remise': float,
                'raison_remise': str
            }
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch('/api/panier/123/appliquer-remise/', {
        >>>     method: 'POST',
        >>>     body: JSON.stringify({
        >>>         type_remise: 'POURCENTAGE',
        >>>         valeur_remise: 10,
        >>>         raison_remise: 'Client fidèle'
        >>>     }),
        >>>     headers: {'Content-Type': 'application/json'}
        >>> });
    """
    from commande.models import Panier, RemisePanier

    try:
        # ========== 1. RÉCUPÉRATION DU PANIER ==========
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        commande = panier.commande

        print(f"💰 Application remise sur panier {panier_id} (Commande {commande.id})")

        # ========== 2. PARSING DES DONNÉES JSON ==========
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Format JSON invalide'
            }, status=400)

        type_remise = data.get('type_remise', 'POURCENTAGE')
        valeur_remise = data.get('valeur_remise')
        raison_remise = data.get('raison_remise', '')

        # ========== 3. VALIDATION DES DONNÉES ==========
        if not valeur_remise:
            return JsonResponse({
                'success': False,
                'error': 'La valeur de la remise est requise'
            }, status=400)

        try:
            valeur_remise = Decimal(str(valeur_remise))
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Valeur de remise invalide'
            }, status=400)

        if valeur_remise <= 0:
            return JsonResponse({
                'success': False,
                'error': 'La valeur de la remise doit être supérieure à 0'
            }, status=400)

        # ========== 4. CALCUL DU SOUS-TOTAL ACTUEL ==========
        # Calculer le sous-total basé sur le prix effectif actuel (upsells, promo, liquidation)
        from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

        prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
        quantite = Decimal(str(panier.quantite))
        sous_total_actuel = prix_unitaire_effectif * quantite

        print(f"📊 Sous-total actuel: {sous_total_actuel} DH")

        # ========== 5. VALIDATION SPÉCIFIQUE POURCENTAGE ==========
        # On ne travaille qu'en pourcentage
        type_remise = 'POURCENTAGE'

        # Contrainte: Le pourcentage ne doit pas dépasser 100%
        if valeur_remise > Decimal('100'):
            return JsonResponse({
                'success': False,
                'error': 'Le pourcentage de remise ne peut pas dépasser 100%'
            }, status=400)

        # ========== 6. VÉRIFICATION REMISE EXISTANTE ==========
        if hasattr(panier, 'remise_personnalisee'):
            return JsonResponse({
                'success': False,
                'error': 'Une remise est déjà appliquée sur ce panier. Veuillez d\'abord la retirer.'
            }, status=400)

        # ========== 7. CRÉATION ET APPLICATION DE LA REMISE ==========
        with transaction.atomic():
            remise = RemisePanier.objects.create(
                panier=panier,
                type_remise=type_remise,
                valeur_remise=valeur_remise,
                raison_remise=raison_remise,
                operateur=operateur
            )

            print(f"✅ RemisePanier créée (ID: {remise.id})")

            # Appliquer la remise (calcule et modifie le sous_total du panier)
            # La méthode appliquer_remise() sauvegarde automatiquement le sous-total original dans panier.sous_total_remise
            nouveau_sous_total = remise.appliquer_remise()

            print(f"📉 Nouveau sous-total après remise: {nouveau_sous_total} DH")

            # Recalculer le total de la commande avec les frais de livraison
            commande.recalculer_total_avec_frais()

        # ========== 8. RÉCUPÉRATION DES DONNÉES FINALES ==========
        panier.refresh_from_db()
        sous_total_original = Decimal(str(panier.sous_total_remise))

        print(f"✅ Remise appliquée avec succès: {remise.montant_applique} DH")

        # ========== 9. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': f'Remise de {remise.montant_applique:.2f} DH appliquée avec succès',
            'data': {
                'panier_id': panier.id,
                'sous_total_original': float(sous_total_original),
                'montant_remise': float(remise.montant_applique),
                'nouveau_sous_total': float(nouveau_sous_total),
                'nouveau_total_commande': float(commande.total_cmd),
                'type_remise': remise.type_remise,
                'valeur_remise': float(remise.valeur_remise),
                'raison_remise': remise.raison_remise
            }
        })

    except Panier.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Panier non trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans appliquer_remise_panier: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'application de la remise: {str(e)}'
        }, status=500)


def retirer_remise_panier(request, panier_id, operateur=None):
    """
    Retire une remise appliquée sur un panier.

    Cette fonction supprime la RemisePanier et restaure le sous_total original.

    Args:
        request: L'objet HttpRequest
        panier_id: L'ID du panier dont retirer la remise
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec:
        {
            'success': True,
            'message': str,
            'data': {
                'panier_id': int,
                'sous_total_restaure': float,
                'montant_remise_retiree': float,
                'nouveau_total_commande': float
            }
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch('/api/panier/123/retirer-remise/', {
        >>>     method: 'POST'
        >>> });
    """
    from commande.models import Panier, RemisePanier

    try:
        # ========== 1. RÉCUPÉRATION DU PANIER ==========
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        commande = panier.commande

        print(f"🗑️ Retrait remise du panier {panier_id} (Commande {commande.id})")

        # ========== 2. VÉRIFICATION REMISE EXISTANTE ==========
        if not hasattr(panier, 'remise_personnalisee'):
            return JsonResponse({
                'success': False,
                'error': 'Aucune remise n\'est appliquée sur ce panier'
            }, status=400)

        remise = panier.remise_personnalisee
        montant_remise_retiree = Decimal(str(remise.montant_applique))

        print(f"📋 Remise à retirer: {montant_remise_retiree} DH ({remise.type_remise})")

        # ========== 3. RETRAIT DE LA REMISE ==========
        with transaction.atomic():
            sous_total_restaure = remise.retirer_remise()

            print(f"↩️ Sous-total restauré: {sous_total_restaure} DH")

            # Recalculer le total de la commande avec les frais de livraison
            commande.recalculer_total_avec_frais()

        print(f"✅ Remise retirée avec succès")

        # ========== 4. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': f'Remise de {montant_remise_retiree:.2f} DH retirée avec succès',
            'data': {
                'panier_id': panier.id,
                'sous_total_restaure': float(sous_total_restaure),
                'montant_remise_retiree': float(montant_remise_retiree),
                'nouveau_total_commande': float(commande.total_cmd)
            }
        })

    except Panier.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Panier non trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans retirer_remise_panier: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du retrait de la remise: {str(e)}'
        }, status=500)


def calculer_remise_panier_preview(request, panier_id):
    """
    Calcule et retourne un aperçu de la remise sans l'appliquer.

    Utile pour afficher le montant et les nouveaux totaux avant confirmation
    de l'application de la remise.

    Args:
        request: L'objet HttpRequest
        panier_id: L'ID du panier pour lequel calculer l'aperçu

    Paramètres GET:
        - type_remise: 'POURCENTAGE' ou 'MONTANT_FIXE'
        - valeur_remise: La valeur de la remise

    Returns:
        JsonResponse avec:
        {
            'success': True,
            'data': {
                'panier_id': int,
                'article_nom': str,
                'quantite': int,
                'sous_total_actuel': float,
                'montant_remise_calcule': float,
                'sous_total_apres_remise': float,
                'pourcentage_reduction': float,
                'type_remise': str,
                'valeur_remise': float
            }
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch('/api/panier/123/preview-remise/?type_remise=POURCENTAGE&valeur_remise=10')
        >>>     .then(response => response.json())
        >>>     .then(data => {
        >>>         console.log(`Remise: ${data.data.montant_remise_calcule} DH`);
        >>>     });
    """
    from commande.models import Panier

    try:
        # ========== 1. RÉCUPÉRATION DU PANIER ==========
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        print(f"👁️ Preview remise pour panier {panier_id}")

        # ========== 2. RÉCUPÉRATION DES PARAMÈTRES ==========
        type_remise = request.GET.get('type_remise', 'POURCENTAGE')
        valeur_remise = request.GET.get('valeur_remise')

        if not valeur_remise:
            return JsonResponse({
                'success': False,
                'error': 'La valeur de la remise est requise'
            }, status=400)

        try:
            valeur_remise = Decimal(str(valeur_remise))
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Valeur de remise invalide'
            }, status=400)

        if valeur_remise <= 0:
            return JsonResponse({
                'success': False,
                'error': 'La valeur de la remise doit être supérieure à 0'
            }, status=400)

        # ========== 3. CALCUL DU SOUS-TOTAL ACTUEL ==========
        # Calculer le sous-total basé sur le prix effectif actuel (upsells, promo, liquidation)
        from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

        prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
        quantite = Decimal(str(panier.quantite))
        sous_total_actuel = prix_unitaire_effectif * quantite

        # ========== 4. VALIDATION ET CALCUL DE LA REMISE ==========
        # On ne travaille qu'en pourcentage
        type_remise = 'POURCENTAGE'

        # Contrainte: Le pourcentage ne doit pas dépasser 100%
        if valeur_remise > Decimal('100'):
            return JsonResponse({
                'success': False,
                'error': 'Le pourcentage de remise ne peut pas dépasser 100%'
            }, status=400)

        montant_remise = sous_total_actuel * (valeur_remise / Decimal('100'))
        pourcentage_reduction = valeur_remise

        # Limiter la remise au sous-total (sécurité supplémentaire)
        if montant_remise > sous_total_actuel:
            montant_remise = sous_total_actuel

        sous_total_apres_remise = sous_total_actuel - montant_remise

        print(f"📊 Preview: {sous_total_actuel} DH - {montant_remise} DH = {sous_total_apres_remise} DH")

        # ========== 5. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'data': {
                'panier_id': panier.id,
                'article_nom': panier.article.nom,
                'quantite': panier.quantite,
                'sous_total_actuel': float(sous_total_actuel),
                'montant_remise_calcule': float(montant_remise),
                'sous_total_apres_remise': float(sous_total_apres_remise),
                'pourcentage_reduction': float(pourcentage_reduction),
                'type_remise': type_remise,
                'valeur_remise': float(valeur_remise)
            }
        })

    except Panier.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Panier non trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans calculer_remise_panier_preview: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du calcul de la remise: {str(e)}'
        }, status=500)


__all__ = [
    'appliquer_remise_panier',
    'retirer_remise_panier',
    'calculer_remise_panier_preview',
]
