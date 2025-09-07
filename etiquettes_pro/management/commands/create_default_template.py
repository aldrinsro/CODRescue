from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from etiquettes_pro.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Créer le template par défaut pour les étiquettes de livraison'

    def handle(self, *args, **options):
        # Vérifier si le template existe déjà
        if EtiquetteTemplate.objects.filter(nom='Template Livraison Standard').exists():
            self.stdout.write(
                self.style.WARNING('Le template par défaut existe déjà.')
            )
            return

        # Créer le template par défaut
        template = EtiquetteTemplate.objects.create(
            nom='Template Livraison Standard',
            description='Template par défaut pour les étiquettes de livraison avec code-barres et informations client',
            type_etiquette='livraison',
            format_page='A4',
            largeur=210.0,
            hauteur=297.0,
            code_type='barcode',
            code_size=80,
            code_position='left',
            # Nouvelles dimensions personnalisées des codes
            code_width=80,
            code_height=25,
            code_quality='high',
            # Paramètres de bordures
            border_enabled=False,
            border_width=0.0,
            border_color='#000000',
            border_radius=0.0,
            police_titre='Helvetica-Bold',
            taille_titre=16,
            police_texte='Helvetica',
            taille_texte=12,
            couleur_principale='#374151',  # Gris foncé pour l'en-tête
            couleur_secondaire='#6B7280',  # Gris moyen pour les sections
            couleur_texte='#1F2937',       # Gris très foncé pour le texte
            actif=True,
            cree_par=User.objects.filter(is_superuser=True).first() or User.objects.first()
        )

        self.stdout.write(
            self.style.SUCCESS(f'Template par défaut créé avec succès: {template.nom}')
        )
