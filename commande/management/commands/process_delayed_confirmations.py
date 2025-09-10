from django.core.management.base import BaseCommand
from django.utils import timezone
from commande.models import EtatCommande, EnumEtatCmd
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Traite les confirmations décalées qui ont atteint leur date de fin'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Début du traitement des confirmations décalées...')
        )
        
        # Récupérer tous les états "Confirmation décalée" qui ont atteint leur date de fin
        now = timezone.now()
        
        etats_delayed = EtatCommande.objects.filter(
            enum_etat__libelle='Confirmation décalée',
            date_fin__isnull=True,  # État encore actif
            date_fin_delayed__lte=now  # Date de fin atteinte
        ).select_related('commande', 'enum_etat', 'operateur')
        
        if not etats_delayed.exists():
            self.stdout.write(
                self.style.SUCCESS('Aucune confirmation décalée à traiter')
            )
            return
        
        # Récupérer l'état "Confirmée"
        try:
            etat_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
        except EnumEtatCmd.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('ERREUR: État "Confirmée" non trouvé dans la configuration')
            )
            return
        
        transitions_effectuees = 0
        
        for etat_delayed in etats_delayed:
            try:
                # Fermer l'état "Confirmation décalée"
                etat_delayed.date_fin = now
                etat_delayed.save()
                
                # Créer le nouvel état "Confirmée"
                nouvel_etat = EtatCommande.objects.create(
                    commande=etat_delayed.commande,
                    enum_etat=etat_confirmee,
                    operateur=etat_delayed.operateur,
                    date_debut=now,
                    commentaire=f'Transition automatique depuis "Confirmation décalée" (fin prévue: {etat_delayed.date_fin_delayed.strftime("%d/%m/%Y %H:%M")})'
                )
                
                transitions_effectuees += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'OK: Commande {etat_delayed.commande.id_yz} : '
                        f'Confirmation décalée -> Confirmée'
                    )
                )
                
                logger.info(
                    f'Transition automatique: Commande {etat_delayed.commande.id_yz} '
                    f'de "Confirmation décalée" vers "Confirmée"'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'ERREUR: Transition commande {etat_delayed.commande.id_yz}: {str(e)}'
                    )
                )
                logger.error(
                    f'Erreur transition automatique commande {etat_delayed.commande.id_yz}: {str(e)}'
                )
        
        # Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(f'=== RÉSUMÉ DU TRAITEMENT ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Confirmations décalées traitées: {transitions_effectuees}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Heure de traitement: {now.strftime("%d/%m/%Y %H:%M:%S")}')
        )
        self.stdout.write('='*60)
        
        if transitions_effectuees > 0:
            self.stdout.write(
                self.style.SUCCESS('Traitement terminé avec succès !')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Aucune transition effectuée')
            )
