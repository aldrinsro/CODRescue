"""
================================================================================
MODULE GLOBAL: API pour la Gestion des Articles
================================================================================

Ce module fournit des APIs réutilisables pour la gestion des articles
dans les commandes via AJAX.

Fonctionnalités:
- Liste des articles disponibles pour les dropdowns
- Récupération des variantes d'un article
- Rafraîchissement de la section articles (HTML + données)

Utilisation:
    from common.api.article_api import (
        api_articles_disponibles,
        get_article_variants,
        rafraichir_articles_section
    )

    # Dans votre urls.py
    path('api/articles-disponibles/', api_articles_disponibles, name='api_articles_disponibles'),

@version 1.0
@author YZ-RESCUE
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.db.models import Prefetch


def api_articles_disponibles(request):
    """
    API pour récupérer la liste complète des articles disponibles.

    Cette API retourne tous les articles actifs avec leurs informations complètes
    (prix, stock, images, références) pour alimenter les dropdowns et sélecteurs.

    Args:
        request: L'objet HttpRequest

    Returns:
        JsonResponse avec la liste des articles au format:
        {
            'articles': [
                {
                    'id': int,
                    'nom': str,
                    'reference': str,
                    'prix_normal': float,
                    'prix_upsell2': float,
                    'prix_upsell3': float,
                    'prix_upsell4': float,
                    'prix_gros': float,
                    'stock_disponible': int,
                    'image_url': str,
                    'phase': str,
                    'isUpsell': bool,
                    'has_variants': bool
                },
                ...
            ]
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch('/api/articles-disponibles/')
        >>>     .then(response => response.json())
        >>>     .then(data => {
        >>>         data.articles.forEach(article => {
        >>>             // Populate dropdown
        >>>         });
        >>>     });
    """
    from article.models import Article

    try:
        # ========== 1. RÉCUPÉRATION DES ARTICLES ACTIFS ==========
        articles = Article.objects.filter(
            actif=True
        ).select_related(
            'categorie'
        ).order_by('nom')

        print(f"📦 API Articles: {articles.count()} articles trouvés")

        # ========== 2. CONSTRUCTION DE LA LISTE ==========
        articles_data = []
        for article in articles:
            # Récupérer l'image si disponible
            image_url = None
            if article.image:
                image_url = article.image.url
            elif article.image_url:
                image_url = article.image_url

            # Vérifier si l'article a des variantes
            has_variants = hasattr(article, 'variantes') and article.variantes.filter(actif=True).exists()

            articles_data.append({
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference or '',
                'prix_unitaire': float(article.prix_unitaire) if article.prix_unitaire else 0.0,
                'prix_actuel': float(article.prix_actuel) if article.prix_actuel else float(article.prix_unitaire) if article.prix_unitaire else 0.0,
                'prix_upsell_2': float(article.prix_upsell_2) if hasattr(article, 'prix_upsell_2') and article.prix_upsell_2 else 0.0,
                'prix_upsell_3': float(article.prix_upsell_3) if hasattr(article, 'prix_upsell_3') and article.prix_upsell_3 else 0.0,
                'prix_upsell_4': float(article.prix_upsell_4) if hasattr(article, 'prix_upsell_4') and article.prix_upsell_4 else 0.0,
                'prix_gros': float(article.prix_gros) if article.prix_gros else 0.0,
                'Prix_liquidation': float(article.Prix_liquidation) if hasattr(article, 'Prix_liquidation') and article.Prix_liquidation else 0.0,
                'qte_disponible': article.get_total_qte_disponible() if hasattr(article, 'get_total_qte_disponible') else 0,
                'stock_total': article.get_total_qte_disponible() if hasattr(article, 'get_total_qte_disponible') else 0,
                'image_url': image_url,
                'phase': article.phase if hasattr(article, 'phase') else 'NORMAL',
                'isUpsell': article.isUpsell if hasattr(article, 'isUpsell') else False,
                'has_promo_active': article.has_promo_active if hasattr(article, 'has_promo_active') else False,
                'has_variants': has_variants,
                'couleur': article.couleur if hasattr(article, 'couleur') else '',
                'pointure': article.pointure if hasattr(article, 'pointure') else '',
                'categorie': article.categorie.nom if article.categorie else None
            })

        print(f"✅ API Articles: {len(articles_data)} articles formatés")

        # ========== 3. RÉPONSE JSON ==========
        return JsonResponse({
            'articles': articles_data
        })

    except Exception as e:
        print(f"❌ Erreur API articles disponibles: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


def get_article_variants(request, article_id):
    """
    API pour récupérer les variantes d'un article spécifique.

    Cette API retourne toutes les variantes actives d'un article avec leurs
    informations complètes (couleur, taille, stock, prix, référence).

    Args:
        request: L'objet HttpRequest
        article_id: L'ID de l'article dont on veut les variantes

    Returns:
        JsonResponse avec les variantes au format:
        {
            'success': True,
            'article_nom': str,
            'variants': [
                {
                    'id': int,
                    'couleur': str,
                    'taille': str,
                    'reference': str,
                    'stock': int,
                    'prix': float,
                    'display': str  # Ex: "Rouge - L (Ref: ABC123)"
                },
                ...
            ]
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch(`/api/article/${articleId}/variants/`)
        >>>     .then(response => response.json())
        >>>     .then(data => {
        >>>         data.variants.forEach(variant => {
        >>>             // Populate variant selector
        >>>         });
        >>>     });
    """
    from article.models import Article

    try:
        # ========== 1. RÉCUPÉRATION DE L'ARTICLE ==========
        article = get_object_or_404(Article, id=article_id)

        print(f"🎨 API Variantes: Article '{article.nom}' (ID: {article_id})")

        # ========== 2. RÉCUPÉRATION DES VARIANTES ACTIVES ==========
        from article.models import VarianteArticle

        variants = VarianteArticle.objects.filter(
            article=article,
            actif=True
        ).select_related('couleur', 'pointure')

        print(f"📊 {variants.count()} variante(s) trouvée(s)")

        # ========== 3. CONSTRUCTION DE LA LISTE ==========
        variants_data = []
        for variant in variants:
            # Construire l'affichage complet de la variante
            display_parts = []

            if variant.couleur:
                display_parts.append(variant.couleur.nom)
            if variant.pointure:
                display_parts.append(variant.pointure.pointure)
            if variant.reference_variante:
                display_parts.append(f"Ref: {variant.reference_variante}")

            display = " - ".join(display_parts) if display_parts else "Variante sans détails"

            # Récupérer le stock
            stock = variant.qte_disponible if hasattr(variant, 'qte_disponible') else 0

            # Récupérer le prix (utilise le prix de l'article parent par défaut)
            prix = float(variant.prix) if hasattr(variant, 'prix') and variant.prix else float(article.prix_actuel if article.prix_actuel else article.prix_unitaire)

            variants_data.append({
                'id': variant.id,
                'couleur': variant.couleur.nom if variant.couleur else None,
                'pointure': variant.pointure.pointure if variant.pointure else None,
                'reference': variant.reference_variante or '',
                'stock': stock,
                'prix': prix,
                'display': display
            })

        print(f"✅ API Variantes: {len(variants_data)} variantes formatées")

        # ========== 4. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'article_nom': article.nom,
            'article_id': article.id,
            'variants': variants_data
        })

    except Article.DoesNotExist:
        print(f"❌ Article {article_id} introuvable")
        return JsonResponse({
            'success': False,
            'error': 'Article introuvable'
        }, status=404)

    except Exception as e:
        print(f"❌ Erreur API variantes: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


def rafraichir_articles_section(request, commande_id, template_path=None):
    """
    API pour rafraîchir la section articles d'une commande.

    Cette API effectue les corrections nécessaires sur les paniers (liquidation, promotion),
    recalcule les totaux upsell, puis retourne le HTML mis à jour de la section articles
    ainsi que les données actualisées de la commande.

    Args:
        request: L'objet HttpRequest
        commande_id: L'ID de la commande à rafraîchir
        template_path: Chemin optionnel vers le template de rendu
                      (défaut: 'common/commande/_articles_section.html')

    Returns:
        JsonResponse avec:
        {
            'success': True,
            'html': str,  # HTML de la section mise à jour
            'total_commande': float,
            'sous_total_articles': float,
            'articles_count': int,
            'compteur': int,
            'frais_livraison': float
        }

    Example:
        >>> # Dans votre JavaScript
        >>> fetch(`/api/commande/${commandeId}/rafraichir-articles/`)
        >>>     .then(response => response.json())
        >>>     .then(data => {
        >>>         $('#articles-section').html(data.html);
        >>>         $('#total-commande').text(data.total_commande);
        >>>     });
    """
    from commande.models import Commande

    # Définir le template par défaut si non spécifié
    if template_path is None:
        template_path = 'common/commande/_articles_section.html'

    try:
        # ========== 1. RÉCUPÉRATION DE LA COMMANDE AVEC OPTIMISATION ==========
        commande = get_object_or_404(
            Commande.objects.prefetch_related(
                Prefetch(
                    'paniers',
                    queryset=None  # Vous pouvez ajouter un queryset optimisé ici si nécessaire
                ),
                'paniers__article',
                'paniers__variante',
                'paniers__variante__couleur',
                'paniers__variante__pointure'
            ).select_related('client', 'ville', 'ville__region'),
            id=commande_id
        )

        print(f"🔄 Rafraîchissement articles pour commande {commande_id}")

        # ========== 2. CORRECTIONS DES PANIERS ==========
        if hasattr(commande, 'corriger_paniers_liquidation_et_promotion'):
            commande.corriger_paniers_liquidation_et_promotion()
            print(f"✅ Corrections liquidation/promotion appliquées")

        # ========== 3. RECALCUL DES TOTAUX UPSELL ==========
        if hasattr(commande, 'recalculer_totaux_upsell'):
            commande.recalculer_totaux_upsell()
            print(f"✅ Totaux upsell recalculés")

        # ========== 4. PRÉPARATION DU CONTEXTE ==========
        context = {
            'commande': commande,
            'paniers': commande.paniers.all()
        }

        # ========== 5. RENDU DU TEMPLATE ==========
        html = render_to_string(template_path, context, request=request)

        print(f"✅ HTML généré ({len(html)} caractères)")

        # ========== 6. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
            'sous_total_articles': float(commande.sous_total_articles) if hasattr(commande, 'sous_total_articles') else float(commande.total_cmd),
            'articles_count': commande.paniers.count(),
            'compteur': commande.compteur if hasattr(commande, 'compteur') else 0,
            'frais_livraison': float(commande.montant_frais_livraison) if hasattr(commande, 'montant_frais_livraison') else 0.0
        })

    except Commande.DoesNotExist:
        print(f"❌ Commande {commande_id} introuvable")
        return JsonResponse({
            'success': False,
            'error': 'Commande introuvable'
        }, status=404)

    except Exception as e:
        print(f"❌ Erreur rafraîchissement articles: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


__all__ = [
    'api_articles_disponibles',
    'get_article_variants',
    'rafraichir_articles_section',
]
