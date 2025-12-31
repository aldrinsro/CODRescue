# 🔍 Système de Filtres Globaux pour les Commandes - YZ-RESCUE

Documentation complète du système de filtres réutilisable pour les commandes.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation](#installation)
3. [Utilisation de base](#utilisation-de-base)
4. [Configuration avancée](#configuration-avancée)
5. [Filtres disponibles](#filtres-disponibles)
6. [API Python](#api-python)
7. [API JavaScript](#api-javascript)
8. [Exemples](#exemples)
9. [Migration depuis smart-search-toolbar](#migration)

---

## 🎯 Vue d'ensemble

Le système de filtres globaux pour les commandes fournit :

- ✅ **Recherche intelligente** en temps réel
- ✅ **Filtres avancés** configurables (client, téléphone, ville, dates, montant, etc.)
- ✅ **Filtrage côté serveur** pour les grandes quantités de données
- ✅ **Filtrage côté client** pour une réactivité instantanée
- ✅ **Composants réutilisables** dans toute l'application
- ✅ **URL persistante** - les filtres sont conservés dans l'URL

---

## 📦 Installation

### Étape 1 : Inclure le template

Dans votre template Django, incluez le composant de filtres :

```django
{% load static %}

<!-- Dans le contenu de votre page -->
{% include 'common/commande-filters.html' %}
```

### Étape 2 : Inclure le JavaScript

Dans votre template, avant la balise `</body>` :

```django
<!-- JavaScript pour les filtres de commandes -->
<script src="{% static 'js/common/commande-filters.js' %}"></script>
```

### Étape 3 : Modifier votre vue

Dans votre vue Django (`views.py`) :

```python
from common.filter_utils import apply_commande_filters

def ma_vue_commandes(request):
    # Récupérer toutes les commandes
    commandes = Commande.objects.all()

    # Appliquer les filtres
    commandes = apply_commande_filters(commandes, request)

    # Reste de votre logique...

    return render(request, 'mon_template.html', {
        'commandes': commandes,
        # ...
    })
```

---

## 🚀 Utilisation de base

### Template minimal

```django
{% extends 'base.html' %}
{% load static %}

{% block content %}
    <!-- Filtres de commandes -->
    {% include 'common/commande-filters.html' %}

    <!-- Votre tableau de commandes -->
    <table id="cmdTable">
        <tbody>
            {% for commande in commandes %}
            <tr>
                <td>{{ commande.id_yz }}</td>
                <td>{{ commande.client.nom }}</td>
                <!-- ... -->
            </tr>
            {% endfor %}
        </tbody>
    </table>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/common/commande-filters.js' %}"></script>
{% endblock %}
```

### Vue minimale

```python
from django.shortcuts import render
from common.filter_utils import apply_commande_filters
from commande.models import Commande

def liste_commandes(request):
    commandes = Commande.objects.all()
    commandes = apply_commande_filters(commandes, request)

    return render(request, 'commandes/liste.html', {
        'commandes': commandes
    })
```

---

## ⚙️ Configuration avancée

### Personnaliser les filtres affichés

Vous pouvez configurer quels filtres afficher :

```django
{% with filter_config=my_filter_config %}
    {% include 'common/commande-filters.html' %}
{% endwith %}
```

Dans votre vue :

```python
def ma_vue(request):
    filter_config = {
        'show_search': True,           # Afficher la barre de recherche
        'show_info_base': True,        # Afficher les filtres de base
        'show_localisation': True,     # Afficher les filtres de localisation
        'show_dates': True,            # Afficher les filtres de dates
        'show_montant': True,          # Afficher les filtres de montant
        'search_placeholder': 'Rechercher...',
        'title': 'Recherche Avancée',
        'description': 'Filtrez vos commandes facilement.',
    }

    return render(request, 'template.html', {
        'filter_config': filter_config
    })
```

### Configuration minimale (recherche uniquement)

```python
filter_config = {
    'show_info_base': False,
    'show_localisation': False,
    'show_dates': False,
    'show_montant': False,
}
```

---

## 📊 Filtres disponibles

### 1. Recherche globale

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `search` | Recherche dans N° commande, client, téléphone, email | `?search=John` |

### 2. Informations de base

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `filter_id_yz` | N° Commande YZ | `?filter_id_yz=212268` |
| `filter_num_cmd` | N° Externe | `?filter_num_cmd=YCN-000290` |
| `filter_client` | Nom du client | `?filter_client=Dupont` |
| `filter_phone` | Téléphone | `?filter_phone=0612345678` |
| `filter_email` | Email | `?filter_email=client@mail.com` |

### 3. Localisation

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `filter_ville_client` | Ville du client | `?filter_ville_client=Casablanca` |
| `filter_ville_region` | Ville & Région | `?filter_ville_region=Rabat` |
| `filter_adresse` | Adresse | `?filter_adresse=rue` |

### 4. Dates

| Paramètre | Description | Format | Exemple |
|-----------|-------------|--------|---------|
| `filter_date_commande` | Date de commande | YYYY-MM-DD | `?filter_date_commande=2025-01-15` |
| `filter_date_confirmation` | Date de confirmation | YYYY-MM-DD | `?filter_date_confirmation=2025-01-16` |
| `filter_date_affectation` | Date d'affectation | YYYY-MM-DD | `?filter_date_affectation=2025-01-17` |
| `filter_date_preparation` | Date de préparation | YYYY-MM-DD | `?filter_date_preparation=2025-01-18` |
| `filter_date_livraison` | Date de livraison | YYYY-MM-DD | `?filter_date_livraison=2025-01-20` |

### 5. Montant & État

| Paramètre | Description | Type | Exemple |
|-----------|-------------|------|---------|
| `filter_total_min` | Montant minimum | Float | `?filter_total_min=100` |
| `filter_total_max` | Montant maximum | Float | `?filter_total_max=1000` |
| `filter_etat` | État de la commande | String | `?filter_etat=Confirmée` |
| `filter_operateur` | Nom de l'opérateur | String | `?filter_operateur=Ahmed` |

---

## 🐍 API Python

### Fonction principale

```python
apply_commande_filters(queryset: QuerySet, request) -> QuerySet
```

Applique tous les filtres disponibles à un QuerySet de commandes.

**Paramètres :**
- `queryset` : QuerySet de Commande à filtrer
- `request` : Objet HttpRequest contenant les paramètres GET

**Retour :**
- QuerySet filtré

**Exemple :**

```python
from common.filter_utils import apply_commande_filters
from commande.models import Commande

def ma_vue(request):
    # Récupérer toutes les commandes confirmées
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).distinct()

    # Appliquer les filtres utilisateur
    commandes = apply_commande_filters(commandes, request)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(commandes, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'template.html', {'page_obj': page_obj})
```

---

## 🟨 API JavaScript

### Fonctions disponibles

#### `initCommandeFilters(options)`

Initialise le système de filtres.

```javascript
initCommandeFilters({
    tableSelector: '#cmdTable tbody tr',
    searchDelay: 300,
    debug: false
});
```

#### `clearSmartSearch()`

Efface la recherche intelligente.

```javascript
clearSmartSearch();
```

#### `toggleAdvancedSearch()`

Bascule l'affichage des filtres avancés.

```javascript
toggleAdvancedSearch();
```

#### `applyFilters()`

Applique les filtres et recharge la page avec les paramètres.

```javascript
applyFilters();
```

#### `clearFilters()`

Efface tous les filtres et recharge la page.

```javascript
clearFilters();
```

#### `countActiveFilters()`

Retourne le nombre de filtres actifs.

```javascript
const count = countActiveFilters();
console.log(`${count} filtre(s) actif(s)`);
```

---

## 💡 Exemples

### Exemple 1 : Page de commandes confirmées

**Template** (`commandes_confirmees.html`) :

```django
{% extends 'base.html' %}
{% load static %}

{% block content %}
    <h1>Commandes Confirmées</h1>

    <!-- Filtres -->
    {% include 'common/commande-filters.html' %}

    <!-- Tableau -->
    <table id="cmdTable" class="w-full">
        <thead>
            <tr>
                <th>N° Commande</th>
                <th>Client</th>
                <th>Ville</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for commande in page_obj %}
            <tr>
                <td>{{ commande.id_yz }}</td>
                <td>{{ commande.client.nom_complet }}</td>
                <td>{{ commande.ville.nom }}</td>
                <td>{{ commande.total_cmd }} DH</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- Pagination -->
    {% include 'pagination.html' %}
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/common/commande-filters.js' %}"></script>
{% endblock %}
```

**Vue** (`views.py`) :

```python
from django.shortcuts import render
from django.core.paginator import Paginator
from common.filter_utils import apply_commande_filters
from commande.models import Commande

def commandes_confirmees(request):
    # Récupérer les commandes confirmées
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').distinct()

    # Appliquer les filtres
    commandes = apply_commande_filters(commandes, request)

    # Pagination
    paginator = Paginator(commandes, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'commandes_confirmees.html', {
        'page_obj': page_obj
    })
```

### Exemple 2 : Filtres personnalisés

**Vue avec configuration personnalisée** :

```python
def commandes_preparation(request):
    # Configuration des filtres
    filter_config = {
        'show_info_base': True,
        'show_localisation': False,  # Masquer les filtres de localisation
        'show_dates': True,
        'show_montant': False,       # Masquer les filtres de montant
        'search_placeholder': 'Rechercher une commande en préparation...',
        'description': 'Gérez vos commandes en préparation.',
    }

    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct()

    commandes = apply_commande_filters(commandes, request)

    return render(request, 'preparation.html', {
        'commandes': commandes,
        'filter_config': filter_config
    })
```

---

## 🔄 Migration depuis smart-search-toolbar

Si vous utilisez actuellement `smart-search-toolbar.html`, voici comment migrer :

### Avant

```django
{% include 'Superpreparation/includes/smart-search-toolbar.html' %}
<script src="{% static 'js/Superpreparation/Suivi_des_Commandes/suivi-commandes-smart-search.js' %}"></script>
```

### Après

```django
{% include 'common/commande-filters.html' %}
<script src="{% static 'js/common/commande-filters.js' %}"></script>
```

**Dans la vue**, ajouter :

```python
from common.filter_utils import apply_commande_filters

commandes = apply_commande_filters(commandes, request)
```

### Avantages de la migration

1. ✅ **Réutilisable** dans toute l'application
2. ✅ **Filtrage côté serveur** pour de meilleures performances
3. ✅ **Code centralisé** et maintenu globalement
4. ✅ **Configuration flexible** selon les besoins

---

## 🛠️ Dépannage

### Les filtres ne fonctionnent pas

1. Vérifiez que le JavaScript est bien inclus :
   ```django
   <script src="{% static 'js/common/commande-filters.js' %}"></script>
   ```

2. Vérifiez que la fonction est appliquée dans la vue :
   ```python
   commandes = apply_commande_filters(commandes, request)
   ```

3. Ouvrez la console du navigateur pour voir les erreurs

### Les filtres ne persistent pas dans l'URL

Assurez-vous d'utiliser `applyFilters()` et non un simple filtrage côté client.

### Performances lentes

- Ajoutez des index sur les champs fréquemment filtrés
- Utilisez `select_related()` et `prefetch_related()`
- Limitez le nombre de résultats avec la pagination

---

## 📚 Voir aussi

- [README.md](../templates/common/README.md) - Documentation des composants communs
- [README_FILTERS.md](README_FILTERS.md) - Documentation des filtres de dates
- [README_ADVANCED_FILTERS.md](README_ADVANCED_FILTERS.md) - Documentation des filtres avancés

---

## 🆘 Support

Pour toute question ou problème :

1. Consultez cette documentation
2. Vérifiez les exemples fournis
3. Vérifiez la console du navigateur pour les erreurs
4. Contactez l'équipe technique YZ-Rescue

---

**Version :** 1.0.0
**Dernière mise à jour :** 20 Novembre 2025
**Auteur :** YZ-Rescue Team
