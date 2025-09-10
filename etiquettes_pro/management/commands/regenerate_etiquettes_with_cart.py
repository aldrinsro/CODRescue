from django.core.management.base import BaseCommand
from django.db import transaction
from etiquettes_pro.models import Etiquette, EtiquetteTemplate
from commande.models import Commande


class Command(BaseCommand):
    help = 'Régénère les étiquettes existantes avec les articles du panier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--template-id',
            type=int,
            help='ID du template à utiliser (optionnel)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        template_id = options.get('template_id')
        
        # Récupérer le template
        if template_id:
            try:
                template = EtiquetteTemplate.objects.get(id=template_id)
            except EtiquetteTemplate.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Template avec l'ID {template_id} non trouvé")
                )
                return
        else:
            # Utiliser le template par défaut
            template = EtiquetteTemplate.objects.filter(
                nom='Template Livraison Standard',
                actif=True
            ).first()
            
            if not template:
                self.stdout.write(
                    self.style.ERROR("❌ Template par défaut 'Template Livraison Standard' non trouvé")
                )
                return
        
        self.stdout.write(f"🔍 Utilisation du template: {template.nom}")
        
        # Récupérer toutes les étiquettes qui ont un commande_id
        etiquettes_a_regenerer = Etiquette.objects.filter(
            commande_id__isnull=False
        ).select_related('template')
        
        self.stdout.write(f"🔍 {etiquettes_a_regenerer.count()} étiquettes à régénérer")
        
        if dry_run:
            self.stdout.write("🔍 Mode dry-run activé - aucune modification ne sera effectuée")
        
        updated_count = 0
        error_count = 0
        
        for etiquette in etiquettes_a_regenerer:
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
                    # Mettre à jour l'étiquette avec les nouvelles données
                    etiquette.template = template
                    etiquette.cart_items = cart_items_data
                    etiquette.nom_article = f"Commande {commande.num_cmd or commande.id_yz}"
                    etiquette.client_nom = f"{commande.client.nom} {commande.client.prenom}" if commande.client else ""
                    etiquette.save()
                
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
                    f"🔍 DRY-RUN: {updated_count} étiquettes seraient régénérées, {error_count} erreurs"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {updated_count} étiquettes régénérées avec succès, {error_count} erreurs"
                )
            )
