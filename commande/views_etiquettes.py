"""
Vues pour la génération d'étiquettes professionnelles avec ReportLab
"""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
import json
import io
from datetime import datetime

# ReportLab imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import Color, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Models
from .models import Commande, Panier, EtiquetteTemplate
from article.models import Article
from client.models import Client


class EtiquetteGeneratorView(View):
    """Vue principale pour générer les étiquettes"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Afficher l'interface de génération d'étiquettes"""
        templates = EtiquetteTemplate.objects.filter(is_active=True)
        commandes = Commande.objects.select_related('client').prefetch_related('paniers__article')[:50]
        
        context = {
            'templates': templates,
            'commandes': commandes,
        }
        return render(request, 'commande/etiquettes_generator.html', context)
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Générer les étiquettes PDF"""
        try:
            data = json.loads(request.body)
            commande_ids = data.get('commande_ids', [])
            template_id = data.get('template_id')
            format_type = data.get('format', 'barcode')  # 'barcode' ou 'qr'
            
            if not commande_ids:
                return JsonResponse({'error': 'Aucune commande sélectionnée'}, status=400)
            
            # Récupérer le template
            template = get_object_or_404(EtiquetteTemplate, id=template_id, is_active=True)
            
            # Récupérer les commandes
            commandes = Commande.objects.filter(
                id__in=commande_ids
            ).select_related('client').prefetch_related('paniers__article')
            
            if not commandes.exists():
                return JsonResponse({'error': 'Aucune commande trouvée'}, status=404)
            
            # Générer le PDF
            pdf_buffer = self.generate_etiquettes_pdf(commandes, template, format_type)
            
            # Retourner le PDF
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="etiquettes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            return response
            
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de la génération: {str(e)}'}, status=500)
    
    def generate_etiquettes_pdf(self, commandes, template, format_type):
        """Générer le PDF des étiquettes"""
        buffer = io.BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=template.get_dimensions(),
            rightMargin=template.margin_right * mm,
            leftMargin=template.margin_left * mm,
            topMargin=template.margin_top * mm,
            bottomMargin=template.margin_bottom * mm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=template.font_size_title,
            textColor=Color(0.17, 0.24, 0.31),  # #2c3e50
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        
        text_style = ParagraphStyle(
            'CustomText',
            parent=styles['Normal'],
            fontSize=template.font_size_text,
            textColor=Color(0.2, 0.2, 0.2),  # #333333
            alignment=TA_LEFT,
            spaceAfter=6,
        )
        
        # Construire le contenu
        story = []
        
        for commande in commandes:
            # Générer une étiquette pour chaque article de la commande
            for panier in commande.paniers.all():
                # En-tête
                if template.show_header:
                    header_text = f"Commande {commande.id_yz or commande.num_cmd}"
                    story.append(Paragraph(header_text, title_style))
                    story.append(Spacer(1, 6))
                
                # Informations de l'article
                article_info = f"""
                <b>Référence:</b> {panier.article.nom}<br/>
                <b>Variante:</b> {panier.variante.nom if panier.variante else 'Standard'}<br/>
                <b>Quantité:</b> {panier.quantite}<br/>
                <b>Client:</b> {commande.client.nom}<br/>
                <b>Date:</b> {commande.date_cmd.strftime('%d/%m/%Y')}
                """
                story.append(Paragraph(article_info, text_style))
                story.append(Spacer(1, 12))
                
                # Code-barres ou QR code
                if format_type == 'barcode' and template.show_barcode:
                    barcode = self.create_barcode(panier.article.nom, template)
                    if barcode:
                        story.append(barcode)
                        story.append(Spacer(1, 12))
                
                elif format_type == 'qr' and template.show_qr:
                    qr_code = self.create_qr_code(panier.article.nom, template)
                    if qr_code:
                        story.append(qr_code)
                        story.append(Spacer(1, 12))
                
                # Pied de page
                if template.show_footer:
                    footer_text = f"<b>Yoozak</b> - Système de gestion des commandes"
                    story.append(Paragraph(footer_text, text_style))
                
                # Saut de page entre les étiquettes
                story.append(Spacer(1, 20))
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def create_barcode(self, text, template):
        """Créer un code-barres"""
        try:
            # Créer le code-barres
            barcode = code128.Code128(
                text,
                barWidth=template.barcode_width * mm,
                barHeight=template.barcode_height * mm,
                fontSize=template.font_size_barcode
            )
            
            # Créer un Drawing pour le code-barres
            drawing = Drawing(200, 100)
            drawing.add(barcode)
            
            return drawing
            
        except Exception as e:
            print(f"Erreur création code-barres: {e}")
            return None
    
    def create_qr_code(self, text, template):
        """Créer un QR code"""
        try:
            # Créer le QR code
            qr_code = qr.QrCodeWidget(text)
            
            # Créer un Drawing pour le QR code
            drawing = Drawing(template.qr_size, template.qr_size)
            drawing.add(qr_code)
            
            return drawing
            
        except Exception as e:
            print(f"Erreur création QR code: {e}")
            return None


@login_required
def get_commande_articles(request, commande_id):
    """API pour récupérer les articles d'une commande"""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        articles = []
        
        for panier in commande.paniers.select_related('article', 'variante').all():
            articles.append({
                'id': panier.article.id,
                'nom': panier.article.nom,
                'variante': panier.variante.nom if panier.variante else 'Standard',
                'quantite': panier.quantite,
                'reference': panier.article.nom,
            })
        
        return JsonResponse({
            'success': True,
            'commande': {
                'id': commande.id,
                'num_cmd': commande.num_cmd,
                'id_yz': commande.id_yz,
                'client': commande.client.nom,
                'date': commande.date_cmd.strftime('%d/%m/%Y'),
            },
            'articles': articles
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def preview_etiquette(request, commande_id, template_id):
    """Aperçu d'une étiquette"""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        template = get_object_or_404(EtiquetteTemplate, id=template_id, is_active=True)
        
        # Générer un PDF d'aperçu avec un seul article
        if commande.paniers.exists():
            panier = commande.paniers.first()
            pdf_buffer = EtiquetteGeneratorView().generate_etiquettes_pdf(
                [commande], template, 'barcode'
            )
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="apercu_etiquette.pdf"'
            return response
        else:
            return JsonResponse({'error': 'Aucun article dans cette commande'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
