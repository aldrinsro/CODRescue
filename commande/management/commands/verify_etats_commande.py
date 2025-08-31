from django.core.management.base import BaseCommand
from commande.models import EnumEtatCmd


class Command(BaseCommand):
    help = 'Vérifie que tous les états de commande par défaut sont présents dans la base de données'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Vérification des états de commande dans la base de données...')
        )

        # Définition des états attendus
        etats_attendus = [
            'Non affectée',
            'Affectée', 
            'En cours de confirmation',
            'Confirmée',
            'En préparation',
            'Préparée',
            'Collectée',
            'Emballée',
            'En livraison',
            'Livrée',
            'Annulée',
            'Doublon',
            'Erronée'
        ]

        # Récupérer tous les états existants
        etats_existants = EnumEtatCmd.objects.all()
        
        self.stdout.write(f'\n📊 ÉTATS ATTENDUS: {len(etats_attendus)}')
        self.stdout.write(f'📊 ÉTATS PRÉSENTS: {etats_existants.count()}')
        
        # Vérifier chaque état attendu
        etats_trouves = []
        etats_manquants = []
        
        for etat_attendu in etats_attendus:
            try:
                etat = EnumEtatCmd.objects.get(libelle=etat_attendu)
                etats_trouves.append(etat)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {etat_attendu} - Couleur: {etat.couleur} - Ordre: {etat.ordre}')
                )
            except EnumEtatCmd.DoesNotExist:
                etats_manquants.append(etat_attendu)
                self.stdout.write(
                    self.style.ERROR(f'❌ {etat_attendu} - MANQUANT')
                )

        # Affichage du résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'📋 RÉSUMÉ DE LA VÉRIFICATION:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • États trouvés: {len(etats_trouves)}')
        )
        self.stdout.write(
            self.style.ERROR(f'   • États manquants: {len(etats_manquants)}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Total attendu: {len(etats_attendus)}')
        )
        self.stdout.write('='*60)

        # Afficher les états manquants
        if etats_manquants:
            self.stdout.write('\n🚨 ÉTATS MANQUANTS:')
            for etat_manquant in etats_manquants:
                self.stdout.write(
                    self.style.ERROR(f'   • {etat_manquant}')
                )
            
            self.stdout.write(
                self.style.WARNING('\n💡 Pour charger les états manquants, exécutez:')
            )
            self.stdout.write(
                self.style.WARNING('   python manage.py load_default_etats_commande')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Tous les états de commande sont présents !')
            )

        # Afficher les états supplémentaires (optionnel)
        etats_supplementaires = etats_existants.exclude(libelle__in=etats_attendus)
        if etats_supplementaires.exists():
            self.stdout.write('\n📝 ÉTATS SUPPLÉMENTAIRES:')
            for etat in etats_supplementaires:
                self.stdout.write(
                    self.style.WARNING(f'   • {etat.libelle} - Couleur: {etat.couleur} - Ordre: {etat.ordre}')
                )

        # Vérification de l'intégrité
        self.stdout.write('\n🔧 VÉRIFICATION DE L\'INTÉGRITÉ:')
        
        # Vérifier les doublons
        doublons = []
        libelles_vus = set()
        for etat in etats_existants:
            if etat.libelle in libelles_vus:
                doublons.append(etat.libelle)
            else:
                libelles_vus.add(etat.libelle)
        
        if doublons:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Doublons détectés: {doublons}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ Aucun doublon détecté')
            )

        # Vérifier l'ordre
        etats_ordonnes = etats_existants.order_by('ordre')
        ordre_valide = True
        for i, etat in enumerate(etats_ordonnes, 1):
            if etat.ordre != i:
                ordre_valide = False
                break
        
        if ordre_valide:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ Ordre des états valide')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Ordre des états non séquentiel')
            )

        # Conclusion
        if not etats_manquants and not doublons:
            self.stdout.write(
                self.style.SUCCESS('\n🎯 VÉRIFICATION TERMINÉE AVEC SUCCÈS !')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n⚠️  VÉRIFICATION TERMINÉE AVEC DES PROBLÈMES !')
            )
