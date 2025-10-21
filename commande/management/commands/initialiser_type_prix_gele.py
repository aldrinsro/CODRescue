"""
Commande de gestion pour initialiser le champ type_prix_gele
pour tous les paniers existants qui n'en ont pas.

Usage:
    python manage.py initialiser_type_prix_gele
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from commande.models import Panier


class Command(BaseCommand):
    help = 'Initialise le champ type_prix_gele pour tous les paniers existants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'exécution sans modifier la base de données',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucune modification ne sera effectuée'))

        # Compter les paniers sans type_prix_gele
        paniers_sans_type = Panier.objects.filter(type_prix_gele='')
        total_paniers = paniers_sans_type.count()

        if total_paniers == 0:
            self.stdout.write(self.style.SUCCESS('[OK] Tous les paniers ont deja un type_prix_gele defini'))
            return

        self.stdout.write(f'[INFO] {total_paniers} paniers a traiter...\n')

        paniers_traites = 0
        paniers_par_type = {}

        with transaction.atomic():
            for panier in paniers_sans_type.select_related('article', 'commande'):
                # Déterminer le type de prix
                if panier.remise_appliquer and panier.type_remise_appliquee:
                    type_prix = panier.type_remise_appliquee
                elif panier.article.phase == 'LIQUIDATION':
                    type_prix = 'liquidation'
                elif hasattr(panier.article, 'has_promo_active') and panier.article.has_promo_active:
                    type_prix = 'promotion'
                elif panier.article.phase == 'EN_TEST':
                    type_prix = 'test'
                elif panier.article.isUpsell and panier.commande.compteur > 0:
                    type_prix = f'upsell_niveau_{panier.commande.compteur}'
                else:
                    type_prix = 'normal'

                # Compter par type
                paniers_par_type[type_prix] = paniers_par_type.get(type_prix, 0) + 1

                if not dry_run:
                    panier.type_prix_gele = type_prix
                    panier.save(update_fields=['type_prix_gele'])

                paniers_traites += 1

                # Afficher progression tous les 100 paniers
                if paniers_traites % 100 == 0:
                    self.stdout.write(f'  Traité {paniers_traites}/{total_paniers} paniers...')

            # En mode dry-run, annuler la transaction
            if dry_run:
                transaction.set_rollback(True)

        # Afficher le résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'[OK] {paniers_traites} paniers traites'))
        self.stdout.write('\n[STATS] Repartition par type de prix :')

        for type_prix, count in sorted(paniers_par_type.items(), key=lambda x: x[1], reverse=True):
            self.stdout.write(f'  - {type_prix:20s}: {count:5d} paniers')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[WARN] MODE SIMULATION - Aucune modification effectuee'))
            self.stdout.write('Pour appliquer les modifications, relancez sans --dry-run')
        else:
            self.stdout.write(self.style.SUCCESS('\n[OK] Initialisation terminee avec succes !'))
