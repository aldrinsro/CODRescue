from django.core.management.base import BaseCommand
from commande.models import Commande


class Command(BaseCommand):
    help = 'Met à jour la source des commandes basée sur leur num_cmd (YCN -> Youcan, SHP -> Shopify)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait mis à jour sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode dry-run activé - Aucune modification ne sera effectuée')
            )
        
        # Compter les commandes à mettre à jour
        youcan_count = Commande.objects.filter(
            num_cmd__startswith='YCN',
            source__isnull=True
        ).count()
        
        shopify_count = Commande.objects.filter(
            num_cmd__startswith='SHP',
            source__isnull=True
        ).count()
        
        total_count = youcan_count + shopify_count
        
        self.stdout.write(f'Commandes YCN à mettre à jour vers "Youcan": {youcan_count}')
        self.stdout.write(f'Commandes SHP à mettre à jour vers "Shopify": {shopify_count}')
        self.stdout.write(f'Total des commandes à mettre à jour: {total_count}')
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucune commande à mettre à jour.')
            )
            return
        
        if not dry_run:
            # Effectuer la mise à jour
            result = Commande.update_sources_from_num_cmd()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Mise à jour terminée:\n'
                    f'   - Commandes Youcan mises à jour: {result["youcan_updated"]}\n'
                    f'   - Commandes Shopify mises à jour: {result["shopify_updated"]}\n'
                    f'   - Total mis à jour: {result["total_updated"]}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Mode dry-run: Aucune modification effectuée')
            )
