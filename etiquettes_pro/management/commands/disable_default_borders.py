from django.core.management.base import BaseCommand
from etiquettes_pro.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Désactiver les bordures par défaut du template standard'

    def handle(self, *args, **options):
        # Trouver le template par défaut
        try:
            template = EtiquetteTemplate.objects.get(nom='Template Livraison Standard')
            
            # Désactiver les bordures
            template.border_enabled = False
            template.border_width = 0.0
            template.border_radius = 0.0
            template.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Bordures désactivées pour le template: {template.nom}')
            )
            
        except EtiquetteTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Template "Template Livraison Standard" non trouvé.')
            )
