from django.core.management.base import BaseCommand
from commande.models import EnumEtatCmd


class Command(BaseCommand):
    help = 'Charge les états de commande par défaut dans la base de données'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Début du chargement des états de commande par défaut...')
        )

        # Définition des états par défaut avec leurs couleurs et ordre
        etats_par_defaut = [
            # États de base
            {'libelle': 'Non affectée', 'couleur': '#6B7280', 'ordre': 1},
            {'libelle': 'Affectée', 'couleur': '#3B82F6', 'ordre': 2},
            {'libelle': 'En cours de confirmation', 'couleur': '#F59E0B', 'ordre': 3},
            {'libelle': 'Confirmée', 'couleur': '#10B981', 'ordre': 4},
            
            # États de préparation
            {'libelle': 'En préparation', 'couleur': '#06B6D4', 'ordre': 5},
            {'libelle': 'Préparée', 'couleur': '#14B8A6', 'ordre': 6},

            # États de livraison
            {'libelle': 'Collectée', 'couleur': '#6B7280', 'ordre': 7},
            {'libelle': 'Emballée', 'couleur': '#6B7280', 'ordre': 8},
            {'libelle': 'En livraison', 'couleur': '#8B5CF6', 'ordre': 9},
            {'libelle': 'Mise en distribution', 'couleur':'#8B5CF6','ordre':20},
            {'libelle': 'Livrée', 'couleur': '#22C55E', 'ordre': 10},
            {'libelle': 'Retournée', 'couleur': '#EF4444', 'ordre': 11},
            {'libelle': 'Retour Confirmation', 'couleur': '#EF4444', 'ordre': 12},
            {'libelle': 'Reportée', 'couleur': '#6B7280', 'ordre': 13},
            {'libelle': 'Retournée', 'couleur': '#6B7280', 'ordre': 14},
            {'libelle': 'Reporté de confirmation', 'couleur': '#6B7280', 'ordre': 15},
       
            # États d'erreur et annulation
            {'libelle': 'Annulée', 'couleur': '#EF4444', 'ordre': 11},
            {'libelle': 'Doublon', 'couleur': '#EF4444', 'ordre': 12},
            {'libelle': 'Erronée', 'couleur': '#F97316', 'ordre': 13},
        ]

        etats_crees = 0
        etats_existants = 0
        etats_mis_a_jour = 0

        for etat_data in etats_par_defaut:
            libelle = etat_data['libelle']
            couleur = etat_data['couleur']
            ordre = etat_data['ordre']

            # Vérifier si l'état existe déjà
            etat_existant, created = EnumEtatCmd.objects.get_or_create(
                libelle=libelle,
                defaults={
                    'couleur': couleur,
                    'ordre': ordre
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Créé: {libelle} (Couleur: {couleur}, Ordre: {ordre})')
                )
                etats_crees += 1
            else:
                # Vérifier si l'état existant doit être mis à jour
                if etat_existant.couleur != couleur or etat_existant.ordre != ordre:
                    etat_existant.couleur = couleur
                    etat_existant.ordre = ordre
                    etat_existant.save()
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Mis à jour: {libelle} (Couleur: {couleur}, Ordre: {ordre})')
                    )
                    etats_mis_a_jour += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'ℹ️  Existant: {libelle} (déjà à jour)')
                    )
                    etats_existants += 1

        # Affichage du résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'📊 RÉSUMÉ DU CHARGEMENT:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États créés: {etats_crees}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États mis à jour: {etats_mis_a_jour}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États déjà existants: {etats_existants}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Total traité: {len(etats_par_defaut)}')
        )
        self.stdout.write('='*60)

        # Vérification finale
        total_etats = EnumEtatCmd.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'\n🎯 Total des états dans la base de données: {total_etats}')
        )

        if total_etats >= len(etats_par_defaut):
            self.stdout.write(
                self.style.SUCCESS('✅ Chargement terminé avec succès !')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Attention: Le nombre d\'états ne correspond pas aux attentes')
            )
