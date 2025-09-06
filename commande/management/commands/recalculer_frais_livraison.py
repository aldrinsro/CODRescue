from django.core.management.base import BaseCommand
from commande.models import Commande


class Command(BaseCommand):
    help = 'Recalcule les totaux des commandes en incluant les frais de livraison si nécessaire'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Récupérer seulement les commandes avec frais de livraison activés
        commandes = Commande.objects.filter(frais_livraison=True)
        
        commandes_modifiees = 0
        total_frais_ajoutes = 0
        
        self.stdout.write(f"🔍 Analyse de {commandes.count()} commandes avec frais de livraison activés...")
        
        for commande in commandes:
            ancien_total = commande.total_cmd
            
            # Recalculer le total avec les frais de livraison
            if not dry_run:
                commande.recalculer_total_avec_frais()
                commande.refresh_from_db()
            
            nouveau_total = commande.total_cmd
            
            if ancien_total != nouveau_total:
                commandes_modifiees += 1
                difference = nouveau_total - ancien_total
                total_frais_ajoutes += difference
                
                self.stdout.write(
                    f"📦 Commande {commande.id_yz}: "
                    f"{ancien_total:.2f} DH → {nouveau_total:.2f} DH "
                    f"(+{difference:.2f} DH)"
                )
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(f"🔍 MODE TEST - Aucune modification effectuée")
        else:
            self.stdout.write(f"✅ MODIFICATION EFFECTUÉE")
        
        self.stdout.write(f"📊 Commandes modifiées: {commandes_modifiees}")
        self.stdout.write(f"💰 Total des frais ajoutés: {total_frais_ajoutes:.2f} DH")
        
        if dry_run and commandes_modifiees > 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Pour appliquer ces modifications, relancez la commande sans --dry-run"
                )
            )
