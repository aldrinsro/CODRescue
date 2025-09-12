"""
Vues pour la gestion des articles retournés lors des livraisons partielles
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


@login_required
def liste_articles_retournes(request):
    """Liste des articles retournés en attente de traitement"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')

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

    # Statistiques
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
        'page_title': 'Gestion des Articles Retournés',
        'page_subtitle': 'Articles retournés lors des livraisons partielles'
    }

    return render(request, 'operatLogistic/articles_retournes/liste.html', context)


@login_required
def detail_article_retourne(request, retour_id):
    """Détail d'un article retourné"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')

    article_retourne = get_object_or_404(
        ArticleRetourne.objects.select_related(
            'commande', 'article', 'variante', 'operateur_retour', 'operateur_traitement'
        ),
        id=retour_id
    )

    context = {
        'article_retourne': article_retourne,
        'page_title': f'Détail Retour #{article_retourne.id}',
        'page_subtitle': f'Article: {article_retourne.article.nom}'
    }

    return render(request, 'operatLogistic/articles_retournes/detail.html', context)


@login_required
@require_POST
def traiter_article_retourne(request, retour_id):
    """Traiter un article retourné (réintégrer, marquer défectueux, etc.)"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})

    try:
        article_retourne = get_object_or_404(ArticleRetourne, id=retour_id)
        
        if article_retourne.statut_retour != 'en_attente':
            return JsonResponse({
                'success': False, 
                'error': 'Cet article a déjà été traité.'
            })

        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '').strip()

        if action == 'reintegrer_stock':
            if article_retourne.peut_etre_reintegre():
                if article_retourne.reintegrer_stock(operateur, commentaire):
                    return JsonResponse({
                        'success': True,
                        'message': f'Article réintégré en stock avec succès. +{article_retourne.quantite_retournee} en stock.'
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
                'message': 'Article marqué comme défectueux.'
            })

        elif action == 'marquer_traite':
            article_retourne.statut_retour = 'traite'
            article_retourne.date_traitement = timezone.now()
            article_retourne.operateur_traitement = operateur
            article_retourne.commentaire_traitement = commentaire or 'Traité manuellement'
            article_retourne.save()

            return JsonResponse({
                'success': True,
                'message': 'Article marqué comme traité.'
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


@login_required
@require_POST
def reintegrer_automatique(request):
    """Réintégrer automatiquement tous les articles retournés éligibles"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})

    try:
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
                    "Réintégration automatique en lot"
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
            'erreurs': erreurs
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la réintégration automatique: {str(e)}'
        })


@login_required
def statistiques_retours(request):
    """Page de statistiques des retours"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')

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
        'page_title': 'Statistiques des Retours',
        'page_subtitle': 'Analyse des articles retournés'
    }

    return render(request, 'operatLogistic/articles_retournes/statistiques.html', context)