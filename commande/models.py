from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from client.models import Client
from article.models import Article, VarianteArticle
from parametre.models import Ville, Operateur

# Create your models here.

class EnumEtatCmd(models.Model):
    # Choix d'états de commande
    STATUS_CHOICES = [
        ('non_affectee', 'Non affectée'),
        ('affectee', 'Affectée'),
        ('en_cours_confirmation', 'En cours de confirmation'),
        ('confirmee', 'Confirmée '),
        ('erronnee', 'Erronée'),
        ('doublon', 'Doublon'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('non_paye', 'Non payé'),
        ('partiellement_paye', 'Partiellement payé'),
        ('paye', 'Payé'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('à imprimer', 'À imprimer'),
        ('en_preparation', 'En préparation'),
        ('collectee', 'Collectée'),
        ('emballee', 'Emballée'),
        ('validee', 'Validée'),
        ('en_livraison', 'En livraison'),
        ('livree', 'Livrée'),
        ('retournee', 'Retournée'),
    ]
    
    libelle = models.CharField(max_length=100, unique=True)
    ordre = models.IntegerField(default=0)  # Pour ordonner les états
    couleur = models.CharField(max_length=7, default='#6B7280')  # Code couleur hex
    
    class Meta:
        verbose_name = "Définition d'état de commande(EnumEtatCmd)"
        verbose_name_plural = "Définitions d'états de commande(EnumEtatCmd)"
        ordering = ['ordre', 'libelle']
    
    def __str__(self):
        return self.libelle


class Commande(models.Model):
    ORIGINE_CHOICES = [
        ('OC', 'Opérateur Confirmation'),
        ('ADMIN', 'Administrateur'),
        ('SYNC', 'Synchronisation')
    ]
    SOURCE_CHOICES = [
        ('Appel', 'Appel'),
        ('Whatsapp ', 'Whatsapp '),
        ('SMS', 'SMS'),
        ('Email', 'Email'),
        ('Facebook', 'Facebook'),
        ("Youcan", "Youcan"),
        ("Shopify", "Shopify"), 
              ]
    PAYER_CHOICES = [
        ('Non payé', 'Non payé'),
        ('Payé', 'Payé'),
        ('Remboursée', 'Remboursée'),
    ]


    num_cmd = models.CharField(max_length=50, unique=True)
    id_yz = models.PositiveIntegerField(unique=True, null=True, blank=True)
    origine = models.CharField(max_length=10, choices=ORIGINE_CHOICES, default='SYNC')
    date_cmd = models.DateField(default=timezone.now)
    total_cmd = models.FloatField()
    adresse = models.TextField()
    motif_annulation = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    last_sync_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de dernière synchronisation")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    ville_init = models.CharField(max_length=100, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, null=True, blank=True, related_name='commandes')
    produit_init = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True, choices=SOURCE_CHOICES)
    compteur = models.IntegerField(default=0, verbose_name="Compteur d'utilisation")  
    payement  = models.CharField(default='Non payé', verbose_name="Payement", choices=PAYER_CHOICES)
    frais_livraison = models.BooleanField(default=True, verbose_name="Frais de livraison")
    Date_livraison = models.DateTimeField(null=True, blank=True, verbose_name="Date de livraison")
    Date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")


    # Relation avec Envoi pour les exports journaliers  
    envoi = models.ForeignKey('Envoi', on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_associees')

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_cmd', '-date_creation', 'id_yz']
        constraints = [
            models.CheckConstraint(check=models.Q(total_cmd__gte=0), name='total_cmd_positif'),
        ]
    
    # Point de départ souhaité pour id_yz
    START_ID_YZ = 211971

    def save(self, *args, **kwargs):
        # Générer l'ID YZ automatiquement si ce n'est pas encore fait
        if self.id_yz is None:
            last_id_yz = Commande.objects.aggregate(max_id=models.Max('id_yz'))['max_id']
            base = self.START_ID_YZ - 1
            # Si aucune commande, commencer à 211971; sinon continuer après le max existant
            self.id_yz = max(last_id_yz or base, base) + 1 
        
        # Détecter automatiquement la source basée sur le numéro de commande
        if self.num_cmd and not self.source:
            if self.num_cmd.startswith('YCN'):
                self.source = 'Youcan'
            elif self.num_cmd.startswith('SHP'):
                self.source = 'Shopify'
        
        # Générer le numéro de commande selon l'origine si ce n'est pas déjà fait
        if not self.num_cmd:
            if self.origine == 'OC':
                # Format pour les opérateurs de confirmation: OC-00001
                prefix = 'OC-'
                last_oc = Commande.objects.filter(
                    num_cmd__startswith=prefix
                ).order_by('-num_cmd').first()
                
                if last_oc:
                    last_number = int(last_oc.num_cmd.split('-')[1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                self.num_cmd = f"{prefix}{new_number:05d}"
                
            elif self.origine == 'ADMIN':
                # Format pour les administrateurs: ADMIN-00001
                prefix = 'ADMIN-'
                last_admin = Commande.objects.filter(
                    num_cmd__startswith=prefix
                ).order_by('-num_cmd').first()
                
                if last_admin:
                    last_number = int(last_admin.num_cmd.split('-')[1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                self.num_cmd = f"{prefix}{new_number:05d}"
            else:
                # Pour les commandes synchronisées, utiliser l'ID YZ comme avant
                self.num_cmd = str(self.id_yz)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def update_sources_from_num_cmd(cls):
        """
        Met à jour la source des commandes existantes basée sur leur num_cmd
        """
        # Mettre à jour les commandes YCN vers Youcan
        updated_youcan = cls.objects.filter(
            num_cmd__startswith='YCN',
            source__isnull=True
        ).update(source='Youcan')
        
        # Mettre à jour les commandes SHP vers Shopify
        updated_shopify = cls.objects.filter(
            num_cmd__startswith='SHP',
            source__isnull=True
        ).update(source='Shopify')
        
        return {
            'youcan_updated': updated_youcan,
            'shopify_updated': updated_shopify,
            'total_updated': updated_youcan + updated_shopify
        }
    
    def __str__(self):
        return f"Commande {self.id_yz or self.num_cmd} - {self.client}"
    
    @property
    def etat_actuel(self):
        """Retourne l'état actuel de la commande"""
        return self.etats.filter(date_fin__isnull=True).first()
    @property
    def historique_etats(self):
        """Retourne l'historique complet des états"""
        return self.etats.all().order_by('date_debut')

    def recalculer_totaux_upsell(self):
        """
        Recalcule automatiquement les totaux de la commande selon le compteur upsell.
        Tous les articles de la commande prennent le prix upsell correspondant au compteur.
        """
        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
        
        print(f"🔄 recalculer_totaux_upsell - Compteur actuel: {self.compteur}")
        
        nouveau_total = 0
        
        # Recalculer chaque panier selon le compteur upsell
        for panier in self.paniers.all():
            # Vérifier si une remise a été appliquée sur ce panier
            if hasattr(panier, 'remise_appliquer') and panier.remise_appliquer:
                # Une remise a été appliquée - NE PAS recalculer, conserver le prix remisé
                print(f"   📦 {panier.article.nom} (REMISE APPLIQUÉE): qté={panier.quantite}, sous_total préservé={panier.sous_total}")
                nouveau_total += float(panier.sous_total)
            else:
                # Aucune remise - calculer selon le compteur de la commande
                prix_unitaire = get_prix_upsell_avec_compteur(panier.article, self.compteur)
                nouveau_sous_total = prix_unitaire * panier.quantite
                
                print(f"   📦 {panier.article.nom} (upsell: {panier.article.isUpsell}): qté={panier.quantite}, prix={prix_unitaire}, sous_total={nouveau_sous_total}")
                
                # Mettre à jour le sous-total du panier si nécessaire
                if panier.sous_total != nouveau_sous_total:
                    panier.sous_total = float(nouveau_sous_total)
                    panier.save()
                
                nouveau_total += float(nouveau_sous_total)
        
        # Ajouter les frais de livraison au total SEULEMENT si frais_livraison = True
        if self.frais_livraison:
            frais_livraison = self.ville.frais_livraison if self.ville else 0
            nouveau_total_avec_frais = float(nouveau_total) + float(frais_livraison)
        else:
            nouveau_total_avec_frais = float(nouveau_total)
        
        # Mettre à jour le total de la commande
        if self.total_cmd != nouveau_total_avec_frais:
            self.total_cmd = nouveau_total_avec_frais
            self.save(update_fields=['total_cmd'])
    
    @property
    def sous_total_articles(self):
        """Retourne le sous-total des articles sans les frais de livraison"""
        return sum(panier.sous_total for panier in self.paniers.all())

    def calculer_quantite_upsell_effective(self):
        """
        Calcule la quantité totale d'articles upsell en EXCLUANT SEULEMENT :
        1. Ceux avec remise appliquée (remise_appliquer=True)

        Les articles avec prix de remise disponibles mais pas appliqués participent au calcul.

        Returns:
            int: Quantité totale d'articles upsell effectifs pour le calcul
        """
        from django.db.models import Sum

        # Compter seulement les paniers upsell SANS remise appliquée
        total_quantite_upsell = self.paniers.filter(
            article__isUpsell=True,
            remise_appliquer=False  # EXCLU seulement les paniers avec remise appliquée
        ).aggregate(total=Sum('quantite'))['total'] or 0

        print(f"🔧 calculer_quantite_upsell_effective: {total_quantite_upsell} (excluant seulement les remises appliquées)")
        return total_quantite_upsell

    def recalculer_compteur_upsell(self):
        """
        Recalcule le compteur upsell en tenant compte des remises appliquées.
        Cette méthode doit être appelée chaque fois qu'une remise est appliquée/désactivée.
        """
        total_quantite_upsell_effective = self.calculer_quantite_upsell_effective()
        ancien_compteur = self.compteur

        # Appliquer la logique : compteur = max(0, total_quantite_upsell_effective - 1)
        if total_quantite_upsell_effective >= 2:
            self.compteur = total_quantite_upsell_effective - 1
        else:
            self.compteur = 0

        if ancien_compteur != self.compteur:
            self.save(update_fields=['compteur'])
            print(f"🔄 Compteur upsell recalculé: {ancien_compteur} → {self.compteur} (quantité effective: {total_quantite_upsell_effective})")

        return self.compteur

    def mettre_a_jour_compteur_si_necessaire(self):
        """
        Version simplifiée qui met à jour automatiquement le compteur sans signal.
        À appeler dans les vues après changement de remise.
        """
        self.recalculer_compteur_upsell()
        self.recalculer_totaux_upsell()
    
    @property
    def total_articles(self):
        """Alias pour sous_total_articles pour la compatibilité avec les templates"""
        return self.sous_total_articles
    
    @property
    def montant_frais_livraison(self):
        """Retourne le montant des frais de livraison de la ville"""
        frais = self.ville.frais_livraison if self.ville else 0
        return float(frais)
    
    @property
    def total_avec_frais(self):
        """Retourne le total articles + frais de livraison"""
        return float(self.sous_total_articles) + float(self.montant_frais_livraison)
    
    def corriger_paniers_liquidation_et_promotion(self):
        """
        Corrige automatiquement tous les paniers d'articles en liquidation et en promotion
        pour s'assurer qu'ils n'ont pas remise_appliquer = True
        """
        from django.db.models import Q
        
        # Corriger les paniers d'articles en liquidation
        paniers_liquidation = self.paniers.filter(
            article__phase='LIQUIDATION',
            remise_appliquer=True
        )
        
        for panier in paniers_liquidation:
            print(f"🔧 Correction panier liquidation: {panier.article.nom}")
            # Recalculer le sous-total avec le prix de liquidation
            prix_liquidation = panier.article.Prix_liquidation or panier.article.prix_actuel or panier.article.prix_unitaire
            panier.sous_total = float(prix_liquidation) * panier.quantite
            panier.remise_appliquer = False
            panier.type_remise_appliquee = ''
            panier.save()
        
        # Corriger les paniers d'articles en promotion
        # Utiliser une requête Django pour identifier les articles avec promotions actives
        from django.utils import timezone
        now = timezone.now()
        
        paniers_promotion = self.paniers.filter(
            article__promotions__active=True,
            article__promotions__date_debut__lte=now,
            article__promotions__date_fin__gte=now,
            remise_appliquer=True
        ).distinct()
        
        for panier in paniers_promotion:
            print(f"🔧 Correction panier promotion: {panier.article.nom}")
            # Recalculer le sous-total avec le prix promotionnel
            prix_promotion = panier.article.prix_actuel or panier.article.prix_unitaire
            panier.sous_total = float(prix_promotion) * panier.quantite
            panier.remise_appliquer = False
            panier.type_remise_appliquee = ''
            panier.save()

    def recalculer_total_avec_frais(self):
        """
        Recalcule le total de la commande en incluant les frais de livraison
        SEULEMENT si frais_livraison = True
        """
        # Corriger d'abord les paniers en liquidation et en promotion
        self.corriger_paniers_liquidation_et_promotion()
        
        # Calculer le sous-total des articles
        sous_total_articles = sum(panier.sous_total for panier in self.paniers.all())
        
        if self.frais_livraison:
            # Récupérer les frais de livraison de la ville
            frais_ville = self.ville.frais_livraison if self.ville else 0
            
            # Calculer le nouveau total avec frais
            nouveau_total = float(sous_total_articles) + float(frais_ville)
            
            # Mettre à jour le total si nécessaire
            if self.total_cmd != nouveau_total:
                self.total_cmd = nouveau_total
                # Éviter la récursion en utilisant update_fields
                Commande.objects.filter(id=self.id).update(total_cmd=nouveau_total)
                print(f"✅ Frais de livraison ajoutés: {sous_total_articles} + {frais_ville} = {nouveau_total}")
        else:
            # Si frais_livraison = False, calculer le total sans frais
            nouveau_total = float(sous_total_articles)
            if self.total_cmd != nouveau_total:
                self.total_cmd = nouveau_total
                Commande.objects.filter(id=self.id).update(total_cmd=nouveau_total)
                print(f"ℹ️  Frais de livraison désactivés - Total recalculé: {nouveau_total}")

    # === Méthodes pour la gestion des articles retournés ===
    
    def get_articles_retournes(self):
        """Retourne tous les articles retournés pour cette commande"""
        return self.articles_retournes.all()
    
    def articles_retournes_en_attente(self):
        """Retourne les articles retournés en attente de traitement"""
        return self.articles_retournes.filter(statut_retour='en_attente')
    
    def articles_retournes_count(self):
        """Nombre total d'articles retournés pour cette commande"""
        return self.articles_retournes.count()
    
    def valeur_articles_retournes(self):
        """Valeur totale des articles retournés"""
        total = 0
        for article_retourne in self.articles_retournes.all():
            total += float(article_retourne.valeur_retour())
        return total
    
    def a_des_articles_retournes(self):
        """Vérifie si la commande a des articles retournés"""
        return self.articles_retournes.exists()
    
    def peut_reintegrer_articles_retournes(self):
        """Vérifie si des articles retournés peuvent être réintégrés en stock"""
        return self.articles_retournes.filter(
            statut_retour='en_attente',
            variante__isnull=False,
            variante__actif=True
        ).exists()
    
    def reintegrer_tous_articles_retournes(self, operateur=None, commentaire="Réintégration automatique"):
        """Réintègre automatiquement tous les articles retournés éligibles"""
        articles_reintegres = 0
        for article_retourne in self.articles_retournes_en_attente():
            if article_retourne.peut_etre_reintegre():
                if article_retourne.reintegrer_stock(operateur, commentaire):
                    articles_reintegres += 1
        return articles_reintegres
    
    def resume_retours(self):
        """Résumé des retours pour cette commande"""
        retours = self.articles_retournes.all()
        if not retours:
            return None
        
        return {
            'total_articles': retours.count(),
            'total_quantite': sum(r.quantite_retournee for r in retours),
            'total_valeur': sum(r.valeur_retour() for r in retours),
            'en_attente': retours.filter(statut_retour='en_attente').count(),
            'reintegres': retours.filter(statut_retour='reintegre_stock').count(),
            'traites': retours.exclude(statut_retour='en_attente').count()
        }


class Panier(models.Model):
    CHOIX_TYPE_REMISE = [
        ('', 'Aucune remise'),
        ('remise_1', 'Prix remise 1'),
        ('remise_2', 'Prix remise 2'),
        ('remise_3', 'Prix remise 3'),
        ('remise_4', 'Prix remise 4'),
      
    ]
    
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='paniers')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='paniers')
    variante = models.ForeignKey(VarianteArticle, on_delete=models.SET_NULL, null=True, blank=True, related_name='paniers')
    quantite = models.IntegerField()
    sous_total = models.FloatField()
    remise_appliquer = models.BooleanField(default=False)
    type_remise_appliquee = models.CharField(max_length=20, choices=CHOIX_TYPE_REMISE, blank=True, default='')
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        unique_together = [['commande', 'article', 'variante']]
        constraints = [
            models.CheckConstraint(check=models.Q(quantite__gt=0), name='quantite_positive'),
            models.CheckConstraint(check=models.Q(sous_total__gte=0), name='sous_total_positif'),
        ]
    
    def save(self, *args, **kwargs):
        # Protection : les articles en liquidation et en promotion ne peuvent pas avoir remise_appliquer = True
        if self.article:
            article_en_liquidation = self.article.phase == 'LIQUIDATION'
            article_en_promotion = hasattr(self.article, 'has_promo_active') and self.article.has_promo_active

            if (article_en_liquidation or article_en_promotion) and self.remise_appliquer:
                motif = "liquidation" if article_en_liquidation else "promotion"
                print(f"⚠️ PROTECTION: Article {self.article.nom} en {motif} - remise_appliquer forcé à False")
                self.remise_appliquer = False
                self.type_remise_appliquee = ''

        super().save(*args, **kwargs)

    def calculer_et_sauvegarder_prix(self, force_recalcul=False):
        """
        Calcule et sauvegarde le prix unitaire et le sous-total de ce panier en tenant compte :
        - Des remises appliquées (remise_appliquer=True)
        - Des prix upsell selon le compteur de la commande
        - Des promotions actives
        - De la phase de l'article (liquidation, test, etc.)

        IMPORTANT: Ne recalcule PAS si la commande est confirmée ou dans un état avancé,
        sauf si force_recalcul=True.

        Args:
            force_recalcul: Si True, force le recalcul même pour commandes confirmées (défaut: False)

        Returns:
            dict: {
                'prix_unitaire': Prix unitaire calculé,
                'sous_total': Sous-total calculé,
                'type_prix': Type de prix appliqué,
                'recalcule': True si le prix a été recalculé, False sinon
            }
        """
        from decimal import Decimal

        # Validation
        if not self.article or self.quantite <= 0:
            return {
                'prix_unitaire': 0,
                'sous_total': 0,
                'type_prix': 'error',
                'recalcule': False
            }

        # PROTECTION: Ne PAS recalculer si la commande est confirmée ou dans un état avancé
        # Les prix sont "gelés" au moment de la confirmation
        etats_proteges = [
            'Confirmée',
            'En préparation',
            'Préparation en cours',
            'Préparée',
            'Mise en distribution',
            'En cours de livraison',
            'En livraison',
            'Livrée',
            'Livrée Partiellement',
            'Livrée avec changement',
            'Retournée',
            'Reportée'
        ]

        if not force_recalcul and self.commande.etat_actuel:
            etat_actuel_libelle = self.commande.etat_actuel.enum_etat.libelle
            if etat_actuel_libelle in etats_proteges:
                # Commande confirmée ou avancée - NE PAS RECALCULER
                prix_unitaire = Decimal(str(self.sous_total)) / Decimal(str(self.quantite))
                return {
                    'prix_unitaire': float(prix_unitaire),
                    'sous_total': float(self.sous_total),
                    'type_prix': 'prix_gele',
                    'recalcule': False,
                    'message': f'Prix gelé - Commande en état "{etat_actuel_libelle}"'
                }

        # 1. Si une remise a été appliquée - NE PAS RECALCULER
        if self.remise_appliquer:
            # Protéger contre les articles en liquidation/promotion
            if self.article.phase == 'LIQUIDATION' or (hasattr(self.article, 'has_promo_active') and self.article.has_promo_active):
                # Forcer la suppression de la remise
                self.remise_appliquer = False
                self.type_remise_appliquee = ''
                # Continuer vers le calcul normal
            else:
                # Conserver le prix avec remise - le sous_total est déjà correct
                prix_unitaire = Decimal(str(self.sous_total)) / Decimal(str(self.quantite))
                return {
                    'prix_unitaire': float(prix_unitaire),
                    'sous_total': float(self.sous_total),
                    'type_prix': f'remise_{self.type_remise_appliquee}',
                    'recalcule': False
                }

        # 2. Déterminer le prix unitaire selon les règles métier
        prix_unitaire = None
        type_prix = 'normal'

        # Promotion active - priorité sur tout sauf remise appliquée
        if hasattr(self.article, 'has_promo_active') and self.article.has_promo_active:
            prix_unitaire = self.article.prix_actuel or self.article.prix_unitaire
            type_prix = 'promotion'

        # Phase liquidation
        elif self.article.phase == 'LIQUIDATION':
            prix_unitaire = self.article.Prix_liquidation if hasattr(self.article, 'Prix_liquidation') and self.article.Prix_liquidation else self.article.prix_actuel or self.article.prix_unitaire
            type_prix = 'liquidation'

        # Phase test
        elif self.article.phase == 'EN_TEST':
            prix_unitaire = self.article.prix_actuel or self.article.prix_unitaire
            type_prix = 'test'

        # Article upsell avec compteur
        elif hasattr(self.article, 'isUpsell') and self.article.isUpsell and self.commande.compteur > 0:
            # Calculer le prix selon le compteur
            if self.commande.compteur == 1 and self.article.prix_upsell_1:
                prix_unitaire = self.article.prix_upsell_1
            elif self.commande.compteur == 2 and self.article.prix_upsell_2:
                prix_unitaire = self.article.prix_upsell_2
            elif self.commande.compteur == 3 and self.article.prix_upsell_3:
                prix_unitaire = self.article.prix_upsell_3
            elif self.commande.compteur >= 4 and self.article.prix_upsell_4:
                prix_unitaire = self.article.prix_upsell_4
            else:
                prix_unitaire = self.article.prix_actuel or self.article.prix_unitaire
            type_prix = f'upsell_niveau_{self.commande.compteur}'

        # Prix normal
        else:
            prix_unitaire = self.article.prix_actuel or self.article.prix_unitaire
            type_prix = 'normal'

        # 3. Calculer le sous-total
        prix_unitaire = Decimal(str(prix_unitaire))
        sous_total = prix_unitaire * Decimal(str(self.quantite))

        # 4. Sauvegarder dans le panier
        self.sous_total = float(sous_total)
        self.save(update_fields=['sous_total', 'remise_appliquer', 'type_remise_appliquee'])

        return {
            'prix_unitaire': float(prix_unitaire),
            'sous_total': float(sous_total),
            'type_prix': type_prix,
            'recalcule': True
        }

    def __str__(self):
        return f"{self.commande.num_cmd} - {self.article.nom} (x{self.quantite})"


class EtatCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='etats')
    enum_etat = models.ForeignKey(EnumEtatCmd, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE, related_name='etats_modifies', blank=True, null=True)
    date_fin_delayed = models.DateTimeField(blank=True, null=True, verbose_name="Date reporte de confirmation décalée")
    
    class Meta:
        verbose_name = "État de commande(Suivi de commande)"
        verbose_name_plural = "États de commande(Suivi de commande)"
        ordering = ['-date_debut']
        constraints = [
            models.CheckConstraint(
                check=models.Q(date_fin__isnull=True) | models.Q(date_debut__lte=models.F('date_fin')),
                name='date_debut_avant_date_fin'
            ),
        ]
    
    def __str__(self):
        return f"{self.commande.num_cmd} - {self.enum_etat.libelle}"
    
    def terminer_etat(self, operateur=None):
        """Termine cet état en définissant la date_fin"""
        self.date_fin = timezone.now()
        if operateur:
            self.operateur = operateur
        self.save()
    
    @property
    def duree(self):
        """Retourne la durée de cet état au format Xj HH:MM:SS"""
        if self.date_fin:
            delta = self.date_fin - self.date_debut
        else:
            delta = timezone.now() - self.date_debut

        # Conversion en secondes
        total_seconds = int(delta.total_seconds())

        jours, reste = divmod(total_seconds, 86400)  # 86400 sec = 1 jour
        heures, reste = divmod(reste, 3600)
        minutes, secondes = divmod(reste, 60)

        if jours > 0:
            return f"{jours}j {heures:02d}h : {minutes:02d}m : {secondes:02d}s"
        elif heures > 0:
            return f"{heures:02d}h : {minutes:02d}m : {secondes:02d}s"
        else:
            return f"{minutes:02d}m : {secondes:02d}s"


class Operation(models.Model):
    TYPE_OPERATION_CHOICES = [
        # Opérations spécifiques de confirmation
        ('APPEL', 'Appel '),
        ("Appel Whatsapp", "Appel Whatsapp"),
        ("Message Whatsapp", "Appel Whatsapp "),
        ("Vocal Whatsapp", "Vocal Whatsapp "),
        ('ENVOI_SMS', 'Envoi de SMS'),
    ]
    Type_Commentaire_CHOICES=[
        ("Appel 1", "Appel 1"),
        ("Appel 2", "Appel 2"),
        ("Appel 3", "Appel 3"),
        ("Appel 4", "Appel 4"),
        ("Appel 5", "Appel 5"),
        ("Appel 6", "Appel 6"),
        ("Confirmée", "Confirmée"),
        ("Confirmée & Echangée", "Confirmée & Echangée"),
        ("Echangée", "Echangée"),
        ("Abonnement","Abonnement"),
        ("Offre","Offre"),
        ('numero errone',"numéro erroné"),
        ('boite vocalee',"boite vocalee"),
        ("indisponible","indisponible"),
        

    ]
    
    type_operation = models.CharField(max_length=30, choices=TYPE_OPERATION_CHOICES)
    date_operation = models.DateTimeField(default=timezone.now)
    conclusion = models.TextField()
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='operations')
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE, related_name='operations')
    commentaire = models.TextField( blank=True, null=True,choices=Type_Commentaire_CHOICES)
    
    class Meta:
        verbose_name = "Opération"
        verbose_name_plural = "Opérations"
        ordering = ['-date_operation']
    
    def __str__(self):
        return f"{self.get_type_operation_display()} - {self.commande.num_cmd} par {self.operateur}"


class Envoi(models.Model):
    # Relations
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='envois', null=True, blank=True)   
    region = models.ForeignKey(
        'parametre.Region', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='envois'
    )
    # Informations principales
    date_envoi = models.DateField(default=timezone.now, verbose_name="Date d'envoi")
    date_livraison_prevue = models.DateField(verbose_name="Date de livraison prévue")
    date_livraison_effective = models.DateField(null=True, blank=True, verbose_name="Date de clôture")
    # Statut et suivi
    status = models.BooleanField(default=True, verbose_name="En cours")
    numero_envoi = models.CharField(max_length=50, blank=True, verbose_name="Numéro d'envoi")
    # Opérateurs et traçabilité
    operateur_creation = models.ForeignKey(
        Operateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='envois_crees',
        verbose_name="Créé par"
    )
    
    # Dates de suivi
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Statistiques
    nb_commandes = models.PositiveIntegerField(default=0, verbose_name="Nombre de commandes")

    class Meta:
        verbose_name = "Envoi"
        verbose_name_plural = "Envois"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['status', 'date_creation']),
            models.Index(fields=['region', 'date_envoi']),
        ]

    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro d'envoi si pas défini
        if not self.numero_envoi:
            from django.utils import timezone
            today = timezone.now().date()
            count = Envoi.objects.filter(date_creation__date=today).count() + 1
            self.numero_envoi = f"ENV-{today.strftime('%Y%m%d')}-{count:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        status_text = "En cours" if self.status else "Clôturé"
        return f"Envoi {self.numero_envoi} - {status_text}"

    @property
    def commandes_associees(self):
        """Retourne les commandes associées à cet envoi"""
        return self.commande_set.all()

    def marquer_comme_livre(self, operateur, date_livraison=None):
        """Marquer l'envoi comme livré (clôturé)"""
        from django.utils import timezone
        self.status = False  # False = clôturé
        self.date_livraison_effective = date_livraison or timezone.now().date()
        self.save()

    def annuler(self, operateur):
        """Annuler l'envoi"""
        self.status = False  # False = annulé/clôturé
        self.save()

class EtatArticleRenvoye(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, related_name='etats_articles_renvoyes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    etat = models.ForeignKey(EnumEtatCmd, on_delete=models.PROTECT)  # FK vers la table d’états
    quantite = models.PositiveIntegerField(default=1)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('commande', 'article')
        verbose_name = "État d'article renvoyé"
        verbose_name_plural = "États d'articles renvoyés"

    def __str__(self):
        return f"{self.article} ({self.etat}) dans {self.commande}"


class EtiquetteTemplate(models.Model):
    """Template pour les étiquettes d'articles professionnelles"""
    name = models.CharField(max_length=100, verbose_name="Nom du template")
    width = models.FloatField(default=180, verbose_name="Largeur (mm)")
    height = models.FloatField(default=260, verbose_name="Hauteur (mm)")
    margin_top = models.FloatField(default=10, verbose_name="Marge haute (mm)")
    margin_bottom = models.FloatField(default=10, verbose_name="Marge basse (mm)")
    margin_left = models.FloatField(default=10, verbose_name="Marge gauche (mm)")
    margin_right = models.FloatField(default=10, verbose_name="Marge droite (mm)")
    
    # Styles
    font_family = models.CharField(max_length=50, default="Helvetica", verbose_name="Police")
    font_size_title = models.IntegerField(default=16, verbose_name="Taille police titre")
    font_size_text = models.IntegerField(default=12, verbose_name="Taille police texte")
    font_size_barcode = models.IntegerField(default=14, verbose_name="Taille police code-barres")
    
    # Couleurs
    color_header = models.CharField(max_length=7, default="#2c3e50", verbose_name="Couleur en-tête")
    color_footer = models.CharField(max_length=7, default="#2c3e50", verbose_name="Couleur pied")
    color_text = models.CharField(max_length=7, default="#333333", verbose_name="Couleur texte")
    
    # Code-barres
    barcode_width = models.FloatField(default=4, verbose_name="Largeur barres (mm)")
    barcode_height = models.FloatField(default=80, verbose_name="Hauteur barres (mm)")
    barcode_format = models.CharField(max_length=20, default="CODE128B", verbose_name="Format code-barres")
    
    # QR Code
    qr_size = models.IntegerField(default=300, verbose_name="Taille QR code (px)")
    
    # Options
    show_header = models.BooleanField(default=True, verbose_name="Afficher en-tête")
    show_footer = models.BooleanField(default=True, verbose_name="Afficher pied")
    show_barcode = models.BooleanField(default=True, verbose_name="Afficher code-barres")
    show_qr = models.BooleanField(default=False, verbose_name="Afficher QR code")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Template d'étiquette"
        verbose_name_plural = "Templates d'étiquettes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.width}x{self.height}mm)"
    
    def get_dimensions(self):
        """Retourne les dimensions en points (pour ReportLab)"""
        from reportlab.lib.units import mm
        return (self.width * mm, self.height * mm)
    
    def get_margins(self):
        """Retourne les marges en points"""
        from reportlab.lib.units import mm
        return {
            'top': self.margin_top * mm,
            'bottom': self.margin_bottom * mm,
            'left': self.margin_left * mm,
            'right': self.margin_right * mm
        }


class ArticleRetourne(models.Model):
    """
    Modèle pour stocker les articles/variantes retournés lors d'une livraison partielle.
    Ces articles seront réintégrés en stock ou renvoyés en préparation.
    """
    commande = models.ForeignKey(
        'Commande', 
        on_delete=models.CASCADE, 
        related_name='articles_retournes',
        help_text="Commande d'origine de l'article retourné"
    )
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE,
        help_text="Article retourné"
    )
    variante = models.ForeignKey(
        VarianteArticle,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Variante spécifique de l'article retourné"
    )
    quantite_retournee = models.PositiveIntegerField(
        help_text="Quantité retournée de cet article/variante"
    )
    prix_unitaire_origine = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Prix unitaire de l'article au moment de la livraison partielle"
    )
    raison_retour = models.TextField(
        max_length=500,
        blank=True,
        help_text="Raison du retour (optionnel)"
    )
    date_retour = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure du retour"
    )
    operateur_retour = models.ForeignKey(
        Operateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Opérateur qui a effectué le retour"
    )
    
    # Statut du traitement du retour
    STATUT_RETOUR_CHOICES = [
        ('en_attente', 'En attente de traitement'),
        ('reintegre_stock', 'Réintégré en stock'),
        ('renvoye_preparation', 'Renvoyé en préparation'),
        ('defectueux', 'Défectueux - à écarter'),
        ('traite', 'Traité'),
    ]
    
    statut_retour = models.CharField(
        max_length=50,
        choices=STATUT_RETOUR_CHOICES,
        default='en_attente',
        help_text="Statut du traitement du retour"
    )
    
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de traitement du retour"
    )
    
    operateur_traitement = models.ForeignKey(
        Operateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retours_traites',
        help_text="Opérateur qui a traité le retour"
    )
    
    commentaire_traitement = models.TextField(
        max_length=500,
        blank=True,
        help_text="Commentaire sur le traitement du retour"
    )

    class Meta:
        verbose_name = "Article Retourné"
        verbose_name_plural = "Articles Retournés"
        ordering = ['-date_retour']
        indexes = [
            models.Index(fields=['commande', 'statut_retour']),
            models.Index(fields=['article', 'statut_retour']),
            models.Index(fields=['date_retour']),
        ]

    def __str__(self):
        variante_str = f" ({self.variante})" if self.variante else ""
        return f"Retour: {self.article.nom}{variante_str} x{self.quantite_retournee} - Commande {self.commande.id_yz}"

    def valeur_retour(self):
        """Calcule la valeur totale du retour"""
        return self.quantite_retournee * self.prix_unitaire_origine

    def peut_etre_reintegre(self):
        """Vérifie si l'article peut être réintégré en stock"""
        return self.statut_retour == 'en_attente' and self.variante and self.variante.actif

    def reintegrer_stock(self, operateur=None, commentaire=""):
        """Réintègre l'article en stock"""
        if self.peut_etre_reintegre():
            # Augmenter la quantité disponible de la variante
            self.variante.qte_disponible += self.quantite_retournee
            self.variante.save(update_fields=['qte_disponible'])
            
            # Mettre à jour le statut
            self.statut_retour = 'reintegre_stock'
            self.date_traitement = timezone.now()
            self.operateur_traitement = operateur
            self.commentaire_traitement = commentaire or f"Réintégré automatiquement en stock: +{self.quantite_retournee}"
            self.save()
            
            return True
        return False
