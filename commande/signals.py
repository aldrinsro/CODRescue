from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Commande


@receiver(pre_save, sender=Commande)
def detect_compteur_change(sender, instance, **kwargs):
    """
    Détecte les changements du compteur et des frais de livraison avant la sauvegarde
    et stocke les anciennes valeurs pour comparaison
    """
    if instance.pk:
        try:
            old_instance = Commande.objects.get(pk=instance.pk)
            instance._old_compteur = old_instance.compteur
            instance._old_frais_livraison = old_instance.frais_livraison
        except Commande.DoesNotExist:
            instance._old_compteur = 0
            instance._old_frais_livraison = False
    else:
        instance._old_compteur = 0
        instance._old_frais_livraison = False


@receiver(post_save, sender=Commande)
def auto_recalcul_totaux_upsell(sender, instance, created, **kwargs):
    """
    Recalcule automatiquement les totaux selon la nouvelle logique upsell
    quand le compteur change d'état (différent de zéro) ou quand les frais de livraison changent
    """
    # Éviter la récursion infinie
    if hasattr(instance, '_recalcul_en_cours'):
        return
    
    # Vérifier si le compteur a changé
    old_compteur = getattr(instance, '_old_compteur', 0)
    nouveau_compteur = instance.compteur
    
    # Vérifier si les frais de livraison ont changé
    old_frais_livraison = getattr(instance, '_old_frais_livraison', False)
    nouveau_frais_livraison = instance.frais_livraison
    
    # Déclencher le recalcul si :
    # 1. Le compteur a changé ET le nouveau compteur n'est pas zéro
    # 2. OU les frais de livraison sont activés (passent de False à True)
    compteur_changed = old_compteur != nouveau_compteur and nouveau_compteur != 0
    frais_activated = not old_frais_livraison and nouveau_frais_livraison
    
    if compteur_changed or frais_activated:
        # Marquer pour éviter la récursion
        instance._recalcul_en_cours = True
        
        try:
            if compteur_changed:
                # Déclencher le recalcul automatique des prix upsell
                instance.recalculer_totaux_upsell()
                print(f"🔄 Recalcul upsell déclenché pour commande {instance.id_yz}")
                print(f"   Compteur: {old_compteur} → {nouveau_compteur}")
            
            if frais_activated:
                # Recalculer avec les frais de livraison (seulement quand activés)
                instance.recalculer_total_avec_frais()
                print(f"🚚 Frais de livraison activés pour commande {instance.id_yz}")
                print(f"   Frais de livraison: {old_frais_livraison} → {nouveau_frais_livraison}")
            
            print(f"   Nouveau total: {instance.total_cmd:.2f} DH")
            
        finally:
            # Nettoyer le flag
            delattr(instance, '_recalcul_en_cours') 