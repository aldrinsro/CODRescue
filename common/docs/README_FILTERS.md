# Système de Filtrage Réutilisable

Ce module `common` fournit un système de filtrage complet et réutilisable pour toute l'application Django.

## 📁 Structure

```
common/
├── filter_utils.py          # Fonctions Python génériques de filtrage
├── date_utils.py            # Fonctions de parsing de dates
templates/common/
└── filters.html             # Template HTML réutilisable
static/js/
└── commande_filters.js      # JavaScript pour la soumission automatique
```

## 🎯 Composants

### 1. Python - `common/filter_utils.py`

Fonctions génériques pour filtrer n'importe quel QuerySet Django :

```python
from common.filter_utils import (
    apply_date_filter,      # Filtre par date
    apply_sync_filter,      # Filtre par synchronisation
    apply_order_filter,     # Filtre de tri
    apply_all_filters,      # Applique tous les filtres
    get_filter_context      # Retourne le context pour le template
)
```

### 2. Template - `templates/common/filters.html`

Partial HTML avec les 3 filtres (date, sync, tri) :

```django
{% include 'common/filters.html' %}
```

### 3. JavaScript - `static/js/commande_filters.js`

Gère la soumission automatique et l'affichage/masquage des options personnalisées.

## 🚀 Utilisation Rapide

### Dans n'importe quel module

#### 1. Template (HTML)

```django
{% load static %}

<form method="get">
    <!-- Votre recherche -->
    <input type="text" name="search" value="{{ search_query }}">
    <button type="submit">Rechercher</button>

    <!-- Filtres réutilisables -->
    {% include 'common/filters.html' %}
</form>

<!-- JavaScript -->
<script src="{% static 'js/commande_filters.js' %}"></script>
```

#### 2. Vue (Python)

```python
from common.filter_utils import apply_all_filters, get_filter_context

def ma_vue(request):
    # QuerySet initial
    items = MonModele.objects.all()

    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(...)

    # Appliquer les filtres réutilisables
    items = apply_all_filters(items, request)

    # Pagination...
    page_obj = paginator.get_page(page_number)

    # Context
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    context.update(get_filter_context(request))

    return render(request, 'mon_template.html', context)
```

## 📚 Documentation Détaillée

### `apply_all_filters(queryset, request, **kwargs)`

Applique automatiquement les 3 filtres (date, sync, tri).

**Paramètres optionnels** :
- `date_field` : Nom du champ de date (défaut: `'date_creation'`)
- `sync_date_field` : Nom du champ de date de sync (défaut: `'last_sync_date'`)
- `origin_field` : Nom du champ d'origine (défaut: `'origine'`)
- `allowed_order_fields` : Liste des champs autorisés pour le tri

**Exemple** :
```python
# Utilisation simple
items = apply_all_filters(MonModele.objects.all(), request)

# Avec champs personnalisés
items = apply_all_filters(
    MonModele.objects.all(),
    request,
    date_field='created_at',
    sync_date_field='synced_at',
    allowed_order_fields=['name', '-name', 'price', '-price']
)
```

### Filtres individuels

Si vous avez besoin de plus de contrôle, utilisez les filtres individuellement :

```python
from common.filter_utils import (
    apply_date_filter,
    apply_sync_filter,
    apply_order_filter
)

queryset = MonModele.objects.all()
queryset = apply_date_filter(queryset, request, field='created_at')
queryset = apply_sync_filter(queryset, request)
queryset = apply_order_filter(queryset, request, allowed_fields=['name', '-name'])
```

## 🔧 Personnalisation

### Adapter les options de tri

Par défaut, le template propose :
- Date de création
- Total (pour commandes)
- Client A-Z
- N° ID

Pour personnaliser, créez votre propre template ou remplacez la section `<!-- Filtre Ordre/Tri -->` :

```django
<!-- Mon filtre personnalisé -->
<select name="order_by">
    <option value="">Par défaut</option>
    <option value="-created_at">Plus récent</option>
    <option value="name">Nom A-Z</option>
    <option value="-price">Prix décroissant</option>
</select>
```

### Désactiver un filtre

Pour n'utiliser que certains filtres :

```python
from common.filter_utils import apply_date_filter, apply_order_filter

queryset = apply_date_filter(queryset, request)
queryset = apply_order_filter(queryset, request)
# Pas de filtre de sync
```

## 🎨 Intégration dans d'autres modules

### Exemple : Module Client

```python
# client/views.py
from common.filter_utils import apply_all_filters, get_filter_context

def liste_clients(request):
    clients = Client.objects.all()

    # Filtre de recherche spécifique
    search = request.GET.get('search', '')
    if search:
        clients = clients.filter(nom__icontains=search)

    # Filtres communs (date d'inscription, tri)
    clients = apply_all_filters(
        clients,
        request,
        date_field='date_inscription',
        allowed_order_fields=['nom', '-nom', 'email', '-email']
    )

    context = {'clients': clients}
    context.update(get_filter_context(request))

    return render(request, 'client/liste.html', context)
```

```django
<!-- client/liste.html -->
<form method="get">
    <input type="text" name="search" placeholder="Rechercher un client...">
    {% include 'common/filters.html' %}
    <button type="submit">Filtrer</button>
</form>
```

## ✅ Modules utilisant ce système

- ✅ **commande** : non_affectees, a_traiter, annulees, suivi_confirmations, suivi_preparations
- 🔜 **client** : À implémenter
- 🔜 **article** : À implémenter

## 🤝 Contribution

Pour ajouter de nouveaux filtres communs :
1. Ajoutez la fonction dans `common/filter_utils.py`
2. Mettez à jour le template `templates/common/filters.html`
3. Ajoutez la logique JavaScript si nécessaire dans `commande_filters.js`
4. Documentez l'utilisation ici

## 📝 Notes

- Les filtres sont **cumulatifs** : date + sync + tri
- La soumission est **automatique** quand vous changez un filtre
- Les valeurs sont **préservées** dans l'URL et la pagination
- Le système est **sans AJAX** pour plus de simplicité et compatibilité
