"""
Vues pour la gestion des services (articles retournés) dans Superpreparation
Adaptation des vues de operatLogistic/articles_retournes_views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone

from parametre.models import Operateur
from commande.models import Commande, ArticleRetourne
from .decorators import superviseur_preparation_required


@superviseur_preparation_required
def liste_articles_retournes_service(request):
    """Liste des articles retournés en attente de traitement - Version Superpreparation"""
   

    # Récupérer les articles retournés avec préfetch des relations
    articles_retournes = ArticleRetourne.objects.select_related(
        'commande', 'article', 'variante', 'operateur_retour'
    ).prefetch_related(
        'variante__couleur', 'variante__pointure'
    ).order_by('-date_retour')

    # Filtre par statut
    statut_filter = request.GET.get('statut', 'en_attente')
    if statut_filter and statut_filter != 'tous':
        articles_retournes = articles_retournes.filter(statut_retour=statut_filter)

    # Filtre par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        articles_retournes = articles_retournes.filter(
            Q(commande__id_yz__icontains=search_query) |
            Q(article__nom__icontains=search_query) |
            Q(commande__client__nom__icontains=search_query) |
            Q(commande__client__prenom__icontains=search_query)
        )

    # Statistiques pour le tableau de bord
    stats = {
        'total_en_attente': ArticleRetourne.objects.filter(statut_retour='en_attente').count(),
        'total_reintegres': ArticleRetourne.objects.filter(statut_retour='reintegre_stock').count(),
        'total_traites': ArticleRetourne.objects.exclude(statut_retour='en_attente').count(),
        'valeur_total_en_attente': ArticleRetourne.objects.filter(
            statut_retour='en_attente'
        ).aggregate(
            total=Sum('quantite_retournee') * Sum('prix_unitaire_origine')
        )['total'] or 0
    }

    # Pagination
    paginator = Paginator(articles_retournes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'stats': stats,
        'page_title': 'Service - Gestion des Articles Retournés',
        'page_subtitle': 'Articles retournés lors des livraisons partielles',
        'active_tab': 'service',
        'breadcrumbs': [
            {'name': 'Accueil', 'url': 'Superpreparation:home'},
            {'name': 'Service', 'url': None},
            {'name': 'Articles Retournés', 'url': None}
        ]
    }

    return render(request, 'Superpreparation/service/articles_retournes/liste.html', context)


@superviseur_preparation_required
def detail_article_retourne_service(request, retour_id):
    """Détail d'un article retourné - Version Superpreparation"""
  

    article_retourne = get_object_or_404(
        ArticleRetourne.objects.select_related(
            'commande', 'article', 'variante', 'operateur_retour', 'operateur_traitement'
        ),
        id=retour_id
    )

    context = {
        'article_retourne': article_retourne,
        'page_title': f'Service - Détail Retour #{article_retourne.id}',
        'page_subtitle': f'Article: {article_retourne.article.nom}',
        'active_tab': 'service',
        'breadcrumbs': [
            {'name': 'Accueil', 'url': 'Superpreparation:home'},
            {'name': 'Service', 'url': None},
            {'name': 'Articles Retournés', 'url': 'Superpreparation:service_liste_articles_retournes'},
            {'name': f'Retour #{article_retourne.id}', 'url': None}
        ]
    }

    return render(request, 'Superpreparation/service/articles_retournes/detail.html', context)


@require_POST
def traiter_article_retourne_service(request, retour_id):
    """Traiter un article retourné (réintégrer, marquer défectueux, etc.) - Version Superpreparation"""
    

    try:
        article_retourne = get_object_or_404(ArticleRetourne, id=retour_id)

        if article_retourne.statut_retour != 'en_attente':
            return JsonResponse({
                'success': False,
                'error': 'Cet article a déjà été traité.'
            })

        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '').strip()

        # Récupérer l'opérateur de manière sécurisée
        try:
            operateur = request.user.profil_operateur
        except AttributeError:
            # Fallback si pas de profil opérateur
            try:
                operateur = Operateur.objects.get(user=request.user, actif=True)
            except Operateur.DoesNotExist:
                operateur = None

        if action == 'reintegrer_stock':
            if article_retourne.peut_etre_reintegre():
                if article_retourne.reintegrer_stock(operateur, commentaire):
                    return JsonResponse({
                        'success': True,
                        'message': f'Article réintégré en stock avec succès. +{article_retourne.quantite_retournee} en stock.',
                        'redirect': True,
                        'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Erreur lors de la réintégration en stock.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Cet article ne peut pas être réintégré (variante inactive ou manquante).'
                })

        elif action == 'marquer_defectueux':
            article_retourne.statut_retour = 'defectueux'
            article_retourne.date_traitement = timezone.now()
            article_retourne.operateur_traitement = operateur
            article_retourne.commentaire_traitement = commentaire or 'Marqué comme défectueux'
            article_retourne.save()

            return JsonResponse({
                'success': True,
                'message': 'Article marqué comme défectueux.',
                'redirect': True,
                'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
            })

        elif action == 'marquer_traite':
            article_retourne.statut_retour = 'traite'
            article_retourne.date_traitement = timezone.now()
            article_retourne.operateur_traitement = operateur
            article_retourne.commentaire_traitement = commentaire or 'Traité manuellement'
            article_retourne.save()

            return JsonResponse({
                'success': True,
                'message': 'Article marqué comme traité.',
                'redirect': True,
                'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
            })

        else:
            return JsonResponse({
                'success': False,
                'error': 'Action non reconnue.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du traitement: {str(e)}'
        })


@superviseur_preparation_required
@require_POST
def reintegrer_automatique_service(request):
    """Réintégrer automatiquement tous les articles retournés éligibles - Version Superpreparation"""
    

    try:
        # Récupérer l'opérateur de manière sécurisée
        try:
            operateur = request.user.profil_operateur
        except AttributeError:
            # Fallback si pas de profil opérateur
            try:
                operateur = Operateur.objects.get(user=request.user, actif=True)
            except Operateur.DoesNotExist:
                operateur = None

        # Récupérer tous les articles retournés éligibles à la réintégration
        articles_eligibles = ArticleRetourne.objects.filter(
            statut_retour='en_attente',
            variante__isnull=False,
            variante__actif=True
        )

        total_reintegres = 0
        erreurs = []

        for article_retourne in articles_eligibles:
            try:
                if article_retourne.reintegrer_stock(
                    operateur,
                    "Réintégration automatique en lot (Service Superpreparation)"
                ):
                    total_reintegres += 1
            except Exception as e:
                erreurs.append(f"Article {article_retourne.id}: {str(e)}")

        if total_reintegres > 0:
            messages.success(
                request,
                f"{total_reintegres} article(s) réintégré(s) automatiquement en stock."
            )

        if erreurs:
            messages.warning(
                request,
                f"Quelques erreurs sont survenues: {', '.join(erreurs[:3])}"
            )

        return JsonResponse({
            'success': True,
            'message': f'{total_reintegres} article(s) réintégré(s) automatiquement.',
            'total_reintegres': total_reintegres,
            'erreurs': erreurs,
            'redirect': True,
            'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la réintégration automatique: {str(e)}'
        })


@superviseur_preparation_required
def statistiques_retours_service(request):
    """Page de statistiques des retours - Version Superpreparation"""
  

    # Statistiques générales
    from django.db.models import Sum, Avg
    from datetime import datetime, timedelta

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    stats_generales = {
        'total_retours': ArticleRetourne.objects.count(),
        'retours_semaine': ArticleRetourne.objects.filter(date_retour__date__gte=week_ago).count(),
        'retours_mois': ArticleRetourne.objects.filter(date_retour__date__gte=month_ago).count(),
        'valeur_totale_retours': ArticleRetourne.objects.aggregate(
            total=Sum('quantite_retournee') * Sum('prix_unitaire_origine')
        )['total'] or 0,
        'taux_reintegration': 0  # À calculer
    }

    # Calculer le taux de réintégration
    total_traites = ArticleRetourne.objects.exclude(statut_retour='en_attente').count()
    total_reintegres = ArticleRetourne.objects.filter(statut_retour='reintegre_stock').count()
    if total_traites > 0:
        stats_generales['taux_reintegration'] = round((total_reintegres / total_traites) * 100, 2)

    # Top articles retournés
    top_articles = ArticleRetourne.objects.values(
        'article__nom'
    ).annotate(
        total_retours=Count('id'),
        total_quantite=Sum('quantite_retournee')
    ).order_by('-total_retours')[:10]

    context = {
        'stats_generales': stats_generales,
        'top_articles': top_articles,
        'page_title': 'Service - Statistiques des Retours',
        'page_subtitle': 'Analyse des articles retournés',
        'active_tab': 'service',
        'breadcrumbs': [
            {'name': 'Accueil', 'url': 'Superpreparation:home'},
            {'name': 'Service', 'url': None},
            {'name': 'Statistiques Retours', 'url': None}
        ]
    }

    return render(request, 'Superpreparation/service/articles_retournes/statistiques.html', context)


@superviseur_preparation_required
def api_articles_retournes_modal(request):
    """API pour récupérer les articles retournés à afficher dans la modale"""
    try:
        # Récupérer les articles retournés en attente uniquement
        articles_retournes = ArticleRetourne.objects.filter(
            statut_retour='en_attente'
        ).select_related(
            'commande', 'commande__client', 'article', 'variante', 'operateur_retour'
        ).prefetch_related(
            'variante__couleur', 'variante__pointure'
        ).order_by('-date_retour')

        # Limiter à 50 pour éviter une surcharge
        articles_retournes = articles_retournes[:50]

        articles_data = []
        for article in articles_retournes:
            try:
                # Construire les données avec vérifications et valeurs par défaut
                has_variante = article.variante is not None

                article_data = {
                    'id': article.id,
                    'article_nom': article.article.nom if article.article else 'N/A',
                    'article_reference': getattr(article.article, 'reference', '') if article.article else '',
                    'variante_info': {
                        'couleur': article.variante.couleur.nom if has_variante and hasattr(article.variante, 'couleur') and article.variante.couleur else '',
                        'pointure': article.variante.pointure.pointure if has_variante and hasattr(article.variante, 'pointure') and article.variante.pointure else '',
                        'reference_variante': getattr(article.variante, 'reference_variante', '') if has_variante else '',
                        'stock_disponible': getattr(article.variante, 'qte_disponible', 0) if has_variante else 0,
                        'has_variante': has_variante,
                    },
                    'commande_info': {
                        'id_yz': getattr(article.commande, 'id_yz', '') if article.commande else '',
                        'num_cmd': getattr(article.commande, 'num_cmd', '') if article.commande else '',
                        'client_nom': f"{article.commande.client.prenom} {article.commande.client.nom}" if article.commande and article.commande.client else 'N/A',
                    },
                    'quantite_retournee': article.quantite_retournee or 0,
                    'prix_unitaire': float(article.prix_unitaire_origine) if article.prix_unitaire_origine else 0.0,
                    'date_retour': article.date_retour.strftime('%d/%m/%Y %H:%M') if article.date_retour else '',
                    'raison_retour': article.raison_retour or 'Non spécifiée',
                    'operateur_retour': f"{article.operateur_retour.prenom} {article.operateur_retour.nom}" if article.operateur_retour else 'N/A',
                    'peut_etre_reintegre': article.peut_etre_reintegre(),
                    'statut': article.get_statut_retour_display(),
                }
                articles_data.append(article_data)
            except Exception as inner_e:
                # Log l'erreur mais continuer avec les autres articles
                print(f"Erreur lors du traitement de l'article {article.id}: {inner_e}")
                continue

        return JsonResponse({
            'success': True,
            'articles': articles_data,
            'total': len(articles_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du chargement des articles: {str(e)}'
        })