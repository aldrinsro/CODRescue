from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q
import json
import io
from datetime import datetime

from .decorators import superviseur_required, can_manage_templates, can_view_templates, can_print_etiquettes

# ReportLab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5, A6
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, blue, red, green
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
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


@superviseur_required
@can_print_etiquettes
def generate_etiquette_pdf(request, etiquette_id):
    """Générer le PDF d'une étiquette individuelle avec ReportLab"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🔍 [PDF] Début génération PDF ReportLab pour étiquette ID: {etiquette_id}")

    etiquette = get_object_or_404(Etiquette, id=etiquette_id)
    template = etiquette.template
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="etiquette_{etiquette.reference}.pdf"'
    
    # Déterminer la taille de page
    if template.format_page == 'A4':
        page_size = A4
    elif template.format_page == 'A5':
        page_size = A5
    elif template.format_page == 'A6':
        page_size = A6
    else:
        page_size = (template.largeur * mm, template.hauteur * mm)
    
    # Créer le document PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=page_size, 
                          leftMargin=10*mm, rightMargin=10*mm,
                          topMargin=10*mm, bottomMargin=10*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=template.police_titre,
        fontSize=template.taille_titre,
        textColor=black,
        alignment=1,  # Centré
        spaceAfter=12
    )
    
    text_style = ParagraphStyle(
        'CustomText',
        parent=styles['Normal'],
        fontName=template.police_texte,
        fontSize=template.taille_texte,
        textColor=black,
        spaceAfter=6
    )
    
    # Contenu de l'étiquette
    story = []
    
    # Styles de paragraphe pour le tableau
    cell_text_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName=template.police_texte,
        fontSize=template.taille_texte,
        textColor=black,
        spaceAfter=0
    )

    bold_cell_text_style = ParagraphStyle(
        'BoldCellText',
        parent=styles['Normal'],
        fontName=template.police_titre,
        fontSize=template.taille_texte,
        textColor=black,
        spaceAfter=0
    )

    white_bold_cell_text_style = ParagraphStyle(
        'WhiteBoldCellText',
        parent=styles['Normal'],
        fontName=template.police_titre,
        fontSize=template.taille_texte,
        textColor=white,
        spaceAfter=0
    )

    # Ligne 1: Code-barres et date
    barcode_content_for_table = ""

    try:
        # Utiliser les nouvelles bibliothèques pour générer les images
        if template.code_type == 'barcode' or template.code_type == 'both':
            # Générer le code-barres avec python-barcode
            from barcode import Code128
            from barcode.writer import ImageWriter
            
            barcode_class = Code128(etiquette.code_data, writer=ImageWriter())
            # Options basées sur les dimensions du template
            options = {
                'module_width': 0.3 if template.code_quality == 'ultra' else 0.4,
                'module_height': template.code_height * 0.8,  # Utiliser code_height du template
                'quiet_zone': 8.0,
                'font_size': 12,
                'text_distance': 6.0,
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'center_text': True,
            }
            
            logger.info(f"🔍 [HTML] Code-barres - Dimensions: {template.code_width}x{template.code_height}mm, Qualité: {template.code_quality}")
            
            # Générer l'image en mémoire
            img_buffer = io.BytesIO()
            barcode_class.write(img_buffer, options=options)
            img_buffer.seek(0)
            
            # Créer une image ReportLab à partir du buffer
            from reportlab.lib.utils import ImageReader
            barcode_image = Image(ImageReader(img_buffer), width=60*mm, height=25*mm)
            barcode_content_for_table = barcode_image
            
        elif template.code_type == 'qr':
            # Générer le QR code avec qrcode
            import qrcode
            from qrcode.image.pil import PilImage
            
            # Paramètres QR basés sur les dimensions du template
            error_correction = qrcode.constants.ERROR_CORRECT_M if template.code_quality == 'ultra' else qrcode.constants.ERROR_CORRECT_L
            box_size = int(template.code_width / 8)  # Basé sur code_width du template
            border = 6 if template.code_quality == 'ultra' else 4
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
            )
            
            logger.info(f"🔍 [HTML] QR Code - Dimensions: {template.code_width}x{template.code_height}mm, Qualité: {template.code_quality}")
            qr.add_data(etiquette.code_data)
            qr.make(fit=True)
            
            # Créer l'image
            img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
            
            # Sauvegarder en mémoire
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Créer une image ReportLab à partir du buffer
            from reportlab.lib.utils import ImageReader
            barcode_content_for_table = Image(ImageReader(img_buffer), width=25*mm, height=25*mm)
            
    except Exception as e:
        # En cas d'erreur, utiliser un Paragraph avec le texte
        barcode_content_for_table = Paragraph(f"Code: {etiquette.code_data}", cell_text_style)
            
    date_text = Paragraph(datetime.now().strftime('%m/%d/%Y'), white_bold_cell_text_style)
    
    data = [
        [barcode_content_for_table, "", date_text], 
    ]
    
    # Récupérer les vraies données de la commande
    commande = None
    if etiquette.commande_id:
        try:
            commande = Commande.objects.get(id=int(etiquette.commande_id))
        except (Commande.DoesNotExist, ValueError):
            pass
    
    # Ligne 2: Informations client
    client_info_parts = []
    if etiquette.client_nom:
        client_info_parts.append(f"Client: {etiquette.client_nom}")
    elif commande and commande.client:
        client_info_parts.append(f"Client: {commande.client.nom} {commande.client.prenom}")
    
    # Utiliser les vraies informations de la commande si disponibles
    if commande and commande.client:
        if commande.client.numero_tel:
            client_info_parts.append(f"Tél: {commande.client.numero_tel}")
        if commande.client.adresse:
            client_info_parts.append(f"Adresse: {commande.client.adresse}")
        if commande.ville:
            client_info_parts.append(f"Ville: {commande.ville.nom}")
    
    client_info_text = "<br/>".join(client_info_parts)
    data.append([Paragraph(client_info_text, cell_text_style), "", ""])
    
    # Ligne 3: Séparateur (ligne horizontale)
    data.append([Paragraph("", cell_text_style), "", ""]) # Paragraphe vide pour le séparateur
    
    # Ligne 4: Article
    if etiquette.nom_article:
        article_text_content = etiquette.nom_article
    elif commande:
        article_text_content = f"Commande {commande.num_cmd or commande.id_yz}"
    else:
        article_text_content = f"Commande {etiquette.commande_id}"
    
    data.append([Paragraph(f"<b>{article_text_content}</b>", bold_cell_text_style), "", ""])
    
    # Ligne 5: Séparateur (ligne horizontale)
    data.append([Paragraph("", cell_text_style), "", ""]) # Paragraphe vide pour le séparateur
    
    # Ligne 6: Prix et informations
    # Utiliser le vrai prix de la commande si disponible
    price_value = ""
    if commande and hasattr(commande, 'total_cmd') and commande.total_cmd is not None:
        price_value = f"<b>{commande.total_cmd} DH</b>"
    else:
        price_value = "<b>Prix non disponible</b>"
        
    price_text = Paragraph(f"{price_value}<br/>YOZAK", bold_cell_text_style)
    
    contact_info_parts = []
    if commande and commande.ville:
        contact_info_parts.append(f"<b>{commande.ville.nom}</b>")
    else:
        contact_info_parts.append("<b>VILLE NON DÉFINIE</b>")
        
    contact_info_parts.append("www.yoozak.com")
    contact_info_parts.append("06 34 21 56 39 / 47")
    contact_info_text = "<br/>".join(contact_info_parts)
    
    data.append([price_text, "", Paragraph(contact_info_text, white_bold_cell_text_style)])
    
    # Créer le tableau
    table = Table(data, colWidths=[80*mm, 20*mm, 50*mm], rowHeights=[30*mm, None, 5*mm, None, 5*mm, None]) # Ajuster colWidths et rowHeights
    
    # Style du tableau
    table_style = TableStyle([
        # Couleurs de fond
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),  # Code-barres (gauche)
        ('BACKGROUND', (2, 0), (2, 0), colors.darkblue),   # Date (droite)
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),      # Client
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),      # Article
        ('BACKGROUND', (0, 5), (1, 5), colors.white),      # Prix (gauche)
        ('BACKGROUND', (2, 5), (2, 5), colors.darkblue),   # Contact (droite)
        
        # Bordures
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black), # Bordure sous la première ligne
        ('LINEBELOW', (0, 2), (-1, 2), 1, colors.black),
        ('LINEBELOW', (0, 4), (-1, 4), 1, colors.black),
        
        # Alignement
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Alignements spécifiques
        ('ALIGN', (2, 0), (2, 0), 'CENTER'), # Date
        ('ALIGN', (0, 3), (-1, 3), 'CENTER'), # Article
        ('ALIGN', (2, 5), (2, 5), 'CENTER'), # Contact
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        
        # Taille de police pour le texte de la date et contact
        ('FONTSIZE', (2, 0), (2, 0), template.taille_texte),
        ('FONTSIZE', (2, 5), (2, 5), template.taille_texte),
        ('LEADING', (2, 5), (2, 5), 10), # Espacement des lignes pour le contact
    ])
    
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 10*mm))
    
    # Construire le PDF
    doc.build(story)
    
    # Récupérer le contenu du buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Marquer l'étiquette comme imprimée
    etiquette.statut = 'printed'
    etiquette.date_impression = datetime.now()
    etiquette.save()
    
    response.write(pdf_content)
    return response


def generate_etiquette_pdf_pillow(request, etiquette_id):
    """Générer le PDF d'une étiquette avec Pillow (sans ReportLab)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 [PDF] Début génération PDF pour étiquette ID: {etiquette_id}")
    
    etiquette = get_object_or_404(Etiquette, id=etiquette_id)
    template = etiquette.template
    
    try:
        # Créer l'image de l'étiquette avec Pillow - 100% Dynamique basé sur le template
        from PIL import Image, ImageDraw, ImageFont
        
        # Dimensions dynamiques basées sur le template - OPTIMISÉ SELON QUALITÉ
        # DPI basé sur la qualité choisie dans le template
        dpi_map = {
            'standard': 300,
            'high': 600,
            'ultra': 600,  # 4K Ultra
        }
        dpi = dpi_map.get(template.code_quality, 600)
        mm_to_px = dpi / 25.4  # Conversion mm vers pixels
        
        logger.info(f"🔍 [PDF] Qualité sélectionnée: {template.code_quality} (DPI: {dpi})")
        
        # Utiliser les dimensions du template
        if template.format_page == 'CUSTOM':
            width = int(template.largeur * mm_to_px)
            height = int(template.hauteur * mm_to_px)
        else:
            # Dimensions standard
            dimensions = {
                'A4': (210, 297),
                'A5': (148, 210),
                'A6': (105, 148),
            }
            largeur_mm, hauteur_mm = dimensions.get(template.format_page, (105, 148))
            width = int(largeur_mm * mm_to_px)
            height = int(hauteur_mm * mm_to_px)
        
        logger.info(f"🔍 [PDF] Dimensions dynamiques: {width}x{height} pixels ({template.format_page})")
        
        # Créer l'image avec anti-aliasing
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Charger les polices dynamiques basées sur le template - 100% RESPECT DU TEMPLATE
        try:
            # Mapper les polices du template vers les polices système
            font_mapping = {
                'Helvetica-Bold': 'arialbd.ttf',
                'Helvetica': 'arial.ttf',
                'Arial-Bold': 'arialbd.ttf',
                'Arial': 'arial.ttf',
                'Times-Bold': 'timesbd.ttf',
                'Times': 'times.ttf',
                'Courier-Bold': 'courbd.ttf',
                'Courier': 'cour.ttf',
            }
            
            # Utiliser les polices définies dans le template
            title_font_name = font_mapping.get(template.police_titre, 'arialbd.ttf')
            text_font_name = font_mapping.get(template.police_texte, 'arial.ttf')
            
            title_font = ImageFont.truetype(title_font_name, int(template.taille_titre * dpi / 72))
            text_font = ImageFont.truetype(text_font_name, int(template.taille_texte * dpi / 72))
            small_font = ImageFont.truetype(text_font_name, int(template.taille_texte * 0.8 * dpi / 72))
            # Police pour les codes (plus fine pour 4K)
            code_font = ImageFont.truetype(text_font_name, int(template.taille_texte * 0.7 * dpi / 72))
            logger.info(f"✅ [PDF] Polices chargées selon template: {template.police_titre} ({template.taille_titre}pt), {template.police_texte} ({template.taille_texte}pt) - DPI: {dpi}")
        except Exception as e:
            # Fallback si les polices ne sont pas disponibles
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            code_font = ImageFont.load_default()
            logger.warning(f"⚠️ [PDF] Polices par défaut utilisées (erreur: {e})")
            logger.warning(f"⚠️ [PDF] Utilisation des polices par défaut")
        
        # Couleurs dynamiques basées sur le template
        def hex_to_rgb(hex_color):
            """Convertir hex en RGB"""
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        couleur_principale = hex_to_rgb(template.couleur_principale)
        couleur_secondaire = hex_to_rgb(template.couleur_secondaire)
        couleur_texte = hex_to_rgb(template.couleur_texte)
        couleur_bordure = hex_to_rgb(template.border_color)
        white = (255, 255, 255)
        
        logger.info(f"🔍 [PDF] Couleurs dynamiques: Principal={couleur_principale}, Secondaire={couleur_secondaire}, Texte={couleur_texte}, Bordure={couleur_bordure}")
        
        # Fonction pour dessiner des rectangles avec coins arrondis
        def draw_rounded_rectangle(draw, xy, fill=None, outline=None, width=1, radius=0):
            """Dessiner un rectangle avec coins arrondis"""
            x1, y1, x2, y2 = xy
            if radius == 0:
                draw.rectangle(xy, fill=fill, outline=outline, width=width)
                return
            
            # Dessiner les coins arrondis
            draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill, outline=outline, width=width)  # Coin supérieur gauche
            draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill, outline=outline, width=width)  # Coin supérieur droit
            draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill, outline=outline, width=width)  # Coin inférieur gauche
            draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill, outline=outline, width=width)  # Coin inférieur droit
            
            # Dessiner les rectangles pour remplir les côtés
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)  # Horizontal
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)  # Vertical
        
        # Ligne 1: Code-barres et date - OPTIMISÉ 4K ULTRA
        code_area_height = int(35 * mm_to_px)  # 35mm en pixels 4K Ultra (plus d'espace)
        date_area_width = int(45 * mm_to_px)   # 45mm en pixels 4K Ultra
        
        # Fond pour le code-barres avec bordures arrondies
        border_radius_px = int(template.border_radius * mm_to_px)
        border_width_px = int(template.border_width * mm_to_px)
        
        if template.border_enabled:
            draw_rounded_rectangle(draw, [0, 0, width - date_area_width, code_area_height], 
                                 fill=couleur_secondaire, outline=couleur_bordure, 
                                 width=border_width_px, radius=border_radius_px)
        else:
            draw.rectangle([0, 0, width - date_area_width, code_area_height], fill=couleur_secondaire)
        
        # Générer le code-barres ou QR code en haute résolution
        code_img = None
        if template.code_type == 'barcode' or template.code_type == 'both':
            logger.info(f"🔍 [PDF] Génération code-barres dynamique avec python-barcode")
            from barcode import Code128
            from barcode.writer import ImageWriter
            
            barcode_class = Code128(etiquette.code_data, writer=ImageWriter())
            # Options dynamiques basées sur le template - DIMENSIONS PERSONNALISÉES
            # Calculer les dimensions basées sur les paramètres du template
            module_width_factor = 0.3 if template.code_quality == 'ultra' else 0.4
            module_height_factor = 1.2 if template.code_quality == 'ultra' else 1.0
            font_size_factor = 1.2 if template.code_quality == 'ultra' else 1.0
            
            options = {
                'module_width': module_width_factor * dpi / 72,
                'module_height': (template.code_height * module_height_factor) * dpi / 72,  # Utiliser code_height du template
                'quiet_zone': 8.0 * dpi / 72,
                'font_size': int(template.taille_texte * font_size_factor * dpi / 72),
                'text_distance': 6.0 * dpi / 72,
                'background': 'white',
                'foreground': 'black',
                'write_text': True,
                'center_text': True,
            }
            
            logger.info(f"🔍 [PDF] Code-barres - Dimensions: {template.code_width}x{template.code_height}mm, Qualité: {template.code_quality}")
            
            code_buffer = io.BytesIO()
            barcode_class.write(code_buffer, options=options)
            code_buffer.seek(0)
            code_img = Image.open(code_buffer)
            
        elif template.code_type == 'qr':
            logger.info(f"🔍 [PDF] Génération QR code dynamique avec qrcode")
            import qrcode
            from qrcode.image.pil import PilImage
            
            # Calculer les paramètres QR basés sur la qualité et les dimensions du template
            error_correction = qrcode.constants.ERROR_CORRECT_M if template.code_quality == 'ultra' else qrcode.constants.ERROR_CORRECT_L
            box_size_factor = 6 if template.code_quality == 'ultra' else 8
            border_factor = 6 if template.code_quality == 'ultra' else 4
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=int((template.code_width / box_size_factor) * dpi / 72),  # Utiliser code_width du template
                border=int(border_factor * dpi / 72),
            )
            
            logger.info(f"🔍 [PDF] QR Code - Dimensions: {template.code_width}x{template.code_height}mm, Qualité: {template.code_quality}")
            qr.add_data(etiquette.code_data)
            qr.make(fit=True)
            
            code_img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
        
        # Coller le code sur l'image avec positionnement dynamique - DIMENSIONS PERSONNALISÉES
        if code_img:
            # Redimensionner le code basé sur les dimensions personnalisées du template
            # Utiliser code_width et code_height du template, avec fallback sur code_size
            code_max_width = int(template.code_width * mm_to_px) if template.code_width else int(template.code_size * mm_to_px)
            code_max_height = int(template.code_height * mm_to_px) if template.code_height else int(template.code_size * mm_to_px)
            
            # Calculer le ratio pour le redimensionnement
            img_ratio = code_img.width / code_img.height
            box_ratio = code_max_width / code_max_height
            
            if img_ratio > box_ratio:
                new_width = code_max_width
                new_height = int(new_width / img_ratio)
            else:
                new_height = code_max_height
                new_width = int(new_height * img_ratio)

            # Redimensionnement avec qualité basée sur le template
            code_img = code_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Améliorer la netteté selon la qualité choisie
            if template.code_quality == 'ultra':
                from PIL import ImageFilter
                code_img = code_img.filter(ImageFilter.SHARPEN)
            
            # Positionnement dynamique basé sur le template
            if template.code_position == 'left':
                code_x = int(5 * mm_to_px)
            elif template.code_position == 'right':
                code_x = int(width*0.7) - new_width - int(5 * mm_to_px)
            else:  # center
                code_x = (int(width*0.7) - new_width) // 2
            
            code_y = (code_area_height - new_height) // 2
            
            img.paste(code_img, (code_x, code_y))
            logger.info(f"✅ [PDF] Code collé: {template.code_type} ({template.code_width}x{template.code_height}mm) à position {template.code_position} - Qualité: {template.code_quality}")
        else:
            # Texte de substitution en cas d'échec
            fallback_text = "Code non disponible"
            text_width_fb = draw.textlength(fallback_text, font=small_font)
            text_x_fb = (int(width*0.7) - text_width_fb) // 2
            text_y_fb = (code_area_height - int(10 * dpi / 72)) // 2
            draw.text((text_x_fb, text_y_fb), fallback_text, fill=couleur_texte, font=small_font)
            logger.warning(f"⚠️ [PDF] Code image non générée, affichage du texte de substitution.")
        
        # Fond pour la date avec bordures arrondies
        date_x = width - date_area_width
        if template.border_enabled:
            draw_rounded_rectangle(draw, [date_x, 0, width, code_area_height], 
                                 fill=couleur_principale, outline=couleur_bordure, 
                                 width=border_width_px, radius=border_radius_px)
        else:
            draw.rectangle([date_x, 0, width, code_area_height], fill=couleur_principale)
        
        # Centrer la date dans l'espace
        date_text = datetime.now().strftime('%m/%d/%Y')
        date_text_width = draw.textlength(date_text, font=text_font)
        date_text_x = date_x + (date_area_width - date_text_width) // 2
        date_text_y = (code_area_height - int(template.taille_texte * dpi / 72)) // 2
        draw.text((date_text_x, date_text_y), date_text, fill=white, font=text_font)
        
        # Calculer le total d'articles AVANT de l'utiliser
        total_articles = 0
        if etiquette.cart_items:
            total_articles = sum(item.get('quantite', 0) for item in etiquette.cart_items)
        
        # Afficher le total d'articles dans un cercle au milieu entre ID YZ et date
        if total_articles > 0:
            # Position du cercle (au milieu entre la zone du code et la zone de date)
            circle_x = date_x - int(15 * mm_to_px)  # 15mm avant la zone de date
            circle_y = int(code_area_height / 2)  # Au milieu verticalement
            circle_radius = int(6 * mm_to_px)  # 6mm de rayon
            
            # Dessiner le cercle
            draw.ellipse([circle_x - circle_radius, circle_y - circle_radius, 
                         circle_x + circle_radius, circle_y + circle_radius], 
                        fill=couleur_principale, outline=couleur_bordure, width=border_width_px)
            
            # Centrer le texte dans le cercle
            total_text = str(total_articles)
            text_width = draw.textlength(total_text, font=small_font)
            text_height = int(template.taille_texte * 0.7 * dpi / 72)
            text_x = circle_x - text_width // 2
            text_y = circle_y - text_height // 2
            
            draw.text((text_x, text_y), total_text, fill=white, font=small_font)
        
        # Récupérer les vraies données de la commande
        commande = None
        if etiquette.commande_id:
            try:
                commande = Commande.objects.get(id=int(etiquette.commande_id))
                logger.info(f"✅ [PDF] Commande trouvée: {commande.num_cmd}")
            except (Commande.DoesNotExist, ValueError):
                pass
        
        # Le total d'articles a déjà été calculé plus haut
        
        # Ligne 2: Informations client - OPTIMISÉ 4K ULTRA
        y_pos = int(40 * mm_to_px)  # 40mm en pixels 4K Ultra (plus d'espace)
        margin_x = int(6 * mm_to_px)  # 6mm de marge pour 4K Ultra
        
        client_info_parts = []
        if etiquette.client_nom:
            client_info_parts.append(f"Client: {etiquette.client_nom}")
        elif commande and commande.client:
            client_info_parts.append(f"Client: {commande.client.nom} {commande.client.prenom}")
        
        if commande and commande.client:
            if commande.client.numero_tel:
                client_info_parts.append(f"Tél: {commande.client.numero_tel}")
            if commande.client.adresse:
                client_info_parts.append(f"Adresse: {commande.client.adresse}")
            if commande.ville:
                client_info_parts.append(f"Ville: {commande.ville.nom}")
        
        line_height = int(7 * mm_to_px)  # 7mm entre les lignes pour 4K Ultra
        for info in client_info_parts:
            draw.text((margin_x, y_pos), info, fill=couleur_texte, font=text_font)
            y_pos += line_height
        
        # Section Panier - DYNAMIQUE
        if etiquette.cart_items:
            y_pos += int(5 * mm_to_px) # Espace avant le panier
            draw.text((margin_x, y_pos), "Articles du panier:", fill=couleur_texte, font=text_font)
            y_pos += int(6 * mm_to_px)
            for item in etiquette.cart_items:
                item_text = f"- {item.get('nom', '')} {item.get('variante', '')} x{item.get('quantite', 1)}"
                draw.text((margin_x + int(5 * mm_to_px), y_pos), item_text, fill=couleur_texte, font=small_font)
                y_pos += int(5 * mm_to_px)
            y_pos += int(5 * mm_to_px) # Espace après le panier

        # Ligne de séparation - OPTIMISÉ 4K ULTRA
        y_pos += int(4 * mm_to_px)  # 4mm d'espace pour 4K Ultra
        line_width = int(0.8 * mm_to_px)  # 0.8mm d'épaisseur pour 4K Ultra
        draw.line([(margin_x, y_pos), (width - margin_x, y_pos)], fill=couleur_texte, width=line_width)
        y_pos += int(6 * mm_to_px)  # 6mm d'espace après la ligne pour 4K Ultra
        
        # Ligne 4: Prix et contact - Dynamique selon le type d'étiquette
        if template.type_etiquette == 'livraison':
            # Pour les étiquettes de livraison, afficher le prix
            price_value = "Prix non disponible"
            if commande and commande.total_cmd:
                price_value = f"{commande.total_cmd} DH"
            draw.text((margin_x, y_pos), price_value, fill=couleur_texte, font=title_font)
            draw.text((margin_x, y_pos + int(10 * mm_to_px)), "YOZAK", fill=couleur_texte, font=text_font)
        elif template.type_etiquette == 'article':
            # Pour les étiquettes d'article, afficher le nom de l'article
            article_name = etiquette.nom_article or "Article non défini"
            draw.text((margin_x, y_pos), article_name, fill=couleur_texte, font=title_font)
            draw.text((margin_x, y_pos + int(10 * mm_to_px)), "YOZAK", fill=couleur_texte, font=text_font)
        elif template.type_etiquette == 'commande':
            # Pour les étiquettes de commande, afficher le numéro de commande
            cmd_ref = etiquette.reference or "Commande non définie"
            draw.text((margin_x, y_pos), cmd_ref, fill=couleur_texte, font=title_font)
            draw.text((margin_x, y_pos + int(10 * mm_to_px)), "YOZAK", fill=couleur_texte, font=text_font)
        elif template.type_etiquette == 'stock':
            # Pour les étiquettes de stock, afficher les informations de stock
            stock_info = "Stock disponible"
            draw.text((margin_x, y_pos), stock_info, fill=couleur_texte, font=title_font)
            draw.text((margin_x, y_pos + int(10 * mm_to_px)), "YOZAK", fill=couleur_texte, font=text_font)
        else:
            # Par défaut, afficher le prix
            price_value = "Prix non disponible"
            if commande and commande.total_cmd:
                price_value = f"{commande.total_cmd} DH"
            draw.text((margin_x, y_pos), price_value, fill=couleur_texte, font=title_font)
            draw.text((margin_x, y_pos + int(10 * mm_to_px)), "YOZAK", fill=couleur_texte, font=text_font)
        
        # Informations de contact - Dynamique basé sur le template
        contact_city = "VILLE NON DÉFINIE"
        if commande and commande.ville:
            contact_city = commande.ville.nom
        
        contact_info = [
            contact_city,
            "www.yoozak.com",
            "06 34 21 56 39 / 47"
        ]
        
        # Zone de contact dynamique - OPTIMISÉ 4K ULTRA
        contact_area_width = int(55 * mm_to_px)  # 55mm de largeur pour 4K Ultra
        contact_area_height = int(30 * mm_to_px)  # 30mm de hauteur pour 4K Ultra
        contact_x = width - contact_area_width - margin_x
        contact_y = y_pos
        
        # Fond pour le contact avec bordures arrondies
        if template.border_enabled:
            draw_rounded_rectangle(draw, [contact_x, contact_y, width - margin_x, contact_y + contact_area_height], 
                                 fill=couleur_principale, outline=couleur_bordure, 
                                 width=border_width_px, radius=border_radius_px)
        else:
            draw.rectangle([contact_x, contact_y, width - margin_x, contact_y + contact_area_height], fill=couleur_principale)
        
        # Centrer le texte de contact dans la zone - OPTIMISÉ 4K ULTRA
        contact_text_y = contact_y + int(4 * mm_to_px)  # 4mm de marge pour 4K Ultra
        for info in contact_info:
            contact_text_width = draw.textlength(info, font=text_font)
            contact_text_x = contact_x + (contact_area_width - contact_text_width) // 2
            draw.text((contact_text_x, contact_text_y), info, fill=white, font=text_font)
            contact_text_y += int(7 * mm_to_px)  # 7mm entre les lignes pour 4K Ultra
        
        # Ajouter la bordure principale autour de tout le ticket
        if template.border_enabled:
            # Bordure extérieure avec coins arrondis
            draw_rounded_rectangle(draw, [0, 0, width-1, height-1], 
                                 fill=None, outline=couleur_bordure, 
                                 width=border_width_px, radius=border_radius_px)
            logger.info(f"✅ [PDF] Bordure principale ajoutée: {template.border_width}mm, couleur: {template.border_color}")
        
        logger.info(f"✅ [PDF] Image 4K Ultra de l'étiquette créée avec succès ({width}x{height} pixels, DPI: {dpi})")
        
        # Convertir l'image en PDF avec qualité optimale - OPTIMISÉ 4K ULTRA
        pdf_buffer = io.BytesIO()
        # Sauvegarder avec qualité maximale et DPI spécifié - OPTIMISÉ 4K ULTRA
        img.save(pdf_buffer, format='PDF', quality=100, dpi=(dpi, dpi), optimize=False)
        pdf_buffer.seek(0)
        
        # Créer la réponse HTTP avec headers optimisés
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="etiquette_{etiquette.reference}_4K_Ultra.pdf"'
        response['Content-Length'] = str(len(pdf_buffer.getvalue()))
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Marquer l'étiquette comme imprimée
        etiquette.statut = 'printed'
        etiquette.date_impression = datetime.now()
        etiquette.save()
        
        logger.info(f"✅ [PDF] PDF généré avec succès")
        return response
        
    except Exception as e:
        logger.error(f"❌ [PDF] Erreur lors de la génération: {str(e)}")
        logger.error(f"❌ [PDF] Type d'erreur: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [PDF] Traceback: {traceback.format_exc()}")
        
        # Retourner une erreur
        return HttpResponse(f'Erreur de génération PDF: {str(e)}', status=500)


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
    context = {
        'templates_count': EtiquetteTemplate.objects.filter(actif=True).count(),
        'etiquettes_count': Etiquette.objects.count(),
        'etiquettes_ready': Etiquette.objects.filter(statut='ready').count(),
        'etiquettes_printed': Etiquette.objects.filter(statut='printed').count(),
        'recent_templates': EtiquetteTemplate.objects.filter(actif=True).order_by('-date_creation')[:5],
        'recent_etiquettes': Etiquette.objects.order_by('-date_creation')[:10],
    }
    return render(request, 'etiquettes_pro/dashboard.html', context)


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
def delete_template(request, pk):
    """Supprimer un template"""
    template = get_object_or_404(EtiquetteTemplate, pk=pk)
    # TODO: Implémenter la suppression
    return redirect('etiquettes_pro:template_list')


@superviseur_required
def etiquette_list(request):
    """Liste des étiquettes avec filtres et pagination"""
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
    
    # Pagination
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
        'etiquettes': etiquettes_page,
        'templates': templates,
        'total_count': total_count,
        'draft_count': draft_count,
        'ready_count': ready_count,
        'printed_count': printed_count,
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
    etiquettes = Etiquette.objects.all()[:50]  # Limiter à 50
    data = [{'id': e.id, 'reference': e.reference, 'statut': e.statut} for e in etiquettes]
    return JsonResponse({'etiquettes': data})


@superviseur_required
@can_print_etiquettes
def generate_etiquettes_commandes_confirmees(request):
    """Générer automatiquement des étiquettes pour toutes les commandes confirmées"""
    try:
        # Récupérer le template par défaut
        template = EtiquetteTemplate.objects.filter(
            nom='Template Livraison Standard',
            actif=True
        ).first()
        
        if not template:
            messages.error(request, 'Template par défaut "Template Livraison Standard" non trouvé. Veuillez le créer d\'abord.')
            return redirect('etiquettes_pro:dashboard')
        
        # Récupérer uniquement les commandes qui ont des articles dans leur panier
        commandes_avec_articles = Commande.objects.filter(
            paniers__isnull=False
        ).select_related('client').distinct()
        
        if not commandes_avec_articles.exists():
            messages.info(request, 'Aucune commande avec des articles dans le panier trouvée.')
            return redirect('etiquettes_pro:dashboard')
        
        # Générer les étiquettes
        etiquettes_creees = []
        for commande in commandes_avec_articles:
            # Vérifier si une étiquette existe déjà pour cette commande
            etiquette_existante = Etiquette.objects.filter(
                commande_id=str(commande.id),
                template=template
            ).first()
            
            if etiquette_existante:
                continue  # Passer cette commande si l'étiquette existe déjà
            
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
                    "variante": variante_nom,
                    "quantite": panier.quantite,
                    "prix_unitaire": float(panier.sous_total / panier.quantite) if panier.quantite > 0 else 0,
                    "sous_total": float(panier.sous_total)
                }
                cart_items_data.append(item_data)
            
            # Créer l'étiquette
            etiquette = Etiquette.objects.create(
                template=template,
                reference=f"{commande.id:06d}",
                nom_article=f"Commande {commande.num_cmd or commande.id_yz}",
                commande_id=str(commande.id),
                client_nom=f"{commande.client.nom} {commande.client.prenom}" if commande.client else "",
                code_data=f"{commande.id:06d}",
                statut='ready',
                cree_par=request.user,
                cart_items=cart_items_data  # Ajouter les articles du panier
            )
            etiquettes_creees.append(etiquette)
        
        if etiquettes_creees:
            messages.success(request, f'{len(etiquettes_creees)} étiquettes générées avec succès pour les commandes avec articles.')
        else:
            messages.info(request, 'Toutes les commandes avec articles ont déjà des étiquettes.')
        
        return redirect('etiquettes_pro:etiquettes_commandes_confirmees')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération des étiquettes: {str(e)}')
        return redirect('etiquettes_pro:dashboard')


@superviseur_required
def etiquettes_commandes_confirmees(request):
    """Afficher les étiquettes des commandes confirmées"""
    # Récupérer le template par défaut
    template = EtiquetteTemplate.objects.filter(
        nom='Template Livraison Standard',
        actif=True
    ).first()
    
    if not template:
        messages.error(request, 'Template par défaut non trouvé.')
        return redirect('etiquettes_pro:dashboard')
    
    # Récupérer les étiquettes des commandes confirmées
    etiquettes = Etiquette.objects.filter(
        template=template,
        commande_id__isnull=False
    ).select_related('template', 'cree_par').order_by('-date_creation')
    
    # Pagination
    paginator = Paginator(etiquettes, 20)
    page_number = request.GET.get('page')
    etiquettes_page = paginator.get_page(page_number)
    
    # Statistiques
    total_etiquettes = etiquettes.count()
    etiquettes_ready = etiquettes.filter(statut='ready').count()
    etiquettes_printed = etiquettes.filter(statut='printed').count()
    
    # Récupérer les commandes avec articles sans étiquettes
    commandes_avec_etiquettes = set(etiquettes.values_list('commande_id', flat=True))
    commandes_avec_articles = Commande.objects.filter(
        paniers__isnull=False
    ).select_related('client').distinct()
    
    commandes_sans_etiquettes = commandes_avec_articles.exclude(
        id__in=[int(cmd_id) for cmd_id in commandes_avec_etiquettes if cmd_id.isdigit()]
    )
    
    context = {
        'etiquettes': etiquettes_page,
        'template': template,
        'total_etiquettes': total_etiquettes,
        'etiquettes_ready': etiquettes_ready,
        'etiquettes_printed': etiquettes_printed,
        'commandes_sans_etiquettes_count': commandes_sans_etiquettes.count(),
        'commandes_avec_articles_count': commandes_avec_articles.count(),
    }
    
    return render(request, 'etiquettes_pro/etiquettes_commandes_confirmees.html', context)