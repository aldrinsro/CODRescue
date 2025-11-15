# Filtres Réutilisables pour les Pages de Commandes

Ce document explique comment utiliser les filtres réutilisables (date, synchronisation, tri) dans les pages de gestion de commandes.

## Composants

### 1. Template Partial (`_filters.html`)
Fournit le HTML des 3 filtres :
- **Filtre par date** : avec option d'intervalle personnalisé
- **Filtre de synchronisation** : avec option de date personnalisée
- **Filtre de tri** : par date, total, client, ID

### 2. JavaScript Global (`static/js/commande_filters.js`)
Gère la soumission automatique des filtres et l'affichage/masquage des options personnalisées.

### 3. Fonctions Python (`commande/utils.py`)
- `apply_commande_filters(queryset, request)` : Applique tous les filtres au QuerySet
- `get_filter_context(request)` : Retourne un dict avec les valeurs des filtres

## Utilisation

### Étape 1 : Template HTML

Dans votre template, ajoutez un formulaire GET avec le partial :

```django
{% load static %}

<form method="get">
    <!-- Recherche -->
    <div class="flex gap-4">
        <input type="text" name="search" value="{{ search_query|default:'' }}">
        <button type="submit">Rechercher</button>
        {% if search_query or date_filter or request.GET.date_start or sync_filter or order_by %}
        <a href="{% url 'votre:url' %}">Réinitialiser</a>
        {% endif %}
    </div>

    <!-- Filtres réutilisables -->
    {% include 'commande/partials/_filters.html' %}
</form>

<!-- Inclure le JS global -->
<script src="{% static 'js/commande_filters.js' %}"></script>
```

### Étape 2 : Backend (views.py)

Dans votre vue, utilisez les fonctions utilitaires :

```python
from .utils import apply_commande_filters, get_filter_context

def ma_vue(request):
    # QuerySet initial
    commandes = Commande.objects.all()

    # Recherche (optionnel)
    search_query = request.GET.get('search', '')
    if search_query:
        commandes = commandes.filter(...)

    # Appliquer les filtres réutilisables
    commandes = apply_commande_filters(commandes, request)

    # Pagination...

    # Context
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        # ... autres variables ...
    }
    # Ajouter les variables des filtres
    context.update(get_filter_context(request))

    return render(request, 'votre_template.html', context)
```

### Étape 3 : Pagination (optional)

Si vous avez un partial de pagination, ajoutez les paramètres de filtres aux liens :

```django
<a href="?page={{ num }}{% if search_query %}&search={{ search_query }}{% endif %}{% if date_filter %}&date_filter={{ date_filter }}{% endif %}{% if request.GET.date_start %}&date_start={{ request.GET.date_start }}{% endif %}{% if request.GET.date_end %}&date_end={{ request.GET.date_end }}{% endif %}{% if sync_filter %}&sync_filter={{ sync_filter }}{% endif %}{% if custom_sync_date %}&custom_sync_date={{ custom_sync_date }}{% endif %}{% if order_by %}&order_by={{ order_by }}{% endif %}">
    {{ num }}
</a>
```

## Exemples d'utilisation

- ✅ `non_affectees.html` - Implémenté
- ✅ `a_traiter.html` - Implémenté
- ✅ `annulees.html` - Implémenté
- ✅ `suivi_confirmations.html` - Implémenté
- ✅ `suivi_preparations.html` - Implémenté

## Avantages

- 🔄 **Réutilisable** : Un seul code pour toutes les pages
- 🛠️ **Maintenable** : Modifications centralisées
- 🎨 **Cohérent** : Interface identique partout
- ⚡ **Performant** : Filtrage optimisé en base de données
