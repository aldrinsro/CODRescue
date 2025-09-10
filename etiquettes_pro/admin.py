from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EtiquetteTemplate, Etiquette


@admin.register(EtiquetteTemplate)
class EtiquetteTemplateAdmin(admin.ModelAdmin):
    """Administration des Templates d'Étiquettes"""
    
    list_display = [
        'nom', 'type_etiquette', 'format_page', 'code_type', 
        'code_quality', 'border_status', 'actif', 'date_creation'
    ]
    list_filter = [
        'type_etiquette', 'format_page', 'code_type', 'code_quality', 
        'border_enabled', 'actif', 'date_creation'
    ]
    search_fields = ['nom', 'description', 'cree_par__username']
    ordering = ['-date_creation']
    list_per_page = 25
    list_editable = ['actif']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('📋 Informations Générales', {
            'fields': ('nom', 'description', 'type_etiquette', 'actif'),
            'classes': ('wide',)
        }),
        ('📏 Dimensions', {
            'fields': ('format_page', 'largeur', 'hauteur'),
            'description': 'Définissez les dimensions de votre étiquette'
        }),
        ('🔢 Configuration des Codes', {
            'fields': ('code_type', 'code_size', 'code_position', 'code_width', 'code_height', 'code_quality'),
            'description': 'Paramètres pour les codes-barres et QR codes'
        }),
        ('🖼️ Paramètres de Bordures', {
            'fields': ('border_enabled', 'border_width', 'border_color', 'border_radius'),
            'classes': ('collapse',),
            'description': 'Personnalisez l\'apparence des bordures'
        }),
        ('🎨 Design et Polices', {
            'fields': ('police_titre', 'taille_titre', 'police_texte', 'taille_texte'),
            'description': 'Configuration de la typographie'
        }),
        ('🌈 Couleurs', {
            'fields': ('couleur_principale', 'couleur_secondaire', 'couleur_texte'),
            'description': 'Palette de couleurs du template'
        }),
        ('📊 Métadonnées', {
            'fields': ('cree_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_creation', 'date_modification']
    
    def border_status(self, obj):
        """Afficher le statut des bordures avec une icône"""
        if obj.border_enabled:
            return format_html(
                '<span style="color: green;">✅ Activées</span><br>'
                '<small>Épaisseur: {}mm | Couleur: {}</small>',
                obj.border_width, obj.border_color
            )
        else:
            return format_html('<span style="color: red;">❌ Désactivées</span>')
    border_status.short_description = 'Bordures'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cree_par')


@admin.register(Etiquette)
class EtiquetteAdmin(admin.ModelAdmin):
    """Administration des Étiquettes"""
    
    list_display = [
        'reference', 'template_link', 'statut', 'commande_id', 
        'client_nom', 'code_status', 'date_creation', 'cart_items_count'
    ]
    list_filter = [
        'template', 'statut', 'code_generated', 'date_creation', 
        'template__type_etiquette', 'template__code_quality'
    ]
    search_fields = [
        'reference', 'nom_article', 'commande_id', 'client_nom', 'code_data'
    ]
    ordering = ['-date_creation']
    list_per_page = 25
    list_editable = ['statut']
    date_hierarchy = 'date_creation'
    actions = ['mark_as_ready', 'mark_as_printed', 'regenerate_codes']
    
    fieldsets = (
        ('📋 Informations Générales', {
            'fields': ('template', 'reference', 'statut'),
            'classes': ('wide',)
        }),
        ('📦 Données de l\'Étiquette', {
            'fields': ('nom_article', 'variante', 'commande_id', 'client_nom', 'cart_items'),
            'description': 'Informations spécifiques à cette étiquette'
        }),
        ('🔢 Code-barres/QR', {
            'fields': ('code_data', 'code_generated'),
            'description': 'Données et statut de génération du code'
        }),
        ('📄 Fichier PDF', {
            'fields': ('fichier_pdf',),
            'classes': ('collapse',),
            'description': 'Fichier PDF généré (si disponible)'
        }),
        ('📊 Métadonnées', {
            'fields': ('cree_par', 'date_creation', 'date_impression'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_creation']
    
    def template_link(self, obj):
        """Lien vers le template"""
        url = reverse('admin:etiquettes_pro_etiquettetemplate_change', args=[obj.template.id])
        return format_html('<a href="{}">{}</a>', url, obj.template.nom)
    template_link.short_description = 'Template'
    template_link.admin_order_field = 'template__nom'
    
    def statut_badge(self, obj):
        """Afficher le statut avec une couleur"""
        colors = {
            'draft': 'orange',
            'ready': 'green',
            'printed': 'blue',
            'archived': 'gray'
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
    statut_badge.admin_order_field = 'statut'
    
    def code_status(self, obj):
        """Statut de génération du code"""
        if obj.code_generated:
            return format_html('<span style="color: green;">✅ Généré</span>')
        else:
            return format_html('<span style="color: red;">❌ Non généré</span>')
    code_status.short_description = 'Code'
    code_status.admin_order_field = 'code_generated'
    
    def cart_items_count(self, obj):
        if obj.cart_items:
            return f"{len(obj.cart_items)} articles"
        return "0 articles"
    cart_items_count.short_description = "Panier Articles"
    
    def mark_as_ready(self, request, queryset):
        """Marquer comme prêtes"""
        updated = queryset.update(statut='ready')
        self.message_user(request, f'{updated} étiquettes marquées comme prêtes.')
    mark_as_ready.short_description = "Marquer comme prêtes"
    
    def mark_as_printed(self, request, queryset):
        """Marquer comme imprimées"""
        from django.utils import timezone
        updated = queryset.update(statut='printed', date_impression=timezone.now())
        self.message_user(request, f'{updated} étiquettes marquées comme imprimées.')
    mark_as_printed.short_description = "Marquer comme imprimées"
    
    def regenerate_codes(self, request, queryset):
        """Régénérer les codes"""
        updated = queryset.update(code_generated=False)
        self.message_user(request, f'{updated} étiquettes marquées pour régénération des codes.')
    regenerate_codes.short_description = "Régénérer les codes"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'cree_par')


# Configuration de l'admin site
admin.site.site_header = "Administration YOZAK - Étiquettes Pro"
admin.site.site_title = "YOZAK Admin"
admin.site.index_title = "Gestion des Étiquettes Professionnelles"
