from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Min, Max
from .models import Article, Promotion, VarianteArticle, Categorie, Genre, Couleur, Pointure
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .forms import PromotionForm
from decimal import Decimal
import json

@login_required
def liste_articles(request):
    """Liste des articles avec recherche, filtres et pagination"""
    articles = Article.objects.all().filter(actif=True).order_by('nom')
    
    # Formulaire de promotion pour la modal
    form_promotion = PromotionForm()
    
    # Récupérer les paramètres de filtrage
    filtre_phase = request.GET.get('filtre_phase', 'tous')
    filtre_promotion = request.GET.get('filtre_promotion', '')
    filtre_stock = request.GET.get('filtre_stock', '')
    search = request.GET.get('search', '')
    
    # Filtrage par phase
    if filtre_phase and filtre_phase != 'tous':
        articles = articles.filter(phase=filtre_phase)
    
    # Filtrage par promotion
    now = timezone.now()
    if filtre_promotion == 'avec_promo':
        articles = articles.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct()
    elif filtre_promotion == 'sans_promo':
        articles = articles.exclude(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct()
    
    # Filtrage par stock
    if filtre_stock == 'disponible':
        articles = articles.filter(variantes__qte_disponible__gt=0, variantes__actif=True).distinct()
    elif filtre_stock == 'rupture':
        articles = articles.exclude(variantes__qte_disponible__gt=0, variantes__actif=True).distinct()
    elif filtre_stock == 'stock_faible':
        articles = articles.filter(
            variantes__qte_disponible__gt=0, 
            variantes__qte_disponible__lt=5, 
            variantes__actif=True
        ).distinct()
    
    # Recherche unique sur plusieurs champs
    if search:
        # Essayer de convertir la recherche en nombre pour le prix
        try:
            # Si c'est un nombre, on cherche le prix exact ou dans une marge de ±10 DH
            search_price = float(search.replace(',', '.'))
            price_query = Q(prix_unitaire__gte=search_price-10) & Q(prix_unitaire__lte=search_price+10)
        except ValueError:
            price_query = Q()  # Query vide si ce n'est pas un prix

        # Vérifier si c'est une fourchette de prix (ex: 100-200)
        if '-' in search and all(part.strip().replace(',', '.').replace('.', '').isdigit() for part in search.split('-')):
            try:
                min_price, max_price = map(lambda x: float(x.strip().replace(',', '.')), search.split('-'))
                price_query = Q(prix_unitaire__gte=min_price) & Q(prix_unitaire__lte=max_price)
            except ValueError:
                pass

        articles = articles.filter(
            Q(reference__icontains=search) |    # Recherche par référence
            Q(nom__icontains=search) |          # Recherche par nom
            Q(variantes__couleur__nom__icontains=search) |      # Recherche par couleur
            Q(variantes__pointure__pointure__icontains=search) | # Recherche par pointure
            Q(categorie__nom__icontains=search) |    # Recherche par catégorie
            price_query                         # Recherche par prix
        ).distinct()
    
    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 12)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des articles non paginés pour les statistiques
    articles_non_pagines = articles
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                articles = list(articles)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(articles, len(articles))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 12
            paginator = Paginator(articles, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher tous les articles
            paginator = Paginator(articles, articles.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 12
            except (ValueError, TypeError):
                items_per_page = 12
            
            paginator = Paginator(articles, items_per_page)
            page_obj = paginator.get_page(page_number)
    
    # Statistiques mises à jour selon les filtres appliqués
    all_articles = Article.objects.all().filter(actif=True)
    stats = {
        'total_articles': all_articles.count(),
        'articles_disponibles': all_articles.filter(variantes__qte_disponible__gt=0, variantes__actif=True).distinct().count(),
        'articles_en_cours': all_articles.filter(phase='EN_COURS').count(),
        'articles_liquidation': all_articles.filter(phase='LIQUIDATION').count(),
        'articles_test': all_articles.filter(phase='EN_TEST').count(),
        'articles_promotion': all_articles.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct().count(),
        'articles_rupture': all_articles.exclude(variantes__qte_disponible__gt=0, variantes__actif=True).distinct().count(),
        'articles_stock_faible': all_articles.filter(
            variantes__qte_disponible__gt=0, 
            variantes__qte_disponible__lt=5, 
            variantes__actif=True
        ).distinct().count(),
    }
    
    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        try:
            # Debug: Vérifier les données de page_obj  
            items_in_page = list(page_obj.object_list)  # Éviter de consommer l'itérateur
            print(f"🔍 DEBUG - Page: {page_obj.number}, Total items: {page_obj.paginator.count}, Items in page: {len(items_in_page)}")
            
            # Rendre les templates partiels pour AJAX
            html_cards_body = render_to_string('article/partials/_articles_cards_body.html', {
                'page_obj': page_obj
            }, request=request)
            print(f"📄 Cards body length: {len(html_cards_body)}")
            
            html_table_body = render_to_string('article/partials/_articles_table_body.html', {
                'page_obj': page_obj
            }, request=request)
            print(f"📄 Table body length: {len(html_table_body)}")
            
            # Vue grille
            html_grid_body = render_to_string('article/partials/_articles_grid_body.html', {
                'page_obj': page_obj
            }, request=request)
            
            html_pagination = render_to_string('article/partials/_articles_pagination.html', {
                'page_obj': page_obj,
                'search': search,
                'filtre_phase': filtre_phase,
                'filtre_promotion': filtre_promotion,
                'filtre_stock': filtre_stock,
                'items_per_page': items_per_page,
                'start_range': start_range,
                'end_range': end_range
            }, request=request)
            print(f"📄 Pagination length: {len(html_pagination)}")
            
            html_pagination_info = render_to_string('article/partials/_articles_pagination_info.html', {
                'page_obj': page_obj
            }, request=request)
            print(f"📄 Pagination info length: {len(html_pagination_info)}")
            
            response_data = {
                'success': True,
                'html_cards_body': html_cards_body,
                'html_table_body': html_table_body,
                'html_grid_body': html_grid_body,
                'html_pagination': html_pagination,
                'html_pagination_info': html_pagination_info,
                'total_count': articles_non_pagines.count(),
                'debug_info': {
                    'page_number': page_obj.number,
                    'total_items': page_obj.paginator.count,
                    'items_in_page': len(list(page_obj)),
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next(),
                }
            }
            
            print(f"✅ JSON Response ready: {len(str(response_data))} chars")
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ Erreur dans la vue AJAX: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Erreur dans la génération des templates: {str(e)}'
            }, status=500)

    context = {
        'page_obj': page_obj,
        'search': search,
        'stats': stats,
        'form_promotion': form_promotion,
        'filtre_phase': filtre_phase,
        'filtre_promotion': filtre_promotion,
        'filtre_stock': filtre_stock,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }
    return render(request, 'article/liste.html', context)

@login_required
def detail_article(request, id):
    """Détail d'un article"""
    article = get_object_or_404(Article, id=id, actif=True)

    # Articles similaires (même catégorie)
    articles_similaires = Article.objects.filter(
        categorie=article.categorie,
        actif=True
    ).exclude(id=article.id).order_by('nom')[:6]
    
    # Calculer les statistiques des variantes
    variantes = article.variantes.all()
    stats_variantes = {
        'total': variantes.count(),
        'en_stock': variantes.filter(qte_disponible__gt=0).count(),
        'stock_faible': variantes.filter(qte_disponible__gt=0, qte_disponible__lt=5).count(),
        'rupture': variantes.filter(qte_disponible=0).count(),
    }
    
    # Préparer les données pour le tableau croisé
    # Récupérer toutes les pointures et couleurs uniques
    pointures_uniques = sorted(set(v.pointure.pointure for v in variantes), key=int)
    couleurs_uniques = sorted(set(v.couleur.nom for v in variantes))
    
    # Créer la matrice du tableau croisé
    tableau_croise = {}
    for pointure in pointures_uniques:
        tableau_croise[pointure] = {}
        for couleur in couleurs_uniques:
            # Chercher la variante correspondante
            variante = variantes.filter(pointure__pointure=pointure, couleur__nom=couleur).first()
            if variante:
                tableau_croise[pointure][couleur] = {
                    'stock': variante.qte_disponible,
                    'status': 'normal' if variante.qte_disponible >= 5 else 'faible' if variante.qte_disponible > 0 else 'rupture'
                }
            else:
                tableau_croise[pointure][couleur] = {'stock': None, 'status': 'inexistant'}
    
    # Récupérer l'URL de la page précédente, avec fallback
    previous_page = request.META.get('HTTP_REFERER', reverse('article:liste'))
    
    context = {
        'article': article,
        'articles_similaires': articles_similaires,
        'previous_page': previous_page,
        'stats_variantes': stats_variantes,
        'tableau_croise': tableau_croise,
        'pointures_uniques': pointures_uniques,
        'couleurs_uniques': couleurs_uniques,
    }
    return render(request, 'article/detail.html', context)

@login_required
def creer_article(request):
    """Créer un nouvel article"""
    categories = Categorie.objects.all()
    genres = Genre.objects.all()
    couleurs = Couleur.objects.filter(actif=True).order_by('nom')
    pointures = Pointure.objects.filter(actif=True).order_by('ordre', 'pointure')

    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom = request.POST.get('nom')
            couleur_id = request.POST.get('couleur')
            pointure_id = request.POST.get('pointure')

            # Vérifier l'unicité de la combinaison nom, couleur, pointure
            if VarianteArticle.objects.filter(
                article__nom=nom, 
                couleur_id=couleur_id, 
                pointure_id=pointure_id
            ).exists():
                messages.error(request, "Un article avec le même nom, couleur et pointure existe déjà.")
                # Renvoyer le formulaire avec les données saisies
                return render(request, 'article/creer.html', {
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })

            # Vérifier l'unicité du modèle
            modele = request.POST.get('modele')
            if modele:
                try:
                    modele_int = int(modele)
                    if modele_int <= 0:
                        messages.error(request, "Le numéro du modèle doit être supérieur à 0.")
                        return render(request, 'article/creer.html', {
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                    
                    # Vérifier si le modèle existe déjà
                    if Article.objects.filter(modele=modele_int).exists():
                        messages.error(request, f"Le modèle {modele_int} est déjà utilisé par un autre article.")
                        return render(request, 'article/creer.html', {
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                except ValueError:
                    messages.error(request, "Le numéro du modèle doit être un nombre entier valide.")
                    return render(request, 'article/creer.html', {
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })

            # Valider et convertir le prix
            prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
            if not prix_str:
                messages.error(request, "Le prix unitaire est obligatoire.")
                return render(request, 'article/creer.html', {
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })
            
            try:
                prix_unitaire = float(prix_str)
                if prix_unitaire <= 0:
                    messages.error(request, "Le prix unitaire doit être supérieur à 0.")
                    return render(request, 'article/creer.html', {
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })
            except ValueError:
                messages.error(request, "Le prix unitaire doit être un nombre valide.")
                return render(request, 'article/creer.html', {
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })

            # Créer l'article principal
            article = Article()
            article.nom = nom
            article.modele = int(modele) if modele else None
            article.description = request.POST.get('description')
            article.prix_unitaire = prix_unitaire
            article.prix_actuel = prix_unitaire  # Assurer que le prix actuel = prix unitaire
            article.categorie_id = request.POST.get('categorie')
            article.genre_id = request.POST.get('genre')
            
            # Générer automatiquement la référence
            if article.categorie_id and article.genre_id and article.modele:
                # Sauvegarder temporairement pour pouvoir générer la référence
                article.save()
                article.refresh_from_db()
                reference_auto = article.generer_reference_automatique()
                if reference_auto:
                    article.reference = reference_auto
                    article.save()
            
            # Gérer le prix d'achat
            prix_achat_str = request.POST.get('prix_achat', '').strip().replace(',', '.')
            if prix_achat_str:
                try:
                    prix_achat = float(prix_achat_str)
                    if prix_achat >= 0:
                        article.prix_achat = prix_achat
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            # Gérer les nouveaux champs
            article.isUpsell = request.POST.get('isUpsell') == 'on'
            article.Compteur = 0  # Initialiser le compteur à 0
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            for i in range(1, 5):
                prix_upsell_str = request.POST.get(f'prix_upsell_{i}', '').strip().replace(',', '.')
                if prix_upsell_str:
                    try:
                        prix_upsell = float(prix_upsell_str)
                        if prix_upsell > 0:
                            setattr(article, f'prix_upsell_{i}', prix_upsell)
                    except ValueError:
                        # Ignorer les valeurs non numériques
                        pass
            
            # Gérer le prix upsell final
            prix_upsell_final_str = request.POST.get('prix_uspell_final', '').strip().replace(',', '.')
            if prix_upsell_final_str:
                try:
                    prix_upsell_final = float(prix_upsell_final_str)
                    if prix_upsell_final > 0:
                        article.prix_uspell_final = prix_upsell_final
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            # Gérer le prix de liquidation
            prix_liquidation_str = request.POST.get('Prix_liquidation', '').strip().replace(',', '.')
            if prix_liquidation_str:
                try:
                    prix_liquidation = float(prix_liquidation_str)
                    if prix_liquidation > 0:
                        article.Prix_liquidation = prix_liquidation
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            article.save()
            
            # Vérifier si c'est une requête AJAX (pour la création des variantes)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'article_id': article.id,
                    'article_nom': article.nom,
                    'message': f"Article '{article.nom}' créé avec succès"
                })
            
            messages.success(request, f"L'article '{article.nom}' a été créé avec succès.")
            
            return redirect('article:liste')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'article : {str(e)}")
            return render(request, 'article/creer.html', {
                'form_data': request.POST,
                'categories': categories,
                'genres': genres,
                'couleurs': couleurs,
                'pointures': pointures
            })
        
    context = {
        'categories': categories,
        'genres': genres,
        'couleurs': couleurs,
        'pointures': pointures,
    }
    
    return render(request,'article/creer.html',context)

@login_required
def modifier_article(request, id):
    """Modifier un article existant"""
    article = get_object_or_404(Article, id=id, actif=True)
    categories = Categorie.objects.all()
    genres = Genre.objects.all()
    couleurs = Couleur.objects.filter(actif=True).order_by('nom')
    pointures = Pointure.objects.filter(actif=True).order_by('ordre', 'pointure')

    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            couleur_id = request.POST.get('couleur')
            pointure_id = request.POST.get('pointure')

            # Vérifier l'unicité de la combinaison nom, couleur, pointure
            if VarianteArticle.objects.filter(
                article__nom=nom, 
                couleur_id=couleur_id, 
                pointure_id=pointure_id
            ).exclude(article=article).exists():
                messages.error(request, "Un autre article avec le même nom, couleur et pointure existe déjà.")
                return render(request, 'article/modifier.html', {
                    'article': article, 
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })

            # Vérifier l'unicité du modèle
            modele = request.POST.get('modele')
            if modele:
                try:
                    modele_int = int(modele)
                    if modele_int <= 0:
                        messages.error(request, "Le numéro du modèle doit être supérieur à 0.")
                        return render(request, 'article/modifier.html', {
                            'article': article, 
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                    
                    # Vérifier si le modèle existe déjà sur un autre article
                    if Article.objects.filter(modele=modele_int).exclude(id=article.id).exists():
                        messages.error(request, f"Le modèle {modele_int} est déjà utilisé par un autre article.")
                        return render(request, 'article/modifier.html', {
                            'article': article, 
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                except ValueError:
                    messages.error(request, "Le numéro du modèle doit être un nombre entier valide.")
                    return render(request, 'article/modifier.html', {
                        'article': article, 
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })

            # Valider et convertir le prix
            prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
            if not prix_str:
                messages.error(request, "Le prix unitaire est obligatoire.")
                return render(request, 'article/modifier.html', {
                    'article': article, 
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })
            
            try:
                prix_unitaire = float(prix_str)
                if prix_unitaire <= 0:
                    messages.error(request, "Le prix unitaire doit être supérieur à 0.")
                    return render(request, 'article/modifier.html', {
                        'article': article, 
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })
            except ValueError:
                messages.error(request, "Le prix unitaire doit être un nombre valide.")
                return render(request, 'article/modifier.html', {
                    'article': article, 
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })

            # Valider la quantité


            article.nom = nom
            article.reference = request.POST.get('reference')
            article.modele = int(modele) if modele else None
            article.description = request.POST.get('description')
            article.prix_unitaire = prix_unitaire
            # La quantité est maintenant gérée dans les variantes
            article.categorie_id = request.POST.get('categorie')
            article.genre_id = request.POST.get('genre')
            
            # Générer automatiquement la référence
            if article.categorie_id and article.genre_id and article.modele:
                reference_auto = article.generer_reference_automatique()
                if reference_auto:
                    article.reference = reference_auto
            
            # Gérer le prix d'achat
            prix_achat_str = request.POST.get('prix_achat', '').strip().replace(',', '.')
            if prix_achat_str:
                try:
                    prix_achat = float(prix_achat_str)
                    if prix_achat >= 0:
                        article.prix_achat = prix_achat
                except ValueError:
                    # Ignorer les valeurs non numériques
                    pass
            
            # Gérer les nouveaux champs
            article.isUpsell = request.POST.get('isUpsell') == 'on'
            # Ne pas modifier le compteur existant - il est géré par d'autres processus
            
            # Récupérer et définir la phase
            phase = request.POST.get('phase')
            # Vérifier si l'article est en promotion avant de changer sa phase
            if phase and phase in dict(Article.PHASE_CHOICES).keys():
                if article.has_promo_active:
                    messages.warning(request, f"Impossible de changer la phase de l'article car il est actuellement en promotion.")
                else:
                    # Vérifier si l'upsell était actif avant le changement
                    upsell_was_active = article.isUpsell
                    old_phase = article.phase
                    
                    article.phase = phase
                    
                    # Message avec info sur l'upsell si désactivé
                    upsell_message = ""
                    if upsell_was_active and phase in ['LIQUIDATION', 'EN_TEST'] and old_phase != phase:
                        upsell_message = " L'upsell a été automatiquement désactivé."
                    
                    if phase == 'LIQUIDATION':
                        messages.warning(request, f"L'article '{article.nom}' a été mis en liquidation.{upsell_message}")
                    elif phase == 'EN_TEST':
                        messages.info(request, f"L'article '{article.nom}' a été mis en phase de test.{upsell_message}")
                    elif phase == 'PROMO':
                        messages.success(request, f"L'article '{article.nom}' a été mis en phase promotion.{upsell_message}")
                    elif phase == 'EN_COURS':
                        messages.success(request, f"L'article '{article.nom}' a été remis en phase par défaut (En Cours).{upsell_message}")
            
            # Gérer l'image si elle est fournie
            if 'image' in request.FILES:
                article.image = request.FILES['image']
            
            # Gérer les prix de substitution (upsell)
            # Réinitialiser les prix upsell
            article.prix_upsell_1 = None
            article.prix_upsell_2 = None
            article.prix_upsell_3 = None
            article.prix_upsell_4 = None
            
            for i in range(1, 5):
                prix_upsell_str = request.POST.get(f'prix_upsell_{i}', '').strip().replace(',', '.')
                if prix_upsell_str:
                    try:
                        prix_upsell = float(prix_upsell_str)
                        if prix_upsell > 0:
                            setattr(article, f'prix_upsell_{i}', prix_upsell)
                    except ValueError:
                        # Ignorer les valeurs non numériques
                        pass
            
            # Gérer le prix upsell final
            prix_upsell_final_str = request.POST.get('prix_uspell_final', '').strip().replace(',', '.')
            if prix_upsell_final_str:
                try:
                    prix_upsell_final = float(prix_upsell_final_str)
                    if prix_upsell_final > 0:
                        article.prix_uspell_final = prix_upsell_final
                    else:
                        article.prix_uspell_final = None
                except ValueError:
                    # Ignorer les valeurs non numériques
                    article.prix_uspell_final = None
            else:
                article.prix_upsell_final = None
            
            # Gérer le prix de liquidation
            prix_liquidation_str = request.POST.get('Prix_liquidation', '').strip().replace(',', '.')
            if prix_liquidation_str:
                try:
                    prix_liquidation = float(prix_liquidation_str)
                    if prix_liquidation > 0:
                        article.Prix_liquidation = prix_liquidation
                    else:
                        article.Prix_liquidation = None
                except ValueError:
                    # Ignorer les valeurs non numériques
                    article.Prix_liquidation = None
            else:
                article.Prix_liquidation = None
            
            # Mettre à jour le prix actuel pour qu'il soit égal au prix unitaire
            # sauf si l'article est en promotion active
            if not article.has_promo_active:
                article.prix_actuel = article.prix_unitaire
            
            article.save()
            
            # Traiter les mises à jour des variantes existantes
            variantes_mises_a_jour = 0
            for key, value in request.POST.items():
                if key.startswith('variante_existante_') and key.endswith('_modifiee') and value == 'true':
                    # Extraire l'ID de la variante
                    variante_id = key.replace('variante_existante_', '').replace('_modifiee', '')
                    try:
                        variante_id = int(variante_id)
                        # Récupérer la nouvelle quantité
                        quantite_key = f'variante_existante_{variante_id}_quantite'
                        nouvelle_quantite = request.POST.get(quantite_key, '0')
                        
                        # Mettre à jour la variante
                        variante = VarianteArticle.objects.get(id=variante_id, article=article)
                        ancienne_quantite = variante.qte_disponible
                        variante.qte_disponible = int(nouvelle_quantite) if nouvelle_quantite else 0
                        variante.save()
                        
                        variantes_mises_a_jour += 1
                        couleur_nom = variante.couleur.nom if variante.couleur else "Aucune couleur"
                        pointure_nom = variante.pointure.pointure if variante.pointure else "Aucune pointure"
                        messages.success(request, f"Quantité mise à jour pour {couleur_nom} / {pointure_nom} : {ancienne_quantite} → {variante.qte_disponible}")
                        
                    except (ValueError, VarianteArticle.DoesNotExist) as e:
                        messages.error(request, f"Erreur lors de la mise à jour de la variante {variante_id}: {str(e)}")
            
            # Traiter les nouvelles variantes ajoutées via le modal
            variantes_crees = 0
            variantes_errors = []
            
            # Récupérer toutes les nouvelles variantes soumises
            variantes_data = {}
            for key, value in request.POST.items():
                if key.startswith('variante_') and '_' in key and not key.startswith('variante_existante_'):
                    parts = key.split('_')
                    if len(parts) >= 4:
                        variante_id = parts[1]
                        field_type = parts[2]
                        if variante_id not in variantes_data:
                            variantes_data[variante_id] = {}
                        variantes_data[variante_id][field_type] = value
            
            # Créer les nouvelles variantes
            for variante_id, variante_info in variantes_data.items():
                couleur_id_variante = variante_info.get('couleur', '')
                pointure_id_variante = variante_info.get('pointure', '')
                quantite = variante_info.get('quantite', '0')
                reference_variante = variante_info.get('reference', '')
                
                # Vérifier qu'au moins une couleur ou une pointure est spécifiée
                if not couleur_id_variante and not pointure_id_variante:
                    variantes_errors.append(f"Variante {variante_id}: Au moins une couleur ou une pointure doit être spécifiée.")
                    continue
                
                try:
                    # Vérifier l'unicité de la combinaison
                    if VarianteArticle.objects.filter(
                        article=article,
                        couleur_id=couleur_id_variante if couleur_id_variante else None,
                        pointure_id=pointure_id_variante if pointure_id_variante else None
                    ).exists():
                        variantes_errors.append(f"Variante {variante_id}: Cette combinaison couleur/pointure existe déjà pour cet article.")
                        continue
                    
                    # Créer la variante
                    variante = VarianteArticle()
                    variante.article = article
                    variante.couleur_id = couleur_id_variante if couleur_id_variante else None
                    variante.pointure_id = pointure_id_variante if pointure_id_variante else None
                    variante.qte_disponible = int(quantite) if quantite else 0
                    variante.prix_unitaire = prix_unitaire
                    variante.prix_achat = article.prix_achat
                    variante.prix_actuel = prix_unitaire
                    variante.actif = True
                    
                    # Définir la référence de la variante
                    if reference_variante:
                        variante.reference_variante = reference_variante
                    else:
                        # Générer automatiquement la référence
                        variante.reference_variante = variante.generer_reference_variante_automatique()
                    variante.reference_variante = variante.generer_reference_variante_automatique()
                    
                    variante.save()
                    variantes_crees += 1
                    
                    # Message de succès pour chaque variante créée
                    couleur_nom = variante.couleur.nom if variante.couleur else "Aucune couleur"
                    pointure_nom = variante.pointure.pointure if variante.pointure else "Aucune pointure"
                    messages.success(request, f"Nouvelle variante créée : {couleur_nom} / {pointure_nom} - Référence: {variante.reference_variante}")
                    
                except Exception as e:
                    variantes_errors.append(f"Variante {variante_id}: Erreur lors de la création - {str(e)}")
            
            # Afficher les erreurs s'il y en a
            if variantes_errors:
                for error in variantes_errors:
                    messages.error(request, error)
            
            # Message de succès global
            message_succes = f"L'article '{article.nom}' a été modifié avec succès."
            if variantes_mises_a_jour > 0:
                message_succes += f" {variantes_mises_a_jour} variante(s) mise(s) à jour."
            if variantes_crees > 0:
                message_succes += f" {variantes_crees} nouvelle(s) variante(s) créée(s)."
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message_succes,
                    'redirect_url': reverse('article:detail', args=[article.id])
                })
                
            messages.success(request, message_succes)
            return redirect('article:detail', id=article.id)
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la modification de l'article : {str(e)}")
            
            # Calculer les couleurs et pointures uniques pour le tableau croisé (même en cas d'erreur)
            couleurs_uniques = []
            pointures_uniques = []
            
            if article.variantes.exists():
                couleurs_uniques = list(article.variantes.exclude(couleur__isnull=True).values_list('couleur__nom', flat=True).distinct().order_by('couleur__nom'))
                pointures_uniques = list(article.variantes.exclude(pointure__isnull=True).values_list('pointure__pointure', flat=True).distinct().order_by('pointure__ordre', 'pointure__pointure'))
                
                if article.variantes.filter(couleur__isnull=True).exists():
                    couleurs_uniques.append("Aucune couleur")
                    
                if article.variantes.filter(pointure__isnull=True).exists():
                    pointures_uniques.append("Aucune pointure")
            
            return render(request, 'article/modifier.html', {
        'article': article,
                'form_data': request.POST,
        'categories': categories,
                'genres': genres,
                'couleurs': couleurs,
                'pointures': pointures,
                'couleurs_uniques': couleurs_uniques,
                'pointures_uniques': pointures_uniques,
            })
    
    # Préparer les données pour le tableau croisé (matrice complète)
    variantes = article.variantes.all()
    couleurs_uniques = []
    pointures_uniques = []
    tableau_matrice = []
    
    if variantes.exists():
        # Récupérer toutes les pointures et couleurs uniques
        pointures_uniques = sorted(set(v.pointure.pointure for v in variantes if v.pointure), key=lambda x: int(x) if x.isdigit() else float('inf'))
        couleurs_uniques = sorted(set(v.couleur.nom for v in variantes if v.couleur))
        
        # Créer une matrice complète ligne par ligne
        for pointure in pointures_uniques:
            ligne = {
                'pointure': pointure,
                'cellules': []
            }
            
            for couleur in couleurs_uniques:
                # Chercher la variante correspondante
                variante = variantes.filter(pointure__pointure=pointure, couleur__nom=couleur).first()
                if variante:
                    ligne['cellules'].append({
                        'existe': True,
                        'id': variante.id,
                        'couleur': couleur,
                        'stock': variante.qte_disponible,
                        'reference': variante.reference_variante,
                        'status': 'normal' if variante.qte_disponible >= 5 else 'faible' if variante.qte_disponible > 0 else 'rupture'
                    })
                else:
                    ligne['cellules'].append({
                        'existe': False,
                        'couleur': couleur
                    })
            
            tableau_matrice.append(ligne)

    context = {
        'article': article,
        'categories': categories,
        'genres': genres,
        'couleurs': couleurs,
        'pointures': pointures,
        'couleurs_uniques': couleurs_uniques,
        'pointures_uniques': pointures_uniques,
        'tableau_matrice': tableau_matrice,
    }
    return render(request, 'article/modifier.html', context)

@login_required
@require_POST
def supprimer_article(request, id):
    """Supprimer un article (méthode POST requise)"""
    article = get_object_or_404(Article, id=id)
    try:
        article.delete()
        messages.success(request, f"L'article '{article.nom}' a été supprimé avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression de l'article : {e}")
    return redirect('article:liste')

@require_POST
@login_required
def supprimer_articles_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun article sélectionné pour la suppression.")
        return redirect('article:liste')

    try:
        count = Article.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} article(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('article:liste')

@login_required
@csrf_exempt
def supprimer_variantes_masse(request):
    """Suppression en masse des variantes d'articles"""
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune variante d'article sélectionnée pour la suppression.")
        return redirect('article:liste_variantes')

    try:
        count = VarianteArticle.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} variante(s) d'article(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('article:liste_variantes')

@login_required
def articles_par_categorie(request, categorie):
    """Articles filtrés par catégorie"""
    articles = Article.objects.filter(
        categorie__nom__icontains=categorie,
        actif=True
    ).order_by('nom')
    
    # Recherche dans la catégorie
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(nom__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(articles, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categorie': categorie,
        'search': search,
        'total_articles': articles.count(),
    }
    return render(request, 'article/categorie.html', context)

@login_required
def stock_faible(request):
    """Articles avec stock faible (moins de 5 unités)"""
    articles = Article.objects.filter(
        variantes__qte_disponible__lt=5,
        variantes__qte_disponible__gt=0,
        variantes__actif=True,
        actif=True
    ).order_by('variantes__qte_disponible', 'nom')
    
    # Pagination
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_articles': articles.count(),
    }
    return render(request, 'article/stock_faible.html', context)

@login_required
def rupture_stock(request):
    """Articles en rupture de stock"""
    articles = Article.objects.filter(
        variantes__qte_disponible=0,
        variantes__actif=True,
        actif=True
    ).order_by('nom', 'variantes__couleur__nom', 'variantes__pointure__pointure')
    
    # Pagination
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_articles': articles.count(),
    }
    return render(request, 'article/rupture_stock.html', context)

@login_required
def liste_promotions(request):
    """Liste des promotions avec recherche et filtres"""
    promotions = Promotion.objects.all().order_by('-date_creation')
    
    # Formulaire de promotion pour le modal
    form_promotion = PromotionForm()
    
    # Filtres
    filtre = request.GET.get('filtre', 'toutes')
    now = timezone.now()
    
    if filtre == 'actives':
        promotions = promotions.filter(active=True, date_debut__lte=now, date_fin__gte=now)
    elif filtre == 'futures':
        promotions = promotions.filter(active=True, date_debut__gt=now)
    elif filtre == 'expirees':
        promotions = promotions.filter(date_fin__lt=now)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        promotions = promotions.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 10)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des promotions non paginées pour les statistiques
    promotions_non_paginees = promotions
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                promotions = list(promotions)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(promotions, len(promotions))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 10
            paginator = Paginator(promotions, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher toutes les promotions
            paginator = Paginator(promotions, promotions.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 10
            except (ValueError, TypeError):
                items_per_page = 10
            
            paginator = Paginator(promotions, items_per_page)
            page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': Promotion.objects.count(),
        'actives': Promotion.objects.filter(
            active=True,
            date_debut__lte=now,
            date_fin__gte=now
        ).count(),
        'futures': Promotion.objects.filter(
            active=True,
            date_debut__gt=now
        ).count(),
        'articles_en_promo': Article.objects.filter(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        ).distinct().count()
    }
    
    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        # Rendre les templates partiels pour AJAX
        html_table_body = render_to_string('article/partials/_promotions_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('article/partials/_promotions_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre': filtre,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('article/partials/_promotions_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': promotions_non_paginees.count()
        })

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filtre': filtre,
        'search': search,
        'form_promotion': form_promotion,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
        'current_time': now,  # Ajouter l'heure actuelle pour le fuseau horaire
    }
    return render(request, 'article/liste_promotions.html', context)

@login_required
def detail_promotion(request, id):
    """Détail d'une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    # Articles en promotion
    articles = promotion.articles.all().order_by('nom')
    
    context = {
        'promotion': promotion,
        'articles': articles
    }
    return render(request, 'article/detail_promotion.html', context)

@login_required
def creer_promotion(request):
    """Créer une nouvelle promotion"""
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            try:
                # Récupérer les articles sélectionnés avant de sauvegarder
                articles_selectionnes = form.cleaned_data.get('articles', [])
                
                # Créer la promotion sans les articles pour l'instant
                promotion = form.save(commit=False)
                promotion.cree_par = request.user
                promotion.save()
                
                # Maintenant que la promotion a un ID, ajouter les articles
                if articles_selectionnes:
                    promotion.articles.set(articles_selectionnes)
                
                    # Vérifier si la promotion doit être active automatiquement
                    now = timezone.now()
                    if promotion.active and promotion.date_debut <= now <= promotion.date_fin:
                        # Compter les articles avec upsell actif avant application
                        articles_avec_upsell = sum(1 for article in articles_selectionnes if article.isUpsell)
                        
                        # Appliquer la promotion aux articles sélectionnés
                        promotion.activer_promotion()
                        
                        # Message avec info sur les upsells désactivés
                        upsell_message = ""
                        if articles_avec_upsell > 0:
                            upsell_message = f" {articles_avec_upsell} upsell(s) ont été automatiquement désactivé(s)."
                        
                        messages.success(request, f"La promotion '{promotion.nom}' a été créée et activée avec succès. Les réductions ont été appliquées aux {len(articles_selectionnes)} article(s) sélectionné(s).{upsell_message}")
                    else:
                        messages.success(request, f"La promotion '{promotion.nom}' a été créée avec succès.")
                else:
                    messages.success(request, f"La promotion '{promotion.nom}' a été créée avec succès.")
                
                return redirect('article:detail_promotion', id=promotion.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la promotion : {str(e)}")
                # Renommer form en form_promotion pour correspondre au template
                return render(request, 'article/liste_promotions.html', {
                    'form_promotion': form,
                    'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
                })
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
            # Renommer form en form_promotion pour correspondre au template
            return render(request, 'article/liste_promotions.html', {
                'form_promotion': form,
                'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
            })
    else:
        # Cette partie ne devrait pas être appelée directement, mais au cas où
        form = PromotionForm()
        return redirect('article:liste_promotions')

@login_required
def modifier_promotion(request, id):
    """Modifier une promotion existante"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        # Conserver les anciens articles pour comparaison
        anciens_articles = list(promotion.articles.all())
        
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            promotion_modifiee = form.save()
            
            # Récupérer les nouveaux articles
            nouveaux_articles = list(promotion_modifiee.articles.all())
            
            # Vérifier si la promotion doit être active
            now = timezone.now()
            if promotion_modifiee.active and promotion_modifiee.date_debut <= now <= promotion_modifiee.date_fin:
                # Retirer la promotion des anciens articles qui ne sont plus dans la promotion
                for article in anciens_articles:
                    if article not in nouveaux_articles:
                        # Vérifier si l'article n'a pas d'autres promotions actives
                        autres_promotions_actives = article.promotions.filter(
                            active=True,
                            date_debut__lte=now,
                            date_fin__gte=now
                        ).exclude(id=promotion_modifiee.id).exists()
                        
                        if not autres_promotions_actives:
                            article.retirer_promotion()
                        else:
                            article.update_prix_actuel()
                
                # Appliquer la promotion aux nouveaux articles
                for article in nouveaux_articles:
                    article.appliquer_promotion(promotion_modifiee)
                
                messages.success(request, f"La promotion '{promotion.nom}' a été modifiée avec succès. Les prix ont été mis à jour.")
            else:
                # Si la promotion n'est pas active, retirer la promotion de tous les anciens articles
                for article in anciens_articles:
                    autres_promotions_actives = article.promotions.filter(
                        active=True,
                        date_debut__lte=now,
                        date_fin__gte=now
                    ).exclude(id=promotion_modifiee.id).exists()
                    
                    if not autres_promotions_actives:
                        article.retirer_promotion()
                    else:
                        article.update_prix_actuel()
                
            messages.success(request, f"La promotion '{promotion.nom}' a été modifiée avec succès.")
            
            return redirect('article:detail_promotion', id=promotion.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = PromotionForm(instance=promotion)
    
    context = {
        'promotion': promotion,
        'form': form,
        'current_time': timezone.now(),  # Ajouter l'heure actuelle pour le fuseau horaire
    }
    return render(request, 'article/modifier_promotion.html', context)

@login_required
def supprimer_promotion(request, id):
    """Supprimer une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        nom = promotion.nom
        promotion.delete()
        messages.success(request, f"La promotion '{nom}' a été supprimée avec succès.")
        return redirect('article:liste_promotions')
    
    return render(request, 'article/supprimer_promotion.html', {'promotion': promotion})

@login_required
def activer_desactiver_promotion(request, id):
    """Activer ou désactiver une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if promotion.active:
        # Désactiver la promotion
        promotion.desactiver_promotion()
        action = "désactivée"
        messages.success(request, f"La promotion '{promotion.nom}' a été {action} avec succès. Les prix des articles ont été remis à leur état initial.")
    else:
        # Compter les articles avec upsell actif avant activation
        articles_avec_upsell = sum(1 for article in promotion.articles.all() if article.isUpsell)
        
        # Activer la promotion
        promotion.activer_promotion()
        action = "activée"
        
        # Message avec info sur les upsells désactivés
        upsell_message = ""
        if articles_avec_upsell > 0:
            upsell_message = f" {articles_avec_upsell} upsell(s) ont été automatiquement désactivé(s)."
        
        messages.success(request, f"La promotion '{promotion.nom}' a été {action} avec succès. Les réductions ont été appliquées aux articles.{upsell_message}")
    
    # Rediriger vers la page précédente ou la liste des promotions
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:liste_promotions')

@login_required
def changer_phase(request, id):
    """Changer la phase d'un article"""
    article = get_object_or_404(Article, id=id)
    now = timezone.now()
    
    if request.method == 'POST':
        phase = request.POST.get('phase')
        
        # Cas spécial : liquidation avec prix de la base de données
        if phase == 'LIQUIDATION_DB':
            return appliquer_liquidation_prix_db(request, id)
        
        if phase in dict(Article.PHASE_CHOICES).keys():
            # Vérifier si l'upsell était actif avant le changement
            upsell_was_active = article.isUpsell
            
            # Si on remet en phase par défaut et qu'il y a une promotion active, la désactiver
            if phase == 'EN_COURS' and article.has_promo_active:
                from article.models import Promotion
                # Désactiver toutes les promotions actives pour cet article
                promotions_actives = article.promotions.filter(
                    active=True,
                    date_debut__lte=now,
                    date_fin__gte=now
                )
                for promotion in promotions_actives:
                    promotion.active = False
                    promotion.save()
            
            article.phase = phase
            
            # Réinitialiser le prix actuel au prix unitaire lors du retour en phase par défaut
            if phase == 'EN_COURS':
                article.prix_actuel = article.prix_unitaire
            
            # L'upsell sera automatiquement désactivé par la méthode save() si nécessaire
            article.save()
            
            # Message en fonction de la phase avec info sur l'upsell
            upsell_message = " L'upsell a été automatiquement désactivé." if upsell_was_active and phase in ['LIQUIDATION', 'EN_TEST'] else ""
            
            if phase == 'EN_COURS':
                promotion_message = " Les promotions actives ont été désactivées." if article.promotions.filter(active=False).exists() else ""
                messages.success(request, f"L'article '{article.nom}' a été remis en phase par défaut (En Cours) et son prix réinitialisé.{upsell_message}{promotion_message}")
            elif phase == 'LIQUIDATION':
                messages.warning(request, f"L'article '{article.nom}' a été mis en liquidation.{upsell_message}")
            elif phase == 'EN_TEST':
                messages.info(request, f"L'article '{article.nom}' a été mis en phase de test.{upsell_message}")
            elif phase == 'PROMO':
                messages.success(request, f"L'article '{article.nom}' a été mis en phase promotion.{upsell_message}")
                
    # Rediriger vers la page précédente ou la page de détail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:detail', id=article.id)

@login_required
@require_POST
def appliquer_liquidation(request, id):
    """Applique une réduction de liquidation à un article"""
    article = get_object_or_404(Article, id=id)
    
    # Vérifier si l'article est déjà en promotion
    if article.has_promo_active:
        messages.error(request, "Impossible d'appliquer une liquidation car l'article est en promotion.")
        return redirect('article:detail', id=article.id)
    
    try:
        pourcentage = Decimal(request.POST.get('pourcentage', '0'))
        if pourcentage <= 0 or pourcentage > 90:
            messages.error(request, "Le pourcentage de réduction doit être compris entre 0 et 90%.")
            return redirect('article:detail', id=article.id)
        
        # Désactiver l'upsell avant de mettre en liquidation
        upsell_was_active = article.isUpsell
        
        # Mettre l'article en liquidation
        article.phase = 'LIQUIDATION'
        # Calculer et appliquer la réduction
        reduction = article.prix_unitaire * (pourcentage / 100)
        article.prix_actuel = article.prix_unitaire - reduction
        # L'upsell sera automatiquement désactivé par la méthode save()
        article.save()
        
        if upsell_was_active:
            messages.success(request, f"L'article a été mis en liquidation avec une réduction de {pourcentage}%. L'upsell a été automatiquement désactivé.")
        else:
            messages.success(request, f"L'article a été mis en liquidation avec une réduction de {pourcentage}%.")
        
    except (ValueError, TypeError):
        messages.error(request, "Le pourcentage de réduction n'est pas valide.")
    
    return redirect('article:detail', id=article.id)

@login_required
@require_POST
def appliquer_liquidation_prix_db(request, id):
    """Applique la liquidation en utilisant le Prix_liquidation de la base de données"""
    article = get_object_or_404(Article, id=id)
    
    # Vérifier si l'article est déjà en promotion
    if article.has_promo_active:
        messages.error(request, "Impossible d'appliquer une liquidation car l'article est en promotion.")
        return redirect('article:detail', id=article.id)
    
    # Vérifier si l'article a un prix de liquidation défini
    if not article.Prix_liquidation or article.Prix_liquidation <= 0:
        messages.error(request, "Aucun prix de liquidation défini pour cet article.")
        return redirect('article:detail', id=article.id)
    
    try:
        # Désactiver l'upsell avant de mettre en liquidation
        upsell_was_active = article.isUpsell
        
        # Mettre l'article en liquidation
        article.phase = 'LIQUIDATION'
        # Appliquer le prix de liquidation défini en base
        article.prix_actuel = article.Prix_liquidation
        # L'upsell sera automatiquement désactivé par la méthode save()
        article.save()
        
        if upsell_was_active:
            messages.success(request, f"L'article a été mis en liquidation au prix de {article.Prix_liquidation} DH. L'upsell a été automatiquement désactivé.")
        else:
            messages.success(request, f"L'article a été mis en liquidation au prix de {article.Prix_liquidation} DH.")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'application de la liquidation : {str(e)}")
    
    return redirect('article:detail', id=article.id)

@login_required
@require_POST
def reinitialiser_prix(request, id):
    """Réinitialise le prix d'un article à son prix unitaire par défaut"""
    article = get_object_or_404(Article, id=id)
    
    # Réinitialiser le prix actuel au prix unitaire
    article.prix_actuel = article.prix_unitaire
    # Remettre la phase en EN_COURS
    article.phase = 'EN_COURS'
    article.save()
    
    messages.success(request, f"Le prix de l'article '{article.nom}' a été réinitialisé avec succès.")
    
    # Rediriger vers la page précédente ou la page de détail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('article:detail', id=article.id)

@login_required
def gerer_promotions_automatiquement(request):
    """Gère automatiquement toutes les promotions selon leur date et statut"""
    now = timezone.now()
    
    # Statistiques
    stats = {
        'activated': 0,
        'deactivated': 0,
        'articles_updated': 0
    }
    
    # Récupérer toutes les promotions
    all_promotions = Promotion.objects.all()
    
    for promotion in all_promotions:
        result = promotion.verifier_et_appliquer_automatiquement()
        
        if result == "activated":
            stats['activated'] += 1
            stats['articles_updated'] += promotion.articles.count()
        elif result == "deactivated":
            stats['deactivated'] += 1
            stats['articles_updated'] += promotion.articles.count()
    
    # Messages de feedback
    messages_list = []
    if stats['activated'] > 0:
        messages_list.append(f"{stats['activated']} promotion(s) activée(s)")
    if stats['deactivated'] > 0:
        messages_list.append(f"{stats['deactivated']} promotion(s) désactivée(s)")
    if stats['articles_updated'] > 0:
        messages_list.append(f"{stats['articles_updated']} article(s) mis à jour")
    
    if messages_list:
        messages.success(request, "Gestion automatique terminée : " + " et ".join(messages_list) + ".")
    else:
        messages.info(request, "Aucune promotion à traiter automatiquement.")
    
    # Rediriger vers la liste des promotions
    return redirect('article:liste_promotions')


@login_required
def liste_variantes(request):
    """Liste des variantes d'articles avec recherche, filtres et pagination"""
    variantes_articles = VarianteArticle.objects.filter(actif=True).select_related(
        'article', 'couleur', 'pointure', 'article__categorie'
    ).order_by('article__nom')
    
    # Formulaire de promotion pour la modal
    form_promotion = PromotionForm()
    
    # Récupérer les paramètres de filtrage
    filtre_phase = request.GET.get('filtre_phase', 'tous')
    filtre_promotion = request.GET.get('filtre_promotion', '')
    filtre_stock = request.GET.get('filtre_stock', '')
    search = request.GET.get('search', '')
    
    # Filtrage par phase
    if filtre_phase and filtre_phase != 'tous':
        variantes_articles = variantes_articles.filter(article__phase=filtre_phase)
    
    # Filtrage par promotion
    now = timezone.now()
    if filtre_promotion == 'avec_promo':
        variantes_articles = variantes_articles.filter(
            article__promotions__active=True,
            article__promotions__date_debut__lte=now,
            article__promotions__date_fin__gte=now
        ).distinct()
    elif filtre_promotion == 'sans_promo':
        variantes_articles = variantes_articles.exclude(
            article__promotions__active=True,
            article__promotions__date_debut__lte=now,
            article__promotions__date_fin__gte=now
        ).distinct()
    
    # Filtrage par stock
    if filtre_stock == 'disponible':
        variantes_articles = variantes_articles.filter(qte_disponible__gt=0, actif=True).distinct()
    elif filtre_stock == 'rupture':
        variantes_articles = variantes_articles.filter(qte_disponible=0, actif=True).distinct()
    elif filtre_stock == 'stock_faible':
        variantes_articles = variantes_articles.filter(
            qte_disponible__gt=0, 
            qte_disponible__lt=5, 
            actif=True
        ).distinct()
    
    # Recherche unique sur plusieurs champs
    if search:
        # Essayer de convertir la recherche en nombre pour le prix
        try:
            # Si c'est un nombre, on cherche le prix exact ou dans une marge de ±10 DH
            search_price = float(search.replace(',', '.'))
            price_query = Q(article__prix_unitaire__gte=search_price-10) & Q(article__prix_unitaire__lte=search_price+10)
        except ValueError:
            price_query = Q()  # Query vide si ce n'est pas un prix

        # Vérifier si c'est une fourchette de prix (ex: 100-200)
        if '-' in search and all(part.strip().replace(',', '.').replace('.', '').isdigit() for part in search.split('-')):
            try:
                min_price, max_price = map(lambda x: float(x.strip().replace(',', '.')), search.split('-'))
                price_query = Q(article__prix_unitaire__gte=min_price) & Q(article__prix_unitaire__lte=max_price)
            except ValueError:
                pass

        variantes_articles = variantes_articles.filter(
            Q(article__reference__icontains=search) |    # Recherche par référence
            Q(article__nom__icontains=search) |          # Recherche par nom
            Q(couleur__nom__icontains=search) |          # Recherche par couleur
            Q(pointure__pointure__icontains=search) |    # Recherche par pointure
            Q(article__categorie__nom__icontains=search) | # Recherche par catégorie
            price_query                                   # Recherche par prix
        ).distinct()
    
    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 12)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des variantes non paginées pour les statistiques
    variantes_non_paginees = variantes_articles
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                variantes_articles = list(variantes_articles)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(variantes_articles, len(variantes_articles))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 12
            paginator = Paginator(variantes_articles, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher toutes les variantes
            paginator = Paginator(variantes_articles, variantes_articles.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 12
            except (ValueError, TypeError):
                items_per_page = 12
            
            paginator = Paginator(variantes_articles, items_per_page)
            page_obj = paginator.get_page(page_number)
    
    # Statistiques mises à jour selon les filtres appliqués
    all_variantes_articles = VarianteArticle.objects.filter(actif=True)
    stats = {
        'total_articles': all_variantes_articles.count(),
        'articles_disponibles': all_variantes_articles.filter(qte_disponible__gt=0, actif=True).distinct().count(),
        'articles_en_cours': all_variantes_articles.filter(article__phase='EN_COURS').count(),
        'articles_liquidation': all_variantes_articles.filter(article__phase='LIQUIDATION').count(),
        'articles_test': all_variantes_articles.filter(article__phase='EN_TEST').count(),
        'articles_promotion': all_variantes_articles.filter(
            article__promotions__active=True,
            article__promotions__date_debut__lte=now,
            article__promotions__date_fin__gte=now
        ).distinct().count(),
        'articles_rupture': all_variantes_articles.filter(qte_disponible=0, actif=True).distinct().count(),
        'articles_stock_faible': all_variantes_articles.filter(
            qte_disponible__gt=0, 
            qte_disponible__lt=5, 
            actif=True
        ).distinct().count(),
    }
    
    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        # Rendre les templates partiels pour AJAX
        html_cards_body = render_to_string('article/partials/variantes_articles_cards_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_table_body = render_to_string('article/partials/variantes_articles_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        # Vue grille pour variantes
        html_grid_body = render_to_string('article/partials/variantes_articles_grid_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('article/partials/_articles_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre_phase': filtre_phase,
            'filtre_promotion': filtre_promotion,
            'filtre_stock': filtre_stock,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('article/partials/_articles_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_cards_body': html_cards_body,
            'html_table_body': html_table_body,
            'html_grid_body': html_grid_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': variantes_non_paginees.count()
        })

    context = {
        'page_obj': page_obj,
        'search': search,
        'stats': stats,
        'form_promotion': form_promotion,
        'filtre_phase': filtre_phase,
        'filtre_promotion': filtre_promotion,
        'filtre_stock': filtre_stock,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }
    return render(request, 'article/Liste_variante_article.html', context)

@login_required
def creer_variantes_ajax(request):
    """Créer des variantes via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        import json
        data = json.loads(request.body)
        article_id = data.get('article_id')
        variantes_data = data.get('variantes', [])
        
        if not article_id:
            return JsonResponse({'success': False, 'error': 'ID de l\'article manquant'})
        
        # Récupérer l'article
        try:
            article = Article.objects.get(id=article_id, actif=True)
        except Article.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Article non trouvé'})
        
        variantes_crees = []
        erreurs = []
        
        for variante_data in variantes_data:
            couleur_id = variante_data.get('couleur_id')
            pointure_id = variante_data.get('pointure_id')
            quantite = variante_data.get('quantite', 0)
            reference = variante_data.get('reference', '')
            
            # Validation
            if not couleur_id and not pointure_id:
                erreurs.append('Au moins une couleur ou une pointure doit être spécifiée')
                continue
            
            # Vérifier l'unicité
            if VarianteArticle.objects.filter(
                article=article,
                couleur_id=couleur_id if couleur_id else None,
                pointure_id=pointure_id if pointure_id else None
            ).exists():
                erreurs.append('Cette combinaison couleur/pointure existe déjà')
                continue
            
            try:
                # Créer la variante
                variante = VarianteArticle()
                variante.article = article
                variante.couleur_id = couleur_id if couleur_id else None
                variante.pointure_id = pointure_id if pointure_id else None
                variante.qte_disponible = int(quantite) if quantite else 0
                
                # Définir la référence
                if reference:
                    variante.reference_variante = reference
                else:
                    # Générer automatiquement
                    variante.save()  # Sauvegarder d'abord pour avoir l'ID
                    variante.reference_variante = variante.generer_reference_variante_automatique()
                
                variante.save()
                
                # Préparer les données de réponse
                variante_info = {
                    'id': variante.id,
                    'couleur': variante.couleur.nom if variante.couleur else None,
                    'pointure': variante.pointure.pointure if variante.pointure else None,
                    'quantite': variante.qte_disponible,
                    'reference': variante.reference_variante
                }
                
                variantes_crees.append(variante_info)
                
            except Exception as e:
                erreurs.append(f'Erreur lors de la création: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'variantes_crees': variantes_crees,
            'nombre_crees': len(variantes_crees),
            'erreurs': erreurs
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur serveur: {str(e)}'})

@login_required
@csrf_exempt
def supprimer_variante(request, id):
    """Supprimer une variante d'article"""
    # Debug CSRF
    print(f"DEBUG CSRF - Token reçu: {request.POST.get('csrfmiddlewaretoken', 'AUCUN')}")
    print(f"DEBUG CSRF - Cookies: {request.COOKIES.get('csrftoken', 'AUCUN')}")
    
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
        messages.error(request, 'Méthode non autorisée')
        return redirect('article:liste')
    
    try:
        variante = VarianteArticle.objects.get(id=id)
        article = variante.article
        
        # Vérifier les permissions (optionnel)
        # Vous pouvez ajouter des vérifications de permissions ici
        
        variante_info = f"{variante.couleur.nom if variante.couleur else 'Aucune couleur'} / {variante.pointure.pointure if variante.pointure else 'Aucune pointure'}"
        variante.delete()
        
        # Si c'est une requête AJAX, retourner JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'Variante "{variante_info}" supprimée avec succès.',
                'variante_id': id
            }, content_type='application/json')
        
        # Sinon, rediriger normalement
        messages.success(request, f'Variante "{variante_info}" supprimée avec succès.')
        return redirect('article:liste_variantes', id=article.id)
        
    except VarianteArticle.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Variante non trouvée.'}, content_type='application/json')
        messages.error(request, 'Variante non trouvée.')
        return redirect('article:liste_variantes')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'Erreur lors de la suppression : {str(e)}'}, content_type='application/json')
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('article:liste_variantes')

@login_required
def gestion_couleurs_pointures(request):
    """Page de gestion des couleurs, pointures, catégories et genres"""
    from article.models import Couleur, Pointure, Categorie, Genre
    
    # Recherche pour les couleurs
    search_couleur = request.GET.get('search_couleur', '')
    couleurs = Couleur.objects.all()
    if search_couleur:
        couleurs = couleurs.filter(
            Q(nom__icontains=search_couleur) |
            Q(description__icontains=search_couleur) |
            Q(code_hex__icontains=search_couleur)
        )
    couleurs = list(couleurs.order_by('nom'))
    
    # Recherche pour les pointures
    search_pointure = request.GET.get('search_pointure', '')
    pointures = Pointure.objects.all()
    if search_pointure:
        pointures = pointures.filter(
            Q(pointure__icontains=search_pointure) |
            Q(description__icontains=search_pointure)
        )
    pointures = list(pointures.order_by('ordre', 'pointure'))
    
    # Recherche pour les catégories
    search_categorie = request.GET.get('search_categorie', '')
    categories = Categorie.objects.all()
    if search_categorie:
        categories = categories.filter(
            Q(nom__icontains=search_categorie) |
            Q(description__icontains=search_categorie)
        )
    categories = list(categories.order_by('nom'))
    
    # Recherche pour les genres
    search_genre = request.GET.get('search_genre', '')
    genres = Genre.objects.all()
    if search_genre:
        genres = genres.filter(
            Q(nom__icontains=search_genre) |
            Q(description__icontains=search_genre)
        )
    genres = list(genres.order_by('nom'))
    
    context = {
        'couleurs': couleurs,
        'pointures': pointures,
        'categories': categories,
        'genres': genres,
        'couleurs_count': len(couleurs),
        'pointures_count': len(pointures),
        'categories_count': len(categories),
        'genres_count': len(genres),
        'search_couleur': search_couleur,
        'search_pointure': search_pointure,
        'search_categorie': search_categorie,
        'search_genre': search_genre,
    }
    
    return render(request, 'article/gestion_couleurs_pointures.html', context)

@login_required
def creer_pointure(request):
    """Créer une nouvelle pointure"""
    if request.method == 'POST':
        try:
            pointure = request.POST.get('pointure')
            ordre = request.POST.get('ordre', 0)
            description = request.POST.get('description', '')
            actif = request.POST.get('actif') == 'on'
            
            # Créer la pointure
            Pointure.objects.create(
                pointure=pointure,
                ordre=ordre,
                description=description,
                actif=actif
            )
            
            messages.success(request, f'Pointure "{pointure}" créée avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def modifier_pointure(request, pointure_id):
    """Modifier une pointure existante"""
    if request.method == 'POST':
        try:
            pointure_obj = get_object_or_404(Pointure, id=pointure_id)
            
            pointure_obj.pointure = request.POST.get('pointure')
            pointure_obj.ordre = request.POST.get('ordre', 0)
            pointure_obj.description = request.POST.get('description', '')
            pointure_obj.actif = request.POST.get('actif') == 'on'
            
            pointure_obj.save()
            
            messages.success(request, f'Pointure "{pointure_obj.pointure}" modifiée avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def supprimer_pointure(request, pointure_id):
    """Supprimer une pointure"""
    try:
        pointure = get_object_or_404(Pointure, id=pointure_id)
        nom_pointure = pointure.pointure
        pointure.delete()
        
        messages.success(request, f'Pointure "{nom_pointure}" supprimée avec succès.')
        return redirect('article:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('article:gestion_couleurs_pointures')

@login_required
def creer_categorie(request):
    """Créer une nouvelle catégorie"""
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            description = request.POST.get('description', '')
            actif = request.POST.get('actif') == 'on'
            
            # Créer la catégorie
            Categorie.objects.create(
                nom=nom,
                description=description,
                actif=actif
            )
            
            messages.success(request, f'Catégorie "{nom}" créée avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def modifier_categorie(request, categorie_id):
    """Modifier une catégorie existante"""
    if request.method == 'POST':
        try:
            categorie_obj = get_object_or_404(Categorie, id=categorie_id)
            
            categorie_obj.nom = request.POST.get('nom')
            categorie_obj.description = request.POST.get('description', '')
            categorie_obj.actif = request.POST.get('actif') == 'on'
            
            categorie_obj.save()
            
            messages.success(request, f'Catégorie "{categorie_obj.nom}" modifiée avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def supprimer_categorie(request, categorie_id):
    """Supprimer une catégorie"""
    try:
        categorie = get_object_or_404(Categorie, id=categorie_id)
        nom_categorie = categorie.nom
        categorie.delete()
        
        messages.success(request, f'Catégorie "{nom_categorie}" supprimée avec succès.')
        return redirect('article:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('article:gestion_couleurs_pointures')

@login_required
def creer_genre(request):
    """Créer un nouveau genre"""
    if request.method == 'POST':
        try:
            nom = request.POST.get('nom')
            description = request.POST.get('description', '')
            actif = request.POST.get('actif') == 'on'
            
            # Créer le genre
            Genre.objects.create(
                nom=nom,
                description=description,
                actif=actif
            )
            
            messages.success(request, f'Genre "{nom}" créé avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def modifier_genre(request, genre_id):
    """Modifier un genre existant"""
    if request.method == 'POST':
        try:
            genre_obj = get_object_or_404(Genre, id=genre_id)
            
            genre_obj.nom = request.POST.get('nom')
            genre_obj.description = request.POST.get('description', '')
            genre_obj.actif = request.POST.get('actif') == 'on'
            
            genre_obj.save()
            
            messages.success(request, f'Genre "{genre_obj.nom}" modifié avec succès.')
            return redirect('article:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('article:gestion_couleurs_pointures')
    
    return redirect('article:gestion_couleurs_pointures')

@login_required
def supprimer_genre(request, genre_id):
    """Supprimer un genre"""
    try:
        genre = get_object_or_404(Genre, id=genre_id)
        nom_genre = genre.nom
        genre.delete()
        
        messages.success(request, f'Genre "{nom_genre}" supprimé avec succès.')
        return redirect('article:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('article:gestion_couleurs_pointures')
    

@login_required
@require_POST
def creer_couleur(request):
    """Créer une nouvelle couleur"""
    nom = request.POST.get('nom')
    code_hex = request.POST.get('code_hex', '').strip()
    description = request.POST.get('description', '').strip()
    actif = request.POST.get('actif') == 'on'
    
    if nom:
        if Couleur.objects.filter(nom__iexact=nom).exists():
            messages.error(request, f'Une couleur avec le nom "{nom}" existe déjà.')
        else:
            Couleur.objects.create(
                nom=nom,
                code_hex=code_hex if code_hex else None,
                description=description if description else None,
                actif=actif
            )
            messages.success(request, f'La couleur "{nom}" a été créée avec succès.')
    else:
        messages.error(request, 'Le nom de la couleur est requis.')
    
    return redirect('article:gestion_couleurs_pointures')


@login_required
@require_POST
def modifier_couleur(request, couleur_id):
    """Modifier une couleur existante"""
    couleur = get_object_or_404(Couleur, id=couleur_id)
    nom = request.POST.get('nom')
    code_hex = request.POST.get('code_hex', '').strip()
    description = request.POST.get('description', '').strip()
    actif = request.POST.get('actif') == 'on'
    
    if nom:
        if Couleur.objects.filter(nom__iexact=nom).exclude(id=couleur_id).exists():
            messages.error(request, f'Une couleur avec le nom "{nom}" existe déjà.')
        else:
            couleur.nom = nom
            couleur.code_hex = code_hex if code_hex else None
            couleur.description = description if description else None
            couleur.actif = actif
            couleur.save()
            messages.success(request, f'La couleur a été modifiée en "{nom}".')
    else:
        messages.error(request, 'Le nom de la couleur est requis.')
    
    return redirect('article:gestion_couleurs_pointures')


@login_required
@require_POST
def supprimer_couleur(request, couleur_id):
    """Supprimer une couleur"""
    couleur = get_object_or_404(Couleur, id=couleur_id)
    nom = couleur.nom
    
    # Vérifier si la couleur est utilisée dans des variantes d'articles
    variantes_utilisant_couleur = VarianteArticle.objects.filter(couleur=couleur).count()
    
    if variantes_utilisant_couleur > 0:
        messages.error(request, f'Impossible de supprimer la couleur "{nom}" car elle est utilisée dans {variantes_utilisant_couleur} variante(s) d\'article(s).')
    else:
        couleur.delete()
        messages.success(request, f'La couleur "{nom}" a été supprimée avec succès.')
    
    return redirect('article:gestion_couleurs_pointures')


