from django.shortcuts               import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib                 import messages
from django.db.models               import Q, Sum, Max, Count
from django.core.paginator          import Paginator
from django.http                    import JsonResponse
from django.views.decorators.http   import require_POST
from django.utils                   import timezone
from django.db                      import transaction
import json

from parametre.models import Operateur
from commande.models  import Commande, Envoi, EnumEtatCmd, EtatCommande, Operation
from article.models   import Article



def surveiller_affectations_anormales():
    # Fonctionnalité supprimée
    return []


def surveiller_livraisons_partielles():
    # Fonctionnalité supprimée
    return []

def corriger_livraisons_partielles():
    # Fonctionnalité supprimée
    return []


@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Statistiques simples pour le dashboard
    en_preparation    = Commande.objects.filter(etats__enum_etat__libelle='En préparation', etats__date_fin__isnull=True).distinct().count()
    prets_expedition  = Commande.objects.filter(etats__enum_etat__libelle='Préparée',        etats__date_fin__isnull=True).distinct().count()
    expedies          = Commande.objects.filter(etats__enum_etat__libelle='En cours de livraison', etats__date_fin__isnull=True).distinct().count()
    
    context = {
        'operateur'        : operateur,
        'en_preparation'   : en_preparation,
        'prets_expedition' : prets_expedition,
        'expedies'         : expedies,
        'page_title'       : 'Tableau de Bord Logistique',
    }
    return render(request, 'composant_generale/operatLogistic/home.html', context)


@login_required
def liste_commandes(request):
    """Liste des commandes affectées à cet opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes avec les relations nécessaires
    # Essayer plusieurs états possibles pour les commandes logistiques
    commandes_list = Commande.objects.filter(
        Q(etats__enum_etat__libelle='Mise en distribution'),
        etats__date_fin__isnull=True
    ).select_related(
        'client', 
        'ville', 
        'ville__region'
    ).prefetch_related(
        'etats__enum_etat',
        'etats__operateur'
    ).distinct().order_by('-etats__date_debut')
    
    # Gestion du filtre de temps
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    preset = request.GET.get('preset')
    
    # Appliquer le filtre de temps si des paramètres sont fournis
    if start_date and end_date:
        try:
            from datetime import datetime
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            # Filtrer par date de début des états "En livraison"
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__range=[start_datetime.date(), end_datetime.date()]
            )
            print(f"🔍 Filtre de temps appliqué: {start_date} à {end_date}")
        except ValueError:
            print("❌ Erreur de format de date dans les paramètres de filtre")
    elif preset:
        # Appliquer des presets prédéfinis
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        if preset == 'today':
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date=today
            )
        elif preset == 'yesterday':
            yesterday = today - timedelta(days=1)
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date=yesterday
            )
        elif preset == 'this_week':
            # Lundi de cette semaine
            monday = today - timedelta(days=today.weekday())
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise enn distribution'],
                etats__date_debut__date__gte=monday
            )
        elif preset == 'last_week':
            # Lundi de la semaine dernière
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__range=[last_monday, last_sunday]
            )
        elif preset == 'this_month':
            # Premier jour du mois
            first_day = today.replace(day=1)
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__gte=first_day
            )
        elif preset == 'last_month':
            # Premier jour du mois dernier
            if today.month == 1:
                first_day_last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                first_day_last_month = today.replace(month=today.month-1, day=1)
            # Dernier jour du mois dernier
            if today.month == 1:
                last_day_last_month = today.replace(year=today.year-1, month=12, day=31)
            else:
                last_day_last_month = (today.replace(month=today.month, day=1) - timedelta(days=1))
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__range=[first_day_last_month, last_day_last_month]
            )
        elif preset == 'this_year':
            # Premier jour de l'année
            first_day_year = today.replace(month=1, day=1)
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__gte=first_day_year
            )
        elif preset == 'last_year':
            # Premier et dernier jour de l'année dernière
            first_day_last_year = today.replace(year=today.year-1, month=1, day=1)
            last_day_last_year = today.replace(year=today.year-1, month=12, day=31)
            commandes_list = commandes_list.filter(
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
                etats__date_debut__date__range=[first_day_last_year, last_day_last_year]
            )
        
        print(f"🔍 Preset appliqué: {preset}")
    
    # Debug: afficher les commandes trouvées
    print(f"🔍 Debug: {commandes_list.count()} commandes trouvées pour l'opérateur {operateur.nom}")
    for cmd in commandes_list[:3]:  # Afficher les 3 premières pour debug
        print(f"  - Commande {cmd.id_yz}: Client={cmd.client}, Ville={cmd.ville}")
    
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_list = commandes_list.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Calculer les statistiques par période
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    # Commandes d'aujourd'hui
    affectees_aujourd_hui = Commande.objects.filter(
        Q(etats__enum_etat__libelle='En cours de livraison') |
        Q(etats__enum_etat__libelle='En livraison')|
        Q(etats__enum_etat__libelle='Mise en distribution'),
        etats__date_fin__isnull=True,
        etats__date_debut__date=today
    ).distinct().count()
    
    # Commandes de cette semaine
    monday = today - timedelta(days=today.weekday())
    affectees_semaine = Commande.objects.filter(
        Q(etats__enum_etat__libelle='En cours de livraison') |
        Q(etats__enum_etat__libelle='En livraison')|
        Q(etats__enum_etat__libelle='Mise en distribution'),
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=monday
    ).distinct().count()
    
    # Commandes de ce mois
    first_day = today.replace(day=1)
    affectees_mois = Commande.objects.filter(
        Q(etats__enum_etat__libelle='En cours de livraison') |
        Q(etats__enum_etat__libelle='En livraison')|
        Q(etats__enum_etat__libelle='Mise en distribution'),
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=first_day
    ).distinct().count()
    
    # Calculer le total des montants
    total_montant = sum(cmd.total_cmd or 0 for cmd in commandes_list)
    
    paginator   = Paginator(commandes_list, 20)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)
    
    context = {
        'page_obj'        : page_obj,
        'search_query'    : search_query,
        'total_commandes' : commandes_list.count(),
        'total_montant'   : total_montant,
        'page_title'      : 'Commandes en Livraison',
        'page_subtitle'   : f'Gestion des livraisons affectées à {operateur.prenom} {operateur.nom}',
        'affectees_aujourd_hui': affectees_aujourd_hui,
        'affectees_semaine': affectees_semaine,
        'affectees_mois': affectees_mois,
        # Paramètres de filtre pour le template
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_preset': preset,
    }
    return render(request, 'operatLogistic/liste_commande.html', context)


@login_required
def detail_commande(request, commande_id):
    """Détails d'une commande pour l'opérateur logistique."""
    commande = get_object_or_404(Commande, id=commande_id)
    
    # S'assurer que les totaux et les prix des articles sont à jour pour l'affichage
    # Calculer le prix de chaque article en fonction du compteur de la commande
    for panier in commande.paniers.all():
        prix_actuel = panier.article.prix_unitaire # Prix de base par défaut
        if commande.compteur > 0:
            if commande.compteur == 1 and panier.article.prix_upsell_1:
                prix_actuel = panier.article.prix_upsell_1
            elif commande.compteur == 2 and panier.article.prix_upsell_2:
                prix_actuel = panier.article.prix_upsell_2
            elif commande.compteur == 3 and panier.article.prix_upsell_3:
                prix_actuel = panier.article.prix_upsell_3
            elif commande.compteur >= 4 and panier.article.prix_upsell_4:
                prix_actuel = panier.article.prix_upsell_4
        panier.prix_actuel_pour_affichage = prix_actuel # Ajouter un attribut pour le template
        print(f"DEBUG: Article {panier.article.nom}, Prix affiché: {panier.prix_actuel_pour_affichage}")

    context = {
        'commande'   : commande,
        'page_title' : f'Détail Commande {commande.id_yz}',
    }
    return render(request, 'operatLogistic/detail_commande.html', context)


# Vues pour le profil
@login_required
def profile_logistique(request):
    """Afficher le profil de l'opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    context = {
        'operateur': operateur,
        'user': request.user,
    }
    return render(request, 'operatLogistic/profile.html', context)


@login_required
def modifier_profile_logistique(request):
    """Modifier le profil de l'opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        adresse = request.POST.get('adresse', '').strip()
        photo = request.FILES.get('photo')
        
        # Validation
        if not first_name or not last_name or not email:
            messages.error(request, "Le prénom, le nom et l'email sont obligatoires.")
            return render(request, 'operatLogistic/modifier_profile.html', {
                'operateur': operateur,
                'user': request.user,
            })
        
        try:
            # Mettre à jour les informations de l'utilisateur
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            # Mettre à jour les informations de l'opérateur
            operateur.prenom = first_name
            operateur.nom = last_name
            operateur.mail = email
            operateur.telephone = telephone if telephone else None
            operateur.adresse = adresse if adresse else None
            
            # Gérer la photo de profil
            if photo:
                operateur.photo = photo
            
            operateur.save()
            
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('operatLogistic:profile')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour du profil : {str(e)}")
            return redirect('operatLogistic:profile')
    
    context = {
        'operateur': operateur,
        'user': request.user,
    }
    return render(request, 'operatLogistic/modifier_profile.html', context)

@login_required
def parametre(request):
    return render(request, 'operatLogistic/parametre.html')


@login_required
def marquer_livree(request, commande_id):
    # Fonctionnalité à implémenter
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
@require_POST
def signaler_probleme(request, commande_id):
    """Afficher le formulaire pour signaler un problème avec une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    commande = get_object_or_404(Commande, id=commande_id)
    
    context = {
        'commande': commande,
        'page_title': 'Signaler un Problème',
        'page_subtitle': f'Commande {commande.id_yz}'
    }
    
    return render(request, 'operatLogistic/signaler_probleme.html', context)


@login_required
@require_POST
def changer_etat_sav(request, commande_id):
    """Changer l'état d'une commande pour le SAV (Reportée, Livrée, etc.)."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les données du formulaire
        print(f"DEBUG: POST data = {dict(request.POST)}")  # Debug
        nouvel_etat = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire', '').strip()
        date_report = request.POST.get('date_report')
        date_livraison = request.POST.get('date_livraison')
        print(f"DEBUG: nouvel_etat = '{nouvel_etat}', commentaire = '{commentaire}'")  # Debug
        
        if not nouvel_etat:
            return JsonResponse({'success': False, 'error': 'Nouvel état non spécifié.'})
        
        # Validation des états autorisés
        etats_autorises = ['Reportée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement', 'Retournée']
        if nouvel_etat not in etats_autorises:
            return JsonResponse({'success': False, 'error': 'État non autorisé.'})
        
        with transaction.atomic():
            # Terminer l'état actuel
            if commande.etat_actuel:
                commande.etat_actuel.terminer_etat(operateur)
            
            # Créer le nouvel état
            etat_enum, _ = EnumEtatCmd.objects.get_or_create(
                libelle=nouvel_etat,
                defaults={'ordre': 80, 'couleur': '#6B7280'}
            )
            
            # Commentaire spécifique selon l'état
            commentaire_final = commentaire
            if nouvel_etat == 'Reportée':
                if date_report:
                    commentaire_final = f"Reportée au {date_report}: {commentaire}"
                else:
                    commentaire_final = f"{commentaire}"
            elif nouvel_etat == 'Livrée':
                commentaire_final = f"{commentaire}"
            elif nouvel_etat == 'Livrée Partiellement':
                commentaire_final = f"{commentaire}"
            elif nouvel_etat == 'Livrée avec changement':
                commentaire_final = f"{commentaire}"
            elif nouvel_etat == 'Retournée':
                commentaire_final = f"{commentaire}"
            
            # Créer le nouvel état
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_enum,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_final
            )
            
            # Si marquée livrée et date fournie, l'enregistrer
            if nouvel_etat == 'Livrée' and date_livraison:
                try:
                    from datetime import datetime
                    try:
                        parsed = datetime.strptime(date_livraison, '%Y-%m-%d %H:%M')
                    except ValueError:
                        parsed = datetime.strptime(date_livraison, '%Y-%m-%d')
                    commande.Date_livraison = parsed
                    commande.save(update_fields=['Date_livraison'])
                except Exception:
                    pass
            
            return JsonResponse({
                'success': True,
                'message': f"État changé vers {nouvel_etat} avec succès",
                'nouvel_etat': nouvel_etat
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def rafraichir_articles(request, commande_id):
    """Rafraîchir la section des articles d'une commande."""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # S'assurer que les totaux sont à jour
        commande.recalculer_totaux_upsell()
        
        context = {
            'commande': commande
        }
        
        # Rendre le template partiel
        from django.template.loader import render_to_string
        html = render_to_string('operatLogistic/partials/_articles_section.html', context, request=request)
        
        # Données supplémentaires pour calcul côté frontend
        frais_livraison = float(commande.ville.frais_livraison or 0)
        inclure_frais = bool(getattr(commande, 'frais_livraison', False))
        total_commande_avec_frais = float(commande.total_cmd) + (frais_livraison if inclure_frais else 0.0)

        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
            'total_commande_avec_frais': total_commande_avec_frais,
            'frais_livraison': frais_livraison,
            'inclure_frais': inclure_frais,
            'articles_count': commande.paniers.count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def api_articles(request):
    """API pour récupérer les articles disponibles."""
    try:
        from article.models import Article
        from django.core.serializers import serialize
        import json
        
        # Récupérer tous les articles actifs
        articles = Article.objects.filter(actif=True).order_by('nom')
        
        # Sérialiser les articles avec les champs nécessaires
        articles_data = []
        for article in articles:
            # Calculer si l'article a une promo active
            has_promo_active = False
            if hasattr(article, 'promotions') and article.promotions.exists():
                has_promo_active = article.promotions.filter(active=True).exists()
                
                article_data = {
                    'id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'description': article.description,
                'prix_unitaire': float(article.prix_unitaire),
                'prix_actuel': float(article.prix_unitaire),  # Prix de base
                'qte_disponible': article.qte_disponible,
                'categorie': article.categorie if article.categorie else None,
                'couleur': article.couleur,
                'pointure': article.pointure,
                'phase': article.phase,
                'isUpsell': article.isUpsell,
                    'has_promo_active': has_promo_active,
                # Prix upsell si disponibles
                'prix_upsell_1': float(article.prix_upsell_1) if article.prix_upsell_1 else None,
                'prix_upsell_2': float(article.prix_upsell_2) if article.prix_upsell_2 else None,
                'prix_upsell_3': float(article.prix_upsell_3) if article.prix_upsell_3 else None,
                'prix_upsell_4': float(article.prix_upsell_4) if article.prix_upsell_4 else None,
            }
                articles_data.append(article_data)
        
        return JsonResponse({
            'success': True,
            'articles': articles_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def ajouter_article(request, commande_id):
    """Ajouter un article à une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        article_id = request.POST.get('article_id')
        variante_id = request.POST.get('variante_id')
        quantite = int(request.POST.get('quantite', 1))
        
        if not article_id:
            return JsonResponse({'success': False, 'error': 'ID de l\'article manquant.'})
        
        if not variante_id:
            return JsonResponse({'success': False, 'error': 'ID de la variante manquant.'})
        
        from article.models import Article, VarianteArticle
        from commande.models import Panier
        
        article = get_object_or_404(Article, id=article_id)
        variante = get_object_or_404(VarianteArticle, id=variante_id, article=article)
        
        # Vérifier que la variante est active
        if not variante.actif:
            return JsonResponse({
                'success': False, 
                'error': f'Variante {variante} désactivée.'
            })
        
        # Vérifier le stock si la commande est confirmée
        if commande.etat_actuel and commande.etat_actuel.enum_etat.libelle == 'Confirmée':
            if variante.qte_disponible < quantite:
                return JsonResponse({
                    'success': False, 
                    'error': f'Stock insuffisant. Disponible: {variante.qte_disponible}, Demandé: {quantite}'
                })
            
            # Décrémenter le stock de la variante
            variante.qte_disponible -= quantite
            variante.save()
        
        # Calculer le prix selon le compteur de la commande
        prix_unitaire = article.prix_unitaire
        if commande.compteur > 0:
            if commande.compteur == 1 and article.prix_upsell_1:
                prix_unitaire = article.prix_upsell_1
            elif commande.compteur == 2 and article.prix_upsell_2:
                prix_unitaire = article.prix_upsell_2
            elif commande.compteur == 3 and article.prix_upsell_3:
                prix_unitaire = article.prix_upsell_3
            elif commande.compteur >= 4 and article.prix_upsell_4:
                prix_unitaire = article.prix_upsell_4
        
        # Créer le panier avec la variante
        panier = Panier.objects.create(
            commande=commande,
            article=article,
            variante=variante,
            quantite=quantite,
            sous_total=float(prix_unitaire * quantite)
        )
            
            # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
            
        return JsonResponse({
            'success': True,
            'message': 'Article ajouté avec succès',
            'panier_id': panier.id,
            'total_commande': float(commande.total_cmd)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
@login_required
@require_POST
def modifier_quantite_article(request, commande_id):
    """Modifier la quantité d'un article dans une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        panier_id = request.POST.get('panier_id')
        nouvelle_quantite = int(request.POST.get('quantite', 1))
            
        if not panier_id:
                return JsonResponse({'success': False, 'error': 'ID du panier manquant.'})
        
        from commande.models import Panier
        
        panier = get_object_or_404(Panier, id=panier_id, commande=commande)
        ancienne_quantite = panier.quantite
        difference = nouvelle_quantite - ancienne_quantite
        
        # Vérifier le stock si la commande est confirmée
        if commande.etat_actuel and commande.etat_actuel.enum_etat.libelle == 'Confirmée':
            if panier.variante:
                # Gestion avec variante
                if not panier.variante.actif:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Variante {panier.variante} désactivée.'
                    })
                
                if difference > 0 and panier.variante.qte_disponible < difference:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Stock insuffisant. Disponible: {panier.variante.qte_disponible}, Demandé: {difference}'
                    })
                
                # Ajuster le stock de la variante
                panier.variante.qte_disponible -= difference
                panier.variante.save()
            else:
                # Cas sans variante (pour compatibilité avec les anciens paniers)
                return JsonResponse({
                    'success': False, 
                    'error': f'Article {panier.article.nom} sans variante définie. Impossible de gérer le stock.'
                })
        
        # Mettre à jour le panier
        panier.quantite = nouvelle_quantite
        panier.sous_total = float(panier.article.prix_unitaire * nouvelle_quantite)
        panier.save()
        
        # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Quantité modifiée avec succès',
            'total_commande': float(commande.total_cmd),
            'sous_total': float(panier.sous_total),
            'article_nom': panier.article.nom,
            'ancienne_quantite': ancienne_quantite
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
@login_required
@require_POST
def renvoyer_en_preparation(request, commande_id):
    # Fonctionnalité supprimée
    return JsonResponse({'success': False, 'error': 'Fonctionnalité supprimée'})


@login_required
@require_POST
def livraison_partielle(request, commande_id):
    """Gérer une livraison partielle avec sélection d'articles."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est bien en cours de livraison
        if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'Mise en distribution':
            return JsonResponse({
                'success': False, 
                'error': 'Cette commande n\'est pas en Mise en distribution. Seules les commandes en Mise en distribution peuvent être livrées partiellement.'
            })
        
        # Récupérer les données du formulaire
        import json
        articles_livres = json.loads(request.POST.get('articles_livres', '[]'))
        articles_renvoyes = json.loads(request.POST.get('articles_renvoyes', '[]'))
        commentaire = request.POST.get('commentaire', '').strip()
        
        # DEBUG: Afficher les valeurs reçues du frontend
        print("=== DEBUG RECEPTION LIVRAISON PARTIELLE ===")
        print(f"Articles livrés reçus (RAW): {articles_livres}")
        print(f"Articles renvoyés reçus (RAW): {articles_renvoyes}")
        for i, article in enumerate(articles_livres):
            print(f"Article livré {i+1}: ID: {article.get('article_id', 'N/A')}, Variante ID: {article.get('variante_id', 'N/A')}, Nom: {article.get('nom', 'N/A')}, Prix Unitaire: {article.get('prix_unitaire', 'N/A')}")
        for i, article in enumerate(articles_renvoyes):
            print(f"Article renvoyé {i+1}: ID: {article.get('article_id', 'N/A')}, Variante ID: {article.get('variante_id', 'N/A')}, Nom: {article.get('nom', 'N/A')}, Prix Unitaire: {article.get('prix_unitaire', 'N/A')}")
        print("=== FIN DEBUG RECEPTION ===")
        
        if not commentaire:
            return JsonResponse({'success': False, 'error': 'Un commentaire est obligatoire pour expliquer la livraison partielle.'})
        
        if not articles_livres:
            return JsonResponse({'success': False, 'error': 'Aucun article à livrer spécifié.'})

        with transaction.atomic():
            # === Réintégration du stock pour les articles renvoyés: déléguée à la préparation ===
            # Construire un récap détaillé côté backend (prix calculés selon compteur/upsell)
            recap_articles_renvoyes = []
            if articles_renvoyes:
                for article_data in articles_renvoyes:
                    article_id = article_data.get('id') or article_data.get('article_id')
                    variante_id = article_data.get('variante_id')
                    nom_article = None
                    quantite_raw = article_data.get('quantite', 0)
                    try:
                        quantite = int(quantite_raw) if quantite_raw else 0
                    except (ValueError, TypeError):
                        quantite = 0
                    if article_id and quantite > 0:
                        try:
                            from article.models import Article, VarianteArticle
                            article_obj = Article.objects.get(id=article_id)
                            nom_article = article_obj.nom
                            # Calcul prix upsell s'il y a lieu
                            prix_unitaire_calc = article_obj.prix_unitaire
                            if commande.compteur > 0 and getattr(article_obj, 'isUpsell', False):
                                if commande.compteur == 1 and article_obj.prix_upsell_1:
                                    prix_unitaire_calc = article_obj.prix_upsell_1
                                elif commande.compteur == 2 and article_obj.prix_upsell_2:
                                    prix_unitaire_calc = article_obj.prix_upsell_2
                                elif commande.compteur == 3 and article_obj.prix_upsell_3:
                                    prix_unitaire_calc = article_obj.prix_upsell_3
                                elif commande.compteur >= 4 and article_obj.prix_upsell_4:
                                    prix_unitaire_calc = article_obj.prix_upsell_4
                            # Enrichir le nom si variante fournie
                            if variante_id:
                                try:
                                    variante_obj = VarianteArticle.objects.get(id=variante_id, article=article_obj)
                                    details = []
                                    if getattr(variante_obj, 'couleur', None):
                                        details.append(str(variante_obj.couleur))
                                    if getattr(variante_obj, 'pointure', None):
                                        details.append(str(variante_obj.pointure))
                                    if getattr(variante_obj, 'taille', None):
                                        details.append(str(variante_obj.taille))
                                    if details:
                                        nom_article = f"{nom_article} - {' / '.join(details)}"
                                except Exception:
                                    pass
                        except Exception:
                            # En cas d'erreur, fallback sûr
                            article_obj = None
                            prix_unitaire_calc = 0.0
                            recap_articles_renvoyes.append({
                                'article_id': article_id,
                                'variante_id': variante_id,
                                'nom': nom_article or '',
                                'quantite': quantite,
                                'prix_unitaire': float(prix_unitaire_calc),
                                'prix_actuel': float(prix_unitaire_calc),
                                'is_upsell': bool(getattr(article_obj, 'isUpsell', False)),
                                'compteur': int(commande.compteur or 0)
                            })
            
            # 1. Terminer l'état "En cours de livraison" actuel
            etat_actuel = commande.etat_actuel
            etat_actuel.terminer_etat(operateur)
            
            # 2. Créer l'état "Livrée Partiellement"
            etat_livree_partiellement, _ = EnumEtatCmd.objects.get_or_create(
                libelle='Livrée Partiellement',
                defaults={'ordre': 70, 'couleur': '#3B82F6'}
            )
            
            # 3. Créer le nouvel état avec le commentaire
            commentaire_etat = f"Livraison partielle effectuée. {commentaire}"
                
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_livree_partiellement,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_etat
            )
            
            # 4. Ne plus créer de commande de renvoi: seulement mettre à jour la commande actuelle
            articles_renvoyes = []
            
            # 5. Mettre à jour les quantités des articles livrés dans la commande originale
            for article_data in articles_livres:
                panier = commande.paniers.filter(
                    id=article_data['panier_id']
                ).first()
                if panier:
                    if article_data['quantite'] > 0:
                        panier.quantite = article_data['quantite']
                        
                        # Appliquer le prix upsell selon le compteur de la commande
                        prix_unitaire = panier.article.prix_unitaire
                        if commande.compteur > 0 and panier.article.isUpsell:
                            if commande.compteur == 1 and panier.article.prix_upsell_1:
                                prix_unitaire = panier.article.prix_upsell_1
                            elif commande.compteur == 2 and panier.article.prix_upsell_2:
                                prix_unitaire = panier.article.prix_upsell_2
                            elif commande.compteur == 3 and panier.article.prix_upsell_3:
                                prix_unitaire = panier.article.prix_upsell_3
                            elif commande.compteur >= 4 and panier.article.prix_upsell_4:
                                prix_unitaire = panier.article.prix_upsell_4
                        
                        panier.sous_total = prix_unitaire * article_data['quantite']
                        panier.save()
                    else:
                        panier.delete()
            
            # 6. Recalculer le compteur upsell après livraison partielle
            from django.db.models import Sum
            total_quantite_upsell_restante = commande.paniers.filter(
                article__isUpsell=True
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            # Appliquer la formule : compteur = max(0, total_quantite_upsell - 1)
            ancien_compteur = commande.compteur
            if total_quantite_upsell_restante >= 2:
                commande.compteur = total_quantite_upsell_restante - 1
            else:
                commande.compteur = 0
                
            print(f"DEBUG LIVRAISON PARTIELLE: Compteur {ancien_compteur} → {commande.compteur}")
            print(f"DEBUG LIVRAISON PARTIELLE: Quantité upsell restante = {total_quantite_upsell_restante}")
            
            # Si le compteur a changé, recalculer les sous-totaux avec les nouveaux prix
            if ancien_compteur != commande.compteur:
                print("DEBUG: Recalcul des prix car compteur a changé")
                for panier in commande.paniers.all():
                    # Calculer le nouveau prix selon le compteur
                    prix_unitaire = panier.article.prix_unitaire
                    if commande.compteur > 0 and panier.article.isUpsell:
                        if commande.compteur == 1 and panier.article.prix_upsell_1:
                            prix_unitaire = panier.article.prix_upsell_1
                        elif commande.compteur == 2 and panier.article.prix_upsell_2:
                            prix_unitaire = panier.article.prix_upsell_2
                        elif commande.compteur == 3 and panier.article.prix_upsell_3:
                            prix_unitaire = panier.article.prix_upsell_3
                        elif commande.compteur >= 4 and panier.article.prix_upsell_4:
                            prix_unitaire = panier.article.prix_upsell_4
                    
                    # Mettre à jour le prix_actuel de l'article ET le sous-total du panier
                    ancien_prix_actuel = panier.article.prix_actuel
                    ancien_sous_total = panier.sous_total
                    
                    panier.article.prix_actuel = prix_unitaire
                    panier.article.save(update_fields=['prix_actuel'])
                    
                    panier.sous_total = prix_unitaire * panier.quantite
                    panier.save()
                    
                    print(f"DEBUG: Article {panier.article.nom}")
                    print(f"  - Prix actuel: {ancien_prix_actuel} → {prix_unitaire}")
                    print(f"  - Sous-total: {ancien_sous_total} → {panier.sous_total}")
            
            # 7. Recalculer le total de la commande originale
            total_commande = commande.paniers.aggregate(
                total=Sum('sous_total')
            )['total'] or 0
            commande.total_cmd = float(total_commande)
            commande.save()
            
            # 8. Construire les récapitulatifs pour l'opération (sans renvoi)
            articles_livres_json = []
            for article_data in articles_livres:
                article_id = article_data.get('article_id') or article_data.get('id')
                variante_id = article_data.get('variante_id')
                try:
                    from article.models import Article
                    article = Article.objects.get(id=article_id)
                    prix_unitaire = article.prix_unitaire
                    
                    # Appliquer les prix upsell seulement si l'article est éligible et le compteur > 0
                    if commande.compteur > 0 and article.isUpsell:
                        if commande.compteur == 1 and article.prix_upsell_1:
                            prix_unitaire = article.prix_upsell_1
                        elif commande.compteur == 2 and article.prix_upsell_2:
                            prix_unitaire = article.prix_upsell_2
                        elif commande.compteur == 3 and article.prix_upsell_3:
                            prix_unitaire = article.prix_upsell_3
                        elif commande.compteur >= 4 and article.prix_upsell_4:
                            prix_unitaire = article.prix_upsell_4
                except Exception:
                    prix_unitaire = 0.0
                payload_item = {
                    'article_id': article_id,
                    'quantite': article_data.get('quantite', 0),
                    'prix_unitaire': float(prix_unitaire)
                }
                if variante_id:
                    payload_item['variante_id'] = variante_id
                articles_livres_json.append(payload_item)

            operation_conclusion_data = {
                'commentaire': commentaire,
                'articles_livres_count': len(articles_livres_json),
                'articles_renvoyes_count': len(recap_articles_renvoyes),
                'articles_livres': articles_livres_json,
                'recap_articles_renvoyes': recap_articles_renvoyes
            }
            
            if recap_articles_renvoyes:
                messages.success(request, 
                    f"Livraison partielle effectuée avec succès. {len(articles_livres)} article(s) livré(s), {len(recap_articles_renvoyes)} article(s) renvoyé(s) en préparation.")
            else:
                messages.success(request, 
                    f"Livraison partielle effectuée avec succès. {len(articles_livres)} article(s) livré(s).")
            
            return JsonResponse({
                'success': True,
                'message': f'Livraison partielle effectuée avec succès',
                'articles_livres': len(articles_livres),
                'articles_renvoyes': len(recap_articles_renvoyes),
                'commande_renvoi_id': None,
                'commande_renvoi_num': None,
                'recap_articles_renvoyes': operation_conclusion_data['recap_articles_renvoyes'],
                'recap_stock_commande': [],
                'compteur_change': {
                    'ancien_compteur': ancien_compteur,
                    'nouveau_compteur': commande.compteur,
                    'total_quantite_upsell_restante': total_quantite_upsell_restante
                }
            })
                
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer les données du panier d'une commande."""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les paniers avec les articles
        paniers = commande.paniers.select_related('article').all()
        
        # Préparer les données du panier avec calcul de prix upsell
        paniers_data = []
        for panier in paniers:
            # Calculer le prix en fonction du compteur et de l'upsell (même logique que detail_commande)
            prix_actuel = panier.article.prix_unitaire  # Prix de base par défaut
            
            if commande.compteur > 0 and panier.article.isUpsell:
                if commande.compteur == 1 and panier.article.prix_upsell_1:
                    prix_actuel = panier.article.prix_upsell_1
                elif commande.compteur == 2 and panier.article.prix_upsell_2:
                    prix_actuel = panier.article.prix_upsell_2
                elif commande.compteur == 3 and panier.article.prix_upsell_3:
                    prix_actuel = panier.article.prix_upsell_3
                elif commande.compteur >= 4 and panier.article.prix_upsell_4:
                    prix_actuel = panier.article.prix_upsell_4
            
            paniers_data.append({
                'id': panier.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'quantite': panier.quantite,
                'prix_unitaire': f"{panier.article.prix_unitaire:.2f}",
                'prix_actuel': f"{prix_actuel:.2f}",
                'sous_total': f"{panier.sous_total:.2f}",
                'pointure': panier.article.pointure,
                'couleur': panier.article.couleur,
                'article_id': panier.article.id,
                'is_upsell': panier.article.isUpsell,
                'compteur': commande.compteur,
            })
        
        # Préparer les données de la commande
        commande_data = {
            'id': commande.id,
            'id_yz': commande.id_yz,
            'num_cmd': commande.num_cmd,
            'total_cmd': f"{commande.total_cmd:.2f}",
            'date_cmd': commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else None,
            'etat_actuel': commande.etat_actuel.enum_etat.libelle if commande.etat_actuel else None,
        }
        
        return JsonResponse({
            'success': True,
            'commande': commande_data,
            'paniers': paniers_data,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


