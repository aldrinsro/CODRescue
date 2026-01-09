"""
================================================================================
MODULE GLOBAL: Handlers pour la Gestion des Articles
================================================================================

Ce module fournit des handlers réutilisables pour la gestion des articles
dans les commandes via AJAX.

Fonctionnalités:
- Ajout d'articles (avec ou sans variantes)
- Suppression d'articles du panier
- Modification de quantité d'articles
- Gestion automatique du compteur upsell
- Gestion automatique des remises

Utilisation:
    from common.views.article_handlers import (
        handle_add_article,
        handle_delete_article,
        handle_update_quantity
    )

    # Dans votre vue
    if action == 'add_article':
        return handle_add_article(request, commande, operateur)

@version 1.0
@author YZ-RESCUE
"""

from django.http import JsonResponse
from common.utils.upsell_utils import (
    determiner_type_prix_gele,
    recalculer_compteur_upsell
)


def handle_add_article(request, commande, operateur=None):
    """
    Handler générique pour l'ajout d'un article à une commande via AJAX.

    Cette fonction:
    - Gère les articles avec ou sans variantes
    - Évite les doublons (incrémente la quantité si l'article existe)
    - Recalcule automatiquement les compteurs upsell
    - Met à jour tous les totaux

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'add_article':
        >>>     return handle_add_article(request, commande, operateur)
    """
    from commande.models import Panier
    from article.models import Article, VarianteArticle
    from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    article_id = request.POST.get('article_id')
    try:
        quantite = int(request.POST.get('quantite', 1))
        if quantite < 1:
            return JsonResponse({
                'success': False,
                'error': 'La quantité doit être au moins 1'
            })
        if quantite > 999:
            return JsonResponse({
                'success': False,
                'error': 'La quantité ne peut pas dépasser 999'
            })
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Quantité invalide'
        })

    variante_id = request.POST.get('variante_id')

    print(f"📦 Ajout article: ID={article_id}, Qté={quantite}, Variante={variante_id}")

    try:
        # ========== 2. RECHERCHE DE L'ARTICLE ET DE LA VARIANTE ==========
        article = None
        variante_obj = None

        # Essayer d'abord de trouver l'article directement
        try:
            article = Article.objects.get(id=article_id, actif=True)
            print(f"✅ Article trouvé directement: {article.nom}")

            # Si une variante est spécifiée, la récupérer
            if variante_id and variante_id not in ['null', '']:
                try:
                    variante_id_int = int(variante_id)
                    variante_obj = VarianteArticle.objects.get(
                        id=variante_id_int,
                        article=article,
                        actif=True
                    )
                    print(f"✅ Variante vérifiée: {variante_obj.id}")
                except (ValueError, VarianteArticle.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': f'La variante sélectionnée (ID: {variante_id}) n\'existe pas ou n\'est pas active.',
                        'message': 'Veuillez sélectionner une variante valide.'
                    })

        except Article.DoesNotExist:
            # Peut-être que c'est l'ID d'une variante directement
            try:
                variante_obj = VarianteArticle.objects.get(id=article_id, actif=True)
                article = variante_obj.article
                print(f"✅ Variante trouvée: {variante_obj} -> Article: {article.nom}")
            except VarianteArticle.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Article ou variante avec l\'ID {article_id} non trouvé ou désactivé.'
                })

        # Vérifier que l'article est actif
        if not article or not article.actif:
            return JsonResponse({
                'success': False,
                'error': 'Article inactif ou introuvable'
            })

        # ========== 3. VÉRIFICATION DES DOUBLONS ==========
        if variante_obj:
            panier_existant = Panier.objects.filter(
                commande=commande,
                article=article,
                variante=variante_obj
            ).first()
        else:
            panier_existant = Panier.objects.filter(
                commande=commande,
                article=article,
                variante__isnull=True
            ).first()

        # ========== 4. CRÉATION OU MISE À JOUR DU PANIER ==========
        if panier_existant:
            # Article existe déjà → Incrémenter la quantité
            panier_existant.quantite += quantite
            panier_existant.sous_total = float(panier_existant.prix_panier * panier_existant.quantite)
            panier_existant.save()
            panier = panier_existant
            print(f"🔄 Article existant mis à jour: ID={article.id}, nouvelle quantité={panier.quantite}")
        else:
            # Nouvel article → Créer un panier
            prix_panier_initial = get_prix_upsell_avec_compteur(article, commande.compteur)
            sous_total_initial = float(prix_panier_initial * quantite)
            type_prix = determiner_type_prix_gele(article, commande.compteur)

            panier = Panier.objects.create(
                commande=commande,
                article=article,
                quantite=quantite,
                prix_panier=float(prix_panier_initial),
                sous_total=sous_total_initial,
                variante=variante_obj,
                type_prix_gele=type_prix
            )
            print(f"➕ Nouvel article ajouté: ID={article.id}, quantité={quantite}, type_prix_gele={type_prix}")

        # ========== 5. RECALCUL DU COMPTEUR UPSELL ==========
        if article.isUpsell:
            recalculer_compteur_upsell(commande)

        # ========== 6. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()

        # ========== 7. RÉPONSE JSON ==========
        message = 'Article ajouté avec succès' if not panier_existant else f'Quantité mise à jour ({panier.quantite})'

        return JsonResponse({
            'success': True,
            'message': message,
            'article_id': panier.id,
            'total_commande': float(commande.total_cmd),
            'nb_articles': commande.paniers.count(),
            'compteur': commande.compteur,
            'was_update': panier_existant is not None,
            'new_quantity': panier.quantite
        })

    except Article.DoesNotExist as e:
        return JsonResponse({
            'success': False,
            'error': f'Article ou variante avec l\'ID {article_id} non trouvé ou désactivé. {str(e)}'
        })
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout d'article: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_delete_article(request, commande, operateur=None):
    """
    Handler générique pour la suppression d'un article du panier via AJAX.

    Cette fonction:
    - Supprime un article/panier de la commande
    - Recalcule automatiquement les compteurs upsell si nécessaire
    - Met à jour tous les totaux de la commande
    - Retourne les nouvelles valeurs pour mise à jour de l'interface

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'delete_panier':
        >>>     return handle_delete_article(request, commande, operateur)
    """
    from commande.models import Panier

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    panier_id = request.POST.get('panier_id')

    if not panier_id:
        return JsonResponse({
            'success': False,
            'error': 'ID du panier non spécifié'
        })

    try:
        # ========== 2. RÉCUPÉRATION DU PANIER À SUPPRIMER ==========
        try:
            panier = Panier.objects.get(id=panier_id, commande=commande)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Article avec l\'ID panier {panier_id} non trouvé dans cette commande'
            })

        # ========== 3. SAUVEGARDE DES INFORMATIONS AVANT SUPPRESSION ==========
        article_nom = panier.article.nom
        etait_upsell = panier.article.isUpsell

        print(f"🗑️ Suppression panier {panier_id}: {article_nom} (upsell: {etait_upsell})")

        # ========== 4. SUPPRESSION DU PANIER ==========
        panier.delete()

        # ========== 5. RECALCUL DU COMPTEUR UPSELL SI NÉCESSAIRE ==========
        if etait_upsell:
            recalculer_compteur_upsell(commande)

        # ========== 6. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()

        # ========== 7. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': f'Article "{article_nom}" supprimé avec succès',
            'total_commande': float(commande.total_cmd),
            'nb_articles': commande.paniers.count(),
            'compteur': commande.compteur
        })

    except Exception as e:
        print(f"❌ Erreur lors de la suppression du panier: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def handle_update_quantity(request, commande, operateur=None):
    """
    Handler générique pour la modification de la quantité d'un article via AJAX.

    Cette fonction:
    - Modifie la quantité d'un article dans le panier
    - Préserve le prix_panier gelé historiquement
    - Recalcule le compteur upsell si nécessaire
    - Recalcule les remises si appliquées
    - Met à jour tous les totaux

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action (optionnel)

    Returns:
        JsonResponse avec le statut de l'opération

    Example:
        >>> # Dans votre vue
        >>> if action == 'update_quantity':
        >>>     return handle_update_quantity(request, commande, operateur)
    """
    from commande.models import Panier

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    panier_id = request.POST.get('panier_id')

    try:
        nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 1))
        if nouvelle_quantite < 1:
            return JsonResponse({
                'success': False,
                'error': 'La quantité doit être au moins 1'
            })
        if nouvelle_quantite > 999:
            return JsonResponse({
                'success': False,
                'error': 'La quantité ne peut pas dépasser 999'
            })
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Quantité invalide'
        })

    try:
        # ========== 2. RÉCUPÉRATION DU PANIER ==========
        try:
            panier = Panier.objects.get(id=panier_id, commande=commande)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Article avec l\'ID panier {panier_id} non trouvé dans cette commande'
            })

        # ========== 3. SAUVEGARDE DES INFORMATIONS ==========
        ancienne_quantite = panier.quantite
        etait_upsell = panier.article.isUpsell

        print(f"🔢 Modification quantité panier {panier_id}: {ancienne_quantite} → {nouvelle_quantite}")

        # ========== 4. MODIFICATION DE LA QUANTITÉ ==========
        # IMPORTANT: Le prix_panier reste INCHANGÉ (prix historique gelé)
        panier.quantite = nouvelle_quantite
        panier.save()

        # ========== 5. RECALCUL DU COMPTEUR UPSELL SI NÉCESSAIRE ==========
        # IMPORTANT: recalculer_compteur_upsell gère automatiquement le recalcul des remises
        if etait_upsell:
            recalculer_compteur_upsell(commande)
            # Rafraîchir le panier pour avoir les données à jour
            panier.refresh_from_db()
            commande.refresh_from_db()

        # ========== 6. GESTION DE LA REMISE SI APPLIQUÉE ET SI PAS UPSELL ==========
        # Si c'était un article upsell, la remise a déjà été recalculée dans recalculer_compteur_upsell
        # On ne recalcule la remise manuellement que pour les articles non-upsell
        from decimal import Decimal
        from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

        remise_info = None  # Pour la réponse JSON

        if not etait_upsell and hasattr(panier, 'remise_personnalisee'):
            remise = panier.remise_personnalisee

            print(f"🏷️ Remise détectée sur panier non-upsell {panier_id}: {remise.type_remise} {remise.valeur_remise}")

            # Calculer le sous-total basé sur le prix effectif actuel
            prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
            quantite = Decimal(str(nouvelle_quantite))
            nouveau_sous_total_sans_remise = prix_unitaire_effectif * quantite

            # Mettre à jour le sous_total_remise
            panier.sous_total_remise = float(nouveau_sous_total_sans_remise)

            # Recalculer le montant de la remise
            montant_remise = remise.calculer_montant_remise()
            remise.montant_applique = float(montant_remise)
            remise.save()

            # Calculer le nouveau sous-total AVEC remise
            nouveau_sous_total_avec_remise = nouveau_sous_total_sans_remise - montant_remise

            # Appliquer le sous-total avec remise
            panier.sous_total = float(nouveau_sous_total_avec_remise)
            panier.save()

            print(f"   ✅ Remise recalculée: {nouveau_sous_total_sans_remise} DH - {montant_remise} DH = {nouveau_sous_total_avec_remise} DH")

            # Préparer les infos de remise pour la réponse JSON
            remise_info = {
                'sous_total_original': float(nouveau_sous_total_sans_remise),
                'montant_remise': float(montant_remise),
                'nouveau_sous_total': float(nouveau_sous_total_avec_remise),
                'type_remise': remise.type_remise,
                'valeur_remise': float(remise.valeur_remise)
            }
        elif not etait_upsell:
            # Pas de remise et pas upsell: recalculer le sous-total basé sur le prix effectif
            prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
            quantite = Decimal(str(nouvelle_quantite))
            panier.sous_total = float(prix_unitaire_effectif * quantite)
            panier.save()

        # Si c'était un article upsell avec remise, récupérer les infos pour la réponse
        if etait_upsell and hasattr(panier, 'remise_personnalisee'):
            panier.refresh_from_db()
            remise = panier.remise_personnalisee
            remise_info = {
                'sous_total_original': float(panier.sous_total_remise),
                'montant_remise': float(remise.montant_applique),
                'nouveau_sous_total': float(panier.sous_total),
                'type_remise': remise.type_remise,
                'valeur_remise': float(remise.valeur_remise)
            }

        # ========== 7. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()

        # ========== 8. CALCUL DU PRIX UNITAIRE EFFECTIF POUR L'AFFICHAGE ==========
        # Pour les articles upsells, le prix unitaire change selon le compteur
        prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)

        # ========== 9. RÉPONSE JSON ==========
        response_data = {
            'success': True,
            'message': f'Quantité modifiée de {ancienne_quantite} à {nouvelle_quantite}',
            'sous_total': float(panier.sous_total),
            'total_commande': float(commande.total_cmd),
            'compteur': commande.compteur,
            'prix_unitaire_effectif': float(prix_unitaire_effectif)  # Prix effectif actuel selon compteur/promo/liquidation
        }

        # Ajouter les infos de remise si elle existe
        if remise_info:
            response_data['remise'] = remise_info

        return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ Erreur lors de la modification de quantité: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


__all__ = [
    'handle_add_article',
    'handle_delete_article',
    'handle_update_quantity',
]
