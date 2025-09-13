"""
Commande Django pour créer un template d'étiquette par défaut
"""
from django.core.management.base import BaseCommand
from commande.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Crée un template d\'étiquette par défaut pour les tests'

    def handle(self, *args, **options):
        # Vérifier si un template par défaut existe déjà
        if EtiquetteTemplate.objects.filter(name='Template Professionnel Standard').exists():
            self.stdout.write(
                self.style.WARNING('Le template par défaut existe déjà.')
            )
            return

        # Créer le template par défaut
        template = EtiquetteTemplate.objects.create(
            name='Template Professionnel Standard',
            width=180,
            height=260,
            margin_top=10,
            margin_bottom=10,
            margin_left=10,
            margin_right=10,
            font_family='Helvetica',
            font_size_title=16,
            font_size_text=12,
            font_size_barcode=14,
            color_header='#2c3e50',
            color_footer='#2c3e50',
            color_text='#333333',
            barcode_width=4,
            barcode_height=80,
            barcode_format='CODE128B',
            qr_size=300,
            show_header=True,
            show_footer=True,
            show_barcode=True,
            show_qr=False,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Template par défaut créé avec succès: {template.name} (ID: {template.id})'
            )
        )

        # Créer un template pour QR codes
        qr_template = EtiquetteTemplate.objects.create(
            name='Template QR Code Standard',
            width=180,
            height=260,
            margin_top=10,
            margin_bottom=10,
            margin_left=10,
            margin_right=10,
            font_family='Helvetica',
            font_size_title=16,
            font_size_text=12,
            font_size_barcode=14,
            color_header='#2c3e50',
            color_footer='#2c3e50',
            color_text='#333333',
            barcode_width=4,
            barcode_height=80,
            barcode_format='CODE128B',
            qr_size=300,
            show_header=True,
            show_footer=True,
            show_barcode=False,
            show_qr=True,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Template QR Code créé avec succès: {qr_template.name} (ID: {qr_template.id})'
            )
        )

        # Créer un template compact
        compact_template = EtiquetteTemplate.objects.create(
            name='Template Compact',
            width=100,
            height=150,
            margin_top=5,
            margin_bottom=5,
            margin_left=5,
            margin_right=5,
            font_family='Helvetica',
            font_size_title=12,
            font_size_text=10,
            font_size_barcode=12,
            color_header='#2c3e50',
            color_footer='#2c3e50',
            color_text='#333333',
            barcode_width=2,
            barcode_height=40,
            barcode_format='CODE128B',
            qr_size=150,
            show_header=True,
            show_footer=False,
            show_barcode=True,
            show_qr=False,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Template Compact créé avec succès: {compact_template.name} (ID: {compact_template.id})'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Tous les templates ont été créés avec succès !'
            )
        )
        self.stdout.write(
            'Vous pouvez maintenant accéder au générateur d\'étiquettes à l\'adresse: /commande/etiquettes/'
        )
