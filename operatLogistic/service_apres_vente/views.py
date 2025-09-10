from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from commande.models import Commande, EtatCommande, EnumEtatCmd, Envoi, Operation
from django.db import transaction
from datetime import datetime
import json
from article.models import Article
from parametre.models import Operateur

@login_required
@require_POST
def changer_etat_livraison(request, commande_id):
    """
    Vue générique pour changer l'état de livraison d'une commande
    par un opérateur logistique.
    """
    try:
        commande = Commande.objects.get(id=commande_id)
        operateur = request.user.profil_operateur
        
        # Vérifier que l'opérateur est bien un opérateur logistique
        if not operateur or not operateur.is_logistique:
            messages.error(request, "Vous n'avez pas les droits pour effectuer cette action.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)
        
        nouvel_etat = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire')
        
        if not nouvel_etat or not commentaire:
            messages.error(request, "L'état et le commentaire sont obligatoires.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)

        with transaction.atomic():
            # Fermer l'état actuel s'il existe
            etat_actuel = commande.etat_actuel
            if etat_actuel:
                etat_actuel.date_fin = timezone.now()
                etat_actuel.save()

            # Créer le nouvel état
            enum_etat = EnumEtatCmd.objects.get(libelle=nouvel_etat)
            
            # Traitement spécifique selon l'état
            details_supplementaires = ""
            
          
            
            if nouvel_etat == 'Reportée':
                # Récupérer et valider la date de report
                date_str = request.POST.get('date_report')
                if not date_str:
                    messages.error(request, "La date de report est obligatoire.")
                    return redirect('operatLogistic:detail_commande', commande_id=commande_id)
                
                try:
                    date_report = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if date_report < timezone.now().date():
                        messages.error(request, "La date de report ne peut pas être dans le passé")
                        return redirect('operatLogistic:detail_commande', commande_id=commande_id)
                    
                    # Mettre à jour l'envoi
                    envoi.reporter(date_report, commentaire, operateur)
                    
                    # Ajouter la date de report au commentaire
                    details_supplementaires = f"\n\nDate de report : {date_report.strftime('%d/%m/%Y')}"
                    details_supplementaires += "\nArticles concernés :"
                    for panier in commande.paniers.all():
                        details_supplementaires += f"\n- {panier.article.nom} (Quantité: {panier.quantite})"
                except ValueError:
                    messages.error(request, "Format de date invalide")
                    return redirect('operatLogistic:detail_commande', commande_id=commande_id)

            elif nouvel_etat == 'Livrée':
                # Marquer l'envoi comme livré
                envoi.marquer_comme_livre(operateur)
                details_supplementaires = f"\nLivraison effectuée le : {timezone.now().strftime('%d/%m/%Y à %H:%M')}"



            # Créer le nouvel état avec le commentaire complet
            commentaire_complet = commentaire + details_supplementaires
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_etat,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_complet
            )

            messages.success(request, f"État de la commande mis à jour : {nouvel_etat}")
            
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {str(e)}")
    
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)

def _render_sav_list(request, commandes, page_title, page_subtitle):
    """Fonction utilitaire pour rendre la liste SAV avec le template standard."""
    context = {
        'commandes': commandes,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    return render(request, 'operatLogistic/sav/liste_commandes_sav.html', context)

def _render_sav_list_custom(request, commandes, template_name):
    """Fonction utilitaire pour rendre la liste SAV avec un template personnalisé."""
    context = {
        'commandes': commandes,
    }
    return render(request, f'operatLogistic/sav/{template_name}', context)

@login_required
def commandes_reportees(request):
    """Affiche les commandes dont la livraison est reportée."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Reportée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel (Reportée)
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Reportée',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
     
        # Analyser les articles pour identifier ceux livrés partiellement (si applicable)
        commande.articles_livres_partiellement = []
        commande.articles_renvoyes = []
        
        # Chercher les informations dans les opérations liées à la livraison partielle
        from commande.models import Operation
        operation_livraison_partielle = Operation.objects.filter(
            commande=commande,
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()
        
        if operation_livraison_partielle and operation_livraison_partielle.conclusion:
            try:
                parsed_conclusion = json.loads(operation_livraison_partielle.conclusion)
                temp_articles_livres = []
                for item in parsed_conclusion.get('articles_livres', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        # Correction: Toujours prendre le prix de l'objet Article si le prix de l'item est 0.0 ou None
                        item_prix = item.get('prix_unitaire')
                        if item_prix is not None and float(item_prix) != 0.0:
                            prix_unitaire_final = float(item_prix)
                        else:
                            prix_unitaire_final = float(article_obj.prix_unitaire) if article_obj.prix_unitaire is not None else 0.0
                        
                        temp_articles_livres.append({
                            'article_id': item['article_id'],
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite_livree': item.get('quantite', 0),
                            'prix_unitaire': prix_unitaire_final
                        })
                    except Article.DoesNotExist:
                        temp_articles_livres.append({
                            'article_id': item.get('article_id'),
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite_livree': item.get('quantite', 0),
                            'prix_unitaire': float(item.get('prix_unitaire', 0.0) or 0.0)
                        })
                commande.articles_livres_partiellement = temp_articles_livres
                temp_articles_renvoyes = []
                for item in parsed_conclusion.get('recap_articles_renvoyes', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        # Correction: Toujours prendre le prix de l'objet Article si le prix de l'item est 0.0 ou None
                        item_prix = item.get('prix_unitaire')
                        if item_prix is not None and float(item_prix) != 0.0:
                            prix_unitaire_final = float(item_prix)
                        else:
                            prix_unitaire_final = float(article_obj.prix_unitaire) if article_obj.prix_unitaire is not None else 0.0

                        temp_articles_renvoyes.append({
                            'article_id': item['article_id'],
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': prix_unitaire_final,
                            'etat': item.get('etat', 'inconnu').lower()
                        })
                    except Article.DoesNotExist:
                        temp_articles_renvoyes.append({
                            'article_id': item.get('article_id'),
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': float(item.get('prix_unitaire', 0.0) or 0.0),
                            'etat': item.get('etat', 'inconnu').lower()
                        })
                commande.articles_renvoyes = temp_articles_renvoyes
            except Exception:
                commande.articles_livres_partiellement = []
                commande.articles_renvoyes = []
        else:
            # fallback : tous les articles du panier comme livrés partiellement
            commande.articles_livres_partiellement = [
                {
                    'article_id': panier.article.id,
                    'nom': panier.article.nom,
                    'reference': panier.article.reference,
                    'pointure': getattr(panier.article, 'pointure', ''),
                    'couleur': getattr(panier.article, 'couleur', ''),
                    'quantite_livree': panier.quantite,
                    'prix_unitaire': float(getattr(panier.article, 'prix_unitaire', 0.0) or 0.0)
                }
                for panier in commande.paniers.all()
            ]
            commande.articles_renvoyes = []
    
    return _render_sav_list_custom(request, commandes, 'commandes_reportees.html')

@login_required
def commandes_livrees_partiellement(request):
    """Affiche les commandes livrées partiellement."""
    # Récupérer toutes les commandes qui ont eu une livraison partielle
    # (même si elles ont été renvoyées en préparation ensuite)
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement'
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'  # Ajouter les paniers et articles
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état "Livrée Partiellement" le plus récent
        etat_livraison_partielle = commande.etats.filter(
            enum_etat__libelle='Livrée Partiellement'
        ).order_by('-date_debut').first()
        
        if etat_livraison_partielle:
            commande.date_livraison_partielle = etat_livraison_partielle.date_debut
            commande.commentaire_livraison_partielle = etat_livraison_partielle.commentaire
            commande.operateur_livraison = etat_livraison_partielle.operateur
        
        # Déterminer le statut actuel de la commande
        etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
        if etat_actuel:
            commande.etat_actuel_sav = etat_actuel
            commande.statut_actuel = etat_actuel.enum_etat.libelle
            commande.est_renvoyee_preparation = etat_actuel.enum_etat.libelle in ['En préparation', 'À imprimer']
        else:
            commande.etat_actuel_sav = None
            commande.statut_actuel = "Inconnu"
            commande.est_renvoyee_preparation = False
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
       
        
        # Analyser les articles pour identifier ceux livrés partiellement
        commande.articles_livres_partiellement = []
        commande.articles_renvoyes = []
        
        # Chercher les informations dans les opérations liées à la livraison partielle
        from commande.models import Operation
        operation_livraison_partielle = Operation.objects.filter(
            commande=commande,
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()

        conclusion_content = ""
        articles_renvoyes_json = []
        if operation_livraison_partielle and operation_livraison_partielle.conclusion:
            conclusion_content = operation_livraison_partielle.conclusion

        try:
            if conclusion_content:
                parsed_conclusion = json.loads(conclusion_content)
                temp_articles_livres = []
                for item in parsed_conclusion.get('articles_livres', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        # prix_unitaire = float(item.get('prix_unitaire', article_obj.prix_unitaire) or article_obj.prix_unitaire or 0.0)
                        # Log ajouté
                        # print(f"DEBUG: Article {article_obj.nom}, Prix Unitaire: {prix_unitaire}")

                        # Correction: Toujours prendre le prix de l'objet Article si le prix de l'item est 0.0 ou None
                        item_prix = item.get('prix_unitaire')
                        if item_prix is not None and float(item_prix) != 0.0:
                            prix_unitaire_final = float(item_prix)
                        else:
                            prix_unitaire_final = float(article_obj.prix_unitaire) if article_obj.prix_unitaire is not None else 0.0
                        
                        temp_articles_livres.append({
                            'article_id': item['article_id'],
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite_livree': item.get('quantite', 0),
                            'prix_unitaire': prix_unitaire_final
                        })
                    except Article.DoesNotExist:
                        temp_articles_livres.append({
                            'article_id': item.get('article_id'),
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite_livree': item.get('quantite', 0),
                            'prix_unitaire': float(item.get('prix_unitaire', 0.0) or 0.0) # Fallback pour articles inconnus
                        })
                commande.articles_livres_partiellement = temp_articles_livres

                temp_articles_renvoyes = []
                for item in parsed_conclusion.get('recap_articles_renvoyes', []):
                    try:
                        article_obj = Article.objects.get(id=item['article_id'])
                        # prix_unitaire = float(item.get('prix_unitaire', 0.0) or 0.0) # Ancien code
                        # Log ajouté
                        # print(f"DEBUG: Article renvoyé {article_obj.nom}, Prix Unitaire: {prix_unitaire}")

                        # Correction: Toujours prendre le prix de l'objet Article si le prix de l'item est 0.0 ou None
                        item_prix = item.get('prix_unitaire')
                        if item_prix is not None and float(item_prix) != 0.0:
                            prix_unitaire_final = float(item_prix)
                        else:
                            prix_unitaire_final = float(article_obj.prix_unitaire) if article_obj.prix_unitaire is not None else 0.0

                        temp_articles_renvoyes.append({
                            'article_id': item['article_id'],
                            'nom': article_obj.nom,
                            'reference': article_obj.reference,
                            'pointure': getattr(article_obj, 'pointure', ''),
                            'couleur': getattr(article_obj, 'couleur', ''),
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': prix_unitaire_final,
                            'etat': item.get('etat', 'inconnu').lower()
                        })
                    except Article.DoesNotExist:
                        temp_articles_renvoyes.append({
                            'article_id': item.get('article_id'),
                            'nom': 'Inconnu',
                            'reference': '',
                            'pointure': '',
                            'couleur': '',
                            'quantite': item.get('quantite', 0),
                            'prix_unitaire': float(item.get('prix_unitaire', 0.0) or 0.0),
                            'etat': item.get('etat', 'inconnu').lower()
                        })
                commande.articles_renvoyes = temp_articles_renvoyes
            else:
                commande.articles_livres_partiellement = []
                commande.articles_renvoyes = []
        except json.JSONDecodeError as e:
            commande.articles_livres_partiellement = []
            commande.articles_renvoyes = []
        except Exception as e:
            commande.articles_livres_partiellement = []
            commande.articles_renvoyes = []

  # dans la modale de détails des articles de la commande originale.

    return _render_sav_list_custom(request, commandes, 'commandes_livrees_partiellement.html')

@login_required
def commandes_livrees_avec_changement(request):
    """Affiche les commandes livrées avec des changements."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée avec changement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Livrée avec changement',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
        # Préparer les articles pour la modale (même logique que pour les livraisons partielles)
        commande.articles_livres_partiellement = [
            {
                'article_id': panier.article.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'pointure': getattr(panier.article, 'pointure', ''),
                'couleur': getattr(panier.article, 'couleur', ''),
                'quantite_livree': panier.quantite,
                'prix_unitaire': float(getattr(panier.article, 'prix_unitaire', 0.0) or 0.0)
            }
            for panier in commande.paniers.all()
        ]
        commande.articles_renvoyes = []
    
    return _render_sav_list_custom(request, commandes, 'commandes_livrees_avec_changement.html')

@login_required
def commandes_retournees(request):
    """Affiche les commandes retournées par l'opérateur logistique."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Retournée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Enrichir les données pour chaque commande
    for commande in commandes:
        # Trouver l'état actuel
        commande.etat_actuel_sav = commande.etats.filter(
            enum_etat__libelle='Retournée',
            date_fin__isnull=True
        ).first()
        
        # Calculer le nombre d'articles dans la commande
        commande.nombre_articles = commande.paniers.count()
        
        commande.articles_livres_partiellement = [
            {
                'article_id': panier.article.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'pointure': getattr(panier.article, 'pointure', ''),
                'couleur': getattr(panier.article, 'couleur', ''),
                'quantite_livree': panier.quantite,
                'prix_unitaire': float(getattr(panier.article, 'prix_unitaire', 0.0) or 0.0),
                'prix_actuel': float(getattr(panier.article, 'prix_actuel', 0.0) or 0.0)
            }
            for panier in commande.paniers.all()
        ]
        commande.articles_renvoyes = []
    
    return _render_sav_list_custom(request, commandes, 'commandes_retournees.html')

@login_required
def commandes_livrees(request):
    """Affiche les commandes livrées avec succès avec onglets pour les payées et non payées."""
    # Récupérer le paramètre d'onglet
    current_tab = request.GET.get('tab', 'toutes')
    
    # Gestion du filtre de temps
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    preset = request.GET.get('preset')
    
    # Construire la requête de base avec tous les filtres
    from datetime import datetime, timedelta
    
    # Base query pour les commandes livrées
    base_query = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur',
        'envois', 'paniers__article'
    )
    
    # Appliquer le filtre de temps une seule fois
    if start_date and end_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            
            # Filtrer par date de début des états "Livrée"
            base_query = base_query.filter(
                etats__date_debut__date__range=[start_datetime.date(), end_datetime.date()]
            )
        except ValueError:
            pass  # Ignorer les erreurs de format de date
    elif preset:
        # Appliquer des presets prédéfinis
        today = datetime.now().date()
        
        if preset == 'today':
            base_query = base_query.filter(etats__date_debut__date=today)
        elif preset == 'yesterday':
            yesterday = today - timedelta(days=1)
            base_query = base_query.filter(etats__date_debut__date=yesterday)
        elif preset == 'this_week':
            # Lundi de cette semaine
            monday = today - timedelta(days=today.weekday())
            base_query = base_query.filter(etats__date_debut__date__gte=monday)
        elif preset == 'last_week':
            # Lundi de la semaine dernière
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            base_query = base_query.filter(etats__date_debut__date__range=[last_monday, last_sunday])
        elif preset == 'this_month':
            # Premier jour du mois
            first_day = today.replace(day=1)
            base_query = base_query.filter(etats__date_debut__date__gte=first_day)
        elif preset == 'last_month':
            # Premier jour du mois dernier
            if today.month == 1:
                first_day_last_month = today.replace(year=today.year-1, month=12, day=1)
                last_day_last_month = today.replace(year=today.year-1, month=12, day=31)
            else:
                first_day_last_month = today.replace(month=today.month-1, day=1)
                last_day_last_month = (today.replace(month=today.month, day=1) - timedelta(days=1))
            base_query = base_query.filter(etats__date_debut__date__range=[first_day_last_month, last_day_last_month])
        elif preset == 'this_year':
            # Premier jour de l'année
            first_day_year = today.replace(month=1, day=1)
            base_query = base_query.filter(etats__date_debut__date__gte=first_day_year)
        elif preset == 'last_year':
            # Premier et dernier jour de l'année dernière
            first_day_last_year = today.replace(year=today.year-1, month=1, day=1)
            last_day_last_year = today.replace(year=today.year-1, month=12, day=31)
            base_query = base_query.filter(etats__date_debut__date__range=[first_day_last_year, last_day_last_year])
    
    # Ajouter l'ordre et distinct une seule fois
    base_query = base_query.order_by('-etats__date_debut').distinct()
    
    # Filtrer selon l'onglet sélectionné
    if current_tab == 'payees':
        commandes = base_query.filter(payement='Payé')
    elif current_tab == 'non_payees':
        commandes = base_query.exclude(payement='Payé')
    else:  # 'toutes'
        commandes = base_query
    
    # Compter les commandes pour chaque onglet (avec le filtre de temps appliqué)
    total_commandes = base_query.count()
    commandes_payees = base_query.filter(payement='Payé').count()
    commandes_non_payees = base_query.exclude(payement='Payé').count()
    
    # Enrichir les données pour chaque commande - optimisé pour éviter les requêtes N+1
    commandes_list = list(commandes)  # Évaluer une seule fois
    
    for commande in commandes_list:
        # Trouver l'état actuel depuis les données préchargées
        commande.etat_actuel_sav = next(
            (etat for etat in commande.etats.all() 
             if etat.enum_etat.libelle == 'Livrée' and etat.date_fin is None), 
            None
        )
        
        # Utiliser les données préchargées pour compter les articles
        panier_list = list(commande.paniers.all())
        commande.nombre_articles = len(panier_list)
        
        # Construire les données des articles depuis les paniers préchargés
        commande.articles_livres_partiellement = [
            {
                'article_id': panier.article.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'pointure': getattr(panier.article, 'pointure', ''),
                'couleur': getattr(panier.article, 'couleur', ''),
                'quantite_livree': panier.quantite,
                'prix_unitaire': float(getattr(panier.article, 'prix_unitaire', 0.0) or 0.0)
            }
            for panier in panier_list
        ]
        commande.articles_renvoyes = []
    
    # Créer le contexte avec les variables supplémentaires
    context = {
        'commandes': commandes_list,
        'current_tab': current_tab,
        'total_commandes': total_commandes,
        'commandes_payees': commandes_payees,
        'commandes_non_payees': commandes_non_payees,
        # Paramètres de filtre pour le template
        'filter_start_date': start_date,
        'filter_end_date': end_date,
        'filter_preset': preset,
    }
    return render(request, 'operatLogistic/sav/commandes_livrees.html', context)


@login_required
@require_POST
def marquer_commande_payee(request, commande_id):
    """Marquer une commande comme payée."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est dans un état qui permet le paiement
        etats_paiement_autorises = ['Livrée', 'Livrée Partiellement', 'Livrée avec changement']
        if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle not in etats_paiement_autorises:
            return JsonResponse({
                'success': False, 
                'error': f'Cette commande ne peut pas être marquée comme payée. État actuel: {commande.etat_actuel.enum_etat.libelle if commande.etat_actuel else "Aucun"}'
            })
        
        # Statut fixe : toujours "Payé"
        nouveau_statut = 'Payé'
        
        with transaction.atomic():
            # Mettre à jour le statut de paiement
            ancien_statut = commande.payement
            commande.payement = nouveau_statut
            commande.save()
            
            # Créer une opération pour tracer l'action
            Operation.objects.create(
                commande=commande,
                type_operation='CHANGEMENT_STATUT_PAIEMENT',
                conclusion=f"Statut de paiement changé de '{ancien_statut}' vers '{nouveau_statut}'",
                operateur=operateur
            )
            return JsonResponse({
                'success': True,
                'message': f'Statut de paiement mis à jour vers {nouveau_statut} avec succès',
                'nouveau_statut': nouveau_statut,
                'ancien_statut': ancien_statut
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
