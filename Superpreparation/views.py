from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q, Sum, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.core.paginator import Paginator
import json
from parametre.models import Operateur, Ville
from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation, Panier, Envoi
from django.urls import reverse
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
import csv
from article.models import Article, MouvementStock, VarianteArticle
from commande.models import Envoi
from .forms import ArticleForm, AjusterStockForm
from .utils import creer_mouvement_stock
from .decorators import superviseur_preparation_required, superviseur_only_required, preparation_team_required
from article.models import Article, Promotion, VarianteArticle, Categorie, Genre, Couleur, Pointure
from django.views.decorators.http import require_POST
from article.forms import PromotionForm
from decimal import Decimal



@superviseur_preparation_required
def home_view(request):
    """Tableau de bord de supervision avec métriques globales et suivi en temps réel"""
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Date de référence
    today = timezone.now().date()
    # Début de la semaine (lundi)
    start_of_week = today - timedelta(days=today.weekday())

    # Récupérer les états nécessaires
    try:
        etat_confirmee = EnumEtatCmd.objects.get(libelle__iexact='Confirmée')
        etat_en_preparation = EnumEtatCmd.objects.get(libelle__iexact='En préparation')
        etat_preparee = EnumEtatCmd.objects.get(libelle__iexact='Préparée')
    except EnumEtatCmd.DoesNotExist as e:
        messages.error(request, f"État manquant dans le système: {str(e)}")
        return redirect('login')


    # 3. Commandes livrées partiellement (supervision)
    commandes_livrees_partiellement = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement',
        etats__date_fin__isnull=True

    ).distinct().count()
    commandes_retournees = Commande.objects.filter(
        etats__enum_etat__libelle='Retournée',
        etats__date_fin__isnull=True
    ).distinct().count()

    commandes_en_cours = Commande.objects.filter(
        etats__enum_etat=etat_en_preparation,
        etats__date_fin__isnull=True
    ).distinct().count()

    ma_performance = EtatCommande.objects.filter(
        enum_etat=etat_preparee,
        date_debut__date=today,
        operateur=operateur_profile
    ).distinct().count()

    commandes_preparees_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date=today
    ).count()



    # Commandes préparées cette semaine (toutes)

    commandes_preparees_week = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date__gte=start_of_week,
        date_fin__date__lte=today
    ).count()



    # Commandes actuellement en préparation (toutes)

    commandes_en_preparation = Commande.objects.filter(
        etats__enum_etat=etat_en_preparation,
        etats__date_fin__isnull=True
    ).count()

    # Performance de l'opérateur aujourd'hui (commandes préparées par lui)
    ma_performance_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date=today,
        operateur=operateur_profile
    ).count()


    # Valeur totale (DH) des commandes préparées aujourd'hui
    commandes_ids_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date=today
    ).values_list('commande_id', flat=True)

    valeur_preparees_today = Commande.objects.filter(id__in=commandes_ids_today).aggregate(total=Sum('total_cmd'))['total'] or 0



    # Articles populaires (semaine en cours)
    commandes_ids_week = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date__gte=start_of_week,
        date_fin__date__lte=today
    ).values_list('commande_id', flat=True)

    articles_populaires = Panier.objects.filter(
        commande_id__in=commandes_ids_week
    ).values('article__nom', 'article__reference').annotate(
        total_quantite=Sum('quantite'),
        total_commandes=Count('commande', distinct=True)
    ).order_by('-total_quantite')[:5]



    # Activité récente (5 dernières préparations de l'opérateur)
    activite_recente = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        operateur=operateur_profile,
        date_fin__isnull=False
    ).select_related('commande', 'commande__client').order_by('-date_fin')[:5]



    # STATISTIQUES GLOBALES ADDITIONNELLES

    # Commandes confirmées aujourd'hui

    commandes_confirmees_today = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_debut__date=today
    ).distinct().count()

    

    # Total global des commandes actives
    total_commandes_actives = commandes_en_cours + commandes_livrees_partiellement + commandes_retournees
    

    # Performance globale (toutes les préparations terminées aujourd'hui)

    performance_globale_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date=today
    ).count()

    

    # Valeur totale traitée aujourd'hui

    valeur_totale_today = Commande.objects.filter(
        etats__enum_etat=etat_en_preparation,
        etats__date_fin__date=today
    ).aggregate(total=Sum('total_cmd'))['total'] or 0

    

    # Taux de réussite (commandes terminées vs commandes reçues)
    taux_reussite = 0
    if commandes_confirmees_today > 0:
        taux_reussite = round((performance_globale_today / commandes_confirmees_today) * 100, 1)

    # Alertes de supervision
    alertes = []
    if commandes_retournees > 0:
        alertes.append({
            'type': 'warning',
            'icon': 'fas fa-exclamation-triangle',
            'message': f'{commandes_retournees} commande(s) retournée(s) nécessite(nt) une attention',
            'url': 'Superpreparation:commandes_retournees'
        })
    if commandes_livrees_partiellement > 0:
        alertes.append({
            'type': 'info',
            'icon': 'fas fa-info-circle',
            'message': f'{commandes_livrees_partiellement} commande(s) livrée(s) partiellement',
            'url': 'Superpreparation:commandes_livrees_partiellement'
        })

        alertes.append({
            'type': 'urgent',
            'icon': 'fas fa-fire',

        })
    

    # Préparer les statistiques de supervision

    stats = {
        # Statistiques principales de supervision
        
        'commandes_en_cours': commandes_en_cours,
        'commandes_livrees_partiellement': commandes_livrees_partiellement,
        'commandes_retournees': commandes_retournees,
        'commandes_confirmees_today': commandes_confirmees_today,
        'total_commandes_actives': total_commandes_actives,
        # Performance et KPIs
        'performance_globale_today': performance_globale_today,
        'ma_performance_today': ma_performance_today,
        'taux_reussite': taux_reussite,
        'valeur_totale_today': valeur_totale_today,
        'valeur_preparees_today': valeur_preparees_today,

        # Données historiques
        'commandes_preparees_today': commandes_preparees_today,
        'commandes_preparees_week': commandes_preparees_week,
        'commandes_en_preparation': commandes_en_preparation,

        # Données détaillées
        'articles_populaires': articles_populaires,
        'activite_recente': activite_recente,
        'alertes': alertes

    }

    context = {
        'page_title': 'Centre de Supervision',
        'page_subtitle': f'Tableau de bord global - {total_commandes_actives} commandes actives',
        'profile': operateur_profile,
        'stats': stats,
        'alertes': alertes,
        'is_supervision': True
    }
    return render(request, 'composant_generale/Superpreparation/home.html', context)

def _get_commandes_en_preparation():
    """Récupère toutes les commandes en préparation sans doublons"""
    from django.db.models import Q
    
    # États de préparation valides
    etats_preparation = ['En préparation', 'Collectée', 'Emballée', 'Préparée']
    
    # Récupérer les IDs des commandes en préparation
    commandes_ids = Commande.objects.filter(
        Q(etats__enum_etat__libelle__in=etats_preparation),
        etats__date_fin__isnull=True
    ).values_list('id', flat=True).distinct()
    
    # Récupérer les commandes avec leurs relations
    return Commande.objects.filter(
        id__in=commandes_ids
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats')


def _get_etat_actuel_preparation(commande):
    """Trouve l'état actuel de préparation d'une commande"""
    etats_preparation = ['À imprimer', 'En préparation', 'Collectée', 'Emballée', 'Préparée']
    
    for etat in commande.etats.all().order_by('date_debut'):
        if etat.enum_etat.libelle in etats_preparation and not etat.date_fin:
            return etat
    return None


def _get_etat_precedent(commande, etat_actuel):
    """Trouve l'état précédent d'une commande"""
    etats_preparation = ['À imprimer', 'En préparation', 'Collectée', 'Emballée', 'Préparée']
    
    for etat in reversed(commande.etats.all().order_by('date_debut')):
        if (etat.date_fin and 
            etat.date_fin < etat_actuel.date_debut and 
            etat.enum_etat.libelle not in etats_preparation):
            return etat
    return None


def _enrichir_commande(commande):
    """Enrichit une commande avec ses états et informations supplémentaires"""
    etat_actuel = _get_etat_actuel_preparation(commande)
    if not etat_actuel:
        return commande
    
    # Ajouter l'état actuel
    commande.etat_actuel_preparation = etat_actuel
    
    # Ajouter l'état précédent
    commande.etat_precedent = _get_etat_precedent(commande, etat_actuel)
    
    # Ajouter l'état de confirmation
    etat_conf = commande.etats.filter(
        enum_etat__libelle='Confirmée',
        operateur__type_operateur='CONFIRMATION'
    ).order_by('-date_debut').first()
    
    if not etat_conf:
        etat_conf = commande.etats.filter(enum_etat__libelle='Confirmée').order_by('date_debut').first()
    
    commande.etat_confirmation = etat_conf
    
    # Générer le code-barres
    if commande.id_yz:
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(buffer, options={'write_text': False, 'module_height': 10.0})
        commande.barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    else:
        commande.barcode_base64 = None
    
    return commande


def _filtrer_commandes_par_type(commandes, filter_type):
    """Filtre les commandes selon le type de filtre"""
    from commande.models import Operation
    
    if filter_type == 'retournees':
        return redirect('Superpreparation:commandes_retournees')
    
    if filter_type == 'all':
        # Pour "Toutes les commandes", filtrer les commandes avec des états problématiques
        commandes_filtrees = []
        for commande in commandes:
            etat_actuel = _get_etat_actuel_preparation(commande)
            if not etat_actuel:
                continue
                
            # Vérifier s'il y a des états ultérieurs problématiques
            if etat_actuel.enum_etat.libelle != 'Préparée':
                etats_problematiques = ['Livrée', 'Livrée Partiellement', 'En cours de livraison']
                for etat in commande.etats.all():
                    if (etat.date_debut > etat_actuel.date_debut and 
                        etat.enum_etat.libelle in etats_problematiques):
                        break
                else:
                    commandes_filtrees.append(commande)
            else:
                commandes_filtrees.append(commande)
        return commandes_filtrees
    
    elif filter_type == 'livrees_partiellement':
        # Commandes avec historique de livraison partielle
        commandes_filtrees = []
        for commande in commandes:
            etat_actuel = _get_etat_actuel_preparation(commande)
            if not etat_actuel:
                continue
                
            # Vérifier l'historique de livraison partielle
            for etat in commande.etats.all().order_by('date_debut'):
                if (etat.enum_etat.libelle == 'Livrée Partiellement' and 
                    etat.date_fin and 
                    etat.date_fin < etat_actuel.date_debut):
                    commandes_filtrees.append(commande)
                    break
        return commandes_filtrees
    
    elif filter_type == 'renvoyees_logistique':
        # Commandes renvoyées par la logistique
        commandes_filtrees = []
        for commande in commandes:
            # Vérifier les opérations de renvoi
            operation_renvoi = Operation.objects.filter(
                commande=commande,
                type_operation='RENVOI_PREPARATION'
            ).first()
            
            if operation_renvoi:
                commandes_filtrees.append(commande)
                continue
            
            # Vérifier les commandes de renvoi
            if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
                num_cmd_original = commande.num_cmd.replace('RENVOI-', '')
                commande_originale = Commande.objects.filter(
                    num_cmd=num_cmd_original,
                    etats__enum_etat__libelle='Livrée Partiellement'
                ).first()
                if commande_originale:
                    commandes_filtrees.append(commande)
                    continue
            
            # Vérifier l'historique des états
            etat_actuel = _get_etat_actuel_preparation(commande)
            if etat_actuel:
                for etat in reversed(commande.etats.all().order_by('date_debut')):
                    if (etat.date_fin and 
                        etat.date_fin < etat_actuel.date_debut and 
                        etat.enum_etat.libelle == 'En cours de livraison'):
                        commandes_filtrees.append(commande)
                        break
        return commandes_filtrees
    
    return list(commandes)


def _calculer_statistiques(operateur_profile):
    """Calcule les statistiques des commandes"""
    from commande.models import Operation
    
    stats = {
        'renvoyees_logistique': 0,
        'livrees_partiellement': 0,
        'affectees_moi': 0,
    }
    
    # Commandes en préparation
    commandes_preparation = _get_commandes_en_preparation()
    
    for commande in commandes_preparation:
        # Vérifier les opérations de renvoi
        if Operation.objects.filter(
            commande=commande,
            type_operation='RENVOI_PREPARATION'
        ).exists():
            stats['renvoyees_logistique'] += 1
            continue
        
        # Vérifier les commandes de renvoi
        if (commande.num_cmd and 
            commande.num_cmd.startswith('RENVOI-') and
            Commande.objects.filter(
                num_cmd=commande.num_cmd.replace('RENVOI-', ''),
                etats__enum_etat__libelle='Livrée Partiellement'
            ).exists()):
            stats['renvoyees_logistique'] += 1
            continue
        
        # Vérifier l'historique des états
        etat_actuel = _get_etat_actuel_preparation(commande)
        if etat_actuel:
            for etat in reversed(commande.etats.all().order_by('date_debut')):
                if (etat.date_fin and 
                    etat.date_fin < etat_actuel.date_debut):
                    if etat.enum_etat.libelle == 'En cours de livraison':
                        stats['renvoyees_logistique'] += 1
                    elif etat.enum_etat.libelle == 'Livrée Partiellement':
                        stats['livrees_partiellement'] += 1
                    break
    
    # Commandes affectées à l'opérateur
    try:
        superviseur_nom = operateur_profile.nom_complet
        if superviseur_nom:
            stats['affectees_moi'] = Commande.objects.filter(
                etats__enum_etat__libelle='En préparation',
                etats__commentaire__icontains=f"Affectée à la préparation par {superviseur_nom}"
            ).distinct().count()
    except Exception:
        pass
    
    return stats


@superviseur_preparation_required
def liste_prepa(request):
    """Liste des commandes à préparer pour les opérateurs de préparation"""
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')
    
    # Récupérer les paramètres
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    items_per_page = int(request.GET.get('items_per_page', 10))
    
    # Récupérer et filtrer les commandes
    commandes = _get_commandes_en_preparation()
    commandes_filtrees = _filtrer_commandes_par_type(commandes, filter_type)
    
    # Appliquer la recherche
    if search_query:
        from django.db.models import Q
        commandes_filtrees = [cmd for cmd in commandes_filtrees if 
            search_query.lower() in str(cmd.id_yz).lower() or
            search_query.lower() in (cmd.num_cmd or '').lower() or
            search_query.lower() in cmd.client.nom.lower() or
            search_query.lower() in cmd.client.prenom.lower() or
            search_query.lower() in (cmd.client.numero_tel or '').lower()
        ]
    
    # Enrichir les commandes
    commandes_enrichies = [_enrichir_commande(cmd) for cmd in commandes_filtrees]
    
    # Trier par date d'affectation
    commandes_enrichies.sort(
        key=lambda x: x.etats.filter(date_fin__isnull=True).first().date_debut 
        if x.etats.filter(date_fin__isnull=True).first() 
        else timezone.now(), 
        reverse=True
    )
    
    # Calculer les statistiques
    stats_par_type = _calculer_statistiques(operateur_profile)
    
    # Statistiques générales
    total_affectees = len(commandes_enrichies)
    valeur_totale = sum(cmd.total_cmd or 0 for cmd in commandes_enrichies)
    date_limite_urgence = timezone.now() - timedelta(days=1)
    commandes_urgentes = sum(1 for cmd in commandes_enrichies if 
        cmd.etats.filter(date_debut__lt=date_limite_urgence).exists()
    )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(commandes_enrichies, items_per_page)
    page_number = request.GET.get('page', 1)
    commandes_page = paginator.get_page(page_number)
    
    # Contexte
    context = {
        'page_title': 'Suivi Général - Préparation',
        'page_subtitle': f'Vue d\'ensemble des commandes en file de préparation ({total_affectees})',
        'commandes_affectees': commandes_page,
        'search_query': search_query,
        'filter_type': filter_type,
        'items_per_page': items_per_page,
        'stats': {
            'total_affectees': total_affectees,
            'valeur_totale': valeur_totale,
            'commandes_urgentes': commandes_urgentes,
        },
        'stats_par_type': stats_par_type,
        'operateur_profile': operateur_profile,
        'api_produits_url_base': reverse('Superpreparation:api_commande_produits', args=[99999999]),
    }
    
    return render(request, 'Superpreparation/liste_prepa.html', context)

@superviseur_preparation_required
def commandes_preparees(request):
    """Liste des commandes préparées (état final) pour les superviseurs"""
    try:
        operateur_profile = request.user.profil_operateur
        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True  # État actif
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_preparees = commandes_preparees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        ).distinct()

    # Statistiques
    total_preparees = commandes_preparees.count()
    valeur_totale = commandes_preparees.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Commandes préparées aujourd'hui
    today = timezone.now().date()
    preparees_today = commandes_preparees.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_debut__date=today
    ).count()

    # Pagination
    items_per_page = request.GET.get('items_per_page', 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page <= 0:
            items_per_page = 10
    except (ValueError, TypeError):
        items_per_page = 10

    paginator = Paginator(commandes_preparees, items_per_page)
    page_number = request.GET.get('page', 1)
    commandes_page = paginator.get_page(page_number)

    context = {
        'page_title': 'Commandes Préparées',
        'page_subtitle': f'Commandes finalisées et prêtes pour livraison ({total_preparees})',
        'commandes_preparees': commandes_page,
        'search_query': search_query,
        'items_per_page': items_per_page,
        'stats': {
            'total_preparees': total_preparees,
            'valeur_totale': valeur_totale,
            'preparees_today': preparees_today,
        },
        'operateur_profile': operateur_profile,
    }
    return render(request, 'Superpreparation/commandes_preparees.html', context)

@superviseur_preparation_required
def commandes_en_preparation(request):
    """Page de suivi (lecture seule) des commandes en préparation"""
    try:
        operateur_profile = request.user.profil_operateur
        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('Superpreparation:home')
    commandes_en_preparation = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True  # État actif (en cours)
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats__operateur').distinct()
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_en_preparation = commandes_en_preparation.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        ).distinct()
    stats = {
        'total_commandes': commandes_en_preparation.count(),
        'commandes_urgentes': commandes_en_preparation.filter(
            etats__date_debut__lt=timezone.now() - timedelta(days=1)
        ).count(),
        'valeur_totale': commandes_en_preparation.aggregate(total=Sum('total_cmd'))['total'] or 0
    }
    context = {
        'page_title': 'Suivi - Commandes en Préparation',
        'page_subtitle': f'Suivi en temps réel de {commandes_en_preparation.count()} commande(s) en cours de préparation',
        'profile': operateur_profile,
        'commandes': commandes_en_preparation,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'en_preparation',
        'is_readonly': True,
        'is_tracking_page': True
    }
    return render(request, 'Superpreparation/commandes_en_preparation.html', context)

@superviseur_preparation_required
def commandes_emballees(request):
    """Page de suivi des commandes emballées qui attendent la finalisation par le superviseur"""
    try:
        operateur_profile = request.user.profil_operateur
        
        # Autoriser superviseur ou équipe préparation
        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('Superpreparation:home')

    # Récupérer TOUTES les commandes emballées qui attendent la finalisation
    commandes_emballees = Commande.objects.filter(
        etats__enum_etat__libelle='Emballée',
        etats__date_fin__isnull=True  # État actif (en cours)
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats__operateur').distinct()

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_emballees = commandes_emballees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        ).distinct()

    # Statistiques
    stats = {
        'total_commandes': commandes_emballees.count(),
        'commandes_urgentes': commandes_emballees.filter(
            etats__date_debut__lt=timezone.now() - timedelta(hours=2)  # Urgent si emballée depuis plus de 2h
        ).count(),
        'valeur_totale': commandes_emballees.aggregate(total=Sum('total_cmd'))['total'] or 0
    }

    context = {
        'page_title': 'Suivi - Commandes Emballées',
        'page_subtitle': f'Suivi en temps réel de {commandes_emballees.count()} commande(s) emballées en attente de finalisation',
        'profile': operateur_profile,
        'commandes': commandes_emballees,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'emballees',

        'is_readonly': False,  # Les superviseurs peuvent finaliser

        'is_tracking_page': True

    }

    return render(request, 'Superpreparation/commandes_emballees.html', context)

@superviseur_preparation_required
def commandes_livrees_partiellement(request):
    """Page de suivi (lecture seule) des commandes livrées partiellement"""
    try:
        operateur_profile = request.user.profil_operateur  # Autoriser superviseur ou équipe préparation
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')
    commandes_livrees_partiellement_qs = (
        Commande.objects
        .filter(etats__enum_etat__libelle='Livrée Partiellement')
        .filter(etats__enum_etat__libelle='En préparation', etats__operateur=operateur_profile)
        .select_related('client', 'ville', 'ville__region')
        .prefetch_related('paniers__article', 'etats')
        .distinct()
    )
    commandes_livrees_partiellement = []
    for commande_originale in commandes_livrees_partiellement_qs:
        commande_renvoi = Commande.objects.filter(
            num_cmd__startswith=f"RENVOI-{commande_originale.num_cmd}",
            client=commande_originale.client
        ).first()
        if commande_renvoi:
            commande_originale.commande_renvoi = commande_renvoi
        commandes_livrees_partiellement.append(commande_originale)
    commandes_filtrees = commandes_livrees_partiellement
    for commande in commandes_livrees_partiellement:
        etat_livraison_partielle = commande.etats.filter(
            enum_etat__libelle='Livrée Partiellement'
        ).order_by('-date_debut').first()
        if etat_livraison_partielle:
            commande.date_livraison_partielle = etat_livraison_partielle.date_debut
            commande.commentaire_livraison_partielle = etat_livraison_partielle.commentaire
            commande.operateur_livraison = etat_livraison_partielle.operateur
            commande.statut_actuel = "Renvoyée en préparation"
            if hasattr(commande, 'commande_renvoi'):
                commande.commande_renvoi_id = commande.commande_renvoi.id
                commande.commande_renvoi_num = commande.commande_renvoi.num_cmd
                commande.commande_renvoi_id_yz = commande.commande_renvoi.id_yz
    context = {
        'page_title': 'Suivi - Commandes Livrées Partiellement',
        'page_subtitle': f'Suivi en temps réel de {len(commandes_livrees_partiellement)} commande(s) livrées partiellement',
        'profile': operateur_profile,
        'commandes_livrees_partiellement': commandes_livrees_partiellement,
        'commandes_count': len(commandes_livrees_partiellement),
        'active_tab': 'livrees_partiellement',
        'is_readonly': True,
        'is_tracking_page': True
    }
    return render(request, 'Superpreparation/commandes_livrees_partiellement.html', context)

@superviseur_preparation_required
def commandes_retournees(request):
    """Page de suivi (lecture seule) des commandes retournées"""
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")
            return redirect('Superpreparation:home')
    
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Récupérer le paramètre d'onglet
    tab = request.GET.get('tab', 'actives')
    
    # Commandes ACTIVES (sans date_fin) - à traiter
    commandes_actives_qs = (
        Commande.objects
        .filter(etats__enum_etat__libelle='Retournée', etats__date_fin__isnull=True) 
        .prefetch_related('paniers__article', 'etats')
        .distinct()
    )
    
    # Commandes TRAITÉES (avec date_fin) - déjà traitées
    commandes_traitees_qs = (
        Commande.objects
        .filter(etats__enum_etat__libelle='Retournée', etats__date_fin__isnull=False) 
        .prefetch_related('paniers__article', 'etats')
        .distinct()
    )

    commandes_actives = list(commandes_actives_qs)
    commandes_traitees = list(commandes_traitees_qs)
    
    # Enrichir avec méta d'état 'Retournée' pour les commandes actives
    for commande in commandes_actives:
        etat_retour = commande.etats.filter(enum_etat__libelle='Retournée').order_by('-date_debut').first()
        if etat_retour:
            commande.date_retournee = etat_retour.date_debut
            commande.commentaire_retournee = etat_retour.commentaire
            commande.operateur_retour = etat_retour.operateur
            commande.etat_retournee = etat_retour  # Ajouter l'état complet
    
    # Enrichir avec méta d'état 'Retournée' pour les commandes traitées
    for commande in commandes_traitees:
        etat_retour = commande.etats.filter(enum_etat__libelle='Retournée').order_by('-date_debut').first()
        if etat_retour:
            commande.date_retournee = etat_retour.date_debut
            commande.date_traitement = etat_retour.date_fin
            commande.commentaire_retournee = etat_retour.commentaire
            commande.operateur_retour = etat_retour.operateur
            commande.operateur_traitement = etat_retour.operateur
            commande.etat_retournee = etat_retour  # Ajouter l'état complet

    # Statistiques
    stats = {
        'total_actives': len(commandes_actives),
        'total_traitees': len(commandes_traitees),
        'valeur_actives': sum(c.total_cmd for c in commandes_actives),
        'valeur_traitees': sum(c.total_cmd for c in commandes_traitees),
    }

    context = {
        'page_title': 'Suivi - Commandes Retournées',
        'page_subtitle': f'Gestion des commandes retournées - {stats["total_actives"]} actives, {stats["total_traitees"]} traitées',
        'profile': operateur_profile,
        'commandes_retournees': commandes_actives if tab == 'actives' else commandes_traitees,
        'commandes_actives': commandes_actives,
        'commandes_traitees': commandes_traitees,
        'commandes_count': len(commandes_actives) if tab == 'actives' else len(commandes_traitees),
        'stats': stats,
        'active_tab': 'retournees',
        'current_tab': tab,
        'is_readonly': True,
        'is_tracking_page': True
    }
    return render(request, 'Superpreparation/commandes_retournees.html', context)

@superviseur_preparation_required
def traiter_commande_retournee_api(request, commande_id):
    """API pour traiter une commande retournée et gérer la réincrémentation du stock"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            return JsonResponse({'success': False, 'message': "Accès réservé à l'équipe préparation"})
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est bien en état "Retournée"
        etat_retournee = commande.etats.filter(
            enum_etat__libelle='Retournée',
            date_fin__isnull=True
        ).first()
        
        if not etat_retournee:
            return JsonResponse({'success': False, 'message': 'Commande non retournée'})
        
        # Récupérer les données de la requête
        data = json.loads(request.body)
        type_traitement = data.get('type_traitement')
        etat_stock = data.get('etat_stock')
        commentaire = data.get('commentaire')
        if not all([type_traitement, etat_stock, commentaire]):
            return JsonResponse({'success': False, 'message': 'Données manquantes'})
        
        # Traitement selon le type
        with transaction.atomic(): 
            if type_traitement == 'repreparer':
                # Traiter tous les paniers de la commande
                for panier in commande.paniers.all():
                    quantite = panier.quantite
                    
                    if panier.variante:
                        # Cas avec variante : traiter la variante spécifique
                        variante = panier.variante
                        
                        # Vérifier que la variante est encore active et existe
                        if not variante.actif:
                            return JsonResponse({
                                'success': False, 
                                'message': f'Variante {variante} désactivée. Impossible de traiter le stock.'
                            })
                        
                        # Créer un mouvement de stock pour tracer (dans tous les cas)
                        from article.models import MouvementStock
                        
                        if etat_stock == 'bon':
                            # Réincrémenter le stock de la variante
                            variante.qte_disponible += quantite
                            variante.save()
                            
                            MouvementStock.objects.create(
                                article=panier.article,
                                variante=variante,
                                quantite=quantite,
                                type_mouvement='entree',
                                commentaire=f"Réincrémentation - Commande retournée {commande.id_yz} - {variante.couleur.nom if variante.couleur else 'N/A'} - {variante.pointure.pointure if variante.pointure else 'N/A'} - Produits en bon état - {commentaire}",
                                operateur=operateur_profile,
                                qte_apres_mouvement=variante.qte_disponible
                            )
                        else:
                            # Produits défectueux : juste tracer sans réincrémenter
                            MouvementStock.objects.create(
                                article=panier.article,
                                variante=variante,
                                quantite=0,  # Quantité 0 car pas de réincrémentation
                                type_mouvement='perte',
                                commentaire=f"Produits défectueux - Commande retournée {commande.id_yz} - {variante.couleur.nom if variante.couleur else 'N/A'} - {variante.pointure.pointure if variante.pointure else 'N/A'} - Produits défectueux (non réintégrés) - {commentaire}",
                                operateur=operateur_profile,
                                qte_apres_mouvement=variante.qte_disponible
                            )
                    else:
                        # Cas sans variante : gérer les articles simples (si ce cas existe dans votre logique métier)
                        # Note: Dans ce système, les articles devraient normalement avoir des variantes
                        return JsonResponse({
                            'success': False, 
                            'message': f'Article {panier.article.nom} sans variante définie. Impossible de gérer le stock.'
                        })
                
                # GESTION DES ÉTATS DE COMMANDE
                # Terminer l'état "Retournée" avec la date de fin (la commande reste à l'état "Retournée")
                etat_retournee.terminer_etat(operateur_profile)
                
                # Créer une opération pour tracer l'action
                Operation.objects.create(
                    commande=commande,
                    type_operation='TRAITEMENT_RETOUR',
                    operateur=operateur_profile,
                    conclusion=f"Commande retournée traitée par {operateur_profile.nom_complet}. Traitement terminé avec date de confirmation.",
                    commentaire=commentaire
                )
                
                # Compter les variantes traitées pour le message de confirmation
                variantes_traitees = commande.paniers.filter(variante__isnull=False).count()
                
                if etat_stock == 'bon':
                    message = f"Stock réincrémenté avec succès pour {variantes_traitees} variante(s). Commande reste en état 'Retournée' avec date de confirmation."
                else:
                    message = f"Traitement effectué pour {variantes_traitees} variante(s) - Stock NON réincrémenté (produits défectueux). Commande reste en état 'Retournée' avec date de confirmation."
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'commande_id': commande.id,
                    'variantes_traitees': variantes_traitees,
                    'etat_actuel': 'Retournée',
                    'date_confirmation': timezone.now().strftime('%d/%m/%Y %H:%M')
                })

            return JsonResponse({
                'success': True,
                'message': message,
                'commande_id': commande.id
            })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@superviseur_preparation_required
def profile_view(request):

    try:

        operateur_profile = request.user.profil_operateur

    except Operateur.DoesNotExist:

        messages.error(request, "Votre profil opérateur n'existe pas.")

        return redirect('login') # Ou une page d'erreur appropriée



    context = {

        'page_title': 'Mon Profil',

        'page_subtitle': 'Gérez les informations de votre profil',

        'profile': operateur_profile,

    }

    return render(request, 'Superpreparation/profile.html', context)

@superviseur_preparation_required
def modifier_profile_view(request):

    try:

        operateur_profile = request.user.profil_operateur

    except Operateur.DoesNotExist:

        messages.error(request, "Votre profil opérateur n'existe pas.")

        return redirect('login')



    if request.method == 'POST':

        # Récupérer les données du formulaire

        nom = request.POST.get('nom')

        prenom = request.POST.get('prenom')

        mail = request.POST.get('mail')

        telephone = request.POST.get('telephone')

        adresse = request.POST.get('adresse')



        # Validation minimale (vous pouvez ajouter plus de validations ici)

        if not nom or not prenom or not mail:

            messages.error(request, "Nom, prénom et email sont requis.")

            context = {

                'page_title': 'Modifier Profil',

                'page_subtitle': 'Mettez à jour vos informations personnelles',

                'profile': operateur_profile,

                'form_data': request.POST, # Pour pré-remplir le formulaire

            }

            return render(request, 'Superpreparation/modifier_profile.html', context)

        

        # Mettre à jour l'utilisateur Django

        request.user.first_name = prenom

        request.user.last_name = nom

        request.user.email = mail

        request.user.save()



        # Mettre à jour le profil de l'opérateur

        operateur_profile.nom = nom

        operateur_profile.prenom = prenom

        operateur_profile.mail = mail

        operateur_profile.telephone = telephone

        operateur_profile.adresse = adresse



        # Gérer l'image si elle est fournie

        if 'photo' in request.FILES:

            operateur_profile.photo = request.FILES['photo']

        

        operateur_profile.save()



        messages.success(request, "Votre profil a été mis à jour avec succès.")

        return redirect('Superpreparation:profile') # Rediriger vers la page de profil après succès

    else:

        context = {

            'page_title': 'Modifier Profil',

            'page_subtitle': 'Mettez à jour vos informations personnelles',

            'profile': operateur_profile,

        }

        return render(request, 'Superpreparation/modifier_profile.html', context)

@superviseur_preparation_required
def changer_mot_de_passe_view(request):

    """Page de changement de mot de passe pour l'opérateur de préparation - Désactivée"""

    return redirect('Superpreparation:profile')

@superviseur_preparation_required
def detail_prepa(request, pk):

    """Vue détaillée pour la préparation d'une commande spécifique"""

    try:

        operateur_profile = request.user.profil_operateur

        

        # Autoriser superviseur ou équipe préparation

        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):

            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")

            return redirect('Superpreparation:home')

            

    except Operateur.DoesNotExist:

        messages.error(request, "Votre profil opérateur n'existe pas.")

        return redirect('login')



    # Récupérer la commande spécifique

    try:

        commande = Commande.objects.select_related(

            'client', 'ville', 'ville__region'

        ).prefetch_related(

            'paniers__article', 'paniers__variante', 'etats__enum_etat', 'etats__operateur'

        ).get(id=pk)

    except Commande.DoesNotExist:

        messages.error(request, "La commande demandée n'existe pas.")

        return redirect('Superpreparation:liste_prepa')



    # Récupérer l'état de préparation actuel (peut être affecté à n'importe quel opérateur)

    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle='À imprimer') | Q(enum_etat__libelle='En préparation'),
        date_fin__isnull=True
    ).first()

    # Récupérer les paniers (articles) de la commande
    paniers = commande.paniers.all().select_related('article', 'variante', 'variante__couleur', 'variante__pointure')
    
    # Initialiser les variables pour les cas de livraison partielle/renvoi
    articles_livres = []
    articles_renvoyes = []
    is_commande_livree_partiellement = False
    commande_renvoi = None # Initialiser à None
    commande_originale = None # Initialiser à None
    etat_articles_renvoyes = {} # Initialiser à un dictionnaire vide

    # Ajouter le prix unitaire, le total de chaque ligne, et l'URL d'image si disponible
    articles_image_urls = {}
    for panier in paniers:
        panier.prix_unitaire = panier.sous_total / panier.quantite if panier.quantite > 0 else 0
        panier.total_ligne = panier.sous_total
        # Préparer affichage variante (couleur/pointure)
        try:
            panier.couleur_display = (
                panier.variante.couleur.nom if getattr(panier, 'variante', None) and getattr(panier, 'variante', 'couleur', None) else getattr(panier.article, 'couleur', '')
            )
        except Exception:
            panier.couleur_display = getattr(panier.article, 'couleur', '')
        try:
            panier.pointure_display = (
                panier.variante.pointure.pointure if getattr(panier, 'variante', None) and getattr(panier.variante, 'pointure', None) else getattr(panier.article, 'pointure', '')
            )
        except Exception:
            panier.pointure_display = getattr(panier.article, 'pointure', '')
        image_url = None
        try:
            # Protéger l'accès à .url si aucun fichier n'est associé
            if getattr(panier.article, 'image', None):
                # Certains backends lèvent une exception si l'image n'existe pas
                if hasattr(panier.article.image, 'url'):
                    image_url = panier.article.image.url
        except Exception:
            image_url = None
        # Rendre accessible directement dans le template via panier.article.image_url
        setattr(panier.article, 'image_url', image_url)
        # Egalement disponible dans le context si nécessaire
        if getattr(panier.article, 'id', None) is not None:
            articles_image_urls[panier.article.id] = image_url
    
    # Récupérer tous les états de la commande pour afficher l'historique

    etats_commande = commande.etats.all().select_related('enum_etat', 'operateur').order_by('date_debut')

    

    # Déterminer l'état actuel

    etat_actuel = etats_commande.filter(date_fin__isnull=True).first()

    

    # Récupérer l'état précédent pour comprendre d'où vient la commande

    etat_precedent = None

    if etat_actuel:

        # Trouver l'état précédent (le dernier état terminé avant l'état actuel)

        for etat in reversed(etats_commande):

            if etat.date_fin and etat.date_fin < etat_actuel.date_debut:

                if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:

                    etat_precedent = etat

                    break

    

    # Analyser les articles pour les commandes livrées partiellement

    articles_livres = []

    articles_renvoyes = []

    is_commande_livree_partiellement = False

    

    # Import pour JSON

    import json



    # Récupérer l'état des articles renvoyés depuis l'opération de livraison partielle (si elle existe)

    etat_articles_renvoyes = {}

    operation_livraison_partielle = None

    

    # Cas 1: La commande actuelle est la commande originale livrée partiellement

    if etat_actuel and etat_actuel.enum_etat.libelle == 'Livrée Partiellement':

        is_commande_livree_partiellement = True

        # Les articles dans cette commande sont ceux qui ont été livrés partiellement

        for panier in paniers:

            articles_livres.append({

                'article': panier.article,

                'quantite_livree': panier.quantite,

                'prix': panier.article.prix_unitaire,

                'sous_total': panier.sous_total

            })

        

        # Chercher la commande de renvoi associée

        commande_renvoi = Commande.objects.filter(

            num_cmd__startswith=f"RENVOI-{commande.num_cmd}",

            client=commande.client

        ).first()

        

        # La commande source pour les articles renvoyés est la commande actuelle

        operation_livraison_partielle = commande.operations.filter(

            type_operation='LIVRAISON_PARTIELLE'

        ).order_by('-date_operation').first()



    # Cas 2: La commande actuelle est une commande de renvoi suite à une livraison partielle

    elif etat_precedent and etat_precedent.enum_etat.libelle == 'Livrée Partiellement':

        is_commande_livree_partiellement = True

        # Chercher la commande originale qui a été livrée partiellement

        commande_originale = Commande.objects.filter(

            num_cmd=commande.num_cmd.replace('RENVOI-', ''),

            client=commande.client

        ).first()

        

        # La commande source pour les articles renvoyés est la commande originale

        if commande_originale:

            operation_livraison_partielle = commande_originale.operations.filter(

                type_operation='LIVRAISON_PARTIELLE'

            ).order_by('-date_operation').first()



    # Si une opération de livraison partielle est trouvée, extraire les états des articles renvoyés

    if operation_livraison_partielle:

        try:

            details = json.loads(operation_livraison_partielle.conclusion)

            if 'recap_articles_renvoyes' in details:

                for item in details['recap_articles_renvoyes']:

                    etat_articles_renvoyes[item['article_id']] = item['etat']

        except Exception:

            pass



    # Populer articles_renvoyes si c'est une commande de renvoi ou si elle a une commande de renvoi associée

    if is_commande_livree_partiellement:

        # Si la commande actuelle est une commande de renvoi (Cas 2)

        if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):

            for panier_renvoi in paniers:

                etat = etat_articles_renvoyes.get(panier_renvoi.article.id, 'bon')

                articles_renvoyes.append({

                    'article': panier_renvoi.article,

                    'quantite': panier_renvoi.quantite,
                    'prix': panier_renvoi.article.prix_unitaire,
                    'sous_total': panier_renvoi.sous_total,
                    'etat': etat
                })
        # Si la commande actuelle est la commande originale livrée partiellement et qu'une commande de renvoi existe (Cas 1)
        elif commande_renvoi:
            for panier_renvoi in commande_renvoi.paniers.all():
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id, 'bon')
                articles_renvoyes.append({
                    'article': panier_renvoi.article,
                    'quantite': panier_renvoi.quantite,
                    'prix': panier_renvoi.article.prix_unitaire,
                    'sous_total': panier_renvoi.sous_total,
                    'etat': etat
                })
    # Pour les articles livrés, on lit l'opération de livraison partielle sur la commande originale
    if is_commande_livree_partiellement and commande_originale:
        operation_livraison_partielle_for_livres = commande_originale.operations.filter(
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()
        if operation_livraison_partielle_for_livres:
            try:
                details = json.loads(operation_livraison_partielle_for_livres.conclusion)
                if 'articles_livres' in details:
                    for article_livre in details['articles_livres']:
                        article_id = article_livre.get('article_id')
                        if article_id:
                            article = Article.objects.filter(id=article_id).first()
                        if article:
                            articles_livres.append({
                                'article': article,
                                'quantite_livree': article_livre.get('quantite', 0),
                                'prix': article.prix_unitaire,
                                'sous_total': article.prix_unitaire * article_livre.get('quantite', 0)
                            })
            except Exception:
                pass
    # Calculer le total des articles
    total_articles = sum(panier.total_ligne for panier in paniers)
    # Récupérer les opérations associées à la commande
    operations = commande.operations.select_related('operateur').order_by('-date_operation')
    # Générer le code-barres pour la commande
    code128 = barcode.get_barcode_class('code128')
    barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
    buffer = BytesIO()
    barcode_instance.write(buffer, options={'write_text': False, 'module_height': 10.0})
    barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    commande_barcode = f"data:image/png;base64,{barcode_base64}"
    # Gestion des actions POST (marquer comme préparée, etc.)
    if request.method == 'POST':
        action = request.POST.get('action')
        # Action 'commencer_preparation' supprimée car les commandes passent maintenant 
        # directement en "En préparation" lors de l'affectation
        if action == 'marquer_preparee':
            with transaction.atomic():
                # Marquer l'état 'En préparation' comme terminé
                etat_en_preparation, created = EnumEtatCmd.objects.get_or_create(libelle='En préparation')
                etat_actuel = EtatCommande.objects.filter(
                    commande=commande,
                    enum_etat=etat_en_preparation,
                    date_fin__isnull=True
                ).first()
                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.operateur = operateur_profile
                    etat_actuel.save()
                # Créer le nouvel état 'Préparée'
                etat_preparee, created = EnumEtatCmd.objects.get_or_create(libelle='Préparée')
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_preparee,
                    operateur=operateur_profile
                )
                # Log de l'opération
                Operation.objects.create(
                    commande=commande,
                    type_operation='PREPARATION_TERMINEE',
                    operateur=operateur_profile,
                    conclusion=f"Commande marquée comme préparée par {operateur_profile.nom_complet}."
                )
            messages.success(request, f"La commande {commande.id_yz} a bien été marquée comme préparée.")
            return redirect('Superpreparation:detail_prepa', pk=commande.pk)
        elif action == 'signaler_probleme':
            with transaction.atomic():
                # 1. Terminer l'état "En préparation" actuel
                etat_en_preparation_enum = get_object_or_404(EnumEtatCmd, libelle='En préparation')
                etat_actuel = EtatCommande.objects.filter(
                    commande=commande,
                    enum_etat=etat_en_preparation_enum,
                    date_fin__isnull=True
                ).first()
                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.commentaire = "Problème signalé par le préparateur."
                    etat_actuel.save()
                # 2. Trouver l'opérateur de confirmation d'origine
                operateur_confirmation_origine = None
                etats_precedents = commande.etats.select_related('operateur').order_by('-date_debut')
                for etat in etats_precedents:
                    if etat.operateur and etat.operateur.is_confirmation:
                        operateur_confirmation_origine = etat.operateur
                        break
                # 3. Créer l'état "Retour Confirmation" et l'affecter
                etat_retour_enum, _ = EnumEtatCmd.objects.get_or_create(
                    libelle='Retour Confirmation',
                    defaults={'ordre': 25, 'couleur': '#D97706'}
                )
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_retour_enum,
                    operateur=operateur_confirmation_origine, # Affectation directe
                    date_debut=timezone.now(),
                    commentaire="Retourné par la préparation pour vérification."
                )
                # 4. Log et message de succès
                if operateur_confirmation_origine:
                    log_conclusion = f"Problème signalé par {operateur_profile.nom_complet}. Commande retournée et affectée à l'opérateur {operateur_confirmation_origine.nom_complet}."
                    messages.success(request, f"La commande {commande.id_yz} a été retournée à {operateur_confirmation_origine.nom_complet} pour vérification.")
                else:
                    log_conclusion = f"Problème signalé par {operateur_profile.nom_complet}. Opérateur d'origine non trouvé, commande renvoyée au pool de confirmation."
                    messages.warning(request, f"La commande {commande.id_yz} a été renvoyée au pool de confirmation (opérateur d'origine non trouvé).")
                Operation.objects.create(
                    commande=commande,
                    type_operation='PROBLEME_SIGNALÉ',
                    operateur=operateur_profile,
                    conclusion=log_conclusion
                )
            return redirect('Superpreparation:liste_prepa')
    # Avant le return render dans detail_prepa
    commande_renvoi_id = None
    if commande_renvoi:
        commande_renvoi_id = commande_renvoi.id
    context = {
        'page_title': f'Préparation Commande {commande.id_yz}',
        'page_subtitle': f'Détails de la commande et étapes de préparation',
        'commande': commande,
        'paniers': paniers,
        'etats_commande': etats_commande,
        'etat_actuel': etat_actuel,
        'etat_precedent': etat_precedent,
        'etat_preparation': etat_preparation,
        'total_articles': total_articles,
        'operations': operations,
        'commande_barcode': commande_barcode,
        'is_commande_livree_partiellement': is_commande_livree_partiellement,
        'articles_livres': articles_livres,
        'articles_renvoyes': articles_renvoyes,
        'articles_image_urls': articles_image_urls,
        # Variables de debug/informations supplémentaires
        'commande_originale': commande_originale,
        'commande_renvoi': commande_renvoi,
        'etat_articles_renvoyes': etat_articles_renvoyes,
        'commande_renvoi_id': commande_renvoi_id,
    }
    return render(request, 'Superpreparation/detail_prepa.html', context)

@superviseur_preparation_required
def api_commandes_confirmees(request):
    """API pour récupérer toutes les commandes confirmées"""
    try:
        commandes_confirmees = Commande.objects.filter(
            etats__enum_etat__libelle='Confirmée'
        ).select_related('client').distinct()
        commandes_data = []
        for commande in commandes_confirmees:
            commandes_data.append({
                'id': commande.id_yz,
                'client_nom': f"{commande.client.prenom} {commande.client.nom}",
                'date_creation': commande.date_creation.strftime('%Y-%m-%d %H:%M:%S'),
                'total': float(commande.total_cmd)
            })
        return JsonResponse({
            'success': True,
            'commandes': commandes_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@superviseur_preparation_required
def api_articles_commande(request, commande_id):
    """API pour récupérer les articles d'une commande avec leurs codes-barres"""
    try:
        commande = get_object_or_404(
            Commande.objects.select_related('client').prefetch_related(
                'paniers__article', 'paniers__variante'
            ),
            id_yz=commande_id
        )
        articles_data = []
        for panier in commande.paniers.all():
            reference = panier.article.reference
            if panier.variante and panier.variante.reference_variante:
                reference = panier.variante.reference_variante
            try:
                from .templatetags.barcode_filters import barcode_image_url
                barcode_url = barcode_image_url(reference)
            except Exception as e:
                barcode_url = ""
            article_data = {
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'quantite': panier.quantite,
                'sous_total': float(panier.sous_total),
                'barcode_url': barcode_url,
            }
            if panier.variante:
                variante_info = {
                    'reference_variante': panier.variante.reference_variante,
                }
                if panier.variante.couleur:
                    variante_info['couleur'] = panier.variante.couleur.nom
                if panier.variante.pointure:
                    variante_info['pointure'] = panier.variante.pointure.pointure
                article_data['variante'] = variante_info
            articles_data.append(article_data)
        return JsonResponse({
            'success': True,
            'articles': articles_data,
            'commande_id': commande.id_yz,
            'client': f"{commande.client.prenom} {commande.client.nom}"
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@superviseur_preparation_required
def api_commande_produits(request, commande_id):
    """API pour récupérer les produits d'une commande pour les étiquettes"""
    try:
        # Récupérer la commande. La sécurité est déjà gérée par la page
        # qui appelle cette API, qui ne liste que les commandes autorisées.
        commande = Commande.objects.get(id=commande_id)
        # Récupérer tous les produits de la commande (avec variantes)
        paniers = (
            commande.paniers.all()
            .select_related('article', 'variante', 'variante__couleur', 'variante__pointure')
        )

        # Construire un rendu HTML des produits pour une meilleure lisibilité dans le ticket
        elements_html = []
        total_qte = 0
        for panier in paniers:
            if panier.article:
                nom = panier.article.nom or ''
                reference = panier.article.reference or ''
                couleur = getattr(getattr(panier.variante, 'couleur', None), 'nom', '') if getattr(panier, 'variante', None) else ''
                pointure = getattr(getattr(panier.variante, 'pointure', None), 'pointure', '') if getattr(panier, 'variante', None) else ''
                ref_var = getattr(panier.variante, 'reference_variante', None) if getattr(panier, 'variante', None) else None
                reference_affichee = ref_var or reference

                details = " ".join([v for v in [reference_affichee, couleur, f"P{pointure}" if pointure else ''] if v])
                elements_html.append(f"<li><strong>{nom}</strong> {details} ×{panier.quantite}</li>")
                total_qte += panier.quantite

        

        # Joindre tous les produits en une liste HTML
        produits_text = (
            "<ul class=\"ticket-products\">" + "".join(elements_html) + "</ul>"
            if elements_html else "PRODUITS NON SPÉCIFIÉS"
        )

        

        return JsonResponse({
            'success': True,
            'produits': produits_text,
            'nombre_articles': total_qte,
        })

        

    except Commande.DoesNotExist:

        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})

    except Exception as e:

        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@superviseur_preparation_required
def modifier_commande_prepa(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de préparation"""
    import json
    from commande.models import Commande, Operation
    from parametre.models import Ville
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de préparation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Vérifier que la commande est affectée à cet opérateur pour la préparation
    etat_preparation = commande.etats.filter(
        Q(enum_etat__enum_etat__libelle='À imprimer') | Q(enum_etat__enum_etat__libelle='En préparation'),
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_preparation:
        messages.error(request, "Cette commande ne vous est pas affectée pour la préparation.")
        return redirect('Superpreparation:liste_prepa')
    
    if request.method == 'POST':
        try:
            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================
            action = request.POST.get('action')
            
            if action == 'add_article':
                # Ajouter un nouvel article immédiatement
                from article.models import Article
                from commande.models import Panier
                
                article_id = request.POST.get('article_id')
                quantite = int(request.POST.get('quantite', 1))
                
                try:
                    article = Article.objects.get(id=article_id)
                    panier_existant = Panier.objects.filter(commande=commande, article=article).first()
                    if panier_existant:
                        # Si l'article existe déjà, mettre à jour la quantité
                        panier_existant.quantite += quantite
                        panier_existant.save()
                        panier = panier_existant
                        print(f"🔄 Article existant mis à jour: ID={article.id}, nouvelle quantité={panier.quantite}")
                    else:
                        # Si l'article n'existe pas, créer un nouveau panier
                        panier = Panier.objects.create(
                            commande=commande,
                            article=article,
                            quantite=quantite,
                            sous_total=0  # Sera recalculé après
                        )
                        print(f"➕ Nouvel article ajouté: ID={article.id}, quantité={quantite}")
                    # Recalculer le compteur après ajout (logique de confirmation)
                    if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:
                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                            total=Sum('quantite')
                        )['total'] or 0
                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        commande.save()
                        commande.recalculer_totaux_upsell()
                    else:
                        # Pour les articles normaux, juste calculer le sous-total
                        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                        prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)
                        sous_total = prix_unitaire * panier.quantite
                        panier.sous_total = float(sous_total)
                        panier.save()
                    total_articles = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0
                    commande.total_cmd = float(total_articles) #+ float(frais_livraison)
                    commande.save()
                    # Calculer les statistiques upsell pour la réponse
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = articles_upsell.aggregate(
                        total=Sum('quantite')
                    )['total'] or 0
                            # Déterminer si c'était un ajout ou une mise à jour
                    message = 'Article ajouté avec succès' if not panier_existant else f'Quantité mise à jour ({panier.quantite})'
                    article_data = {
                        'panier_id': panier.id,
                        'nom': article.nom,
                        'reference': article.reference,
                        'couleur_fr': article.couleur or '',
                        'couleur_ar': article.couleur or '',
                        'pointure': article.pointure or '',
                        'quantite': panier.quantite,
                        'prix': panier.sous_total / panier.quantite,  # Prix unitaire
                        'sous_total': panier.sous_total,
                        'is_upsell': article.isUpsell,
                        'phase': article.phase,
                        'has_promo_active': article.has_promo_active,
                        'qte_disponible': article.qte_disponible,
                        'description': article.description or ''
                    }
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'article_id': panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur,
                        'was_update': panier_existant is not None,
                        'new_quantity': panier.quantite,
                        'article_data': article_data,
                        'articles_count': commande.paniers.count(),
                        'sous_total_articles': float(sum(p.sous_total for p in commande.paniers.all())),
                        'articles_upsell': articles_upsell.count(),
                        'quantite_totale_upsell': total_quantite_upsell
                    })
                except Article.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Article non trouvé'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            elif action == 'replace_article':
                # Remplacer un article existant
                from article.models import Article
                from commande.models import Panier

                ancien_article_id = request.POST.get('ancien_article_id')
                nouvel_article_id = request.POST.get('nouvel_article_id')
                nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 1))
                try:
                    ancien_panier = Panier.objects.get(id=ancien_article_id, commande=commande)
                    ancien_article = ancien_panier.article
                    ancien_etait_upsell = ancien_article.isUpsell
                    ancien_panier.delete()
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                        total=Sum('quantite')
                    )['total'] or 0
                    if nouvel_article.isUpsell:
                        total_quantite_upsell += nouvelle_quantite
                    if total_quantite_upsell >= 2:
                        commande.compteur = total_quantite_upsell - 1
                    else:
                        commande.compteur = 0

                    commande.save()

                    commande.recalculer_totaux_upsell()

                    from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                    prix_unitaire = get_prix_upsell_avec_compteur(nouvel_article, commande.compteur)
                    sous_total = prix_unitaire * nouvelle_quantite
                    nouveau_panier = Panier.objects.create(
                        commande=commande,
                        article=nouvel_article,
                        quantite=nouvelle_quantite,
                        sous_total=float(sous_total)
                    )

                    total_commande = commande.paniers.aggregate(

                        total=Sum('sous_total')

                    )['total'] or 0

                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0

                    commande.total_cmd = float(total_commande) #+ float(frais_livraison)

                    commande.save()

                    

                    # Calculer les statistiques upsell pour la réponse

                    articles_upsell = commande.paniers.filter(article__isUpsell=True)

                    total_quantite_upsell = articles_upsell.aggregate(

                        total=Sum('quantite')

                    )['total'] or 0

                    

                    return JsonResponse({

                        'success': True,

                        'message': 'Article remplacé avec succès',

                        'nouvel_article_id': nouveau_panier.id,

                        'total_commande': float(commande.total_cmd),

                        'nb_articles': commande.paniers.count(),

                        'compteur': commande.compteur,

                        'articles_upsell': articles_upsell.count(),

                        'quantite_totale_upsell': total_quantite_upsell,

                        'sous_total_articles': float(commande.sous_total_articles)

                    })

                    

                except Panier.DoesNotExist:

                    return JsonResponse({

                        'success': False,

                        'error': 'Article original non trouvé'

                    })

                except Article.DoesNotExist:

                    return JsonResponse({

                        'success': False,

                        'error': 'Nouvel article non trouvé'

                    })

                except Exception as e:

                    return JsonResponse({

                        'success': False,

                        'error': str(e)

                    })

            

            

            elif action == 'update_operation':

                # Mettre à jour une opération existante

                try:

                    from commande.models import Operation

                    import logging

                    logger = logging.getLogger(__name__)

                    

                    operation_id = request.POST.get('operation_id')

                    nouveau_commentaire = request.POST.get('nouveau_commentaire', '').strip()

                    

                    if not operation_id or not nouveau_commentaire:

                        return JsonResponse({'success': False, 'error': 'ID opération et commentaire requis'})

                    

                    # Récupérer et mettre à jour l'opération

                    operation = Operation.objects.get(id=operation_id, commande=commande)

                    operation.conclusion = nouveau_commentaire

                    operation.operateur = operateur  # Mettre à jour l'opérateur qui modifie

                    operation.save()

                    

                    return JsonResponse({

                        'success': True,

                        'message': 'Opération mise à jour avec succès',

                        'operation_id': operation_id,

                        'nouveau_commentaire': nouveau_commentaire

                    })

                    

                except Operation.DoesNotExist:

                    return JsonResponse({

                        'success': False,

                        'error': 'Opération non trouvée'

                    })

                except Exception as e:

                    return JsonResponse({

                        'success': False,

                        'error': str(e)

                    })

            

            elif action == 'add_operation':

                # Ajouter une nouvelle opération

                try:

                    from commande.models import Operation

                    

                    type_operation = request.POST.get('type_operation', '').strip()

                    commentaire = request.POST.get('commentaire', '').strip()

                    

                    if not type_operation or not commentaire:

                        return JsonResponse({

                            'success': False,

                            'error': 'Type d\'opération et commentaire requis'

                        })

                    

                    # Créer la nouvelle opération

                    operation = Operation.objects.create(
                        commande=commande,
                        type_operation=type_operation,
                        conclusion=commentaire,
                        operateur=operateur
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Opération ajoutée avec succès',
                        'operation_id': operation.id,
                        'type_operation': type_operation,
                        'commentaire': commentaire
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'modifier_quantites_multiple':
                # Modifier plusieurs quantités d'articles en une fois
                try:
                    from commande.models import Panier
                    import json
                    
                    modifications_json = request.POST.get('modifications', '[]')
                    modifications = json.loads(modifications_json)
                    
                    if not modifications:
                        return JsonResponse({
                            'success': False,
                            'error': 'Aucune modification fournie'
                        })
                    for mod in modifications:
                        panier_id = mod.get('panier_id')
                        nouvelle_quantite = mod.get('nouvelle_quantite', 0)
                        try:
                            panier = Panier.objects.get(id=panier_id, commande=commande)
                            
                            if nouvelle_quantite <= 0:
                                # Supprimer l'article si quantité = 0
                                panier.delete()
                            else:
                                # Mettre à jour la quantité et le sous-total
                                panier.quantite = nouvelle_quantite
                                panier.sous_total = float(panier.article.prix_unitaire * nouvelle_quantite)
                                panier.save()
                        except Panier.DoesNotExist:
                            continue  # Ignorer les paniers non trouvés

                    total_commande = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_QUANTITES',
                        conclusion=f"Modification en masse des quantités d'articles par l'opérateur de préparation.",
                        operateur=operateur
                    )
                    return JsonResponse({
                        'success': True,
                        'message': f'{len(modifications)} quantité(s) modifiée(s) avec succès',
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                    })
                    
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Format de données invalide'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'modifier_quantite_directe':
                # Modifier directement la quantité d'un article
                try:
                    from commande.models import Panier
                    
                    panier_id = request.POST.get('panier_id')
                    nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 0))
                    
                    print(f"🔄 Modification quantité directe - Panier ID: {panier_id}, Nouvelle quantité: {nouvelle_quantite}")
                    
                    if nouvelle_quantite < 0:
                        return JsonResponse({
                            'success': False,
                            'error': 'La quantité ne peut pas être négative'
                        })
                    try:
                        panier = Panier.objects.get(id=panier_id, commande=commande)
                        ancienne_quantite = panier.quantite
                        nouveau_sous_total = 0
                        print(f"📦 Article trouvé: {panier.article.nom}, Ancienne quantité: {ancienne_quantite}")
                        if panier.commande.id != commande.id:
                            print(f"❌ ERREUR: Le panier {panier_id} n'appartient pas à la commande {commande.id}")
                            return JsonResponse({
                                'success': False,
                                'error': 'Article non trouvé dans cette commande'
                            })
                        
                        if nouvelle_quantite == 0:
                            # Supprimer l'article si quantité = 0
                            panier.delete()
                            message = 'Article supprimé avec succès'
                        else:
                            # Mettre à jour la quantité et le sous-total avec la logique complète de prix
                            panier.quantite = nouvelle_quantite
                            
                            # Recalculer le compteur si c'est un article upsell
                            if panier.article.isUpsell:
                                # Sauvegarder d'abord la nouvelle quantité
                                panier.save()
                                
                                # Compter la quantité totale d'articles upsell après modification
                                total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                                    total=Sum('quantite')
                                )['total'] or 0
                                print(f"🔄 Calcul du compteur upsell: total_quantite_upsell = {total_quantite_upsell}")
                                if total_quantite_upsell >= 2:
                                    commande.compteur = total_quantite_upsell - 1
                                else:
                                    commande.compteur = 0
                            
                                print(f"✅ Nouveau compteur calculé: {commande.compteur}")
                                commande.save()
                                
                                # Recalculer TOUS les articles de la commande avec le nouveau compteur
                                commande.recalculer_totaux_upsell()
                            else:
                                # Pour les articles normaux, mettre à jour la quantité et calculer le sous-total
                                from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                                prix_unitaire = get_prix_upsell_avec_compteur(panier.article, commande.compteur)
                                panier.quantite = nouvelle_quantite
                                panier.sous_total = float(prix_unitaire * nouvelle_quantite)
                                panier.save()
                            
                            nouveau_sous_total = panier.sous_total
                            message = 'Quantité modifiée avec succès'
                            
                            print(f"✅ Quantité mise à jour: {ancienne_quantite} → {nouvelle_quantite}, Nouveau sous-total: {nouveau_sous_total}")
                            
                            # Vérifier que la mise à jour a bien été sauvegardée
                            panier.refresh_from_db()
                            if panier.quantite != nouvelle_quantite:
                                print(f"❌ ERREUR: La quantité n'a pas été sauvegardée correctement. Attendu: {nouvelle_quantite}, Actuel: {panier.quantite}")
                            else:
                                print(f"✅ Vérification OK: Quantité sauvegardée: {panier.quantite}")
                    except Panier.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'error': 'Article non trouvé'
                        })
                    # Recalculer le total de la commande avec frais de livraison
                    total_articles = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0
                    commande.total_cmd = float(total_articles) #+ float(frais_livraison)
                    commande.save()
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = articles_upsell.aggregate(
                        total=Sum('quantite')
                    )['total'] or 0

                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_QUANTITE',
                        conclusion=f"Quantité d'article modifiée de {ancienne_quantite} à {nouvelle_quantite}.",
                        operateur=operateur
                    )

                    
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'sous_total': float(nouveau_sous_total),
                        'sous_total_articles': float(total_articles),
                        'total_commande': float(commande.total_cmd),
                        'frais_livraison': float(frais_livraison),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur,
                        'articles_upsell': articles_upsell.count(),
                        'quantite_totale_upsell': total_quantite_upsell
                    })
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Quantité invalide'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            elif action == 'update_commande_info':
                # Mettre à jour les informations de base de la commande
                try:
                    nouvelle_adresse = request.POST.get('adresse', '').strip()
                    nouvelle_ville_id = request.POST.get('ville_id')
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Ville non trouvée'
                            })
                    commande.save()
                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_PREPA',
                        conclusion=f"La commande a été modifiée par l'opérateur.",
                        operateur=operateur
                    )
                    messages.success(request, f"Commande {commande.id_yz} mise à jour avec succès.")
                    return redirect('Superpreparation:detail_prepa', pk=commande.id)
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            else:
                # Traitement du formulaire principal (non-AJAX)
                with transaction.atomic():
                    # Mettre à jour les informations du client
                    client = commande.client
                    client.nom = request.POST.get('client_nom', client.nom).strip()
                    client.prenom = request.POST.get('client_prenom', client.prenom).strip()
                    client.numero_tel = request.POST.get('client_telephone', client.numero_tel).strip()
                    client.save()
                    # Mettre à jour les informations de base de la commande
                    nouvelle_adresse = request.POST.get('adresse', '').strip()
                    nouvelle_ville_id = request.POST.get('ville_id')
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            messages.error(request, "Ville sélectionnée non trouvée.")
                            return redirect('Superpreparation:modifier_commande', commande_id=commande.id)

                    commande.save()
                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_PREPA',
                        conclusion=f"La commande a été modifiée par l'opérateur.",
                        operateur=operateur
                    )
                    messages.success(request, f"Les modifications de la commande {commande.id_yz} ont été enregistrées avec succès.")
                    return redirect('Superpreparation:detail_prepa', pk=commande.id)
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            return redirect('Superpreparation:modifier_commande', commande_id=commande.id)
    # Récupérer les données pour l'affichage
    paniers = commande.paniers.all().select_related('article')
    operations = commande.operations.all().select_related('operateur').order_by('-date_operation')
    villes = Ville.objects.all().order_by('nom')
    # Calculer le total des articles
    total_articles = sum(panier.sous_total for panier in paniers)
    # Vérifier si c'est une commande renvoyée par la logistique
    operation_renvoi = operations.filter(type_operation='RENVOI_PREPARATION').first()
    is_commande_renvoyee = operation_renvoi is not None
    # Initialiser les variables pour les cas de livraison partielle/renvoi
    articles_livres = []
    articles_renvoyes = []
    is_commande_livree_partiellement = False
    commande_renvoi_obj = None # Variable pour la commande de renvoi trouvée
    commande_originale_obj = None # Variable pour la commande originale trouvée
    etat_articles_renvoyes = {} # Dictionnaire pour stocker l'état des articles renvoyés (article_id -> etat)
    operation_livraison_partielle_source = None # Opération source pour les détails de livraison partielle
    # Récupérer l'état actuel de la commande
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    etat_precedent = None
    if etat_actuel:
        # Trouver l'état précédent
        etats_precedents = commande.etats.all().order_by('-date_debut')
        for etat in etats_precedents:
            if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:
                    etat_precedent = etat
                    break

    if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
        # C'est une commande de renvoi. On cherche la commande originale.
        num_cmd_original = commande.num_cmd.replace('RENVOI-', '')
        commande_originale_obj = Commande.objects.filter(num_cmd=num_cmd_original, client=commande.client).first()
        if commande_originale_obj:
            # Vérifier si la commande originale a bien été livrée partiellement
            if commande_originale_obj.etats.filter(enum_etat__libelle='Livrée Partiellement').exists():
                is_commande_livree_partiellement = True
                operation_livraison_partielle_source = commande_originale_obj.operations.filter(
                    type_operation='LIVRAISON_PARTIELLE'
                ).order_by('-date_operation').first()
                commande_renvoi_obj = commande # Dans ce cas, la commande actuelle est la commande de renvoi
    elif etat_actuel and etat_actuel.enum_etat.libelle == 'Livrée Partiellement':
        # La commande actuelle est l'originale qui a été livrée partiellement
        is_commande_livree_partiellement = True
        operation_livraison_partielle_source = commande.operations.filter(
            type_operation='LIVRAISON_PARTIELLE'
        ).order_by('-date_operation').first()
        # Chercher une commande de renvoi associée si elle existe
        commande_renvoi_obj = Commande.objects.filter(
            num_cmd__startswith=f"RENVOI-{commande.num_cmd}",
            client=commande.client
        ).first()
    # Si une opération de livraison partielle est trouvée, extraire les états des articles renvoyés
    if operation_livraison_partielle_source:
        try:
            details = json.loads(operation_livraison_partielle_source.conclusion)
            if 'recap_articles_renvoyes' in details:
                for item in details['recap_articles_renvoyes']:
                    etat_articles_renvoyes[item['article_id']] = item['etat']
            # Populer articles_livres à partir de la conclusion de l'opération de livraison partielle
            if 'articles_livres' in details:
                for article_livre in details['articles_livres']:
                    article_id = article_livre.get('article_id')
                    if article_id:
                        article_obj = Article.objects.filter(id=article_id).first()
                    if article_obj:
                        articles_livres.append({
                            'article': article_obj,
                            'quantite_livree': article_livre.get('quantite', 0),
                            'prix': article_obj.prix_unitaire,
                            'sous_total': article_obj.prix_unitaire * article_livre.get('quantite', 0)
                        })
        except Exception as e:
            print(f"DEBUG: Erreur lors du parsing des détails de l'opération de livraison partielle: {e}")
            pass
    # Populer articles_renvoyes si c'est une commande de renvoi ou si elle a une commande de renvoi associée
    if is_commande_livree_partiellement:
        # Si la commande actuelle est une commande de renvoi (celle que nous modifions)
        if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
            # Les paniers de la commande actuelle sont les articles renvoyés
            for panier_renvoi in paniers:
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id)
                if etat is None:
                    etat = 'inconnu'
                    print(f"ALERTE: État inconnu pour l'article ID {panier_renvoi.article.id} dans la commande {commande.id_yz}")
                articles_renvoyes.append({
                    'article': panier_renvoi.article,
                    'quantite': panier_renvoi.quantite,
                    'prix': panier_renvoi.article.prix_unitaire,
                    'sous_total': panier_renvoi.sous_total,
                    'etat': etat
                })
        # Si la commande actuelle est la commande originale livrée partiellement (Cas 1 initial)
        elif commande_renvoi_obj:
            # Les paniers de la commande de renvoi associée sont les articles renvoyés
            for panier_renvoi in commande_renvoi_obj.paniers.all():
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id)
                if etat is None:
                    etat = 'inconnu'
                    print(f"ALERTE: État inconnu pour l'article ID {panier_renvoi.article.id} dans la commande {commande_renvoi_obj.id_yz}")
                articles_renvoyes.append({
                    'article': panier_renvoi.article,
                    'quantite': panier_renvoi.quantite,
                    'prix': panier_renvoi.article.prix_unitaire,
                    'sous_total': panier_renvoi.sous_total,
                    'etat': etat
                })
    print(f"DEBUG (modifier_commande_prepa): articles_renvoyes APRES POPULATION: {articles_renvoyes}")
    context = {
        'page_title': "Modifier Commande " + str(commande.id_yz),
        'page_subtitle': "Modification des détails de la commande en préparation",
        'commande': commande,
        'paniers': paniers,
        'villes': villes,
        'total_articles': total_articles,
        'is_commande_renvoyee': is_commande_renvoyee,
        'operation_renvoi': operation_renvoi,
        'is_commande_livree_partiellement': is_commande_livree_partiellement,
        'articles_livres': articles_livres,
        'articles_renvoyes': articles_renvoyes,
        # Variables de debug/informations supplémentaires
        'commande_originale': commande_originale_obj,
        'commande_renvoi': commande_renvoi_obj,
        'etat_articles_renvoyes': etat_articles_renvoyes,
        # 'articles_renvoyes_map': articles_renvoyes_map, # Retiré car plus nécessaire
    }
    return render(request, 'Superpreparation/modifier_commande.html', context)

@superviseur_preparation_required
def modifier_commande_superviseur(request, commande_id):

    """Page de modification complète d'une commande pour les superviseurs de préparation"""

    import json

    from commande.models import Commande, Operation

    from parametre.models import Ville

    

    try:

        # Accepter PREPARATION et SUPERVISEUR_PREPARATION

        operateur = Operateur.objects.get(user=request.user, actif=True)

        if operateur.type_operateur not in ['PREPARATION', 'SUPERVISEUR_PREPARATION']:

            messages.error(request, "Accès non autorisé. Réservé à l'équipe préparation.")

            return redirect('Superpreparation:home')

    except Operateur.DoesNotExist:

        # Pas de profil: continuer (le décorateur a déjà validé l'accès via groupes)

        operateur = None

    

    # Récupérer la commande avec ses relations

    commande = get_object_or_404(Commande.objects.select_related('client', 'ville', 'ville__region'), id=commande_id)

    

    # Pour les superviseurs, on ne vérifie pas l'affectation spécifique

    # Ils peuvent modifier toutes les commandes en préparation

    

    if request.method == 'POST':

        try:

            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================

            action = request.POST.get('action')

            

            if action == 'add_article':

                # Ajouter un nouvel article immédiatement

                from article.models import Article

                from commande.models import Panier

                

                article_id = request.POST.get('article_id')

                quantite = int(request.POST.get('quantite', 1))

                

                try:

                    article = Article.objects.get(id=article_id)

                    

                    # Vérifier si l'article existe déjà dans la commande

                    panier_existant = Panier.objects.filter(commande=commande, article=article).first()

                    

                    if panier_existant:

                        # Si l'article existe déjà, mettre à jour la quantité

                        panier_existant.quantite += quantite

                        panier_existant.save()

                        panier = panier_existant

                        print(f"🔄 Article existant mis à jour: ID={article.id}, nouvelle quantité={panier.quantite}")

                    else:

                        # Si l'article n'existe pas, créer un nouveau panier

                        panier = Panier.objects.create(

                            commande=commande,

                            article=article,

                            quantite=quantite,

                            sous_total=0  # Sera recalculé après

                        )

                        print(f"➕ Nouvel article ajouté: ID={article.id}, quantité={quantite}")

                    

                    # Recalculer le compteur après ajout (logique de confirmation)

                    if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:

                        # Compter la quantité totale d'articles upsell (après ajout)

                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(

                            total=Sum('quantite')

                        )['total'] or 0

                        

                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell

                        # 0-1 unités upsell → compteur = 0

                        # 2+ unités upsell → compteur = total_quantite_upsell - 1

                        if total_quantite_upsell >= 2:

                            commande.compteur = total_quantite_upsell - 1

                        else:

                            commande.compteur = 0

                        

                        commande.save()

                        

                        # Recalculer TOUS les articles de la commande avec le nouveau compteur

                        commande.recalculer_totaux_upsell()

                    else:

                        # Pour les articles normaux, juste calculer le sous-total

                        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur

                        prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)

                        sous_total = prix_unitaire * panier.quantite

                        panier.sous_total = float(sous_total)

                        panier.save()

                    

                    # Recalculer le total de la commande avec frais de livraison

                    total_articles = commande.paniers.aggregate(

                        total=Sum('sous_total')

                    )['total'] or 0

                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0

                    commande.total_cmd = float(total_articles) #+ float(frais_livraison)

                    commande.save()

                    

                    # Calculer les statistiques upsell pour la réponse

                    articles_upsell = commande.paniers.filter(article__isUpsell=True)

                    total_quantite_upsell = articles_upsell.aggregate(

                        total=Sum('quantite')

                    )['total'] or 0

                    

                    return JsonResponse({

                        'success': True,

                        'message': f'Article {article.nom} ajouté avec succès',

                        'article_id': article.id,

                        'article_nom': article.nom,

                        'quantite': panier.quantite,

                        'sous_total': float(panier.sous_total),

                        'compteur_upsell': commande.compteur,

                        'total_quantite_upsell': total_quantite_upsell,

                        'total_commande': float(commande.total_cmd),

                        'frais_livraison': float(frais_livraison),

                        'total_final': float(commande.total_cmd) + float(frais_livraison)

                    })

                    

                except Article.DoesNotExist:

                    return JsonResponse({'success': False, 'message': 'Article non trouvé'})

                except Exception as e:

                    print(f"❌ Erreur lors de l'ajout d'article: {e}")

                    return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

            

            elif action in ['modify_quantity', 'modifier_quantite_directe', 'update_article']:

                # Modifier la quantité d'un article existant

                from commande.models import Panier

                

                panier_id = request.POST.get('panier_id')

                # Les différentes actions peuvent envoyer des noms différents

                quantite_str = request.POST.get('nouvelle_quantite') or request.POST.get('quantite') or request.POST.get('new_quantity')

                try:

                    nouvelle_quantite = int(quantite_str) if quantite_str is not None else 1

                except ValueError:

                    nouvelle_quantite = 1

                

                try:

                    panier = Panier.objects.get(id=panier_id, commande=commande)

                    article = panier.article

                    

                    if nouvelle_quantite <= 0:

                        # Supprimer l'article si quantité <= 0

                        panier.delete()

                        message = f'Article {article.nom} supprimé de la commande'

                    else:

                        # Mettre à jour la quantité

                        panier.quantite = nouvelle_quantite

                        

                        # Recalculer le sous-total

                        if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:

                            # Recalculer le compteur upsell

                            total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(

                                total=Sum('quantite')

                            )['total'] or 0

                            

                            if total_quantite_upsell >= 2:
                                commande.compteur = total_quantite_upsell - 1
                            else:
                                commande.compteur = 0
                            
                            commande.save()
                            commande.recalculer_totaux_upsell()
                        else:
                            from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                            prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)
                            sous_total = prix_unitaire * panier.quantite
                            panier.sous_total = float(sous_total)
                            panier.save()
                        
                        message = f'Quantité de {article.nom} mise à jour: {nouvelle_quantite}'
                    
                    # Recalculer le total de la commande
                    total_articles = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0
                    commande.total_cmd = float(total_articles) #+ float(frais_livraison)
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'sous_total': float(panier.sous_total) if nouvelle_quantite > 0 else 0,
                        'compteur_upsell': commande.compteur,
                        'total_commande': float(commande.total_cmd),
                        'frais_livraison': float(frais_livraison),
                        'total_final': float(commande.total_cmd) + float(frais_livraison)
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Article non trouvé dans la commande'})
                except Exception as e:
                    print(f"❌ Erreur lors de la modification de quantité: {e}")
                    return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
            
            elif action == 'delete_article':
                # Supprimer un article de la commande
                from commande.models import Panier
                
                panier_id = request.POST.get('panier_id')
                
                try:
                    panier = Panier.objects.get(id=panier_id, commande=commande)
                    article_nom = panier.article.nom
                    etait_upsell = panier.article.isUpsell  # Sauvegarder avant suppression

                    panier.delete()

                    

                    # Recalculer le compteur upsell si nécessaire

                    if etait_upsell:

                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(

                            total=Sum('quantite')

                        )['total'] or 0

                        

                        if total_quantite_upsell >= 2:

                            commande.compteur = total_quantite_upsell - 1

                        else:

                            commande.compteur = 0

                        

                        commande.save()

                        commande.recalculer_totaux_upsell()

                    

                    # Recalculer le total de la commande

                    total_articles = commande.paniers.aggregate(

                        total=Sum('sous_total')

                    )['total'] or 0

                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0

                    commande.total_cmd = float(total_articles) #+ float(frais_livraison)

                    commande.save()

                    

                    return JsonResponse({

                        'success': True,

                        'message': f'Article {article_nom} supprimé avec succès',

                        'compteur_upsell': commande.compteur,

                        'articles_count': commande.paniers.count(),

                        'total_commande': float(commande.total_cmd),

                        'frais_livraison': float(frais_livraison),

                        'total_final': float(commande.total_cmd) + float(frais_livraison)

                    })

                    

                except Panier.DoesNotExist:

                    return JsonResponse({'success': False, 'message': 'Article non trouvé dans la commande'})

                except Exception as e:

                    print(f"❌ Erreur lors de la suppression d'article: {e}")

                    return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

            

            else:

                # Soumission du formulaire principal (pas d'action AJAX)

                try:

                    nouvelle_adresse = request.POST.get('adresse', '').strip()

                    nouvelle_ville_id = request.POST.get('ville_id')



                    if nouvelle_adresse:

                        commande.adresse = nouvelle_adresse



                    if nouvelle_ville_id:

                        try:

                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)

                            commande.ville = nouvelle_ville

                        except Ville.DoesNotExist:

                            messages.error(request, "Ville sélectionnée non trouvée.")

                            return redirect('Superpreparation:modifier_commande_superviseur', commande_id=commande.id)



                    commande.save()



                    # Journaliser l'opération

                    Operation.objects.create(

                        commande=commande,

                        type_operation='MODIFICATION_PREPA',

                        conclusion=request.POST.get('commentaire_operateur', "Modifications enregistrées par le superviseur."),

                        operateur=operateur

                    )



                    messages.success(request, f"Les modifications de la commande {commande.id_yz} ont été enregistrées avec succès.")

                    return redirect('Superpreparation:detail_prepa', pk=commande.id)

                except Exception as e:

                    messages.error(request, f"Erreur lors de l'enregistrement: {str(e)}")

                    return redirect('Superpreparation:modifier_commande_superviseur', commande_id=commande.id)

                

        except Exception as e:

            print(f"❌ Erreur générale dans modifier_commande_superviseur: {e}")

            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

    

    # ================ AFFICHAGE DE LA PAGE (GET) ================

    

    # Récupérer les articles de la commande

    paniers = commande.paniers.select_related('article').all()

    

    # Calculer le total des articles

    total_articles = sum(panier.sous_total for panier in paniers)

    

    # Récupérer les informations de livraison

    frais_livraison = commande.ville.frais_livraison if commande.ville else 0

    

    # Récupérer toutes les villes pour le formulaire

    villes = Ville.objects.all().order_by('nom')

    

    # Vérifier si c'est une commande renvoyée

    is_commande_renvoyee = False

    commande_originale_obj = None

    commande_renvoi_obj = None

    etat_articles_renvoyes = None

    articles_livres = []

    articles_renvoyes = []

    

    # Vérifier si cette commande est un renvoi

    if hasattr(commande, 'commande_renvoi') and commande.commande_renvoi:

        is_commande_renvoyee = True

        commande_originale_obj = commande.commande_renvoi

        commande_renvoi_obj = commande

        

        # Récupérer l'état des articles renvoyés

        try:

            etat_articles_renvoyes = Operation.objects.filter(

                commande=commande_originale_obj,

                enum_etat__libelle='Livrée partiellement'

            ).first()

            

            if etat_articles_renvoyes:

                # Récupérer les articles livrés et renvoyés

                articles_livres = etat_articles_renvoyes.articles_livres.all() if hasattr(etat_articles_renvoyes, 'articles_livres') else []

                articles_renvoyes = etat_articles_renvoyes.articles_renvoyes.all() if hasattr(etat_articles_renvoyes, 'articles_renvoyes') else []

        except Exception as e:

            print(f"⚠️ Erreur lors de la récupération des articles renvoyés: {e}")

    

    # Préparer le contexte

    context = {

        'commande': commande,

        'paniers': paniers,

        'total_articles': total_articles,

        'operateur': operateur,

        'is_commande_renvoyee': is_commande_renvoyee,

        'articles_livres': articles_livres,

        'articles_renvoyes': articles_renvoyes,

        # Variables de debug/informations supplémentaires

        'commande_originale': commande_originale_obj,

        'commande_renvoi': commande_renvoi_obj,

        'etat_articles_renvoyes': etat_articles_renvoyes,

        # Informations de livraison

        'frais_livraison': float(frais_livraison),

        'villes': villes,

        # 'articles_renvoyes_map': articles_renvoyes_map, # Retiré car plus nécessaire

    }

    return render(request, 'Superpreparation/modifier_commande_superviseur.html', context)

@superviseur_preparation_required
def api_articles_disponibles_prepa(request):

    """API pour récupérer les articles disponibles pour les opérateurs de préparation"""

    from article.models import Article

    

    try:

        # Accepter PREPARATION, SUPERVISEUR_PREPARATION et ADMIN

        operateur = Operateur.objects.get(user=request.user, actif=True)

        if operateur.type_operateur not in ['PREPARATION', 'SUPERVISEUR_PREPARATION', 'ADMIN']:

            return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)

    except Operateur.DoesNotExist:

        # Pas de profil: continuer (le décorateur a déjà validé l'accès via groupes)

        operateur = None

    

    try:

        search_query = request.GET.get('search', '')

        filter_type = request.GET.get('filter', 'tous')

        

        # Récupérer les articles actifs

        articles = Article.objects.filter(actif=True)

        

        # Appliquer les filtres selon le type

        if filter_type == 'disponible':

            # Filtrer les articles qui ont au moins une variante avec stock > 0

            articles = articles.filter(variantes__qte_disponible__gt=0, variantes__actif=True).distinct()

        elif filter_type == 'upsell':

            articles = articles.filter(isUpsell=True)

        elif filter_type == 'liquidation':

            articles = articles.filter(phase='LIQUIDATION')

        elif filter_type == 'test':

            articles = articles.filter(phase='EN_TEST')

        

        # Recherche textuelle

        if search_query:

            articles = articles.filter(

                Q(nom__icontains=search_query) |

                Q(reference__icontains=search_query) |

                Q(couleur__icontains=search_query) |

                Q(pointure__icontains=search_query) |

                Q(description__icontains=search_query)

            )

        

        # Filtrer les articles en promotion si nécessaire (approche plus sûre)

        if filter_type == 'promo':

            # Filtrer les articles qui ont un prix actuel inférieur au prix unitaire

            articles = articles.filter(

                prix_actuel__isnull=False,

                prix_actuel__lt=F('prix_unitaire')

            )

        

        # Limiter les résultats

        articles = articles[:50]

        

        articles_data = []

        for article in articles:

            # Mettre à jour le prix actuel si nécessaire

            if article.prix_actuel is None:

                article.prix_actuel = article.prix_unitaire

                article.save(update_fields=['prix_actuel'])

            

            # Récupérer toutes les variantes actives (inclet celles en rupture)

            variantes_actives = article.variantes.filter(actif=True)

            

            # Si pas de variantes, créer une entrée avec les propriétés de compatibilité

            if not variantes_actives.exists():

                # Propriétés de compatibilité du modèle Article

                stock = article.qte_disponible

                couleur = article.couleur

                pointure = article.pointure

                

                if stock > 0:

                    articles_data.append({

                        'id': article.id,

                        'nom': article.nom,

                        'reference': article.reference or '',

                        'couleur': couleur or '',

                        'pointure': pointure or '',

                        'description': article.description or '',

                        'prix_unitaire': float(article.prix_unitaire),

                        'prix_actuel': float(article.prix_actuel or article.prix_unitaire),

                        'qte_disponible': stock,

                        'isUpsell': bool(article.isUpsell),

                        'phase': article.phase or 'NORMAL',

                        'has_promo_active': article.has_promo_active,

                        'image_url': article.image.url if article.image else article.image_url,

                        'categorie': str(article.categorie) if article.categorie else '',

                        'genre': str(article.genre) if article.genre else '',

                        'modele': article.modele_complet(),

                        'variantes_count': 0,

                        'is_variante': False,

                        'variante_id': None,

                        # Propriétés pour compatibilité avec le template

                        'prix': float(article.prix_actuel or article.prix_unitaire),

                        'prix_original': float(article.prix_unitaire),

                        'has_reduction': article.has_promo_active,

                        'reduction_pourcentage': round(((float(article.prix_unitaire) - float(article.prix_actuel or article.prix_unitaire)) / float(article.prix_unitaire)) * 100, 0) if article.has_promo_active else 0,

                        'article_type': 'normal',

                        'type_icon': 'fas fa-box',

                        'type_color': 'text-gray-600',

                        'display_text': f"{article.nom} - {couleur or ''} - {pointure or ''} ({float(article.prix_actuel or article.prix_unitaire):.2f} DH)"

                    })

            else:

                # Préparer la liste complète des variantes pour affichage (y compris rupture)

                variantes_list = []

                for v in variantes_actives:

                    variantes_list.append({

                        'id': v.id,

                        'couleur': v.couleur.nom if v.couleur else '',

                        'pointure': v.pointure.pointure if v.pointure else '',

                        'qte_disponible': v.qte_disponible,

                        'reference_variante': v.reference_variante,

                    })



                # Créer une entrée pour chaque variante (même celles en rupture)

                for variante in variantes_actives:

                    # Déterminer le type d'article pour l'affichage

                    article_type = 'normal'

                    type_icon = 'fas fa-box'

                    type_color = 'text-gray-600'

                    

                    if article.isUpsell:

                        article_type = 'upsell'

                        type_icon = 'fas fa-arrow-up'

                        type_color = 'text-purple-600'

                    elif article.phase == 'LIQUIDATION':

                        article_type = 'liquidation'

                        type_icon = 'fas fa-money-bill-wave'

                        type_color = 'text-red-600'

                    elif article.phase == 'EN_TEST':

                        article_type = 'test'

                        type_icon = 'fas fa-flask'

                        type_color = 'text-yellow-600'

                    

                    # Vérifier si l'article est en promotion

                    if article.has_promo_active:

                        article_type = 'promo'

                        type_icon = 'fas fa-fire'

                        type_color = 'text-orange-600'

                    

                    articles_data.append({

                        'id': article.id,

                        'nom': article.nom,

                        'reference': article.reference or '',

                        'couleur': variante.couleur.nom if variante.couleur else '',

                        'pointure': variante.pointure.pointure if variante.pointure else '',

                        'description': article.description or '',

                        'prix_unitaire': float(article.prix_unitaire),

                        'prix_actuel': float(article.prix_actuel or article.prix_unitaire),

                        'qte_disponible': variante.qte_disponible,

                        'isUpsell': bool(article.isUpsell),

                        'phase': article.phase or 'NORMAL',

                        'has_promo_active': article.has_promo_active,

                        'image_url': article.image.url if article.image else article.image_url,

                        'categorie': str(article.categorie) if article.categorie else '',

                        'genre': str(article.genre) if article.genre else '',

                        'modele': article.modele_complet(),

                        'variantes_count': variantes_actives.count(),

                        'is_variante': True,

                        'variante_id': variante.id,

                        'reference_variante': variante.reference_variante,

                        'variantes_all': variantes_list,

                        # Propriétés pour compatibilité avec le template

                        'prix': float(article.prix_actuel or article.prix_unitaire),

                        'prix_original': float(article.prix_unitaire),

                        'has_reduction': article.has_promo_active,

                        'reduction_pourcentage': round(((float(article.prix_unitaire) - float(article.prix_actuel or article.prix_unitaire)) / float(article.prix_unitaire)) * 100, 0) if article.has_promo_active else 0,

                        'article_type': article_type,

                        'type_icon': type_icon,

                        'type_color': type_color,

                        'display_text': f"{article.nom} - {variante.couleur.nom if variante.couleur else ''} - {variante.pointure.pointure if variante.pointure else ''} ({float(article.prix_actuel or article.prix_unitaire):.2f} DH)"

                    })

        

        # Calculer les statistiques pour la réponse

        stats = {

            "total": len(articles_data),

            "disponible": len([a for a in articles_data if a.get('qte_disponible', 0) > 0]),

            "upsell": len([a for a in articles_data if a.get('isUpsell', False)]),

            "liquidation": len([a for a in articles_data if a.get('phase') == 'LIQUIDATION']),

            "test": len([a for a in articles_data if a.get('phase') == 'EN_TEST']),

            "promo": len([a for a in articles_data if a.get('has_promo_active', False)])

        }

        

        # Retourner le format attendu par le frontend

        return JsonResponse({

            'success': True,

            'articles': articles_data,

            'stats': stats

        })

        

    except Exception as e:

        import traceback

        traceback.print_exc()  # This will print to the server console

        return JsonResponse({

            'success': False,

            'message': 'Erreur interne du serveur lors du chargement des articles.',

            'details': str(e)

        }, status=500)

@superviseur_preparation_required
def api_panier_commande_prepa(request, commande_id):
    """API pour récupérer le panier d'une commande pour les opérateurs de préparation"""
    try:
        # Accepter PREPARATION et SUPERVISEUR_PREPARATION
        operateur = Operateur.objects.get(user=request.user, actif=True)
        if operateur.type_operateur not in ['PREPARATION', 'SUPERVISEUR_PREPARATION']:
            return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
    except Operateur.DoesNotExist:
        # Pas de profil: continuer (le décorateur a déjà validé l'accès via groupes)
        operateur = None
    # Récupérer la commande
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    # Pour les superviseurs, on ne vérifie pas l'affectation spécifique
    # Ils peuvent accéder à toutes les commandes en préparation
    if operateur and operateur.type_operateur == 'SUPERVISEUR_PREPARATION':
        # Vérifier seulement que la commande est en préparation (incluant les états finaux)
        etat_preparation = commande.etats.filter(
            Q(enum_etat__libelle='En préparation') | Q(enum_etat__libelle='Collectée') | Q(enum_etat__libelle='Emballée') | Q(enum_etat__libelle='Préparée'),
            date_fin__isnull=True
        ).first()
    else:
        # Pour les opérateurs normaux, vérifier l'affectation spécifique
        etat_preparation = commande.etats.filter(
            Q(enum_etat__libelle='En préparation') | Q(enum_etat__libelle='Collectée') | Q(enum_etat__libelle='Emballée') | Q(enum_etat__libelle='Préparée'),
            operateur=operateur,
            date_fin__isnull=True
        ).first()
    if not etat_preparation:
        return JsonResponse({'success': False, 'message': 'Commande non affectée'})
    # Récupérer les paniers
    paniers = commande.paniers.all().select_related('article')
    # Construire le format "articles" attendu par le front (compatibilité)
    articles = []
    total_articles_montant = 0.0
    for panier in paniers:
        prix_unitaire = float(panier.article.prix_unitaire) if panier.article and panier.article.prix_unitaire is not None else 0.0
        sous_total = float(panier.sous_total) if panier.sous_total is not None else round(prix_unitaire * (panier.quantite or 0), 2)
        total_articles_montant += sous_total
        articles.append({
            'id': panier.id,
            'article_id': getattr(panier.article, 'id', None),
            'nom': getattr(panier.article, 'nom', ''),
            'reference': getattr(panier.article, 'reference', '') or '',
            'couleur': getattr(panier.article, 'couleur', ''),
            'pointure': getattr(panier.article, 'pointure', ''),
            'quantite': panier.quantite or 0,
            'prix_unitaire': prix_unitaire,
            'sous_total': sous_total,
        })
    # Objet commande attendu par le front
    client_nom = ''
    try:
        if commande.client:
            prenom = getattr(commande.client, 'prenom', '') or ''
            nom = getattr(commande.client, 'nom', '') or ''
            client_nom = (prenom + ' ' + nom).strip()
    except Exception:
        client_nom = ''
    commande_payload = {
        'id': commande.id,
        'id_yz': getattr(commande, 'id_yz', ''),
        'client_nom': client_nom,
        'total_articles': len(articles),
        'total_montant': round(total_articles_montant, 2),
        'total_final': float(commande.total_cmd) if getattr(commande, 'total_cmd', None) is not None else round(total_articles_montant, 2),
    }
    # Réponse incluant les deux formats (nouveau et legacy) pour compatibilité
    return JsonResponse({
        'success': True,
        # Nouveau format utilisé par le front de Suivi Général
        'commande': commande_payload,
        'articles': articles,
        # Legacy (au cas où)
        'paniers': articles,
        'total_commande': commande_payload['total_final'],
        'nb_articles': len(articles),
    })

@superviseur_preparation_required
def api_finaliser_commande(request, commande_id):
    """API pour finaliser une commande depuis la liste (pour les superviseurs)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    try:
        operateur_profile = request.user.profil_operateur
        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):
            return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil opérateur non trouvé'}, status=403)
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'}, status=404)
    # Vérifier que la commande est emballée (prête pour finalisation)
    etat_actuel = commande.etat_actuel
    if not etat_actuel or etat_actuel.enum_etat.libelle != 'Emballée':
        return JsonResponse({
            'success': False, 
            'message': f'La commande n\'est pas emballée (état actuel: {etat_actuel.enum_etat.libelle if etat_actuel else "Aucun"})'
        }, status=400)
    try:
        with transaction.atomic():
            # Marquer l'état 'Emballée' comme terminé
            etat_actuel.date_fin = timezone.now()
            etat_actuel.operateur = operateur_profile
            etat_actuel.save()
            # Créer le nouvel état 'Préparée' (final)
            etat_preparee, created = EnumEtatCmd.objects.get_or_create(libelle='Préparée')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_preparee,
                operateur=operateur_profile
            )
            Operation.objects.create(
                commande=commande,
                type_operation='PREPARATION_TERMINEE',
                operateur=operateur_profile,
                conclusion=f"Commande préparée par {operateur_profile.nom_complet} (via API)."
            )
        return JsonResponse({
            'success': True,
            'message': f'La commande {commande.id_yz} a été préparée avec succès.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la finalisation: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def api_panier_commande(request, commande_id):
    """API pour récupérer le contenu du panier d'une commande (pour le modal)"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    try:
        operateur_profile = request.user.profil_operateur
        if not (operateur_profile.is_preparation or operateur_profile.is_superviseur_preparation):
            return JsonResponse({'success': False, 'message': 'Accès non autorisé'}, status=403)
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil opérateur non trouvé'}, status=403)
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'}, status=404)
    try:
        # Récupérer les articles du panier
        paniers = commande.paniers.all().select_related('article')
        if not paniers.exists():
            html_content = '''
                <div class="text-center py-8">
                    <i class="fas fa-shopping-cart text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">Aucun article dans le panier</p>
                </div>
            '''
            return JsonResponse({
                'success': True,
                'html': html_content
            })

        # Construire le HTML du panier
        html_content = '''
            <div class="space-y-4">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Commande #''' + str(commande.id_yz) + '''</h4>
                    <p class="text-sm text-gray-600">Client: ''' + (commande.client.prenom + ' ' + commande.client.nom if commande.client else 'Non défini') + '''</p>
                </div>
                <div class="space-y-3">
        '''
        total_articles = 0
        total_montant = 0
        for panier in paniers:
            article = panier.article
            quantite = panier.quantite or 0
            prix = getattr(article, 'prix', 0) or 0
            sous_total = quantite * prix
            total_articles += quantite
            total_montant += sous_total

            # Informations de l'article
            nom_article = getattr(article, 'nom', 'Article sans nom') or 'Article sans nom'
            reference = getattr(article, 'reference', '') or ''
            couleur = getattr(article, 'couleur', '') or ''
            pointure = getattr(article, 'pointure', '') or ''
            html_content += '''
                <div class="border border-gray-200 rounded-lg p-4">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex-1">
                            <h5 class="font-medium text-gray-900">''' + nom_article + '''</h5>
                            <p class="text-sm text-gray-600">Réf: ''' + reference + '''</p>
                        </div>
                        <div class="text-right">
                            <span class="text-lg font-bold text-green-600">''' + str(prix) + ''' DH</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="text-gray-500">Quantité:</span>
                            <span class="font-medium text-gray-900 ml-1">''' + str(quantite) + '''</span>
                        </div>
                        <div>
                            <span class="text-gray-500">Sous-total:</span>
                            <span class="font-medium text-green-600 ml-1">''' + str(sous_total) + ''' DH</span>
                        </div>
            '''
       # Ajouter couleur et pointure si disponibles
            if couleur or pointure:
                html_content += '''
                        <div class="col-span-2 flex space-x-4">
                '''
                if couleur:
                    html_content += '''
                            <div>
                                <span class="text-gray-500">Couleur:</span>
                                <span class="font-medium text-gray-900 ml-1">''' + couleur + '''</span>
                            </div>
                    '''
                if pointure:
                    html_content += '''
                            <div>
                                <span class="text-gray-500">Pointure:</span>
                                <span class="font-medium text-gray-900 ml-1">''' + pointure + '''</span>
                            </div>
                    '''
                html_content += '''
                        </div>
                '''
            html_content += '''
                    </div>
                </div>
            '''
        # Ajouter le total
        html_content += '''
                </div>
                <div class="border-t border-gray-200 pt-4">
                    <div class="flex justify-between items-center">
                        <div class="text-lg font-medium text-gray-900">
                            Total (''' + str(total_articles) + ''' article''' + ('s' if total_articles > 1 else '') + '''):
                        </div>
                        <div class="text-2xl font-bold text-green-600">
                            ''' + str(round(total_montant, 2)) + ''' DH
                        </div>
                    </div>
                </div>
            </div>
        '''
        return JsonResponse({
            'success': True,
            'html': html_content
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du chargement du panier: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def imprimer_tickets_preparation(request):
    """
    Vue pour imprimer les tickets de préparation SANS changer l'état des commandes.
    Permet d'imprimer ou de réimprimer des tickets pour les commandes en préparation.
    """
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            return HttpResponse("Accès non autorisé.", status=403)
    except Operateur.DoesNotExist:
        return HttpResponse("Profil opérateur non trouvé.", status=403)
    commande_ids_str = request.GET.get('ids')
    if not commande_ids_str:
        return HttpResponse("Aucun ID de commande fourni.", status=400)
    try:
        commande_ids = [int(id) for id in commande_ids_str.split(',') if id.isdigit()]
    except ValueError:
        return HttpResponse("IDs de commande invalides.", status=400)
    commandes = Commande.objects.filter(
        id__in=commande_ids,
        etats__operateur=operateur_profile,
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct()

    if not commandes.exists():
        messages.info(request, "L'impression des tickets est désactivée. Utilisez les outils de gestion.")
        return redirect('Superpreparation:liste_prepa')
    code128 = barcode.get_barcode_class('code128')
    messages.info(request, "L'impression des tickets a été retirée de l'interface superviseur.")
    return redirect('Superpreparation:liste_prepa')


def get_operateur_display_name(operateur):
    """Fonction helper pour obtenir le nom d'affichage d'un opérateur"""
    if not operateur:
        return "Opérateur inconnu"
    
    if hasattr(operateur, 'nom_complet') and operateur.nom_complet:
        return operateur.nom_complet
    elif operateur.nom and operateur.prenom:
        return f"{operateur.prenom} {operateur.nom}"
    elif operateur.nom:
        return operateur.nom
    elif hasattr(operateur, 'user') and operateur.user:
        return operateur.user.username
    else:
        return "Opérateur inconnu"

@superviseur_preparation_required
def export_envois(request):
    """Export des envois journaliers - Service de préparation"""
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé.")
            return redirect('login')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil opérateur non trouvé.")
        return redirect('login')
    
    from parametre.models import Region, Operateur
    from django.utils import timezone
    import datetime
    
    # Date par défaut : aujourd'hui
    today = timezone.now().date()
    date_envoi = request.GET.get('date_envoi', today)
    region_id = request.GET.get('region')
    livreur_id = request.GET.get('livreur')
    
    # Obtenir tous les livreurs (opérateurs de livraison)
    livreurs = Operateur.objects.filter(is_livraison=True, actif=True)
    regions = Region.objects.all()
    
    # Simuler des envois (à remplacer par votre modèle Envoi)
    envois = []
    
    # Commandes PRÉPARÉES à être envoyées
    commandes_pretes = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).select_related('ville__region')
    
    if region_id and region_id.strip():
        commandes_pretes = commandes_pretes.filter(ville__region_id=region_id)
    
    # Statistiques
    stats = {
        'total_envois': len(envois),
        'total_commandes': 0,
        'commandes_pretes': commandes_pretes.count(),
        'livreurs_actifs': livreurs.filter(actif=True).count(),
    }
    
    context = {
        'envois': envois,
        'commandes_pretes': commandes_pretes,
        'livreurs': livreurs,
        'regions': regions,
        'stats': stats,
        'today': today,
    }
    
    return render(request, 'Superpreparation/export_envois.html', context)

@superviseur_preparation_required
def details_region_view(request):
    """Vue détaillée pour afficher les commandes par région - Service de préparation"""
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé.")
            return redirect('login')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil opérateur non trouvé.")
        return redirect('login')
    
    from parametre.models import Region, Ville
    
    # Récupérer les paramètres de filtrage
    region_name = request.GET.get('region')
    ville_name = request.GET.get('ville')
    
    # Base queryset pour toutes les commandes en traitement
    commandes_reparties = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Confirmée', 'À imprimer', 'Préparée', 'En cours de livraison'],
        etats__date_fin__isnull=True,
        ville__isnull=False,  # Exclure les commandes sans ville
        ville__region__isnull=False  # Exclure les commandes sans région
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__operateur', 'etats__enum_etat', 'paniers__article'
    ).distinct()
    
    # Appliquer les filtres
    if region_name:
        commandes_reparties = commandes_reparties.filter(ville__region__nom_region=region_name)
    if ville_name:
        commandes_reparties = commandes_reparties.filter(ville__nom=ville_name)
    
    # Statistiques par ville dans la région/ville filtrée
    stats_par_ville = commandes_reparties.values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Statistiques des commandes PRÉPARÉES par ville dans la région/ville filtrée
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).select_related('ville', 'ville__region')
    
    # Appliquer les mêmes filtres que pour les commandes en traitement
    if region_name:
        commandes_preparees = commandes_preparees.filter(ville__region__nom_region=region_name)
    if ville_name:
        commandes_preparees = commandes_preparees.filter(ville__nom=ville_name)
    
    stats_preparees_par_ville = commandes_preparees.values(
        'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Créer un dictionnaire pour un accès rapide
    preparees_par_ville = {(stat['ville__nom'], stat['ville__region__nom_region']): stat['nb_commandes_preparees'] for stat in stats_preparees_par_ville}
    
    # Calculer les totaux
    total_commandes = commandes_reparties.count()
    total_montant = commandes_reparties.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Définir le titre selon le filtre appliqué
    if region_name:
        page_title = f"Détails - {region_name}"
        page_subtitle = f"Commandes en traitement dans la région {region_name}"
    elif ville_name:
        page_title = f"Détails - {ville_name}"
        page_subtitle = f"Commandes en traitement à {ville_name}"
    else:
        page_title = "Détails par Région"
        page_subtitle = "Répartition détaillée des commandes en traitement"
    
    context = {
        'operateur': operateur_profile,
        'commandes_reparties': commandes_reparties,
        'stats_par_ville': stats_par_ville,
        'preparees_par_ville': preparees_par_ville,
        'total_commandes': total_commandes,
        'total_montant': total_montant,
        'region_name': region_name,
        'ville_name': ville_name,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    
    return render(request, 'Superpreparation/details_region.html', context)

@superviseur_preparation_required
def exporter_envoi(request, envoi_id, format):
    """
    Exporte un envoi dans un format spécifique (CSV/PDF).
    """
    envoi = get_object_or_404(Envoi, id=envoi_id)
    if format == 'csv':
        # Logique d'export CSV
        return HttpResponse(f"Export CSV de l'envoi {envoi_id}", content_type="text/csv")
    elif format == 'pdf':
        # Logique d'export PDF
        return HttpResponse(f"Export PDF de l'envoi {envoi_id}", content_type="application/pdf")
    return HttpResponse("Format non supporté", status=400)


@superviseur_preparation_required
def envois_view(request):
    """Page de gestion des envois (création/en cours)."""
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé.")
            return redirect('login')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil opérateur non trouvé.")
        return redirect('login')

    # Données placeholder: commandes prêtes (même logique que export_envois)
    from parametre.models import Region
    regions = Region.objects.all()
    commandes_pretes = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).select_related('ville__region')
    
    # Récupérer les envois actifs (non clôturés)
    envois_actifs = Envoi.objects.exclude(
        status=False
    ).select_related('region').order_by('-date_creation')

    # Mettre à jour le compteur de commandes pour chaque envoi
    for envoi in envois_actifs:
        nb_commandes = Commande.objects.filter(
            ville__region=envoi.region,
            etats__enum_etat__libelle='Préparée',
            etats__date_fin__isnull=True
        ).count()
        
        # Mettre à jour seulement si le nombre a changé
        if envoi.nb_commandes != nb_commandes:
            envoi.nb_commandes = nb_commandes
            envoi.save(update_fields=['nb_commandes'])

    # Récupérer les IDs des régions qui ont déjà un envoi actif
    regions_avec_envoi_actif = set(envois_actifs.values_list('region_id', flat=True))

    context = {
        'regions': regions,
        'commandes_pretes': commandes_pretes,
        'envois_actifs': envois_actifs,
        'regions_avec_envoi_actif': regions_avec_envoi_actif,
        'page_title': 'Gestion des envois',
        'page_subtitle': 'Créer et suivre les envois en cours',
    }
    return render(request, 'Superpreparation/envois.html', context)

@superviseur_preparation_required
def commandes_envoi(request, envoi_id):
    """Récupérer les commandes d'un envoi spécifique"""
    try:
        envoi = Envoi.objects.get(id=envoi_id)
        
        # Récupérer seulement les commandes préparées de cet envoi spécifique
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Préparée',
            etats__date_fin__isnull=True  # État actuel (pas terminé)
        ).select_related('client', 'ville', 'ville__region').prefetch_related(
            'etats', 
            'paniers__article', 
            'paniers__variante__couleur', 
            'paniers__variante__pointure'
        ).distinct()
        
        print(f"DEBUG: Envoi {envoi.id} - Commandes préparées trouvées: {commandes.count()}")
        
        # Préparer les données pour le JSON
        commandes_data = []
        for commande in commandes:
            try:
                print(f"DEBUG: Traitement commande {commande.id} - ID YZ: {commande.id_yz}")
                # Récupérer l'état actuel de manière sécurisée
                etat_actuel = commande.etat_actuel
                libelle_etat = None
                if etat_actuel and etat_actuel.enum_etat:
                    libelle_etat = etat_actuel.enum_etat.libelle
                    print(f"DEBUG: État actuel: {libelle_etat}")
                else:
                    print(f"DEBUG: Aucun état actuel trouvé pour la commande {commande.id}")
                
                # Récupérer les paniers avec leurs variantes
                paniers_data = []
                for panier in commande.paniers.all():
                    panier_info = {
                        'id': panier.id,
                        'article': {
                            'id': panier.article.id,
                            'nom': panier.article.nom,
                            'reference': panier.article.reference,
                        },
                        'quantite': panier.quantite,
                        'sous_total': float(panier.sous_total) if panier.sous_total else 0,
                        'variante': None
                    }
                    
                    # Ajouter les informations de variante si elle existe
                    if panier.variante:
                        panier_info['variante'] = {
                            'id': panier.variante.id,
                            'reference_variante': panier.variante.reference_variante,
                            'couleur': panier.variante.couleur.nom if panier.variante.couleur else None,
                            'pointure': panier.variante.pointure.pointure if panier.variante.pointure else None,
                            'qte_disponible': panier.variante.qte_disponible,
                        }
                        print(f"DEBUG: Variante trouvée pour panier {panier.id}: {panier.variante.reference_variante}")
                    else:
                        print(f"DEBUG: Aucune variante pour panier {panier.id}")
                    
                    paniers_data.append(panier_info)
                
                commandes_data.append({
                    'id': commande.id,
                    'id_yz': commande.id_yz,
                    'num_cmd': commande.num_cmd,
                    'total_cmd': float(commande.total_cmd) if commande.total_cmd else 0,
                    'client': {
                        'nom': commande.client.nom if commande.client else None,
                        'prenom': commande.client.prenom if commande.client else None,
                        'email': commande.client.email if commande.client else None,
                        'numero_tel': commande.client.numero_tel if commande.client else None,
                    },
                    'ville': {
                        'nom_ville': commande.ville.nom if commande.ville else None,
                    },
                    'etat_actuel': {
                        'enum_etat': {
                            'libelle': libelle_etat,
                        }
                    } if etat_actuel else None,
                    'paniers': paniers_data,
                })
            except Exception as e:
                # Si une commande spécifique pose problème, on la saute et on continue
                print(f"Erreur lors du traitement de la commande {commande.id}: {str(e)}")
                continue
        
        print(f"DEBUG: Total commandes ajoutées aux données: {len(commandes_data)}")
        
        return JsonResponse({
            'success': True,
            'commandes': commandes_data,
            'envoi': {
                'id': envoi.id,
                'numero_envoi': envoi.numero_envoi,
                'region': envoi.region.nom_region,
                'nb_commandes': envoi.nb_commandes,
            }
        })
        
    except Envoi.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Envoi non trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"Erreur dans commandes_envoi: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des commandes: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def commandes_envoi_historique(request, envoi_id):
    """Récupérer les commandes d'un envoi clôturé pour l'historique"""
    try:
        envoi = Envoi.objects.get(id=envoi_id, status=False)  # Seulement les envois clôturés
        
        print(f"DEBUG: Récupération commandes pour envoi clôturé {envoi.id} - Région: {envoi.region.nom_region}")
        commandes = Commande.objects.filter(
            envoi =envoi
        ).select_related('client', 'ville', 'ville__region').prefetch_related(
            'etats', 
            'paniers__article', 
            'paniers__variante__couleur', 
            'paniers__variante__pointure'
        ).distinct()
        
        print(f"DEBUG: Total commandes trouvées pour l'envoi clôturé: {commandes.count()}")
        commandes_data = []
        for commande in commandes:
            try:
                print(f"DEBUG: Traitement commande {commande.id} - ID YZ: {commande.id_yz}")
                
                # Récupérer l'état actuel de manière sécurisée
                etat_actuel = commande.etat_actuel
                libelle_etat = None
                if etat_actuel and etat_actuel.enum_etat:
                    libelle_etat = etat_actuel.enum_etat.libelle
                    print(f"DEBUG: État actuel: {libelle_etat}")
                else:
                    print(f"DEBUG: Aucun état actuel trouvé pour la commande {commande.id}")
                
                # Récupérer les paniers avec leurs variantes
                paniers_data = []
                for panier in commande.paniers.all():
                    panier_info = {
                        'id': panier.id,
                        'article': {
                            'id': panier.article.id,
                            'nom': panier.article.nom,
                            'reference': panier.article.reference,
                        },
                        'quantite': panier.quantite,
                        'sous_total': float(panier.sous_total) if panier.sous_total else 0,
                        'variante': None
                    }
                    
                    # Ajouter les informations de variante si elle existe
                    if panier.variante:
                        panier_info['variante'] = {
                            'id': panier.variante.id,
                            'reference_variante': panier.variante.reference_variante,
                            'couleur': panier.variante.couleur.nom if panier.variante.couleur else None,
                            'pointure': panier.variante.pointure.pointure if panier.variante.pointure else None,
                            'qte_disponible': panier.variante.qte_disponible,
                        }
                        print(f"DEBUG: Variante trouvée pour panier {panier.id}: {panier.variante.reference_variante}")
                    else:
                        print(f"DEBUG: Aucune variante pour panier {panier.id}")
                    
                    paniers_data.append(panier_info)
                
                commandes_data.append({
                    'id': commande.id,
                    'id_yz': commande.id_yz,
                    'num_cmd': commande.num_cmd,
                    'total_cmd': float(commande.total_cmd) if commande.total_cmd else 0,
                    'client': {
                        'nom': commande.client.nom if commande.client else None,
                        'prenom': commande.client.prenom if commande.client else None,
                        'email': commande.client.email if commande.client else None,
                        'numero_tel': commande.client.numero_tel if commande.client else None,
                    },
                    'ville': {
                        'nom_ville': commande.ville.nom if commande.ville else None,
                    },
                    'etat_actuel': {
                        'enum_etat': {
                            'libelle': libelle_etat,
                        }
                    } if etat_actuel else None,
                    'paniers_data': paniers_data,
                })
            except Exception as e:
                # Si une commande spécifique pose problème, on la saute et on continue
                print(f"Erreur lors du traitement de la commande {commande.id}: {str(e)}")
                continue
        
        print(f"DEBUG: Total commandes ajoutées aux données: {len(commandes_data)}")
        
        return JsonResponse({
            'success': True,
            'commandes': commandes_data,
            'envoi': {
                'id': envoi.id,
                'numero_envoi': envoi.numero_envoi,
                'region': envoi.region.nom_region,
                'nb_commandes': envoi.nb_commandes,
                'date_creation': envoi.date_creation.strftime('%d/%m/%Y'),
                'date_cloture': envoi.date_livraison_effective.strftime('%d/%m/%Y') if envoi.date_livraison_effective else None,
            }
        })
        
    except Envoi.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Envoi clôturé non trouvé'
        }, status=404)
    except Exception as e:
        import traceback
        print(f"Erreur dans commandes_envoi_historique: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des commandes: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def historique_envois_view(request):
    """Page d'historique des envois clôturés."""
    from django.core.paginator import Paginator
    from datetime import datetime, timedelta
    
    # Récupérer les envois clôturés (status=False)
    envois_clotures = Envoi.objects.filter(
        status=False  # False = clôturé
    ).select_related('region', 'operateur_creation').order_by('-date_creation')
    
    # Mettre à jour le compteur de commandes pour chaque envoi clôturé
    for envoi in envois_clotures:
        # Pour les envois clôturés, on compte TOUTES les commandes de la région
        # peu importe leur état actuel
        nb_commandes = Commande.objects.filter(
            envoi=envoi
        ).count()
        
        # Mettre à jour seulement si le nombre a changé
        if envoi.nb_commandes != nb_commandes:
            envoi.nb_commandes = nb_commandes
            envoi.save(update_fields=['nb_commandes'])
    
    # Filtrage par période si demandé
    periode = request.GET.get('periode')
    if periode:
        today = datetime.now().date()
        if periode == '7j':
            date_debut = today - timedelta(days=7)
            envois_clotures = envois_clotures.filter(date_creation__gte=date_debut)
        elif periode == '30j':
            date_debut = today - timedelta(days=30)
            envois_clotures = envois_clotures.filter(date_creation__gte=date_debut)
        elif periode == '90j':
            date_debut = today - timedelta(days=90)
            envois_clotures = envois_clotures.filter(date_creation__gte=date_debut)
    
    # Filtrage par région si demandé
    region_filter = request.GET.get('region')
    if region_filter:
        envois_clotures = envois_clotures.filter(region__id=region_filter)
    
    # Pagination
    paginator = Paginator(envois_clotures, 12)  # 12 envois par page
    page_number = request.GET.get('page')
    envois = paginator.get_page(page_number)
    
    # Récupérer toutes les régions pour le filtre
    from parametre.models import Region
    regions = Region.objects.all().order_by('nom_region')
    
    context = {
        'envois': envois,
        'regions': regions,
        'periode_selected': periode,
        'region_selected': region_filter,
        'page_title': 'Historique des envois',
        'page_subtitle': 'Consulter les envois clôturés et exporter leurs données',
    }
    return render(request, 'Superpreparation/historique_envois.html', context)

@csrf_exempt
@login_required
def creer_envoi_region(request):

    """Créer un envoi basé sur une région (POST)."""
    # Debug: Afficher les informations de l'utilisateur
    print(f"🔍 DEBUG - Utilisateur: {request.user.username}")
    print(f"🔍 DEBUG - Authentifié: {request.user.is_authenticated}")
    print(f"🔍 DEBUG - Headers: {dict(request.headers)}")
    print(f"🔍 DEBUG - Method: {request.method}")
    
    try:
        from parametre.models import Operateur
        operateur = Operateur.objects.get(user=request.user, actif=True)
        print(f"🔍 DEBUG - Profil opérateur: {operateur.type_operateur}")
    except Operateur.DoesNotExist:
        print(f"🔍 DEBUG - Aucun profil opérateur trouvé")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        from parametre.models import Region
        region_id = request.POST.get('region_id')

        if not region_id:
            return JsonResponse({'success': False, 'message': 'Région requise'}, status=400)

        region = Region.objects.get(id=region_id)

        # Vérifier qu'il n'y a pas déjà un envoi actif pour cette région
        envoi_actif_existant = Envoi.objects.filter(region=region, status=True).exists()
        if envoi_actif_existant:
            return JsonResponse({
                'success': False, 
                'message': f'Il existe déjà un envoi actif pour la région {region.nom_region}. Veuillez clôturer l\'envoi existant avant d\'en créer un nouveau.'
            }, status=400)

        # Générer un numéro d'envoi via le modèle Envoi
        from django.utils import timezone
        
        # Récupérer le profil opérateur
        try:
            from parametre.models import Operateur
            operateur_creation = Operateur.objects.get(user=request.user, actif=True)
        except Operateur.DoesNotExist:
            operateur_creation = None
            
        envoi = Envoi.objects.create(
            region=region,
            operateur_creation=operateur_creation,
            date_envoi=timezone.now().date(),
            date_livraison_prevue=timezone.now().date(),
        )

        return JsonResponse({'success': True, 'envoi_id': envoi.id, 'numero': envoi.numero_envoi})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@superviseur_preparation_required
def creer_envois_multiples(request):
    """Créer plusieurs envois en une seule opération pour les régions sélectionnées"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        import json
        from parametre.models import Region, Operateur
        from django.utils import timezone
        
        # Récupérer les IDs des régions sélectionnées
        data = json.loads(request.body)
        regions_ids = data.get('regions_ids', [])
        
        if not regions_ids:
            return JsonResponse({'success': False, 'message': 'Aucune région sélectionnée'}, status=400)
        
        # Récupérer le profil opérateur
        try:
            operateur_creation = Operateur.objects.get(user=request.user, actif=True)
        except Operateur.DoesNotExist:
            operateur_creation = None
        
        envois_crees = []
        erreurs = []
        
        for region_id in regions_ids:
            try:
                region = Region.objects.get(id=region_id)
                
                # Vérifier qu'il n'y a pas déjà un envoi actif pour cette région
                envoi_actif_existant = Envoi.objects.filter(region=region, status=True).exists()
                if envoi_actif_existant:
                    erreurs.append(f'Région {region.nom_region}: Un envoi actif existe déjà')
                    continue
                
                # Créer l'envoi
                envoi = Envoi.objects.create(
                    region=region,
                    operateur_creation=operateur_creation,
                    date_envoi=timezone.now().date(),
                    date_livraison_prevue=timezone.now().date(),
                )
                
                envois_crees.append({
                    'id': envoi.id,
                    'numero': envoi.numero_envoi,
                    'region': region.nom_region
                })
                
            except Region.DoesNotExist:
                erreurs.append(f'Région ID {region_id}: Région non trouvée')
            except Exception as e:
                erreurs.append(f'Région ID {region_id}: {str(e)}')
        
        # Préparer la réponse
        if envois_crees and not erreurs:
            return JsonResponse({
                'success': True,
                'message': f'{len(envois_crees)} envoi(s) créé(s) avec succès',
                'envois_crees': envois_crees
            })
        elif envois_crees and erreurs:
            return JsonResponse({
                'success': True,
                'message': f'{len(envois_crees)} envoi(s) créé(s), {len(erreurs)} erreur(s)',
                'envois_crees': envois_crees,
                'erreurs': erreurs
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun envoi créé',
                'erreurs': erreurs
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@superviseur_preparation_required
def cloturer_envois_multiples(request):
    """Clôturer plusieurs envois en une seule opération"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        import json
        from django.utils import timezone
        from parametre.models import Operateur
        
        # Récupérer les IDs des envois sélectionnés
        data = json.loads(request.body)
        envois_ids = data.get('envois_ids', [])
        
        if not envois_ids:
            return JsonResponse({'success': False, 'message': 'Aucun envoi sélectionné'}, status=400)
        
        # Récupérer le profil opérateur
        try:
            operateur_cloture = Operateur.objects.get(user=request.user, actif=True)
        except Operateur.DoesNotExist:
            operateur_cloture = None
        
        envois_clotures = []
        erreurs = []
        
        for envoi_id in envois_ids:
            try:
                envoi = Envoi.objects.get(id=envoi_id)
                
                # Vérifier que l'envoi est encore actif
                if not envoi.status:
                    erreurs.append(f'Envoi {envoi.numero_envoi}: Déjà clôturé')
                    continue
                
                # Clôturer l'envoi
                envoi.status = False
                envoi.operateur_cloture = operateur_cloture
                envoi.date_cloture = timezone.now()
                envoi.save()
                
                envois_clotures.append({
                    'id': envoi.id,
                    'numero': envoi.numero_envoi,
                    'region': envoi.region.nom_region
                })
                
            except Envoi.DoesNotExist:
                erreurs.append(f'Envoi ID {envoi_id}: Envoi non trouvé')
            except Exception as e:
                erreurs.append(f'Envoi ID {envoi_id}: {str(e)}')
        
        # Préparer la réponse
        if envois_clotures and not erreurs:
            return JsonResponse({
                'success': True,
                'message': f'{len(envois_clotures)} envoi(s) clôturé(s) avec succès',
                'envois_clotures': envois_clotures
            })
        elif envois_clotures and erreurs:
            return JsonResponse({
                'success': True,
                'message': f'{len(envois_clotures)} envoi(s) clôturé(s), {len(erreurs)} erreur(s)',
                'envois_clotures': envois_clotures,
                'erreurs': erreurs
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun envoi clôturé',
                'erreurs': erreurs
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@login_required
def cloturer_envoi(request):
    """Clôturer un envoi (POST)."""
    print(f"🔍 DEBUG CLOTURER - Utilisateur: {request.user.username}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

    try:
        envoi_id = request.POST.get('envoi_id')
        if not envoi_id:
            return JsonResponse({'success': False, 'message': 'ID d\'envoi requis'}, status=400)

        envoi = Envoi.objects.get(id=envoi_id)
        
        # Vérifier que l'envoi n'est pas déjà clôturé
        if not envoi.status:  # False = déjà clôturé
            return JsonResponse({'success': False, 'message': 'Cet envoi est déjà clôturé'}, status=400)

        from django.db import transaction
        from django.utils import timezone
        from commande.models import Commande, EtatCommande, EnumEtatCmd

        with transaction.atomic():
            # Passer toutes les commandes liées à l'envoi en "En livraison"
            # On cible explicitement les commandes dont l'état courant est "Préparée"
            commandes = Commande.objects.filter(
                envoi=envoi,
                etats__enum_etat__libelle='Préparée',
                etats__date_fin__isnull=True,
            ).distinct()
            if not commandes.exists():
                # Fallback: prendre les commandes 'Préparée' de la région de l'envoi
                commandes = (
                    Commande.objects.filter(
                        ville__region=envoi.region,
                        etats__enum_etat__libelle='Préparée',
                        etats__date_fin__isnull=True,
                    )
                    .select_related('client', 'ville')
                    .distinct()
                )
            etat_enum, _ = EnumEtatCmd.objects.get_or_create(
                libelle='En livraison',
                defaults={'ordre': 17, 'couleur': '#8B5CF6'}
            )

            for commande in commandes:
                try:
                    # Lier la commande à cet envoi si ce n'est pas déjà fait
                    if commande.envoi_id != envoi.id:
                        commande.envoi = envoi
                        commande.save(update_fields=['envoi'])
                    
                    # Fermer l'état courant "Préparée" s'il existe
                    etat_actuel = commande.etats.filter(date_fin__isnull=True).order_by('-date_debut').first()
                    if etat_actuel and etat_actuel.enum_etat.libelle == 'Préparée':
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save(update_fields=['date_fin'])

                    # Créer le nouvel état
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_enum,
                        operateur=getattr(request.user, 'profil_operateur', None),
                        date_debut=timezone.now(),
                        commentaire=f"Envoi clôturé: {envoi.numero_envoi}"
                    )
                except Exception as state_err:
                    print(f"⚠️ Erreur transition état commande {commande.id}: {state_err}")
                    continue

            # Marquer l'envoi comme livré (clôturé)
            envoi.marquer_comme_livre(getattr(request.user, 'profil_operateur', None))

        return JsonResponse({
            'success': True, 
            'message': f'Envoi {envoi.numero_envoi} clôturé avec succès'
        })
    except Envoi.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Envoi non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@superviseur_preparation_required
def rafraichir_articles_commande_prepa(request, commande_id):
    """Rafraîchir la section des articles de la commande en préparation"""
    print(f"🔄 Rafraîchissement des articles pour la commande {commande_id}")
    
    try:
        operateur = Operateur.objects.get(user=request.user, actif=True)
        
        # Vérifier le type d'opérateur
        if operateur.type_operateur not in ['SUPERVISEUR_PREPARATION', 'PREPARATION', 'ADMIN']:
            return JsonResponse({'error': 'Accès non autorisé.'}, status=403)
            
    except Operateur.DoesNotExist:
        # Fallback si pas de profil: autoriser selon groupes Django
        if not request.user.groups.filter(name__in=['superviseur', 'operateur_preparation']).exists():
            return JsonResponse({'error': 'Profil d\'opérateur de préparation non trouvé.'}, status=403)
        operateur = None
    
    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Pour les superviseurs, on ne vérifie pas l'affectation spécifique
        # Ils peuvent accéder à toutes les commandes en préparation
        if operateur and operateur.type_operateur == 'SUPERVISEUR_PREPARATION':
            # Vérifier seulement que la commande est en préparation
            etat_preparation = commande.etats.filter(
                enum_etat__libelle__in=['En préparation', 'À imprimer'],
                date_fin__isnull=True
            ).first()
        else:
            # Pour les opérateurs normaux, vérifier l'affectation spécifique
            etat_preparation = commande.etats.filter(
                operateur=operateur,
                enum_etat__libelle__in=['En préparation', 'À imprimer'],
                date_fin__isnull=True
            ).first()
        
        if not etat_preparation:
            return JsonResponse({'error': 'Cette commande ne vous est pas affectée.'}, status=403)
        
        # Générer le HTML directement pour éviter les erreurs de template
        paniers = commande.paniers.select_related('article').all()
        html_rows = []
        
        for panier in paniers:
            # Utiliser le filtre Django pour calculer le prix selon la logique upsell
            from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
            
            prix_calcule = get_prix_upsell_avec_compteur(panier.article, commande.compteur)
            
            # Déterminer l'affichage selon le type d'article
            if panier.article.isUpsell:
                prix_class = "text-orange-600"
                upsell_badge = f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-700 ml-2"><i class="fas fa-arrow-up mr-1"></i>Upsell</span>'
                
                # Déterminer le niveau d'upsell affiché
                if commande.compteur >= 4 and panier.article.prix_upsell_4 is not None:
                    niveau_upsell = 4
                elif commande.compteur >= 3 and panier.article.prix_upsell_3 is not None:
                    niveau_upsell = 3
                elif commande.compteur >= 2 and panier.article.prix_upsell_2 is not None:
                    niveau_upsell = 2
                elif commande.compteur >= 1 and panier.article.prix_upsell_1 is not None:
                    niveau_upsell = 1
                else:
                    niveau_upsell = 0
                
                if niveau_upsell > 0:
                    upsell_info = f'<div class="text-xs text-orange-600 flex items-center justify-center gap-1"><i class="fas fa-arrow-up"></i>Upsell Niveau {niveau_upsell}</div>'
                else:
                    upsell_info = f'<div class="text-xs text-orange-600 flex items-center justify-center gap-1"><i class="fas fa-arrow-up"></i>Upsell (Prix normal)</div>'
            else:
                # Prix normal
                prix_class = "text-gray-700"
                upsell_badge = ""
                upsell_info = ""
            
            sous_total = prix_calcule * panier.quantite
            
            html_row = f"""
            <tr data-panier-id="{panier.id}" data-article-id="{panier.article.id}">
                <td class="px-4 py-3">
                    <div class="flex items-center">
                        <div class="flex-1">
                            <div class="font-medium text-gray-900 flex items-center">
                                {panier.article.nom}
                                {upsell_badge}
                            </div>
                            <div class="text-sm text-gray-500">
                                Réf: {panier.article.reference or 'N/A'}
                                {f" · Réf variante: {getattr(panier.variante, 'reference', '')}" if hasattr(panier, 'variante') and getattr(panier, 'variante', None) and getattr(panier.variante, 'reference', None) else ''}
                                {f" · Couleur: {getattr(getattr(panier.variante,'couleur', None),'nom','')}" if hasattr(panier, 'variante') and getattr(panier, 'variante', None) and getattr(panier.variante, 'couleur', None) else ''}
                                {f" · Pointure: {getattr(getattr(panier.variante,'pointure', None),'pointure','')}" if hasattr(panier, 'variante') and getattr(panier, 'variante', None) and getattr(panier.variante, 'pointure', None) else ''}
                            </div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center space-x-2">
                        <button type="button" onclick="modifierQuantite({panier.id}, -1)" 
                                class="w-8 h-8 bg-gray-200 hover:bg-gray-300 rounded text-sm transition-colors">-</button>
                        <input type="number" id="quantite-{panier.id}" value="{panier.quantite}" min="1" 
                               class="w-16 p-2 border rounded-lg text-center" 
                               onchange="modifierQuantiteDirecte({panier.id}, this.value)">
                        <button type="button" onclick="modifierQuantite({panier.id}, 1)" 
                                class="w-8 h-8 bg-gray-200 hover:bg-gray-300 rounded text-sm transition-colors">+</button>
                    </div>
                </td>
                <td class="px-4 py-3 text-center">
                    <div class="font-medium {prix_class}" id="prix-unitaire-{panier.id}">
                        {prix_calcule:.2f} DH
                    </div>
                    {upsell_info}
                </td>
                <td class="px-4 py-3 text-center">
                    <div class="font-bold text-gray-900">
                        {sous_total:.2f} DH
                    </div>
                </td>
                <td class="px-4 py-3 text-center">
                    <button type="button" onclick="supprimerArticle({panier.id})" 
                            class="px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors">
                        <i class="text-white text-sm rounded-lg transition-colors">
                        <i class="fas fa-trash mr-1"></i>Supprimer
                    </button>
                </td>
            </tr>
            """
            html_rows.append(html_row)
        
        html = "".join(html_rows)
        
        # Calculer les statistiques upsell
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        total_quantite_upsell = articles_upsell.aggregate(
            total=Sum('quantite')
        )['total'] or 0
        
        response_data = {
            'success': True,
            'html': html,
            'articles_count': commande.paniers.count(),
            'total_commande': float(commande.total_cmd),
            'sous_total_articles': float(commande.sous_total_articles),
            'compteur': commande.compteur,
            'articles_upsell': articles_upsell.count(),
            'quantite_totale_upsell': total_quantite_upsell
        }
        
        print(f"✅ Rafraîchissement terminé - Articles: {response_data['articles_count']}, Compteur: {response_data['compteur']}")
        print(f"🔍 Détails du compteur: type={type(commande.compteur)}, valeur={commande.compteur}")
        if commande.compteur is None:
            print("⚠️ ATTENTION: Le compteur est None dans la base de données")
        elif commande.compteur == 0:
            print("ℹ️ Le compteur est 0 (normal si pas d'articles upsell)")
        else:
            print(f"✅ Le compteur a une valeur: {commande.compteur}")
        return JsonResponse(response_data)
        
    except Commande.DoesNotExist:
        print(f"❌ Commande {commande_id} non trouvée")
        return JsonResponse({'error': 'Commande non trouvée'}, status=404)
    except Exception as e:
        print(f"❌ Erreur lors du rafraîchissement: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)

@superviseur_preparation_required
def ajouter_article_commande_prepa(request, commande_id):
    """Ajouter un article à la commande en préparation"""
    print("🔄 ===== DÉBUT ajouter_article_commande_prepa =====")
    print(f"📦 Méthode HTTP: {request.method}")
    print(f"📦 Commande ID: {commande_id}")
    print(f"📦 User: {request.user}")
    print(f"📦 POST data: {dict(request.POST)}")
    print(f"📦 Headers: {dict(request.headers)}")
    
    if request.method != 'POST':
        print("❌ Méthode non autorisée")
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Autoriser PREPARATION et SUPERVISEUR_PREPARATION
        operateur = Operateur.objects.get(user=request.user, actif=True)
        print(f"✅ Opérateur trouvé: {operateur.id} - Type: {operateur.type_operateur}")
        if operateur.type_operateur not in ['PREPARATION', 'SUPERVISEUR_PREPARATION']:
            print(f"❌ Type d'opérateur non autorisé: {operateur.type_operateur}")
            return JsonResponse({'error': "Accès réservé à l'équipe préparation"}, status=403)
    except Operateur.DoesNotExist:
        print("❌ Profil d'opérateur non trouvé")
        return JsonResponse({'error': 'Profil d\'opérateur non trouvé.'}, status=403)
    
    try:
        with transaction.atomic():
            print("🔧 Début de la transaction atomique")
            commande = Commande.objects.select_for_update().get(id=commande_id)
            print(f"✅ Commande trouvée: {commande.id} - ID YZ: {commande.id_yz}")
            
            # Vérifier que la commande est en préparation
            if operateur.type_operateur == 'SUPERVISEUR_PREPARATION':
                # Le superviseur peut agir sur toute commande en cours (sans contrainte d'affectation)
                etat_preparation = commande.etats.filter(
                    enum_etat__libelle__in=['En préparation', 'À imprimer'],
                    date_fin__isnull=True
                ).first()
            else:
                # Opérateur préparation: seulement sur les commandes qui lui sont affectées
                etat_preparation = commande.etats.filter(
                    operateur=operateur,
                    enum_etat__libelle__in=['En préparation', 'À imprimer'],
                    date_fin__isnull=True
                ).first()
            
            if not etat_preparation:
                print("❌ Commande non en préparation pour cet opérateur")
                return JsonResponse({'error': 'Cette commande n\'est pas en préparation pour vous.'}, status=403)
            
            print(f"✅ État de préparation trouvé: {etat_preparation.enum_etat.libelle}")
            
            article_id = request.POST.get('article_id')
            quantite = int(request.POST.get('quantite', 1))
            variante_id = request.POST.get('variante_id')

            print("[AJOUT VARIANTE] entrée:", {
                'commande_id': commande_id,
                'operateur': getattr(operateur, 'id', None),
                'article_id': article_id,
                'quantite': quantite,
                'variante_id': variante_id,
            })
            
            if not article_id or quantite <= 0:
                print(f"❌ Données invalides: article_id={article_id}, quantite={quantite}")
                return JsonResponse({'error': 'Données invalides'}, status=400)

            print(f"✅ Données reçues: article_id={article_id}, quantite={quantite}, variante_id={variante_id}")
            article = Article.objects.get(id=article_id)
            print(f"✅ Article trouvé: {article.id} - {article.nom}")
            variante_obj = None
            if variante_id:
                try:
                    from article.models import VarianteArticle
                    variante_obj = VarianteArticle.objects.get(id=int(variante_id), article=article)
                    print("[AJOUT VARIANTE] variante trouvée:", {
                        'id': variante_obj.id,
                        'couleur': getattr(getattr(variante_obj, 'couleur', None), 'nom', None),
                        'pointure': getattr(getattr(variante_obj, 'pointure', None), 'pointure', None),
                        'qte_disponible_avant': variante_obj.qte_disponible,
                    })
                except Exception:
                    variante_obj = None
                    print("[AJOUT VARIANTE] variante introuvable ou invalide", variante_id)
            
            # Décrémenter le stock et créer un mouvement
            print("[AJOUT VARIANTE] création mouvement stock", {
                'article': article.id,
                'quantite': quantite,
                'type': 'sortie',
                'variante': getattr(variante_obj, 'id', None),
            })
            creer_mouvement_stock(
                article=article, quantite=quantite, type_mouvement='sortie',
                commande=commande, operateur=operateur,
                commentaire=f'Ajout article pendant préparation cmd {commande.id_yz}',
                variante=variante_obj
            )
            
            # Vérifier si l'article existe déjà dans la commande
            filtre_panier = {'commande': commande, 'article': article}
            if hasattr(Panier, 'variante'):
                filtre_panier['variante'] = variante_obj
            panier_existant = Panier.objects.filter(**filtre_panier).first()
            print("[AJOUT VARIANTE] filtre panier:", {
                'commande': commande.id,
                'article': article.id,
                'variante': getattr(variante_obj, 'id', None),
                'existant': getattr(panier_existant, 'id', None)
            })
            
            if panier_existant:
                # Si l'article existe déjà, mettre à jour la quantité
                panier_existant.quantite += quantite
                panier_existant.save()
                panier = panier_existant
                print(f"[AJOUT VARIANTE] 🔄 panier existant {panier.id} mis à jour, nouvelle_quantite={panier.quantite}")
            else:
                # Si l'article n'existe pas, créer un nouveau panier
                create_kwargs = {
                    'commande': commande,
                    'article': article,
                    'quantite': quantite,
                    'sous_total': 0,
                }
                if hasattr(Panier, 'variante'):
                    create_kwargs['variante'] = variante_obj
                panier = Panier.objects.create(**create_kwargs)
                print(f"[AJOUT VARIANTE] ➕ nouveau panier créé id={panier.id}, article={article.id}, variante={getattr(variante_obj,'id',None)}, quantite={quantite}")
            
            # Recalculer le compteur après ajout (logique de confirmation)
            if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:
                # Compter la quantité totale d'articles upsell (après ajout)
                total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                    total=Sum('quantite')
                )['total'] or 0
                
                # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                # 0-1 unités upsell → compteur = 0
                # 2+ unités upsell → compteur = total_quantite_upsell - 1
                if total_quantite_upsell >= 2:
                    commande.compteur = total_quantite_upsell - 1
                else:
                    commande.compteur = 0
                
                commande.save()
                
                # Recalculer TOUS les articles de la commande avec le nouveau compteur
                commande.recalculer_totaux_upsell()
            else:
                # Pour les articles normaux, juste calculer le sous-total
                from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)
                sous_total = prix_unitaire * panier.quantite
                panier.sous_total = float(sous_total)
                panier.save()
            
            # Recalculer le total
            commande.total_cmd = sum(p.sous_total for p in commande.paniers.all())
            commande.save()
            print("[AJOUT VARIANTE] totaux mis à jour:", {
                'commande_id': commande.id,
                'total_cmd': commande.total_cmd,
                'articles_count': commande.paniers.count(),
            })
            
            # Calculer les statistiques upsell
            articles_upsell = commande.paniers.filter(article__isUpsell=True)
            total_quantite_upsell = articles_upsell.aggregate(
                total=Sum('quantite')
            )['total'] or 0
            
            # Déterminer si c'était un ajout ou une mise à jour
            message = 'Article ajouté' if not panier_existant else f'Quantité mise à jour ({panier.quantite})'
            
            # Préparer les données de l'article pour le frontend
            article_data = {
                'panier_id': panier.id,
                'article_id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'couleur_fr': (variante_obj.couleur.nom if variante_obj and variante_obj.couleur else (article.couleur or '')),
                'couleur_ar': (variante_obj.couleur.nom if variante_obj and variante_obj.couleur else (article.couleur or '')),
                'pointure': (variante_obj.pointure.pointure if variante_obj and variante_obj.pointure else (article.pointure or '')),
                'quantite': panier.quantite,
                'prix': panier.sous_total / panier.quantite,  # Prix unitaire
                'sous_total': panier.sous_total,
                'is_upsell': article.isUpsell,
                'compteur': commande.compteur,
                'phase': article.phase,
                'has_promo_active': article.has_promo_active,
                'qte_disponible': variante_obj.qte_disponible if variante_obj else article.qte_disponible,
                'description': article.description or ''
            }
            
            response_data = {
                'success': True, 
                'message': message,
                'compteur': commande.compteur,
                'total_commande': float(commande.total_cmd),
                'was_update': panier_existant is not None,
                'new_quantity': panier.quantite,
                'article_data': article_data,
                'articles_count': commande.paniers.count(),
                'sous_total_articles': float(sum(p.sous_total for p in commande.paniers.all())),
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            }
            
            print("✅ ===== SUCCÈS ajouter_article_commande_prepa =====")
            print(f"📦 Réponse: {response_data}")
            
            return JsonResponse(response_data)
            
    except Article.DoesNotExist:
        print("❌ Article non trouvé")
        return JsonResponse({'error': 'Article non trouvé'}, status=404)
    except Exception as e:
        print(f"❌ ===== ERREUR ajouter_article_commande_prepa =====")
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)

@superviseur_preparation_required
def modifier_quantite_article_prepa(request, commande_id):
    """Modifier la quantité d'un article dans la commande en préparation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Profil d\'opérateur non trouvé.'}, status=403)

    try:
        with transaction.atomic():
            commande = Commande.objects.select_for_update().get(id=commande_id)
            
            # Vérifier l'affectation
            if not commande.etats.filter(operateur=operateur, enum_etat__libelle__in=['En préparation', 'À imprimer'], date_fin__isnull=True).exists():
                return JsonResponse({'error': 'Commande non affectée.'}, status=403)
            
            panier_id = request.POST.get('panier_id')
            nouvelle_quantite = int(request.POST.get('quantite', 1))

            panier = Panier.objects.get(id=panier_id, commande=commande)
            ancienne_quantite = panier.quantite
            article = panier.article
            difference = nouvelle_quantite - ancienne_quantite

            if difference > 0:
                creer_mouvement_stock(article, difference, 'sortie', commande, operateur, f'Ajustement qté cmd {commande.id_yz}')
            elif difference < 0:
                creer_mouvement_stock(article, abs(difference), 'entree', commande, operateur, f'Ajustement qté cmd {commande.id_yz}')

            panier.quantite = nouvelle_quantite
            
            # Recalculer le compteur si c'est un article upsell
            if article.isUpsell:
                # Compter la quantité totale d'articles upsell après modification
                total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                    total=Sum('quantite')
                )['total'] or 0
                
                # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                if total_quantite_upsell >= 2:
                    commande.compteur = total_quantite_upsell - 1
                else:
                    commande.compteur = 0
                
                commande.save()
                
                # Recalculer TOUS les articles de la commande avec le nouveau compteur
                commande.recalculer_totaux_upsell()
            else:
                # Pour les articles normaux, juste calculer le sous-total
                from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)
                panier.sous_total = prix_unitaire * nouvelle_quantite
            panier.save()

            commande.total_cmd = sum(p.sous_total for p in commande.paniers.all())
            commande.save()

            # Calculer les statistiques upsell
            articles_upsell = commande.paniers.filter(article__isUpsell=True)
            total_quantite_upsell = articles_upsell.aggregate(
                total=Sum('quantite')
            )['total'] or 0

            return JsonResponse({
                'success': True, 
                'message': 'Quantité modifiée',
                'compteur': commande.compteur,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell,
                'total_commande': float(commande.total_cmd),
                'sous_total_articles': float(commande.sous_total_articles)
            })

    except Panier.DoesNotExist:
        return JsonResponse({'error': 'Panier non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)

@superviseur_preparation_required
def supprimer_article_commande_prepa(request, commande_id):
    """Supprimer un article de la commande en préparation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Profil d\'opérateur non trouvé.'}, status=403)

    try:
        with transaction.atomic():
            commande = Commande.objects.select_for_update().get(id=commande_id)
            
            # Vérifier l'affectation
            if not commande.etats.filter(operateur=operateur, enum_etat__libelle__in=['En préparation', 'À imprimer'], date_fin__isnull=True).exists():
                return JsonResponse({'error': 'Commande non affectée.'}, status=403)

            panier_id = request.POST.get('panier_id')
            panier = Panier.objects.get(id=panier_id, commande=commande)
            quantite_supprimee = panier.quantite
            article = panier.article
            
            creer_mouvement_stock(article, quantite_supprimee, 'entree', commande, operateur, f'Suppression article cmd {commande.id_yz}')
            
            # Sauvegarder l'info avant suppression
            etait_upsell = panier.article.isUpsell
            
            # Supprimer l'article
            panier.delete()

            # Recalculer le compteur après suppression (logique de confirmation)
            if etait_upsell:
                # Compter la quantité totale d'articles upsell restants (après suppression)
                total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                    total=Sum('quantite')
                )['total'] or 0
                
                # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                if total_quantite_upsell >= 2:
                    commande.compteur = total_quantite_upsell - 1
                else:
                    commande.compteur = 0
                
                commande.save()
                
                # Recalculer TOUS les articles de la commande avec le nouveau compteur
                commande.recalculer_totaux_upsell()

            commande.total_cmd = sum(p.sous_total for p in commande.paniers.all())
            commande.save()

            # Calculer les statistiques upsell
            articles_upsell = commande.paniers.filter(article__isUpsell=True)
            total_quantite_upsell = articles_upsell.aggregate(
                total=Sum('quantite')
            )['total'] or 0

            return JsonResponse({
                'success': True, 
                'message': 'Article supprimé',
                'compteur': commande.compteur,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell,
                'total_commande': float(commande.total_cmd),
                'sous_total_articles': float(commande.sous_total_articles)
            })

    except Panier.DoesNotExist:
        return JsonResponse({'error': 'Panier non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erreur interne: {str(e)}'}, status=500)

@superviseur_preparation_required
def api_panier_commande_livraison(request, commande_id):
    """API pour récupérer le panier d'une commande pour les opérateurs de livraison"""
    try:
        # Vérifier que l'utilisateur est un opérateur de livraison
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
    
    # Récupérer la commande
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    
    # Récupérer les paniers de la commande
    paniers = commande.paniers.all().select_related('article')
    
    paniers_data = []
    for panier in paniers:
        paniers_data.append({
            'id': panier.id,
            'article_id': panier.article.id,
            'nom': panier.article.nom,
            'reference': panier.article.reference,
            'couleur': panier.article.couleur,
            'pointure': panier.article.pointure,
            'prix_unitaire': float(panier.article.prix_unitaire),
            'quantite': panier.quantite,
            'sous_total': float(panier.sous_total),
            'qte_disponible': panier.article.qte_disponible,
        })
    
    return JsonResponse({
        'success': True,
        'paniers': paniers_data,
        'total_commande': float(commande.total_cmd)
    })

@superviseur_preparation_required
def api_articles_commande_livree_partiellement(request, commande_id):
    """API pour récupérer les détails des articles d'une commande livrée partiellement"""
    import json
    from article.models import Article
    from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation
    from parametre.models import Operateur

    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
    
    # Récupérer la commande
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur lors de la récupération de la commande: {str(e)}'})
    
    # Analyser les articles pour les commandes livrées partiellement
    articles_livres = []
    articles_renvoyes = []
    
    # Récupérer tous les états de la commande
    etats_commande = commande.etats.all().select_related('enum_etat', 'operateur').order_by('date_debut')
    
    # Déterminer l'état actuel
    etat_actuel = etats_commande.filter(date_fin__isnull=True).first()
    
    # Récupérer l'état précédent pour comprendre d'où vient la commande
    etat_precedent = None
    if etat_actuel:
        # Trouver l'état précédent (le dernier état terminé avant l'état actuel)
        for etat in reversed(etats_commande):
            if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:
                    etat_precedent = etat
                    break
    
    # Vérifier si c'est une commande livrée partiellement
    if etat_actuel and etat_actuel.enum_etat.libelle == 'Livrée Partiellement':
        # Les articles dans cette commande sont ceux qui ont été livrés partiellement
        for panier in commande.paniers.all():
            articles_livres.append({
                'article_id': panier.article.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'couleur': panier.article.couleur,
                'pointure': panier.article.pointure,
                'quantite_livree': panier.quantite,
                'prix': float(panier.article.prix_unitaire),
                'sous_total': float(panier.sous_total)
            })
        
        # Chercher la commande de renvoi associée
        commande_renvoi = Commande.objects.filter(
            num_cmd__startswith=f"RENVOI-{commande.num_cmd}",
            client=commande.client
        ).first()
        
        if commande_renvoi:
            # Récupérer l'état des articles renvoyés depuis l'opération de livraison partielle
            etat_articles_renvoyes = {}
            operation_livraison_partielle = commande.operations.filter(
                type_operation='LIVRAISON_PARTIELLE'
            ).order_by('-date_operation').first()
            if operation_livraison_partielle:
                try:
                    details = json.loads(operation_livraison_partielle.conclusion)
                    if 'recap_articles_renvoyes' in details:
                        for item in details['recap_articles_renvoyes']:
                            etat_articles_renvoyes[item['article_id']] = item['etat']
                except Exception:
                    pass
            if commande_renvoi:
                for panier_renvoi in commande_renvoi.paniers.all():
                    etat = etat_articles_renvoyes.get(panier_renvoi.article.id, 'bon')
                    articles_renvoyes.append({
                        'article_id': panier_renvoi.article.id,
                        'nom': panier_renvoi.article.nom,
                        'reference': panier_renvoi.article.reference,
                        'couleur': panier_renvoi.article.couleur,
                        'pointure': panier_renvoi.article.pointure,
                        'quantite': panier_renvoi.quantite,
                        'prix': float(panier_renvoi.article.prix_unitaire),
                        'sous_total': float(panier_renvoi.sous_total),
                        'etat': etat
                    })
    # Vérifier si c'est une commande renvoyée après livraison partielle
    elif etat_precedent and etat_precedent.enum_etat.libelle == 'Livrée Partiellement':
        # Chercher la commande originale qui a été livrée partiellement
        commande_originale = Commande.objects.filter(
            num_cmd=commande.num_cmd.replace('RENVOI-', ''),
            client=commande.client
        ).first()
        # Récupérer l'état des articles renvoyés depuis l'opération de livraison partielle
        etat_articles_renvoyes = {}
        if commande_originale:
            operation_livraison_partielle = commande_originale.operations.filter(
                type_operation='LIVRAISON_PARTIELLE'
            ).order_by('-date_operation').first()
            if operation_livraison_partielle:
                try:
                    details = json.loads(operation_livraison_partielle.conclusion)
                    if 'recap_articles_renvoyes' in details:
                        for item in details['recap_articles_renvoyes']:
                            etat_articles_renvoyes[item['article_id']] = item['etat']
                except Exception:
                    pass
        if commande_originale:
            # Les articles dans cette commande de renvoi sont ceux qui ont été renvoyés
            for panier in commande_originale.paniers.all():
                etat = etat_articles_renvoyes.get(panier.article.id, 'bon')
                articles_renvoyes.append({
                    'article': panier.article,
                    'quantite': panier.quantite,
                    'prix': panier.article.prix_unitaire,
                    'sous_total': panier.sous_total,
                    'etat': etat
                })
    
    # Récupérer les détails de la livraison partielle
    date_livraison_partielle = None
    commentaire_livraison_partielle = None
    operateur_livraison = None
    
    if etat_actuel and etat_actuel.enum_etat.libelle == 'Livrée Partiellement':
        date_livraison_partielle = etat_actuel.date_debut
        commentaire_livraison_partielle = etat_actuel.commentaire
        operateur_livraison = etat_actuel.operateur
    elif etat_precedent and etat_precedent.enum_etat.libelle == 'Livrée Partiellement':
        date_livraison_partielle = etat_precedent.date_debut
        commentaire_livraison_partielle = etat_precedent.commentaire
        operateur_livraison = etat_precedent.operateur
    
    try:
        return JsonResponse({
            'success': True,
            'commande': {
                'id': commande.id,
                'id_yz': commande.id_yz,
                'num_cmd': commande.num_cmd,
                'total_cmd': float(commande.total_cmd),
                'date_livraison_partielle': date_livraison_partielle.isoformat() if date_livraison_partielle else None,
                'commentaire_livraison_partielle': commentaire_livraison_partielle,
                'operateur_livraison': {
                    'nom': operateur_livraison.nom_complet if operateur_livraison else None,
                    'email': operateur_livraison.mail if operateur_livraison else None
                } if operateur_livraison else None
            },
            'articles_livres': articles_livres,
            'articles_renvoyes': articles_renvoyes,
            'total_articles_livres': len(articles_livres),
            'total_articles_renvoyes': len(articles_renvoyes)
        })
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse JSON: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erreur lors de la génération de la réponse: {str(e)}'
        })

@superviseur_preparation_required
def api_prix_upsell_articles(request, commande_id):
    """API pour récupérer les prix upsell mis à jour des articles"""
    print(f"🔄 Récupération des prix upsell pour la commande {commande_id}")

    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Profil d\'opérateur de préparation non trouvé.'}, status=403)

    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_preparation = commande.etats.filter(
            operateur=operateur,
            enum_etat__libelle__in=['En préparation', 'À imprimer'],
            date_fin__isnull=True
        ).first()
        
        if not etat_preparation:
            return JsonResponse({'error': 'Cette commande ne vous est pas affectée.'}, status=403)
        
        # Récupérer tous les articles du panier avec leurs prix mis à jour
        paniers = commande.paniers.select_related('article').all()
        prix_articles = {}
        
        for panier in paniers:
            # Utiliser le filtre Django pour calculer le prix selon la logique upsell
            from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
            
            # Debug: Afficher les informations de l'article
            print(f"🔍 Article {panier.article.id} ({panier.article.nom}):")
            print(f"   - isUpsell: {panier.article.isUpsell}")
            print(f"   - prix_actuel: {panier.article.prix_actuel}")
            print(f"   - prix_unitaire: {panier.article.prix_unitaire}")
            print(f"   - prix_upsell_1: {panier.article.prix_upsell_1}")
            print(f"   - prix_upsell_2: {panier.article.prix_upsell_2}")
            print(f"   - prix_upsell_3: {panier.article.prix_upsell_3}")
            print(f"   - prix_upsell_4: {panier.article.prix_upsell_4}")
            print(f"   - compteur: {commande.compteur}")
            
            prix_calcule = get_prix_upsell_avec_compteur(panier.article, commande.compteur)
            print(f"   - prix_calcule: {prix_calcule}")
            
            # Convertir en float pour éviter les problèmes de sérialisation JSON
            prix_calcule = float(prix_calcule) if prix_calcule is not None else 0.0
            
            # Déterminer le type de prix et les informations
            if panier.article.isUpsell:
                prix_type = "upsell"
                
                # Déterminer le niveau d'upsell affiché
                if commande.compteur >= 4 and panier.article.prix_upsell_4 is not None:
                    niveau_upsell = 4
                elif commande.compteur >= 3 and panier.article.prix_upsell_3 is not None:
                    niveau_upsell = 3
                elif commande.compteur >= 2 and panier.article.prix_upsell_2 is not None:
                    niveau_upsell = 2
                elif commande.compteur >= 1 and panier.article.prix_upsell_1 is not None:
                    niveau_upsell = 1
                else:
                    niveau_upsell = 0
                
                if niveau_upsell > 0:
                    libelle = f"Upsell Niveau {niveau_upsell}"
                else:
                    libelle = "Upsell (Prix normal)"
                    
                icone = "fas fa-arrow-up"
            else:
                prix_type = "normal"
                libelle = "Prix normal"
                icone = "fas fa-tag"
                niveau_upsell = 0
            
            prix_articles[panier.id] = {
                'prix': prix_calcule,
                'type': prix_type,
                'libelle': libelle,
                'icone': icone,
                'niveau_upsell': niveau_upsell,
                'is_upsell': panier.article.isUpsell,
                'sous_total': float(prix_calcule * panier.quantite)
            }
        
        return JsonResponse({
            'success': True,
            'prix_articles': prix_articles,
            'compteur': commande.compteur,
            'message': f'Prix mis à jour pour {len(prix_articles)} articles'
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'error': 'Commande non trouvée.'}, status=404)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des prix upsell: {e}")
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)

@superviseur_preparation_required
def commandes_confirmees(request):
    """Page des commandes confirmées"""
    from django.utils import timezone
    from datetime import datetime, timedelta

    # Récupérer toutes les commandes confirmées (état actif sans date_fin)
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True  # État actif (en cours)
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_confirmees = commandes_confirmees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(etats__operateur__nom__icontains=search_query) |
            Q(etats__operateur__prenom__icontains=search_query)
        ).distinct()

    # Tri par date de confirmation (plus récentes en premier)
    commandes_confirmees = commandes_confirmees.order_by('-etats__date_debut')

    # Créer une copie des données non paginées pour les statistiques AVANT la pagination
    commandes_non_paginees = commandes_confirmees

    # Paramètres de pagination flexible
    items_per_page = request.GET.get('items_per_page', 25)
    start_range = request.GET.get('start_range')
    end_range = request.GET.get('end_range')

    # Gestion de la pagination flexible
    if start_range and end_range:
        try:
            start_range = int(start_range)
            end_range = int(end_range)
            if start_range > 0 and end_range >= start_range:
                # Pagination par plage personnalisée
                commandes_confirmees = commandes_confirmees[start_range-1:end_range]
                paginator = Paginator(commandes_confirmees, end_range - start_range + 1)
                page_obj = paginator.get_page(1)
            else:
                # Plage invalide, utiliser la pagination normale
                items_per_page = 25
                paginator = Paginator(commandes_confirmees, items_per_page)
                page_number = request.GET.get('page', 1)
                page_obj = paginator.get_page(page_number)
        except (ValueError, TypeError):
            # Erreur de conversion, utiliser la pagination normale
            items_per_page = 25
            paginator = Paginator(commandes_confirmees, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        if items_per_page == 'all':
            # Afficher toutes les commandes
            paginator = Paginator(commandes_confirmees, commandes_confirmees.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 25
            except (ValueError, TypeError):
                items_per_page = 25
            
            paginator = Paginator(commandes_confirmees, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)

    # Statistiques
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Confirmées aujourd'hui
    confirmees_aujourd_hui = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,  # État actif
        etats__date_debut__date=today
    ).distinct().count()

    # Confirmées cette semaine
    confirmees_semaine = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,  # État actif
        etats__date_debut__date__gte=week_start
    ).distinct().count()

    # Confirmées ce mois
    confirmees_mois = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,  # État actif
        etats__date_debut__date__gte=month_start
    ).distinct().count()

    # Total des commandes confirmées (utiliser les données non paginées)
    total_confirmees = commandes_non_paginees.count()

    # Montant total des commandes confirmées (utiliser les données non paginées)
    montant_total = commandes_non_paginees.aggregate(total=Sum('total_cmd'))['total'] or 0

    # Ajouter l'état de confirmation à chaque commande
    for commande in page_obj:
        etats_commande = list(commande.etats.all().order_by('date_debut'))
        
        # Trouver l'état de confirmation (le premier état "Confirmée")
        etat_confirmation = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == 'Confirmée':
                etat_confirmation = etat
                break
        
        commande.etat_confirmation = etat_confirmation

    # Récupérer les opérateurs de préparation actifs
    operateurs_preparation = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).order_by('nom', 'prenom')

    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Rendre les templates partiels pour AJAX
        html_table_body = render_to_string('Superpreparation/partials/_confirmees_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('Superpreparation/partials/_confirmees_pagination.html', {
            'page_obj': page_obj,
            'search_query': search_query,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('Superpreparation/partials/_confirmees_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': commandes_confirmees.count()
        })

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_confirmees': total_confirmees,
        'confirmees_aujourd_hui': confirmees_aujourd_hui,
        'confirmees_semaine': confirmees_semaine,
        'confirmees_mois': confirmees_mois,
        'montant_total': montant_total,
        'operateurs_preparation': operateurs_preparation,
        'page_title': 'Suivi des Commandes Confirmées',
        'page_subtitle': 'Suivi et gestion des commandes validées prêtes pour la préparation',
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }

    return render(request, 'Superpreparation/commande_confirmees.html', context)

@login_required
def get_article_variants(request, article_id):
    """Récupère toutes les variantes disponibles d'un article donné"""
    try:
        from article.models import Article, VarianteArticle
        
        print(f"🔍 Recherche des variantes pour l'article ID: {article_id} (type: {type(article_id)})")
        
        # D'abord, vérifier si l'article existe (avec ou sans le filtre actif=True)
        try:
            article_test = Article.objects.get(id=article_id)
            print(f"📋 Article trouvé mais actif={article_test.actif}")
        except Article.DoesNotExist:
            print(f"❌ Aucun article trouvé avec l'ID {article_id}")
            # Lister quelques articles pour debug
            articles_existants = Article.objects.all()[:5]
            print("📚 Articles existants (premiers 5):")
            for art in articles_existants:
                print(f"   - ID: {art.id}, Nom: {art.nom}, Actif: {art.actif}")
        
        # Vérifier que l'article existe ET est actif
        article = get_object_or_404(Article, id=article_id, actif=True)
        print(f"✅ Article trouvé: {article.nom}")
        
        # Récupérer toutes les variantes actives de cet article
        variantes = VarianteArticle.objects.filter(
            article=article,
            actif=True
        ).select_related('couleur', 'pointure').order_by('couleur__nom', 'pointure__ordre')
        
        print(f"📊 Nombre de variantes trouvées: {variantes.count()}")
        
        # Construire la liste des variantes avec leurs informations
        variants_data = []
        for variante in variantes:
            print(f"🔸 Variante: {variante.id} - Couleur: {variante.couleur} - Pointure: {variante.pointure} - Stock: {variante.qte_disponible}")
            
            variant_info = {
                'id': variante.id,
                'couleur': variante.couleur.nom if variante.couleur else None,
                'pointure': variante.pointure.pointure if variante.pointure else None,
                'taille': None,  # À adapter selon votre modèle si vous avez des tailles
                'stock': variante.qte_disponible,
                'qte_disponible': variante.qte_disponible,
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
        
        print(f"📤 Réponse envoyée: {len(variants_data)} variantes")
        return JsonResponse(response_data)
        
    except Article.DoesNotExist:
        print(f"❌ Article {article_id} non trouvé")
        return JsonResponse({
            'success': False,
            'error': 'Article non trouvé'
        }, status=404)
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans get_article_variants: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la récupération des variantes'
        }, status=500)

def generate_barcode_for_commande(commande_id_yz):
    """Fonction utilitaire pour générer le code-barres d'une commande"""
    try:
        barcode_data = str(commande_id_yz)
        print(f"📊 Génération du code-barres: {barcode_data}")
        
        # Créer un code-barres avec les mêmes options que Prepacommande
        code128 = barcode.get_barcode_class("code128")
        barcode_instance = code128(barcode_data, writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(
            buffer,
            options={
                "write_text": False,
                "module_height": 4.0,  # Hauteur augmentée pour meilleure lisibilité
                "module_width": 0.15,  # Largeur augmentée pour impression claire
                "quiet_zone": 2.0,     # Zone de silence autour du code-barres
            },
        )
        barcode_base64 = base64.b64encode(buffer.getvalue()).decode()
        print(f"✅ Code-barres généré avec succès (dimensions optimisées)")
        return barcode_base64
    except Exception as barcode_error:
            print(f"❌ Erreur lors de la génération du code-barres: {str(barcode_error)}")
    return ""


@superviseur_preparation_required
def api_ticket_commande(request):
    """API pour récupérer le contenu HTML du ticket de commande"""
    try:
        ids = request.GET.get('ids')
        if not ids:
            return JsonResponse({'error': 'IDs des commandes requis'}, status=400)
        
        # Supporter plusieurs IDs séparés par des virgules
        id_list = [id.strip() for id in ids.split(',') if id.strip()]
        
        print(f"🔍 Recherche des commandes avec id_yz: {id_list} pour ticket")
        
        all_tickets_html = []
        commandes_data = []
        
        for commande_id in id_list:
            try:
                print(f"🔍 Traitement de la commande ID: {commande_id}")
                commande = Commande.objects.filter(
                    id_yz=commande_id,
                    etats__enum_etat__libelle='Confirmée',
                    paniers__isnull=False
                ).distinct().first()
                
                if not commande:
                    print(f"❌ Commande {commande_id} non trouvée ou non confirmée ou sans articles")
                    continue
                
                print(f"✅ Commande confirmée trouvée: {commande.id_yz}")
                
                # Préparer la description des articles
                articles_description = ""
                total_articles = 0
                paniers = commande.paniers.all().select_related('article', 'variante')
                for panier in paniers:
                    article = panier.article
                    variante = panier.variante
                    total_articles += panier.quantite  # Ajouter la quantité au total
                    if articles_description:
                        articles_description += " + "
                    articles_description += f"{article.nom} {variante.couleur if variante else ''} , P{panier.quantite}"
                
                # Générer le code-barres en réutilisant la logique existante
                barcode_base64 = generate_barcode_for_commande(commande.id_yz)
                
                # Récupérer toutes les variantes de la commande
                variantes = []
                print(f"🔍 Traitement de {len(paniers)} paniers pour la commande {commande.id_yz}")
                for i, panier in enumerate(paniers):
                    try:
                        print(f"  Panier {i+1}: variante={panier.variante}, article={panier.article}")
                        print(f"    🔗 Relation variante->article: {panier.variante.article if panier.variante else 'Pas de variante'}")
                        print(f"    🔗 Relation panier->article: {panier.article}")
                        
                        # Vérifier que la variante existe et qu'elle est bien liée à un article
                        if panier.variante and panier.variante.article:
                            print(f"    ✅ Variante {panier.variante.id} liée à l'article {panier.variante.article.id}")
                            
                            # Vérifier si cette variante n'est pas déjà ajoutée
                            variante_exists = any(v['id'] == panier.variante.id for v in variantes)
                            if not variante_exists:
                                variante_data = {
                                    'id': panier.variante.id,
                                    'article': {
                                        'id': panier.variante.article.id,
                                        'nom': panier.variante.article.nom or "Article sans nom",
                                        'reference': panier.variante.article.reference or ""
                                    },
                                    'couleur': panier.variante.couleur.nom if panier.variante.couleur else "",
                                    'pointure': panier.variante.pointure.pointure if panier.variante.pointure else "",
                                    'quantite': panier.quantite or 0
                                }
                                variantes.append(variante_data)
                                print(f"    ✅ Variante ajoutée: {variante_data['article']['nom']} (ID: {variante_data['id']})")
                            else:
                                print(f"    ⚠️ Variante déjà ajoutée: {panier.variante.id}")
                        elif panier.variante and not panier.variante.article:
                            print(f"    ❌ Variante {panier.variante.id} sans article associé")
                        elif not panier.variante and panier.article:
                            print(f"    ❌ Panier avec article {panier.article.id} mais sans variante")
                        else:
                            print(f"    ❌ Panier sans variante ni article")
                    except Exception as e:
                        print(f"    ❌ Erreur lors du traitement du panier {i+1}: {str(e)}")
                        continue
                
                print(f"📋 Total variantes récupérées: {len(variantes)}")
                
                # Préparer les données de la commande
                commande_data = {
                    'id_yz': commande.id_yz,
                    'num_cmd': commande.num_cmd,
                    'client_nom': f"{commande.client.nom} {commande.client.prenom}" if commande.client else "Client non défini",
                    'client_telephone': commande.client.numero_tel if commande.client else "",
                    'client_adresse': commande.adresse,
                    'ville_client': commande.ville.nom if commande.ville else "",
                    'total': commande.total_cmd,
                    'date_confirmation': commande.date_creation,
                    'articles_description': articles_description,
                    'total_articles': total_articles,
                    'barcode_image': barcode_base64,
                    'variantes': variantes
                }
                
                # Rendre le template HTML pour cette commande
                ticket_html = render_to_string('Superpreparation/partials/_ticket_commande.html', {
                    'commande': commande_data
                })
                
                all_tickets_html.append(ticket_html)
                commandes_data.append(commande_data)
                
            except Exception as e:
                import traceback
                print(f"❌ Erreur lors du traitement de la commande {commande_id}: {str(e)}")
                print(traceback.format_exc())
                continue
        
        if not all_tickets_html:
            return JsonResponse({'error': 'Aucune commande valide trouvée'}, status=404)
        
        # Combiner tous les tickets avec un conteneur en bloc pour l'impression individuelle
        combined_html = f'''
        <div class="ticket-commande-container" style="display: block; width: 100%; margin: 0 auto; padding: 0; -webkit-print-color-adjust: exact !important; color-adjust: exact !important; print-color-adjust: exact !important;">
            {''.join(all_tickets_html)}
        </div>
        '''
        
        return JsonResponse({
            'success': True,
            'html': combined_html,
            'commandes': commandes_data
        })
        
    except Exception as e:
        import traceback
        print(f"Erreur dans api_ticket_commande: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération du ticket: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def api_etiquettes_articles(request):
    """API pour récupérer le contenu HTML des étiquettes des articles"""
    try:
        ids = request.GET.get('ids')
        format_type = request.GET.get('format', 'qr')  # 'qr' ou 'barcode'
        
        if not ids:
            return JsonResponse({'error': 'IDs des commandes requis'}, status=400)
        
        print(f"🔍 Recherche de la commande avec id_yz: {ids} pour format: {format_type}")
        
        # Récupérer la commande confirmée avec des articles
        try:
            commande = Commande.objects.filter(
                id_yz=ids,
                etats__enum_etat__libelle='Confirmée',
                paniers__isnull=False
            ).distinct().first()
            
            if not commande:
                print(f"❌ Commande {ids} non trouvée ou non confirmée ou sans articles")
                return JsonResponse({'error': f'Commande {ids} non confirmée ou sans articles'}, status=404)
            
            print(f"✅ Commande confirmée trouvée: {commande.id_yz}")
        except Exception as e:
            print(f"❌ Erreur lors de la recherche de la commande {ids}: {str(e)}")
            return JsonResponse({'error': f'Erreur lors de la recherche de la commande {ids}'}, status=500)
        
        articles = commande.paniers.all().select_related('article', 'variante')
        
        articles_data = []
        for panier in articles:
            article = panier.article
            variante = panier.variante
            
            # Générer le QR code pour l'article
            try:
                import qrcode
                qr_data = f"ART{article.id}_{variante.id if variante else 'NO_VAR'}"
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir en base64
                buffer = BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            except ImportError:
                # Fallback si qrcode n'est pas installé
                qr_base64 = ""
                print("Warning: qrcode library not installed, QR codes will not be generated")
            
            # Générer le code-barres pour l'article
            barcode_data = f"ART{article.reference}_{variante.reference_variante if variante else 'NO_VAR'}"
            code128 = barcode.get_barcode_class("code128")
            barcode_image = code128(barcode_data, writer=ImageWriter())
            buffer = BytesIO()
            barcode_image.write(buffer)
            barcode_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Calculer le prix unitaire à partir du sous_total et de la quantité
            prix_unitaire = panier.sous_total / panier.quantite if panier.quantite > 0 else 0
            
            article_data = {
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'prix': float(prix_unitaire),
                'quantite': panier.quantite,
                'couleur': variante.couleur.nom if variante and variante.couleur else "Standard",
                'pointure': variante.pointure.pointure if variante and variante.pointure else "Standard",
                'qr_image': qr_base64,
                'barcode_image': barcode_base64,
                'commande_id': commande.id_yz
            }
            articles_data.append(article_data)
        
        # Rendre le template HTML avec le format spécifié
        html_content = render_to_string('Superpreparation/partials/_etiquettes_articles.html', {
            'articles': articles_data,
            'commande': {
                'id_yz': commande.id_yz,
                'client_nom': f"{commande.client.nom} {commande.client.prenom}" if commande.client else "Client non défini"
            },
            'format_type': format_type
        })
        
        return JsonResponse({
            'success': True,
            'html': html_content,
            'articles': articles_data,
            'format_type': format_type
        })
        
    except Exception as e:
        import traceback
        print(f"Erreur dans api_etiquettes_articles: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des étiquettes: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def api_etiquettes_articles_multiple(request):
    """
    API pour récupérer le contenu HTML des étiquettes de tous les articles de toutes les commandes confirmées
    Supporte la sélection de commandes spécifiques ou toutes les commandes
    """
    try:
        format_type = request.GET.get('format', 'qr')  # 'qr' ou 'barcode'
        selected_ids = request.GET.get('selected_ids', '')
        print(f"🔍 Récupération des articles pour étiquettes multiples, format: {format_type}")
        base_filter = {
            'etats__enum_etat__libelle': 'Confirmée',
            'paniers__isnull': False
        }
        # Si des IDs sont spécifiés, filtrer par ces IDs
        if selected_ids:
            try:
                # Convertir la chaîne d'IDs en liste d'entiers
                commande_ids = [int(id.strip()) for id in selected_ids.split(',') if id.strip().isdigit()]
                if commande_ids:
                    base_filter['id__in'] = commande_ids
                    print(f"🔍 Filtrage par {len(commande_ids)} commandes sélectionnées: {commande_ids}")
                else:
                    print("⚠️ Aucun ID valide trouvé dans selected_ids")
            except (ValueError, AttributeError) as e:
                print(f"❌ Erreur lors du parsing des IDs: {e}")
        else:
            print("🔍 Aucune sélection spécifique - impression de tous les articles des commandes confirmées")
        commandes = Commande.objects.filter(**base_filter).distinct().prefetch_related('paniers__article', 'paniers__variante__couleur', 'paniers__variante__pointure')
        print(f"📊 Nombre de commandes confirmées avec paniers: {commandes.count()}")
        all_articles_data = []


        for commande in commandes:
            print(f"📋 Traitement de la commande: {commande.id_yz}")
            articles = commande.paniers.all()
            print(f"  📦 Nombre de paniers: {articles.count()}")

            if articles.count() == 0:
                print(f"  ⚠️ Aucun panier trouvé pour la commande {commande.id_yz}")
                continue

            for panier in articles:
                article = panier.article
                variante = panier.variante

                try:
                    import qrcode
                    qr_data = f"ART{article.id}_{variante.id if variante else 'NO_VAR'}"
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="black", back_color="white")
                    buffer = BytesIO()
                    qr_img.save(buffer, format='PNG')
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                except ImportError:
                    # Fallback si qrcode n'est pas install
                    qr_base64 = ""
                    print("Warning: qrcode library not installed, QR codes will not be generated")
                barcode_data = f"ART{article.reference}_{variante.reference_variante if variante else 'NO_VAR'}"
                code128 = barcode.get_barcode_class("code128")
                barcode_image = code128(barcode_data, writer=ImageWriter())
                buffer = BytesIO()
                barcode_image.write(buffer)
                barcode_base64 = base64.b64encode(buffer.getvalue()).decode()

                prix_unitaire = panier.sous_total / panier.quantite if panier.quantite > 0 else 0
                article_data = {
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference,
                    'prix': float(prix_unitaire),
                    'quantite': panier.quantite,
                    'couleur': variante.couleur.nom if variante and variante.couleur else "Standard",
                    'pointure': variante.pointure.pointure if variante and variante.pointure else "Standard",
                    'qr_image': qr_base64,
                    'barcode_image': barcode_base64,
                    'commande_id': commande.id_yz
                }
                all_articles_data.append(article_data)
        print(f"📦 Nombre total d'articles: {len(all_articles_data)}")
        if not all_articles_data:
            return JsonResponse({'error': 'Aucun article trouvé dans les commandes confirmées'}, status=404)
        html_content = render_to_string('Superpreparation/partials/_etiquettes_articles.html', {
            'articles': all_articles_data,
            'commande': {
                'id_yz': 'MULTIPLE',
                'client_nom': 'Toutes les commandes confirmées'
            },
            'format_type': format_type
        })

        return JsonResponse({
            'success': True,
            'html': html_content,
            'articles': all_articles_data,
            'format_type': format_type,
            'total_articles': len(all_articles_data)
        })
    except Exception as e:
        import traceback
        print(f"Erreur dans api_etiquettes_articles_multiple: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des étiquettes multiples: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def api_ticket_commande_multiple(request):
    """
    API pour récupérer le contenu HTML des tickets de commande multiples
    Utilise la fonction api_ticket_commande existante pour éviter la duplication de code
    """
    print("🚀 === API TICKET COMMANDE MULTIPLE DÉMARRÉE ===")
    print(f"📡 Méthode HTTP: {request.method}")
    print(f"📡 URL: {request.path}")
    print(f"📡 Paramètres GET: {dict(request.GET)}")

    try:
     # Vérifier si c'est pour l'impression directe
        direct_print = request.GET.get('direct_print', 'false').lower() == 'true'
        print(f"🖨️ Impression directe: {direct_print}")
        
        # Récupérer les IDs des commandes sélectionnées
        selected_ids = request.GET.get('selected_ids', '')
        print(f"📋 Paramètre selected_ids reçu: '{selected_ids}' (type: {type(selected_ids)})")
        
        # Construire le filtre de base
        base_filter = {
            'etats__enum_etat__libelle': 'Confirmée',
            'paniers__isnull': False
        }
        print(f"🔧 Filtre de base: {base_filter}")
        
        if selected_ids:
            print(f"🔍 Traitement de la sélection: '{selected_ids}'")
            try:
                commande_ids = [int(id.strip()) for id in selected_ids.split(',') if id.strip().isdigit()]
                print(f"🔍 IDs parsés: {commande_ids}")
                if commande_ids:
                    base_filter['id__in'] = commande_ids
                    print(f"✅ Filtrage par {len(commande_ids)} commandes sélectionnées: {commande_ids}")
                else:
                    print("⚠️ Aucun ID valide trouvé dans selected_ids")
            except (ValueError, AttributeError) as e:
                print(f"❌ Erreur lors du parsing des IDs: {e}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
        else:
            print("🔍 Aucune sélection spécifique - impression de toutes les commandes confirmées")
        
        print(f"🔍 Filtre final appliqué: {base_filter}")
        print("🔍 Exécution de la requête de base de données...")

        # Récupérer les commandes selon le filtre
        commandes = Commande.objects.filter(**base_filter).distinct()
        print(f"📊 Nombre de commandes confirmées avec paniers: {commandes.count()}")

        if not commandes.exists():
            return JsonResponse({'error': 'Aucune commande confirmée trouvée'}, status=404)

        # Extraire les IDs YZ des commandes
        commande_ids_yz = [str(commande.id_yz) for commande in commandes]
        print(f"🔍 IDs YZ des commandes: {commande_ids_yz}")

        # Créer une nouvelle requête simulée pour api_ticket_commande
        class MockRequest:
            def __init__(self, ids_string, user):
                self.GET = {'ids': ids_string}
                self.user = user
        
        # Appeler la fonction api_ticket_commande existante
        mock_request = MockRequest(','.join(commande_ids_yz), request.user)
        print(f"🔄 Appel de api_ticket_commande avec IDs: {','.join(commande_ids_yz)}")
        
        response = api_ticket_commande(mock_request)
        
        # Vérifier si la réponse est un JsonResponse
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content.decode('utf-8'))
            
            if data.get('success'):
                print(f"✅ {len(commande_ids_yz)} tickets générés avec succès via api_ticket_commande")
                
                # Modifier le HTML si c'est pour l'impression directe
                if direct_print:
                    import re
                    html_content = data['html']
                    # Supprimer les checkboxes
                    html_content = re.sub(r'<input[^>]*class="[^"]*ticket-checkbox[^"]*"[^>]*>', '', html_content)
                    # Ajuster l'affichage des badges
                    html_content = html_content.replace('class="articles-count-badge"', 'class="articles-count-badge" style="display: inline-block !important;"')
                    data['html'] = html_content
                
                return JsonResponse({
                    'success': True,
                    'html': data['html'],
                    'commandes': data['commandes']
                })
            else:
                print(f"❌ Erreur dans api_ticket_commande: {data.get('error')}")
                return JsonResponse({
                    'success': False,
                    'error': f"Erreur lors de la génération des tickets: {data.get('error')}"
                }, status=500)
        else:
            # Si ce n'est pas un JsonResponse, retourner directement
            return response
            
    except Exception as e:
        print(f"❌ Erreur dans api_ticket_commande_multiple: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f"Erreur lors de la génération des tickets multiples: {str(e)}"
        }, status=500)

@superviseur_preparation_required
@transaction.atomic
def api_finaliser_preparation(request, commande_id):
    """API pour finaliser la préparation d'une commande (changer l'état vers "Préparée")
    Seul le superviseur peut finaliser la préparation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        # Récupérer la commande
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que l'opérateur est bien un superviseur
        operateur = request.user.profil_operateur
        if not operateur or operateur.type_operateur != 'SUPERVISEUR_PREPARATION':
            return JsonResponse({
                'success': False, 
                'error': 'Seuls les superviseurs de préparation peuvent finaliser la préparation'
            }, status=403)
        
        # Vérifier que la commande est dans l'état "Emballée"
        etat_actuel = commande.etat_actuel
        if not etat_actuel or etat_actuel.enum_etat.libelle != 'Emballée':
            return JsonResponse({
                'success': False, 
                'error': 'La commande doit être dans l\'état "Emballée" pour être finalisée'
            }, status=400)
        
        # Récupérer l'état "Préparée"
        try:
            etat_preparee = EnumEtatCmd.objects.get(libelle='Préparée')
        except EnumEtatCmd.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'L\'état "Préparée" n\'existe pas dans le système'
            }, status=500)
        
        # Fermer l'état actuel (Emballée)
        etat_actuel.date_fin = timezone.now()
        etat_actuel.save()
        
        # Créer le nouvel état (Préparée)
        nouvel_etat = EtatCommande.objects.create(
            commande=commande,
            enum_etat=etat_preparee,
            operateur=operateur,
            date_debut=timezone.now(),
            date_fin=None  # État actif
        )
        
        # Créer une opération pour tracer l'action
        Operation.objects.create(
            commande=commande,
            type_operation='FINALISATION_PREPARATION',
            operateur=operateur,
            date_operation=timezone.now(),
            description=f'Préparation finalisée par le superviseur {operateur.nom} {operateur.prenom}'
        )
        
        print(f"✅ Préparation finalisée pour la commande {commande.id_yz} par {operateur.nom}")
        
        return JsonResponse({
            'success': True,
            'message': f'La préparation de la commande {commande.id_yz} a été finalisée avec succès',
            'nouvel_etat': 'Préparée',
            'operateur': f'{operateur.nom} {operateur.prenom}',
            'date_finalisation': timezone.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Commande non trouvée'
        }, status=404)
    except Exception as e:
        print(f"Erreur lors de la finalisation de la préparation: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Erreur lors de la finalisation: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def export_commandes_envoi_excel(request, envoi_id):
    """Exporter les commandes préparées d'un envoi en fichier Excel"""
    from django.http import HttpResponse
    from django.utils import timezone

    try:
        print(f"🔍 DEBUG - Export Excel pour envoi ID: {envoi_id}")
        
        # Récupérer l'envoi
        envoi = Envoi.objects.select_related('region').get(id=envoi_id)
        print(f"🔍 DEBUG - Envoi trouvé: {envoi.numero_envoi}, Région: {envoi.region.nom_region}")
        
        # Importer openpyxl après avoir vérifié l'envoi
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            print("🔍 DEBUG - Imports openpyxl réussis")
        except ImportError as import_error:
            print(f"🚫 ERREUR - Import openpyxl échoué: {import_error}")
            return JsonResponse({
                'success': False,
                'error': f'Erreur d\'import openpyxl: {import_error}'
            }, status=500)
        
        # Récupérer les commandes associées à cet envoi. Si aucune n'est encore liée,
        # fallback: prendre les commandes "Préparée" de la région de l'envoi.
        commandes = (
            Commande.objects.filter(envoi=envoi)
            .select_related('client', 'ville', 'ville__region')
            .prefetch_related(
                'paniers__article',
                'paniers__variante',
                'paniers__variante__couleur',
                'paniers__variante__pointure',
            )
            .distinct()
        )

        if not commandes.exists():
            print("🔎 Aucun lien direct commande→envoi. Fallback sur TOUTES les commandes de la région.")
            commandes = (
                Commande.objects.filter(
                    ville__region=envoi.region,
                )
                .select_related('client', 'ville', 'ville__region')
                .prefetch_related(
                    'paniers__article',
                    'paniers__variante',
                    'paniers__variante__couleur',
                    'paniers__variante__pointure',
                )
                .distinct()
            )
        
        print(f"🔍 DEBUG - Nombre de commandes trouvées: {commandes.count()}")
        
        # Test: Créer un workbook simple d'abord
        try:
            wb = openpyxl.Workbook()
            print("🔍 DEBUG - Workbook créé avec succès")
            ws = wb.active
            ws.title = f"Envoi_{envoi.numero_envoi}"[:31]  # Limiter à 31 caractères
            print(f"🔍 DEBUG - Worksheet configuré: {ws.title}")
        except Exception as wb_error:
            print(f"🚫 ERREUR - Création workbook échouée: {wb_error}")
            raise wb_error
        
        # TEST SIMPLE: Ajoutons juste quelques données de base
        try:
            # En-tête simple
            ws['A1'] = f"EXPORT COMMANDES - ENVOI {envoi.numero_envoi}"
            ws['A2'] = f"Région: {envoi.region.nom_region}"
            ws['A3'] = f"Date: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            
            # En-têtes des colonnes
            headers = ['N° Commande', 'Client', 'Téléphone', 'Adresse', 'Ville', 'Région', 'Total', 'Panier']
            for col, header in enumerate(headers, 1):
                ws.cell(row=5, column=col, value=header)
            
            print(f"🔍 DEBUG - En-têtes ajoutés")
            
            # Données simplifiées des commandes
            row = 6
            for commande in commandes:
                try:
                    # Données de base
                    client_nom = (
                        f"{(commande.client.prenom or '').strip()} {(commande.client.nom or '').strip()}".strip()
                        if commande.client else "N/A"
                    )
                    adresse_livraison = commande.adresse or (commande.client.adresse if getattr(commande, 'client', None) else '') or ""
                    ville_nom = commande.ville.nom if commande.ville else "N/A"
                    region_nom = commande.ville.region.nom_region if getattr(commande, 'ville', None) and commande.ville.region else (
                        envoi.region.nom_region if envoi and envoi.region else "N/A"
                    )

                    # Détails du panier (items)
                    items_texts = []
                    for p in commande.paniers.all():
                        try:
                            article_nom = p.article.nom if p.article else "Article N/A"
                            variante_text = ""
                            if p.variante:
                                couleur = getattr(p.variante.couleur, 'nom', None)
                                pointure = getattr(p.variante.pointure, 'pointure', None)
                                details = [v for v in [couleur, pointure] if v]
                                if details:
                                    variante_text = f" ({' - '.join(details)})"
                            items_texts.append(f"{p.quantite}x {article_nom}{variante_text}")
                        except Exception as p_err:
                            print(f"⚠️ ERREUR panier commande {commande.id}: {p_err}")
                            continue
                    panier_str = "\n".join(items_texts) if items_texts else ""

                    # Ecrire la ligne
                    ws.cell(row=row, column=1, value=commande.num_cmd)
                    ws.cell(row=row, column=2, value=client_nom)
                    ws.cell(row=row, column=3, value=getattr(commande.client, 'numero_tel', '') if commande.client else '')
                    ws.cell(row=row, column=4, value=adresse_livraison)
                    ws.cell(row=row, column=5, value=ville_nom)
                    ws.cell(row=row, column=6, value=region_nom)
                    # Total commande (montant total des articles)
                    ws.cell(row=row, column=7, value=float(getattr(commande, 'total_cmd', 0) or 0))
                    panier_cell = ws.cell(row=row, column=8, value=panier_str)
                    panier_cell.alignment = Alignment(wrap_text=True, vertical='top')

                    row += 1

                except Exception as row_error:
                    print(f"🚫 ERREUR - Ligne commande {commande.id}: {row_error}")
                    continue
            
            print(f"🔍 DEBUG - {row-6} lignes de données ajoutées")
            
        except Exception as data_error:
            print(f"🚫 ERREUR - Ajout des données: {data_error}")
            raise data_error
        
        # Préparer la réponse HTTP
        try:
            print("🔍 DEBUG - Préparation de la réponse HTTP")
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="Envoi_{envoi.numero_envoi}_Commandes.xlsx"'
            print(f"🔍 DEBUG - Headers HTTP configurés")
            
            # Sauvegarder le workbook dans la réponse
            print("🔍 DEBUG - Sauvegarde du workbook...")
            wb.save(response)
            print("🔍 DEBUG - Workbook sauvegardé avec succès")
            
            return response
            
        except Exception as save_error:
            print(f"🚫 ERREUR - Sauvegarde échouée: {save_error}")
            raise save_error
        
    except Envoi.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Envoi non trouvé'}, status=404)
    except Exception as e:
        import traceback
        print(f"Erreur dans export_commandes_envoi_excel: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération du fichier Excel: {str(e)}'
        }, status=500)

@superviseur_preparation_required
def api_commande_info(request, commande_id):
    """API pour récupérer les informations détaillées d'une commande pour la modale"""
    try:
        # Récupérer la commande
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les informations détaillées de manière sécurisée
        try:
            etat_actuel = commande.etat_actuel
        except:
            etat_actuel = None
        try:
            etat_precedent = commande.etat_precedent
        except:
            etat_precedent = None
        try:
            etat_confirmation = commande.etat_confirmation
        except:
            etat_confirmation = None
            
        try:
            operations = commande.operations.all().order_by('-date_operation')
        except:
            operations = []
        
        # Récupérer les informations détaillées
        context = {
            'commande': commande,
            'etat_actuel': etat_actuel,
            'etat_precedent': etat_precedent,
            'etat_confirmation': etat_confirmation,
            'operations': operations,
        }
        
        # Rendre le template HTML pour les informations détaillées
        html_content = render_to_string('Superpreparation/partials/_commande_info_modal.html', context)
        
        return JsonResponse({
            'success': True,
            'html_content': html_content
        })
        
    except Exception as e:
        import traceback
        print(f"Erreur dans api_commande_info: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du chargement des informations: {str(e)}'
        }, status=500)

""""
Views pour la gestion des stocks
"""
@superviseur_preparation_required
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
            
            # Rendre les templates partiels pour AJAX - CORRIGÉ pour les ARTICLES
            html_cards_body = render_to_string('Superpreparation/partials/_articles_cards_body.html', {
                'page_obj': page_obj
            }, request=request)
            print(f"📄 Cards body length: {len(html_cards_body)}")
            
            html_table_body = render_to_string('Superpreparation/partials/_articles_table_body.html', {
                'page_obj': page_obj
            }, request=request)
            print(f"📄 Table body length: {len(html_table_body)}")
            
            # Vue grille pour ARTICLES (pas variantes)
            html_grid_body = render_to_string('Superpreparation/partials/_articles_grid_body.html', {
                'page_obj': page_obj
            }, request=request)
            
            html_pagination = render_to_string('Superpreparation/partials/_articles_pagination.html', {
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
            
            html_pagination_info = render_to_string('Superpreparation/partials/_articles_pagination_info.html', {
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
    return render(request, 'Superpreparation/liste_articles.html', context)

@superviseur_preparation_required
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
    previous_page = request.META.get('HTTP_REFERER', reverse('Superpreparation:liste_articles'))
    
    context = {
        'article': article,
        'articles_similaires': articles_similaires,
        'previous_page': previous_page,
        'stats_variantes': stats_variantes,
        'tableau_croise': tableau_croise,
        'pointures_uniques': pointures_uniques,
        'couleurs_uniques': couleurs_uniques,
    }
    return render(request, 'Superpreparation/Detail_article.html', context)

@superviseur_preparation_required
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
                error_message = "Un article avec le même nom, couleur et pointure existe déjà."
                
                # Si c'est une requête AJAX, retourner une erreur JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=400)
                
                # Sinon, afficher le message d'erreur normalement
                messages.error(request, error_message)
                return render(request, 'Superpreparation/creer_article.html', {
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
                        error_message = "Le numéro du modèle doit être supérieur à 0."
                        
                        # Si c'est une requête AJAX, retourner une erreur JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': error_message
                            }, status=400)
                        
                        # Sinon, afficher le message d'erreur normalement
                        messages.error(request, error_message)
                        return render(request, 'Superpreparation/creer_article.html', {
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                    
                    # Vérifier si le modèle existe déjà
                    if Article.objects.filter(modele=modele_int).exists():
                        error_message = f"Le modèle {modele_int} est déjà utilisé par un autre article."
                        
                        # Si c'est une requête AJAX, retourner une erreur JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': error_message
                            }, status=400)
                        
                        # Sinon, afficher le message d'erreur normalement
                        messages.error(request, error_message)
                        return render(request, 'Superpreparation/creer_article.html', {
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                except ValueError:
                    error_message = "Le numéro du modèle doit être un nombre entier valide."
                    
                    # Si c'est une requête AJAX, retourner une erreur JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_message
                        }, status=400)
                    
                    # Sinon, afficher le message d'erreur normalement
                    messages.error(request, error_message)
                    return render(request, 'Superpreparation/creer_article.html', {
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })

            # Valider et convertir le prix
            prix_str = request.POST.get('prix_unitaire', '').strip().replace(',', '.')
            if not prix_str:
                error_message = "Le prix unitaire est obligatoire."
                
                # Si c'est une requête AJAX, retourner une erreur JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=400)
                
                # Sinon, afficher le message d'erreur normalement
                messages.error(request, error_message)
                return render(request, 'Superpreparation/creer_article.html', {
                    'form_data': request.POST,
                    'categories': categories,
                    'genres': genres,
                    'couleurs': couleurs,
                    'pointures': pointures
                })
            
            try:
                prix_unitaire = float(prix_str)
                if prix_unitaire <= 0:
                    error_message = "Le prix unitaire doit être supérieur à 0."
                    
                    # Si c'est une requête AJAX, retourner une erreur JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_message
                        }, status=400)
                    
                    # Sinon, afficher le message d'erreur normalement
                    messages.error(request, error_message)
                    return render(request, 'Superpreparation/creer_article.html', {
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })
            except ValueError:
                error_message = "Le prix unitaire doit être un nombre valide."
                
                # Si c'est une requête AJAX, retourner une erreur JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=400)
                
                # Sinon, afficher le message d'erreur normalement
                messages.error(request, error_message)
                return render(request, 'Superpreparation/creer_article.html', {
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
            
            return redirect('Superpreparation:liste_articles')
            
        except Exception as e:
            error_message = f"Une erreur est survenue lors de la création de l'article : {str(e)}"
            
            # Si c'est une requête AJAX, retourner une erreur JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_message
                }, status=500)
            
            # Sinon, afficher le message d'erreur normalement
            messages.error(request, error_message)
            return render(request, 'Superpreparation/creer_article.html', {
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
    
    return render(request,'Superpreparation/creer_article.html',context)

@superviseur_preparation_required
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
                return render(request, 'Superpreparation/modifier_article.html', {
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
                        return render(request, 'Superpreparation/modifier_article.html', {
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
                        return render(request, 'Superpreparation/modifier_article.html', {
                            'article': article, 
                            'form_data': request.POST,
                            'categories': categories,
                            'genres': genres,
                            'couleurs': couleurs,
                            'pointures': pointures
                        })
                except ValueError:
                    messages.error(request, "Le numéro du modèle doit être un nombre entier valide.")
                    return render(request, 'Superpreparation/modifier_article.html', {
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
                return render(request, 'Superpreparation/modifier_article.html', {
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
                    return render(request, 'Superpreparation/modifier_article.html', {
                        'article': article, 
                        'form_data': request.POST,
                        'categories': categories,
                        'genres': genres,
                        'couleurs': couleurs,
                        'pointures': pointures
                    })
            except ValueError:
                messages.error(request, "Le prix unitaire doit être un nombre valide.")
                return render(request, 'Superpreparation/modifier_article.html', {
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
                    'redirect_url': reverse('Superpreparation:detail_article', args=[article.id])
                })
                
            messages.success(request, message_succes)
            return redirect('Superpreparation:detail_article', id=article.id)
            
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
            
            return render(request, 'Superpreparation/modifier_article.html', {
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
    return render(request, 'Superpreparation/modifier_article.html', context)

@superviseur_preparation_required
@require_POST
def supprimer_article(request, id):
    """Supprimer un article (méthode POST requise)"""
    article = get_object_or_404(Article, id=id)
    try:
        article.delete()
        messages.success(request, f"L'article '{article.nom}' a été supprimé avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression de l'article : {e}")
    return redirect('Superpreparation:liste_articles')

@require_POST
@superviseur_preparation_required
def supprimer_articles_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun article sélectionné pour la suppression.")
        return redirect('Superpreparation:liste_articles')

    try:
        count = Article.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} article(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('Superpreparation:liste_articles')

@login_required
@csrf_exempt
def supprimer_variantes_masse(request):
    """Suppression en masse des variantes d'articles"""
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune variante d'article sélectionnée pour la suppression.")
        return redirect('Superpreparation:liste_variantes')

    try:
        count = VarianteArticle.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} variante(s) d'article(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('Superpreparation:liste_variantes')

@superviseur_preparation_required
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
    return render(request, 'Superpreparation/categorie.html', context)

@superviseur_preparation_required
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
    return render(request, 'Superpreparation/stock_faible.html', context)

@superviseur_preparation_required
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
    return render(request, 'Superpreparation/rupture_stock.html', context)

@superviseur_preparation_required
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
        
        # Rendre les templates partiels pour AJAX - Utiliser les templates Superpreparation
        html_table_body = render_to_string('Superpreparation/partials/_promotions_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('Superpreparation/partials/_promotions_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre': filtre,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('Superpreparation/partials/_promotions_pagination_info.html', {
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
    }
    return render(request, 'Superpreparation/Liste_promotion_article.html', context)

@superviseur_preparation_required
def detail_promotion(request, id):
    """Détail d'une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    # Articles en promotion
    articles = promotion.articles.all().order_by('nom')
    
    context = {
        'promotion': promotion,
        'articles': articles
    }
    return render(request, 'Superpreparation/detail_promotion.html', context)

@superviseur_preparation_required
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
                
                return redirect('Superpreparation:detail_promotion', id=promotion.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la promotion : {str(e)}")
                # Renommer form en form_promotion pour correspondre au template
                return render(request, 'Superpreparation/Liste_promotion_article.html', {
                    'form_promotion': form,
                    'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
                })
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
            # Renommer form en form_promotion pour correspondre au template
            return render(request, 'Superpreparation/Liste_promotion_article.html', {
                'form_promotion': form,
                'page_obj': Promotion.objects.all().order_by('-date_creation')[:10]
            })
    else:
        # Cette partie ne devrait pas être appelée directement, mais au cas où
        form = PromotionForm()
        return redirect('Superpreparation:liste_promotions')

@superviseur_preparation_required
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
            
            return redirect('Superpreparation:detail_promotion', id=promotion.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = PromotionForm(instance=promotion)
    
    context = {
        'promotion': promotion,
        'form': form,
    }
    return render(request, 'Superpreparation/modifier_promotion.html', context)

@superviseur_preparation_required
def supprimer_promotion(request, id):
    """Supprimer une promotion"""
    promotion = get_object_or_404(Promotion, id=id)
    
    if request.method == 'POST':
        nom = promotion.nom
        promotion.delete()
        messages.success(request, f"La promotion '{nom}' a été supprimée avec succès.")
        return redirect('article:liste_promotions')
    
    return render(request, 'Superpreparation/supprimer_promotion.html', {'promotion': promotion})

@superviseur_preparation_required
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
    return redirect('Superpreparation:liste_promotions')

@superviseur_preparation_required
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
    return redirect('Superpreparation:detail_article', id=article.id)

@superviseur_preparation_required
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
    
    return redirect('Superpreparation:detail_article', id=article.id)

@superviseur_preparation_required
@require_POST
def appliquer_liquidation_prix_db(request, id):
    """Applique la liquidation en utilisant le Prix_liquidation de la base de données"""
    article = get_object_or_404(Article, id=id)
    now = timezone.now()
    
    # Vérifier si l'article a un prix de liquidation défini
    if not article.Prix_liquidation or article.Prix_liquidation <= 0:
        messages.error(request, "Aucun prix de liquidation défini pour cet article.")
        return redirect('Superpreparation:detail_article', id=article.id)
    
    try:
        # Désactiver l'upsell avant de mettre en liquidation
        upsell_was_active = article.isUpsell
        
        # Si l'article est en promotion, désactiver les promotions actives
        promotions_desactivees = False
        if article.has_promo_active:
            from article.models import Promotion
            promotions_actives = article.promotions.filter(
                active=True,
                date_debut__lte=now,
                date_fin__gte=now
            )
            for promotion in promotions_actives:
                promotion.active = False
                promotion.save()
                promotions_desactivees = True
        
        # Mettre l'article en liquidation
        article.phase = 'LIQUIDATION'
        # Appliquer le prix de liquidation défini en base
        article.prix_actuel = article.Prix_liquidation
        # L'upsell sera automatiquement désactivé par la méthode save()
        article.save()
        
        message = f"L'article a été mis en liquidation au prix de {article.Prix_liquidation} DH."
        if upsell_was_active:
            message += " L'upsell a été automatiquement désactivé."
        if promotions_desactivees:
            message += " Les promotions actives ont été annulées."
            
        messages.success(request, message)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'application de la liquidation : {str(e)}")
    
    return redirect('Superpreparation:detail_article', id=article.id)

@superviseur_preparation_required
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

@superviseur_preparation_required
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
    return redirect('Superpreparation:liste_promotions')


@superviseur_preparation_required
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
        html_cards_body = render_to_string('Superpreparation/partials/variantes_articles_cards_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_table_body = render_to_string('Superpreparation/partials/variantes_articles_table_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        # Vue grille pour variantes
        html_grid_body = render_to_string('Superpreparation/partials/variantes_articles_grid_body.html', {
            'page_obj': page_obj
        }, request=request)
        
        html_pagination = render_to_string('Superpreparation/partials/_articles_pagination.html', {
            'page_obj': page_obj,
            'search': search,
            'filtre_phase': filtre_phase,
            'filtre_promotion': filtre_promotion,
            'filtre_stock': filtre_stock,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('Superpreparation/partials/_articles_pagination_info.html', {
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
    return render(request, 'Superpreparation/Liste_variante_article.html', context)

@superviseur_preparation_required
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

@superviseur_preparation_required
@csrf_exempt
def supprimer_variante(request, id):
    """Supprimer une variante d'article"""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
        messages.error(request, 'Méthode non autorisée')
        return redirect('Superpreparation:liste_variantes')
    
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
        return redirect('Superpreparation:liste_variantes', id=article.id)
        
    except VarianteArticle.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Variante non trouvée.'}, content_type='application/json')
        messages.error(request, 'Variante non trouvée.')
        return redirect('Superpreparation:liste_variantes')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'Erreur lors de la suppression : {str(e)}'}, content_type='application/json')
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('Superpreparation:liste_variantes')

@superviseur_preparation_required
def gestion_couleurs_pointures(request):
    """Page de gestion des couleurs, pointures, catégories et genres"""
    from django.core.paginator import Paginator, EmptyPage, InvalidPage
    from article.models import Couleur, Pointure, Categorie, Genre
    
    # Paramètres de pagination
    items_per_page = request.GET.get('items_per_page', '10')
    try:
        items_per_page = int(items_per_page)
    except ValueError:
        items_per_page = 10
    
    # Recherche pour les couleurs
    search_couleur = request.GET.get('search_couleur', '')
    couleurs = Couleur.objects.all()
    if search_couleur:
        couleurs = couleurs.filter(
            Q(nom__icontains=search_couleur) |
            Q(description__icontains=search_couleur) |
            Q(code_hex__icontains=search_couleur)
        )
    couleurs = couleurs.order_by('nom')
    
    # Pagination pour les couleurs
    paginator_couleurs = Paginator(couleurs, items_per_page)
    page_couleur = request.GET.get('page_couleur', 1)
    try:
        couleurs = paginator_couleurs.page(page_couleur)
    except (ValueError, EmptyPage, InvalidPage):
        couleurs = paginator_couleurs.page(1)
    
    # Recherche pour les pointures
    search_pointure = request.GET.get('search_pointure', '')
    pointures = Pointure.objects.all()
    if search_pointure:
        pointures = pointures.filter(
            Q(pointure__icontains=search_pointure) |
            Q(description__icontains=search_pointure)
        )
    pointures = pointures.order_by('ordre', 'pointure')
    
    # Pagination pour les pointures
    paginator_pointures = Paginator(pointures, items_per_page)
    page_pointure = request.GET.get('page_pointure', 1)
    try:
        pointures = paginator_pointures.page(page_pointure)
    except (ValueError, EmptyPage, InvalidPage):
        pointures = paginator_pointures.page(1)
    
    # Recherche pour les catégories
    search_categorie = request.GET.get('search_categorie', '')
    categories = Categorie.objects.all()
    if search_categorie:
        categories = categories.filter(
            Q(nom__icontains=search_categorie) |
            Q(description__icontains=search_categorie)
        )
    categories = categories.order_by('nom')
    
    # Pagination pour les catégories
    paginator_categories = Paginator(categories, items_per_page)
    page_categorie = request.GET.get('page_categorie', 1)
    try:
        categories = paginator_categories.page(page_categorie)
    except (ValueError, EmptyPage, InvalidPage):
        categories = paginator_categories.page(1)
    
    # Recherche pour les genres
    search_genre = request.GET.get('search_genre', '')
    genres = Genre.objects.all()
    if search_genre:
        genres = genres.filter(
            Q(nom__icontains=search_genre) |
            Q(description__icontains=search_genre)
        )
    genres = genres.order_by('nom')
    
    # Pagination pour les genres
    paginator_genres = Paginator(genres, items_per_page)
    page_genre = request.GET.get('page_genre', 1)
    try:
        genres = paginator_genres.page(page_genre)
    except (ValueError, EmptyPage, InvalidPage):
        genres = paginator_genres.page(1)
    
    context = {
        'couleurs': couleurs,
        'pointures': pointures,
        'categories': categories,
        'genres': genres,
        'couleurs_count': Couleur.objects.count(),
        'pointures_count': Pointure.objects.count(),
        'categories_count': Categorie.objects.count(),
        'genres_count': Genre.objects.count(),
        'search_couleur': search_couleur,
        'search_pointure': search_pointure,
        'search_categorie': search_categorie,
        'search_genre': search_genre,
        'items_per_page': str(items_per_page),
        'total_couleurs': paginator_couleurs.count,
        'total_pointures': paginator_pointures.count,
        'total_categories': paginator_categories.count,
        'total_genres': paginator_genres.count,
    }
    
    return render(request, 'Superpreparation/gestion_attribut.html', context)

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def supprimer_pointure(request, pointure_id):
    """Supprimer une pointure"""
    try:
        pointure = get_object_or_404(Pointure, id=pointure_id)
        nom_pointure = pointure.pointure
        pointure.delete()
        
        messages.success(request, f'Pointure "{nom_pointure}" supprimée avec succès.')
        return redirect('Superpreparation:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def supprimer_categorie(request, categorie_id):
    """Supprimer une catégorie"""
    try:
        categorie = get_object_or_404(Categorie, id=categorie_id)
        nom_categorie = categorie.nom
        categorie.delete()
        
        messages.success(request, f'Catégorie "{nom_categorie}" supprimée avec succès.')
        return redirect('Superpreparation:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
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
            return redirect('Superpreparation:gestion_couleurs_pointures')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
            return redirect('Superpreparation:gestion_couleurs_pointures')
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def supprimer_genre(request, genre_id):
    """Supprimer un genre"""
    try:
        genre = get_object_or_404(Genre, id=genre_id)
        nom_genre = genre.nom
        genre.delete()
        
        messages.success(request, f'Genre "{nom_genre}" supprimé avec succès.')
        return redirect('Superpreparation:gestion_couleurs_pointures')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
        return redirect('Superpreparation:gestion_couleurs_pointures')
    

@superviseur_preparation_required
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
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def diagnostiquer_compteur(request, commande_id):
    """
    Fonction pour diagnostiquer et corriger le compteur d'une commande
    """
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Diagnostiquer la situation actuelle
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        compteur_actuel = commande.compteur
        
        # Calculer la quantité totale d'articles upsell
        total_quantite_upsell = (
            articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
        )
        
        print(f"🔍 DIAGNOSTIC Commande {commande.id_yz}:")
        print(f"📊 Compteur actuel: {compteur_actuel}")
        print(f"📦 Articles upsell trouvés: {articles_upsell.count()}")
        print(f"🔢 Quantité totale d'articles upsell: {total_quantite_upsell}")
        
        if articles_upsell.exists():
            print("📋 Articles upsell dans la commande:")
            for panier in articles_upsell:
                print(
                    f"  - {panier.article.nom} (Qté: {panier.quantite}, ID: {panier.article.id}, isUpsell: {panier.article.isUpsell})"
                )
        
        # Déterminer le compteur correct selon la nouvelle logique :
        # 0-1 unités upsell → compteur = 0
        # 2+ unités upsell → compteur = total_quantite_upsell - 1
        if total_quantite_upsell >= 2:
            compteur_correct = total_quantite_upsell - 1
        else:
            compteur_correct = 0
        
        print(f"✅ Compteur correct: {compteur_correct}")
        print(
            "📖 Logique: 0-1 unités upsell → compteur=0 | 2+ unités upsell → compteur=total_quantité-1"
        )
        
        # Corriger si nécessaire
        if compteur_actuel != compteur_correct:
            commande.compteur = compteur_correct
            commande.save()
            print(f"🔧 Compteur corrigé: {compteur_actuel} → {compteur_correct}")
            
            return JsonResponse({
                'success': True,
                'message': f'Compteur corrigé: {compteur_actuel} → {compteur_correct}',
                'compteur_actuel': compteur_correct,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
        else:
            print("✅ Compteur déjà correct")
            return JsonResponse({
                'success': True,
                'message': 'Compteur déjà correct',
                'compteur_actuel': compteur_actuel,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
            
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du diagnostic: {str(e)}'
        }, status=500)

@superviseur_preparation_required
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
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def diagnostiquer_compteur(request, commande_id):
    """
    Fonction pour diagnostiquer et corriger le compteur d'une commande
    """
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Diagnostiquer la situation actuelle
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        compteur_actuel = commande.compteur
        
        # Calculer la quantité totale d'articles upsell
        total_quantite_upsell = (
            articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
        )
        
        print(f"🔍 DIAGNOSTIC Commande {commande.id_yz}:")
        print(f"📊 Compteur actuel: {compteur_actuel}")
        print(f"📦 Articles upsell trouvés: {articles_upsell.count()}")
        print(f"🔢 Quantité totale d'articles upsell: {total_quantite_upsell}")
        
        if articles_upsell.exists():
            print("📋 Articles upsell dans la commande:")
            for panier in articles_upsell:
                print(
                    f"  - {panier.article.nom} (Qté: {panier.quantite}, ID: {panier.article.id}, isUpsell: {panier.article.isUpsell})"
                )
        
        # Déterminer le compteur correct selon la nouvelle logique :
        # 0-1 unités upsell → compteur = 0
        # 2+ unités upsell → compteur = total_quantite_upsell - 1
        if total_quantite_upsell >= 2:
            compteur_correct = total_quantite_upsell - 1
        else:
            compteur_correct = 0
        
        print(f"✅ Compteur correct: {compteur_correct}")
        print(
            "📖 Logique: 0-1 unités upsell → compteur=0 | 2+ unités upsell → compteur=total_quantité-1"
        )
        
        # Corriger si nécessaire
        if compteur_actuel != compteur_correct:
            commande.compteur = compteur_correct
            commande.save()
            print(f"🔧 Compteur corrigé: {compteur_actuel} → {compteur_correct}")
            
            return JsonResponse({
                'success': True,
                'message': f'Compteur corrigé: {compteur_actuel} → {compteur_correct}',
                'compteur_actuel': compteur_correct,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
        else:
            print("✅ Compteur déjà correct")
            return JsonResponse({
                'success': True,
                'message': 'Compteur déjà correct',
                'compteur_actuel': compteur_actuel,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
            
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du diagnostic: {str(e)}'
        }, status=500)

@superviseur_preparation_required
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
    
    return redirect('Superpreparation:gestion_couleurs_pointures')

@superviseur_preparation_required
def diagnostiquer_compteur(request, commande_id):
    """
    Fonction pour diagnostiquer et corriger le compteur d'une commande
    """
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Diagnostiquer la situation actuelle
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        compteur_actuel = commande.compteur
        
        # Calculer la quantité totale d'articles upsell
        total_quantite_upsell = (
            articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
        )
        
        print(f"🔍 DIAGNOSTIC Commande {commande.id_yz}:")
        print(f"📊 Compteur actuel: {compteur_actuel}")
        print(f"📦 Articles upsell trouvés: {articles_upsell.count()}")
        print(f"🔢 Quantité totale d'articles upsell: {total_quantite_upsell}")
        
        if articles_upsell.exists():
            print("📋 Articles upsell dans la commande:")
            for panier in articles_upsell:
                print(
                    f"  - {panier.article.nom} (Qté: {panier.quantite}, ID: {panier.article.id}, isUpsell: {panier.article.isUpsell})"
                )
        
        # Déterminer le compteur correct selon la nouvelle logique :
        # 0-1 unités upsell → compteur = 0
        # 2+ unités upsell → compteur = total_quantite_upsell - 1
        if total_quantite_upsell >= 2:
            compteur_correct = total_quantite_upsell - 1
        else:
            compteur_correct = 0
        
        print(f"✅ Compteur correct: {compteur_correct}")
        print(
            "📖 Logique: 0-1 unités upsell → compteur=0 | 2+ unités upsell → compteur=total_quantité-1"
        )
        
        # Corriger si nécessaire
        if compteur_actuel != compteur_correct:
            commande.compteur = compteur_correct
            commande.save()
            print(f"🔧 Compteur corrigé: {compteur_actuel} → {compteur_correct}")
            
            return JsonResponse({
                'success': True,
                'message': f'Compteur corrigé: {compteur_actuel} → {compteur_correct}',
                'compteur_actuel': compteur_correct,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
        else:
            print("✅ Compteur déjà correct")
            return JsonResponse({
                'success': True,
                'message': 'Compteur déjà correct',
                'compteur_actuel': compteur_actuel,
                'compteur_precedent': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
            
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du diagnostic: {str(e)}'
        }, status=500)



