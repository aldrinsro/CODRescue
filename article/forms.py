from django import forms
from django.utils import timezone
from .models import Promotion, Article, VarianteArticle, Couleur, Pointure
from django.db.models import Q

"""
Formulaires pour la gestion des articles et promotions.

Gestion du fuseau horaire :
- Toutes les dates sont automatiquement converties au fuseau horaire configuré dans settings.py
- TIME_ZONE = 'Africa/Casablanca' est respecté pour l'affichage et le traitement
- Les dates sont rendues timezone-aware si nécessaire
- timezone.localtime() est utilisé pour convertir les dates stockées en fuseau local
"""

class FilteredSelectMultiple(forms.SelectMultiple):
    """Widget personnalisé pour améliorer la sélection multiple des articles"""
    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = ('admin/js/jquery.init.js', 'admin/js/SelectFilter2.js')

class PromotionForm(forms.ModelForm):
    # Champ de recherche pour les articles
    article_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher un article...',
            'class': 'article-search-input',
            'data-target': 'article-selection'
        }),
        label="Rechercher un article"
    )
    
    # Filtres pour les articles
    article_filter_categorie = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes catégories')],  # Sera rempli dynamiquement
        widget=forms.Select(attrs={'class': 'article-filter', 'data-filter': 'categorie'}),
        label="Filtrer par catégorie"
    )
    
    article_filter_couleur = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes couleurs')],  # Sera rempli dynamiquement
        widget=forms.Select(attrs={'class': 'article-filter', 'data-filter': 'couleur'}),
        label="Filtrer par couleur"
    )
    
    class Meta:
        model = Promotion
        fields = ['nom', 'description', 'pourcentage_reduction', 'date_debut', 'date_fin', 'articles', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'pourcentage_reduction': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.01'}),
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'articles': forms.CheckboxSelectMultiple(attrs={'class': 'article-selection'}),
        }
        labels = {
            'date_debut': "Date de début",
            'date_fin': "Date de fin",
            'articles': "Articles en promotion"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtenir l'heure actuelle dans le fuseau horaire configuré (Maroc)
        now = timezone.now()
        now_local = timezone.localtime(now)
        
        # Construire la requête de base pour les articles disponibles
        base_query = Q(phase='EN_COURS', actif=True)
        
        # Exclure les articles en promotion active (sauf ceux de la promotion actuelle)
        exclusion_query = Q(
            promotions__active=True,
            promotions__date_debut__lte=now,
            promotions__date_fin__gte=now
        )
        
        if self.instance.pk:
            # Ne pas exclure les articles de la promotion actuelle
            exclusion_query &= ~Q(promotions=self.instance)
        
        # Récupérer tous les articles disponibles
        articles_disponibles = Article.objects.filter(base_query).exclude(exclusion_query).distinct()
        
        # Limiter les choix d'articles
        if 'articles' in self.fields:
            self.fields['articles'].queryset = articles_disponibles
            self.fields['articles'].widget.attrs['data-selectable'] = 'true'
        
        # Conversion des dates au format ISO pour les champs datetime-local
        if self.instance.pk:
            if 'date_debut' in self.fields and self.instance.date_debut:
                # Convertir en fuseau horaire local (Maroc) puis formater
                date_debut_local = timezone.localtime(self.instance.date_debut)
                self.initial['date_debut'] = date_debut_local.strftime('%Y-%m-%dT%H:%M')
                print(f"DEBUG: Date début originale: {self.instance.date_debut}")
                print(f"DEBUG: Date début locale: {date_debut_local}")
                print(f"DEBUG: Format ISO: {date_debut_local.strftime('%Y-%m-%dT%H:%M')}")
            if 'date_fin' in self.fields and self.instance.date_fin:
                # Convertir en fuseau horaire local (Maroc) puis formater
                date_fin_local = timezone.localtime(self.instance.date_fin)
                self.initial['date_fin'] = date_fin_local.strftime('%Y-%m-%dT%H:%M')
                print(f"DEBUG: Date fin originale: {self.instance.date_fin}")
                print(f"DEBUG: Date fin locale: {date_fin_local}")
                print(f"DEBUG: Format ISO: {date_fin_local.strftime('%Y-%m-%dT%H:%M')}")
        
        # Remplir les options pour les filtres de catégorie et couleur
        categories = sorted(set(articles_disponibles.values_list('categorie__nom', flat=True)))
        couleurs = sorted(set(VarianteArticle.objects.filter(
            article__in=articles_disponibles, 
            actif=True
        ).values_list('couleur__nom', flat=True)))
        
        self.fields['article_filter_categorie'].choices += [(cat, cat) for cat in categories if cat]
        self.fields['article_filter_couleur'].choices += [(coul, coul) for coul in couleurs if coul]
        
        # Définir les champs initiaux pour la date/heure au format ISO
        if not self.instance.pk:  # Si c'est une nouvelle promotion
            if 'date_debut' in self.fields:
                # Utiliser l'heure actuelle dans le fuseau horaire local (Maroc)
                self.initial['date_debut'] = now_local.strftime('%Y-%m-%dT%H:%M')
                print(f"DEBUG: Nouvelle promotion - Date début: {now_local.strftime('%Y-%m-%dT%H:%M')}")
            if 'date_fin' in self.fields:
                # Définir la fin de journée dans le fuseau horaire local (Maroc)
                fin_journee = now_local.replace(hour=23, minute=59, second=59)
                self.initial['date_fin'] = fin_journee.strftime('%Y-%m-%dT%H:%M')
                print(f"DEBUG: Nouvelle promotion - Date fin: {fin_journee.strftime('%Y-%m-%dT%H:%M')}")
            if 'active' in self.fields:
                self.initial['active'] = True

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        pourcentage = cleaned_data.get('pourcentage_reduction')
        articles = cleaned_data.get('articles', [])

        print(f"DEBUG: Nettoyage des données - Date début: {date_debut}")
        print(f"DEBUG: Nettoyage des données - Date fin: {date_fin}")

        # Traitement des dates pour s'assurer qu'elles sont dans le bon fuseau horaire
        if date_debut:
            if not timezone.is_aware(date_debut):
                # Si la date n'est pas timezone-aware, l'interpréter comme étant dans le fuseau local (Maroc)
                date_debut = timezone.make_aware(date_debut, timezone.get_current_timezone())
                cleaned_data['date_debut'] = date_debut
                print(f"DEBUG: Date début rendue timezone-aware: {date_debut}")
            else:
                # Si déjà timezone-aware, convertir en fuseau local pour l'affichage
                date_debut_local = timezone.localtime(date_debut)
                print(f"DEBUG: Date début en fuseau local: {date_debut_local}")
        
        if date_fin:
            if not timezone.is_aware(date_fin):
                # Si la date n'est pas timezone-aware, l'interpréter comme étant dans le fuseau local (Maroc)
                date_fin = timezone.make_aware(date_fin, timezone.get_current_timezone())
                cleaned_data['date_fin'] = date_fin
                print(f"DEBUG: Date fin rendue timezone-aware: {date_fin}")
            else:
                # Si déjà timezone-aware, convertir en fuseau local pour l'affichage
                date_fin_local = timezone.localtime(date_fin)
                print(f"DEBUG: Date fin en fuseau local: {date_fin_local}")

        # Validation des dates
        if date_debut and date_fin:
            if date_fin <= date_debut:
                self.add_error('date_fin', "La date de fin doit être postérieure à la date de début")
            
            # Validation supplémentaire : la promotion doit durer au moins 1 heure
            if (date_fin - date_debut).total_seconds() < 3600:
                self.add_error('date_fin', "La promotion doit durer au moins 1 heure")
            
            print(f"DEBUG: Validation - Durée de la promotion: {(date_fin - date_debut).total_seconds() / 3600:.2f} heures")

        # Validation du pourcentage
        if pourcentage is not None:
            if pourcentage <= 0:
                self.add_error('pourcentage_reduction', "Le pourcentage de réduction doit être supérieur à 0")
            elif pourcentage > 100:
                self.add_error('pourcentage_reduction', "Le pourcentage de réduction ne peut pas dépasser 100")
        
        # Validation des articles (phase EN_COURS)
        if articles:
            articles_non_valides = [a for a in articles if a.phase != 'EN_COURS']
            if articles_non_valides:
                article_names = [f"{a.nom}" for a in articles_non_valides]
                self.add_error('articles', f"Seuls les articles en phase 'En Cours' peuvent être ajoutés à une promotion. "
                                         f"Articles non valides : {', '.join(article_names)}")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        print(f"DEBUG: Sauvegarde - Date début avant: {instance.date_debut}")
        print(f"DEBUG: Sauvegarde - Date fin avant: {instance.date_fin}")
        
        # S'assurer que les dates sont dans le bon fuseau horaire
        if instance.date_debut and not timezone.is_aware(instance.date_debut):
            # Si la date n'est pas timezone-aware, l'interpréter comme étant dans le fuseau local
            instance.date_debut = timezone.make_aware(instance.date_debut, timezone.get_current_timezone())
            print(f"DEBUG: Date début rendue timezone-aware: {instance.date_debut}")
        elif instance.date_debut:
            # Convertir en fuseau local pour vérification
            date_debut_local = timezone.localtime(instance.date_debut)
            print(f"DEBUG: Date début en fuseau local: {date_debut_local}")
            
        if instance.date_fin and not timezone.is_aware(instance.date_fin):
            # Si la date n'est pas timezone-aware, l'interpréter comme étant dans le fuseau local
            instance.date_fin = timezone.make_aware(instance.date_fin, timezone.get_current_timezone())
            print(f"DEBUG: Date fin rendue timezone-aware: {instance.date_fin}")
        elif instance.date_fin:
            # Convertir en fuseau local pour vérification
            date_fin_local = timezone.localtime(instance.date_fin)
            print(f"DEBUG: Date fin en fuseau local: {date_fin_local}")
        
        # Désactive automatiquement la promo si la date de fin est dépassée
        now = timezone.now()
        now_local = timezone.localtime(now)
        print(f"DEBUG: Heure actuelle (UTC): {now}")
        print(f"DEBUG: Heure actuelle (locale): {now_local}")
        
        if instance.date_fin < now:
            instance.active = False
            print(f"DEBUG: Promotion désactivée car date de fin dépassée")
        elif not instance.pk:  # Nouvelle instance
            instance.active = True
            print(f"DEBUG: Nouvelle promotion activée")
            
        if commit:
            instance.save()
            self.save_m2m()
            print(f"DEBUG: Promotion sauvegardée avec succès")
        return instance 

class AjustementStockForm(forms.Form):
    """
    Formulaire pour ajuster le stock d'un article
    """
    nouvelle_quantite = forms.IntegerField(
        min_value=0,
        label="Nouvelle quantité",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez la nouvelle quantité',
            'min': '0'
        }),
        help_text="Quantité en stock après ajustement"
    )
    
    commentaire = forms.CharField(
        required=False,
        max_length=500,
        label="Commentaire",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motif de l\'ajustement (optionnel)...'
        }),
        help_text="Raison de l'ajustement de stock"
    )
    
    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        super().__init__(*args, **kwargs)
        
        if self.article:
            # Utiliser la quantité totale des variantes
            total_qte = self.article.get_total_qte_disponible()
            self.fields['nouvelle_quantite'].initial = total_qte
            self.fields['nouvelle_quantite'].help_text = f"Quantité actuelle totale : {total_qte}"
    
    def clean_nouvelle_quantite(self):
        nouvelle_quantite = self.cleaned_data['nouvelle_quantite']
        
        if nouvelle_quantite < 0:
            raise forms.ValidationError("La quantité ne peut pas être négative.")
            
        return nouvelle_quantite 