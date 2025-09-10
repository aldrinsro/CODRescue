"""
Commande de surveillance en temps réel des commandes avec paniers
Peut être exécutée périodiquement pour générer automatiquement les étiquettes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from etiquettes_pro.models import EtiquetteTemplate, Etiquette
from commande.models import Commande
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Surveille les commandes avec paniers et génère automatiquement les étiquettes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalle de surveillance en secondes (défaut: 30)',
        )
        parser.add_argument(
            '--max-runs',
            type=int,
            default=0,
            help='Nombre maximum d\'exécutions (0 = infini)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Exécuter une seule fois puis s\'arrêter',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        max_runs = options['max_runs']
        once = options['once']
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Démarrage de la surveillance des commandes (intervalle: {interval}s)')
        )
        
        runs = 0
        
        try:
            while True:
                runs += 1
                
                if max_runs > 0 and runs > max_runs:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Nombre maximum d\'exécutions atteint ({max_runs})')
                    )
                    break
                
                if runs > 1:
                    self.stdout.write(f'⏰ Exécution #{runs} - {timezone.now().strftime("%H:%M:%S")}')
                
                # Vérifier les nouvelles commandes
                new_etiquettes = self.check_and_generate_etiquettes()
                
                if new_etiquettes > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {new_etiquettes} nouvelle(s) étiquette(s) générée(s)')
                    )
                else:
                    self.stdout.write('ℹ️  Aucune nouvelle étiquette à générer')
                
                if once:
                    break
                
                # Attendre l'intervalle suivant
                if not once:
                    time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n⏹️  Surveillance arrêtée par l\'utilisateur')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la surveillance: {str(e)}')
            )
            logger.error(f'Erreur surveillance commandes: {str(e)}')
            raise

    def check_and_generate_etiquettes(self):
        """Vérifie et génère les étiquettes pour les nouvelles commandes"""
        try:
            # Récupérer le template par défaut
            template = EtiquetteTemplate.objects.filter(
                nom='Template Livraison Standard',
                actif=True
            ).first()
            
            if not template:
                return 0
            
            # Récupérer les commandes avec paniers créées récemment (dernières 5 minutes)
            recent_time = timezone.now() - timezone.timedelta(minutes=5)
            commandes_recentes = Commande.objects.filter(
                paniers__isnull=False,
                date_creation__gte=recent_time
            ).select_related('client', 'ville').distinct()
            
            # Récupérer les IDs des commandes qui ont déjà des étiquettes
            commandes_avec_etiquettes = set(
                Etiquette.objects.filter(
                    template=template,
                    commande_id__isnull=False
                ).values_list('commande_id', flat=True)
            )
            
            etiquettes_creees = 0
            
            for commande in commandes_recentes:
                if str(commande.id) in commandes_avec_etiquettes:
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
                
                logger.info(f'Étiquette auto-générée pour commande #{commande.num_cmd or commande.id_yz}')
            
            return etiquettes_creees
            
        except Exception as e:
            logger.error(f'Erreur lors de la génération automatique: {str(e)}')
            return 0
