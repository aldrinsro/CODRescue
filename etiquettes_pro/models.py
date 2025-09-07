from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EtiquetteTemplate(models.Model):
    """Modèle pour les templates d'étiquettes"""
    
    FORMAT_CHOICES = [
        ('A4', 'A4 (210x297mm)'),
        ('A5', 'A5 (148x210mm)'),
        ('A6', 'A6 (105x148mm)'),
        ('CUSTOM', 'Personnalisé'),
    ]
    
    TYPE_CHOICES = [
        ('article', 'Étiquette Article'),
        ('commande', 'Étiquette Commande'),
        ('livraison', 'Étiquette Livraison'),
        ('stock', 'Étiquette Stock'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom du template")
    description = models.TextField(blank=True, verbose_name="Description")
    type_etiquette = models.CharField(max_length=20, choices=TYPE_CHOICES, default='article')
    format_page = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='A4')
    
    # Dimensions personnalisées
    largeur = models.FloatField(default=210, verbose_name="Largeur (mm)")
    hauteur = models.FloatField(default=297, verbose_name="Hauteur (mm)")
    
    # Paramètres du code-barres/QR
    code_type = models.CharField(max_length=20, choices=[
        ('barcode', 'Code-barres'),
        ('qr', 'QR Code'),
        ('both', 'Les deux'),
    ], default='barcode')
    
    code_size = models.IntegerField(default=80, verbose_name="Taille du code (mm)")
    code_position = models.CharField(max_length=20, choices=[
        ('center', 'Centre'),
        ('left', 'Gauche'),
        ('right', 'Droite'),
    ], default='center')
    
    # Dimensions personnalisées des codes
    code_width = models.IntegerField(default=80, verbose_name="Largeur du code (mm)")
    code_height = models.IntegerField(default=25, verbose_name="Hauteur du code (mm)")
    code_quality = models.CharField(max_length=20, choices=[
        ('standard', 'Standard (300 DPI)'),
        ('high', 'Haute qualité (600 DPI)'),
        ('ultra', 'Ultra qualité (4K)'),
    ], default='high', verbose_name="Qualité du code")
    
    # Paramètres de bordures
    border_enabled = models.BooleanField(default=True, verbose_name="Activer les bordures")
    border_width = models.FloatField(default=1.0, verbose_name="Épaisseur des bordures (mm)")
    border_color = models.CharField(max_length=7, default='#000000', verbose_name="Couleur des bordures")
    border_radius = models.FloatField(default=2.0, verbose_name="Rayon des coins arrondis (mm)")
    
    # Paramètres de design
    police_titre = models.CharField(max_length=50, default='Helvetica-Bold')
    taille_titre = models.IntegerField(default=16)
    police_texte = models.CharField(max_length=50, default='Helvetica')
    taille_texte = models.IntegerField(default=12)
    
    # Couleurs
    couleur_principale = models.CharField(max_length=7, default='#3B82F6', verbose_name="Couleur principale")
    couleur_secondaire = models.CharField(max_length=7, default='#1E40AF', verbose_name="Couleur secondaire")
    couleur_texte = models.CharField(max_length=7, default='#1F2937', verbose_name="Couleur du texte")
    
    # Métadonnées
    actif = models.BooleanField(default=True)
    cree_par = models.ForeignKey(User, on_delete=models.CASCADE, related_name='templates_etiquettes')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template d'étiquette"
        verbose_name_plural = "Templates d'étiquettes"
        ordering = ['-date_creation']
        permissions = [
            ("can_manage_etiquette_templates", "Peut gérer les templates d'étiquettes"),
            ("can_view_etiquette_templates", "Peut voir les templates d'étiquettes"),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_etiquette_display()})"


class Etiquette(models.Model):
    """Modèle pour les étiquettes générées"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('ready', 'Prête'),
        ('printed', 'Imprimée'),
        ('archived', 'Archivée'),
    ]
    
    template = models.ForeignKey(EtiquetteTemplate, on_delete=models.CASCADE, related_name='etiquettes')
    
    # Données de l'étiquette
    reference = models.CharField(max_length=100, verbose_name="Référence")
    nom_article = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'article")
    variante = models.CharField(max_length=100, blank=True, verbose_name="Variante")
    commande_id = models.CharField(max_length=50, blank=True, verbose_name="ID Commande")
    client_nom = models.CharField(max_length=200, blank=True, verbose_name="Nom du client")
    
    # Panier (liste d'articles avec variantes et quantités)
    cart_items = models.JSONField(null=True, blank=True, verbose_name="Articles du panier")
    
    # Code-barres/QR
    code_data = models.TextField(verbose_name="Données du code")
    code_generated = models.BooleanField(default=False)
    
    # Statut et métadonnées
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    cree_par = models.ForeignKey(User, on_delete=models.CASCADE, related_name='etiquettes_creees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_impression = models.DateTimeField(null=True, blank=True)
    
    # Fichier PDF généré
    fichier_pdf = models.FileField(upload_to='etiquettes_pdf/', null=True, blank=True)
    
    class Meta:
        verbose_name = "Étiquette"
        verbose_name_plural = "Étiquettes"
        ordering = ['-date_creation']
        permissions = [
            ("can_manage_etiquettes", "Peut gérer les étiquettes"),
            ("can_view_etiquettes", "Peut voir les étiquettes"),
            ("can_print_etiquettes", "Peut imprimer les étiquettes"),
        ]
    
    def __str__(self):
        return f"Étiquette {self.reference} - {self.template.nom}"

