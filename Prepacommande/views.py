from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q, Sum, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.core.paginator import Paginator

import json
from parametre.models import Operateur
from commande.models import Commande, EtatCommande, EnumEtatCmd, Panier
from django.urls import reverse

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
import csv

from article.models import Article, MouvementStock
from commande.models import Envoi
from .forms import ArticleForm, AjusterStockForm
from .utils import creer_mouvement_stock

# Décorateur pour gérer les erreurs AJAX
def handle_ajax_errors(view_func):
    def wrapper(request, *args, **kwargs):
        print(f"🔍 Décorateur handle_ajax_errors appelé pour {view_func.__name__}")
        try:
            result = view_func(request, *args, **kwargs)
            print(f"🔍 Fonction {view_func.__name__} terminée avec succès")
            return result
        except Exception as e:
            print(f"❌ Erreur globale dans {view_func.__name__}: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                print(f"🔍 Retour de réponse JSON pour erreur AJAX")
                return JsonResponse({"success": False, "error": f"Erreur serveur: {str(e)}"})
            
            # Sinon, laisser Django gérer l'erreur normalement
            print(f"🔍 Relance de l'exception pour gestion normale")
            raise
    return wrapper

# Create your views here.


@login_required
def home_view(request):
    """Page d'accueil avec statistiques pour les opérateurs de préparation"""
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Date de référence
    today = timezone.now().date()
    # Début de la semaine (lundi)
    start_of_week = today - timedelta(days=today.weekday())

    # Récupérer les états nécessaires
    try:
        etat_confirmee = EnumEtatCmd.objects.get(libelle__iexact="Confirmée")
        etat_en_preparation = EnumEtatCmd.objects.get(libelle__iexact="En préparation")
        etat_preparee = EnumEtatCmd.objects.get(libelle__iexact="Préparée")
    except EnumEtatCmd.DoesNotExist as e:
        messages.error(request, f"État manquant dans le système: {str(e)}")
        return redirect("login")

    # 1. Commandes à préparer (à imprimer et affectées à cet opérateur)
    commandes_a_preparer = (
        Commande.objects.filter(
            etats__enum_etat__libelle="En préparation",
        etats__operateur=operateur_profile,
            etats__date_fin__isnull=True,
        )
        .distinct()
        .count()
    )
    
    # 2. Commandes préparées aujourd'hui par cet opérateur
    commandes_preparees = (
        EtatCommande.objects.filter(
            enum_etat__libelle="Préparée",
        date_debut__date=today,
            operateur=operateur_profile,
        )
        .distinct()
        .count()
    )

    # 3. Commandes en cours de préparation
    commandes_en_cours = (
        Commande.objects.filter(
        etats__enum_etat=etat_en_preparation,
        etats__date_fin__isnull=True,
            etats__operateur=operateur_profile,
        )
        .distinct()
        .count()
    )

    # 4. Performance de l'opérateur aujourd'hui
    ma_performance = (
        EtatCommande.objects.filter(
            enum_etat=etat_preparee, date_debut__date=today, operateur=operateur_profile
        )
        .distinct()
        .count()
    )

    # === Calculs supplémentaires pour le tableau de bord ===
    # Commandes préparées aujourd'hui (toutes)
    commandes_preparees_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation, date_fin__date=today
    ).count()

    # Commandes préparées cette semaine (toutes)
    commandes_preparees_week = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date__gte=start_of_week,
        date_fin__date__lte=today,
    ).count()

    # Commandes actuellement en préparation (toutes)
    commandes_en_preparation = Commande.objects.filter(
        etats__enum_etat=etat_en_preparation, etats__date_fin__isnull=True
    ).count()

    # Performance de l'opérateur aujourd'hui (commandes préparées par lui)
    ma_performance_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation, date_fin__date=today, operateur=operateur_profile
    ).count()

    # Valeur totale (DH) des commandes préparées aujourd'hui
    commandes_ids_today = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation, date_fin__date=today
    ).values_list("commande_id", flat=True)
    valeur_preparees_today = (
        Commande.objects.filter(id__in=commandes_ids_today).aggregate(
            total=Sum("total_cmd")
        )["total"]
        or 0
    )

    # Articles populaires (semaine en cours)
    commandes_ids_week = EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        date_fin__date__gte=start_of_week,
        date_fin__date__lte=today,
    ).values_list("commande_id", flat=True)
    articles_populaires = (
        Panier.objects.filter(commande_id__in=commandes_ids_week)
        .values("article__nom", "article__reference")
        .annotate(
            total_quantite=Sum("quantite"),
            total_commandes=Count("commande", distinct=True),
        )
        .order_by("-total_quantite")[:5]
    )

    # Activité récente (5 dernières préparations de l'opérateur)
    activite_recente = (
        EtatCommande.objects.filter(
        enum_etat=etat_en_preparation,
        operateur=operateur_profile,
            date_fin__isnull=False,
        )
        .select_related("commande", "commande__client")
        .order_by("-date_fin")[:5]
    )

    # Préparer les statistiques
    stats = {
        "commandes_a_preparer": commandes_a_preparer,
        "commandes_preparees": commandes_preparees,
        "commandes_en_cours": commandes_en_cours,
        "ma_performance": ma_performance,
        # Ajout des nouvelles statistiques
        "commandes_preparees_today": commandes_preparees_today,
        "commandes_preparees_week": commandes_preparees_week,
        "commandes_en_preparation": commandes_en_preparation,
        "ma_performance_today": ma_performance_today,
        "valeur_preparees_today": valeur_preparees_today,
        "articles_populaires": articles_populaires,
        "activite_recente": activite_recente,
    }

    context = {
        "page_title": "Tableau de Bord",
        "page_subtitle": "Interface Opérateur de Préparation",
        "profile": operateur_profile,
        "stats": stats,
        "total_commandes": commandes_a_preparer,  # Ajout du total des commandes à préparer
    }
    return render(request, "composant_generale/operatPrepa/home.html", context)


@login_required
def liste_prepa(request):
    """Liste des commandes à préparer pour les opérateurs de préparation"""
    from commande.models import Operation
    from django.core.paginator import Paginator
    
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(
                request,
                "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.",
            )
            return redirect("login")
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Récupérer les commandes dont l'état ACTUEL est "À imprimer" ou "En préparation" et qui sont affectées à cet opérateur
    # On cherche les commandes qui ont un état "À imprimer" ou "En préparation" actif (sans date_fin) avec cet opérateur
    from django.db.models import Q, Max
    
    # Définir le type de filtre en premier
    filter_type = request.GET.get("filter", "all")
    
    if filter_type == "livrees_partiellement":
        # Filtrer les commandes qui ont été livrées partiellement et sont maintenant en préparation
        commandes_affectees = []
        commandes_base = (
            Commande.objects.filter(
                Q(etats__enum_etat__libelle="À imprimer")
                | Q(etats__enum_etat__libelle="En préparation")
                | Q(etats__enum_etat__libelle="Collectée")
                | Q(etats__enum_etat__libelle="Emballée"),
            etats__operateur=operateur_profile,
                etats__date_fin__isnull=True,
            )
            .select_related("client", "ville", "ville__region")
            .prefetch_related("paniers__article", "etats")
            .distinct()
        )
        
        for commande in commandes_base:
            etats_commande = commande.etats.all().order_by("date_debut")
            etat_prepa_actuel = None
            
            # Trouver l'état actuel de préparation
            for etat in etats_commande:
                if (
                    etat.enum_etat.libelle
                    in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                    and not etat.date_fin
                ):
                    etat_prepa_actuel = etat
                    break
            
            if etat_prepa_actuel:
                # Vérifier si la commande a un historique de livraison partielle
                has_partially_delivered_history = False
                for etat in etats_commande:
                    if (
                        etat.enum_etat.libelle == "Livrée Partiellement"
                        and etat.date_fin
                        and etat.date_fin < etat_prepa_actuel.date_debut
                    ):
                        has_partially_delivered_history = True
                        break
                
                if has_partially_delivered_history:
                    commandes_affectees.append(commande)
    elif filter_type == "renvoyees_logistique":
        # Pour les commandes renvoyées par la logistique, ne pas exclure les états problématiques
        # car on veut inclure les commandes avec opération de renvoi même si elles ont des états ultérieurs
        commandes_affectees = (
            Commande.objects.filter(
                Q(etats__enum_etat__libelle="À imprimer")
                | Q(etats__enum_etat__libelle="En préparation")
                | Q(etats__enum_etat__libelle="Collectée")
                | Q(etats__enum_etat__libelle="Emballée"),
            etats__operateur=operateur_profile,
                etats__date_fin__isnull=True,  # État actif (en cours)
            )
            .select_related("client", "ville", "ville__region")
            .prefetch_related("paniers__article", "etats")
            .distinct()
        )
    elif filter_type == "retournees":
        # Obsolète: rediriger vers la page dédiée
        return redirect("Prepacommande:commandes_retournees")

    elif filter_type == "affectees_supervision":
        # Filtrer les commandes affectées par les superviseurs de préparation
        commandes_affectees = []
        commandes_base = (
            Commande.objects.filter(
                Q(etats__enum_etat__libelle="À imprimer")
                | Q(etats__enum_etat__libelle="En préparation")
                | Q(etats__enum_etat__libelle="Collectée")
                | Q(etats__enum_etat__libelle="Emballée"),
                etats__operateur=operateur_profile,
                etats__date_fin__isnull=True,
            )
            .select_related("client", "ville", "ville__region")
            .prefetch_related("paniers__article", "etats")
            .distinct()
        )

        for commande in commandes_base:
            etats_commande = commande.etats.all().order_by("date_debut")
            etat_prepa_actuel = None

            # Trouver l'état actuel de préparation
            for etat in etats_commande:
                if (
                    etat.enum_etat.libelle
                    in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                    and not etat.date_fin
                ):
                    etat_prepa_actuel = etat
                    break

            if etat_prepa_actuel:
                # Vérifier s'il y a des états ultérieurs problématiques
                a_etats_ultérieurs_problematiques = False
                for etat in etats_commande:
                    if (
                        etat.date_debut > etat_prepa_actuel.date_debut
                        and etat.enum_etat.libelle
                        in [
                            "Livrée",
                            "Livrée Partiellement",
                            "Préparée",
                            "En cours de livraison",
                        ]
                    ):
                        a_etats_ultérieurs_problematiques = True
                        break
               
                # Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
                if commande.num_cmd and commande.num_cmd.startswith("RENVOI-"):
                    # Chercher la commande originale
                    num_cmd_original = commande.num_cmd.replace("RENVOI-", "")
                    commande_originale = Commande.objects.filter(
                        num_cmd=num_cmd_original,
                        etats__enum_etat__libelle="Livrée Partiellement",
                    ).first()

                    if commande_originale:
                        continue  # Exclure les commandes de renvoi livraison partielle

                # Vérifier l'historique pour renvoi depuis livraison
                has_return_from_delivery = False
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_prepa_actuel.date_debut:
                        if etat.enum_etat.libelle in [
                            "En cours de livraison",
                            "Livrée Partiellement",
                        ]:
                            has_return_from_delivery = True
                            break

                if not has_return_from_delivery:
                    # Vérifier si la commande a été affectée par un superviseur
                    # Chercher les opérations d'affectation par supervision
                    

                    if operation_affectation_supervision:
                        commandes_affectees.append(commande)
    else:  # filter_type == 'all'
        # Pour "Toutes les commandes", afficher toutes les commandes des 5 autres onglets
        commandes_affectees = []
        commandes_base = (
            Commande.objects.filter(
                Q(etats__enum_etat__libelle="À imprimer")
                | Q(etats__enum_etat__libelle="En préparation")
                | Q(etats__enum_etat__libelle="Collectée")
                | Q(etats__enum_etat__libelle="Emballée"),
            etats__operateur=operateur_profile,
                etats__date_fin__isnull=True,
            )
            .select_related("client", "ville", "ville__region")
            .prefetch_related("paniers__article", "etats")
            .distinct()
        )
        
        for commande in commandes_base:
            etats_commande = commande.etats.all().order_by("date_debut")
            etat_prepa_actuel = None
            
            # Trouver l'état actuel de préparation
            for etat in etats_commande:
                if (
                    etat.enum_etat.libelle
                    in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                    and not etat.date_fin
                ):
                    etat_prepa_actuel = etat
                    break
            
            if etat_prepa_actuel:
                # Vérifier s'il y a des états ultérieurs problématiques
                a_etats_ultérieurs_problematiques = False
                for etat in etats_commande:
                    if (
                        etat.date_debut > etat_prepa_actuel.date_debut
                        and etat.enum_etat.libelle
                        in [
                            "Livrée",
                            "Livrée Partiellement",
                            "Préparée",
                            "En cours de livraison",
                        ]
                    ):
                        a_etats_ultérieurs_problematiques = True
                        break
                
                if a_etats_ultérieurs_problematiques:
                    continue
                
                # Inclure toutes les commandes valides (pas d'exclusion basée sur le type)
                commandes_affectees.append(commande)
    
    # Pour les commandes renvoyées par la logistique, respecter l'affectation spécifique à chaque opérateur
    if filter_type == "renvoyees_logistique":
        # Filtrer seulement les commandes renvoyées par la logistique ET affectées à cet opérateur spécifique
        commandes_filtrees = []
        for commande in commandes_affectees:
            
            
            # Vérifier que la commande n'a pas d'états ultérieurs problématiques
            etats_commande = commande.etats.all().order_by("date_debut")
            etat_actuel = None
            
            # Trouver l'état actuel (En préparation)
            for etat in etats_commande:
                if (
                    etat.enum_etat.libelle
                    in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                    and not etat.date_fin
                ):
                    etat_actuel = etat
                    break
            
            if etat_actuel:
                # Vérifier les opérations de traçabilité EN PREMIER
               

                

                # Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
                if commande.num_cmd and commande.num_cmd.startswith("RENVOI-"):
                    # Chercher la commande originale
                    num_cmd_original = commande.num_cmd.replace("RENVOI-", "")
                    commande_originale = Commande.objects.filter(
                        num_cmd=num_cmd_original,
                        etats__enum_etat__libelle="Livrée Partiellement",
                    ).first()

                    if commande_originale:
                        commandes_filtrees.append(commande)
                        continue

                # Sinon, vérifier s'il y a des états ultérieurs problématiques
                a_etats_ultérieurs_problematiques = False
                for etat in etats_commande:
                    if (
                        etat.date_debut > etat_actuel.date_debut
                        and etat.enum_etat.libelle
                        in [
                            "Livrée",
                            "Livrée Partiellement",
                            "Préparée",
                            "En cours de livraison",
                        ]
                    ):
                        a_etats_ultérieurs_problematiques = True
                        break

                if a_etats_ultérieurs_problematiques:
                    continue  # Ignorer cette commande

                # Vérifier l'historique des états de la commande
                # Trouver l'état précédent
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                        if etat.enum_etat.libelle == "En cours de livraison":
                            commandes_filtrees.append(commande)
                            break
        
        commandes_affectees = commandes_filtrees
    
    # Calculer les statistiques par type de commande
    stats_par_type = {
        "renvoyees_logistique": 0,
        "livrees_partiellement": 0,
        "retournees": 0,
        "affectees_admin": 0,
    }
    
    # Pour chaque commande, ajouter l'état précédent pour comprendre d'où elle vient
    for commande in commandes_affectees:
        # Récupérer tous les états de la commande dans l'ordre chronologique
        etats_commande = commande.etats.all().order_by("date_debut")
        
        # Trouver l'état actuel (À imprimer, En préparation, Collectée, ou Emballée)
        etat_actuel = None
        for etat in etats_commande:
            if (
                etat.enum_etat.libelle
                in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                and not etat.date_fin
            ):
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Trouver l'état précédent (le dernier état terminé avant l'état actuel)
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle not in [
                        "À imprimer",
                        "En préparation",
                        "Collectée",
                        "Emballée",
                    ]:
                        etat_precedent = etat
                        break
            
            commande.etat_precedent = etat_precedent
            
            # Trouver l'état de confirmation (le premier état "Confirmée")
            etat_confirmation = None
            for etat in etats_commande:
                if etat.enum_etat.libelle == "Confirmée":
                    etat_confirmation = etat
                    break
            
            commande.etat_confirmation = etat_confirmation
    
    # Si aucune commande trouvée avec la méthode stricte, essayer une approche plus large
    if isinstance(commandes_affectees, list):
        has_commandes = len(commandes_affectees) > 0
    else:
        has_commandes = commandes_affectees.exists()
    
    if not has_commandes:
        # Chercher toutes les commandes qui ont été affectées à cet opérateur pour la préparation
        # et qui n'ont pas encore d'état "Préparée" ou "En cours de livraison"
        commandes_affectees = (
            Commande.objects.filter(
                Q(etats__enum_etat__libelle="À imprimer")
                | Q(etats__enum_etat__libelle="En préparation")
                | Q(etats__enum_etat__libelle="Collectée")
                | Q(etats__enum_etat__libelle="Emballée"),
                etats__operateur=operateur_profile,
            )
            .exclude(
            # Exclure les commandes qui ont déjà un état ultérieur actif
                Q(
                    etats__enum_etat__libelle__in=[
                        "Préparée",
                        "En cours de livraison",
                        "Livrée",
                        "Annulée",
                    ],
                    etats__date_fin__isnull=True,
                )
            )
            .select_related("client", "ville", "ville__region")
            .prefetch_related("paniers__article", "etats")
            .distinct()
        )
        
        # Pour chaque commande, ajouter l'état précédent pour comprendre d'où elle vient
        for commande in commandes_affectees:
            # Récupérer tous les états de la commande dans l'ordre chronologique
            etats_commande = commande.etats.all().order_by("date_debut")
            
            # Trouver l'état actuel (À imprimer, En préparation, Collectée, ou Emballée)
            etat_actuel = None
            for etat in etats_commande:
                if (
                    etat.enum_etat.libelle
                    in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                    and not etat.date_fin
                ):
                    etat_actuel = etat
                    break
            
            if etat_actuel:
                # Trouver l'état précédent (le dernier état terminé avant l'état actuel)
                etat_precedent = None
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                        if etat.enum_etat.libelle not in [
                            "À imprimer",
                            "En préparation",
                            "Collectée",
                            "Emballée",
                        ]:
                            etat_precedent = etat
                            break
                
                commande.etat_precedent = etat_precedent
                
                # Trouver l'état de confirmation (le premier état "Confirmée")
                etat_confirmation = None
                for etat in etats_commande:
                    if etat.enum_etat.libelle == "Confirmée":
                        etat_confirmation = etat
                        break
                
                commande.etat_confirmation = etat_confirmation
    
    # Suppression du filtre 'nouvelles' car redondant avec l'affectation automatique
    # Suppression du filtre 'renvoyees_preparation' car non nécessaire
    
    # Recherche
    search_query = request.GET.get("search", "")
    if search_query:
        if isinstance(commandes_affectees, list):
            # Si c'est une liste (après filtrage)
            commandes_affectees = [
                cmd
                for cmd in commandes_affectees
                if search_query.lower() in str(cmd.id_yz).lower()
                or search_query.lower() in (cmd.num_cmd or "").lower()
                or search_query.lower() in cmd.client.nom.lower()
                or search_query.lower() in cmd.client.prenom.lower()
                or search_query.lower() in (cmd.client.numero_tel or "").lower()
            ]
        else:
            # Si c'est un QuerySet
            commandes_affectees = commandes_affectees.filter(
                Q(id_yz__icontains=search_query)
                | Q(num_cmd__icontains=search_query)
                | Q(client__nom__icontains=search_query)
                | Q(client__prenom__icontains=search_query)
                | Q(client__numero_tel__icontains=search_query)
            ).distinct()
    
    # Tri par date d'affectation (plus récentes en premier)
    if isinstance(commandes_affectees, list):
        commandes_affectees.sort(
            key=lambda x: x.etats.filter(date_fin__isnull=True).first().date_debut
            if x.etats.filter(date_fin__isnull=True).first()
            else timezone.now(),
            reverse=True,
        )
    else:
        commandes_affectees = commandes_affectees.order_by("-etats__date_debut")

    # Générer les codes-barres pour chaque commande
    code128 = barcode.get_barcode_class("code128")
    for commande in commandes_affectees:
        if commande.id_yz:
            barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
            buffer = BytesIO()
            barcode_instance.write(
                buffer, options={"write_text": False, "module_height": 10.0}
            )
            barcode_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            commande.barcode_base64 = barcode_base64
        else:
            commande.barcode_base64 = None
    
    # Statistiques
    if isinstance(commandes_affectees, list):
        total_affectees = len(commandes_affectees)
        valeur_totale = sum(cmd.total_cmd or 0 for cmd in commandes_affectees)
        
        # Commandes urgentes (affectées depuis plus de 1 jour)
        date_limite_urgence = timezone.now() - timedelta(days=1)
        commandes_urgentes = sum(
            1
            for cmd in commandes_affectees
            if cmd.etats.filter(date_debut__lt=date_limite_urgence).exists()
        )
    else:
        total_affectees = commandes_affectees.count()
        valeur_totale = (
            commandes_affectees.aggregate(total=Sum("total_cmd"))["total"] or 0
        )
        
        # Commandes urgentes (affectées depuis plus de 1 jour)
        date_limite_urgence = timezone.now() - timedelta(days=1)
        commandes_urgentes = commandes_affectees.filter(
            etats__date_debut__lt=date_limite_urgence
        ).count()
    
    # Statistiques par type pour les onglets
    stats_par_type = {
        "renvoyees_logistique": 0,
        "livrees_partiellement": 0,
        "retournees": 0,
        "affectees_supervision": 0,
    }
    
    # Recalculer les statistiques pour tous les types
    # D'abord, récupérer toutes les commandes affectées à cet opérateur (sans filtre)
    toutes_commandes = (
        Commande.objects.filter(
            Q(etats__enum_etat__libelle="À imprimer")
            | Q(etats__enum_etat__libelle="En préparation")
            | Q(etats__enum_etat__libelle="Collectée")
            | Q(etats__enum_etat__libelle="Emballée"),
        etats__operateur=operateur_profile,
            etats__date_fin__isnull=True,  # État actif (en cours)
        )
        .select_related("client", "ville", "ville__region")
        .prefetch_related("paniers__article", "etats")
        .distinct()
    )
    
    for cmd in toutes_commandes:
        # Vérifier si c'est une commande renvoyée par la logistique
        
        
        
        
        # Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
        if cmd.num_cmd and cmd.num_cmd.startswith("RENVOI-"):
            # Chercher la commande originale
            num_cmd_original = cmd.num_cmd.replace("RENVOI-", "")
            commande_originale = Commande.objects.filter(
                num_cmd=num_cmd_original,
                etats__enum_etat__libelle="Livrée Partiellement",
            ).first()
            
            if commande_originale:
                stats_par_type["renvoyees_logistique"] += 1
                continue
        
        # Vérifier l'état précédent
        etats_commande = cmd.etats.all().order_by("date_debut")
        etat_actuel = None
        
        # Trouver l'état actuel
        for etat in etats_commande:
            if (
                etat.enum_etat.libelle
                in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                and not etat.date_fin
            ):
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Vérifier s'il y a des états ultérieurs problématiques
            a_etats_ultérieurs_problematiques = False
            for etat in etats_commande:
                if (
                    etat.date_debut > etat_actuel.date_debut
                    and etat.enum_etat.libelle
                    in [
                        "Livrée",
                        "Livrée Partiellement",
                        "Préparée",
                        "En cours de livraison",
                    ]
                ):
                    a_etats_ultérieurs_problematiques = True
                    break
            
            # Si il y a des états ultérieurs problématiques, ignorer cette commande
            if a_etats_ultérieurs_problematiques:
                continue
            
            # Trouver l'état précédent
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == "En cours de livraison":
                        stats_par_type["renvoyees_logistique"] += 1
                        break
                    elif etat.enum_etat.libelle == "Livrée Partiellement":
                        stats_par_type["livrees_partiellement"] += 1
                        break
            
    # Recalculer le compteur des livraisons partielles en utilisant la même logique que la vue séparée
    # Chercher les commandes de renvoi créées lors de livraisons partielles
    commandes_renvoi_livraison_partielle = Commande.objects.filter(
        num_cmd__startswith="RENVOI-",
        etats__enum_etat__libelle="En préparation",
        etats__operateur=operateur_profile,
        etats__date_fin__isnull=True,
    ).distinct()
    
    livrees_partiellement_count = 0
    for commande_renvoi in commandes_renvoi_livraison_partielle:
        # Extraire le numéro de commande original
        num_cmd_original = commande_renvoi.num_cmd.replace("RENVOI-", "")
        
        # Vérifier que la commande originale a été livrée partiellement
        commande_originale = Commande.objects.filter(
            num_cmd=num_cmd_original, etats__enum_etat__libelle="Livrée Partiellement"
        ).first()
        
        if commande_originale:
            livrees_partiellement_count += 1
    
    # Mettre à jour le compteur avec la valeur correcte
    stats_par_type["livrees_partiellement"] = livrees_partiellement_count
    

    


    # Calculer les statistiques pour les commandes affectées par supervision
    commandes_affectees_supervision = 0
    for cmd in toutes_commandes:
        # Vérifier si c'est une commande renvoyée par la logistique
        

        # Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
        if cmd.num_cmd and cmd.num_cmd.startswith("RENVOI-"):
            # Chercher la commande originale
            num_cmd_original = cmd.num_cmd.replace("RENVOI-", "")
            commande_originale = Commande.objects.filter(
                num_cmd=num_cmd_original,
                etats__enum_etat__libelle="Livrée Partiellement",
            ).first()

            if commande_originale:
                continue  # Déjà comptée dans livrees_partiellement

        # Vérifier l'historique des états
        etats_commande = cmd.etats.all().order_by("date_debut")
        etat_actuel = None

        # Trouver l'état actuel
        for etat in etats_commande:
            if (
                etat.enum_etat.libelle
                in ["À imprimer", "En préparation", "Collectée", "Emballée"]
                and not etat.date_fin
            ):
                etat_actuel = etat
                break

        if etat_actuel:
            # Vérifier s'il y a des états ultérieurs problématiques
            a_etats_ultérieurs_problematiques = False
            for etat in etats_commande:
                if (
                    etat.date_debut > etat_actuel.date_debut
                    and etat.enum_etat.libelle
                    in [
                        "Livrée",
                        "Livrée Partiellement",
                        "Préparée",
                        "En cours de livraison",
                    ]
                ):
                    a_etats_ultérieurs_problematiques = True
                    break

            if a_etats_ultérieurs_problematiques:
                continue

            # Vérifier l'historique pour renvoi depuis livraison
            has_return_from_delivery = False
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == "En cours de livraison":
                        has_return_from_delivery = True
                        break
                    elif etat.enum_etat.libelle == "Livrée Partiellement":
                        has_return_from_delivery = True
                        break

            

    stats_par_type["affectees_supervision"] = commandes_affectees_supervision

    # Pour l'onglet "Toutes les commandes", le total doit être la somme des 3 autres onglets
    if filter_type == "all":
        total_affectees = (
            stats_par_type["renvoyees_logistique"]
            + stats_par_type["livrees_partiellement"]
            + stats_par_type["affectees_supervision"]
        )

    # Calculer les statistiques par état
    stats_etats = {
        "en_preparation": toutes_commandes.filter(etats__enum_etat__libelle="En préparation", etats__date_fin__isnull=True).distinct().count(),
        "collectee": toutes_commandes.filter(etats__enum_etat__libelle="Collectée", etats__date_fin__isnull=True).distinct().count(),
        "emballee": toutes_commandes.filter(etats__enum_etat__libelle="Emballée", etats__date_fin__isnull=True).distinct().count(),
    }

    # Gérer le filtre par état
    etat_filter = request.GET.get("etat", "")
    if etat_filter == "en_preparation":
        if isinstance(commandes_affectees, list):
            commandes_affectees = [cmd for cmd in commandes_affectees if cmd.etat_actuel and cmd.etat_actuel.enum_etat.libelle == "En préparation"]
        else:
            commandes_affectees = commandes_affectees.filter(etats__enum_etat__libelle="En préparation", etats__date_fin__isnull=True)
        filter_type = "en_preparation"
    elif etat_filter == "collectee":
        if isinstance(commandes_affectees, list):
            commandes_affectees = [cmd for cmd in commandes_affectees if cmd.etat_actuel and cmd.etat_actuel.enum_etat.libelle == "Collectée"]
        else:
            commandes_affectees = commandes_affectees.filter(etats__enum_etat__libelle="Collectée", etats__date_fin__isnull=True)
        filter_type = "collectee"
    elif etat_filter == "emballee":
        if isinstance(commandes_affectees, list):
            commandes_affectees = [cmd for cmd in commandes_affectees if cmd.etat_actuel and cmd.etat_actuel.enum_etat.libelle == "Emballée"]
        else:
            commandes_affectees = commandes_affectees.filter(etats__enum_etat__libelle="Emballée", etats__date_fin__isnull=True)
        filter_type = "emballee"

    # Vérifier si c'est une requête AJAX pour les statistiques
    if request.GET.get("ajax") == "stats":
        from django.http import JsonResponse

        return JsonResponse(
            {
                "affectees_supervision": stats_par_type.get("affectees_supervision", 0),
                "total_affectees": total_affectees,
                "renvoyees_logistique": stats_par_type.get("renvoyees_logistique", 0),
                "en_preparation": stats_etats.get("en_preparation", 0),
                "collectee": stats_etats.get("collectee", 0),
                "emballee": stats_etats.get("emballee", 0),
            }
        )

    # Pagination côté serveur
    items_per_page = int(request.GET.get('per_page', 10))  # Par défaut 10 éléments par page
    page_number = request.GET.get('page', 1)
    
    # Créer le paginator avec la liste des commandes
    paginator = Paginator(commandes_affectees, items_per_page)
    
    try:
        commandes_paginated = paginator.page(page_number)
    except (Paginator.EmptyPage, ValueError):
        # Si la page demandée n'existe pas ou n'est pas un nombre valide, afficher la première page
        commandes_paginated = paginator.page(1)
        page_number = 1

    context = {
        "page_title": "Mes Commandes à Préparer",
        "page_subtitle": f"Vous avez {total_affectees} commande(s) affectée(s)",
        "commandes_affectees": commandes_paginated,  # Utiliser les commandes paginées
        "search_query": search_query,
        "filter_type": filter_type,
        "stats": {
            "total_affectees": total_affectees,
            "valeur_totale": valeur_totale,
            "commandes_urgentes": commandes_urgentes,
            "en_preparation": stats_etats.get("en_preparation", 0),
            "collectee": stats_etats.get("collectee", 0),
            "emballee": stats_etats.get("emballee", 0),
        },
        "stats_par_type": stats_par_type,
        "operateur_profile": operateur_profile,
        "api_produits_url_base": reverse(
            "Prepacommande:api_commande_produits", args=[99999999]
        ),
        # Informations de pagination
        "paginator": paginator,
        "page_obj": commandes_paginated,
        "items_per_page": items_per_page,
        "current_page": page_number,
        "total_pages": paginator.num_pages,
        "has_previous": commandes_paginated.has_previous(),
        "has_next": commandes_paginated.has_next(),
        "previous_page_number": commandes_paginated.previous_page_number() if commandes_paginated.has_previous() else None,
        "next_page_number": commandes_paginated.next_page_number() if commandes_paginated.has_next() else None,
    }
    return render(request, "Prepacommande/liste_prepa.html", context)


@login_required
def commandes_en_preparation(request):
    """Liste des commandes en cours de préparation pour les opérateurs de préparation"""
    from django.core.paginator import Paginator
    
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(
                request,
                "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.",
            )
            return redirect("login")
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Récupérer les commandes dont l'état ACTUEL est "En préparation" et qui sont affectées à cet opérateur
    commandes_en_preparation = (
        Commande.objects.filter(
            etats__enum_etat__libelle="En préparation",
        etats__operateur=operateur_profile,
            etats__date_fin__isnull=True,  # État actif (en cours)
        )
        .select_related("client", "ville", "ville__region")
        .prefetch_related("paniers__article", "etats")
        .distinct()
    )

    # Pagination côté serveur
    items_per_page = int(request.GET.get('per_page', 10))  # Par défaut 10 éléments par page
    page_number = request.GET.get('page', 1)
    
    # Créer le paginator avec la liste des commandes
    paginator = Paginator(commandes_en_preparation, items_per_page)
    
    try:
        commandes_paginated = paginator.page(page_number)
    except (Paginator.EmptyPage, ValueError):
        # Si la page demandée n'existe pas ou n'est pas un nombre valide, afficher la première page
        commandes_paginated = paginator.page(1)
        page_number = 1

    context = {
        "page_title": "Commandes en Préparation",
        "page_subtitle": "Interface Opérateur de Préparation",
        "profile": operateur_profile,
        "commandes": commandes_paginated,  # Utiliser les commandes paginées
        "active_tab": "en_preparation",
        # Informations de pagination
        "paginator": paginator,
        "page_obj": commandes_paginated,
        "items_per_page": items_per_page,
        "current_page": page_number,
        "total_pages": paginator.num_pages,
        "has_previous": commandes_paginated.has_previous(),
        "has_next": commandes_paginated.has_next(),
        "previous_page_number": commandes_paginated.previous_page_number() if commandes_paginated.has_previous() else None,
        "next_page_number": commandes_paginated.next_page_number() if commandes_paginated.has_next() else None,
    }
    return render(request, "Prepacommande/commandes_en_preparation.html", context)


@login_required
def traiter_commande_retournee_api(request, commande_id):
    """API pour traiter une commande retournée et gérer la réincrémentation du stock"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"})
    
    try:
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            return JsonResponse({"success": False, "message": "Accès non autorisé"})
        
        # Récupérer la commande
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est bien retournée et préparée par cet opérateur
        if not commande.etats.filter(
            enum_etat__libelle="Retournée", date_fin__isnull=True
        ).exists():
            return JsonResponse({"success": False, "message": "Commande non retournée"})
        
        if not commande.etats.filter(
            enum_etat__libelle="En préparation", operateur=operateur_profile
        ).exists():
            return JsonResponse(
                {"success": False, "message": "Commande non préparée par vous"}
            )
        
        # Récupérer les données de la requête
        data = json.loads(request.body)
        type_traitement = data.get("type_traitement")
        etat_stock = data.get("etat_stock")
        commentaire = data.get("commentaire")
        
        if not all([type_traitement, etat_stock, commentaire]):
            return JsonResponse({"success": False, "message": "Données manquantes"})
        
        # Traitement selon le type
        with transaction.atomic():
            if type_traitement == "repreparer":
                # Ne pas changer l'état de la commande, elle reste "Retournée"
                # Seulement réincrémenter le stock si les produits sont en bon état
                if etat_stock == "bon":
                    for panier in commande.paniers.all():
                        article = panier.article
                        quantite = panier.quantite
                        
                        # Réincrémenter le stock disponible
                        article.qte_disponible += quantite
                        article.save()
                        
                        # Créer un mouvement de stock pour tracer
                        from article.models import MouvementStock

                        MouvementStock.objects.create(
                            article=article,
                            quantite=quantite,
                            type_mouvement="entree",
                            commentaire=f"Réincrémentation - Commande retournée {commande.id_yz} - Produits en bon état - {commentaire}",
                            operateur=operateur_profile,
                            qte_apres_mouvement=article.qte_disponible,
                        )
                
                message = f"Stock réincrémenté: {'Oui' if etat_stock == 'bon' else 'Non'}. Commande reste en état 'Retournée'."
                
                return JsonResponse(
                    {"success": True, "message": message, "commande_id": commande.id}
                )

            return JsonResponse(
                {"success": True, "message": message, "commande_id": commande.id}
            )
            
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})


@login_required
def profile_view(request):
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")  # Ou une page d'erreur appropriée

    context = {
        "page_title": "Mon Profil",
        "page_subtitle": "Gérez les informations de votre profil",
        "profile": operateur_profile,
    }
    return render(request, "Prepacommande/profile.html", context)


@login_required
def modifier_profile_view(request):
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    if request.method == "POST":
        # Récupérer les données du formulaire
        nom = request.POST.get("nom")
        prenom = request.POST.get("prenom")
        mail = request.POST.get("mail")
        telephone = request.POST.get("telephone")
        adresse = request.POST.get("adresse")

        # Validation minimale (vous pouvez ajouter plus de validations ici)
        if not nom or not prenom or not mail:
            messages.error(request, "Nom, prénom et email sont requis.")
            context = {
                "page_title": "Modifier Profil",
                "page_subtitle": "Mettez à jour vos informations personnelles",
                "profile": operateur_profile,
                "form_data": request.POST,  # Pour pré-remplir le formulaire
            }
            return render(request, "Prepacommande/modifier_profile.html", context)
        
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
        if "photo" in request.FILES:
            operateur_profile.photo = request.FILES["photo"]
        
        operateur_profile.save()

        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect(
            "Prepacommande:profile"
        )  # Rediriger vers la page de profil après succès
    else:
        context = {
            "page_title": "Modifier Profil",
            "page_subtitle": "Mettez à jour vos informations personnelles",
            "profile": operateur_profile,
        }
        return render(request, "Prepacommande/modifier_profile.html", context)


@login_required
def changer_mot_de_passe_view(request):
    """Page de changement de mot de passe pour l'opérateur de préparation - Désactivée"""
    return redirect("Prepacommande:profile")


@login_required
def detail_prepa(request, pk):
    """Vue détaillée pour la préparation d'une commande spécifique"""
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(
                request,
                "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.",
            )
            return redirect("login")
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Récupérer la commande spécifique
    try:
        commande = (
            Commande.objects.select_related("client", "ville", "ville__region")
            .prefetch_related(
                "paniers__article",
                "paniers__variante",
                "paniers__variante__couleur",
                "paniers__variante__pointure",
                "etats__enum_etat",
                "etats__operateur"
            )
            .get(id=pk)
        )
    except Commande.DoesNotExist:
        messages.error(request, "La commande demandée n'existe pas.")
        return redirect("Prepacommande:liste_prepa")

    # Vérifier que la commande est bien affectée à cet opérateur pour la préparation
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle="À imprimer")
        | Q(enum_etat__libelle="En préparation")
        | Q(enum_etat__libelle="Collectée")
        | Q(enum_etat__libelle="Emballée"),
        operateur=operateur_profile,
    ).first()
    
    if not etat_preparation:
        messages.error(
            request, "Cette commande ne vous est pas affectée pour la préparation."
        )
        return redirect("Prepacommande:liste_prepa")

    # Récupérer les paniers (articles) de la commande
    paniers = commande.paniers.all().select_related(
        "article",
        "variante",
        "variante__couleur",
        "variante__pointure",
        "remise_personnalisee"
    )

    # Initialiser les variables pour les cas de livraison partielle/renvoi
    articles_livres = []
    articles_renvoyes = []
    is_commande_livree_partiellement = False
    commande_renvoi = None  # Initialiser à None
    commande_originale = None  # Initialiser à None
    etat_articles_renvoyes = {}  # Initialiser à un dictionnaire vide

    # Ajouter le prix unitaire, le total de chaque ligne, l'URL d'image et les variantes
    articles_image_urls = {}
    total_articles = 0
    total_remises = 0

    for panier in paniers:
        # Prix unitaire - utiliser prix_panier qui est le prix historique gelé
        panier.prix_unitaire = panier.prix_panier if panier.prix_panier else (
            panier.sous_total / panier.quantite if panier.quantite > 0 else 0
        )

        # Calculer le sous-total avant remise
        panier.sous_total_avant_remise = panier.prix_panier * panier.quantite if panier.prix_panier else panier.sous_total

        # Gérer les remises
        panier.a_remise = False
        panier.montant_remise = 0
        panier.info_remise = ""

        # Vérifier si une remise personnalisée existe
        if hasattr(panier, 'remise_personnalisee') and panier.remise_personnalisee:
            remise = panier.remise_personnalisee
            panier.a_remise = True
            panier.montant_remise = float(remise.montant_applique)

            if remise.type_remise == 'POURCENTAGE':
                panier.info_remise = f"Remise {remise.valeur_remise}%"
            else:
                panier.info_remise = f"Remise {remise.valeur_remise} DH"

            total_remises += panier.montant_remise
        # Vérifier si une remise standard est appliquée
        elif panier.remise_appliquer and panier.type_remise_appliquee:
            panier.a_remise = True
            # Calculer le montant de la remise
            if panier.sous_total_remise and panier.sous_total_remise > 0:
                panier.montant_remise = panier.sous_total_avant_remise - panier.sous_total_remise
                panier.info_remise = f"Remise {panier.type_remise_appliquee}"
                total_remises += panier.montant_remise

        # Total ligne final (après remise si applicable)
        if panier.a_remise:
            if panier.sous_total_remise and panier.sous_total_remise > 0:
                panier.total_ligne = panier.sous_total_remise
            else:
                panier.total_ligne = panier.sous_total_avant_remise - panier.montant_remise
        else:
            panier.total_ligne = panier.sous_total_avant_remise

        total_articles += panier.total_ligne

        # Image de l'article
        image_url = None
        try:
            # Protéger l'accès à .url si aucun fichier n'est associé
            if getattr(panier.article, "image", None):
                # Certains backends lèvent une exception si l'image n'existe pas
                if hasattr(panier.article.image, "url"):
                    image_url = panier.article.image.url
        except Exception:
            image_url = None
        # Rendre accessible directement dans le template via panier.article.image_url
        setattr(panier.article, "image_url", image_url)
        # Egalement disponible dans le context si nécessaire
        if getattr(panier.article, "id", None) is not None:
            articles_image_urls[panier.article.id] = image_url

        # Ajouter les informations de variante (couleur et pointure)
        if panier.variante:
            panier.couleur_display = panier.variante.couleur.nom if panier.variante.couleur else None
            panier.pointure_display = panier.variante.pointure.pointure if panier.variante.pointure else None
        else:
            panier.couleur_display = None
            panier.pointure_display = None
    
    # Récupérer tous les états de la commande pour afficher l'historique
    etats_commande = (
        commande.etats.all()
        .select_related("enum_etat", "operateur")
        .order_by("date_debut")
    )
    
    # Déterminer l'état actuel
    etat_actuel = etats_commande.filter(date_fin__isnull=True).first()
    
    # Récupérer l'état précédent pour comprendre d'où vient la commande
    etat_precedent = None
    if etat_actuel:
        # Trouver l'état précédent (le dernier état terminé avant l'état actuel)
        for etat in reversed(etats_commande):
            if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                if etat.enum_etat.libelle not in [
                    "À imprimer",
                    "En préparation",
                    "Collectée",
                    "Emballée",
                ]:
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
    if etat_actuel and etat_actuel.enum_etat.libelle == "Livrée Partiellement":
        is_commande_livree_partiellement = True
        # Les articles dans cette commande sont ceux qui ont été livrés partiellement
        for panier in paniers:
            articles_livres.append(
                {
                    "article": panier.article,
                    "quantite_livree": panier.quantite,
                    "prix": panier.article.prix_unitaire,
                    "sous_total": panier.sous_total,
                }
            )
        
        # Chercher la commande de renvoi associée
        commande_renvoi = Commande.objects.filter(
            num_cmd__startswith=f"RENVOI-{commande.num_cmd}", client=commande.client
        ).first()
        
        # La commande source pour les articles renvoyés est la commande actuelle
        operation_livraison_partielle = (
            commande.operations.filter(type_operation="LIVRAISON_PARTIELLE")
            .order_by("-date_operation")
            .first()
        )

    # Cas 2: La commande actuelle est une commande de renvoi suite à une livraison partielle
    elif etat_precedent and etat_precedent.enum_etat.libelle == "Livrée Partiellement":
        is_commande_livree_partiellement = True
        # Chercher la commande originale qui a été livrée partiellement
        commande_originale = Commande.objects.filter(
            num_cmd=commande.num_cmd.replace("RENVOI-", ""), client=commande.client
        ).first()
        
        # La commande source pour les articles renvoyés est la commande originale
        if commande_originale:
            operation_livraison_partielle = (
                commande_originale.operations.filter(
                    type_operation="LIVRAISON_PARTIELLE"
                )
                .order_by("-date_operation")
                .first()
            )

    # Si une opération de livraison partielle est trouvée, extraire les états des articles renvoyés
    if operation_livraison_partielle:
        try:
            details = json.loads(operation_livraison_partielle.conclusion)
            if "recap_articles_renvoyes" in details:
                for item in details["recap_articles_renvoyes"]:
                    etat_articles_renvoyes[item["article_id"]] = item["etat"]
        except Exception:
            pass

    # Populer articles_renvoyes si c'est une commande de renvoi ou si elle a une commande de renvoi associée
    if is_commande_livree_partiellement:
        # Si la commande actuelle est une commande de renvoi (Cas 2)
        if commande.num_cmd and commande.num_cmd.startswith("RENVOI-"):
            for panier_renvoi in paniers:
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id, "bon")
                articles_renvoyes.append(
                    {
                        "article": panier_renvoi.article,
                        "quantite": panier_renvoi.quantite,
                        "prix": panier_renvoi.article.prix_unitaire,
                        "sous_total": panier_renvoi.sous_total,
                        "etat": etat,
                    }
                )
        # Si la commande actuelle est la commande originale livrée partiellement et qu'une commande de renvoi existe (Cas 1)
        elif commande_renvoi:
            for panier_renvoi in commande_renvoi.paniers.all():
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id, "bon")
                articles_renvoyes.append(
                    {
                        "article": panier_renvoi.article,
                        "quantite": panier_renvoi.quantite,
                        "prix": panier_renvoi.article.prix_unitaire,
                        "sous_total": panier_renvoi.sous_total,
                        "etat": etat,
                    }
                )

    # Pour les articles livrés, on lit l'opération de livraison partielle sur la commande originale
    if is_commande_livree_partiellement and commande_originale:
        operation_livraison_partielle_for_livres = (
            commande_originale.operations.filter(type_operation="LIVRAISON_PARTIELLE")
            .order_by("-date_operation")
            .first()
        )
        if operation_livraison_partielle_for_livres:
            try:
                details = json.loads(
                    operation_livraison_partielle_for_livres.conclusion
                )
                if "articles_livres" in details:
                    for article_livre in details["articles_livres"]:
                        article = Article.objects.filter(
                            id=article_livre.get("article_id")
                        ).first()
                        if article:
                            articles_livres.append(
                                {
                                    "article": article,
                                    "quantite_livree": article_livre.get("quantite", 0),
                                    "prix": article.prix_unitaire,
                                    "sous_total": article.prix_unitaire
                                    * article_livre.get("quantite", 0),
                                }
                            )
            except Exception:
                pass

    # Note: total_articles et total_remises sont déjà calculés dans la boucle des paniers ci-dessus

    # Récupérer les opérations associées à la commande
    operations = commande.operations.select_related("operateur").order_by(
        "-date_operation"
    )
    
    # Générer le code-barres pour la commande
    code128 = barcode.get_barcode_class("code128")
    barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
    buffer = BytesIO()
    barcode_instance.write(buffer, options={"write_text": False, "module_height": 10.0})
    barcode_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    commande_barcode = f"data:image/png;base64,{barcode_base64}"

    # Gestion des actions POST (marquer comme préparée, etc.)
    if request.method == "POST":
        action = request.POST.get("action")
        
        # Action 'commencer_preparation' supprimée car les commandes passent maintenant 
        # directement en "En préparation" lors de l'affectation
        
        if action == "marquer_collectee":
            with transaction.atomic():
                # Marquer l'état 'En préparation' comme terminé
                etat_en_preparation, created = EnumEtatCmd.objects.get_or_create(
                    libelle="En préparation"
                )
                
                etat_actuel = EtatCommande.objects.filter(
                    commande=commande,
                    enum_etat=etat_en_preparation,
                    date_fin__isnull=True,
                ).first()
                
                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.operateur = operateur_profile
                    etat_actuel.save()
                
                # Créer le nouvel état 'Collectée'
                etat_collectee, created = EnumEtatCmd.objects.get_or_create(
                    libelle="Collectée"
                )
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_collectee,
                    operateur=operateur_profile,
                )
                
                # Log de l'opération
           

            messages.success(
                request,
                f"La commande {commande.id_yz} a bien été marquée comme collectée.",
            )
            return redirect("Prepacommande:detail_prepa", pk=commande.pk)

        elif action == "marquer_emballee":
            with transaction.atomic():
                # Marquer l'état 'Collectée' comme terminé
                etat_collectee, created = EnumEtatCmd.objects.get_or_create(
                    libelle="Collectée"
                )

                etat_actuel = EtatCommande.objects.filter(
                    commande=commande, enum_etat=etat_collectee, date_fin__isnull=True
                ).first()

                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.operateur = operateur_profile
                    etat_actuel.save()

                # Créer le nouvel état 'Emballée'
                etat_emballee, created = EnumEtatCmd.objects.get_or_create(
                    libelle="Emballée"
                )
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_emballee,
                    operateur=operateur_profile,
                )

             

                # TODO: Ajouter ici la notification au superviseur
                # Pour l'instant, on peut utiliser les messages Django ou créer un système de notification

            messages.success(
                request,
                f"La commande {commande.id_yz} a bien été marquée comme emballée. Le superviseur a été notifié.",
            )
            return redirect("Prepacommande:detail_prepa", pk=commande.pk)

        elif action == "signaler_probleme":
            with transaction.atomic():
                # 1. Terminer l'état "En préparation" actuel
                etat_en_preparation_enum = get_object_or_404(
                    EnumEtatCmd, libelle="En préparation"
                )
                etat_actuel = EtatCommande.objects.filter(
                    commande=commande,
                    enum_etat=etat_en_preparation_enum,
                    date_fin__isnull=True,
                ).first()

                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.commentaire = "Problème signalé par le préparateur."
                    etat_actuel.save()

                # 2. Trouver l'opérateur de confirmation d'origine
                operateur_confirmation_origine = None
                etats_precedents = commande.etats.select_related("operateur").order_by(
                    "-date_debut"
                )
                
                for etat in etats_precedents:
                    if etat.operateur and etat.operateur.is_confirmation:
                        operateur_confirmation_origine = etat.operateur
                        break
                
                # 3. Créer l'état "Retour Confirmation" et l'affecter
                etat_retour_enum, _ = EnumEtatCmd.objects.get_or_create(
                    libelle="Retour Confirmation",
                    defaults={"ordre": 25, "couleur": "#D97706"},
                )
                
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_retour_enum,
                    operateur=operateur_confirmation_origine,  # Affectation directe
                    date_debut=timezone.now(),
                    commentaire="Retourné par la préparation pour vérification.",
                )

                # 4. Log et message de succès
                if operateur_confirmation_origine:
                    log_conclusion = f"Problème signalé par {operateur_profile.nom_complet}. Commande retournée et affectée à l'opérateur {operateur_confirmation_origine.nom_complet}."
                    messages.success(
                        request,
                        f"La commande {commande.id_yz} a été retournée à {operateur_confirmation_origine.nom_complet} pour vérification.",
                    )
                else:
                    log_conclusion = f"Problème signalé par {operateur_profile.nom_complet}. Opérateur d'origine non trouvé, commande renvoyée au pool de confirmation."
                    messages.warning(
                        request,
                        f"La commande {commande.id_yz} a été renvoyée au pool de confirmation (opérateur d'origine non trouvé).",
                    )

              

            return redirect("Prepacommande:liste_prepa")
    
    # Avant le return render dans detail_prepa
    commande_renvoi_id = None
    if commande_renvoi:
        commande_renvoi_id = commande_renvoi.id
    
    context = {
        "page_title": f"Préparation Commande {commande.id_yz}",
        "page_subtitle": f"Détails de la commande et étapes de préparation",
        "commande": commande,
        "paniers": paniers,
        "etats_commande": etats_commande,
        "etat_actuel": etat_actuel,
        "etat_precedent": etat_precedent,
        "etat_preparation": etat_preparation,
        "total_articles": total_articles,
        "total_remises": total_remises,
        "operations": operations,
        "commande_barcode": commande_barcode,
        "is_commande_livree_partiellement": is_commande_livree_partiellement,
        "articles_livres": articles_livres,
        "articles_renvoyes": articles_renvoyes,
        "articles_image_urls": articles_image_urls,
        # Variables de debug/informations supplémentaires
        "commande_originale": commande_originale,
        "commande_renvoi": commande_renvoi,
        "etat_articles_renvoyes": etat_articles_renvoyes,
        "commande_renvoi_id": commande_renvoi_id,
    }
    return render(request, "Prepacommande/detail_prepa.html", context)


@login_required
def api_commande_produits(request, commande_id):
    """API pour récupérer les produits d'une commande pour les étiquettes"""
    try:
        # Récupérer la commande. La sécurité est déjà gérée par la page
        # qui appelle cette API, qui ne liste que les commandes autorisées.
        commande = Commande.objects.get(id=commande_id)
        
        # Récupérer tous les produits de la commande
        paniers = commande.paniers.all().select_related("article")
        
        # Construire la liste des produits
        produits_list = []
        for panier in paniers:
            if panier.article:
                # Format: "NOM REFERENCE , POINTURE"
                produit_info = f"{panier.article.nom or ''} {panier.article.reference or ''}".strip()
                if panier.article.pointure:
                    produit_info += f" , {panier.article.pointure}"
                
                # Ajouter la quantité si elle est supérieure à 1
                if panier.quantite > 1:
                    produit_info += (
                        f" (x{panier.quantite})"  # Mettre la quantité entre parenthèses
                    )
                produits_list.append(produit_info)
        
        # Joindre tous les produits en une seule chaîne, en utilisant " + " comme séparateur
        produits_text = (
            " + ".join(produits_list) if produits_list else "PRODUITS NON SPÉCIFIÉS"
        )

        return JsonResponse(
            {
                "success": True,
                "produits": produits_text,
                "nombre_articles": len(produits_list),
            }
        )
        
    except Commande.DoesNotExist:
        return JsonResponse({"success": False, "message": "Commande non trouvée"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"})


@login_required
@handle_ajax_errors
def modifier_commande_prepa(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de préparation"""
    print(f"🔍 ===== DÉBUT modifier_commande_prepa =====")
    print(f"🔍 Méthode: {request.method}")
    print(f"🔍 Commande ID: {commande_id}")
    print(f"🔍 URL: {request.path}")
    
    import json
    from commande.models import Commande
    from parametre.models import Ville
    
    print(f"🔍 Récupération de l'opérateur")
    # Récupérer l'opérateur
    try:
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
        print(f"✅ Opérateur trouvé: {operateur.user.username}")
    except Operateur.DoesNotExist:
        print(f"❌ Opérateur non trouvé pour l'utilisateur: {request.user.username}")
        messages.error(request, "Profil d'opérateur de préparation non trouvé.")
        return redirect("login")
    
    print(f"🔍 Récupération de la commande: {commande_id}")
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
    print(f"✅ Commande trouvée: {commande.id_yz}")
    
    print(f"🔍 Vérification de l'état de préparation")
    # Vérifier que la commande est affectée à cet opérateur pour la préparation
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle="À imprimer") | Q(enum_etat__libelle="En préparation"),
        operateur=operateur,
        date_fin__isnull=True,
    ).first()
    
    print(f"🔍 État de préparation trouvé: {etat_preparation}")
    
    if not etat_preparation:
        print(f"❌ Commande non affectée à l'opérateur pour la préparation")
        messages.error(
            request, "Cette commande ne vous est pas affectée pour la préparation."
        )
        return redirect("Prepacommande:liste_prepa")
    
    print(f"✅ Commande affectée à l'opérateur pour la préparation")

    if request.method == "POST":
        print(f"🔍 Requête POST reçue")
        print(f"🔍 POST data: {dict(request.POST)}")
        try:
            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================
            action = request.POST.get("action")
            
            # Vérifier si c'est une requête AJAX
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
            
            # Forcer le traitement AJAX pour les actions spécifiques
            if action in ['add_article', 'delete_article', 'update_quantity', 'replace_article', 'update_operation', 'add_operation', 'update_commande_info']:
                is_ajax = True
                print(f"🔄 Traitement AJAX forcé pour l'action: {action}")
            
            print(f"🔍 Action détectée: {action}")
            print(f"🔍 Requête AJAX: {is_ajax}")
            print(f"🔍 Content-Type: {request.content_type}")
            print(f"🔍 Headers: {dict(request.headers)}")
            
            # Si c'est une action AJAX mais pas détectée comme telle, forcer le traitement
            if action and action in ['add_article', 'delete_article', 'update_quantity', 'replace_article', 'update_operation', 'add_operation', 'update_commande_info'] and not is_ajax:
                print(f"⚠️ Action AJAX non détectée, forçage du traitement AJAX pour: {action}")
                is_ajax = True
            
            if action == "add_article":
                print(f"🔄 Traitement de l'action add_article (AJAX: {is_ajax})")
                print(f"🔍 Début du traitement add_article")
                
                # Ajouter un nouvel article immédiatement
                from article.models import Article, Variante
                from commande.models import Panier
                
                # Support both parameter names for backward compatibility
                article_id = request.POST.get("articleId") or request.POST.get("article_id")
                quantite = int(request.POST.get("quantite", 1))
                variante_id = request.POST.get("varianteId") or request.POST.get("variante_id")
                
                print(f"🔍 Paramètres reçus: article_id={article_id}, quantite={quantite}, variante_id={variante_id}")
                print(f"🔍 Type des paramètres: article_id={type(article_id)}, quantite={type(quantite)}, variante_id={type(variante_id)}")
                
                try:
                    print(f"🔍 Début du bloc try pour add_article")
                    print(f"🔍 Vérification des variantes et articles")
                    # Vérifier si une variante spécifique a été sélectionnée
                    if variante_id:
                        print(f"🔍 Recherche de variante spécifique: {variante_id}")
                        try:
                            variante = Variante.objects.get(id=variante_id)
                            article = variante.article  # Utiliser l'article parent de la variante
                            print(f"🔄 Variante spécifique trouvée: ID={variante.id}, Article parent: {article.nom}")
                        except Variante.DoesNotExist:
                            print(f"❌ Variante spécifiée non trouvée: {variante_id}")
                            return JsonResponse({"success": False, "error": "Variante non trouvée"})
                    else:
                        print(f"🔍 Pas de variante spécifiée, recherche d'article: {article_id}")
                        # Vérifier si l'article_id est une variante ou un article
                        try:
                            # Essayer de trouver une variante d'abord
                            variante = Variante.objects.get(id=article_id)
                            article = variante.article  # Utiliser l'article parent de la variante
                            print(f"🔄 Variante trouvée: ID={variante.id}, Article parent: {article.nom}")
                        except Variante.DoesNotExist:
                            print(f"🔍 Pas une variante, recherche d'article normal: {article_id}")
                            # Si ce n'est pas une variante, c'est un article normal
                            article = Article.objects.get(id=article_id)
                            variante = None
                            print(f"🔄 Article normal trouvé: ID={article.id}, Nom: {article.nom}")
                    
                    print(f"🔍 Vérification du panier existant")
                    # Vérifier si l'article existe déjà dans la commande
                    panier_existant = Panier.objects.filter(
                        commande=commande, article=article
                    ).first()
                    
                    print(f"🔍 Panier existant trouvé: {panier_existant is not None}")
                    
                    if panier_existant:
                        print(f"🔍 Mise à jour du panier existant")
                        # Si l'article existe déjà, mettre à jour la quantité
                        panier_existant.quantite += quantite
                        panier_existant.save()
                        panier = panier_existant
                        print(
                            f"🔄 Article existant mis à jour: ID={article.id}, nouvelle quantité={panier.quantite}"
                        )
                    else:
                        print(f"🔍 Création d'un nouveau panier")
                        # Si l'article n'existe pas, créer un nouveau panier
                        panier = Panier.objects.create(
                            commande=commande,
                            article=article,
                            quantite=quantite,
                            sous_total=0,  # Sera recalculé après
                        )
                        print(
                            f"➕ Nouvel article ajouté: ID={article.id}, quantité={quantite}"
                        )
                    
                    print(f"🔍 Gestion des variantes et calcul des prix")
                    # Si c'était une variante, stocker l'information de la variante
                    if variante:
                        print(f"🔍 Stockage des informations de variante")
                        # Vous pouvez ajouter un champ personnalisé au panier pour stocker la variante
                        # Ou utiliser un système de commentaires pour stocker cette information
                        panier.commentaire = f"Variante sélectionnée: {variante.couleur} - {variante.pointure}"
                        panier.save()
                        print(f"📝 Variante stockée: {variante.couleur} - {variante.pointure}")
                    
                    print(f"🔍 Vérification si article est upsell")
                    # Recalculer le compteur après ajout (logique de confirmation)
                    if (
                        article.isUpsell
                        and hasattr(article, "prix_upsell_1")
                        and article.prix_upsell_1 is not None
                    ):
                        print(f"🔍 Calcul du compteur upsell")
                        # Compter la quantité totale d'articles upsell (après ajout)
                        total_quantite_upsell = (
                            commande.paniers.filter(article__isUpsell=True).aggregate(
                                total=Sum("quantite")
                            )["total"]
                            or 0
                        )
                        
                        print(f"🔍 Total quantité upsell: {total_quantite_upsell}")
                        
                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                        # 0-1 unités upsell → compteur = 0
                        # 2+ unités upsell → compteur = total_quantite_upsell - 1
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        
                        print(f"🔍 Nouveau compteur: {commande.compteur}")
                        commande.save()
                        
                        print(f"🔍 Recalcul des totaux upsell")
                        # Recalculer TOUS les articles de la commande avec le nouveau compteur
                        commande.recalculer_totaux_upsell()
                    else:
                        print(f"🔍 Calcul des prix pour article normal")
                        # Pour les articles normaux, juste calculer le sous-total
                        from commande.templatetags.commande_filters import (
                            get_prix_upsell_avec_compteur,
                        )

                        print(f"🔍 Récupération du prix unitaire")
                        prix_unitaire = get_prix_upsell_avec_compteur(
                            article, commande.compteur
                        )
                        print(f"🔍 Prix unitaire: {prix_unitaire}")
                        sous_total = prix_unitaire * panier.quantite
                        print(f"🔍 Sous-total: {sous_total}")
                        panier.sous_total = float(sous_total)
                        panier.save()
                        print(f"🔍 Panier sauvegardé avec sous-total: {panier.sous_total}")
                    
                    # Recalculer le total de la commande avec frais de livraison
                    total_articles = (
                        commande.paniers.aggregate(total=Sum("sous_total"))["total"]
                        or 0
                    )
                    frais_livraison = (
                        commande.ville.frais_livraison if commande.ville else 0
                    )
                    commande.total_cmd = float(
                        total_articles
                    )  # + float(frais_livraison)
                    commande.save()
                    
                    # Calculer les statistiques upsell pour la réponse
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = (
                        articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
                    )
                    
                    # Déterminer si c'était un ajout ou une mise à jour
                    message = (
                        "Article ajouté avec succès"
                        if not panier_existant
                        else f"Quantité mise à jour ({panier.quantite})"
                    )
                    
                    # Préparer les données de l'article pour le frontend
                    article_data = {
                        "panier_id": panier.id,
                        "nom": article.nom,
                        "reference": article.reference,
                        "couleur_fr": variante.couleur if variante else (article.couleur or ""),
                        "couleur_ar": variante.couleur if variante else (article.couleur or ""),
                        "pointure": variante.pointure if variante else (article.pointure or ""),
                        "quantite": panier.quantite,
                        "prix": panier.sous_total / panier.quantite,  # Prix unitaire
                        "sous_total": panier.sous_total,
                        "is_upsell": article.isUpsell,
                        "isUpsell": article.isUpsell,
                        "phase": article.phase,
                        "qte_disponible": article.get_total_qte_disponible(),
                        "has_promo_active": article.has_promo_active if hasattr(article, 'has_promo_active') else False,
                        "description": article.description or "",
                        "variante_info": f"{variante.couleur} - {variante.pointure}" if variante else None,
                    }

                    print(f"🔍 Préparation de la réponse JSON")
                    print(f"✅ Action add_article terminée avec succès, retour de la réponse JSON")
                    return JsonResponse(
                        {
                            "success": True,
                            "message": message,
                            "article_id": panier.id,
                            "total_commande": float(commande.total_cmd),
                            "nb_articles": commande.paniers.count(),
                            "compteur": commande.compteur,
                            "was_update": panier_existant is not None,
                            "new_quantity": panier.quantite,
                            "article_data": article_data,
                            "articles_count": commande.paniers.count(),
                            "sous_total_articles": float(
                                sum(p.sous_total for p in commande.paniers.all())
                            ),
                            "articles_upsell": articles_upsell.count(),
                            "quantite_totale_upsell": total_quantite_upsell,
                        }
                    )
                    
                except Article.DoesNotExist:
                    print(f"❌ Article non trouvé: {article_id}")
                    return JsonResponse(
                        {"success": False, "error": "Article non trouvé"}
                    )
                except (ValueError, TypeError) as e:
                    print(f"❌ Erreur de type dans l'action add_article: {str(e)}")
                    return JsonResponse({"success": False, "error": f"Erreur de type: {str(e)}"})
                except Exception as e:
                    print(f"❌ Erreur générale dans l'action add_article: {str(e)}")
                    import traceback
                    print(f"❌ Traceback: {traceback.format_exc()}")
                    return JsonResponse({"success": False, "error": f"Erreur lors de l'ajout: {str(e)}"})
            
            elif action == "replace_article":
                # Remplacer un article existant
                from article.models import Article
                from commande.models import Panier
                
                ancien_article_id = request.POST.get("ancien_article_id")
                nouvel_article_id = request.POST.get("nouvel_article_id")
                nouvelle_quantite = int(request.POST.get("nouvelle_quantite", 1))
                
                try:
                    # Supprimer l'ancien panier et décrémenter le compteur
                    ancien_panier = Panier.objects.get(
                        id=ancien_article_id, commande=commande
                    )
                    ancien_article = ancien_panier.article
                    
                    # Sauvegarder les infos avant suppression
                    ancien_etait_upsell = ancien_article.isUpsell
                    
                    # Supprimer l'ancien panier
                    ancien_panier.delete()
                    
                    # Créer le nouveau panier
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    
                    # Recalculer le compteur après remplacement (logique de confirmation)
                    total_quantite_upsell = (
                        commande.paniers.filter(article__isUpsell=True).aggregate(
                            total=Sum("quantite")
                        )["total"]
                        or 0
                    )
                    
                    # Ajouter la quantité si le nouvel article est upsell
                    if nouvel_article.isUpsell:
                        total_quantite_upsell += nouvelle_quantite
                    
                    # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                    if total_quantite_upsell >= 2:
                        commande.compteur = total_quantite_upsell - 1
                    else:
                        commande.compteur = 0
                    
                    commande.save()
                    
                    # Recalculer TOUS les articles de la commande avec le nouveau compteur
                    commande.recalculer_totaux_upsell()
                    
                    # Calculer le sous-total selon le compteur de la commande
                    from commande.templatetags.commande_filters import (
                        get_prix_upsell_avec_compteur,
                    )

                    prix_unitaire = get_prix_upsell_avec_compteur(
                        nouvel_article, commande.compteur
                    )
                    sous_total = prix_unitaire * nouvelle_quantite
                    
                    nouveau_panier = Panier.objects.create(
                        commande=commande,
                        article=nouvel_article,
                        quantite=nouvelle_quantite,
                        sous_total=float(sous_total),
                    )
                    
                    # Recalculer le total de la commande avec frais de livraison
                    total_commande = (
                        commande.paniers.aggregate(total=Sum("sous_total"))["total"]
                        or 0
                    )
                    frais_livraison = (
                        commande.ville.frais_livraison if commande.ville else 0
                    )
                    commande.total_cmd = float(
                        total_commande
                    )  # + float(frais_livraison)
                    commande.save()
                    
                    # Calculer les statistiques upsell pour la réponse
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = (
                        articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
                    )

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Article remplacé avec succès",
                            "nouvel_article_id": nouveau_panier.id,
                            "total_commande": float(commande.total_cmd),
                            "nb_articles": commande.paniers.count(),
                            "compteur": commande.compteur,
                            "articles_upsell": articles_upsell.count(),
                            "quantite_totale_upsell": total_quantite_upsell,
                            "sous_total_articles": float(commande.sous_total_articles),
                        }
                    )
                    
                except Panier.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Article original non trouvé"}
                    )
                except Article.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Nouvel article non trouvé"}
                    )
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "delete_article":
                # Supprimer un article
                from commande.models import Panier
                
                panier_id = request.POST.get("panier_id")
                
                try:
                    panier = Panier.objects.get(id=panier_id, commande=commande)
                    
                    # Sauvegarder l'info avant suppression
                    etait_upsell = panier.article.isUpsell
                    
                    # Supprimer l'article
                    panier.delete()
                    
                    # Recalculer le compteur après suppression (logique de confirmation)
                    if etait_upsell:
                        # Compter la quantité totale d'articles upsell restants (après suppression)
                        total_quantite_upsell = (
                            commande.paniers.filter(article__isUpsell=True).aggregate(
                                total=Sum("quantite")
                            )["total"]
                            or 0
                        )
                        
                        # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        
                        commande.save()
                        
                        # Recalculer TOUS les articles de la commande avec le nouveau compteur
                        commande.recalculer_totaux_upsell()
                    
                    # Recalculer le total de la commande avec frais de livraison
                    total_commande = (
                        commande.paniers.aggregate(total=Sum("sous_total"))["total"]
                        or 0
                    )
                    frais_livraison = (
                        commande.ville.frais_livraison if commande.ville else 0
                    )
                    commande.total_cmd = float(
                        total_commande
                    )  # + float(frais_livraison)
                    commande.save()
                    
                    # Calculer les statistiques upsell pour la réponse
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = (
                        articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
                    )

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Article supprimé avec succès",
                            "total_commande": float(commande.total_cmd),
                            "nb_articles": commande.paniers.count(),
                            "compteur": commande.compteur,
                            "articles_upsell": articles_upsell.count(),
                            "quantite_totale_upsell": total_quantite_upsell,
                            "sous_total_articles": float(commande.sous_total_articles),
                        }
                    )
                    
                except Panier.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": "Article non trouvé"}
                    )
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "update_operation":
                # Mettre à jour une opération existante
                try:
                    from commande.models import Operation
                    import logging

                    logger = logging.getLogger(__name__)
                    
                    operation_id = request.POST.get("operation_id")
                    nouveau_commentaire = request.POST.get(
                        "nouveau_commentaire", ""
                    ).strip()
                    
                    if not operation_id or not nouveau_commentaire:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "ID opération et commentaire requis",
                            }
                        )
                    
                    
                    
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Opération mise à jour avec succès",
                            "operation_id": operation_id,
                            "nouveau_commentaire": nouveau_commentaire,
                        }
                    )
                    
                
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "add_operation":
                # Ajouter une nouvelle opération
                try:
                
                    
                    type_operation = request.POST.get("type_operation", "").strip()
                    commentaire = request.POST.get("commentaire", "").strip()
                    
                    if not type_operation or not commentaire:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "Type d'opération et commentaire requis",
                            }
                        )
                    
                 

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Opération ajoutée avec succès",
                            "operation_id": operation.id,
                            "type_operation": type_operation,
                            "commentaire": commentaire,
                        }
                    )
                    
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "modifier_quantites_multiple":
                # Modifier plusieurs quantités d'articles en une fois
                try:
                    from commande.models import Panier
                    import json
                    
                    modifications_json = request.POST.get("modifications", "[]")
                    modifications = json.loads(modifications_json)
                    
                    if not modifications:
                        return JsonResponse(
                            {"success": False, "error": "Aucune modification fournie"}
                        )
                    
                    # Appliquer les modifications
                    for mod in modifications:
                        panier_id = mod.get("panier_id")
                        nouvelle_quantite = mod.get("nouvelle_quantite", 0)
                        
                        try:
                            panier = Panier.objects.get(id=panier_id, commande=commande)
                            
                            if nouvelle_quantite <= 0:
                                # Supprimer l'article si quantité = 0
                                panier.delete()
                            else:
                                # Mettre à jour la quantité et le sous-total
                                panier.quantite = nouvelle_quantite
                                panier.sous_total = float(
                                    panier.article.prix_unitaire * nouvelle_quantite
                                )
                                panier.save()
                                
                        except Panier.DoesNotExist:
                            continue  # Ignorer les paniers non trouvés
                    
                    # Recalculer le total de la commande
                    total_commande = (
                        commande.paniers.aggregate(total=Sum("sous_total"))["total"]
                        or 0
                    )
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                

                    return JsonResponse(
                        {
                            "success": True,
                            "message": f"{len(modifications)} quantité(s) modifiée(s) avec succès",
                            "total_commande": float(commande.total_cmd),
                            "nb_articles": commande.paniers.count(),
                        }
                    )
                    
                except json.JSONDecodeError:
                    return JsonResponse(
                        {"success": False, "error": "Format de données invalide"}
                    )
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "modifier_quantite_directe":
                # Modifier directement la quantité d'un article
                try:
                    from commande.models import Panier
                    
                    panier_id = request.POST.get("panier_id")
                    nouvelle_quantite = int(request.POST.get("nouvelle_quantite", 0))
                    
                    print(
                        f"🔄 Modification quantité directe - Panier ID: {panier_id}, Nouvelle quantité: {nouvelle_quantite}"
                    )
                    
                    if nouvelle_quantite < 0:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "La quantité ne peut pas être négative",
                            }
                        )
                    
                    try:
                        panier = Panier.objects.get(id=panier_id, commande=commande)
                        ancienne_quantite = panier.quantite
                        nouveau_sous_total = 0
                        
                        print(
                            f"📦 Article trouvé: {panier.article.nom}, Ancienne quantité: {ancienne_quantite}"
                        )
                        
                        # Vérifier que le panier appartient bien à cette commande
                        if panier.commande.id != commande.id:
                            print(
                                f"❌ ERREUR: Le panier {panier_id} n'appartient pas à la commande {commande.id}"
                            )
                            return JsonResponse(
                                {
                                    "success": False,
                                    "error": "Article non trouvé dans cette commande",
                                }
                            )
                        
                        if nouvelle_quantite == 0:
                            # Supprimer l'article si quantité = 0
                            panier.delete()
                            message = "Article supprimé avec succès"
                        else:
                            # Mettre à jour la quantité et le sous-total avec la logique complète de prix
                            panier.quantite = nouvelle_quantite
                            
                            # Recalculer le compteur si c'est un article upsell
                            if panier.article.isUpsell:
                                # Sauvegarder d'abord la nouvelle quantité
                                panier.save()
                                
                                # Compter la quantité totale d'articles upsell après modification
                                total_quantite_upsell = (
                                    commande.paniers.filter(
                                        article__isUpsell=True
                                    ).aggregate(total=Sum("quantite"))["total"]
                                    or 0
                                )

                                print(
                                    f"🔄 Calcul du compteur upsell: total_quantite_upsell = {total_quantite_upsell}"
                                )
                                
                                # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                                if total_quantite_upsell >= 2:
                                    commande.compteur = total_quantite_upsell - 1
                                else:
                                    commande.compteur = 0
                                
                                print(
                                    f"✅ Nouveau compteur calculé: {commande.compteur}"
                                )
                                commande.save()
                                
                                # Recalculer TOUS les articles de la commande avec le nouveau compteur
                                commande.recalculer_totaux_upsell()
                            else:
                                # Pour les articles normaux, mettre à jour la quantité et calculer le sous-total
                                from commande.templatetags.commande_filters import (
                                    get_prix_upsell_avec_compteur,
                                )

                                prix_unitaire = get_prix_upsell_avec_compteur(
                                    panier.article, commande.compteur
                                )
                                panier.quantite = nouvelle_quantite
                                panier.sous_total = float(
                                    prix_unitaire * nouvelle_quantite
                                )
                                panier.save()
                            
                            nouveau_sous_total = panier.sous_total
                            message = "Quantité modifiée avec succès"
                            
                            print(
                                f"✅ Quantité mise à jour: {ancienne_quantite} → {nouvelle_quantite}, Nouveau sous-total: {nouveau_sous_total}"
                            )
                            
                            # Vérifier que la mise à jour a bien été sauvegardée
                            panier.refresh_from_db()
                            if panier.quantite != nouvelle_quantite:
                                print(
                                    f"❌ ERREUR: La quantité n'a pas été sauvegardée correctement. Attendu: {nouvelle_quantite}, Actuel: {panier.quantite}"
                                )
                            else:
                                print(
                                    f"✅ Vérification OK: Quantité sauvegardée: {panier.quantite}"
                                )
                            
                    except Panier.DoesNotExist:
                        return JsonResponse(
                            {"success": False, "error": "Article non trouvé"}
                        )
                    
                    # Recalculer le total de la commande avec frais de livraison
                    total_articles = (
                        commande.paniers.aggregate(total=Sum("sous_total"))["total"]
                        or 0
                    )
                    frais_livraison = (
                        commande.ville.frais_livraison if commande.ville else 0
                    )
                    commande.total_cmd = float(
                        total_articles
                    )  # + float(frais_livraison)
                    commande.save()
                    
                    # Calculer les statistiques upsell pour la réponse
                    articles_upsell = commande.paniers.filter(article__isUpsell=True)
                    total_quantite_upsell = (
                        articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
                    )
                    
                   

                    return JsonResponse(
                        {
                            "success": True,
                            "message": message,
                            "sous_total": float(nouveau_sous_total),
                            "sous_total_articles": float(total_articles),
                            "total_commande": float(commande.total_cmd),
                            "frais_livraison": float(frais_livraison),
                            "nb_articles": commande.paniers.count(),
                            "compteur": commande.compteur,
                            "articles_upsell": articles_upsell.count(),
                            "quantite_totale_upsell": total_quantite_upsell,
                        }
                    )
                    
                except ValueError:
                    return JsonResponse(
                        {"success": False, "error": "Quantité invalide"}
                    )
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            elif action == "update_commande_info":
                # Mettre à jour les informations de base de la commande
                try:
                    # Récupérer les données du formulaire
                    nouvelle_adresse = request.POST.get("adresse", "").strip()
                    nouvelle_ville_id = request.POST.get("ville_id")
                    
                    # Mettre à jour l'adresse
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    
                    # Mettre à jour la ville si fournie
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            return JsonResponse(
                                {"success": False, "error": "Ville non trouvée"}
                            )
                    
                    commande.save()
                    
                   

                    messages.success(
                        request, f"Commande {commande.id_yz} mise à jour avec succès."
                    )
                    return redirect("Prepacommande:detail_prepa", pk=commande.id)
                    
                except Exception as e:
                    return JsonResponse({"success": False, "error": str(e)})
            
            else:
                # Traitement du formulaire principal (non-AJAX)
                with transaction.atomic():
                    # Mettre à jour les informations du client
                    client = commande.client
                    client.nom = request.POST.get("client_nom", client.nom).strip()
                    client.prenom = request.POST.get(
                        "client_prenom", client.prenom
                    ).strip()
                    client.numero_tel = request.POST.get(
                        "client_telephone", client.numero_tel
                    ).strip()
                    client.save()

                    # Mettre à jour les informations de base de la commande
                    nouvelle_adresse = request.POST.get("adresse", "").strip()
                    nouvelle_ville_id = request.POST.get("ville_id")
                    
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            messages.error(request, "Ville sélectionnée non trouvée.")
                            return redirect("Prepacommande:liste_prepa")
                    
                    commande.save()

                    # Créer une opération pour consigner la modification
              

                    messages.success(
                        request,
                        f"Les modifications de la commande {commande.id_yz} ont été enregistrées avec succès.",
                    )
                    return redirect("Prepacommande:detail_prepa", pk=commande.id)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            return redirect("Prepacommande:liste_prepa")
    
    # Récupérer les données pour l'affichage
    paniers = commande.paniers.all().select_related("article")
    operations = (
        commande.operations.all()
        .select_related("operateur")
        .order_by("-date_operation")
    )
    villes = Ville.objects.all().order_by("nom")
    
    # Calculer le total des articles
    total_articles = sum(panier.sous_total for panier in paniers)
    
    
    # Initialiser les variables pour les cas de livraison partielle/renvoi
    articles_livres = []
    articles_renvoyes = []
    is_commande_livree_partiellement = False
    commande_renvoi_obj = None  # Variable pour la commande de renvoi trouvée
    commande_originale_obj = None  # Variable pour la commande originale trouvée
    etat_articles_renvoyes = (
        {}
    )  # Dictionnaire pour stocker l'état des articles renvoyés (article_id -> etat)
    operation_livraison_partielle_source = (
        None  # Opération source pour les détails de livraison partielle
    )

    # Récupérer l'état actuel de la commande
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    etat_precedent = None
    
    if etat_actuel:
        # Trouver l'état précédent
        etats_precedents = commande.etats.all().order_by("-date_debut")
        for etat in etats_precedents:
            if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                if etat.enum_etat.libelle not in ["À imprimer", "En préparation"]:
                    etat_precedent = etat
                    break
    
    # NOUVELLE LOGIQUE POUR DÉTECTER LA LIVRAISON PARTIELLE ET LES ARTICLES RENVOYÉS
    # Une commande est considérée comme "livrée partiellement" dans le contexte de modification
    # si elle-même a été livrée partiellement ou si c'est une commande de RENVOI associée à une livraison partielle.
    
    if commande.num_cmd and commande.num_cmd.startswith("RENVOI-"):
        # C'est une commande de renvoi. On cherche la commande originale.
        num_cmd_original = commande.num_cmd.replace("RENVOI-", "")
        commande_originale_obj = Commande.objects.filter(
            num_cmd=num_cmd_original, client=commande.client
        ).first()
        
        if commande_originale_obj:
            # Vérifier si la commande originale a bien été livrée partiellement
            if commande_originale_obj.etats.filter(
                enum_etat__libelle="Livrée Partiellement"
            ).exists():
                is_commande_livree_partiellement = True
                operation_livraison_partielle_source = (
                    commande_originale_obj.operations.filter(
                        type_operation="LIVRAISON_PARTIELLE"
                    )
                    .order_by("-date_operation")
                    .first()
                )
                commande_renvoi_obj = commande  # Dans ce cas, la commande actuelle est la commande de renvoi

    elif etat_actuel and etat_actuel.enum_etat.libelle == "Livrée Partiellement":
        # La commande actuelle est l'originale qui a été livrée partiellement
        is_commande_livree_partiellement = True
        operation_livraison_partielle_source = (
            commande.operations.filter(type_operation="LIVRAISON_PARTIELLE")
            .order_by("-date_operation")
            .first()
        )
        # Chercher une commande de renvoi associée si elle existe
        commande_renvoi_obj = Commande.objects.filter(
            num_cmd__startswith=f"RENVOI-{commande.num_cmd}", client=commande.client
        ).first()

    # Si une opération de livraison partielle est trouvée, extraire les états des articles renvoyés
    if operation_livraison_partielle_source:
        try:
            details = json.loads(operation_livraison_partielle_source.conclusion)
            if "recap_articles_renvoyes" in details:
                for item in details["recap_articles_renvoyes"]:
                    etat_articles_renvoyes[item["article_id"]] = item["etat"]
            
            # Populer articles_livres à partir de la conclusion de l'opération de livraison partielle
            if "articles_livres" in details:
                for article_livre in details["articles_livres"]:
                    article_obj = Article.objects.filter(
                        id=article_livre.get("article_id")
                    ).first()
                    if article_obj:
                        articles_livres.append(
                            {
                                "article": article_obj,
                                "quantite_livree": article_livre.get("quantite", 0),
                                "prix": article_obj.prix_unitaire,
                                "sous_total": article_obj.prix_unitaire
                                * article_livre.get("quantite", 0),
                            }
                        )
        except Exception as e:
            print(
                f"DEBUG: Erreur lors du parsing des détails de l'opération de livraison partielle: {e}"
            )
            pass



    # Populer articles_renvoyes si c'est une commande de renvoi ou si elle a une commande de renvoi associée
    if is_commande_livree_partiellement:
        # Si la commande actuelle est une commande de renvoi (celle que nous modifions)
        if commande.num_cmd and commande.num_cmd.startswith("RENVOI-"):
            # Les paniers de la commande actuelle sont les articles renvoyés
            for panier_renvoi in paniers:
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id)
                if etat is None:
                    etat = "inconnu"
                    print(
                        f"ALERTE: État inconnu pour l'article ID {panier_renvoi.article.id} dans la commande {commande.id_yz}"
                    )
                articles_renvoyes.append(
                    {
                        "article": panier_renvoi.article,
                        "quantite": panier_renvoi.quantite,
                        "prix": panier_renvoi.article.prix_unitaire,
                        "sous_total": panier_renvoi.sous_total,
                        "etat": etat,
                    }
                )
        # Si la commande actuelle est la commande originale livrée partiellement (Cas 1 initial)
        elif commande_renvoi_obj:
            # Les paniers de la commande de renvoi associée sont les articles renvoyés
            for panier_renvoi in commande_renvoi_obj.paniers.all():
                etat = etat_articles_renvoyes.get(panier_renvoi.article.id)
                if etat is None:
                    etat = "inconnu"
                    print(
                        f"ALERTE: État inconnu pour l'article ID {panier_renvoi.article.id} dans la commande {commande_renvoi_obj.id_yz}"
                    )
                articles_renvoyes.append(
                    {
                        "article": panier_renvoi.article,
                        "quantite": panier_renvoi.quantite,
                        "prix": panier_renvoi.article.prix_unitaire,
                        "sous_total": panier_renvoi.sous_total,
                        "etat": etat,
                    }
                )
    
    # DEBUG: Afficher le contenu de articles_renvoyes après peuplement
    print(
        f"DEBUG (modifier_commande_prepa): articles_renvoyes APRES POPULATION: {articles_renvoyes}"
    )

    # Créer un map pour accéder facilement aux articles renvoyés par leur ID dans le template
    # articles_renvoyes_map = {item['article'].id: item for item in articles_renvoyes}

    # Pour les articles livrés, on lit l'opération de livraison partielle sur la commande originale
    # C'est pertinent uniquement si la commande actuelle est la commande de renvoi
    # if is_commande_livree_partiellement and commande.num_cmd and commande.num_cmd.startswith('RENVOI-') and commande_originale_obj:
    #     operation_livraison_partielle_for_livres = commande_originale_obj.operations.filter(
    #         type_operation='LIVRAISON_PARTIELLE'
    #     ).order_by('-date_operation').first()
    #     if operation_livraison_partielle_for_livres:
    #         try:
    #             details = json.loads(operation_livraison_partielle_for_livres.conclusion)
    #             if 'articles_livres' in details:
    #                 for article_livre in details['articles_livres']:
    #                     article = Article.objects.filter(id=article_livre.get('article_id')).first()
    #                     if article:
    #                         articles_livres.append({
    #                             'article': article,
    #                             'quantite_livree': article_livre.get('quantite', 0),
    #                             'prix': article.prix_unitaire,
    #                             'sous_total': article.prix_unitaire * article_livre.get('quantite', 0)
    #                         })
    #         except Exception:
    #             pass

    context = {
        "page_title": "Modifier Commande " + str(commande.id_yz),
        "page_subtitle": "Modification des détails de la commande en préparation",
        "commande": commande,
        "paniers": paniers,
        "villes": villes,
        "total_articles": total_articles,
        "is_commande_renvoyee": is_commande_renvoyee,
        
        "is_commande_livree_partiellement": is_commande_livree_partiellement,
        "articles_livres": articles_livres,
        "articles_renvoyes": articles_renvoyes,
        # Variables de debug/informations supplémentaires
        "commande_originale": commande_originale_obj,
        "commande_renvoi": commande_renvoi_obj,
        "etat_articles_renvoyes": etat_articles_renvoyes,
        # 'articles_renvoyes_map': articles_renvoyes_map, # Retiré car plus nécessaire
    }
    
    # Gestion d'erreur pour les requêtes AJAX non traitées
    if request.method == "POST":
        action = request.POST.get("action")
        if action and action not in ["add_article", "delete_article", "update_quantity", "replace_article", "update_operation", "add_operation", "update_commande_info"]:
            print(f"⚠️ Action non reconnue: {action}")
            return JsonResponse({"success": False, "message": f"Action non reconnue: {action}"})
        
        # Si c'est une action AJAX mais qu'aucune réponse JSON n'a été retournée, retourner une erreur
        if action and action in ["add_article", "delete_article", "update_quantity", "replace_article", "update_operation", "add_operation", "update_commande_info"]:
            print(f"⚠️ Action AJAX non traitée: {action}")
            return JsonResponse({"success": False, "message": f"Action non traitée: {action}"})
    
    print(f"🔍 ===== FIN modifier_commande_prepa (RENDER) =====")
    return render(request, "Prepacommande/modifier_commande.html", context)


@login_required
def ajouter_article_commande_prepa(request, commande_id):
    """Ajouter un article à la commande en préparation"""
  
    
    if request.method != 'POST':
        print("❌ Méthode non autorisée")
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer l'opérateur de préparation
        operateur = Operateur.objects.get(user=request.user, type_operateur="PREPARATION")
        print(f"✅ Opérateur trouvé: {operateur.id} - Type: {operateur.type_operateur}")
    except Operateur.DoesNotExist:
        print("❌ Profil d'opérateur de préparation non trouvé")
        return JsonResponse({'error': 'Profil d\'opérateur de préparation non trouvé.'}, status=403)
    
    try:
        with transaction.atomic():
            print("🔧 Début de la transaction atomique")
            commande = Commande.objects.select_for_update().get(id=commande_id)
            print(f"✅ Commande trouvée: {commande.id} - ID YZ: {commande.id_yz}")
            
            # Vérifier que la commande est affectée à cet opérateur pour la préparation
            etat_preparation = commande.etats.filter(
                Q(enum_etat__libelle="À imprimer") | Q(enum_etat__libelle="En préparation"),
                operateur=operateur,
                date_fin__isnull=True,
            ).first()
            
            if not etat_preparation:
                print("❌ Commande non affectée à l'opérateur pour la préparation")
                return JsonResponse({'error': 'Cette commande ne vous est pas affectée pour la préparation.'}, status=403)
            
            print(f"✅ État de préparation trouvé: {etat_preparation.enum_etat.libelle}")
            
            # Support both parameter names for backward compatibility
            article_id = request.POST.get("articleId") or request.POST.get("article_id")
            quantite = int(request.POST.get("quantite", 1))
            variante_id = request.POST.get("varianteId") or request.POST.get("variante_id")

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
            
            # Handle variant if provided
            variante_obj = None
            if variante_id:
                try:
                    from article.models import Variante
                    variante_obj = Variante.objects.get(id=int(variante_id), article=article)
                    print("[AJOUT VARIANTE] variante trouvée:", {
                        'id': variante_obj.id,
                        'couleur': getattr(variante_obj, 'couleur', None),
                        'pointure': getattr(variante_obj, 'pointure', None),
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
            panier_existant = Panier.objects.filter(
                commande=commande, article=article
            ).first()
            
            print("[AJOUT VARIANTE] filtre panier:", {
                'commande': commande.id,
                'article': article.id,
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
                panier = Panier.objects.create(
                    commande=commande,
                    article=article,
                    quantite=quantite,
                    sous_total=0,
                )
                print(f"[AJOUT VARIANTE] ➕ nouveau panier créé id={panier.id}, article={article.id}, quantite={quantite}")
            
            # Si c'était une variante, stocker l'information de la variante
            if variante_obj:
                panier.commentaire = f"Variante sélectionnée: {variante_obj.couleur} - {variante_obj.pointure}"
                panier.save()
                print(f"📝 Variante stockée: {variante_obj.couleur} - {variante_obj.pointure}")
            
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
            message = 'Article ajouté avec succès' if not panier_existant else f'Quantité mise à jour ({panier.quantite})'
            
            # Préparer les données de l'article pour le frontend
            article_data = {
                'panier_id': panier.id,
                'nom': article.nom,
                'reference': article.reference,
                'couleur_fr': variante_obj.couleur if variante_obj else (article.couleur or ""),
                'couleur_ar': variante_obj.couleur if variante_obj else (article.couleur or ""),
                'pointure': variante_obj.pointure if variante_obj else (article.pointure or ""),
                'quantite': panier.quantite,
                'prix': panier.sous_total / panier.quantite,  # Prix unitaire
                'sous_total': panier.sous_total,
                'is_upsell': article.isUpsell,
                'isUpsell': article.isUpsell,
                'phase': article.phase,
                'qte_disponible': article.get_total_qte_disponible(),
                'has_promo_active': article.has_promo_active if hasattr(article, 'has_promo_active') else False,
                'description': article.description or "",
                'variante_info': f"{variante_obj.couleur} - {variante_obj.pointure}" if variante_obj else None,
            }
            
            response_data = {
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
            }
            
            print("✅ ===== SUCCÈS ajouter_article_commande_prepa =====")
            print(f"📦 Réponse: {response_data}")
            
            return JsonResponse(response_data)
            
    except Article.DoesNotExist:
        print("❌ Article non trouvé")
        return JsonResponse({'success': False, 'error': 'Article non trouvé'}, status=404)
    except Exception as e:
        print(f"❌ ===== ERREUR ajouter_article_commande_prepa =====")
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': f'Erreur interne: {str(e)}'}, status=500)


@login_required
def api_articles_disponibles_prepa(request):
    """API pour récupérer les articles disponibles pour les opérateurs de préparation"""
    from article.models import Article
    
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse({"success": False, "message": "Accès non autorisé"})
    
    search_query = request.GET.get("search", "")
    filter_type = request.GET.get("filter", "tous")
    
    # Récupérer les articles actifs
    articles = Article.objects.filter(actif=True)
    
    # Appliquer les filtres selon le type
    if filter_type == "disponible":
        # Filtrer les articles qui ont au moins une variante avec stock > 0
        articles = articles.filter(variantes__qte_disponible__gt=0, variantes__actif=True).distinct()
    elif filter_type == "upsell":
        articles = articles.filter(isUpsell=True)
    elif filter_type == "liquidation":
        articles = articles.filter(phase="LIQUIDATION")
    elif filter_type == "test":
        articles = articles.filter(phase="EN_TEST")
    
    # Recherche textuelle
    if search_query:
        articles = articles.filter(
            Q(nom__icontains=search_query)
            | Q(reference__icontains=search_query)
            | Q(couleur__icontains=search_query)
            | Q(pointure__icontains=search_query)
            | Q(description__icontains=search_query)
        )
    
    # Compter les articles par type pour les statistiques
    stats = {
        "tous": Article.objects.filter(actif=True).count(),
        "disponible": Article.objects.filter(actif=True, variantes__qte_disponible__gt=0, variantes__actif=True).distinct().count(),
        "upsell": Article.objects.filter(actif=True, isUpsell=True).count(),
        "liquidation": Article.objects.filter(actif=True, phase="LIQUIDATION").count(),
        "test": Article.objects.filter(actif=True, phase="EN_TEST").count(),
    }
    
    # Compter les articles en promotion en utilisant une approche différente
    # Chercher les articles qui ont un prix actuel différent du prix unitaire
    articles_promo_count = Article.objects.filter(
        actif=True, prix_actuel__lt=F("prix_unitaire")
    ).count()
    stats["promo"] = articles_promo_count
    
    # Filtrer les articles en promotion si nécessaire
    if filter_type == "promo":
        articles = articles.filter(prix_actuel__lt=F("prix_unitaire"))
    
    # Limiter les résultats
    articles = articles[:50]
    
    articles_data = []
    for article in articles:
        # Prix à afficher (prix actuel si différent du prix unitaire)
        prix_affichage = float(article.prix_actuel or article.prix_unitaire)
        prix_original = float(article.prix_unitaire)
        has_reduction = prix_affichage < prix_original
        
        # Déterminer le type d'article pour l'affichage
        article_type = "normal"
        type_icon = "fas fa-box"
        type_color = "text-gray-600"
        
        if article.isUpsell:
            article_type = "upsell"
            type_icon = "fas fa-arrow-up"
            type_color = "text-purple-600"
        elif article.phase == "LIQUIDATION":
            article_type = "liquidation"
            type_icon = "fas fa-money-bill-wave"
            type_color = "text-red-600"
        elif article.phase == "EN_TEST":
            article_type = "test"
            type_icon = "fas fa-flask"
            type_color = "text-yellow-600"
        
        # Vérifier si l'article est en promotion (prix actuel < prix unitaire)
        if has_reduction:
            article_type = "promo"
            type_icon = "fas fa-fire"
            type_color = "text-orange-600"

        # Récupérer les variantes de l'article
        variantes_data = []
        for variante in article.variantes.filter(actif=True):
            variantes_data.append({
                "id": variante.id,
                "couleur": str(variante.couleur) if variante.couleur else "",
                "pointure": str(variante.pointure) if variante.pointure else "",
                "prix_actuel": float(variante.prix_actuel or variante.prix_unitaire),
                "prix": float(variante.prix_unitaire),
                "qte_disponible": variante.qte_disponible,
                "stock": variante.qte_disponible,
                "reference_variante": variante.reference_variante or "",
                "actif": variante.actif,
            })

        articles_data.append(
            {
                "id": article.id,
                "nom": article.nom,
                "reference": article.reference or "",
                "couleur": str(article.couleur) if article.couleur else "",
                "pointure": str(article.pointure) if article.pointure else "",
                "description": article.description or "",
                "prix": prix_affichage,
                "prix_original": prix_original,
                "has_reduction": has_reduction,
                "reduction_pourcentage": round(
                    ((prix_original - prix_affichage) / prix_original) * 100, 0
                )
                if has_reduction
                else 0,
                "qte_disponible": article.get_total_qte_disponible(),
                "article_type": article_type,
                "type_icon": type_icon,
                "type_color": type_color,
                "phase": article.phase,
                "isUpsell": article.isUpsell,
                "display_text": f"{article.nom} - {str(article.couleur) if article.couleur else ''} - {str(article.pointure) if article.pointure else ''} ({prix_affichage} DH)",
                "variantes_all": variantes_data,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "articles": articles_data,
            "stats": stats,
            "filter_applied": filter_type,
        }
    )


@login_required
def api_panier_commande_prepa(request, commande_id):
    """API pour récupérer le panier d'une commande pour les opérateurs de préparation"""
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse({"success": False, "message": "Accès non autorisé"})
    
    # Récupérer la commande
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({"success": False, "message": "Commande non trouvée"})
    
    # Vérifier que la commande est affectée à cet opérateur
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle="À imprimer") | Q(enum_etat__libelle="En préparation"),
        operateur=operateur,
        date_fin__isnull=True,
    ).first()
    
    if not etat_preparation:
        return JsonResponse({"success": False, "message": "Commande non affectée"})
    
    # Récupérer les paniers avec les variantes
    paniers = commande.paniers.all().select_related(
        "article",
        "variante",
        "variante__couleur",
        "variante__pointure"
    )

    paniers_data = []
    for panier in paniers:
        # Récupérer les informations de variante
        couleur = ""
        pointure = ""
        if panier.variante:
            if panier.variante.couleur:
                couleur = panier.variante.couleur.nom
            if panier.variante.pointure:
                pointure = panier.variante.pointure.pointure

        # Construire le texte d'affichage
        display_parts = [panier.article.nom]
        if couleur:
            display_parts.append(couleur)
        if pointure:
            display_parts.append(pointure)
        display_text = " - ".join(display_parts)

        paniers_data.append(
            {
                "id": panier.id,
                "article_id": panier.article.id,
                "article_nom": panier.article.nom,
                "article_reference": panier.article.reference or "",
                "article_couleur": couleur,
                "article_pointure": pointure,
                "quantite": panier.quantite,
                "prix_unitaire": float(panier.article.prix_unitaire),
                "sous_total": float(panier.sous_total),
                "display_text": display_text,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "paniers": paniers_data,
            "total_commande": float(commande.total_cmd),
            "nb_articles": len(paniers_data),
        }
    )


    article = get_object_or_404(Article, pk=article_id)
    
    # Calculer la valeur totale du stock
    valeur_stock = (
        article.prix_actuel * article.qte_disponible if article.prix_actuel else 0
    )
    
    # Récupérer le dernier mouvement de stock pour cet article
    dernier_mouvement = article.mouvements.order_by("-date_mouvement").first()

    context = {
        "article": article,
        "valeur_stock": valeur_stock,
        "dernier_mouvement": dernier_mouvement,
        "page_title": f"Détail de l'article : {article.nom}",
        "page_subtitle": "Informations complètes sur l'article",
    }
    return render(request, "Prepacommande/stock/detail_article.html", context)


# === NOUVELLES FONCTIONNALITÉS : RÉPARTITION AUTOMATIQUE ===


def get_operateur_display_name(operateur):
    """Fonction helper pour obtenir le nom d'affichage d'un opérateur"""
    if not operateur:
        return "Opérateur inconnu"
    
    if hasattr(operateur, "nom_complet") and operateur.nom_complet:
        return operateur.nom_complet
    elif operateur.nom and operateur.prenom:
        return f"{operateur.prenom} {operateur.nom}"
    elif operateur.nom:
        return operateur.nom
    elif hasattr(operateur, "user") and operateur.user:
        return operateur.user.username
    else:
        return "Opérateur inconnu"



@login_required
def rafraichir_articles_commande_prepa(request, commande_id):
    """Rafraîchir la section des articles de la commande en préparation"""
    print(f"🔄 Rafraîchissement des articles pour la commande {commande_id}")
    
    try:
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse(
            {"error": "Profil d'opérateur de préparation non trouvé."}, status=403
        )
    
    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_preparation = commande.etats.filter(
            operateur=operateur,
            enum_etat__libelle__in=["En préparation", "À imprimer"],
            date_fin__isnull=True,
        ).first()
        
        if not etat_preparation:
            return JsonResponse(
                {"error": "Cette commande ne vous est pas affectée."}, status=403
            )
        
        # Générer le HTML directement pour éviter les erreurs de template
        paniers = commande.paniers.select_related(
            "article",
            "variante",
            "variante__couleur",
            "variante__pointure"
        ).all()
        html_rows = []

        for panier in paniers:
            # Utiliser le filtre Django pour calculer le prix selon la logique upsell
            from commande.templatetags.commande_filters import (
                get_prix_upsell_avec_compteur,
            )
            
            prix_calcule = get_prix_upsell_avec_compteur(
                panier.article, commande.compteur
            )
            
            # Déterminer l'affichage selon le type d'article
            if panier.article.isUpsell:
                prix_class = "text-orange-600"
                upsell_badge = f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-700 ml-2"><i class="fas fa-arrow-up mr-1"></i>Upsell</span>'
                
                # Déterminer le niveau d'upsell affiché
                if commande.compteur >= 4 and panier.article.prix_upsell_4 is not None:
                    niveau_upsell = 4
                elif (
                    commande.compteur >= 3 and panier.article.prix_upsell_3 is not None
                ):
                    niveau_upsell = 3
                elif (
                    commande.compteur >= 2 and panier.article.prix_upsell_2 is not None
                ):
                    niveau_upsell = 2
                elif (
                    commande.compteur >= 1 and panier.article.prix_upsell_1 is not None
                ):
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

            # Récupérer les informations de variante
            variante_html = ""
            if panier.variante:
                variante_parts = []
                if panier.variante.couleur:
                    variante_parts.append(f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"><i class="fas fa-palette mr-1"></i>{panier.variante.couleur.nom}</span>')
                if panier.variante.pointure:
                    variante_parts.append(f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"><i class="fas fa-ruler mr-1"></i>{panier.variante.pointure.pointure}</span>')
                if variante_parts:
                    variante_html = f'<div class="flex gap-1 mt-1">{"".join(variante_parts)}</div>'

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
                            </div>
                            {variante_html}
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
                        <i class="fas fa-trash mr-1"></i>Supprimer
                    </button>
                </td>
            </tr>
            """
            html_rows.append(html_row)
        
        html = "".join(html_rows)
        
        # Calculer les statistiques upsell
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        total_quantite_upsell = (
            articles_upsell.aggregate(total=Sum("quantite"))["total"] or 0
        )
        
        response_data = {
            "success": True,
            "html": html,
            "articles_count": commande.paniers.count(),
            "total_commande": float(commande.total_cmd),
            "sous_total_articles": float(commande.sous_total_articles),
            "compteur": commande.compteur,
            "articles_upsell": articles_upsell.count(),
            "quantite_totale_upsell": total_quantite_upsell,
        }

        print(
            f"✅ Rafraîchissement terminé - Articles: {response_data['articles_count']}, Compteur: {response_data['compteur']}"
        )
        return JsonResponse(response_data)
        
    except Commande.DoesNotExist:
        print(f"❌ Commande {commande_id} non trouvée")
        return JsonResponse({"error": "Commande non trouvée"}, status=404)
    except Exception as e:
        print(f"❌ Erreur lors du rafraîchissement: {str(e)}")
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": f"Erreur interne: {str(e)}"}, status=500)




@login_required
def api_prix_upsell_articles(request, commande_id):
    """API pour récupérer les prix upsell mis à jour des articles"""
    print(f"🔄 Récupération des prix upsell pour la commande {commande_id}")
    
    try:
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse(
            {"error": "Profil d'opérateur de préparation non trouvé."}, status=403
        )
    
    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_preparation = commande.etats.filter(
            operateur=operateur,
            enum_etat__libelle__in=["En préparation", "À imprimer"],
            date_fin__isnull=True,
        ).first()
        
        if not etat_preparation:
            return JsonResponse(
                {"error": "Cette commande ne vous est pas affectée."}, status=403
            )
        
        # Récupérer tous les articles du panier avec leurs prix mis à jour
        paniers = commande.paniers.select_related("article").all()
        prix_articles = {}
        
        for panier in paniers:
            # Utiliser le filtre Django pour calculer le prix selon la logique upsell
            from commande.templatetags.commande_filters import (
                get_prix_upsell_avec_compteur,
            )
            
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
            
            prix_calcule = get_prix_upsell_avec_compteur(
                panier.article, commande.compteur
            )
            print(f"   - prix_calcule: {prix_calcule}")
            
            # Convertir en float pour éviter les problèmes de sérialisation JSON
            prix_calcule = float(prix_calcule) if prix_calcule is not None else 0.0
            
            # Déterminer le type de prix et les informations
            if panier.article.isUpsell:
                prix_type = "upsell"
                
                # Déterminer le niveau d'upsell affiché
                if commande.compteur >= 4 and panier.article.prix_upsell_4 is not None:
                    niveau_upsell = 4
                elif (
                    commande.compteur >= 3 and panier.article.prix_upsell_3 is not None
                ):
                    niveau_upsell = 3
                elif (
                    commande.compteur >= 2 and panier.article.prix_upsell_2 is not None
                ):
                    niveau_upsell = 2
                elif (
                    commande.compteur >= 1 and panier.article.prix_upsell_1 is not None
                ):
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
                "prix": prix_calcule,
                "type": prix_type,
                "libelle": libelle,
                "icone": icone,
                "niveau_upsell": niveau_upsell,
                "is_upsell": panier.article.isUpsell,
                "sous_total": float(prix_calcule * panier.quantite),
            }

        return JsonResponse(
            {
                "success": True,
                "prix_articles": prix_articles,
                "compteur": commande.compteur,
                "message": f"Prix mis à jour pour {len(prix_articles)} articles",
            }
        )
        
    except Commande.DoesNotExist:
        return JsonResponse({"error": "Commande non trouvée."}, status=404)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des prix upsell: {e}")
        return JsonResponse({"error": f"Erreur serveur: {str(e)}"}, status=500)


@login_required
def api_changer_etat_commande(request, commande_id):
    """API pour changer l'état d'une commande (Collectée, Emballée)"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)
    
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse({"success": False, "error": "Accès non autorisé"}, status=403)
    
    try:
        # Récupérer les données de la requête
        data = json.loads(request.body)
        nouvel_etat = data.get('nouvel_etat')
        
        if not nouvel_etat:
            return JsonResponse({"success": False, "error": "Nouvel état non spécifié"}, status=400)
        
        # Vérifier que l'état est valide
        etats_valides = ['Collectée', 'Emballée']
        if nouvel_etat not in etats_valides:
            return JsonResponse({"success": False, "error": f"État invalide. États autorisés: {', '.join(etats_valides)}"}, status=400)
        
        # Récupérer la commande
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_actuel = commande.etats.filter(
            operateur=operateur,
            enum_etat__libelle__in=["En préparation", "À imprimer", "Collectée", "Emballée"],
            date_fin__isnull=True,
        ).first()
        
        if not etat_actuel:
            return JsonResponse({"success": False, "error": "Cette commande ne vous est pas affectée"}, status=403)
        
        # Vérifier la logique de transition d'état
        etat_actuel_libelle = etat_actuel.enum_etat.libelle
        
        if nouvel_etat == 'Collectée':
            if etat_actuel_libelle not in ['En préparation', 'À imprimer']:
                return JsonResponse({"success": False, "error": "Impossible de passer à 'Collectée' depuis cet état"}, status=400)
        elif nouvel_etat == 'Emballée':
            if etat_actuel_libelle not in ['Collectée']:
                return JsonResponse({"success": False, "error": "Impossible de passer à 'Emballée' depuis cet état"}, status=400)
        
        # Récupérer l'état correspondant
        try:
            nouvel_etat_enum = EnumEtatCmd.objects.get(libelle=nouvel_etat)
        except EnumEtatCmd.DoesNotExist:
            return JsonResponse({"success": False, "error": f"État '{nouvel_etat}' non trouvé dans le système"}, status=400)
        
        with transaction.atomic():
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=nouvel_etat_enum,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"État changé vers {nouvel_etat} par l'opérateur de préparation"
            )
             
        return JsonResponse({
            "success": True,
            "message": f"État changé avec succès vers '{nouvel_etat}'",
            "nouvel_etat": nouvel_etat,
            "commande_id": commande_id
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({"success": False, "error": "Commande non trouvée"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Données JSON invalides"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Erreur serveur: {str(e)}"}, status=500)


@login_required
def commandes_collectees(request):
    """Liste des commandes En préparation à collecter pour les opérateurs de préparation"""
    from django.core.paginator import Paginator

    try:
        operateur_profile = request.user.profil_operateur

        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(
                request,
                "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.",
            )
            return redirect("login")

    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Récupérer les commandes dans l'état "En préparation" affectées à cet opérateur
    commandes_affectees = (
        Commande.objects.filter(
            etats__enum_etat__libelle="En préparation",
            etats__operateur=operateur_profile,
            etats__date_fin__isnull=True,  # État actif (en cours)
        )
        .select_related("client", "ville", "ville__region")
        .prefetch_related("paniers__article", "etats")
        .distinct()
        .order_by("-etats__date_debut")
    )

    # Recherche
    search_query = request.GET.get("search", "").strip()
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(id_yz__icontains=search_query)
            | Q(num_cmd__icontains=search_query)
            | Q(client__nom__icontains=search_query)
            | Q(client__prenom__icontains=search_query)
            | Q(client__numero_tel__icontains=search_query)
        )

    # Ajouter l'état précédent pour chaque commande
    for commande in commandes_affectees:
        etats_commande = commande.etats.all().order_by("date_debut")

        # Trouver l'état actuel (En préparation)
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == "En préparation" and not etat.date_fin:
                etat_actuel = etat
                break

        # Trouver l'état précédent
        if etat_actuel:
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    etat_precedent = etat
                    break
            commande.etat_precedent = etat_precedent

    # Pagination
    items_per_page = request.GET.get("per_page", 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [5, 10, 25, 50, 100]:
            items_per_page = 10
    except (ValueError, TypeError):
        items_per_page = 10

    paginator = Paginator(commandes_affectees, items_per_page)
    page_number = request.GET.get("page", 1)
    commandes_affectees = paginator.get_page(page_number)

    # Statistiques
    stats = {
        "total_a_collecter": paginator.count,
        "valeur_totale": sum([cmd.total_cmd or 0 for cmd in paginator.object_list]),
    }

    context = {
        "commandes_affectees": commandes_affectees,
        "page_title": "Commandes à Collecter",
        "page_subtitle": "Liste des commandes en préparation - À marquer comme collectées",
        "stats": stats,
        "search_query": search_query,
        "items_per_page": items_per_page,
        "paginator": paginator,
        "current_page": commandes_affectees.number,
        "total_pages": paginator.num_pages,
        "has_previous": commandes_affectees.has_previous(),
        "has_next": commandes_affectees.has_next(),
        "previous_page_number": commandes_affectees.previous_page_number() if commandes_affectees.has_previous() else None,
        "next_page_number": commandes_affectees.next_page_number() if commandes_affectees.has_next() else None,
    }

    return render(request, "Prepacommande/commandes_collectees.html", context)


@login_required
def commandes_emballees(request):
    """Liste des commandes Collectées à emballer pour les opérateurs de préparation"""
    from django.core.paginator import Paginator

    try:
        operateur_profile = request.user.profil_operateur

        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(
                request,
                "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.",
            )
            return redirect("login")

    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect("login")

    # Récupérer les commandes dans l'état "Collectée" affectées à cet opérateur
    commandes_affectees = (
        Commande.objects.filter(
            etats__enum_etat__libelle="Collectée",
            etats__operateur=operateur_profile,
            etats__date_fin__isnull=True,  # État actif (en cours)
        )
        .select_related("client", "ville", "ville__region")
        .prefetch_related("paniers__article", "etats")
        .distinct()
        .order_by("-etats__date_debut")
    )

    # Recherche
    search_query = request.GET.get("search", "").strip()
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(id_yz__icontains=search_query)
            | Q(num_cmd__icontains=search_query)
            | Q(client__nom__icontains=search_query)
            | Q(client__prenom__icontains=search_query)
            | Q(client__numero_tel__icontains=search_query)
        )

    # Ajouter l'état précédent pour chaque commande
    for commande in commandes_affectees:
        etats_commande = commande.etats.all().order_by("date_debut")

        # Trouver l'état actuel (Collectée)
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == "Collectée" and not etat.date_fin:
                etat_actuel = etat
                break

        # Trouver l'état précédent
        if etat_actuel:
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    etat_precedent = etat
                    break
            commande.etat_precedent = etat_precedent

    # Pagination
    items_per_page = request.GET.get("per_page", 10)
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [5, 10, 25, 50, 100]:
            items_per_page = 10
    except (ValueError, TypeError):
        items_per_page = 10

    paginator = Paginator(commandes_affectees, items_per_page)
    page_number = request.GET.get("page", 1)
    commandes_affectees = paginator.get_page(page_number)

    # Statistiques
    stats = {
        "total_a_emballer": paginator.count,
        "valeur_totale": sum([cmd.total_cmd or 0 for cmd in paginator.object_list]),
    }

    context = {
        "commandes_affectees": commandes_affectees,
        "page_title": "Commandes à Emballer",
        "page_subtitle": "Liste des commandes collectées - À marquer comme emballées",
        "stats": stats,
        "search_query": search_query,
        "items_per_page": items_per_page,
        "paginator": paginator,
        "current_page": commandes_affectees.number,
        "total_pages": paginator.num_pages,
        "has_previous": commandes_affectees.has_previous(),
        "has_next": commandes_affectees.has_next(),
        "previous_page_number": commandes_affectees.previous_page_number() if commandes_affectees.has_previous() else None,
        "next_page_number": commandes_affectees.next_page_number() if commandes_affectees.has_next() else None,
    }

    return render(request, "Prepacommande/commandes_emballees.html", context)


@login_required
def api_bulk_changer_etat_commandes(request):
    """API pour changer l'état de plusieurs commandes en une seule fois"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Méthode non autorisée"}, status=405)

    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(
            user=request.user, type_operateur="PREPARATION"
        )
    except Operateur.DoesNotExist:
        return JsonResponse({"success": False, "error": "Accès non autorisé"}, status=403)

    try:
        # Récupérer les données de la requête
        data = json.loads(request.body)
        commande_ids = data.get('commande_ids', [])
        nouvel_etat = data.get('nouvel_etat')

        if not commande_ids:
            return JsonResponse({"success": False, "error": "Aucune commande sélectionnée"}, status=400)

        if not nouvel_etat:
            return JsonResponse({"success": False, "error": "Nouvel état non spécifié"}, status=400)

        # Vérifier que l'état est valide
        etats_valides = ['Collectée', 'Emballée']
        if nouvel_etat not in etats_valides:
            return JsonResponse({"success": False, "error": f"État invalide. États autorisés: {', '.join(etats_valides)}"}, status=400)

        # Récupérer l'état enum correspondant
        try:
            nouvel_etat_enum = EnumEtatCmd.objects.get(libelle=nouvel_etat)
        except EnumEtatCmd.DoesNotExist:
            return JsonResponse({"success": False, "error": f"État '{nouvel_etat}' non trouvé dans le système"}, status=400)

        updated_commandes = []
        errors = []

        # Traiter chaque commande
        for commande_id in commande_ids:
            try:
                with transaction.atomic():
                    # Récupérer la commande
                    commande = Commande.objects.get(id=commande_id)

                    # Vérifier que la commande est affectée à cet opérateur
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        enum_etat__libelle__in=["En préparation", "À imprimer", "Collectée", "Emballée"],
                        date_fin__isnull=True,
                    ).first()

                    if not etat_actuel:
                        errors.append(f"Commande {commande_id}: non affectée à cet opérateur")
                        continue

                    # Vérifier la logique de transition d'état
                    etat_actuel_libelle = etat_actuel.enum_etat.libelle

                    if nouvel_etat == 'Collectée':
                        if etat_actuel_libelle not in ['En préparation', 'À imprimer']:
                            errors.append(f"Commande {commande_id}: impossible de passer à 'Collectée' depuis l'état '{etat_actuel_libelle}'")
                            continue
                    elif nouvel_etat == 'Emballée':
                        if etat_actuel_libelle not in ['Collectée']:
                            errors.append(f"Commande {commande_id}: impossible de passer à 'Emballée' depuis l'état '{etat_actuel_libelle}'")
                            continue

                    # Terminer l'état actuel
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.save()

                    # Créer le nouvel état
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=nouvel_etat_enum,
                        operateur=operateur,
                        date_debut=timezone.now(),
                        commentaire=f"État changé vers {nouvel_etat} par l'opérateur de préparation (action groupée)"
                    )

                    updated_commandes.append(commande_id)

            except Commande.DoesNotExist:
                errors.append(f"Commande {commande_id}: non trouvée")
            except Exception as e:
                errors.append(f"Commande {commande_id}: {str(e)}")

        # Préparer la réponse
        response_data = {
            "success": len(updated_commandes) > 0,
            "updated_count": len(updated_commandes),
            "updated_commandes": updated_commandes,
            "nouvel_etat": nouvel_etat,
        }

        if errors:
            response_data["errors"] = errors
            response_data["error_count"] = len(errors)

        if len(updated_commandes) > 0:
            response_data["message"] = f"{len(updated_commandes)} commande(s) mise(s) à jour avec succès"
        else:
            response_data["error"] = "Aucune commande n'a pu être mise à jour"

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Données JSON invalides"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Erreur serveur: {str(e)}"}, status=500)
