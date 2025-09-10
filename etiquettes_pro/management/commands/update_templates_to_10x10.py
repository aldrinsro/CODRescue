from django.core.management.base import BaseCommand
from etiquettes_pro.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Mettre à jour tous les templates existants pour utiliser le format 10x10 cm'

    def handle(self, *args, **options):
        # Mettre à jour tous les templates existants
        templates_updated = 0
        
        for template in EtiquetteTemplate.objects.all():
            # Mettre à jour le format et les dimensions
            template.format_page = '10x10'
            template.largeur = 100.0
            template.hauteur = 100.0
            
            # Ajuster les paramètres d'impression pour le format 10x10 cm
            template.print_code_width = 200  # Réduire pour s'adapter au format 10x10
            template.print_code_height = 60
            template.print_contact_width = 200
            template.print_padding = 10
            template.print_font_size_title = 12
            template.print_font_size_text = 10
            template.print_font_size_small = 8
            
            # Ajuster les marges pour le format 10x10 cm
            template.print_margin_top = 5
            template.print_margin_bottom = 5
            template.print_margin_left = 5
            template.print_margin_right = 5
            
            template.save()
            templates_updated += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Template "{template.nom}" mis à jour vers le format 10x10 cm')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {templates_updated} template(s) mis à jour vers le format 10x10 cm')
        )
