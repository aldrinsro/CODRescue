from django.core.management.base import BaseCommand
from etiquettes_pro.models import EtiquetteTemplate


class Command(BaseCommand):
    help = 'Mettre à jour le template existant avec les icônes professionnelles'

    def handle(self, *args, **options):
        # Trouver le template par défaut
        try:
            template = EtiquetteTemplate.objects.get(nom='Template Livraison Standard')
            
            # Mettre à jour avec les icônes professionnelles
            template.icone_client = 'fas fa-user'
            template.icone_telephone = 'fas fa-phone'
            template.icone_adresse = 'fas fa-map-marker-alt'
            template.icone_ville = 'fas fa-building'
            template.icone_article = 'fas fa-box'
            template.icone_prix = 'fas fa-money-bill-wave'
            template.icone_marque = 'fas fa-crown'
            template.icone_website = 'fas fa-globe'
            template.icone_panier = 'fas fa-shopping-cart'
            template.icone_code = 'fas fa-barcode'
            template.icone_date = 'fas fa-calendar-alt'
            template.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Template mis à jour avec les icônes professionnelles: {template.nom}')
            )
            
        except EtiquetteTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Template "Template Livraison Standard" non trouvé.')
            )
