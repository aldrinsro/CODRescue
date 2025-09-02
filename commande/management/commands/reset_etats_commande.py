from django.core.management.base import BaseCommand
from django.core.management import call_command
from commande.models import EnumEtatCmd


class Command(BaseCommand):
    help = 'Réinitialise complètement les états de commande (supprime tout et recharge)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la réinitialisation sans confirmation',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if not force:
            self.stdout.write(
                self.style.WARNING('⚠️  ATTENTION: Cette action va supprimer TOUS les états de commande existants !')
            )
            self.stdout.write(
                self.style.WARNING('   • Toutes les données d\'états seront perdues')
            )
            self.stdout.write(
                self.style.WARNING('   • Les commandes existantes pourraient être affectées')
            )
            
            confirmation = input('\n🔒 Êtes-vous sûr de vouloir continuer ? (oui/non): ')
            if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(
                    self.style.ERROR('❌ Réinitialisation annulée par l\'utilisateur')
                )
                return

        self.stdout.write(
            self.style.SUCCESS('🚀 Début de la réinitialisation des états de commande...')
        )

        # Étape 1: Sauvegarder le nombre d'états existants
        etats_existants_count = EnumEtatCmd.objects.count()
        self.stdout.write(f'📊 États existants avant réinitialisation: {etats_existants_count}')

        # Étape 2: Supprimer tous les états existants
        self.stdout.write('\n🗑️  Suppression de tous les états existants...')
        deleted_count, _ = EnumEtatCmd.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'✅ {deleted_count} états supprimés')
        )

        # Étape 3: Vérifier que la table est vide
        etats_apres_suppression = EnumEtatCmd.objects.count()
        if etats_apres_suppression == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Table des états vidée avec succès')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur: {etats_apres_suppression} états restent dans la table')
            )
            return

        # Étape 4: Recharger les états par défaut
        self.stdout.write('\n📥 Rechargement des états par défaut...')
        try:
            call_command('load_default_etats_commande')
            self.stdout.write(
                self.style.SUCCESS('✅ États par défaut rechargés avec succès')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du rechargement: {str(e)}')
            )
            return

        # Étape 5: Vérification finale
        self.stdout.write('\n🔍 Vérification finale...')
        try:
            call_command('verify_etats_commande')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la vérification: {str(e)}')
            )

        # Résumé final
        etats_finaux = EnumEtatCmd.objects.count()
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'🎯 RÉINITIALISATION TERMINÉE:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États supprimés: {etats_existants_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États rechargés: {etats_finaux}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Statut: {"✅ Succès" if etats_finaux > 0 else "❌ Échec"}')
        )
        self.stdout.write('='*60)

        if etats_finaux > 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Réinitialisation terminée avec succès !')
            )
            self.stdout.write(
                self.style.SUCCESS('💡 Vous pouvez maintenant utiliser les états de commande par défaut.')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n❌ Réinitialisation échouée !')
            )
            self.stdout.write(
                self.style.ERROR('💡 Vérifiez les logs pour identifier le problème.')
            )
