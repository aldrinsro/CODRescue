from django.core.management.base import BaseCommand
from etiquettes_pro.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Met à jour les templates existants avec les paramètres de personnalisation d\'impression par défaut'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Mise à jour des templates avec les paramètres d\'impression...')
        
        templates_updated = 0
        
        for template in EtiquetteTemplate.objects.all():
            updated = False
            
            # Paramètres de dimensions des codes
            if template.print_code_width == 250:  # Valeur par défaut
                template.print_code_width = 250
                updated = True
                
            if template.print_code_height == 80:  # Valeur par défaut
                template.print_code_height = 80
                updated = True
                
            if template.print_contact_width == 250:  # Valeur par défaut
                template.print_contact_width = 250
                updated = True
            
            # Paramètres d'affichage (tous activés par défaut)
            if template.print_show_prices is None:
                template.print_show_prices = True
                updated = True
                
            if template.print_show_articles is None:
                template.print_show_articles = True
                updated = True
                
            if template.print_show_client_info is None:
                template.print_show_client_info = True
                updated = True
                
            if template.print_show_contact_info is None:
                template.print_show_contact_info = True
                updated = True
                
            if template.print_show_brand is None:
                template.print_show_brand = True
                updated = True
                
            if template.print_show_date is None:
                template.print_show_date = True
                updated = True
                
            if template.print_show_total_circle is None:
                template.print_show_total_circle = True
                updated = True
            
            # Paramètres de mise en page
            if template.print_margin_top == 10:  # Valeur par défaut
                template.print_margin_top = 10
                updated = True
                
            if template.print_margin_bottom == 10:  # Valeur par défaut
                template.print_margin_bottom = 10
                updated = True
                
            if template.print_margin_left == 10:  # Valeur par défaut
                template.print_margin_left = 10
                updated = True
                
            if template.print_margin_right == 10:  # Valeur par défaut
                template.print_margin_right = 10
                updated = True
                
            if template.print_padding == 15:  # Valeur par défaut
                template.print_padding = 15
                updated = True
            
            # Paramètres de police
            if template.print_font_size_title == 16:  # Valeur par défaut
                template.print_font_size_title = 16
                updated = True
                
            if template.print_font_size_text == 12:  # Valeur par défaut
                template.print_font_size_text = 12
                updated = True
                
            if template.print_font_size_small == 10:  # Valeur par défaut
                template.print_font_size_small = 10
                updated = True
            
            if updated:
                template.save()
                templates_updated += 1
                self.stdout.write(f'✅ Template "{template.nom}" mis à jour')
        
        if templates_updated > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 {templates_updated} template(s) mis à jour avec succès !'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️ Aucun template n\'a nécessité de mise à jour.'
                )
            )
        
        self.stdout.write('✨ Personnalisation d\'impression configurée !')
