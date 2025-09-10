from django.core.management.base import BaseCommand
from django.db import transaction
from etiquettes_pro.models import Etiquette
from commande.models import Commande


class Command(BaseCommand):
    help = 'Met à jour les étiquettes existantes avec les articles du panier de leurs commandes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Récupérer toutes les étiquettes qui ont un commande_id mais pas de cart_items
        etiquettes_a_mettre_a_jour = Etiquette.objects.filter(
            commande_id__isnull=False,
            cart_items__isnull=True
        )
        
        self.stdout.write(f"🔍 {etiquettes_a_mettre_a_jour.count()} étiquettes à mettre à jour")
        
        if dry_run:
            self.stdout.write("🔍 Mode dry-run activé - aucune modification ne sera effectuée")
        
        updated_count = 0
        error_count = 0
        
        for etiquette in etiquettes_a_mettre_a_jour:
            try:
                # Vérifier que commande_id n'est pas vide
                if not etiquette.commande_id or etiquette.commande_id.strip() == '':
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Étiquette {etiquette.reference} a un commande_id vide"
                        )
                    )
                    continue
                
                # Récupérer la commande associée
                commande = Commande.objects.get(id=int(etiquette.commande_id))
                
                # Récupérer les articles de la commande
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
                
                if not dry_run:
                    # Mettre à jour l'étiquette
                    etiquette.cart_items = cart_items_data
                    etiquette.save(update_fields=['cart_items'])
                
                updated_count += 1
                self.stdout.write(
                    f"✅ Étiquette {etiquette.reference} - {len(cart_items_data)} articles"
                )
                
            except Commande.DoesNotExist:
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Commande {etiquette.commande_id} non trouvée pour l'étiquette {etiquette.reference}"
                    )
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Erreur pour l'étiquette {etiquette.reference}: {str(e)}"
                    )
                )
        
        # Résumé
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🔍 DRY-RUN: {updated_count} étiquettes seraient mises à jour, {error_count} erreurs"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {updated_count} étiquettes mises à jour avec succès, {error_count} erreurs"
                )
            )
