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


def corriger_affectation_commandes_renvoyees():
    """
    Fonction utilitaire pour corriger automatiquement l'affectation des commandes renvoyées.
    À appeler périodiquement ou lors de problèmes d'affectation.
    """
    try:
        # Trouver toutes les commandes renvoyées en préparation
        commandes_renvoyees = Commande.objects.filter(
            etats__enum_etat__libelle='En préparation',
            etats__date_fin__isnull=True
        ).distinct()
        
        corrections_effectuees = 0
        
        for commande in commandes_renvoyees:
            # Trouver l'état actuel
            etat_actuel = commande.etats.filter(
                enum_etat__libelle='En préparation', 
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                continue
                
            # Chercher l'opérateur original qui avait préparé
            etat_preparee_original = commande.etats.filter(
                enum_etat__libelle='Préparée',
                date_fin__isnull=False
            ).order_by('-date_fin').first()
            
            operateur_cible = None
            
            if etat_preparee_original and etat_preparee_original.operateur:
                if (etat_preparee_original.operateur.type_operateur == 'PREPARATION' and 
                    etat_preparee_original.operateur.actif):
                    operateur_cible = etat_preparee_original.operateur
            
            # Si pas d'opérateur original, prendre le moins chargé
            if not operateur_cible:
                operateurs_preparation = Operateur.objects.filter(
                    type_operateur='PREPARATION',
                    actif=True
                ).order_by('id')
                
                if operateurs_preparation.exists():
                    from django.db.models import Count, Q
                    operateur_cible = operateurs_preparation.annotate(
                        commandes_en_cours=Count('etats_modifies', filter=Q(
                            etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                            etats_modifies__date_fin__isnull=True
                        ))
                    ).order_by('commandes_en_cours', 'id').first()
            
            # Corriger l'affectation si nécessaire
            if operateur_cible and etat_actuel.operateur != operateur_cible:
                ancien_operateur = etat_actuel.operateur
                etat_actuel.operateur = operateur_cible
                etat_actuel.save()
                corrections_effectuees += 1
                print(f"✅ Correction: Commande {commande.id_yz} réaffectée de {ancien_operateur} vers {operateur_cible.nom_complet}")
        
        return corrections_effectuees
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction des affectations: {e}")
        return 0


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
                etats__enum_etat__libelle__in=['En cours de livraison', 'En livraison','Mise en distribution'],
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
    
    # Gestion de la pagination avec sélecteur
    per_page = request.GET.get('per_page', '20')
    try:
        per_page = int(per_page)
        if per_page not in [5, 10, 15, 20, 25, 30, 40, 50]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator   = Paginator(commandes_list, per_page)
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
        'per_page'        : per_page,
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
        nouvel_etat = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire', '').strip()
        date_report = request.POST.get('date_report')
        date_livraison = request.POST.get('date_livraison')
        print(f"DEBUG: nouvel_etat = '{nouvel_etat}', commentaire = '{commentaire}'")  # Debug
        
        if not nouvel_etat:
            return JsonResponse({'success': False, 'error': 'Nouvel état non spécifié.'})
        
        # Validation des états autorisés
        etats_autorises = ['Reportée', 'Livrée', 'Livrée avec changement', 'Retournée']
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
            
            messages.success(request, f"État de la commande changé vers '{nouvel_etat}' avec succès.")
            
            return JsonResponse({
                'success': True,
                'message': f"État changé vers {nouvel_etat} avec succès",
                'nouvel_etat': nouvel_etat
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def creer_envoi(request, commande_id):
    """Créer un envoi pour une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        with transaction.atomic():
            # Vérifier si un envoi existe déjà
            if commande.envois.exists():
                return JsonResponse({'success': False, 'error': 'Un envoi existe déjà pour cette commande.'})
            
            # Créer l'envoi
            envoi = Envoi.objects.create(
                commande=commande,
                date_livraison_prevue=timezone.now().date(),
                operateur_creation=operateur,
                status='en_preparation'
            )
            
            # Générer un numéro d'envoi unique
            envoi.numero_envoi = f"ENV-{commande.id_yz}-{envoi.id:04d}"
            envoi.save()
            
            # Mettre à jour l'état de la commande si nécessaire
            if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'En cours de livraison':
                # Fermer l'état actuel
                if commande.etat_actuel:
                    commande.etat_actuel.date_fin = timezone.now()
                    commande.etat_actuel.save()
                
                # Créer l'état "En cours de livraison"
                etat_enum, _ = EnumEtatCmd.objects.get_or_create(
                    libelle='En cours de livraison',
                    defaults={'ordre': 60, 'couleur': '#3B82F6'}
                )
                
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_enum,
                    operateur=operateur,
                    date_debut=timezone.now(),
                    commentaire=f"Envoi créé: {envoi.numero_envoi}"
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Envoi {envoi.numero_envoi} créé avec succès',
                'numero_envoi': envoi.numero_envoi
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
        
        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
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
def creer_commande_sav(request, commande_id):
    """Créer une nouvelle commande SAV pour les articles défectueux retournés."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande_originale = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est dans un état qui permet la création d'une commande SAV
        etats_sav_autorises = ['Retournée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement']
        if not commande_originale.etat_actuel or commande_originale.etat_actuel.enum_etat.libelle not in etats_sav_autorises:
            return JsonResponse({
                'success': False, 
                'error': f'Cette commande ne peut pas avoir de SAV. État actuel: {commande_originale.etat_actuel.enum_etat.libelle if commande_originale.etat_actuel else "Aucun"}'
            })
        
        # Récupérer les articles défectueux depuis la requête POST
        import json
        articles_defectueux = json.loads(request.POST.get('articles_defectueux', '[]'))
        commentaire = request.POST.get('commentaire', '')
        
        if not articles_defectueux:
            return JsonResponse({'success': False, 'error': 'Aucun article défectueux spécifié.'})
        
        with transaction.atomic():
            # Générer un ID YZ unique pour la commande SAV
            last_id_yz = Commande.objects.aggregate(
                max_id=Max('id_yz')
            )['max_id']
            new_id_yz = (last_id_yz or 0) + 1
            
            # Créer une nouvelle commande SAV
            nouvelle_commande = Commande.objects.create(
                client=commande_originale.client,
                ville=commande_originale.ville,
                adresse=commande_originale.adresse,
                total_cmd=0,  # Sera recalculé
                num_cmd=f"SAV-{commande_originale.num_cmd}",
                id_yz=new_id_yz,
                is_upsell=False,
                compteur=0
            )
            
            total = 0
            # Créer les paniers pour les articles défectueux
            for article_data in articles_defectueux:
                article_id = article_data['article_id']
                quantite = int(article_data['quantite'])
                
                # Récupérer l'article original
                panier_original = commande_originale.paniers.filter(
                    article_id=article_id
                ).first()
                
                if panier_original:
                    from commande.models import Panier
                    Panier.objects.create(
                        commande=nouvelle_commande,
                        article=panier_original.article,
                    quantite=quantite,
                        sous_total=panier_original.article.prix_unitaire * quantite
                    )
                    total += panier_original.article.prix_unitaire * quantite
            
            # Mettre à jour le total de la commande
            nouvelle_commande.total_cmd = total
            nouvelle_commande.save()
            
            # Créer l'état initial "Non affectée"
            enum_etat = EnumEtatCmd.objects.get(libelle='Non affectée')
            EtatCommande.objects.create(
                commande=nouvelle_commande,
                enum_etat=enum_etat,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"Commande SAV créée pour articles défectueux de {commande_originale.id_yz}. {commentaire}"
            )
            
            messages.success(request, 
                f"Commande SAV {nouvelle_commande.id_yz} créée avec succès pour {len(articles_defectueux)} article(s) défectueux.")
            
            return JsonResponse({
                'success': True,
                'message': f'Commande SAV {nouvelle_commande.id_yz} créée avec succès',
                'commande_sav_id': nouvelle_commande.id,
                'commande_sav_num': nouvelle_commande.id_yz,
                'total': float(total)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
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
    """Renvoie une commande aux opérateurs de préparation pour modification du panier."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        commentaire = request.POST.get('commentaire', '').strip()
        
        if not commentaire:
            return JsonResponse({'success': False, 'error': 'Un commentaire est obligatoire pour expliquer le renvoi.'})
        
        # Vérifier que la commande est bien en cours de livraison
        if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'En cours de livraison':
            return JsonResponse({
                'success': False, 
                'error': 'Cette commande n\'est pas en cours de livraison. Seules les commandes en cours de livraison peuvent être renvoyées en préparation.'
            })
        
        with transaction.atomic():
            # 0. Corriger automatiquement les affectations existantes si nécessaire
            corrections = corriger_affectation_commandes_renvoyees()
            if corrections > 0:
                print(f"🔧 {corrections} affectations corrigées automatiquement")
            
            # 0.1. Surveiller les anomalies avant le renvoi
            anomalies = surveiller_affectations_anormales()
            if anomalies:
                print(f"⚠️  {len(anomalies)} anomalies détectées avant renvoi:")
                for anomaly in anomalies[:3]:  # Afficher les 3 premières
                    print(f"   - {anomaly['message']}")
            
            # 1. Terminer l'état "En cours de livraison" actuel
            etat_actuel = commande.etat_actuel
            etat_actuel.terminer_etat(operateur)
            
            # 2. Créer ou récupérer l'état "En préparation"
            etat_en_preparation, _ = EnumEtatCmd.objects.get_or_create(
                libelle='En préparation',
                defaults={'ordre': 30, 'couleur': '#3B82F6'}
            )
            
            # 3. Identifier et réaffecter à l'opérateur de préparation original
            # Chercher l'opérateur qui avait préparé cette commande initialement
            operateur_preparation_original = None
            
            # Chercher dans l'historique des états "En préparation" précédents de cette commande
            etat_preparation_precedent = commande.etats.filter(
                enum_etat__libelle='En préparation',
                date_fin__isnull=False  # État terminé
            ).order_by('-date_fin').first()
            
            if etat_preparation_precedent and etat_preparation_precedent.operateur:
                # Vérifier que cet opérateur est toujours actif et de type préparation
                if (etat_preparation_precedent.operateur.type_operateur == 'PREPARATION' and 
                    etat_preparation_precedent.operateur.actif):
                    operateur_preparation_original = etat_preparation_precedent.operateur
                    print(f"✅ Opérateur original trouvé: {operateur_preparation_original.nom_complet}")
                else:
                    print(f"⚠️  Opérateur original trouvé mais non disponible: {etat_preparation_precedent.operateur.nom_complet} (type: {etat_preparation_precedent.operateur.type_operateur}, actif: {etat_preparation_precedent.operateur.actif})")
            else:
                print("⚠️  Aucun état 'En préparation' précédent trouvé dans l'historique de la commande")
                
                # Fallback : chercher l'état "À imprimer" précédent
                etat_imprimer_precedent = commande.etats.filter(
                    enum_etat__libelle='À imprimer',
                    date_fin__isnull=False  # État terminé
                ).order_by('-date_fin').first()
                
                if etat_imprimer_precedent and etat_imprimer_precedent.operateur:
                    if (etat_imprimer_precedent.operateur.type_operateur == 'PREPARATION' and 
                        etat_imprimer_precedent.operateur.actif):
                        operateur_preparation_original = etat_imprimer_precedent.operateur
                        print(f"✅ Opérateur original trouvé (via 'À imprimer'): {operateur_preparation_original.nom_complet}")
                    else:
                        print(f"⚠️  Opérateur 'À imprimer' trouvé mais non disponible: {etat_imprimer_precedent.operateur.nom_complet}")
                else:
                    print("⚠️  Aucun état 'À imprimer' précédent trouvé non plus")
            
            # Si pas d'opérateur original trouvé ou plus actif, prendre le moins chargé
            if not operateur_preparation_original:
                operateurs_preparation = Operateur.objects.filter(
                    type_operateur='PREPARATION',
                    actif=True
                ).order_by('id')
                
                if operateurs_preparation.exists():
                    from django.db.models import Count, Q
                    
                    # Annoter chaque opérateur avec le nombre de commandes en cours
                    operateurs_charges = operateurs_preparation.annotate(
                        commandes_en_cours=Count('etats_modifies', filter=Q(
                            etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                            etats_modifies__date_fin__isnull=True
                        ))
                    ).order_by('commandes_en_cours', 'id')
                    
                    # L'opérateur le moins chargé est le premier de la liste
                    operateur_preparation_original = operateurs_charges.first()
                    print(f"✅ Affectation au moins chargé: {operateur_preparation_original.nom_complet} ({operateur_preparation_original.commandes_en_cours} commandes en cours)")
                else:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Aucun opérateur de préparation disponible. Impossible de renvoyer la commande.'
                    })
            
            # Vérification finale de sécurité
            if not operateur_preparation_original:
                return JsonResponse({
                    'success': False, 
                    'error': 'Impossible de déterminer un opérateur de préparation pour cette commande.'
                })
            
            # Validation de l'affectation
            is_valid, validation_message = valider_affectation_commande(commande, operateur_preparation_original)
            if not is_valid:
                return JsonResponse({
                    'success': False, 
                    'error': f'Affectation invalide: {validation_message}'
                })
            
            print(f"✅ {validation_message}")
            
            # Créer le nouvel état "En préparation" avec l'opérateur affecté
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_preparation,
                operateur=operateur_preparation_original,
                date_debut=timezone.now(),
                commentaire=f"Commande renvoyée en préparation pour modification du panier client. Demande client: {commentaire}"
            )
            
            # 4. Créer une opération pour tracer l'action
            Operation.objects.create(
                commande=commande,
                type_operation='RENVOI_PREPARATION',
                conclusion=f"Commande renvoyée aux opérateurs de préparation suite à demande de modification client: {commentaire}",
                operateur=operateur
            )
            
            messages.success(request, 
                f"Commande {commande.id_yz} renvoyée avec succès aux opérateurs de préparation pour modification du panier client.")
            
            return JsonResponse({
                'success': True,
                'message': f'Commande {commande.id_yz} renvoyée aux opérateurs de préparation. Ils effectueront les modifications demandées par le client.',
                'nouvel_etat': 'En préparation',
                'commande_id': commande.id
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def commandes_renvoyees_preparation(request):
    """Affiche les commandes que cet opérateur logistique a renvoyées en préparation."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes que cet opérateur a renvoyées en préparation
    # On cherche les commandes qui ont un état "En préparation" actif
    commandes_renvoyees = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True  # État actif
    ).select_related(
        'client', 
        'ville', 
        'ville__region'
    ).prefetch_related(
        'etats__enum_etat',
        'etats__operateur'
    ).distinct()
    
    # Filtrer pour ne garder que celles qui ont été renvoyées par cet opérateur logistique
    commandes_filtrees = []
    for commande in commandes_renvoyees:
        # Récupérer tous les états de la commande dans l'ordre chronologique
        etats_commande = commande.etats.all().order_by('date_debut')
        
        # Trouver l'état "En préparation" actuel
        etat_preparation_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == 'En préparation' and not etat.date_fin:
                etat_preparation_actuel = etat
                break
        
        if etat_preparation_actuel:
            # Trouver l'état précédent (le dernier état terminé avant l'état "En préparation" actuel)
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_preparation_actuel.date_debut:
                    if etat.enum_etat.libelle != 'En préparation':
                        etat_precedent = etat
                        break
            
            # Si l'état précédent était "En cours de livraison", c'est un renvoi depuis la logistique
            if etat_precedent and etat_precedent.enum_etat.libelle == 'En cours de livraison':
                # Vérifier que cet opérateur logistique était impliqué
                # Soit comme opérateur de l'état précédent, soit comme opérateur qui a créé l'envoi
                if (etat_precedent.operateur == operateur or 
                    commande.envois.filter(operateur_creation=operateur).exists()):
                    commande.etat_precedent = etat_precedent
                    commande.date_renvoi = etat_preparation_actuel.date_debut
                    commandes_filtrees.append(commande)
            
            # Alternative : chercher dans les opérations de traçabilité
            # Si une commande a une opération de renvoi en préparation par cet opérateur
            from commande.models import Operation
            operation_renvoi = Operation.objects.filter(
                commande=commande,
                type_operation='RENVOI_PREPARATION',
                operateur=operateur
            ).first()
            
            if operation_renvoi:
                commande.etat_precedent = etat_precedent
                commande.date_renvoi = operation_renvoi.date_operation
                if commande not in commandes_filtrees:
                    commandes_filtrees.append(commande)
            
            # 4. Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
            # Chercher les commandes de renvoi créées par cet opérateur lors d'une livraison partielle
            if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
                # Chercher l'opération de livraison partielle qui a créé cette commande de renvoi
                operation_livraison_partielle = Operation.objects.filter(
                    type_operation='LIVRAISON_PARTIELLE',
                    operateur=operateur,
                    conclusion__icontains=commande.num_cmd.replace('RENVOI-', '')
                ).first()
                
                if operation_livraison_partielle:
                    commande.etat_precedent = None  # Pas d'état précédent pour les commandes de renvoi
                    commande.date_renvoi = etat_preparation_actuel.date_debut
                    commande.type_renvoi = 'livraison_partielle'
                if commande not in commandes_filtrees:
                    commandes_filtrees.append(commande)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_filtrees = [cmd for cmd in commandes_filtrees if 
            search_query.lower() in str(cmd.id_yz).lower() or
            search_query.lower() in (cmd.num_cmd or '').lower() or
            search_query.lower() in cmd.client.nom.lower() or
            search_query.lower() in cmd.client.prenom.lower() or
            search_query.lower() in (cmd.client.numero_tel or '').lower()
        ]
    
    # S'assurer que toutes les commandes ont une date_renvoi définie
    for commande in commandes_filtrees:
        if not hasattr(commande, 'date_renvoi') or commande.date_renvoi is None:
            # Utiliser la date de l'état "En préparation" actuel comme fallback
            etat_preparation = commande.etats.filter(
                enum_etat__libelle='En préparation',
                date_fin__isnull=True
            ).first()
            commande.date_renvoi = etat_preparation.date_debut if etat_preparation else timezone.now()
    
    # Tri par date de renvoi (plus récentes en premier)
    commandes_filtrees.sort(key=lambda x: x.date_renvoi, reverse=True)
    
    # Pagination
    paginator = Paginator(commandes_filtrees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_renvoyees = len(commandes_filtrees)
    valeur_totale = sum(cmd.total_cmd or 0 for cmd in commandes_filtrees)
    
    # Commandes renvoyées aujourd'hui
    aujourd_hui = timezone.now().date()
    renvoyees_aujourd_hui = sum(1 for cmd in commandes_filtrees if hasattr(cmd, 'date_renvoi') and cmd.date_renvoi and cmd.date_renvoi.date() == aujourd_hui)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_renvoyees': total_renvoyees,
        'valeur_totale': valeur_totale,
        'renvoyees_aujourd_hui': renvoyees_aujourd_hui,
        'page_title': 'Commandes Renvoyées en Préparation',
        'page_subtitle': f'Commandes que vous avez renvoyées aux opérateurs de préparation',
        'operateur': operateur,
    }
    return render(request, 'operatLogistic/commandes_renvoyees_preparation.html', context)


@login_required
@require_POST
def supprimer_article(request, commande_id):
    """Supprimer un article d'une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        panier_id = request.POST.get('panier_id')
        
        if not panier_id:
            return JsonResponse({'success': False, 'error': 'ID du panier manquant.'})
        
        from commande.models import Panier
        
        panier = get_object_or_404(Panier, id=panier_id, commande=commande)
        quantite_supprimee = panier.quantite
        
        # Note: La réincrémentation du stock est maintenant gérée par les opérateurs de préparation
                        
        # Supprimer le panier
        panier.delete()
                
                # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
                )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
            
        return JsonResponse({
                'success': True,
            'message': 'Article supprimé avec succès',
            'total_commande': float(commande.total_cmd)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
        
        # Récupérer les chaînes JSON brutes pour diagnostiquer
        articles_livres_raw = request.POST.get('articles_livres', '[]')
        articles_renvoyes_raw = request.POST.get('articles_renvoyes', '[]')
        commentaire = request.POST.get('commentaire', '').strip()
        type_retour = request.POST.get('type_retour', 'preparation').strip()
        
        print(f"🔧 DEBUG JSON: articles_livres_raw = '{articles_livres_raw}'")
        print(f"🔧 DEBUG JSON: articles_renvoyes_raw = '{articles_renvoyes_raw}'")
        
        # Parser avec gestion d'erreur
        try:
            articles_livres = json.loads(articles_livres_raw) if articles_livres_raw.strip() else []
        except json.JSONDecodeError as e:
            print(f"❌ ERREUR JSON articles_livres: {e}")
            return JsonResponse({'success': False, 'error': f'Erreur JSON articles_livres: {str(e)}'})
        
        try:
            articles_renvoyes = json.loads(articles_renvoyes_raw) if articles_renvoyes_raw.strip() else []
        except json.JSONDecodeError as e:
            print(f"❌ ERREUR JSON articles_renvoyes: {e}")
            return JsonResponse({'success': False, 'error': f'Erreur JSON articles_renvoyes: {str(e)}'})
        
        # DEBUG: Afficher les valeurs reçues du frontend
        print("=== DEBUG RECEPTION LIVRAISON PARTIELLE ===")
        print(f"Articles livrés reçus (RAW): {articles_livres}")
        print(f"Articles retournés reçus (RAW): {articles_renvoyes}")
        for i, article in enumerate(articles_livres):
            print(f"Article livré {i+1}: ID: {article.get('article_id', 'N/A')}, Nom: {article.get('article_nom', 'N/A')}, Prix: {article.get('data-article-prix', 'N/A')}, Prix Unitaire: {article.get('prix_unitaire', 'N/A')}") # Utilise data-article-prix ici
        for i, article in enumerate(articles_renvoyes):
            print(f"Article retourné {i+1}: ID: {article.get('article_id', 'N/A')}, Variante ID: {article.get('variante_id', 'N/A')}, Nom: {article.get('nom', 'N/A')}, Prix Unitaire: {article.get('prix_unitaire', 'N/A')}")
        print("=== FIN DEBUG RECEPTION ===")
        
        if not commentaire:
            return JsonResponse({'success': False, 'error': 'Un commentaire est obligatoire pour expliquer la livraison partielle.'})
        
        if not articles_livres:
            return JsonResponse({'success': False, 'error': 'Aucun article à livrer spécifié.'})

        with transaction.atomic():
            # === AJOUT : Réintégration dans le stock pour les articles renvoyés en bon état ===
            print(f"🔄 [DEBUG] Début de la réintégration du stock - {len(articles_renvoyes)} articles à traiter")
            recap_articles_renvoyes = []
            
            if articles_renvoyes:  # Seulement si il y a des articles à renvoyer
                for i, article_data in enumerate(articles_renvoyes):
                    print(f"🔍 [DEBUG] Article renvoyé {i+1}: Données complètes = {article_data}")
                    
                    etat = article_data.get('etat', 'bon')
                    article_id = article_data.get('id') or article_data.get('article_id')
                    quantite_raw = article_data.get('quantite', 0)
                    
                    print(f"📊 [DEBUG] Article {i+1} - État: {etat}, ID: {article_id}, Quantité brute: {quantite_raw}")
                    
                    try:
                        quantite = int(quantite_raw) if quantite_raw else 0
                        print(f"🔢 [DEBUG] Article {i+1} - Quantité convertie: {quantite}")
                    except (ValueError, TypeError) as e:
                        print(f"❌ [DEBUG] Erreur conversion quantité pour article {i+1}: {e}")
                        quantite = 0
                    
                    if article_id and quantite > 0:
                        # Note: La réincrémentation du stock est maintenant gérée par les opérateurs de préparation
                        recap_articles_renvoyes.append({
                            'nom': article_data.get('nom', f'Article ID {article_id}'),
                            'quantite': quantite,
                            'etat': etat,
                            'message': f'Article renvoyé en préparation - Quantité: {quantite}'
                        })
                    else:
                        recap_articles_renvoyes.append({
                            'nom': article_data.get('nom', f'Article ID {article_id}'),
                            'quantite': quantite,
                            'etat': etat,
                            'message': 'Article ou quantité invalide'
                        })
            else:
                print(f"✅ Aucun article à renvoyer")
            
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
            if type_retour == 'definitif':
                commentaire_etat += f" Type de retour: Retour définitif client."
            else:
                commentaire_etat += f" Type de retour: Renvoi en préparation."
                
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_livree_partiellement,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_etat
            )
            
            # 4. NOUVELLE LOGIQUE: Stocker les articles retournés en base de données
            from commande.models import ArticleRetourne
            articles_retournes_crees = []
            
            # Traiter les articles livrés et créer les retours pour les quantités non livrées
            paniers_traites = set()  # Éviter le double traitement
            
            for article_data in articles_livres:
                panier_id = article_data['panier_id']
                panier = commande.paniers.filter(id=panier_id).first()
                
                if panier and panier_id not in paniers_traites:
                    paniers_traites.add(panier_id)
                    
                    quantite_originale = panier.quantite
                    quantite_livree = max(0, int(article_data['quantite']))  # S'assurer que c'est positif
                    quantite_retournee = quantite_originale - quantite_livree
                    
                    print(f"DEBUG QUANTITÉS: Panier {panier.id} - Original: {quantite_originale}, Livrée: {quantite_livree}, Retournée: {quantite_retournee}")
                    
                    # Validation des quantités
                    if quantite_livree > quantite_originale:
                        print(f"❌ ERREUR: Quantité livrée ({quantite_livree}) > Quantité originale ({quantite_originale}) pour panier {panier_id}")
                        continue
                    
                    # Calculer le prix unitaire actuel (avec upsell si applicable)
                    prix_unitaire_actuel = panier.article.prix_unitaire
                    if commande.compteur > 0 and getattr(panier.article, 'isUpsell', False):
                        if commande.compteur == 1 and getattr(panier.article, 'prix_upsell_1', None):
                            prix_unitaire_actuel = panier.article.prix_upsell_1
                        elif commande.compteur == 2 and getattr(panier.article, 'prix_upsell_2', None):
                            prix_unitaire_actuel = panier.article.prix_upsell_2
                        elif commande.compteur == 3 and getattr(panier.article, 'prix_upsell_3', None):
                            prix_unitaire_actuel = panier.article.prix_upsell_3
                        elif commande.compteur >= 4 and getattr(panier.article, 'prix_upsell_4', None):
                            prix_unitaire_actuel = panier.article.prix_upsell_4
                    
                    # Créer un enregistrement de retour si une partie n'est pas livrée
                    if quantite_retournee > 0:
                        article_retourne = ArticleRetourne.objects.create(
                            commande=commande,
                            article=panier.article,
                            variante=panier.variante,
                            quantite_retournee=quantite_retournee,
                            prix_unitaire_origine=prix_unitaire_actuel,
                            raison_retour=f"Livraison partielle - {commentaire}",
                            operateur_retour=operateur,
                            statut_retour='en_attente'
                        )
                        articles_retournes_crees.append(article_retourne)
                        print(f"✅ Article retourné créé: {panier.article.nom} - Quantité: {quantite_retournee}")
                    
                    # Mettre à jour le panier avec seulement la quantité livrée
                    if quantite_livree > 0:
                        panier.quantite = quantite_livree
                        panier.sous_total = prix_unitaire_actuel * quantite_livree
                        panier.save()
                        print(f"✅ Panier {panier.id} mis à jour - Quantité livrée: {quantite_livree}, Sous-total: {panier.sous_total}")
                    else:
                        # Aucun article livré, supprimer le panier
                        print(f"🗑️ Panier {panier.id} supprimé - Aucun article livré")
                        panier.delete()
            
            # Traiter les articles entièrement retournés (seulement ceux pas déjà traités)
            articles_retournes_ids = []
            if articles_renvoyes:
                for article_data in articles_renvoyes:
                    panier_id = article_data.get('panier_id')
                    if panier_id and panier_id not in paniers_traites:
                        try:
                            panier = commande.paniers.get(id=panier_id)
                            
                            # Calculer le prix unitaire au moment du retour (avec upsell si applicable)
                            prix_unitaire_retour = panier.article.prix_unitaire
                            if commande.compteur > 0 and getattr(panier.article, 'isUpsell', False):
                                if commande.compteur == 1 and getattr(panier.article, 'prix_upsell_1', None):
                                    prix_unitaire_retour = panier.article.prix_upsell_1
                                elif commande.compteur == 2 and getattr(panier.article, 'prix_upsell_2', None):
                                    prix_unitaire_retour = panier.article.prix_upsell_2
                                elif commande.compteur == 3 and getattr(panier.article, 'prix_upsell_3', None):
                                    prix_unitaire_retour = panier.article.prix_upsell_3
                                elif commande.compteur >= 4 and getattr(panier.article, 'prix_upsell_4', None):
                                    prix_unitaire_retour = panier.article.prix_upsell_4
                            
                            # Créer l'enregistrement de retour complet
                            article_retourne = ArticleRetourne.objects.create(
                                commande=commande,
                                article=panier.article,
                                variante=panier.variante,
                                quantite_retournee=panier.quantite,
                                prix_unitaire_origine=prix_unitaire_retour,
                                raison_retour=f"Article entièrement retourné - {commentaire}",
                                operateur_retour=operateur,
                                statut_retour='en_attente'
                            )
                            articles_retournes_crees.append(article_retourne)
                            articles_retournes_ids.append(panier_id)
                            paniers_traites.add(panier_id)
                            
                            print(f"✅ Article entièrement retourné créé: {panier.article.nom} - Quantité: {panier.quantite}")
                            panier.delete()  # Supprimer le panier original
                        except Exception as e:
                            print(f"❌ Erreur traitement panier retourné {panier_id}: {e}")
                    elif panier_id in paniers_traites:
                        print(f"⚠️ Panier {panier_id} déjà traité, ignoré dans articles_renvoyes")
            
            # 5. Construire le récap des articles retournés depuis les enregistrements créés
            recap_articles_retournes = []
            for article_retourne in articles_retournes_crees:
                variante_details = {}
                if article_retourne.variante:
                    variante_details = {
                        'id': article_retourne.variante.id,
                        'couleur': article_retourne.variante.couleur.nom if article_retourne.variante.couleur else None,
                        'pointure': article_retourne.variante.pointure.pointure if article_retourne.variante.pointure else None,
                        'reference_variante': article_retourne.variante.reference_variante
                    }
                
                recap_articles_retournes.append({
                    'article_id': article_retourne.article.id,
                    'variante_id': article_retourne.variante.id if article_retourne.variante else None,
                    'nom': article_retourne.article.nom,
                    'quantite': article_retourne.quantite_retournee,
                    'prix_unitaire': float(article_retourne.article.prix_unitaire),
                    'prix_actuel': float(article_retourne.prix_unitaire_origine),
                    'is_upsell': bool(getattr(article_retourne.article, 'isUpsell', False)),
                    'compteur': int(commande.compteur or 0),
                    'variante_details': variante_details,
                    'retour_id': article_retourne.id,
                    'statut_retour': article_retourne.statut_retour,
                    'date_retour': article_retourne.date_retour.isoformat()
                })
            
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
            
            # 7. Recalculer le total de la commande originale avec frais de livraison
            sous_total_articles = commande.paniers.aggregate(
                total=Sum('sous_total')
            )['total'] or 0
            
            # Ajouter les frais de livraison si activés
            if commande.frais_livraison and commande.ville:
                frais_livraison = float(commande.ville.frais_livraison or 0)
                total_commande = float(sous_total_articles) + frais_livraison
                print(f"DEBUG LIVRAISON PARTIELLE: Sous-total articles: {sous_total_articles} + Frais livraison: {frais_livraison} = Total: {total_commande}")
            else:
                total_commande = float(sous_total_articles)
                print(f"DEBUG LIVRAISON PARTIELLE: Sous-total articles: {sous_total_articles} (sans frais de livraison)")
            
            commande.total_cmd = total_commande
            commande.save()
            
            # 8. Construire les récapitulatifs pour l'opération (sans renvoi)
            articles_livres_json = []
            for article_data in articles_livres:
                article_id = article_data.get('article_id') or article_data.get('id')
                variante_id = article_data.get('variante_id')
                quantite_livree = article_data.get('quantite', 0)
                
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
                
                # Trouver la quantité originale de l'article avant livraison partielle
                quantite_originale = 0
                for panier_original in commande.paniers.all():
                    if panier_original.article.id == article_id:
                        quantite_originale = panier_original.quantite
                        break
                
                payload_item = {
                    'article_id': article_id,
                    'quantite_livree': quantite_livree,
                    'quantite_originale': quantite_originale,
                    'quantite_retournee': quantite_originale - quantite_livree,
                    'prix_unitaire': float(prix_unitaire),
                    'est_livraison_partielle': quantite_livree < quantite_originale
                }
                if variante_id:
                    payload_item['variante_id'] = variante_id
                articles_livres_json.append(payload_item)

            operation_conclusion_data = {
                'commentaire': commentaire,
                'articles_livres_count': len(articles_livres_json),
                'articles_retournes_count': len(recap_articles_retournes),
                'articles_livres': articles_livres_json,
                'recap_articles_retournes': recap_articles_retournes,
                'articles_retournes_ids': articles_retournes_ids,  # IDs des paniers supprimés
                'compteur_change': {
                    'ancien_compteur': ancien_compteur,
                    'nouveau_compteur': commande.compteur,
                    'total_quantite_upsell_restante': total_quantite_upsell_restante
                },
                'totaux': {
                    'sous_total_articles': float(sous_total_articles),
                    'total_commande': float(total_commande),
                    'frais_livraison_inclus': bool(commande.frais_livraison and commande.ville)
                }
            }
            Operation.objects.create(
                commande=commande,
                type_operation='LIVRAISON_PARTIELLE',
                conclusion=json.dumps(operation_conclusion_data, ensure_ascii=False),
                operateur=operateur
            )
            
            if recap_articles_retournes:
                messages.success(request, 
                    f"Livraison partielle effectuée avec succès. {len(articles_livres)} article(s) livré(s), {len(recap_articles_retournes)} article(s) retourné(s).")
            else:
                messages.success(request, 
                    f"Livraison partielle effectuée avec succès. {len(articles_livres)} article(s) livré(s).")
            
            return JsonResponse({
                'success': True,
                'message': f'Livraison partielle effectuée avec succès',
                'articles_livres': len(articles_livres),
                'articles_retournes': len(recap_articles_retournes),
                'recap_articles_retournes': recap_articles_retournes,
                'compteur_change': {
                    'ancien_compteur': ancien_compteur,
                    'nouveau_compteur': commande.compteur,
                    'total_quantite_upsell_restante': total_quantite_upsell_restante
                },
                'totaux': {
                    'sous_total_articles': float(sous_total_articles),
                    'total_commande': float(total_commande),
                    'frais_livraison_inclus': bool(commande.frais_livraison and commande.ville)
                }
            })
                
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer les données du panier d'une commande."""
    try:
        print(f"🔧 DEBUG API: Recherche commande ID {commande_id}")
        commande = get_object_or_404(Commande, id=commande_id)
        print(f"🔧 DEBUG API: Commande trouvée {commande.id_yz}")
        
        # Récupérer les paniers avec les articles
        paniers = commande.paniers.select_related('article').all()
        print(f"🔧 DEBUG API: Nombre de paniers trouvés: {paniers.count()}")
        
        # Préparer les données du panier avec calcul de prix upsell
        paniers_data = []
        for panier in paniers:
            try:
                # Calculer le prix en fonction du compteur et de l'upsell (même logique que detail_commande)
                prix_actuel = float(panier.article.prix_unitaire or 0)  # Prix de base par défaut
                
                if commande.compteur and commande.compteur > 0 and getattr(panier.article, 'isUpsell', False):
                    if commande.compteur == 1 and getattr(panier.article, 'prix_upsell_1', None):
                        prix_actuel = float(panier.article.prix_upsell_1)
                    elif commande.compteur == 2 and getattr(panier.article, 'prix_upsell_2', None):
                        prix_actuel = float(panier.article.prix_upsell_2)
                    elif commande.compteur == 3 and getattr(panier.article, 'prix_upsell_3', None):
                        prix_actuel = float(panier.article.prix_upsell_3)
                    elif commande.compteur >= 4 and getattr(panier.article, 'prix_upsell_4', None):
                        prix_actuel = float(panier.article.prix_upsell_4)
                
                paniers_data.append({
                    'id': panier.id,
                    'nom': panier.article.nom or '',
                    'reference': getattr(panier.article, 'reference', '') or '',
                    'quantite': panier.quantite or 0,
                    'prix_unitaire': f"{float(panier.article.prix_unitaire or 0):.2f}",
                    'prix_actuel': f"{prix_actuel:.2f}",
                    'sous_total': f"{float(panier.sous_total or 0):.2f}",
                    'pointure': getattr(panier.article, 'pointure', '') or '',
                    'couleur': getattr(panier.article, 'couleur', '') or '',
                    'article_id': panier.article.id,
                    'is_upsell': getattr(panier.article, 'isUpsell', False),
                    'compteur': commande.compteur or 0,
                })
            except Exception as panier_error:
                print(f"❌ Erreur traitement panier {panier.id}: {panier_error}")
                # Ajouter quand même le panier avec des valeurs par défaut
                paniers_data.append({
                    'id': panier.id,
                    'nom': getattr(panier.article, 'nom', f'Article {panier.id}'),
                    'reference': getattr(panier.article, 'reference', ''),
                    'quantite': panier.quantite or 0,
                    'prix_unitaire': "0.00",
                    'prix_actuel': "0.00",
                    'sous_total': "0.00",
                    'pointure': '',
                    'couleur': '',
                    'article_id': getattr(panier.article, 'id', 0),
                    'is_upsell': False,
                    'compteur': 0,
                })
        
        # Préparer les données de la commande
        try:
            commande_data = {
                'id': commande.id,
                'id_yz': commande.id_yz or '',
                'num_cmd': commande.num_cmd or '',
                'total_cmd': f"{float(commande.total_cmd or 0):.2f}",
                'date_cmd': commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else None,
                'etat_actuel': commande.etat_actuel.enum_etat.libelle if (commande.etat_actuel and hasattr(commande.etat_actuel, 'enum_etat')) else None,
            }
        except Exception as commande_error:
            print(f"❌ Erreur traitement commande {commande.id}: {commande_error}")
            commande_data = {
                'id': commande.id,
                'id_yz': getattr(commande, 'id_yz', ''),
                'num_cmd': getattr(commande, 'num_cmd', ''),
                'total_cmd': "0.00",
                'date_cmd': None,
                'etat_actuel': None,
            }
        
        print(f"🔧 DEBUG API: Préparation réponse avec {len(paniers_data)} paniers")
        return JsonResponse({
            'success': True,
            'commande': commande_data,
            'paniers': paniers_data,
        })
        
    except Exception as e:
        print(f"❌ ERREUR API api_panier_commande: {str(e)}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def api_verifier_stock_article(request, article_id):
    """API pour vérifier l'état du stock d'un article."""
    try:
        print(f"🔍 [STOCK_CHECK] Vérification stock article ID: {article_id}")
        
        article = get_object_or_404(Article, id=article_id)
        print(f"📦 [STOCK_CHECK] Article trouvé: {article.nom}, Stock: {article.qte_disponible}")
        
        return JsonResponse({
            'success': True,
            'article': {
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'qte_disponible': article.qte_disponible,
                'prix_unitaire': float(article.prix_unitaire),
                'actif': article.actif,
                'categorie': article.categorie,
                'couleur': article.couleur,
                'pointure': article.pointure,
                'phase': article.phase,
                'isUpsell': article.isUpsell,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'article_id': article_id
        })


# Note: La fonction de test de réintégration du stock a été supprimée
# car la réincrémentation du stock est maintenant gérée par les opérateurs de préparation
