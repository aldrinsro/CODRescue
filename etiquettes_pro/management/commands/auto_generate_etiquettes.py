"""
Commande de management pour générer automatiquement les étiquettes
pour toutes les commandes qui ont des paniers
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from etiquettes_pro.models import EtiquetteTemplate, Etiquette
from commande.models import Commande
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Génère automatiquement les étiquettes pour les commandes avec paniers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans exécuter les actions',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la génération même si des étiquettes existent déjà',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage de la génération automatique des étiquettes')
        )
        
        try:
            # Récupérer le template par défaut
            template = EtiquetteTemplate.objects.filter(
                nom='Template Livraison Standard',
                actif=True
            ).first()
            
            if not template:
                self.stdout.write(
                    self.style.ERROR('❌ Template par défaut "Template Livraison Standard" non trouvé')
                )
                return
            
            self.stdout.write(f'✅ Template trouvé: {template.nom}')
            
            # Récupérer les commandes avec paniers
            commandes_avec_paniers = Commande.objects.filter(
                paniers__isnull=False
            ).select_related('client', 'ville').distinct()
            
            total_commandes = commandes_avec_paniers.count()
            self.stdout.write(f'📊 {total_commandes} commandes avec paniers trouvées')
            
            if total_commandes == 0:
                self.stdout.write(
                    self.style.WARNING('⚠️ Aucune commande avec paniers trouvée')
                )
                return
            
            # Récupérer les IDs des commandes qui ont déjà des étiquettes
            if not force:
                commandes_avec_etiquettes = set(
                    Etiquette.objects.filter(
                        template=template,
                        commande_id__isnull=False
                    ).values_list('commande_id', flat=True)
                )
            else:
                commandes_avec_etiquettes = set()
            
            # Générer les étiquettes
            etiquettes_creees = 0
            etiquettes_skip = 0
            
            for commande in commandes_avec_paniers:
                if str(commande.id) in commandes_avec_etiquettes:
                    etiquettes_skip += 1
                    if dry_run:
                        self.stdout.write(f'⏭️  Commande #{commande.num_cmd or commande.id_yz} - Étiquette existe déjà')
                    continue
                
                if dry_run:
                    self.stdout.write(f'🔄 Commande #{commande.num_cmd or commande.id_yz} - Serait générée')
                    etiquettes_creees += 1
                    continue
                
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
                    cart_items=cart_items_data
                )
                etiquettes_creees += 1
                
                self.stdout.write(f'✅ Étiquette créée pour commande #{commande.num_cmd or commande.id_yz}')
            
            # Résumé
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'📋 RÉSUMÉ (DRY RUN):')
                )
                self.stdout.write(f'   • Étiquettes qui seraient créées: {etiquettes_creees}')
                self.stdout.write(f'   • Étiquettes qui seraient ignorées: {etiquettes_skip}')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'🎉 GÉNÉRATION TERMINÉE:')
                )
                self.stdout.write(f'   • Étiquettes créées: {etiquettes_creees}')
                self.stdout.write(f'   • Étiquettes ignorées: {etiquettes_skip}')
                
                if etiquettes_creees > 0:
                    logger.info(f'Génération automatique: {etiquettes_creees} étiquettes créées')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la génération: {str(e)}')
            )
            logger.error(f'Erreur génération automatique étiquettes: {str(e)}')
            raise
