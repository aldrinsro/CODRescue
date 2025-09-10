from django.utils import timezone
from django.core.cache import cache
from .models import EtatCommande, EnumEtatCmd
import logging

logger = logging.getLogger(__name__)

class DelayedConfirmationMiddleware:
    """
    Middleware qui vérifie automatiquement les confirmations décalées expirées
    à chaque requête (avec limitation de fréquence via cache)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier les confirmations décalées (maximum toutes les 30 secondes)
        self.check_delayed_confirmations()
        
        response = self.get_response(request)
        return response

    def check_delayed_confirmations(self):
        """
        Vérifie et traite les confirmations décalées expirées
        """
        # Utiliser le cache pour limiter la fréquence de vérification
        cache_key = 'last_delayed_confirmation_check'
        last_check = cache.get(cache_key)
        now = timezone.now()
        
        # Vérifier seulement si la dernière vérification date de plus de 10 secondes
        if last_check and (now - last_check).total_seconds() < 10:
            return
        
        try:
            # Récupérer tous les états "Confirmation décalée" qui ont atteint leur date de fin
            etats_delayed = EtatCommande.objects.filter(
                enum_etat__libelle='Confirmation décalée',
                date_fin__isnull=True,  # État encore actif
                date_fin_delayed__lte=now  # Date de fin atteinte
            ).select_related('commande', 'enum_etat', 'operateur')
            
            if not etats_delayed.exists():
                # Mettre à jour le cache même s'il n'y a rien à traiter
                cache.set(cache_key, now, 60)  # Cache pour 1 minute
                return
            
            # Récupérer l'état "Confirmée"
            try:
                etat_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
            except EnumEtatCmd.DoesNotExist:
                logger.error('État "Confirmée" non trouvé dans la configuration')
                return
            
            transitions_effectuees = 0
            
            for etat_delayed in etats_delayed:
                try:
                    # Fermer TOUS les états actifs de cette commande
                    commande = etat_delayed.commande
                    etats_actifs = commande.etats.filter(date_fin__isnull=True)
                    
                    for etat_actif in etats_actifs:
                        etat_actif.date_fin = now
                        etat_actif.save()
                    
                    # Créer le nouvel état "Confirmée"
                    nouvel_etat = EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_confirmee,
                        operateur=etat_delayed.operateur,
                        date_debut=now,
                        commentaire=f'Transition automatique depuis "Confirmation décalée" (fin prévue: {etat_delayed.date_fin_delayed.strftime("%d/%m/%Y %H:%M")})'
                    )
                    
                    transitions_effectuees += 1
                    
                    logger.info(
                        f'Transition automatique: Commande {etat_delayed.commande.id_yz} '
                        f'de "Confirmation décalée" vers "Confirmée"'
                    )
                    
                except Exception as e:
                    logger.error(
                        f'Erreur lors de la transition de la commande {etat_delayed.commande.id_yz}: {str(e)}'
                    )
            
            # Mettre à jour le cache
            cache.set(cache_key, now, 60)  # Cache pour 1 minute
            
            if transitions_effectuees > 0:
                logger.info(f'{transitions_effectuees} confirmations décalées traitées automatiquement')
                
        except Exception as e:
            logger.error(f'Erreur dans le middleware de vérification des confirmations décalées: {str(e)}')
            # Mettre à jour le cache même en cas d'erreur pour éviter les boucles
            cache.set(cache_key, now, 60)
