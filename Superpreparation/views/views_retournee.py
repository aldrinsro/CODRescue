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
from ..decorators import superviseur_preparation_required


@superviseur_preparation_required
def liste_articles_retournes_service(request):
    """Liste des articles retournés en attente de traitement - Version Superpreparation"""
    # Récupérer les articles retournés avec préfetch des relations optimisées
    articles_retournes = ArticleRetourne.objects.select_related(
        'commande', 'commande__client', 'commande__ville', 'commande__ville__region',
        'article', 'variante', 'variante__couleur', 'variante__pointure',
        'operateur_retour', 'operateur_traitement'
    ).prefetch_related(
        'commande__etats__enum_etat',
        'commande__etats__operateur'
    ).order_by('-date_retour')


    # === RECHERCHE INTELLIGENTE COMPLÈTE ===
    # Recherche simple (barre de recherche principale)
    search_query = request.GET.get('search', '').strip()

    # Filtres avancés individuels
    filter_article_nom = request.GET.get('article_nom', '').strip()
    filter_article_modele = request.GET.get('article_modele', '').strip()
    filter_couleur = request.GET.get('couleur', '').strip()
    filter_pointure = request.GET.get('pointure', '').strip()
    filter_commande_id = request.GET.get('commande_id', '').strip()
    filter_num_cmd = request.GET.get('num_cmd', '').strip()
    filter_client = request.GET.get('client', '').strip()
    filter_phone = request.GET.get('phone', '').strip()
    filter_date_retour_debut = request.GET.get('date_retour_debut', '').strip()
    filter_date_retour_fin = request.GET.get('date_retour_fin', '').strip()
    filter_raison_retour = request.GET.get('raison_retour', '').strip()
    filter_prix_min = request.GET.get('prix_min', '').strip()
    filter_prix_max = request.GET.get('prix_max', '').strip()
    filter_quantite_min = request.GET.get('quantite_min', '').strip()
    filter_quantite_max = request.GET.get('quantite_max', '').strip()
    filter_operateur = request.GET.get('operateur', '').strip()
    filter_statut = request.GET.get('statut', '').strip()

    # Application de la recherche simple (recherche dans tous les champs)
    if search_query:
        articles_retournes = articles_retournes.filter(
            Q(id__icontains=search_query) |
            Q(commande__id_yz__icontains=search_query) |
            Q(commande__num_cmd__icontains=search_query) |
            Q(article__nom__icontains=search_query) |
            Q(article__reference__icontains=search_query) |
            Q(article__modele__icontains=search_query) |
            Q(commande__client__nom__icontains=search_query) |
            Q(commande__client__prenom__icontains=search_query) |
            Q(commande__client__numero_tel__icontains=search_query) |
            Q(commande__client__email__icontains=search_query) |
            Q(variante__couleur__nom__icontains=search_query) |
            Q(variante__pointure__pointure__icontains=search_query) |
            Q(raison_retour__icontains=search_query) |
            Q(operateur_traitement__nom__icontains=search_query) |
            Q(operateur_traitement__prenom__icontains=search_query)
        )

    # Application des filtres avancés
    if filter_article_nom:
        articles_retournes = articles_retournes.filter(article__nom__icontains=filter_article_nom)

    if filter_article_modele:
        articles_retournes = articles_retournes.filter(article__modele__icontains=filter_article_modele)

    if filter_couleur:
        articles_retournes = articles_retournes.filter(variante__couleur__nom__icontains=filter_couleur)

    if filter_pointure:
        articles_retournes = articles_retournes.filter(variante__pointure__pointure__icontains=filter_pointure)

    if filter_commande_id:
        articles_retournes = articles_retournes.filter(commande__id_yz__icontains=filter_commande_id)

    if filter_num_cmd:
        articles_retournes = articles_retournes.filter(commande__num_cmd__icontains=filter_num_cmd)

    if filter_client:
        articles_retournes = articles_retournes.filter(
            Q(commande__client__nom__icontains=filter_client) |
            Q(commande__client__prenom__icontains=filter_client)
        )

    if filter_phone:
        articles_retournes = articles_retournes.filter(commande__client__numero_tel__icontains=filter_phone)

    if filter_date_retour_debut:
        articles_retournes = articles_retournes.filter(date_retour__date__gte=filter_date_retour_debut)

    if filter_date_retour_fin:
        articles_retournes = articles_retournes.filter(date_retour__date__lte=filter_date_retour_fin)

    if filter_raison_retour:
        articles_retournes = articles_retournes.filter(raison_retour__icontains=filter_raison_retour)

    if filter_prix_min:
        try:
            articles_retournes = articles_retournes.filter(prix_unitaire_origine__gte=float(filter_prix_min))
        except ValueError:
            pass

    if filter_prix_max:
        try:
            articles_retournes = articles_retournes.filter(prix_unitaire_origine__lte=float(filter_prix_max))
        except ValueError:
            pass

    if filter_quantite_min:
        try:
            articles_retournes = articles_retournes.filter(quantite_retournee__gte=int(filter_quantite_min))
        except ValueError:
            pass

    if filter_quantite_max:
        try:
            articles_retournes = articles_retournes.filter(quantite_retournee__lte=int(filter_quantite_max))
        except ValueError:
            pass

    if filter_operateur:
        articles_retournes = articles_retournes.filter(
            Q(operateur_traitement__nom__icontains=filter_operateur) |
            Q(operateur_traitement__prenom__icontains=filter_operateur)
        )

    if filter_statut:
        # Mapping des statuts affichés vers les valeurs en base
        statut_mapping = {
            'en_attente': 'en_attente',
            'en attente': 'en_attente',
            'reintegre': 'reintegre_stock',
            'reintegre_stock': 'reintegre_stock',
            'réintégré': 'reintegre_stock',
            'defectueux': 'defectueux',
            'défectueux': 'defectueux',
            'traite': 'traite',
            'traité': 'traite'
        }
        statut_recherche = statut_mapping.get(filter_statut.lower(), filter_statut)
        articles_retournes = articles_retournes.filter(statut_retour=statut_recherche)

    # Statistiques pour le tableau de bord
    stats = {
        'total_en_attente': ArticleRetourne.objects.filter(statut_retour='en_attente').count(),
        'total_reintegres': ArticleRetourne.objects.filter(statut_retour='reintegre_stock').count(),
        'total_traites': ArticleRetourne.objects.exclude(statut_retour='en_attente').count(),
        'total_articles': ArticleRetourne.objects.count(),
        'commandes_urgentes': ArticleRetourne.objects.filter(statut_retour='defectueux').count(),  # Nombre d'articles défectueux
        'valeur_totale': articles_retournes.aggregate(
            total=Sum('quantite_retournee') * Sum('prix_unitaire_origine')
        )['total'] or 0
    }

    # Statistiques spécifiques pour les articles retournés
    articles_retournes_stats = {
        'total_en_attente': stats['total_en_attente'],
        'total_reintegres': stats['total_reintegres'],
        'total_traites': stats['total_traites']
    }

    # Récupérer les commandes qui ont des articles retournés (pour simuler les commandes livrées partiellement)
    commandes_avec_retours = []
    commandes_distinctes = articles_retournes.values('commande').distinct()

    for commande_data in commandes_distinctes:
        try:
            commande = Commande.objects.select_related(
                'client', 'ville', 'ville__region'
            ).prefetch_related(
                'paniers',
                'etats__enum_etat',
                'etats__operateur'
            ).get(id=commande_data['commande'])
            commandes_avec_retours.append(commande)
        except Commande.DoesNotExist:
            continue

    # Pagination pour les articles retournés
    paginator = Paginator(articles_retournes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'articles_retournes': articles_retournes,  # Tous les articles retournés
        'commandes_livrees_partiellement': commandes_avec_retours,  # Commandes avec retours
        'page_obj': page_obj,
        'search_query': search_query,
        
        'stats': stats,
        'articles_retournes_stats': articles_retournes_stats,
        'page_title': 'Service - Gestion des Articles Retournés',
        'page_subtitle': 'Articles retournés lors des livraisons partielles',
        'active_tab': 'service',
        'breadcrumbs': [
            {'name': 'Accueil', 'url': 'Superpreparation:home'},
            {'name': 'Service', 'url': None},
            {'name': 'Articles Retournés', 'url': None}
        ]
    }

    return render(request, 'Superpreparation/articles_retournes/liste.html', context)


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

        # Nouvelle fonctionnalité: récupérer la quantité à traiter (optionnel)
        quantite_str = request.POST.get('quantite', '').strip()
        quantite = None

        if quantite_str:
            try:
                quantite = int(quantite_str)
                if quantite <= 0 or quantite > article_retourne.quantite_retournee:
                    return JsonResponse({
                        'success': False,
                        'error': f'Quantité invalide. Doit être entre 1 et {article_retourne.quantite_retournee}.'
                    })
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Quantité invalide (nombre entier requis).'
                })

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
                success, article_cree = article_retourne.reintegrer_stock(operateur, commentaire, quantite)

                if success:
                    qte_traitee = quantite if quantite else article_retourne.quantite_retournee + (quantite or 0)

                    # Message différent selon traitement total ou partiel
                    if article_cree:
                        message = f'Réintégration partielle réussie: +{qte_traitee} en stock. {article_retourne.quantite_retournee} restant(s) en attente.'
                    else:
                        message = f'Article réintégré en stock avec succès. +{qte_traitee} en stock.'

                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'partial': article_cree is not None,
                        'quantite_traitee': qte_traitee,
                        'quantite_restante': article_retourne.quantite_retournee if article_cree else 0,
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
            success, article_cree = article_retourne.marquer_defectueux(operateur, commentaire, quantite)

            if success:
                qte_traitee = quantite if quantite else article_retourne.quantite_retournee + (quantite or 0)

                # Message différent selon traitement total ou partiel
                if article_cree:
                    message = f'Marquage partiel réussi: {qte_traitee} marqué(s) comme défectueux. {article_retourne.quantite_retournee} restant(s) en attente.'
                else:
                    message = f'Article marqué comme défectueux: {qte_traitee} unité(s).'

                return JsonResponse({
                    'success': True,
                    'message': message,
                    'partial': article_cree is not None,
                    'quantite_traitee': qte_traitee,
                    'quantite_restante': article_retourne.quantite_retournee if article_cree else 0,
                    'redirect': True,
                    'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur lors du marquage comme défectueux.'
                })

        elif action == 'marquer_traite':
            success, article_cree = article_retourne.traiter('traite', operateur, commentaire, quantite)

            if success:
                qte_traitee = quantite if quantite else article_retourne.quantite_retournee + (quantite or 0)

                # Message différent selon traitement total ou partiel
                if article_cree:
                    message = f'Traitement partiel réussi: {qte_traitee} traité(s). {article_retourne.quantite_retournee} restant(s) en attente.'
                else:
                    message = f'Article marqué comme traité: {qte_traitee} unité(s).'

                return JsonResponse({
                    'success': True,
                    'message': message,
                    'partial': article_cree is not None,
                    'quantite_traitee': qte_traitee,
                    'quantite_restante': article_retourne.quantite_retournee if article_cree else 0,
                    'redirect': True,
                    'redirect_url': request.META.get('HTTP_REFERER', '/superpreparation/service/articles-retournes/')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur lors du traitement.'
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