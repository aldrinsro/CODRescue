from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from commande.models import Commande
from django.contrib import messages
from django.contrib.auth.models import User, Group
from parametre.models import Operateur, Ville # Assurez-vous que ce chemin est correct
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm # Importez PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.utils import timezone
from commande.models import Commande, EtatCommande, EnumEtatCmd, Panier
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db import models, transaction
from client.models import Client
from article.models import Article, VarianteArticle
import logging
from django.urls import reverse
from django.template.loader import render_to_string
from decimal import Decimal
# Suppression de l'app notifications: retirer les imports

# Create your views here.

@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur de confirmation"""
    from commande.models import Commande, EtatCommande
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Sum
    
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Dates pour les calculs de périodes
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # Récupérer les commandes affectées à cet opérateur
    commandes_affectees = Commande.objects.filter(
        Q(etats__operateur=operateur, etats__date_fin__isnull=True, etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation']) |
        Q(etats__date_fin__isnull=True, etats__enum_etat__libelle='Retour Confirmation')
    ).distinct().select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'paniers__article'
    ).order_by('-date_cmd', '-date_creation')
    
    # Statistiques des commandes affectées à cet opérateur
    stats = {}
    
    # Commandes en attente de confirmation (affectées mais pas encore en cours de confirmation)
    stats['commandes_en_attente'] = commandes_affectees.filter(
        etats__enum_etat__libelle='Affectée',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes en cours de confirmation
    stats['commandes_en_cours'] = commandes_affectees.filter(
        etats__enum_etat__libelle='En cours de confirmation',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes retournées par la préparation
    stats['commandes_retournees'] = Commande.objects.filter(
        etats__enum_etat__libelle='Retour Confirmation',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Commandes confirmées par cet opérateur (toutes)
    commandes_confirmees_all = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Confirmée'
    ).distinct()
    
    stats['commandes_confirmees'] = commandes_confirmees_all.count()
    
    # Commandes confirmées aujourd'hui
    stats['commandes_confirmees_aujourd_hui'] = commandes_confirmees_all.filter(
        etats__date_debut__date=today
    ).count()
    
    # Commandes confirmées cette semaine
    stats['commandes_confirmees_semaine'] = commandes_confirmees_all.filter(
        etats__date_debut__date__gte=week_start
    ).count()
    
    # Valeur totale des commandes confirmées
    valeur_totale = commandes_confirmees_all.aggregate(
        total=Sum('total_cmd')
    )['total'] or 0
    stats['valeur_totale_confirmees'] = valeur_totale
    
        # Commandes marquées erronées par cet opérateur
    stats['commandes_erronnees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Erronée'
    ).distinct().count()

    # Commandes annulées par cet opérateur
    stats['commandes_annulees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Annulée'
    ).distinct().count()

    stats['total_commandes'] = commandes_affectees.count()
    
    # Taux de performance
    if stats['total_commandes'] > 0:
        stats['taux_confirmation'] = round((stats['commandes_confirmees'] / stats['total_commandes']) * 100, 1)
    else:
        stats['taux_confirmation'] = 0
    
    context = {
        'operateur': operateur,
        **stats  # Ajouter toutes les statistiques au contexte
    }
    
    return render(request, 'composant_generale/operatConfirme/home.html', context)

@login_required
def liste_commandes(request):
    """Liste des commandes affectées à l'opérateur de confirmation connecté"""
    from django.core.paginator import Paginator
    from django.db.models import Q, Count, Sum
    from commande.models import Commande, EtatCommande
    from common.filter_utils import apply_all_filters, get_filter_context
    
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Commandes à afficher :
    # Celles qui sont explicitement affectées à l'opérateur avec un état actif.
    commandes_list = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True,
        etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation', 'Report de confirmation']
    ).distinct().select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'paniers__article', 'operations'
    ).order_by('-etats__date_debut')
    
    # Recherche
    search_query = request.GET.get('search', '').strip()
    if search_query:
        commandes_list = commandes_list.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(adresse__icontains=search_query)
        )

    # Appliquer les filtres (date, synchronisation, tri)
    commandes_list = apply_all_filters(commandes_list, request)

    # Statistiques pour l'affichage des onglets/badges
    stats = {
        'en_attente': Commande.objects.filter(
            etats__operateur=operateur,
            etats__date_fin__isnull=True,
            etats__enum_etat__libelle='Affectée'
        ).distinct().count(),

        'en_cours': Commande.objects.filter(
            etats__operateur=operateur,
            etats__date_fin__isnull=True,
            etats__enum_etat__libelle='En cours de confirmation'
        ).distinct().count(),

        # Reportées de confirmation (avec date_report en date_fin_delayed)
        'reportees': Commande.objects.filter(
            etats__operateur=operateur,
            etats__date_fin__isnull=True,
            etats__enum_etat__libelle='Report de confirmation'
        ).distinct().count(),

        # Ancien compteur conservé si utilisé ailleurs (retours de préparation)
      
    }
    stats['total'] = stats['en_attente'] + stats['en_cours'] + stats['reportees']

    # Filtrage par onglet
    tab = request.GET.get('tab', 'toutes')
    tab_map = {
        'en_attente': {'libelle': 'Affectée', 'display': 'En Attente'},
        'en_cours': {'libelle': 'En cours de confirmation', 'display': 'En Cours'},
        'reportees': {'libelle': 'Report de confirmation', 'display': 'Reportées'},
        'retournees': {'libelle': 'Retour Confirmation', 'display': 'Retournées'},
    }
    
    current_tab_display_name = "Toutes"
    if tab in tab_map:
        commandes_list = commandes_list.filter(etats__enum_etat__libelle=tab_map[tab]['libelle'], etats__date_fin__isnull=True)
        current_tab_display_name = tab_map[tab]['display']
    
    # Pagination
    paginator = Paginator(commandes_list, 15)  # 15 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Préparer un mapping des dates de report pour affichage (commande_id -> date_fin_delayed)
    dates_report = {}
    try:
        # Récupérer les états actifs "Reporté de confirmation" pour l'opérateur
        etats_reportes = EtatCommande.objects.filter(
            operateur=operateur,
            date_fin__isnull=True,
            enum_etat__libelle='Report de confirmation'
        ).select_related('commande')
        for etat in etats_reportes:
            dates_report[etat.commande_id] = etat.date_fin_delayed
    except Exception:
        pass

    context = {
        'page_title': 'Mes Commandes à Confirmer',
        'page_subtitle': f"Gestion des commandes qui vous sont affectées ou retournées.",
        'commandes': commandes_list,  # Passer toutes les commandes pour la pagination intelligente
        'page_obj': page_obj,  # Garder pour compatibilité si nécessaire
        'search_query': search_query,
        'operateur': operateur,
        'stats': stats,
        'current_tab': tab,
        'current_tab_display_name': current_tab_display_name,
        'dates_report': dates_report,
    }
    context.update(get_filter_context(request))

    return render(request, 'operatConfirme/liste_commande.html', context)

@login_required
def confirmer_commande_ajax(request, commande_id):
    """Confirme une commande spécifique via AJAX depuis la page de confirmation"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation
    from article.models import Article
    from django.http import JsonResponse
    from django.utils import timezone
    from django.db import transaction
    
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            commentaire = data.get('commentaire', '')
            # Forcer la confirmation immédiate: ignorer tout type « delayed »
            confirmation_type = 'immediate'
            date_fin_delayed = None
        except:
            commentaire = ''
            confirmation_type = 'immediate'
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil d\'opérateur de confirmation non trouvé.'})
    
    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_actuel = commande.etat_actuel
        if not (etat_actuel and etat_actuel.operateur == operateur):
            return JsonResponse({'success': False, 'message': 'Cette commande ne vous est pas affectée.'})
        
        # Vérifier que la commande n'est pas déjà confirmée
        if etat_actuel.enum_etat.libelle == 'Confirmée':
            return JsonResponse({'success': False, 'message': 'Cette commande est déjà confirmée.'})
            
        # Vérifier qu'au moins une opération a été effectuée
        operations_effectuees = Operation.objects.filter(
            commande=commande,
            operateur=operateur,
            type_operation__in=[
                'APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'Vocal Whatsapp', 'ENVOI_SMS'
            ]
        ).exists()
        
        if not operations_effectuees:
            return JsonResponse({
                'success': False, 
                'message': 'Vous devez effectuer au moins une opération (appel, message, etc.) avant de confirmer la commande.'
            })
        
        # Utiliser une transaction pour la confirmation et la décrémentation du stock
        with transaction.atomic():
            print(f"🎯 DEBUG: Début de la confirmation de la commande {commande.id_yz}")
            
            # IMPORTANT: Récupérer et sauvegarder les informations de livraison depuis le formulaire
            # Ces informations doivent être envoyées avec la requête de confirmation
            try:
                if 'ville_livraison' in data and data['ville_livraison']:
                    from parametre.models import Ville
                    nouvelle_ville = Ville.objects.get(id=data['ville_livraison'])
                    commande.ville = nouvelle_ville
                    print(f"🏙️ DEBUG: Ville de livraison mise à jour: {nouvelle_ville.nom}")
                
                if 'adresse_livraison' in data:
                    commande.adresse = data['adresse_livraison']
                    print(f"📍 DEBUG: Adresse de livraison mise à jour: {data['adresse_livraison'][:50]}...")
                
                # Sauvegarder les modifications de la commande
                commande.save()
                print(f"💾 DEBUG: Informations de livraison sauvegardées")
                
            except Ville.DoesNotExist:
                print(f"❌ DEBUG: Ville de livraison non trouvée: {data.get('ville_livraison')}")
            except Exception as e:
                print(f"⚠️ DEBUG: Erreur lors de la sauvegarde des infos de livraison: {str(e)}")
            
            # Vérifier le stock et décrémenter les articles
            articles_decrémentes = []
            stock_insuffisant = []
            
            for panier in commande.paniers.all():
                article = panier.article
                variante = panier.variante
                quantite_commandee = panier.quantite

                # Vérifier l'intégrité de la variante référencée
                if variante:
                    # Vérifier que la variante existe encore et appartient bien à l'article
                    try:
                        variante_verifiee = VarianteArticle.objects.get(
                            id=variante.id,
                            article=article,
                            actif=True
                        )
                        stock_disponible = variante_verifiee.qte_disponible
                        nom_article = f"{article.nom} - {variante_verifiee.couleur}/{variante_verifiee.pointure}"
                        print(f"📦 DEBUG: Variante {nom_article} (ID:{variante_verifiee.id})")
                        # Utiliser la variante vérifiée
                        variante = variante_verifiee
                    except VarianteArticle.DoesNotExist:
                        # La variante n'existe plus, basculer sur l'article principal
                        print(f"⚠️ ATTENTION: Variante {variante.id} introuvable pour l'article {article.id}")
                        print(f"   Basculement vers l'article principal...")
                        variante = None
                        stock_disponible = article.qte_disponible
                        nom_article = f"{article.nom} (article principal - variante supprimée)"
                        print(f"📦 DEBUG: Article principal {nom_article} (ID:{article.id})")

                        # Mettre à jour le panier pour supprimer la référence incorrecte
                        panier.variante = None
                        panier.save()
                        print(f"🔧 DEBUG: Panier {panier.id} corrigé (variante supprimée)")
                else:
                    stock_disponible = article.qte_disponible
                    nom_article = article.nom
                    print(f"📦 DEBUG: Article {nom_article} (ID:{article.id})")
                
                print(f"   - Stock actuel: {stock_disponible}")
                print(f"   - Quantité commandée: {quantite_commandee}")
                
                # Vérifier si le stock est suffisant
                if stock_disponible < quantite_commandee:
                    stock_insuffisant.append({
                        'article': nom_article,
                        'stock_actuel': stock_disponible,
                        'quantite_demandee': quantite_commandee
                    })
                    print(f"❌ DEBUG: Stock insuffisant pour {nom_article}")
                else:
                    # Décrémentation directe et simple du stock
                    ancien_stock = stock_disponible

                    # Décrémenter directement le stock sur la variante ou l'article
                    if variante:
                        # Décrémenter sur la variante
                        variante.qte_disponible = max(0, variante.qte_disponible - quantite_commandee)
                        variante.save()
                        nouveau_stock = variante.qte_disponible
                        print(f"✅ DEBUG: Stock variante mis à jour: {ancien_stock} → {nouveau_stock}")
                    else:
                        # Décrémenter sur l'article principal
                        article.qte_disponible = max(0, article.qte_disponible - quantite_commandee)
                        article.save()
                        nouveau_stock = article.qte_disponible
                        print(f"✅ DEBUG: Stock article mis à jour: {ancien_stock} → {nouveau_stock}")

                    articles_decrémentes.append({
                        'article': nom_article,
                        'ancien_stock': ancien_stock,
                        'nouveau_stock': nouveau_stock,
                        'quantite_decrémententée': quantite_commandee
                    })
                    
                    print(f"✅ DEBUG: Stock mis à jour pour {nom_article}")
                    print(f"   - Ancien stock: {ancien_stock}")
                    print(f"   - Nouveau stock: {nouveau_stock}")
            
            # Si il y a des problèmes de stock, annuler la transaction
            if stock_insuffisant:
                error_msg = f"Stock insuffisant pour : "
                for item in stock_insuffisant:
                    error_msg += f"\n• {item['article']}: Stock={item['stock_actuel']}, Demandé={item['quantite_demandee']}"
                
                print(f"❌ DEBUG: Confirmation annulée - problèmes de stock")
                for item in stock_insuffisant:
                    print(f"   - {item['article']}: {item['stock_actuel']}/{item['quantite_demandee']}")
                
                return JsonResponse({
                    'success': False, 
                    'message': error_msg,
                    'stock_insuffisant': stock_insuffisant
                })
            
            # Déterminer l'état suivant: toujours "Confirmée"
            enum_suivant = EnumEtatCmd.objects.get(libelle='Confirmée')
            print(f"⚡ DEBUG: Confirmation immédiate (forcée)")
            
            # Fermer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            print(f"🔄 DEBUG: État actuel fermé: {etat_actuel.enum_etat.libelle}")
            
            # Créer le nouvel état selon le type de confirmation
            nouvel_etat = EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_suivant,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire,
                date_fin_delayed=None
            )
            print(f"✅ DEBUG: Nouvel état créé: {enum_suivant.libelle}")

            # L'état "Confirmée" reste actif (pas de date_fin définie)
            # La commande sera visible dans la liste des commandes confirmées
            print("✅ DEBUG: État 'Confirmée' créé et maintenu actif")
            
            # Note: L'état "Confirmée" reste ouvert pour permettre le suivi
            # La transition vers "À imprimer" se fera manuellement par les superviseurs
            # ou automatiquement lors de la prochaine étape du processus
            
            # Log des articles décrémernts
            print(f"📊 DEBUG: Résumé de la décrémentation:")
            print(f"   - {len(articles_decrémentes)} article(s) décrémenté(s)")
            for item in articles_decrémentes:
                print(f"   - {item['article']}: {item['ancien_stock']} → {item['nouveau_stock']} (-{item['quantite_decrémententée']})")
        
        # Message selon le type de confirmation
        message = f'Commande {commande.id_yz} confirmée immédiatement avec succès.'
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'confirmation_type': confirmation_type,
            'articles_decrémentes': len(articles_decrémentes),
            'details_stock': articles_decrémentes,
            'redirect_url': '/operateur-confirme/confirmation/'
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée.'})
    except EnumEtatCmd.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'État "Confirmée" non trouvé dans la configuration.'})
    except Exception as e:
        print(f"❌ DEBUG: Erreur lors de la confirmation: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@login_required
def confirmer_commande(request, commande_id):
    """Confirmer une commande"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.utils import timezone
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(pk=commande_id)
            
            # Vérifier que la commande est bien affectée à cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                messages.error(request, "Cette commande ne vous est pas affectée.")
                return redirect('operatConfirme:liste_commandes')
            
            # Terminer l'état actuel
            etat_actuel.terminer_etat(operateur)
            
            # Créer un nouvel état "confirmée"
            enum_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_confirmee,
                operateur=operateur,
                commentaire=request.POST.get('commentaire', '')
            )
            
           
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande confirmée'})
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la confirmation : {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
    
    return redirect('operatConfirme:liste_commandes')

@login_required
def marquer_erronnee(request, commande_id):
    """Marquer une commande comme erronée"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.utils import timezone
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(pk=commande_id)
            
            # Vérifier que la commande est bien affectée à cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                messages.error(request, "Cette commande ne vous est pas affectée.")
                return redirect('operatConfirme:liste_commandes')
            
            # Terminer l'état actuel
            etat_actuel.terminer_etat(operateur)
            
            # Créer un nouvel état "erronée"
            enum_erronnee = EnumEtatCmd.objects.get(libelle='Erronée')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_erronnee,
                operateur=operateur,
                commentaire=request.POST.get('motif', '')
            )
            
            messages.success(request, f"Commande {commande.id_yz} marquée comme erronée.")
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande marquée comme erronée'})
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'opération : {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
    
    return redirect('operatConfirme:liste_commandes')

@login_required
def parametre(request):
    """Page des paramètres opérateur confirmation"""
    return render(request, 'operatConfirme/parametre.html')

@login_required
def commandes_confirmees(request):
    """Vue pour afficher les commandes confirmées par l'opérateur connecté"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Vérifier que l'utilisateur est connecté
        if not request.user.is_authenticated:
            from django.contrib import messages
            messages.error(request, 'Vous devez être connecté pour accéder à cette page.')
            return redirect('login')
        
        # Récupérer l'objet Operateur correspondant à l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
        
        # Récupérer seulement les commandes confirmées par cet opérateur
        mes_commandes_confirmees = Commande.objects.filter(
            etats__enum_etat__libelle='Confirmée',
            etats__operateur=operateur  # Inclure même si l'état Confirmée est clôturé
        ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
        

        
        # Tri par date de confirmation (plus récentes en premier)
        mes_commandes_confirmees = mes_commandes_confirmees.order_by('-etats__date_debut')
        
        # Calcul des statistiques
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        stats = {}
        stats['total_confirmees'] = mes_commandes_confirmees.count()
        
        # Valeur totale des commandes confirmées
        valeur_totale = mes_commandes_confirmees.aggregate(
            total=Sum('total_cmd')
        )['total'] or 0
        stats['valeur_totale'] = valeur_totale
        
        # Commandes confirmées cette semaine
        stats['confirmees_semaine'] = mes_commandes_confirmees.filter(
            etats__date_debut__date__gte=week_start,
            etats__enum_etat__libelle='Confirmée'
        ).count()
        
        # Commandes confirmées aujourd'hui
        stats['confirmees_aujourdhui'] = mes_commandes_confirmees.filter(
            etats__date_debut__date=today,
            etats__enum_etat__libelle='Confirmée'
        ).count()
        
    except Operateur.DoesNotExist:
        # Si l'utilisateur n'est pas un opérateur de confirmation, afficher notification JS
        mes_commandes_confirmees = Commande.objects.none()
        stats = {
            'total_confirmees': 0,
            'valeur_totale': 0,
            'confirmees_semaine': 0,
            'confirmees_aujourdhui': 0
        }
        # Ajouter un flag pour déclencher la notification côté client
        context = {
            'mes_commandes_confirmees': mes_commandes_confirmees,
            'stats': stats,
            'show_unauthorized_message': True,
            'user_username': request.user.username
        }
        return render(request, 'operatConfirme/commandes_confirmees.html', context)
    
    context = {
        'mes_commandes_confirmees': mes_commandes_confirmees,
        'stats': stats,
    }
    
    return render(request, 'operatConfirme/commandes_confirmees.html', context)

@login_required
def creer_operateur_confirme(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation de base (vous pouvez ajouter des validations plus robustes ici)
        if not all([username, password, nom, prenom, mail]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})
        
        if User.objects.filter(email=mail).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})

        try:
            # Créer l'utilisateur Django
            user = User.objects.create_user(
                username=username,
                email=mail,
                password=password,
                first_name=prenom,
                last_name=nom
            )
            user.save()

            # Créer le profil Operateur
            operateur = Operateur.objects.create(
                user=user,
                nom=nom,
                prenom=prenom,
                mail=mail,
                type_operateur='CONFIRMATION',
                telephone=telephone,
                adresse=adresse
            )
            operateur.save()

            # Ajouter l'utilisateur au groupe 'operateur_confirme'
            group, created = Group.objects.get_or_create(name='operateur_confirme')
            user.groups.add(group)

            messages.success(request, f"L'opérateur de confirmation {prenom} {nom} a été créé avec succès.")
            return redirect('app_admin:liste_operateurs') # Rediriger vers la liste des opérateurs

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'opérateur : {e}")
            # Si l'utilisateur a été créé mais pas l'opérateur, le supprimer pour éviter les orphelins
            if 'user' in locals() and user.pk: 
                user.delete()
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})

    return render(request, 'composant_generale/creer_operateur.html')

@login_required
def profile_confirme(request):
    """Page de profil pour l'opérateur de confirmation"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur non trouvé.")
        return redirect('login') # Rediriger vers la page de connexion ou une page d'erreur
    return render(request, 'operatConfirme/profile.html', {'operateur': operateur})

@login_required
def modifier_profile_confirme(request):
    """Page de modification de profil pour l'opérateur de confirmation"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur non trouvé.")
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation de base
        if not all([first_name, last_name, email]):
            messages.error(request, "Le prénom, le nom et l'email sont obligatoires.")
            return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})

        # Vérifier si l'email est déjà utilisé par un autre utilisateur (sauf l'utilisateur actuel)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "Cet email est déjà utilisé par un autre compte.")
            return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})
        
        try:
            # Mettre à jour l'objet User
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            # Mettre à jour l'objet Operateur
            operateur.nom = last_name # Mettre à jour le nom de famille de l'opérateur
            operateur.prenom = first_name # Mettre à jour le prénom de l'opérateur
            operateur.mail = email
            operateur.telephone = telephone
            operateur.adresse = adresse
            # Gérer le téléchargement de la photo
            if 'photo' in request.FILES:
                operateur.photo = request.FILES['photo']
            elif request.POST.get('photo-clear'): # Si une case à cocher pour supprimer la photo est présente
                operateur.photo = None

            # Ne pas modifier type_operateur ou actif
            operateur.save()

            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('operatConfirme:profile')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la mise à jour : {e}")

    return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})

@login_required
def changer_mot_de_passe_confirme(request):
    """Page de changement de mot de passe pour l'opérateur de confirmation - Désactivée"""
    return redirect('operatConfirme:profile')

@login_required
def detail_commande(request, commande_id):
    """Aperçu détaillé d'une commande avec possibilité de modification"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande avec toutes les relations
    commande = get_object_or_404(
        Commande.objects.select_related(
            'client', 'ville', 'ville__region'
        ).prefetch_related(
            'paniers__article', 'etats__enum_etat', 'etats__operateur'
        ),
        pk=commande_id
    )
    
    # Vérifier que la commande est bien affectée à cet opérateur
    etat_actuel = commande.etats.filter(
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_actuel:
        messages.error(request, "Cette commande ne vous est pas affectée.")
        return redirect('operatConfirme:liste_commandes')
    
    # Traitement de la modification si POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'modifier_commande':
            # Modifier les champs modifiables
            nouvelle_adresse = request.POST.get('adresse', '').strip()
            nouveau_telephone = request.POST.get('telephone', '').strip()
            commentaire = request.POST.get('commentaire', '').strip()
            
            # Mise à jour des champs
            if nouvelle_adresse:
                commande.adresse = nouvelle_adresse
            
            if nouveau_telephone:
                commande.client.numero_tel = nouveau_telephone
                commande.client.save()
            
            commande.save()
            
            # Ajouter un commentaire si fourni
            if commentaire:
                etat_actuel.commentaire = commentaire
                etat_actuel.save()
            
            messages.success(request, "Commande mise à jour avec succès.")
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande mise à jour'})
        
        elif action == 'confirmer':
            return confirmer_commande(request, commande_id)
        
        elif action == 'marquer_erronnee':
            return marquer_erronnee(request, commande_id)
    
    # Calculer le sous-total des articles
    total_articles = sum(panier.sous_total for panier in commande.paniers.all())
    
    context = {
        'commande': commande,
        'etat_actuel': etat_actuel,
        'operateur': operateur,
        'total_articles': total_articles,
        'historique_etats': commande.historique_etats
    }
    
    return render(request, 'operatConfirme/detail_commande.html', context)

@login_required
def confirmation(request):
    """Page dédiée à la confirmation des commandes"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.http import JsonResponse
    from django.utils import timezone
    from django.core.paginator import Paginator
    from django.db.models import Q
    from common.filter_utils import apply_all_filters, get_filter_context
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer toutes les commandes affectées à cet opérateur qui peuvent être confirmées
    # Inclut tous les états de confirmation possibles
    etats_confirmables = [
        'Affectée',                    # Nouvellement affectées
        'En cours de confirmation',     # En cours de traitement
        'Report de confirmation',       # Report de confirmation (ancien)
              # Report de confirmation (nouveau)           # Commandes non encore affectées mais visibles
    ]
    
    commandes_a_confirmer = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True,  # États actifs (non terminés)
        etats__enum_etat__libelle__in=etats_confirmables
    ).select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'paniers__article', 'etats__enum_etat'
    ).distinct().order_by('-date_cmd', '-date_creation')

    # Recherche
    search_query = request.GET.get('search', '').strip()
    if search_query:
        commandes_a_confirmer = commandes_a_confirmer.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(adresse__icontains=search_query)
        )

    # Appliquer les filtres (date, synchronisation, tri)
    commandes_a_confirmer = apply_all_filters(commandes_a_confirmer, request)

    # Pagination
    paginator = Paginator(commandes_a_confirmer, 15)  # 15 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'operateur': operateur,
        'commandes_a_confirmer': commandes_a_confirmer,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    context.update(get_filter_context(request))

    return render(request, 'operatConfirme/confirmation.html', context)

@login_required
def lancer_confirmations(request):
    """Lance le processus de confirmation automatique pour l'opérateur"""
    from django.http import JsonResponse
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer toutes les commandes affectées à cet opérateur qui sont en attente
            commandes_a_traiter = Commande.objects.filter(
                etats__operateur=operateur,
                etats__date_fin__isnull=True,
                etats__enum_etat__libelle='affectee'
            ).distinct()
            
            # Compteur pour les commandes traitées
            commandes_traitees = 0
            erreurs = []
            
            for commande in commandes_a_traiter:
                try:
                    # Récupérer l'état actuel
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    if etat_actuel:
                        # Terminer l'état actuel
                        etat_actuel.terminer_etat(operateur)
                        
                        # Créer un nouvel état "en cours de confirmation"
                        enum_en_cours = EnumEtatCmd.objects.get_or_create(
                            libelle='en_cours_confirmation',
                            defaults={'ordre': 2, 'couleur': '#3B82F6'}
                        )[0]
                        
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=enum_en_cours,
                            operateur=operateur,
                            commentaire='Processus de confirmation automatique lancé'
                        )
                        
                        commandes_traitees += 1
                        
                except Exception as e:
                    erreurs.append(f"Commande {commande.id_yz}: {str(e)}")
            
            # Préparer la réponse
            if erreurs:
                message = f"{commandes_traitees} commandes traitées avec {len(erreurs)} erreurs."
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'commandes_traitees': commandes_traitees,
                    'erreurs': erreurs
                })
            else:
                message = f"Processus lancé avec succès ! {commandes_traitees} commandes mises en cours de confirmation."
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'commandes_traitees': commandes_traitees
                })
                
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Profil d'opérateur non trouvé."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors du traitement: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def selectionner_operation(request):
    """Vue AJAX pour sélectionner une opération pour une commande"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            commande_id = data.get('commande_id')
            type_operation = data.get('type_operation')
            commentaire = data.get('commentaire', '')
            
            if not commande_id or not type_operation:
                return JsonResponse({
                    'success': False,
                    'message': 'Données manquantes'
                })
            
            # Valider le type d'opération côté serveur
            from commande.models import Operation
            allowed_types = {choice[0] for choice in Operation.TYPE_OPERATION_CHOICES}
            if type_operation not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': 'Type d\'opération non autorisé'
                })

            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(id=commande_id)
            
            # Vérifier que la commande est en cours de confirmation par cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True,
                enum_etat__libelle='En cours de confirmation'
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande n\'est pas en cours de confirmation par vous'
                })
            
            # Supprimer l'ancienne opération si elle existe pour cette commande
            from commande.models import Operation
            Operation.objects.filter(
                commande=commande,
                operateur=operateur,
                type_operation__in=[
                    'AUCUNE_ACTION', 'APPEL_1', 'APPEL_2', 'APPEL_3', 'APPEL_4',
                    'APPEL_5', 'APPEL_6', 'APPEL_7', 'APPEL_8', 'ENVOI_SMS',
                    'ENVOI_MSG', 'PROPOSITION_ABONNEMENT', 'PROPOSITION_REDUCTION'
                ]
            ).delete()
            
            # Créer la nouvelle opération
            conclusion = commentaire if commentaire else f"Opération sélectionnée : {dict(Operation.TYPE_OPERATION_CHOICES)[type_operation]}"
            
            operation = Operation.objects.create(
                commande=commande,
                type_operation=type_operation,
                conclusion=conclusion,
                operateur=operateur
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Opération "{operation.get_type_operation_display()}" sélectionnée',
                'operation_display': operation.get_type_operation_display()
            })
            
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil d\'opérateur non trouvé'
            })
        except Commande.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Commande non trouvée'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def confirmer_commandes_ajax(request):
    """Vue AJAX pour confirmer plusieurs commandes en masse"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commande_ids = data.get('commande_ids', [])
            
            if not commande_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande sélectionnée'
                })
            
            # Vérifier que l'opérateur est bien de type confirmation
            if not hasattr(request.user, 'operateurconfirme'):
                return JsonResponse({
                    'success': False,
                    'message': 'Accès non autorisé'
                })
            
            operateur = request.user.operateurconfirme
            confirmed_count = 0
            
            # État "Confirmée"
            try:
                etat_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "confirmée" non trouvé dans le système'
                })
            
            for commande_id in commande_ids:
                try:
                    # Récupérer la commande
                    commande = Commande.objects.get(
                        id=commande_id,
                        etats__operateur=operateur,
                        etats__date_fin__isnull=True
                    )
                    
                    # Récupérer l'état actuel (non terminé) de cette commande pour cet opérateur
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    if etat_actuel:
                        # Autoriser la confirmation depuis Affectée / En cours / Report de confirmation
                        etat_label = etat_actuel.enum_etat.libelle if etat_actuel and etat_actuel.enum_etat else ''
                        etats_autorises = ['Affectée', 'En cours de confirmation', 'Report de confirmation', 'Reporté de confirmation', 'Retour Confirmation']
                        if etat_label not in etats_autorises:
                            continue
                        # Terminer tous les états actifs précédents de cette commande (sécurité)
                        commande.etats.filter(date_fin__isnull=True).update(date_fin=timezone.now())
                        
                        # Créer le nouvel état "confirmée"
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_confirmee,
                            operateur=operateur,
                            date_debut=timezone.now(),
                            commentaire=f"Commande confirmée via confirmation en masse"
                        )
                        
                        confirmed_count += 1
                
                except Commande.DoesNotExist:
                    continue  # Ignorer les commandes non trouvées
                except Exception as e:
                    continue  # Ignorer les erreurs individuelles
            
            if confirmed_count > 0:
                return JsonResponse({
                    'success': True,
                    'message': f'{confirmed_count} commande(s) confirmée(s) avec succès',
                    'redirect_url': reverse('operatConfirme:confirmation')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande n\'a pu être confirmée'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Données JSON invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de la confirmation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def lancer_confirmation(request, commande_id):
    """Vue pour lancer la confirmation d'une commande (Affectée -> En cours de confirmation)"""
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })
            
            # Vérifier que la commande est dans l'état "Affectée"
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande ne vous est pas affectée'
                })
            
            if etat_actuel.enum_etat.libelle.lower() == 'en cours de confirmation':
                return JsonResponse({
                    'success': True,
                    'message': 'La commande est déjà en cours de confirmation'
                })
            
            if etat_actuel.enum_etat.libelle.lower() != 'affectée':
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est déjà en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être mise en cours de confirmation'
                })
            
            # États requis
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "En cours de confirmation"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_cours,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire="Confirmation lancée par l'opérateur"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Confirmation lancée avec succès pour la commande {commande.id_yz}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du lancement de la confirmation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def lancer_confirmations_masse(request):
    """Vue AJAX pour lancer la confirmation de plusieurs commandes en masse"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commande_ids = data.get('commande_ids', [])
            
            if not commande_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande sélectionnée'
                })
            
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            launched_count = 0
            redirect_url = None
            
            # État "En cours de confirmation"
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            # Si une seule commande est lancée, préparer l'URL de redirection
            if len(commande_ids) == 1:
                redirect_url = reverse('operatConfirme:modifier_commande', args=[commande_ids[0]])

            for commande_id in commande_ids:
                try:
                    # Récupérer la commande
                    commande = Commande.objects.get(
                        id=commande_id,
                        etats__operateur=operateur,
                        etats__date_fin__isnull=True
                    )
                    
                    # Récupérer l'état actuel (non terminé) de cette commande pour cet opérateur
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    # Vérifier que la commande est dans l'état "Affectée"
                    if etat_actuel and etat_actuel.enum_etat.libelle.lower() == 'affectée':
                        # Terminer l'état actuel
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save()
                        
                        # Créer le nouvel état "En cours de confirmation"
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_en_cours,
                            operateur=operateur,
                            date_debut=timezone.now(),
                            commentaire="Confirmation lancée en masse"
                        )
                        
                        launched_count += 1
                
                except Commande.DoesNotExist:
                    continue  # Ignorer les commandes non trouvées
                except Exception as e:
                    continue  # Ignorer les erreurs individuelles
            
            if launched_count > 0:
                response_data = {
                    'success': True,
                    'message': f'{launched_count} confirmation(s) lancée(s) avec succès'
                }
                if redirect_url:
                    response_data['redirect_url'] = redirect_url
                return JsonResponse(response_data)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande n\'a pu être mise en cours de confirmation'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Données JSON invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du lancement: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def annuler_commande_confirmation(request, commande_id):
    """Vue pour annuler définitivement une commande (En cours de confirmation -> Annulée)"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            motif = data.get('motif', '').strip()
            
            if not motif:
                return JsonResponse({
                    'success': False,
                    'message': 'Le motif d\'annulation est obligatoire'
                })
            
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })
            
            # Vérifier que la commande est dans l'état "En cours de confirmation" ou "Affectée"
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande ne vous est pas affectée'
                })
            
            if etat_actuel.enum_etat.libelle.lower() == 'annulée':
                return JsonResponse({
                    'success': True,
                    'message': 'La commande est déjà annulée'
                })
            
            # Autoriser l'annulation depuis "En cours de confirmation" ou "Affectée"
            etats_autorises = ['en cours de confirmation', 'affectée','report de confirmation']
            if etat_actuel.enum_etat.libelle.lower() not in etats_autorises:
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être annulée depuis cet état'
                })
            
            # Récupérer ou créer l'état "Annulée"
            etat_annulee, created = EnumEtatCmd.objects.get_or_create(
                libelle='Annulée',
                defaults={'ordre': 70, 'couleur': '#EF4444'}
            )
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "Annulée"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_annulee,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"Commande annulée par l'opérateur de confirmation - Motif: {motif}"
            )
            
            # Sauvegarder le motif d'annulation dans la commande
            commande.motif_annulation = motif
            commande.save()
            
            # Créer une opération d'annulation
            from commande.models import Operation
            Operation.objects.create(
                commande=commande,
                type_operation='ANNULATION',
                conclusion=motif,
                operateur=operateur
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Commande {commande.id_yz} annulée définitivement. Motif: {motif}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de l\'annulation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def reporter_commande_confirmation(request, commande_id):
    """Reporter une commande avec une date de report spécifiée (Affectée/En cours -> Reportée)."""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body) if request.body else request.POST
            motif = (data.get('motif') or '').strip()
            date_report_str = (data.get('date_report') or '').strip()

            if not date_report_str:
                return JsonResponse({
                    'success': False,
                    'message': "La date de report est obligatoire"
                })

            # Parser la date de report (accepte ISO ou 'YYYY-MM-DD HH:MM')
            from datetime import datetime
            try:
                try:
                    date_report = datetime.fromisoformat(date_report_str)
                except ValueError:
                    date_report = datetime.strptime(date_report_str, '%Y-%m-%d %H:%M')
            except Exception:
                return JsonResponse({
                    'success': False,
                    'message': "Format de date invalide. Utilisez ISO (YYYY-MM-DDTHH:MM) ou 'YYYY-MM-DD HH:MM'"
                })

            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': "Profil d'opérateur de confirmation non trouvé"
                })

            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })

            # Vérifier que la commande est dans un état actif pour cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()

            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': "Cette commande ne vous est pas affectée"
                })

            # Autoriser depuis Affectée ou En cours de confirmation (et Retour Confirmation)
            etats_autorises = ['affectée', 'en cours de confirmation', 'retour confirmation']
            if etat_actuel.enum_etat.libelle.lower() not in etats_autorises:
                return JsonResponse({
                    'success': False,
                    'message': f"Cette commande est en état '{etat_actuel.enum_etat.libelle}' et ne peut pas être reportée depuis cet état"
                })

            # Créer (ou récupérer) l'état Reportée
            etat_reportee, _ = EnumEtatCmd.objects.get_or_create(
                libelle='Report de confirmation',
                defaults={'ordre':15, 'couleur':'#6B7280'}
            )
            

            # Fermer l'état actuel et créer l'état Reportée
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()

            nouvel_etat = EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_reportee,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=(motif or 'Commande reportée par l\'opérateur de confirmation'),
                date_fin_delayed=date_report
            )

            return JsonResponse({
                'success': True,
                'message': f"Commande {commande.id_yz} reportée au {date_report.strftime('%d/%m/%Y %H:%M')}",
                'nouvel_etat': 'Reportée'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors du report: {str(e)}"
            })

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

def determiner_type_prix_gele(article, compteur):
    """
    Détermine le type de prix gelé à enregistrer dans le panier.

    PRIORITÉ 1: Les phases spéciales (promotion, liquidation, test) sont TOUJOURS gelées,
                même pour les articles upsell.

    PRIORITÉ 2: Les articles upsell en phase normale → enregistrer le niveau upsell actuel
                basé sur le compteur au moment de la création du panier.

    PRIORITÉ 3: Les articles normaux en phase normale ont le type 'normal'.
    """
    # PRIORITÉ 1: Phases spéciales et promotions (même pour les articles upsell)
    # Ces types doivent être gelés car ils représentent des prix spéciaux
    if hasattr(article, 'has_promo_active') and article.has_promo_active:
        return 'promotion'
    elif article.phase == 'LIQUIDATION':
        return 'liquidation'
    elif article.phase == 'EN_TEST':
        return 'test'

    # PRIORITÉ 2: Articles upsell en phase normale → enregistrer le niveau selon le compteur
    # Le niveau upsell est gelé au moment de l'ajout du panier
    if article.isUpsell:
        if compteur == 0:
            return 'normal'  # Pas encore de niveau upsell
        elif compteur == 1:
            return 'upsell_niveau_1'
        elif compteur == 2:
            return 'upsell_niveau_2'
        elif compteur == 3:
            return 'upsell_niveau_3'
        elif compteur >= 4:
            return 'upsell_niveau_4'
        else:
            return 'normal'

    # PRIORITÉ 3: Articles normaux en phase normale
    return 'normal'


def mettre_a_jour_types_prix_gele_upsell(commande):
    """
    Met à jour dynamiquement les type_prix_gele de tous les paniers upsell
    en fonction du compteur actuel de la commande.

    Cette fonction doit être appelée après chaque modification du panier qui peut
    impacter le compteur (ajout, suppression, modification de quantité).

    IMPORTANT: Seuls les paniers upsell en phase normale sont mis à jour.
    Les paniers en promotion, liquidation ou test conservent leur type_prix_gele fixe.
    """
    from commande.models import Panier

    # Récupérer tous les paniers upsell de la commande
    paniers_upsell = commande.paniers.filter(article__isUpsell=True)

    for panier in paniers_upsell:
        article = panier.article

        # Recalculer le type_prix_gele basé sur le compteur actuel
        nouveau_type = determiner_type_prix_gele(article, commande.compteur)

        # Mettre à jour uniquement si le type a changé et que ce n'est pas une phase spéciale
        # (les phases spéciales restent figées)
        if nouveau_type != panier.type_prix_gele and nouveau_type not in ['promotion', 'liquidation', 'test']:
            ancien_type = panier.type_prix_gele
            panier.type_prix_gele = nouveau_type
            panier.save(update_fields=['type_prix_gele'])
            print(f"🔄 Panier {panier.id} mis à jour: {ancien_type} → {nouveau_type} (compteur={commande.compteur})")


def _recalculer_remises_apres_changement_compteur(commande):
    """
    Recalcule toutes les remises personnalisées des paniers après un changement de compteur upsell.

    Cette fonction est nécessaire car:
    - Le compteur upsell détermine le prix unitaire effectif
    - Les remises en pourcentage dépendent du prix effectif
    - Quand le compteur change, toutes les remises doivent être recalculées

    Args:
        commande: L'instance de la commande
    """
    from decimal import Decimal
    from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

    # Récupérer tous les paniers avec une remise personnalisée
    paniers_avec_remise = commande.paniers.filter(remise_appliquer=True).prefetch_related('remise_personnalisee')

    for panier in paniers_avec_remise:
        if hasattr(panier, 'remise_personnalisee'):
            remise = panier.remise_personnalisee

            # Recalculer le sous-total basé sur le prix effectif actuel (avec le nouveau compteur)
            prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
            quantite = Decimal(str(panier.quantite))
            sous_total_sans_remise = prix_unitaire_effectif * quantite

            # Mettre à jour le sous_total_remise
            panier.sous_total_remise = float(sous_total_sans_remise)

            # Recalculer le montant de la remise
            montant_remise = remise.calculer_montant_remise()
            remise.montant_applique = float(montant_remise)
            remise.save()

            # Recalculer le sous-total avec remise
            sous_total_avec_remise = sous_total_sans_remise - montant_remise
            panier.sous_total = float(sous_total_avec_remise)
            panier.save()

            print(f"   🏷️ Remise recalculée pour panier {panier.id}: {sous_total_sans_remise} DH - {montant_remise} DH = {sous_total_avec_remise} DH")


def _recalculer_compteur_upsell(commande):
    """
    Recalcule le compteur upsell de la commande et met à jour tous les paniers concernés.

    Cette fonction centralise la logique de recalcul du compteur upsell:
    - Compte les articles upsell dans la commande
    - Applique la règle: compteur = max(0, total_upsell - 1) si total >= 2, sinon 0
    - Met à jour les type_prix_gele de tous les paniers upsell
    - Recalcule tous les totaux
    - Recalcule toutes les remises personnalisées

    Args:
        commande: L'instance de la commande à recalculer
    """
    from django.db.models import Sum

    # Compter la quantité totale d'articles upsell
    total_quantite_upsell = commande.paniers.filter(
        article__isUpsell=True
    ).aggregate(total=Sum('quantite'))['total'] or 0

    # Règle métier: Le compteur s'incrémente à partir de 2 unités d'articles upsell
    # 0-1 unités → compteur = 0
    # 2+ unités → compteur = total - 1
    ancien_compteur = commande.compteur
    if total_quantite_upsell >= 2:
        commande.compteur = total_quantite_upsell - 1
    else:
        commande.compteur = 0

    commande.save()

    # Mettre à jour les type_prix_gele de tous les paniers upsell
    mettre_a_jour_types_prix_gele_upsell(commande)

    # Recalculer tous les totaux
    commande.recalculer_totaux_upsell()

    # Si le compteur a changé, recalculer toutes les remises personnalisées
    if ancien_compteur != commande.compteur:
        print(f"🔄 Compteur upsell changé: {ancien_compteur} → {commande.compteur}")
        _recalculer_remises_apres_changement_compteur(commande)

    print(f"🔄 Compteur upsell recalculé: {commande.compteur} (total articles upsell: {total_quantite_upsell})")


def _handle_add_article(request, commande, operateur):
    """
    Gère l'ajout d'un article à une commande via AJAX.
    
    Cette fonction spécialisée:
    - Gère les articles avec ou sans variantes
    - Évite les doublons (incrémente la quantité si l'article existe)
    - Recalcule automatiquement les compteurs upsell
    - Met à jour tous les totaux
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    from commande.models import Panier
    from article.models import Article, VarianteArticle
    from django.db.models import Sum
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
        if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:
            _recalculer_compteur_upsell(commande)
        
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


def _handle_delete_panier(request, commande, operateur):
    """
    Gère la suppression d'un article du panier via AJAX.
    
    Cette fonction spécialisée:
    - Supprime un article/panier de la commande
    - Recalcule automatiquement les compteurs upsell si nécessaire
    - Met à jour tous les totaux de la commande
    - Retourne les nouvelles valeurs pour mise à jour de l'interface
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
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
            _recalculer_compteur_upsell(commande)
        
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


def _handle_save_client_info(request, commande, operateur):
    """
    Gère la sauvegarde des informations du client via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    # ========== 1. RÉCUPÉRATION DES DONNÉES ==========
    nom = request.POST.get('nom', '').strip()
    prenom = request.POST.get('prenom', '').strip()
    telephone = request.POST.get('telephone', '').strip()
    
    print(f"👤 Sauvegarde infos client: {prenom} {nom}, Tel: {telephone}")
    
    try:
        # ========== 2. MISE À JOUR DU CLIENT ==========
        client = commande.client
        client.nom = nom
        client.prenom = prenom
        client.numero_tel = telephone
        client.save()
        
        # ========== 3. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Informations client sauvegardées avec succès'
        })
    
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des infos client: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def _handle_update_quantity(request, commande, operateur):
    """
    Gère la modification de la quantité d'un article via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
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
        # IMPORTANT: _recalculer_compteur_upsell gère automatiquement le recalcul des remises
        if etait_upsell:
            _recalculer_compteur_upsell(commande)
            # Rafraîchir le panier pour avoir les données à jour
            panier.refresh_from_db()
            commande.refresh_from_db()

        # ========== 6. GESTION DE LA REMISE SI APPLIQUÉE ET SI PAS UPSELL ==========
        # Si c'était un article upsell, la remise a déjà été recalculée dans _recalculer_compteur_upsell
        # On ne recalcule la remise manuellement que pour les articles non-upsell
        from commande.models import RemisePanier
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


def _handle_update_operation(request, commande, operateur):
    """
    Gère la mise à jour d'une opération existante via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    from commande.models import Operation
    import logging
    
    logger = logging.getLogger(__name__)
    
    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    operation_id = request.POST.get('operation_id')
    nouveau_commentaire = request.POST.get('nouveau_commentaire', '').strip()
    
    print(f"🔄 Mise à jour opération {operation_id} pour commande {commande.id}")
    print(f"📝 Nouveau commentaire: '{nouveau_commentaire}'")
    
    if not operation_id or not nouveau_commentaire:
        print(f"❌ Données manquantes - operation_id: '{operation_id}', commentaire: '{nouveau_commentaire}'")
        return JsonResponse({
            'success': False,
            'error': 'ID opération et commentaire requis'
        })
    
    try:
        # ========== 2. RÉCUPÉRATION DE L'OPÉRATION ==========
        try:
            operation = Operation.objects.get(id=operation_id, commande=commande)
        except Operation.DoesNotExist:
            print(f"❌ Opération {operation_id} introuvable pour commande {commande.id}")
            return JsonResponse({
                'success': False,
                'error': 'Opération introuvable'
            })
        
        # ========== 3. SAUVEGARDE DE L'ANCIEN COMMENTAIRE ==========
        ancien_commentaire = operation.conclusion
        print(f"📋 Ancien commentaire: '{ancien_commentaire}'")
        
        # ========== 4. MISE À JOUR DE L'OPÉRATION ==========
        operation.conclusion = nouveau_commentaire
        operation.operateur = operateur  # Mettre à jour l'opérateur qui modifie
        operation.save()
        
        print(f"✅ Opération {operation_id} sauvegardée en base de données")
        
        # ========== 5. VÉRIFICATION POST-SAUVEGARDE ==========
        operation_verif = Operation.objects.get(id=operation_id)
        print(f"🔍 Vérification en base: conclusion = '{operation_verif.conclusion}'")
        
        # ========== 6. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Opération mise à jour avec succès',
            'operation_id': operation_id,
            'nouveau_commentaire': nouveau_commentaire,
            'ancien_commentaire': ancien_commentaire,
            'debug_info': {
                'verification_conclusion': operation_verif.conclusion,
                'total_operations': Operation.objects.filter(commande=commande).count()
            }
        })
    
    except Exception as e:
        print(f"❌ Erreur mise à jour opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def _handle_create_operation(request, commande, operateur):
    """
    Gère la création d'une nouvelle opération via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    from commande.models import Operation
    
    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    type_operation = request.POST.get('type_operation')
    commentaire = request.POST.get('commentaire', '').strip()
    
    print(f"🆕 Création nouvelle opération pour commande {commande.id}")
    print(f"📝 Type: '{type_operation}', Commentaire: '{commentaire}'")
    
    if not type_operation or not commentaire:
        print(f"❌ Données manquantes - type: '{type_operation}', commentaire: '{commentaire}'")
        return JsonResponse({
            'success': False,
            'error': 'Type d\'opération et commentaire requis'
        })
    
    try:
        # ========== 2. VALIDATION DU TYPE D'OPÉRATION ==========
        allowed_types = {choice[0] for choice in Operation.TYPE_OPERATION_CHOICES}
        if type_operation not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': "Type d'opération non autorisé"
            })
        
        # ========== 3. CRÉATION DE LA NOUVELLE OPÉRATION ==========
        nouvelle_operation = Operation.objects.create(
            type_operation=type_operation,
            conclusion=commentaire,
            commande=commande,
            operateur=operateur
        )
        
        print(f"✅ Nouvelle opération créée avec ID: {nouvelle_operation.id}")
        
        # ========== 4. VÉRIFICATION POST-CRÉATION ==========
        toutes_operations = Operation.objects.filter(commande=commande)
        print(f"📊 {toutes_operations.count()} opération(s) totales pour cette commande")
        
        # ========== 5. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': 'Nouvelle opération créée avec succès',
            'operation_id': nouvelle_operation.id,
            'type_operation': nouvelle_operation.type_operation,
            'commentaire': nouvelle_operation.conclusion,
            'debug_info': {
                'total_operations': toutes_operations.count(),
                'operation_date': nouvelle_operation.date_operation.strftime('%d/%m/%Y %H:%M')
            }
        })
    
    except Exception as e:
        print(f"❌ Erreur création opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def _handle_delete_operation(request, commande, operateur):
    """
    Gère la suppression d'une opération via AJAX.

    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action

    Returns:
        JsonResponse avec le statut de l'opération
    """
    from commande.models import Operation
    import logging

    logger = logging.getLogger(__name__)

    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    operation_id = request.POST.get('operation_id')

    print(f"🗑️ Suppression opération {operation_id} pour commande {commande.id}")

    if not operation_id:
        print(f"❌ Données manquantes - operation_id: '{operation_id}'")
        return JsonResponse({
            'success': False,
            'error': 'ID opération requis'
        })

    try:
        # ========== 2. RÉCUPÉRATION DE L'OPÉRATION ==========
        try:
            operation = Operation.objects.get(
                id=operation_id,
                commande=commande
            )
            print(f"✅ Opération {operation_id} trouvée: {operation.type_operation}")
        except Operation.DoesNotExist:
            print(f"❌ Opération {operation_id} introuvable pour commande {commande.id}")
            return JsonResponse({
                'success': False,
                'error': 'Opération introuvable'
            })

        # ========== 3. SAUVEGARDE DES INFORMATIONS AVANT SUPPRESSION ==========
        operation_info = {
            'id': operation.id,
            'type_operation': operation.type_operation,
            'conclusion': operation.conclusion,
            'date_operation': operation.date_operation.strftime('%d/%m/%Y %H:%M')
        }

        print(f"📋 Informations de l'opération à supprimer:")
        print(f"   - Type: {operation_info['type_operation']}")
        print(f"   - Conclusion: {operation_info['conclusion']}")
        print(f"   - Date: {operation_info['date_operation']}")

        # ========== 4. SUPPRESSION DE L'OPÉRATION ==========
        operation.delete()
        print(f"✅ Opération {operation_id} supprimée avec succès")

        # ========== 5. VÉRIFICATION POST-SUPPRESSION ==========
        operations_restantes = Operation.objects.filter(commande=commande)
        print(f"📊 {operations_restantes.count()} opération(s) restante(s) pour cette commande")

        # ========== 6. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': f'Opération {operation_info["type_operation"]} supprimée avec succès',
            'operation_deleted': operation_info,
            'debug_info': {
                'total_operations_restantes': operations_restantes.count(),
            }
        })

    except Exception as e:
        print(f"❌ Erreur suppression opération: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def _handle_save_livraison(request, commande, operateur):
    """
    Gère la sauvegarde des informations de livraison via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    from parametre.models import Ville
    
    # ========== 1. RÉCUPÉRATION DES DONNÉES ==========
    ville_id = request.POST.get('ville_livraison')
    adresse = request.POST.get('adresse_livraison', '').strip()
    
    print(f"🚚 Sauvegarde livraison: Ville ID={ville_id}, Adresse={adresse[:50] if adresse else 'N/A'}")
    
    try:
        # ========== 2. MISE À JOUR DE LA VILLE ==========
        if ville_id:
            try:
                nouvelle_ville = Ville.objects.get(id=ville_id)
                commande.ville = nouvelle_ville
            except Ville.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Ville de livraison invalide'
                })
        
        # ========== 3. MISE À JOUR DE L'ADRESSE ==========
        commande.adresse = adresse
        
        # ========== 4. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()
        
        # ========== 5. SAUVEGARDE ==========
        commande.save()
        
        # ========== 6. PRÉPARATION DU MESSAGE DE SUCCÈS ==========
        elements_sauvegardes = []
        if ville_id:
            elements_sauvegardes.append(f"ville: {commande.ville.nom}")
        if adresse:
            elements_sauvegardes.append(f"adresse: {adresse[:50]}{'...' if len(adresse) > 50 else ''}")
        
        if elements_sauvegardes:
            message = f"Informations de livraison sauvegardées ({', '.join(elements_sauvegardes)})"
        else:
            message = 'Section livraison validée'
        
        # ========== 7. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': message,
            'ville_nom': commande.ville.nom if commande.ville else None,
            'region_nom': commande.ville.region.nom_region if commande.ville and commande.ville.region else None,
            'frais_livraison': commande.montant_frais_livraison,
            'adresse': adresse,
            'nouveau_total': commande.total_cmd,
            'sous_total_articles': commande.sous_total_articles
        })
    
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de la livraison: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


def _handle_toggle_frais_livraison(request, commande, operateur):
    """
    Gère l'activation/désactivation des frais de livraison via AJAX.
    
    Args:
        request: L'objet HttpRequest contenant les données POST
        commande: L'instance de la commande à modifier
        operateur: L'opérateur effectuant l'action
    
    Returns:
        JsonResponse avec le statut de l'opération
    """
    # ========== 1. RÉCUPÉRATION ET VALIDATION DES DONNÉES ==========
    nouveau_statut = request.POST.get('frais_livraison_actif') == 'true'
    ancien_statut = commande.frais_livraison
    
    print(f"💰 Toggle frais de livraison: {ancien_statut} → {nouveau_statut}")
    
    try:
        # ========== 2. MISE À JOUR DU STATUT ==========
        commande.frais_livraison = nouveau_statut
        commande.save()
        
        # ========== 3. RECALCUL DU TOTAL AVEC FRAIS ==========
        commande.recalculer_total_avec_frais()
        
        # ========== 4. PRÉPARATION DU MESSAGE ET DES INFOS D'AFFICHAGE ==========
        if nouveau_statut:
            message = "Frais de livraison activés et inclus dans le total"
            statut_display = "Activés"
            couleur = "green"
        else:
            message = "Frais de livraison désactivés et retirés du total"
            statut_display = "Désactivés"
            couleur = "gray"
        
        # ========== 5. RÉPONSE JSON ==========
        return JsonResponse({
            'success': True,
            'message': message,
            'nouveau_statut': nouveau_statut,
            'statut_display': statut_display,
            'couleur': couleur,
            'total_commande': float(commande.total_cmd),
            'frais_livraison_ville': float(commande.montant_frais_livraison),
            'ancien_statut': ancien_statut
        })
    
    except Exception as e:
        print(f"❌ Erreur lors du toggle des frais de livraison: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        })


@login_required
def modifier_commande(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de confirmation"""
    from commande.models import Commande, Operation, Panier
    from parametre.models import Ville
    from article.models import Article, VarianteArticle
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
        
    # Vérifier que la commande est affectée à cet opérateur
    etat_actuel = commande.etats.filter(
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_actuel:
        messages.error(request, "Cette commande ne vous est pas affectée.")
        return redirect('operatConfirme:confirmation')
    
    if request.method == 'POST':
        try:
            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================
            action = request.POST.get('action')
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            print(f"🔍 DEBUG: POST reçu - Action: {action}, AJAX: {is_ajax}")
            
            # Si c'est une requête AJAX sans action reconnue, retourner une erreur JSON
            if is_ajax and not action:
                return JsonResponse({'success': False, 'error': 'Action non spécifiée'})
            
            if is_ajax and action not in ['add_article', 'update_ville', 'toggle_frais_livraison', 'remove_article', 'update_article_complet', 'save_livraison', 'update_quantity', 'delete_panier', 'save_client_info', 'update_operation', 'create_operation', 'delete_operation']:
                return JsonResponse({'success': False, 'error': f'Action non reconnue: {action}'})
            
            # ================ ACTIONS AJAX INDIVIDUELLES ================
            
            if action == 'add_article':
                # Déléguer à la fonction spécialisée
                return _handle_add_article(request, commande, operateur)
            
            elif action == 'delete_panier':
                # Déléguer à la fonction spécialisée
                return _handle_delete_panier(request, commande, operateur)
            
            elif action == 'save_client_info':
                # Déléguer à la fonction spécialisée
                return _handle_save_client_info(request, commande, operateur)
            
            elif action == 'update_quantity':
                # Déléguer à la fonction spécialisée
                return _handle_update_quantity(request, commande, operateur)
            
            elif action == 'update_operation':
                # Déléguer à la fonction spécialisée
                return _handle_update_operation(request, commande, operateur)
            
            elif action == 'create_operation':
                # Déléguer à la fonction spécialisée
                return _handle_create_operation(request, commande, operateur)

            elif action == 'delete_operation':
                # Déléguer à la fonction spécialisée
                return _handle_delete_operation(request, commande, operateur)

            elif action == 'save_livraison':
                # Déléguer à la fonction spécialisée
                return _handle_save_livraison(request, commande, operateur)
            
            elif action == 'toggle_frais_livraison':
                # Déléguer à la fonction spécialisée
                return _handle_toggle_frais_livraison(request, commande, operateur)
            
            # ================ TRAITEMENT NORMAL DU FORMULAIRE ================
            
            # Mise à jour des informations client
            commande.client.nom = request.POST.get('client_nom', '').strip()
            commande.client.prenom = request.POST.get('client_prenom', '').strip()
            commande.client.numero_tel = request.POST.get('client_telephone', '').strip()
            commande.client.save()
            
            # Mise à jour de la date de commande
            date_cmd = request.POST.get('date_cmd')
            if date_cmd:
                from datetime import datetime
                commande.date_cmd = datetime.strptime(date_cmd, '%Y-%m-%d').date()
            
            # Mise à jour de la ville et de l'adresse
            ville_id = request.POST.get('ville_livraison')
            if ville_id:
                nouvelle_ville = Ville.objects.get(id=ville_id)
                commande.ville = nouvelle_ville
            
            adresse = request.POST.get('adresse_livraison', '').strip()
            if adresse:
                commande.adresse = adresse
            
            # Mise à jour du champ upsell
            is_upsell = request.POST.get('is_upsell', 'false')
            commande.is_upsell = (is_upsell == 'true')
            
            # ================ GESTION DES ARTICLES/PANIERS ================
            
            # 1. Gestion des articles supprimés
            articles_supprimes = request.POST.getlist('deleted_articles[]')
            if articles_supprimes:
                from commande.models import Panier
                for panier_id in articles_supprimes:
                    try:
                        panier = Panier.objects.get(id=panier_id, commande=commande)
                        panier.delete()
                    except Panier.DoesNotExist:
                        pass
            
            # 2. Gestion des articles modifiés
            articles_modifies = request.POST.getlist('modified_articles[]')
            nouvelles_quantites = request.POST.getlist('modified_quantities[]')
            
            if articles_modifies and nouvelles_quantites:
                from commande.models import Panier
                for i, panier_id in enumerate(articles_modifies):
                    if i < len(nouvelles_quantites):
                        try:
                            panier = Panier.objects.get(id=panier_id, commande=commande)
                            nouvelle_quantite = int(nouvelles_quantites[i])
                            if nouvelle_quantite > 0:
                                # INTÉGRITÉ: Le prix_panier est un prix historique gelé
                                # On ne modifie QUE la quantité et le sous-total
                                # Le prix_panier reste INCHANGÉ pour préserver l'historique des prix
                                panier.quantite = nouvelle_quantite
                                panier.sous_total = float(panier.prix_panier * nouvelle_quantite)
                                panier.save()
                        except (Panier.DoesNotExist, ValueError):
                            continue
            
            # 3. Gestion des nouveaux articles
            nouveaux_articles = request.POST.getlist('new_articles[]')
            quantites_nouveaux = request.POST.getlist('new_quantities[]')
            
            if nouveaux_articles and quantites_nouveaux:
                from article.models import Article
                from commande.models import Panier
                
                for i, article_id in enumerate(nouveaux_articles):
                    if i < len(quantites_nouveaux):
                        try:
                            article = Article.objects.get(id=article_id)
                            quantite = int(quantites_nouveaux[i])
                            if quantite > 0:
                                # Utiliser la logique upsell pour calculer le prix_panier
                                from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                                prix_panier = get_prix_upsell_avec_compteur(article, commande.compteur)
                                sous_total = float(prix_panier * quantite)

                                # Déterminer le type de prix gelé
                                type_prix = determiner_type_prix_gele(article, commande.compteur)

                                Panier.objects.create(
                                    commande=commande,
                                    article=article,
                                    quantite=quantite,
                                    prix_panier=float(prix_panier),
                                    sous_total=sous_total,
                                    type_prix_gele=type_prix
                                )
                        except (Article.DoesNotExist, ValueError):
                            continue
            
            # 4. Recalculer le total de la commande avec les frais de livraison
            commande.recalculer_total_avec_frais()
            
            # ================ GESTION DES OPÉRATIONS ================
            
            # Gestion des opérations individuelles avec commentaires spécifiques
            operations_selectionnees = request.POST.getlist('operations[]')
            operations_creees = []
            
            for type_operation in operations_selectionnees:
                if type_operation:  # Vérifier que le type n'est pas vide
                    # Récupérer le commentaire spécifique à cette opération
                    commentaire_specifique = request.POST.get(f'comment_{type_operation}', '').strip()
                    
                    # L'opérateur DOIT saisir un commentaire - pas de commentaire automatique
                    if commentaire_specifique:
                        # Créer l'opération avec le commentaire saisi par l'opérateur
                        operation = Operation.objects.create(
                            type_operation=type_operation,
                            conclusion=commentaire_specifique,
                            commande=commande,
                            operateur=operateur
                        )
                        operations_creees.append(operation)
                    else:
                        # Ignorer l'opération si aucun commentaire n'est fourni
                        messages.warning(request, f"Opération {type_operation} ignorée : aucun commentaire fourni par l'opérateur.")
            
            # Messages de succès
            messages_success = []
            if operations_creees:
                operations_names = [op.get_type_operation_display() for op in operations_creees]
                messages_success.append(f'Opérations ajoutées : {", ".join(operations_names)}')
            
            # Compter les modifications d'articles
            nb_articles_modifies = len(articles_supprimes) + len(articles_modifies) + len(nouveaux_articles)
            if nb_articles_modifies > 0:
                messages_success.append(f'{nb_articles_modifies} modification(s) d\'articles appliquée(s)')
            
            # Vérifier si c'est une requête AJAX pour la sauvegarde automatique
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                # Réponse JSON pour les requêtes AJAX
                response_data = {
                    'success': True,
                    'message': 'Modifications sauvegardées avec succès',
                    'total_commande': float(commande.total_cmd),
                    'nb_articles': commande.paniers.count(),
                }
                
                if operations_creees:
                    operations_names = [op.get_type_operation_display() for op in operations_creees]
                    response_data['operations_ajoutees'] = operations_names
                
                if nb_articles_modifies > 0:
                    response_data['articles_modifies'] = nb_articles_modifies
                
                return JsonResponse(response_data)
            else:
                # Réponse normale avec redirect pour les soumissions manuelles
                if messages_success:
                    messages.success(request, f'Commande modifiée avec succès. {" | ".join(messages_success)}')
                else:
                    messages.success(request, 'Commande modifiée avec succès.')
                    
                return redirect('operatConfirme:modifier_commande', commande_id=commande_id)
            
        except Exception as e:
            print(f"❌ ERREUR GLOBALE dans modifier_commande: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f'Erreur serveur: {str(e)}'})
            else:
                messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    # Récupérer toutes les villes pour la liste déroulante
    villes = Ville.objects.select_related('region').order_by('nom')
    
    # Récupérer tous les articles pour le modal d'ajout
    articles = Article.objects.filter(actif=True).order_by('nom')
    
    # Préparer les données JSON pour les articles (comme dans l'interface de création)
    articles_data = []
    for article in articles:
        # Déterminer l'URL de l'image (priorité à l'image locale)
        image_url = ''
        if article.image:
            # Construire l'URL complète pour l'image locale
            from django.conf import settings
            image_url = f"{settings.MEDIA_URL}{article.image.name}"
        elif article.image_url:
            image_url = article.image_url
            
        articles_data.append({
            'id': article.pk,
            'nom': str(article.nom or ''),
            'reference': str(article.reference or ''),
            'prix_actuel': float(article.prix_actuel) if article.prix_actuel else 0.0,
            'prix_unitaire': float(article.prix_unitaire) if article.prix_unitaire else 0.0,
            'prix_upsell_1': float(article.prix_upsell_1) if article.prix_upsell_1 else 0.0,
            'prix_upsell_2': float(article.prix_upsell_2) if article.prix_upsell_2 else 0.0,
            'prix_upsell_3': float(article.prix_upsell_3) if article.prix_upsell_3 else 0.0,
            'prix_upsell_4': float(article.prix_upsell_4) if article.prix_upsell_4 else 0.0,
            'qte_disponible': int(article.get_total_qte_disponible()),
            'couleur': str(article.couleur or ''),
            'pointure': str(article.pointure or ''),
            'categorie': str(article.categorie) if hasattr(article, 'categorie') and article.categorie else '',
            'phase': str(article.phase or ''),
            'has_promo_active': bool(article.has_promo_active),
            'isUpsell': bool(article.isUpsell),
            'image_url': image_url
        })
    
    context = {
        'commande': commande,
        'operateur': operateur,
        'villes': villes,
        'articles_json': articles_data,
    }
    
    return render(request, 'operatConfirme/modifier_commande.html', context)

@login_required
def api_operations_commande(request, commande_id):
    """API pour récupérer les opérations d'une commande mises à jour"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
        
        # Récupérer la commande
        commande = Commande.objects.get(id=commande_id)
        
        # Récupérer toutes les opérations de cette commande
        operations = commande.operations.all().order_by('date_operation')
        
        operations_data = []
        for operation in operations:
            # Déterminer la classe CSS selon le type d'opération
            if operation.type_operation == "APPEL":
                classe_css = 'bg-blue-100 text-blue-800'
            elif operation.type_operation == "ENVOI_SMS":
                classe_css = 'bg-green-100 text-green-800'
            elif "Whatsapp" in operation.type_operation:
                classe_css = 'bg-emerald-100 text-emerald-800'
            else:
                classe_css = 'bg-gray-100 text-gray-800'
            
            # Déterminer le type principal
            if operation.type_operation == "APPEL":
                type_principal = 'APPEL'
            elif operation.type_operation == "ENVOI_SMS":
                type_principal = 'SMS'
            elif "Whatsapp" in operation.type_operation:
                type_principal = 'WHATSAPP'
            else:
                type_principal = 'OTHER'
            
            operations_data.append({
                'id': operation.id,
                'type_operation': operation.type_operation,
                'nom_display': operation.get_type_operation_display(),
                'classe_css': classe_css,
                'date_operation': operation.date_operation.strftime('%d/%m/%Y %H:%M'),
                'conclusion': operation.conclusion or '',
                'type_principal': type_principal
            })
        
        return JsonResponse({
            'success': True,
            'operations': operations_data,
            'count': len(operations_data)
        })
        
    except Operateur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Utilisateur non autorisé'
        })
    except Commande.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Commande introuvable'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def api_articles_disponibles(request):
    try:
        # Récupérer tous les articles disponibles
        articles = Article.objects.filter(
            actif=True, 
        ).order_by('nom')
        
        # Préparer les données des articles
        articles_data = []
        for article in articles:
            # Mettre à jour le prix actuel si nécessaire
            if article.prix_actuel is None:
                article.prix_actuel = article.prix_unitaire
                article.save(update_fields=['prix_actuel'])
            
            # S'assurer que qte_disponible est bien un entier
            stock = article.qte_disponible
            if stock is None:
                stock = 0
            
            # Déterminer l'URL de l'image
            image_url = None
            if article.image:
                # Construire l'URL complète pour l'image locale
                from django.conf import settings
                image_url = f"{settings.MEDIA_URL}{article.image.name}"
            elif article.image_url:
                image_url = article.image_url
            
            articles_data.append({
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference or '',
                'pointure': article.pointure or '',
                'couleur': article.couleur or '',
                'categorie': (str(article.categorie) if article.categorie else ''),
                'prix_unitaire': float(article.prix_unitaire),
                'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                'prix_upsell_1': float(article.prix_upsell_1) if article.prix_upsell_1 else None,
                'prix_upsell_2': float(article.prix_upsell_2) if article.prix_upsell_2 else None,
                'prix_upsell_3': float(article.prix_upsell_3) if article.prix_upsell_3 else None,
                'prix_upsell_4': float(article.prix_upsell_4) if article.prix_upsell_4 else None,
                'qte_disponible': stock,
                'isUpsell': bool(article.isUpsell),
                'phase': article.phase,
                'has_promo_active': article.has_promo_active,
                'description': article.description or '',
                'image_url': image_url,
            })
        
        return JsonResponse(articles_data, safe=False)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False, 
            'error': 'Impossible de charger les articles. Veuillez réessayer.',
            'details': str(e)
        }, status=500)

@login_required
def api_commentaires_disponibles(request):
    """API pour récupérer la liste des commentaires prédéfinis depuis le modèle"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'GET':
        from commande.models import Operation
        
        # Récupérer les choix de commentaires depuis le modèle
        commentaires_choices = Operation.Type_Commentaire_CHOICES
        
        print(f"🔍 DEBUG: Type_Commentaire_CHOICES récupéré: {commentaires_choices}")
        print(f"📊 DEBUG: Nombre de choix: {len(commentaires_choices)}")
        
        # Convertir en format utilisable par le frontend
        commentaires_data = {
            'APPEL': [],
            'ENVOI_SMS': [],
            'Appel Whatsapp': [],
            'Message Whatsapp': [],
            'Vocal Whatsapp': []
        }
        
        # Tous les commentaires sont utilisables pour tous les types d'opérations
        for choice_value, choice_label in commentaires_choices:
            commentaire_item = {
                'value': choice_value,
                'label': choice_label
            }
            
            # Ajouter le commentaire à tous les types d'opérations
            for type_operation in commentaires_data.keys():
                commentaires_data[type_operation].append(commentaire_item)
        
        print(f"✅ DEBUG: Commentaires formatés: {commentaires_data}")
        print(f"📝 DEBUG: Nombre de commentaires par type:")
        for type_op, comments in commentaires_data.items():
            print(f"   - {type_op}: {len(comments)} commentaires")
        
        return JsonResponse({
            'success': True,
            'commentaires': commentaires_data
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def creer_commande(request):
    """Créer une nouvelle commande - Interface opérateur de confirmation"""
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Récupérer les données du formulaire
                type_client = request.POST.get('type_client')
                ville_id = request.POST.get('ville_livraison')
                adresse = request.POST.get('adresse', '').strip()
                total_cmd = request.POST.get('total_cmd', 0)
                source = request.POST.get('source')
                payement = request.POST.get('payement', 'Non payé')
                frais_livraison_actif = request.POST.get('frais_livraison_actif', '').lower() == 'true'

                # Log des données reçues
                logging.info(f"Données de création de commande reçues: type_client={type_client}, ville_id={ville_id}, adresse={adresse}, total_cmd={total_cmd}, frais_livraison_actif={frais_livraison_actif}")

                # Valider la présence de la ville et de l'adresse
                if not ville_id or not adresse:
                    messages.error(request, "Veuillez sélectionner une ville et fournir une adresse.")
                    return redirect('operatConfirme:creer_commande')

                # Gérer le client selon le type
                if type_client == 'existant':
                    client_id = request.POST.get('client')
                    if not client_id:
                        messages.error(request, "Veuillez sélectionner un client existant.")
                        return redirect('operatConfirme:creer_commande')
                    client = get_object_or_404(Client, pk=client_id)
                else:  # nouveau client
                    # Récupérer les données du nouveau client
                    nouveau_prenom = request.POST.get('nouveau_prenom', '').strip()
                    nouveau_nom = request.POST.get('nouveau_nom', '').strip()
                    nouveau_telephone = request.POST.get('nouveau_telephone', '').strip()
                    nouveau_email = request.POST.get('nouveau_email', '').strip()

                    # Validation des champs obligatoires pour nouveau client
                    if not all([nouveau_prenom, nouveau_nom, nouveau_telephone]):
                        messages.error(request, "Veuillez remplir tous les champs obligatoires du nouveau client (prénom, nom, téléphone).")
                        return redirect('operatConfirme:creer_commande')

                    # Vérifier si le téléphone existe déjà
                    if Client.objects.filter(numero_tel=nouveau_telephone).exists():
                        messages.warning(request, f"Un client avec le numéro {nouveau_telephone} existe déjà. Utilisez 'Client existant' ou modifiez le numéro.")
                        return redirect('operatConfirme:creer_commande')

                    # Créer le nouveau client
                    client = Client.objects.create(
                        prenom=nouveau_prenom,
                        nom=nouveau_nom,
                        numero_tel=nouveau_telephone,
                        email=nouveau_email if nouveau_email else None,
                        is_active=True
                    )

                ville = get_object_or_404(Ville, pk=ville_id)

                # Créer la commande (total sera calculé après ajout des articles)
                try:
                    commande = Commande.objects.create(
                        client=client,
                        ville=ville,
                        adresse=adresse,
                        total_cmd=0,  # Sera calculé après ajout des articles
                        origine='OC',  # Définir l'origine comme Opérateur Confirmation
                        source=source,
                        payement=payement,
                        frais_livraison=frais_livraison_actif
                    )
                except Exception as e:
                    logging.error(f"Erreur lors de la création de la commande: {str(e)}")
                    messages.error(request, f"Impossible de créer la commande: {str(e)}")
                    return redirect('operatConfirme:creer_commande')

                # Traiter le panier et calculer le total (même logique que l'interface admin)
                total_calcule = 0.0
                article_counter = 0
                
                while f'article_{article_counter}' in request.POST:
                    article_id = request.POST.get(f'article_{article_counter}')
                    variante_id = request.POST.get(f'variante_{article_counter}')
                    quantite = request.POST.get(f'quantite_{article_counter}')
                    
                    if article_id and quantite:
                        try:
                            quantite = int(quantite)
                            if quantite > 0:
                                article = Article.objects.get(pk=article_id)

                                # Gérer la variante si elle est spécifiée
                                variante = None
                                if variante_id:
                                    try:
                                        variante = VarianteArticle.objects.get(pk=variante_id, article=article)
                                        # Utiliser le prix de la variante si disponible
                                        prix_a_utiliser = float(variante.prix_actuel if variante.prix_actuel is not None else article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire)
                                        logging.info(f"Variante {variante.id} - Article {article.id}: prix_variante={variante.prix_actuel}, prix_utilisé={prix_a_utiliser}")
                                    except VarianteArticle.DoesNotExist:
                                        logging.warning(f"Variante {variante_id} non trouvée pour l'article {article_id}")
                                        variante = None
                                        prix_a_utiliser = float(article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire)
                                else:
                                    # Pas de variante, utiliser le prix de l'article
                                    prix_a_utiliser = float(article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire)

                                # Log pour comprendre le calcul du prix
                                logging.info(f"Article {article.id}, Variante {variante.id if variante else 'N/A'}: prix_utilisé={prix_a_utiliser}")

                                sous_total = float(prix_a_utiliser * quantite)
                                total_calcule += sous_total

                                # Déterminer le type de prix gelé
                                type_prix = determiner_type_prix_gele(article, commande.compteur)

                                Panier.objects.create(
                                    commande=commande,
                                    article=article,
                                    variante=variante,
                                    quantite=quantite,
                                    prix_panier=float(prix_a_utiliser),
                                    sous_total=float(sous_total),
                                    type_prix_gele=type_prix
                                )

                        except (ValueError, Article.DoesNotExist) as e:
                            logging.error(f"Erreur lors de l'ajout d'un article: {str(e)}")
                            messages.error(request, f"Erreur lors de l'ajout d'un article : {e}")
                            raise e # Annule la transaction
                    
                    article_counter += 1
                
                logging.info(f"Articles traités: {article_counter}, Total calculé: {total_calcule}")

                # Mettre à jour le total final de la commande avec le montant recalculé
                commande.total_cmd = float(total_calcule)

                # Recalculer le compteur en fonction du nombre total d'articles upsell
                from django.db.models import Sum
                total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                    total=Sum('quantite')
                )['total'] or 0

                if total_quantite_upsell >= 2:
                    commande.compteur = total_quantite_upsell - 1
                else:
                    commande.compteur = 0

                commande.save()

                # Mettre à jour les type_prix_gele de tous les paniers upsell
                mettre_a_jour_types_prix_gele_upsell(commande)

                # Recalculer le total avec les frais de livraison si activés
                commande.recalculer_total_avec_frais()

                # Créer l'état initial "Affectée" directement à l'opérateur créateur
                try:
                    etat_affectee = EnumEtatCmd.objects.get(libelle='Affectée')
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_affectee,
                        operateur=operateur,
                        commentaire=f"Commande créée et auto-affectée à {operateur.nom_complet}"
                    )
                except EnumEtatCmd.DoesNotExist:
                    try:
                        etat_initial = EnumEtatCmd.objects.get(libelle='Non affectée')
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_initial,
                            commentaire=f"Commande créée par {operateur.nom_complet}"
                        )
                    except EnumEtatCmd.DoesNotExist:
                        pass # Si aucun état n'existe, créer sans état initial
                
                # Composer le message de succès final adapté au contenu
                if article_counter > 0:
                    message_final = f"Commande YZ-{commande.id_yz} créée avec succès avec {article_counter} article(s) pour un total de {commande.total_cmd:.2f} DH."
                else:
                    message_final = f"Commande YZ-{commande.id_yz} créée avec succès. Vous pouvez ajouter des articles plus tard via la modification."
                
                if type_client != 'existant':
                    message_final = f"Nouveau client '{client.get_full_name}' créé. " + message_final

                messages.success(request, message_final)
                return redirect('operatConfirme:liste_commandes')

        except Exception as e:
            logging.error(f"Erreur critique lors de la création de la commande: {str(e)}")
            messages.error(request, f"Erreur critique lors de la création de la commande: {str(e)}")
            # Rediriger vers le formulaire pour correction
            return redirect('operatConfirme:creer_commande')

    # GET request - afficher le formulaire
    clients = Client.objects.all().order_by('prenom', 'nom')
    articles = Article.objects.all().order_by('nom')
    villes = Ville.objects.select_related('region').order_by('nom')

    # Préparer les données JSON pour les articles (comme dans l'interface admin)
    articles_data = []
    for article in articles:
        # Déterminer l'URL de l'image (priorité à l'image locale)
        image_url = ''
        if article.image:
            # Construire l'URL complète pour l'image locale
            from django.conf import settings
            image_url = f"{settings.MEDIA_URL}{article.image.name}"
        elif article.image_url:
            image_url = article.image_url
            
        articles_data.append({
            'id': article.pk,
            'nom': str(article.nom or ''),
            'reference': str(article.reference or ''),
            'prix_unitaire': float(article.prix_unitaire) if article.prix_unitaire else 0.0,
            'qte_disponible': int(article.get_total_qte_disponible()),
            'couleur': str(article.couleur or ''),
            'pointure': str(article.pointure or ''),
            'categorie': str(article.categorie) if hasattr(article, 'categorie') and article.categorie else '',
            'phase': str(article.phase or ''),
            'has_promo_active': bool(article.has_promo_active),
            'isUpsell': bool(article.isUpsell),
            'image_url': image_url
        })

    context = {
        'operateur': operateur,
        'clients': clients,
        'articles': articles,
        'articles_json': articles_data,
        'villes': villes,
    }

    return render(request, 'operatConfirme/creer_commande.html', context)

@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer le contenu du panier d'une commande"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'GET':
        try:
            # Récupérer la commande avec ses paniers et variantes
            commande = get_object_or_404(
                Commande.objects.select_related('client', 'ville').prefetch_related(
                    'paniers__article',
                    'paniers__variante__couleur',
                    'paniers__variante__pointure'
                ),
                pk=commande_id
            )

            # Vérifier que l'opérateur peut voir cette commande
            # Soit elle lui est actuellement affectée (date_fin=null)
            # Soit il l'a déjà traitée (peu importe date_fin)
            etat_operateur = commande.etats.filter(
                operateur=operateur
            ).first()

            if not etat_operateur:
                return JsonResponse({'error': 'Cette commande ne vous est pas affectée'}, status=403)

            # Préparer les données pour le template
            paniers = commande.paniers.all()
            total_articles = sum(panier.quantite for panier in paniers)
            total_montant = sum(panier.sous_total for panier in paniers)

            # Calculer les frais de livraison SEULEMENT si activés
            if commande.frais_livraison:
                frais_livraison = commande.ville.frais_livraison if commande.ville else 0
                total_final = float(total_montant) + float(frais_livraison)
            else:
                frais_livraison = 0
                total_final = float(total_montant)

            # Construire la liste des articles pour le JSON
            articles_data = []
            for panier in paniers:
                # Construire l'URL de l'image
                image_url = None
                if panier.article.image:
                    image_url = panier.article.image.url
                elif panier.article.image_url:
                    image_url = panier.article.image_url

                article_dict = {
                    'nom': str(panier.article.nom),
                    'reference': str(panier.article.reference) if panier.article.reference else 'N/A',
                    'description': str(panier.article.description) if panier.article.description else '',
                    'prix_panier': float(panier.prix_panier) if panier.prix_panier else float(panier.article.prix_unitaire),
                    'prix_unitaire': float(panier.article.prix_unitaire),
                    'quantite': panier.quantite,
                    'sous_total': float(panier.sous_total),
                    'sous_total_remise': float(panier.sous_total_remise) if panier.sous_total_remise else 0,
                    'remise_appliquee': panier.remise_appliquer,
                    'type_remise_appliquee': panier.type_remise_appliquee if panier.type_remise_appliquee else '',
                    'image_url': image_url,
                    'phase': panier.article.phase,
                    'isUpsell': panier.article.isUpsell,
                    'has_promo_active': panier.article.has_promo_active
                }

                # Ajouter les informations de la variante si elle existe
                if panier.variante:
                    article_dict['variante'] = {
                        'id': panier.variante.pk,
                        'couleur': str(panier.variante.couleur.nom) if panier.variante.couleur else None,
                        'pointure': str(panier.variante.pointure.pointure) if panier.variante.pointure else None
                    }
                else:
                    article_dict['variante'] = None

                articles_data.append(article_dict)
            
            return JsonResponse({
                'success': True,
                'commande': {
                    'id_yz': commande.id_yz,
                    'client_nom': str(commande.client.get_full_name),
                    'total_articles': total_articles,
                    'total_montant': float(total_montant),
                    'frais_livraison': float(frais_livraison),
                    'total_final': float(total_final)
                },
                'articles': articles_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la récupération du panier: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def rafraichir_articles_section(request, commande_id):
    """
    Vue pour rafraîchir la section des articles d'une commande et renvoyer le HTML.
    """
    try:
        commande = get_object_or_404(Commande.objects.prefetch_related('paniers__article'), id=commande_id)
        
        # Corriger automatiquement les paniers d'articles en liquidation et en promotion
        commande.corriger_paniers_liquidation_et_promotion()
        
        # S'assurer que les totaux et le compteur sont à jour
        commande.recalculer_totaux_upsell()

        context = {
            'commande': commande,
            'villes': Ville.objects.select_related('region').order_by('region__nom_region', 'nom')
        }
        
        # Rendre le template partiel avec la liste des articles
        html = render_to_string('operatConfirme/partials/_articles_section.html', context, request=request)
        
        # Renvoyer le HTML et les totaux mis à jour
        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
            'articles_count': commande.paniers.count(),
            'compteur': commande.compteur,
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commande non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_recherche_client_tel(request):
    """API pour rechercher un client par numéro de téléphone (recherche partielle)"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        results = []
        if query and len(query) >= 3:
            from client.models import Client
            clients = Client.objects.filter(numero_tel__icontains=query).order_by('prenom', 'nom')[:10]
            for c in clients:
                results.append({
                    'id': c.pk,
                    'nom': c.nom,
                    'prenom': c.prenom,
                    'numero_tel': c.numero_tel,
                    'full_name': f"{c.prenom} {c.nom}",
                })
        return JsonResponse({'results': results})
    return JsonResponse({'results': []}, status=405)

@login_required
def rechercher_client_telephone(request):
    """API pour rechercher un client par numéro de téléphone exact"""
    from django.http import JsonResponse
    from client.models import Client
    
    if request.method == 'GET':
        telephone = request.GET.get('telephone', '').strip()
        
        if not telephone:
            return JsonResponse({
                'success': False,
                'error': 'Numéro de téléphone requis'
            }, status=400)
        
        try:
            # Rechercher le client par numéro de téléphone exact
            client = Client.objects.get(numero_tel=telephone, is_active=True)
            
            return JsonResponse({
                'success': True,
                'client': {
                    'id': client.id,
                    'nom_complet': client.get_full_name,
                    'nom': client.nom,
                    'prenom': client.prenom,
                    'numero_tel': client.numero_tel,
                    'email': client.email or '',
                    'adresse': client.adresse or ''
                }
            })
            
        except Client.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Aucun client trouvé avec ce numéro de téléphone'
            })
            
        except Client.MultipleObjectsReturned:
            # Si plusieurs clients avec le même numéro (cas rare)
            clients = Client.objects.filter(numero_tel=telephone, is_active=True)
            return JsonResponse({
                'success': False,
                'error': f'Plusieurs clients trouvés avec ce numéro ({clients.count()})'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la recherche: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)

@login_required
def api_recherche_article_ref(request):
    """API pour rechercher des articles par référence ou nom"""
    try:
        # Récupérer les paramètres de recherche
        query = request.GET.get('q', '').strip()
        article_id = request.GET.get('id', '').strip()
        reference = request.GET.get('reference', '').strip()
        
        # Cas 1: Recherche par ID (pour modifier_commande.html)
        if article_id:
            try:
                article = Article.objects.get(id=article_id, actif=True)
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                article_data = {
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                }
                
                return JsonResponse({
                    'success': True,
                    'article': article_data
                })
            except Article.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Article avec l\'ID {article_id} non trouvé ou désactivé'
                })
        
        # Cas 2: Recherche par référence exacte
        elif reference:
            article = Article.objects.filter(reference=reference, actif=True).first()
            if article:
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                article_data = {
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                }
                
                return JsonResponse({
                    'success': True,
                    'article': article_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Article avec la référence "{reference}" non trouvé ou désactivé'
                })
        
        # Cas 3: Recherche par texte (pour creer_commande.html)
        elif query and len(query) >= 2:
            # Rechercher les articles par référence ou nom
            articles = Article.objects.filter(
                Q(reference__icontains=query) | 
                Q(nom__icontains=query),
                actif=True
            ).order_by('nom')[:10]  # Limiter à 10 résultats
            
            results = []
            for article in articles:
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                results.append({
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                })
            
            return JsonResponse({
                'results': results
            })
        
        # Cas par défaut: aucun paramètre valide
        else:
            return JsonResponse({
                'results': []
            })
        
    except Exception as e:
        import traceback
        print(f"Erreur dans api_recherche_article_ref: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'results': [],
            'error': str(e)
        })

# Vues liées aux notifications supprimées (test_modal, centre_notifications)

@login_required
def get_article_variants(request, article_id):
    """
    Récupère toutes les variantes disponibles d'un article donné
    """
    try:
        from article.models import Article, VarianteArticle
        
        print(f"🔍 Recherche des variantes pour l'article ID: {article_id} (type: {type(article_id)})")
        
        # Vérifier si l'article existe et s'il est actif
        try:
            article = Article.objects.get(id=article_id)
            print(f"📋 Article trouvé: {article.nom} (actif: {article.actif})")
            
            if not article.actif:
                print(f"⚠️ Article {article_id} existe mais est inactif")
                return JsonResponse({
                    'success': False,
                    'error': f'L\'article "{article.nom}" (ID: {article_id}) est désactivé'
                }, status=404)
                
        except Article.DoesNotExist:
            print(f"❌ Aucun article trouvé avec l'ID {article_id}")
            return JsonResponse({
                'success': False,
                'error': f'Aucun article trouvé avec l\'ID {article_id}'
            }, status=404)
            
        print(f"✅ Article actif trouvé: {article.nom}")
        
        # Récupérer toutes les variantes actives de cet article
        variantes = VarianteArticle.objects.filter(
            article=article,
            actif=True
        ).select_related('couleur', 'pointure').order_by('couleur__nom', 'pointure__ordre')
        
        print(f"📊 Nombre de variantes trouvées: {variantes.count()}")
        
        # Construire la liste des variantes avec leurs informations
        variants_data = []
        for variante in variantes:
            
            variant_info = {
                'id': variante.id,
                'couleur': variante.couleur.nom if variante.couleur else None,
                'pointure': variante.pointure.pointure if variante.pointure else None,
                'taille': None,  # À adapter selon votre modèle si vous avez des tailles
                'stock': variante.qte_disponible,
                'prix_unitaire': float(variante.prix_unitaire),
                'prix_actuel': float(variante.prix_actuel),
                'reference_variante': variante.reference_variante,
                'est_disponible': variante.est_disponible
            }
            variants_data.append(variant_info)
        
        response_data = {
            'success': True,
            'variants': variants_data,
            'article': {
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference
            }
        }
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans get_article_variants: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la récupération des variantes'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def appliquer_remise_panier(request, panier_id):
    """
    Applique une remise personnalisée sur un panier spécifique.
    La remise est calculée sur le sous_total du panier (pas sur prix_panier).

    Paramètres attendus (POST JSON):
    - type_remise: 'POURCENTAGE' ou 'MONTANT_FIXE'
    - valeur_remise: La valeur de la remise (pourcentage ou montant en DH)
    - raison_remise: (optionnel) Motif de la remise

    Returns:
        JsonResponse avec:
        - success: bool
        - message: str
        - data: {
            sous_total_original: Decimal,
            montant_remise: Decimal,
            nouveau_sous_total: Decimal,
            nouveau_total_commande: Decimal
        }
    """
    from commande.models import RemisePanier
    from django.views.decorators.http import require_http_methods
    from decimal import Decimal

    try:
        # Récupérer l'opérateur
        try:
            operateur = Operateur.objects.get(
                user=request.user,
                type_operateur__in=['CONFIRMATION', 'SUPERVISEUR_PREPARATION']
            )
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Profil opérateur non trouvé'
            }, status=403)

        # Récupérer le panier
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        commande = panier.commande

        # Vérifier que la commande appartient aux commandes accessibles par l'opérateur
        if not commande.etats.filter(
            Q(operateur=operateur) | Q(enum_etat__libelle__in=['Affectée', 'En cours de confirmation', 'Retour Confirmation'])
        ).exists():
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'avez pas accès à cette commande'
            }, status=403)

        # Parser les données JSON
        data = json.loads(request.body)
        type_remise = data.get('type_remise', 'POURCENTAGE')
        valeur_remise = data.get('valeur_remise')
        raison_remise = data.get('raison_remise', '')

        # Validation des données
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

        # Calculer le sous-total basé sur le prix effectif actuel (upsells, promo, liquidation)
        from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

        prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
        quantite = Decimal(str(panier.quantite))
        sous_total_actuel = prix_unitaire_effectif * quantite

        # On ne travaille qu'en pourcentage
        type_remise = 'POURCENTAGE'
        # Contrainte: Le pourcentage ne doit pas dépasser 100%
        if valeur_remise > Decimal('100'):
            return JsonResponse({
                'success': False,
                'error': 'Le pourcentage de remise ne peut pas dépasser 100%'
            }, status=400)

        # Vérifier si une remise existe déjà
        if hasattr(panier, 'remise_personnalisee'):
            return JsonResponse({
                'success': False,
                'error': 'Une remise est déjà appliquée sur ce panier. Veuillez d\'abord la retirer.'
            }, status=400)

        # Créer la remise avec transaction
        with transaction.atomic():
            remise = RemisePanier.objects.create(
                panier=panier,
                type_remise=type_remise,
                valeur_remise=valeur_remise,
                raison_remise=raison_remise,
                operateur=operateur
            )

            # Appliquer la remise (calcule et modifie le sous_total du panier)
            # La méthode appliquer_remise() sauvegarde automatiquement le sous-total original dans panier.sous_total_remise
            nouveau_sous_total = remise.appliquer_remise()

            # Recalculer le total de la commande avec les frais de livraison
            commande.recalculer_total_avec_frais()

        # Récupérer le sous-total original depuis panier.sous_total_remise (sauvegardé par appliquer_remise)
        panier.refresh_from_db()
        sous_total_original = Decimal(str(panier.sous_total_remise))

        # Retourner les informations
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


@login_required
@require_http_methods(["POST"])
def retirer_remise_panier(request, panier_id):
    """
    Retire une remise appliquée sur un panier.
    Restaure le sous_total original du panier.

    Returns:
        JsonResponse avec:
        - success: bool
        - message: str
        - data: {
            sous_total_restaure: Decimal,
            montant_remise_retiree: Decimal,
            nouveau_total_commande: Decimal
        }
    """
    from commande.models import RemisePanier
    from django.views.decorators.http import require_http_methods
    from decimal import Decimal

    try:
        # Récupérer l'opérateur
        try:
            operateur = Operateur.objects.get(
                user=request.user,
                type_operateur__in=['CONFIRMATION', 'SUPERVISEUR_PREPARATION']
            )
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Profil opérateur non trouvé'
            }, status=403)

        # Récupérer le panier
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        commande = panier.commande

        # Vérifier l'accès
        if not commande.etats.filter(
            Q(operateur=operateur) | Q(enum_etat__libelle__in=['Affectée', 'En cours de confirmation', 'Retour Confirmation'])
        ).exists():
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'avez pas accès à cette commande'
            }, status=403)

        # Vérifier si une remise existe
        if not hasattr(panier, 'remise_personnalisee'):
            return JsonResponse({
                'success': False,
                'error': 'Aucune remise n\'est appliquée sur ce panier'
            }, status=400)

        remise = panier.remise_personnalisee
        montant_remise_retiree = Decimal(str(remise.montant_applique))

        # Retirer la remise avec transaction
        with transaction.atomic():
            sous_total_restaure = remise.retirer_remise()

            # Recalculer le total de la commande avec les frais de livraison
            commande.recalculer_total_avec_frais()

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


@login_required
def calculer_remise_panier_preview(request, panier_id):
    """
    Calcule et retourne un aperçu de la remise sans l'appliquer.
    Utile pour afficher le montant avant confirmation.

    Paramètres GET:
    - type_remise: 'POURCENTAGE' ou 'MONTANT_FIXE'
    - valeur_remise: La valeur de la remise

    Returns:
        JsonResponse avec:
        - success: bool
        - data: {
            sous_total_actuel: Decimal,
            montant_remise_calcule: Decimal,
            sous_total_apres_remise: Decimal,
            pourcentage_reduction: Decimal (si applicable)
        }
    """
    from decimal import Decimal

    try:
        # Récupérer le panier
        try:
            panier = Panier.objects.get(id=panier_id)
        except Panier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Panier non trouvé'
            }, status=404)

        # Récupérer les paramètres
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

        # Calculer le sous-total basé sur le prix effectif actuel (upsells, promo, liquidation)
        from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

        prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
        quantite = Decimal(str(panier.quantite))
        sous_total_actuel = prix_unitaire_effectif * quantite

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



