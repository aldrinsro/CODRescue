from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
import json
import io
import base64
from datetime import datetime

from .decorators import superviseur_required, can_manage_templates, can_view_templates, can_print_etiquettes
from commande.models import Commande

# ReportLab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5, A6
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, blue, red, green
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
import qrcode
from io import BytesIO
from .models import EtiquetteTemplate, Etiquette
from commande.models import Commande
from article.models import Article


@method_decorator(superviseur_required, name='dispatch')
class EtiquetteTemplateListView(ListView):
    """Vue pour lister les templates d'étiquettes"""
    model = EtiquetteTemplate
    template_name = 'etiquettes_pro/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EtiquetteTemplate.objects.filter(actif=True)
        
        # Filtrage par type
        type_filter = self.request.GET.get('type')
        if type_filter:
            queryset = queryset.filter(type_etiquette=type_filter)
        
        # Recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-date_creation')




# Fonction de génération PDF supprimée


@superviseur_required
def generate_barcode_image(request, code_data):
    """Générer une image de code-barres pour l'aperçu avec python-barcode"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 [BARCODE] Début génération - code_data: '{code_data}'")
    logger.info(f"🔍 [BARCODE] URL demandée: {request.get_full_path()}")
    logger.info(f"🔍 [BARCODE] User-Agent: {request.META.get('HTTP_USER_AGENT', 'N/A')}")
    
    try:
        logger.info(f"🔍 [BARCODE] Création du code-barres avec python-barcode")
        
        # Utiliser python-barcode pour générer le code-barres
        from barcode import Code128
        from barcode.writer import ImageWriter
        
        # Créer le code-barres
        barcode_class = Code128(code_data, writer=ImageWriter())
        
        # Options pour l'image
        options = {
            'module_width': 0.4,  # Largeur des barres
            'module_height': 15.0,  # Hauteur des barres
            'quiet_zone': 6.5,  # Zone de silence
            'font_size': 10,  # Taille de la police
            'text_distance': 5.0,  # Distance entre le code et le texte
            'background': 'white',
            'foreground': 'black',
        }
        
        # Générer l'image en mémoire
        img_buffer = io.BytesIO()
        barcode_class.write(img_buffer, options=options)
        img_buffer.seek(0)
            
        image_size = len(img_buffer.getvalue())
        logger.info(f"✅ [BARCODE] Image PNG générée avec python-barcode - Taille: {image_size} bytes")
        
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        response['Content-Length'] = str(image_size)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        logger.info(f"✅ [BARCODE] Réponse HTTP créée avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ [BARCODE] Erreur lors de la génération: {str(e)}")
        logger.error(f"❌ [BARCODE] Type d'erreur: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [BARCODE] Traceback: {traceback.format_exc()}")
        
        # Retourner une image d'erreur simple
        error_response = HttpResponse(
            f'<svg width="200" height="40" xmlns="http://www.w3.org/2000/svg"><rect width="200" height="40" fill="red"/><text x="10" y="25" fill="white" font-size="12">Erreur: {str(e)}</text></svg>',
            content_type='image/svg+xml'
        )
        return error_response

@superviseur_required
def generate_qrcode_image(request, code_data):
    """Générer une image de QR code pour l'aperçu avec qrcode"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 [QRCODE] Début génération - code_data: '{code_data}'")
    logger.info(f"🔍 [QRCODE] URL demandée: {request.get_full_path()}")
    logger.info(f"🔍 [QRCODE] User-Agent: {request.META.get('HTTP_USER_AGENT', 'N/A')}")
    
    try:
        logger.info(f"🔍 [QRCODE] Création du QR code avec qrcode")
        
        # Utiliser qrcode pour générer le QR code
        import qrcode
        from qrcode.image.pil import PilImage
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,  # Version du QR code (1-40)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Niveau de correction d'erreur
            box_size=10,  # Taille de chaque boîte en pixels
            border=4,  # Taille de la bordure
        )
        
        # Ajouter les données
        qr.add_data(code_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
        
        # Sauvegarder en mémoire
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
                
        image_size = len(img_buffer.getvalue())
        logger.info(f"✅ [QRCODE] Image PNG générée avec qrcode - Taille: {image_size} bytes")
        
        response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
        response['Content-Length'] = str(image_size)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        logger.info(f"✅ [QRCODE] Réponse HTTP créée avec succès")
        return response
            
    except Exception as e:
        logger.error(f"❌ [QRCODE] Erreur lors de la génération: {str(e)}")
        logger.error(f"❌ [QRCODE] Type d'erreur: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [QRCODE] Traceback: {traceback.format_exc()}")
        
        # Retourner une image d'erreur simple
        error_response = HttpResponse(
            f'<svg width="40" height="40" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" fill="red"/><text x="5" y="25" fill="white" font-size="8">Erreur: {str(e)}</text></svg>',
            content_type='image/svg+xml'
        )
        return error_response

@superviseur_required
def etiquettes_dashboard(request):
    """Tableau de bord des étiquettes"""
    # Récupérer les commandes confirmées avec paniers
    from commande.models import Commande
    commandes_confirmees_avec_paniers = Commande.objects.filter(
        paniers__isnull=False,
        etats__enum_etat__libelle='Confirmée',  # SANS espace à la fin
        etats__date_fin__isnull=True  # État actuel (non terminé)
    ).select_related('client', 'ville').distinct()
    
    # Récupérer les étiquettes des commandes confirmées avec paniers uniquement
    commandes_ids = [cmd.id for cmd in commandes_confirmees_avec_paniers]
    all_etiquettes = Etiquette.objects.filter(
        commande_id__in=commandes_ids
    ).select_related('template').order_by('-date_creation')
    
    # Préparer les données des étiquettes avec leurs commandes
    all_etiquettes_with_commandes = []
    for etiquette in all_etiquettes:
        etiquette_data = {
            'etiquette': etiquette,
            'commande': None,
            'etat_commande': None
        }
        
        if etiquette.commande_id:
            try:
                commande = Commande.objects.select_related('client', 'ville').get(id=int(etiquette.commande_id))
                etiquette_data['commande'] = commande
                etiquette_data['etat_commande'] = commande.etat_actuel
            except (Commande.DoesNotExist, ValueError):
                pass
        
        all_etiquettes_with_commandes.append(etiquette_data)
    
    # Statistiques (seulement pour les étiquettes des commandes confirmées)
    total_count = all_etiquettes.count()
    draft_count = all_etiquettes.filter(statut='draft').count()
    ready_count = all_etiquettes.filter(statut='ready').count()
    printed_count = all_etiquettes.filter(statut='printed').count()
    
    context = {
        'templates_count': EtiquetteTemplate.objects.filter(actif=True).count(),
        'etiquettes_count': total_count,
        'etiquettes_ready': ready_count,
        'etiquettes_printed': printed_count,
        'recent_templates': EtiquetteTemplate.objects.filter(actif=True).order_by('-date_creation')[:5],
        # Données pour la pagination intelligente du tableau (commandes confirmées uniquement)
        'all_etiquettes_with_commandes': all_etiquettes_with_commandes,
        'total_count': total_count,
        'draft_count': draft_count,
        'ready_count': ready_count,
        'printed_count': printed_count,
    }
    return render(request, 'etiquettes_pro/dashboard.html', context)


@superviseur_required
@can_print_etiquettes
def generate_qr_codes_articles(request, etiquette_id):
    """Générer les codes QR pour tous les articles du panier de la commande confirmée"""
    try:
        # Récupérer l'étiquette
        etiquette = get_object_or_404(Etiquette, id=etiquette_id)
        
        # Récupérer la commande associée
        if not etiquette.commande_id:
            return JsonResponse({
                'success': False,
                'error': 'Aucune commande associée à cette étiquette'
            }, status=400)
        
        commande = get_object_or_404(Commande, id=int(etiquette.commande_id))
        
        # Vérifier que la commande est confirmée
        etat_actuel = commande.etat_actuel
        if not etat_actuel or not etat_actuel.enum_etat or etat_actuel.enum_etat.libelle != 'Confirmée':
            return JsonResponse({
                'success': False,
                'error': 'La commande doit être confirmée pour générer les codes QR'
            }, status=400)
        
        # Récupérer tous les articles du panier
        paniers = commande.paniers.select_related('article', 'variante').all()
        
        if not paniers.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucun article trouvé dans le panier de cette commande'
            }, status=400)
        
        # Préparer les données pour le template
        articles_data = []
        
        for panier in paniers:
            article = panier.article
            variante = panier.variante
            
            # Générer le code QR
            qr_content = f"{article.reference or article.nom}"
            if variante and variante.reference_variante:
                qr_content = variante.reference_variante
            
            # Ajouter l'ID de commande au contenu du QR code
            if commande.id_yz:
                qr_content = f"{qr_content}|CMD:{commande.id_yz}"
            
            # Créer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Convertir en image base64 pour l'affichage HTML
            qr_img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Préparer les données de l'article
            article_data = {
                'article': article,
                'variante': variante,
                'panier': panier,
                'qr_content': qr_content,
                'qr_image': f"data:image/png;base64,{qr_base64}"
            }
            
            articles_data.append(article_data)
        
        # Rendre le template HTML pour l'impression
        context = {
            'commande': commande,
            'etiquette': etiquette,
            'articles_data': articles_data,
            'template': etiquette.template,  # Ajouter le template pour le format
        }
        
        return render(request, 'etiquettes_pro/qr_codes_print.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des codes QR: {str(e)}'
        }, status=500)


@superviseur_required
@can_print_etiquettes
def generate_qr_codes_simple(request, etiquette_id):
    """Générer les codes QR simples (sans détails) pour tous les articles du panier de la commande confirmée"""
    try:
        # Récupérer l'étiquette
        etiquette = get_object_or_404(Etiquette, id=etiquette_id)
        
        # Récupérer la commande associée
        if not etiquette.commande_id:
            return JsonResponse({
                'success': False,
                'error': 'Aucune commande associée à cette étiquette'
            }, status=400)
        
        commande = get_object_or_404(Commande, id=int(etiquette.commande_id))
        
        # Vérifier que la commande est confirmée
        etat_actuel = commande.etat_actuel
        if not etat_actuel or not etat_actuel.enum_etat or etat_actuel.enum_etat.libelle != 'Confirmée':
            return JsonResponse({
                'success': False,
                'error': 'La commande doit être confirmée pour générer les codes QR'
            }, status=400)
        
        # Récupérer tous les articles du panier
        paniers = commande.paniers.select_related('article', 'variante').all()
        
        if not paniers.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucun article trouvé dans le panier de cette commande'
            }, status=400)
        
        # Préparer les données pour le template
        articles_data = []
        
        for panier in paniers:
            article = panier.article
            variante = panier.variante
            
            # Générer le code QR
            qr_content = f"{article.reference or article.nom}"
            if variante and variante.reference_variante:
                qr_content = variante.reference_variante
            
            # Ajouter l'ID de commande au contenu du QR code
            if commande.id_yz:
                qr_content = f"{qr_content}|CMD:{commande.id_yz}"
            
            # Créer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Convertir en image base64 pour l'affichage HTML
            qr_img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Préparer les données de l'article (seulement pour la quantité)
            article_data = {
                'article': article,
                'variante': variante,
                'panier': panier,
                'qr_content': qr_content,
                'qr_image': f"data:image/png;base64,{qr_base64}"
            }
            
            articles_data.append(article_data)
        
        # Rendre le template HTML pour l'impression simple
        context = {
            'commande': commande,
            'etiquette': etiquette,
            'articles_data': articles_data,
            'template': etiquette.template,  # Ajouter le template pour le format
        }
        
        return render(request, 'etiquettes_pro/qr_codes_simple_print.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des codes QR: {str(e)}'
        }, status=500)


@superviseur_required
@can_print_etiquettes
@require_http_methods(["POST"])
def bulk_print_qr_codes_simple(request):
    """Impression multiple des codes QR simples pour plusieurs étiquettes sélectionnées"""
    try:
        # Récupérer les IDs des étiquettes sélectionnées
        etiquette_ids = request.POST.getlist('etiquette_ids[]')
        
        if not etiquette_ids:
            return JsonResponse({
                'success': False,
                'error': 'Aucune étiquette sélectionnée'
            }, status=400)
        
        # Récupérer les étiquettes
        etiquettes = Etiquette.objects.filter(id__in=etiquette_ids).select_related('template')
        
        if not etiquettes.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucune étiquette valide trouvée'
            }, status=400)
        
        # Préparer les données pour toutes les étiquettes
        all_articles_data = []
        commandes_info = []
        
        for etiquette in etiquettes:
            if not etiquette.commande_id:
                continue
                
            # Récupérer la commande par son ID
            try:
                commande = Commande.objects.select_related('client').get(id=int(etiquette.commande_id))
            except (Commande.DoesNotExist, ValueError):
                continue
            
            # Vérifier que la commande est confirmée
            etat_actuel = commande.etat_actuel
            if not etat_actuel or not etat_actuel.enum_etat or etat_actuel.enum_etat.libelle != 'Confirmée':
                continue
            
            # Récupérer tous les articles du panier
            paniers = commande.paniers.select_related('article', 'variante').all()
            
            if not paniers.exists():
                continue
            
            # Ajouter les infos de la commande
            commandes_info.append({
                'commande': commande,
                'etiquette': etiquette,
                'paniers_count': paniers.count()
            })
            
            # Générer les codes QR pour chaque article
            for panier in paniers:
                article = panier.article
                variante = panier.variante
                
                # Générer le code QR
                qr_content = f"{article.reference or article.nom}"
                if variante and variante.reference_variante:
                    qr_content = variante.reference_variante
                
                # Ajouter l'ID de commande au contenu du QR code
                if commande.id_yz:
                    qr_content = f"{qr_content}|CMD:{commande.id_yz}"
                
                # Créer le QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=8,
                    border=4,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)
                
                # Convertir en image base64 pour l'affichage HTML
                qr_img = qr.make_image(fill_color="black", back_color="white")
                img_buffer = BytesIO()
                qr_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                # Répéter selon la quantité
                for i in range(panier.quantite):
                    article_data = {
                        'article': article,
                        'variante': variante,
                        'panier': panier,
                        'qr_content': qr_content,
                        'qr_image': f"data:image/png;base64,{qr_base64}",
                        'commande_num': commande.num_cmd,
                        'etiquette_id': etiquette.id
                    }
                    all_articles_data.append(article_data)
        
        if not all_articles_data:
            return JsonResponse({
                'success': False,
                'error': 'Aucun code QR à générer pour les étiquettes sélectionnées'
            }, status=400)
        
        # Rendre le template HTML pour l'impression multiple
        context = {
            'commandes_info': commandes_info,
            'all_articles_data': all_articles_data,
            'total_qr_codes': len(all_articles_data),
            'template': EtiquetteTemplate.objects.filter(format_page='10x10').first() or EtiquetteTemplate.objects.first(),  # Template par défaut 10x10
        }
        
        return render(request, 'etiquettes_pro/bulk_qr_codes_simple_print.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des codes QR: {str(e)}'
        }, status=500)


@superviseur_required
@can_print_etiquettes
@require_http_methods(["POST"])
def bulk_print_qr_codes_details(request):
    """Impression multiple des codes QR avec détails pour plusieurs étiquettes sélectionnées"""
    try:
        # Récupérer les IDs des étiquettes sélectionnées
        etiquette_ids = request.POST.getlist('etiquette_ids[]')
        
        if not etiquette_ids:
            return JsonResponse({
                'success': False,
                'error': 'Aucune étiquette sélectionnée'
            }, status=400)
        
        # Récupérer les étiquettes
        etiquettes = Etiquette.objects.filter(id__in=etiquette_ids).select_related('template')
        
        if not etiquettes.exists():
            return JsonResponse({
                'success': False,
                'error': 'Aucune étiquette valide trouvée'
            }, status=400)
        
        # Préparer les données pour toutes les étiquettes
        all_articles_data = []
        commandes_info = []
        
        for etiquette in etiquettes:
            if not etiquette.commande_id:
                continue
                
            # Récupérer la commande par son ID
            try:
                commande = Commande.objects.select_related('client').get(id=int(etiquette.commande_id))
            except (Commande.DoesNotExist, ValueError):
                continue
            
            # Vérifier que la commande est confirmée
            etat_actuel = commande.etat_actuel
            if not etat_actuel or not etat_actuel.enum_etat or etat_actuel.enum_etat.libelle != 'Confirmée':
                continue
            
            # Récupérer tous les articles du panier
            paniers = commande.paniers.select_related('article', 'variante').all()
            
            if not paniers.exists():
                continue
            
            # Ajouter les infos de la commande
            commandes_info.append({
                'commande': commande,
                'etiquette': etiquette,
                'paniers_count': paniers.count()
            })
            
            # Générer les codes QR pour chaque article
            for panier in paniers:
                article = panier.article
                variante = panier.variante
                
                # Générer le code QR
                qr_content = f"{article.reference or article.nom}"
                if variante and variante.reference_variante:
                    qr_content = variante.reference_variante
                
                # Ajouter l'ID de commande au contenu du QR code
                if commande.id_yz:
                    qr_content = f"{qr_content}|CMD:{commande.id_yz}"
        
                # Créer le QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=6,
                    border=4,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)
                
                # Convertir en image base64 pour l'affichage HTML
                qr_img = qr.make_image(fill_color="black", back_color="white")
                img_buffer = BytesIO()
                qr_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                
                # Répéter selon la quantité
                for i in range(panier.quantite):
                    article_data = {
                        'article': article,
                        'variante': variante,
                        'panier': panier,
                        'qr_content': qr_content,
                        'qr_image': f"data:image/png;base64,{qr_base64}",
                        'commande_num': commande.num_cmd,
                        'etiquette_id': etiquette.id
                    }
                    all_articles_data.append(article_data)
        
        if not all_articles_data:
            return JsonResponse({
                'success': False,
                'error': 'Aucun code QR à générer pour les étiquettes sélectionnées'
            }, status=400)
        
        # Rendre le template HTML pour l'impression multiple
        context = {
            'commandes_info': commandes_info,
            'all_articles_data': all_articles_data,
            'total_qr_codes': len(all_articles_data),
            'template': EtiquetteTemplate.objects.filter(format_page='10x10').first() or EtiquetteTemplate.objects.first(),  # Template par défaut 10x10
        }
        
        return render(request, 'etiquettes_pro/bulk_qr_codes_details_print.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la génération des codes QR: {str(e)}'
        }, status=500)


@superviseur_required
@can_manage_templates
def create_template(request):
    """Créer un nouveau template d'étiquette"""
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            nom = request.POST.get('nom')
            description = request.POST.get('description', '')
            type_etiquette = request.POST.get('type_etiquette')
            format_page = request.POST.get('format_page')
            try:
                largeur_str = request.POST.get('largeur', '210')
                hauteur_str = request.POST.get('hauteur', '297')
                largeur = float(largeur_str) if largeur_str else 210.0
                hauteur = float(hauteur_str) if hauteur_str else 297.0
            except ValueError:
                largeur = 210.0
                hauteur = 297.0
            code_type = request.POST.get('code_type')
            try:
                code_size_str = request.POST.get('code_size', '80')
                code_size = int(code_size_str) if code_size_str else 80
            except ValueError:
                code_size = 80
            code_position = request.POST.get('code_position')
            police_titre = request.POST.get('police_titre')
            try:
                taille_titre_str = request.POST.get('taille_titre', '16')
                taille_titre = int(taille_titre_str) if taille_titre_str else 16
            except ValueError:
                taille_titre = 16
            police_texte = request.POST.get('police_texte')
            try:
                taille_texte_str = request.POST.get('taille_texte', '12')
                taille_texte = int(taille_texte_str) if taille_texte_str else 12
            except ValueError:
                taille_texte = 12
            couleur_principale = request.POST.get('couleur_principale', '#3B82F6')
            couleur_secondaire = request.POST.get('couleur_secondaire', '#1E40AF')
            couleur_texte = request.POST.get('couleur_texte', '#1F2937')
            actif = request.POST.get('actif') == 'on'
            
            # Validation des données requises
            if not nom or not type_etiquette or not format_page or not code_type:
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return render(request, 'etiquettes_pro/template_form.html')
            
            # Création du template
            template = EtiquetteTemplate.objects.create(
                nom=nom,
                description=description,
                type_etiquette=type_etiquette,
                format_page=format_page,
                largeur=largeur,
                hauteur=hauteur,
                code_type=code_type,
                code_size=code_size,
                code_position=code_position,
                police_titre=police_titre,
                taille_titre=taille_titre,
                police_texte=police_texte,
                taille_texte=taille_texte,
                couleur_principale=couleur_principale,
                couleur_secondaire=couleur_secondaire,
                couleur_texte=couleur_texte,
                actif=actif,
                cree_par=request.user
            )
            
            messages.success(request, f'Template "{nom}" créé avec succès!')
            return redirect('etiquettes_pro:template_detail', pk=template.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du template: {str(e)}')
            return render(request, 'etiquettes_pro/template_form.html')
    
    return render(request, 'etiquettes_pro/template_form.html')


@superviseur_required
@can_view_templates
def template_detail(request, pk):
    """Détail d'un template"""
    template = get_object_or_404(EtiquetteTemplate, pk=pk)
    return render(request, 'etiquettes_pro/template_detail.html', {'template': template})


@superviseur_required
@can_manage_templates
def edit_template(request, pk):
    """Modifier un template"""
    template = get_object_or_404(EtiquetteTemplate, pk=pk)
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            template.nom = request.POST.get('nom')
            template.description = request.POST.get('description', '')
            template.type_etiquette = request.POST.get('type_etiquette')
            template.format_page = request.POST.get('format_page')
            try:
                largeur_str = request.POST.get('largeur', '210')
                hauteur_str = request.POST.get('hauteur', '297')
                template.largeur = float(largeur_str) if largeur_str else 210.0
                template.hauteur = float(hauteur_str) if hauteur_str else 297.0
            except ValueError:
                template.largeur = 210.0
                template.hauteur = 297.0
            template.code_type = request.POST.get('code_type')
            try:
                code_size_str = request.POST.get('code_size', '80')
                template.code_size = int(code_size_str) if code_size_str else 80
            except ValueError:
                template.code_size = 80
            template.code_position = request.POST.get('code_position')
            template.police_titre = request.POST.get('police_titre')
            try:
                taille_titre_str = request.POST.get('taille_titre', '16')
                template.taille_titre = int(taille_titre_str) if taille_titre_str else 16
            except ValueError:
                template.taille_titre = 16
            template.police_texte = request.POST.get('police_texte')
            try:
                taille_texte_str = request.POST.get('taille_texte', '12')
                template.taille_texte = int(taille_texte_str) if taille_texte_str else 12
            except ValueError:
                template.taille_texte = 12
            template.couleur_principale = request.POST.get('couleur_principale', '#3B82F6')
            template.couleur_secondaire = request.POST.get('couleur_secondaire', '#1E40AF')
            template.couleur_texte = request.POST.get('couleur_texte', '#1F2937')
            template.actif = request.POST.get('actif') == 'on'
            
            # Validation des données requises
            if not template.nom or not template.type_etiquette or not template.format_page or not template.code_type:
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return render(request, 'etiquettes_pro/template_form.html', {'template': template})
            
            # Sauvegarde du template
            template.save()
            
            messages.success(request, f'Template "{template.nom}" modifié avec succès!')
            return redirect('etiquettes_pro:template_detail', pk=template.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification du template: {str(e)}')
            return render(request, 'etiquettes_pro/template_form.html', {'template': template})
    
    return render(request, 'etiquettes_pro/template_form.html', {'template': template})


@superviseur_required
@can_manage_templates
@require_http_methods(["DELETE"])
def delete_template(request, pk):
    """Supprimer un template d'étiquette"""
    try:
        template = get_object_or_404(EtiquetteTemplate, pk=pk)
        nom_template = template.nom

        # Vérifier s'il y a des étiquettes qui utilisent ce template
        etiquettes_count = template.etiquettes.count()
        if etiquettes_count > 0:
            return JsonResponse({
                'success': False,
                'error': (
                    f'Impossible de supprimer le template "{nom_template}". '
                    f'{etiquettes_count} étiquette(s) l\'utilisent encore.'
                )
            }, status=400)

        # Supprimer le template
        template.delete()

        return JsonResponse({
            'success': True,
            'message': f'Template "{nom_template}" supprimé avec succès',
            'nom': nom_template
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression: {str(e)}'
        }, status=500)


@superviseur_required
def etiquette_list(request):
    """Liste des étiquettes avec filtres et pagination intelligente"""
    # Récupérer les paramètres de filtrage
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    template_id = request.GET.get('template', '')
    
    # Construire la requête de base
    etiquettes = Etiquette.objects.select_related('template', 'cree_par').order_by('-date_creation')
    
    # Appliquer les filtres
    if search:
        etiquettes = etiquettes.filter(
            Q(reference__icontains=search) | 
            Q(template__nom__icontains=search) |
            Q(commande_id__icontains=search) |
            Q(nom_article__icontains=search) |
            Q(client_nom__icontains=search)
        )
    
    if statut:
        etiquettes = etiquettes.filter(statut=statut)
    
    if template_id:
        etiquettes = etiquettes.filter(template_id=template_id)
    
    # Pour la pagination intelligente, on passe toutes les étiquettes
    # La pagination sera gérée côté client
    etiquettes_list = list(etiquettes)
    
    # Pagination Django (fallback)
    paginator = Paginator(etiquettes, 20)  # 20 étiquettes par page
    page_number = request.GET.get('page')
    etiquettes_page = paginator.get_page(page_number)
    
    # Statistiques
    total_count = Etiquette.objects.count()
    draft_count = Etiquette.objects.filter(statut='draft').count()
    ready_count = Etiquette.objects.filter(statut='ready').count()
    printed_count = Etiquette.objects.filter(statut='printed').count()
    
    # Templates pour le filtre
    templates = EtiquetteTemplate.objects.filter(actif=True).order_by('nom')
    
    context = {
        'etiquettes': etiquettes_list,  # Toutes les étiquettes pour la pagination intelligente
        'etiquettes_page': etiquettes_page,  # Page Django (fallback)
        'templates': templates,
        'total_count': total_count,
        'draft_count': draft_count,
        'ready_count': ready_count,
        'printed_count': printed_count,
        'search_query': search,
        'statut_filter': statut,
        'template_filter': template_id,
    }
    
    return render(request, 'etiquettes_pro/etiquette_list.html', context)


@superviseur_required
def preview_etiquette(request, etiquette_id):
    """Aperçu d'une étiquette"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 [PREVIEW] Début aperçu étiquette ID: {etiquette_id}")
    
    etiquette = get_object_or_404(Etiquette, id=etiquette_id)
    logger.info(f"🔍 [PREVIEW] Étiquette trouvée - Reference: {etiquette.reference}")
    logger.info(f"🔍 [PREVIEW] Template: {etiquette.template.nom} (code_type: {etiquette.template.code_type})")
    logger.info(f"🔍 [PREVIEW] Code_data: '{etiquette.code_data}'")
    logger.info(f"🔍 [PREVIEW] Commande_id: '{etiquette.commande_id}'")
    
    commande = None
    if etiquette.commande_id:
        try:
            commande = Commande.objects.get(id=int(etiquette.commande_id))
            logger.info(f"✅ [PREVIEW] Commande trouvée - ID: {commande.id}, Num: {commande.num_cmd}")
            logger.info(f"✅ [PREVIEW] Client: {commande.client.nom} {commande.client.prenom}")
            logger.info(f"✅ [PREVIEW] Total: {commande.total_cmd}")
        except (Commande.DoesNotExist, ValueError) as e:
            logger.warning(f"⚠️ [PREVIEW] Commande non trouvée: {e}")
            pass
    else:
        logger.warning(f"⚠️ [PREVIEW] Pas de commande_id dans l'étiquette")
    
    # Calculer le total d'articles pour l'affichage
    total_articles = 0
    if etiquette.cart_items:
        total_articles = sum(item.get('quantite', 0) for item in etiquette.cart_items)
            
    context = {
        'etiquette': etiquette,
        'commande': commande,
        'total_articles': total_articles,
    }
    
    logger.info(f"✅ [PREVIEW] Contexte préparé, rendu du template")
    return render(request, 'etiquettes_pro/etiquette_preview.html', context)


def api_template_list(request):
    """API pour lister les templates"""
    templates = EtiquetteTemplate.objects.filter(actif=True)
    data = [{'id': t.id, 'nom': t.nom, 'type': t.type_etiquette} for t in templates]
    return JsonResponse({'templates': data})


def api_etiquette_list(request):
    """API pour lister les étiquettes"""
    # Vérifier si un filtre par commande_id est demandé
    commande_id = request.GET.get('commande_id')
    
    if commande_id:
        # Filtrer par commande_id
        etiquettes = Etiquette.objects.filter(commande_id=str(commande_id))
        print(f"🔍 [DEBUG API] Recherche étiquettes pour commande_id: {commande_id}, trouvées: {etiquettes.count()}")
    else:
        # Récupérer toutes les étiquettes (limitées à 50)
        etiquettes = Etiquette.objects.all()[:50]
    
    data = [{'id': e.id, 'reference': e.reference, 'statut': e.statut, 'commande_id': e.commande_id} for e in etiquettes]
    return JsonResponse(data, safe=False)




@superviseur_required
def get_commandes_with_paniers(request):
    """Récupérer les commandes confirmées avec paniers qui n'ont pas encore d'étiquettes"""
    try:
        # Récupérer le template par défaut
        template = EtiquetteTemplate.objects.filter(
            nom='Template Livraison Standard',
            actif=True
        ).first()
        
        print(f"🔍 [DEBUG] Template trouvé: {template}")
        
        if not template:
            # Essayer de récupérer n'importe quel template actif
            template = EtiquetteTemplate.objects.filter(actif=True).first()
            print(f"🔍 [DEBUG] Template par défaut non trouvé, utilisation du premier template actif: {template}")
        
        if not template:
            return JsonResponse({'error': 'Aucun template actif trouvé'}, status=404)
        
        # Récupérer uniquement les commandes confirmées avec paniers
        commandes_avec_paniers = Commande.objects.filter(
            paniers__isnull=False,
            etats__enum_etat__libelle='Confirmée',  # SANS espace à la fin
            etats__date_fin__isnull=True  # État actuel (non terminé)
        ).select_related('client', 'ville').distinct()
        
        print(f"🔍 [DEBUG] Commandes confirmées avec paniers trouvées: {commandes_avec_paniers.count()}")
        
        # Récupérer les IDs des commandes qui ont déjà des étiquettes (avec n'importe quel template)
        commandes_avec_etiquettes = set(
            Etiquette.objects.filter(
                commande_id__isnull=False
            ).values_list('commande_id', flat=True)
        )
        
        print(f"🔍 [DEBUG] Commandes avec étiquettes: {len(commandes_avec_etiquettes)}")
        print(f"🔍 [DEBUG] IDs des commandes avec étiquettes: {list(commandes_avec_etiquettes)[:10]}...")  # Afficher les 10 premiers
        
        # Filtrer les commandes sans étiquettes
        commandes_sans_etiquettes = []
        for commande in commandes_avec_paniers:
            if str(commande.id) not in commandes_avec_etiquettes:
                # Calculer le nombre total d'articles
                total_articles = sum(panier.quantite for panier in commande.paniers.all())
                
                commandes_sans_etiquettes.append({
                    'id': commande.id,
                    'num_cmd': commande.num_cmd or commande.id_yz,
                    'client_nom': f"{commande.client.nom} {commande.client.prenom}" if commande.client else "Client inconnu",
                    'client_telephone': commande.client.numero_tel if commande.client else "",
                    'ville_init': commande.ville_init or "",
                    'ville_livraison': commande.ville.nom if commande.ville else "",
                    'total_articles': total_articles,
                    'date_creation': commande.date_creation.strftime('%d/%m/%Y %H:%M') if commande.date_creation else "",
                    'paniers_count': commande.paniers.count()
                })
        
        print(f"🔍 [DEBUG] Commandes sans étiquettes trouvées: {len(commandes_sans_etiquettes)}")
        if commandes_sans_etiquettes:
            print(f"🔍 [DEBUG] Première commande sans étiquette: {commandes_sans_etiquettes[0]}")
        
        return JsonResponse({
            'commandes': commandes_sans_etiquettes,
            'total': len(commandes_sans_etiquettes)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)


@superviseur_required
def generate_etiquettes_manually(request):
    """Générer manuellement des étiquettes pour les commandes confirmées avec paniers"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
        
        # Récupérer le template par défaut
        template = EtiquetteTemplate.objects.filter(
            nom='Template Livraison Standard',
            actif=True
        ).first()
        
        if not template:
            return JsonResponse({'error': 'Template par défaut non trouvé'}, status=404)
        
        # Vérifier si une commande spécifique est demandée
        import json
        commande_id = None
        try:
            if request.body:
                body = json.loads(request.body)
                commande_id = body.get('commande_id')
        except (json.JSONDecodeError, AttributeError):
            pass
        
        commandes_avec_paniers = Commande.objects.none() # Initialiser à vide
        commandes_avec_etiquettes = set()

        if commande_id:
            # Générer pour une seule commande (doit être confirmée)
            print(f"🔍 [DEBUG] Génération individuelle pour la commande {commande_id}")
            commandes_avec_paniers = Commande.objects.filter(
                id=commande_id,
                paniers__isnull=False,
                etats__enum_etat__libelle='Confirmée',  # SANS espace à la fin
                etats__date_fin__isnull=True  # État actuel (non terminé)
            ).select_related('client', 'ville')
            
            print(f"🔍 [DEBUG] Commande {commande_id} trouvée: {commandes_avec_paniers.exists()}")
            
            if not commandes_avec_paniers.exists():
                return JsonResponse({'error': f'Commande {commande_id} non trouvée, sans paniers ou non confirmée'}, status=404)

            # Si commande_id est présent (génération individuelle), supprimer l'étiquette existante si elle existe (avec n'importe quel template)
            etiquettes_supprimees = Etiquette.objects.filter(
                commande_id=str(commande_id)
            ).count()
            Etiquette.objects.filter(
                commande_id=str(commande_id)
            ).delete()
            print(f"🔍 [DEBUG] Étiquettes supprimées pour la commande {commande_id}: {etiquettes_supprimees}")

            # Pour la génération individuelle, nous ne voulons pas sauter la création, donc l'ensemble est vide
            # commandes_avec_etiquettes reste vide ici pour forcer la création de l'étiquette individuelle

        else:
            # Générer pour toutes les commandes confirmées
            commandes_avec_paniers = Commande.objects.filter(
                paniers__isnull=False,
                etats__enum_etat__libelle='Confirmée',  # SANS espace à la fin
                etats__date_fin__isnull=True  # État actuel (non terminé)
            ).select_related('client', 'ville').distinct()

            # Récupérer les IDs des commandes qui ont déjà des étiquettes (pour la génération en lot, avec n'importe quel template)
            commandes_avec_etiquettes = set(
                Etiquette.objects.filter(
                    commande_id__isnull=False
                ).values_list('commande_id', flat=True)
            )
        
        # Générer les étiquettes
        etiquettes_creees = []
        for commande in commandes_avec_paniers:
            # Pour la génération individuelle, on ne vérifie pas les étiquettes existantes car on les a déjà supprimées
            # Pour la génération en lot, on vérifie si la commande a déjà une étiquette
            if not commande_id and str(commande.id) in commandes_avec_etiquettes:
                continue
            
            # Récupérer les vrais articles de la commande depuis le modèle Panier
            cart_items_data = []
            for panier in commande.paniers.all():
                # Construire le nom de la variante
                variante_nom = "Standard"
                if panier.variante:
                    couleur = panier.variante.couleur.nom if panier.variante.couleur else ""
                    pointure = panier.variante.pointure.pointure if panier.variante.pointure else ""
                    if couleur and pointure:
                        variante_nom = f"{couleur} {pointure}"
                    elif couleur:
                        variante_nom = couleur
                    elif pointure:
                        variante_nom = pointure
                
                item_data = {
                    "nom": panier.article.nom,
                    "reference": panier.article.reference or "",
                    "variante": variante_nom,
                    "quantite": panier.quantite,
                    "prix_unitaire": float(panier.sous_total / panier.quantite) if panier.quantite > 0 else 0,
                    "sous_total": float(panier.sous_total)
                }
                cart_items_data.append(item_data)
            
            # Créer l'étiquette
            print(f"🔍 [DEBUG] Création de l'étiquette pour la commande {commande.id}")
            etiquette = Etiquette.objects.create(
                template=template,
                reference=f"{commande.id:06d}",
                nom_article=f"Commande {commande.num_cmd or commande.id_yz}",
                commande_id=str(commande.id),
                client_nom=f"{commande.client.nom} {commande.client.prenom}" if commande.client else "",
                code_data=f"{commande.id:06d}",
                statut='ready',
                cree_par=request.user,
                cart_items=cart_items_data
            )
            print(f"🔍 [DEBUG] Étiquette créée: ID {etiquette.id}, Référence {etiquette.reference}, Template {etiquette.template.nom}")
            etiquettes_creees.append(etiquette)
            
            # Pour la génération individuelle, on s'arrête après avoir créé une étiquette
            if commande_id:
                print(f"🔍 [DEBUG] Génération individuelle terminée pour la commande {commande_id}")
                break
        
        return JsonResponse({
            'success': True,
            'etiquettes_creees': len(etiquettes_creees),
            'message': f'{len(etiquettes_creees)} étiquettes générées avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la génération: {str(e)}'}, status=500)


@login_required
def etiquette_print_data(request, etiquette_id):
    """Récupérer les données d'une étiquette pour l'impression avec le template configuré"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        etiquette = get_object_or_404(Etiquette, id=etiquette_id)
        template = etiquette.template
        
        # Récupérer les données de la commande
        commande = None
        if etiquette.commande_id:
            try:
                commande = Commande.objects.get(id=int(etiquette.commande_id))
            except (Commande.DoesNotExist, ValueError):
                pass
        
        # Calculer le total d'articles
        total_articles = 0
        if etiquette.cart_items:
            total_articles = sum(item.get('quantite', 0) for item in etiquette.cart_items)
        
        # Préparer les données pour l'impression
        data = {
            'success': True,
            'etiquette': {
                'id': etiquette.id,
                'reference': etiquette.reference,
                'code_data': etiquette.code_data,
                'nom_article': etiquette.nom_article,
                'client_nom': etiquette.client_nom,
                'cart_items': etiquette.cart_items or [],
            },
            'template': {
                # Informations de base
                'nom': template.nom,
                'description': template.description,
                'type_etiquette': template.type_etiquette,
                'format_page': template.format_page,
                
                # Dimensions
                'largeur': template.largeur,
                'hauteur': template.hauteur,
                
                # Paramètres du code-barres/QR
                'code_type': template.code_type,
                'code_size': template.code_size,
                'code_position': template.code_position,
                'code_width': template.code_width,
                'code_height': template.code_height,
                'code_quality': template.code_quality,
                
                # Paramètres de bordures
                'border_enabled': template.border_enabled,
                'border_width': template.border_width,
                'border_color': template.border_color,
                'border_radius': template.border_radius,
                
                # Paramètres de design
                'police_titre': template.police_titre,
                'taille_titre': template.taille_titre,
                'police_texte': template.police_texte,
                'taille_texte': template.taille_texte,
                
                # Couleurs
                'couleur_principale': template.couleur_principale,
                'couleur_secondaire': template.couleur_secondaire,
                'couleur_texte': template.couleur_texte,
                
                # Icônes professionnelles
                'icone_client': template.icone_client,
                'icone_telephone': template.icone_telephone,
                'icone_adresse': template.icone_adresse,
                'icone_ville': template.icone_ville,
                'icone_article': template.icone_article,
                'icone_prix': template.icone_prix,
                'icone_marque': template.icone_marque,
                'icone_website': template.icone_website,
                'icone_panier': template.icone_panier,
                'icone_code': template.icone_code,
                'icone_date': template.icone_date,
                
                # Paramètres de personnalisation d'impression
                'print_code_width': template.print_code_width,
                'print_code_height': template.print_code_height,
                'print_contact_width': template.print_contact_width,
                'print_show_prices': template.print_show_prices,
                'print_show_articles': template.print_show_articles,
                'print_show_client_info': template.print_show_client_info,
                'print_show_contact_info': template.print_show_contact_info,
                'print_show_brand': template.print_show_brand,
                'print_show_date': template.print_show_date,
                'print_show_total_circle': template.print_show_total_circle,
                'print_margin_top': template.print_margin_top,
                'print_margin_bottom': template.print_margin_bottom,
                'print_margin_left': template.print_margin_left,
                'print_margin_right': template.print_margin_right,
                'print_padding': template.print_padding,
                'print_font_size_title': template.print_font_size_title,
                'print_font_size_text': template.print_font_size_text,
                'print_font_size_small': template.print_font_size_small,
                
                # Métadonnées
                'actif': template.actif,
                'date_creation': template.date_creation.isoformat() if template.date_creation else None,
                'date_modification': template.date_modification.isoformat() if template.date_modification else None,
            },
            'commande': {
                'id': commande.id if commande else None,
                'num_cmd': commande.num_cmd if commande else None,
                'total_cmd': commande.total_cmd if commande else None,
                'ville_init': commande.ville_init if commande else None,
                'client': {
                    'nom': commande.client.nom if commande and commande.client else None,
                    'prenom': commande.client.prenom if commande and commande.client else None,
                    'numero_tel': commande.client.numero_tel if commande and commande.client else None,
                    'adresse': commande.client.adresse if commande and commande.client else None,
                } if commande and commande.client else None,
                'ville': {
                    'nom': commande.ville.nom if commande and commande.ville else None,
                } if commande and commande.ville else None,
            } if commande else None,
            'total_articles': total_articles,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données d'impression: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des données: {str(e)}'
        }, status=500)


def update_template_print_settings(request, template_id):
    """Mettre à jour les paramètres de personnalisation d'impression d'un template"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        template = EtiquetteTemplate.objects.get(id=template_id)
    except EtiquetteTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Template non trouvé'})
    
    try:
        # Mettre à jour les paramètres de personnalisation d'impression
        template.print_code_width = int(request.POST.get('print_code_width', 250))
        template.print_code_height = int(request.POST.get('print_code_height', 80))
        template.print_contact_width = int(request.POST.get('print_contact_width', 250))
        template.print_show_prices = request.POST.get('print_show_prices') == 'on'
        template.print_show_articles = request.POST.get('print_show_articles') == 'on'
        template.print_show_client_info = request.POST.get('print_show_client_info') == 'on'
        template.print_show_contact_info = request.POST.get('print_show_contact_info') == 'on'
        template.print_show_brand = request.POST.get('print_show_brand') == 'on'
        template.print_show_date = request.POST.get('print_show_date') == 'on'
        template.print_show_total_circle = request.POST.get('print_show_total_circle') == 'on'
        template.print_padding = int(request.POST.get('print_padding', 15))
        template.print_font_size_title = int(request.POST.get('print_font_size_title', 16))
        template.print_font_size_text = int(request.POST.get('print_font_size_text', 12))
        template.print_font_size_small = int(request.POST.get('print_font_size_small', 10))
        
        template.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Paramètres d\'impression mis à jour avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        })



@superviseur_required
@require_http_methods(["DELETE"])
def delete_etiquette(request, etiquette_id):
    """Supprimer une étiquette"""
    try:
        etiquette = get_object_or_404(Etiquette, id=etiquette_id)
        reference = etiquette.reference
        
        # Supprimer l'étiquette
        etiquette.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Étiquette {reference} supprimée avec succès',
            'reference': reference
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression: {str(e)}'
        })