# 📦 Composants Templates Communs - YZ-RESCUE

Ce dossier contient des composants templates réutilisables dans toute l'application.

---

## 📋 Composants disponibles

### 1. 🔍 Système de Filtres Avancés

**Fichier:** `advanced-filters.html`

Panneau de filtres avancés configurable pour filtrer dynamiquement les tableaux.

**Utilisation:**

```django
{% include 'common/advanced-filters.html' with filter_config=filter_config %}
```

**Documentation complète:** `common/README_ADVANCED_FILTERS.md`

**Exemple d'utilisation:** `common/EXAMPLE_USAGE.md`

---

### 2. 📅 Filtres de Dates

**Fichier:** `filters.html`

Filtres de dates avec expressions naturelles (aujourd'hui, cette semaine, etc.)

**Utilisation:**

```django
{% include 'common/filters.html' %}
```

**Documentation:** `common/README_FILTERS.md`

---

### 3. 📦 Filtres de Commandes (NOUVEAU)

**Fichier:** `commande-filters.html`

Système de filtres complet pour les pages de gestion de commandes avec recherche intelligente et filtres avancés.

**Utilisation:**

```django
{% include 'common/commande-filters.html' %}
<script src="{% static 'js/common/commande-filters.js' %}"></script>
```

**Vue Python:**

```python
from common.filter_utils import apply_commande_filters
commandes = apply_commande_filters(commandes, request)
```

**Documentation complète:** `common/README_COMMANDE_FILTERS.md`

**Caractéristiques:**
- ✅ Recherche globale intelligente
- ✅ Filtres par client, téléphone, email
- ✅ Filtres de localisation (ville, région, adresse)
- ✅ Filtres de dates (commande, confirmation, préparation, livraison)
- ✅ Filtres de montant (min/max)
- ✅ Filtres par état et opérateur
- ✅ Filtrage côté serveur pour les performances
- ✅ URL persistante

---

## 🚀 Quick Start

### Installation

```django
{% load static %}

{# Dans le head #}
<link rel="stylesheet" href="{% static 'css/common/filter-system.css' %}">

{# Avant la fermeture du body #}
<script src="{% static 'js/common/filter-system.js' %}"></script>
```

### Configuration dans la vue

```python
# views.py
def ma_vue(request):
    filter_config = {
        'title': 'Filtres avancés',
        'button_text': 'Filtres',
        'filters': [
            {
                'id': 'filterClient',
                'label': 'Client',
                'type': 'text',
                'data_field': 'client'
            },
            # ... autres filtres
        ]
    }

    return render(request, 'template.html', {
        'filter_config': filter_config
    })
```

### Utilisation dans le template

```django
{# Inclure le composant #}
{% include 'common/advanced-filters.html' with filter_config=filter_config %}

{# Tableau avec data-attributes #}
<tbody>
    <tr class="filterable-row" data-client="John Doe" data-total="500">
        <td>John Doe</td>
        <td>500 DH</td>
    </tr>
</tbody>
```

---

## 📁 Structure des fichiers

```
CODRescue/
├── common/
│   ├── README_ADVANCED_FILTERS.md    # Documentation système de filtres
│   ├── EXAMPLE_USAGE.md              # Exemples d'utilisation
│   └── README_FILTERS.md             # Documentation filtres de dates
│
├── templates/common/
│   ├── README.md                     # Ce fichier
│   ├── advanced-filters.html         # Composant filtres avancés
│   └── filters.html                  # Composant filtres de dates
│
└── static/
    ├── js/common/
    │   └── filter-system.js          # Logique filtres avancés
    └── css/common/
        └── filter-system.css         # Styles filtres avancés
```

---

## 🎯 Cas d'usage

### Filtrer une liste de commandes

```python
filter_config = {
    'filters': [
        {'id': 'filterIdYz', 'label': 'N° Commande', 'type': 'text', 'data_field': 'idYz'},
        {'id': 'filterClient', 'label': 'Client', 'type': 'text', 'data_field': 'client'},
        {'id': 'filterTotalMin', 'label': 'Total Min', 'type': 'number', 'data_field': 'total', 'filter_type': 'min'},
    ]
}
```

### Filtrer avec statuts

```python
filter_config = {
    'filters': [
        {
            'id': 'filterStatut',
            'label': 'Statut',
            'type': 'select',
            'data_field': 'statut',
            'options': [
                {'value': 'En cours', 'label': 'En cours'},
                {'value': 'Terminé', 'label': 'Terminé'},
            ]
        },
    ]
}
```

---

## 🔧 API

### Fonctions JavaScript globales

```javascript
// Basculer les filtres
toggleAdvancedFilters();

// Appliquer les filtres
applyAdvancedFilters();

// Effacer les filtres
clearAdvancedFilters();

// Initialiser manuellement
initFilterSystem({ rowSelector: '.ma-classe' });
```

---

## 📖 Documentation détaillée

- **Filtres avancés:** `common/README_ADVANCED_FILTERS.md`
- **Exemple complet:** `common/EXAMPLE_USAGE.md`
- **Filtres de dates:** `common/README_FILTERS.md`

---

## 🆘 Support

Pour toute question :

1. Consultez la documentation appropriée
2. Vérifiez les exemples fournis
3. Vérifiez la console du navigateur pour les erreurs
4. Contactez l'équipe technique

---

**Version:** 1.0.0
**Dernière mise à jour:** 19 Novembre 2025
**Auteur:** YZ-Rescue Team
