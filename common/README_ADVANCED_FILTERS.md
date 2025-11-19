# 🔍 Système de Filtres Avancés Global - YZ-RESCUE

Système de filtrage réutilisable et configurable pour toutes les pages de l'application.

## 📦 Fichiers

```
common/
└── README_ADVANCED_FILTERS.md         # Cette documentation

templates/common/
└── advanced-filters.html              # Template HTML réutilisable

static/
├── js/common/filter-system.js         # Logique JavaScript
└── css/common/filter-system.css       # Styles CSS
```

---

## 🚀 Installation rapide

### 1️⃣ Inclure les fichiers dans votre template

```django
{% load static %}

{# Dans le head #}
<link rel="stylesheet" href="{% static 'css/common/filter-system.css' %}">

{# Avant la fermeture du body #}
<script src="{% static 'js/common/filter-system.js' %}"></script>
```

### 2️⃣ Définir la configuration des filtres dans votre vue

```python
# views.py
def ma_vue(request):
    filter_config = {
        'title': 'Filtres avancés',
        'button_text': 'Filtres',
        'button_class': 'bg-blue-600 hover:bg-blue-700',  # Optionnel
        'filters': [
            {
                'id': 'filterIdYz',
                'label': 'N° Commande',
                'type': 'text',
                'placeholder': 'Ex: 212268',
                'data_field': 'idYz'
            },
            {
                'id': 'filterClient',
                'label': 'Client',
                'type': 'text',
                'placeholder': 'Nom ou prénom...',
                'data_field': 'client'
            },
            {
                'id': 'filterTotalMin',
                'label': 'Total Min',
                'type': 'number',
                'placeholder': '0',
                'data_field': 'total',
                'filter_type': 'min'
            },
            {
                'id': 'filterTotalMax',
                'label': 'Total Max',
                'type': 'number',
                'placeholder': '1000',
                'data_field': 'total',
                'filter_type': 'max'
            },
            {
                'id': 'filterDate',
                'label': 'Date',
                'type': 'date',
                'data_field': 'datePreparation'
            },
        ]
    }

    return render(request, 'ma_page.html', {
        'filter_config': filter_config,
        # ... autres données
    })
```

### 3️⃣ Inclure le composant dans votre template

```django
{# Dans votre toolbar de recherche #}
<div class="flex items-center space-x-2">
    {# Autres boutons... #}

    {% include 'common/advanced-filters.html' with filter_config=filter_config %}
</div>
```

### 4️⃣ Ajouter les data-attributes sur vos lignes de tableau

```django
<tbody>
    {% for commande in commandes %}
    <tr class="filterable-row"
        data-id-yz="{{ commande.id_yz }}"
        data-client="{{ commande.client.nom }} {{ commande.client.prenom }}"
        data-total="{{ commande.total_cmd }}"
        data-date-preparation="{{ commande.date_preparation|date:'d/m/Y' }}">

        <td>{{ commande.id_yz }}</td>
        <td>{{ commande.client.nom }}</td>
        {# ... autres colonnes #}
    </tr>
    {% endfor %}
</tbody>
```

### 5️⃣ Initialiser le système (optionnel)

Le système s'initialise automatiquement si les éléments sont présents.
Sinon, vous pouvez l'initialiser manuellement :

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation manuelle (optionnel)
    const filterSystem = initFilterSystem({
        rowSelector: '.filterable-row',  // Sélecteur des lignes
        panelId: 'advancedFilters',      // ID du panneau
        resultsId: 'filterResults',      // ID de l'indicateur de résultats
        badgeId: 'filterBadge'           // ID du badge
    });
});
</script>
```

---

## 📋 Configuration des filtres

### Types de filtres disponibles

| Type | Description | Exemple |
|------|-------------|---------|
| `text` | Recherche textuelle insensible à la casse | Nom, prénom, ville |
| `email` | Recherche d'email | Email client |
| `number` | Comparaison exacte de nombre | Montant exact |
| `min` | Filtre minimum (>=) | Total minimum |
| `max` | Filtre maximum (<=) | Total maximum |
| `date` | Comparaison de dates | Date de commande |
| `select` | Liste déroulante | État, statut |

### Structure d'un filtre

```python
{
    'id': 'filterUnique',          # ID unique de l'input
    'label': 'Label affiché',      # Label visible par l'utilisateur
    'type': 'text',                # Type de filtre (voir tableau ci-dessus)
    'placeholder': 'Texte...',     # Placeholder (optionnel)
    'data_field': 'nomDuChamp',    # Nom du data-attribute sur les lignes
    'filter_type': 'text',         # Type de filtrage (text, min, max, date)

    # Pour les selects uniquement:
    'options': [
        {'value': 'val1', 'label': 'Option 1'},
        {'value': 'val2', 'label': 'Option 2'},
    ]
}
```

---

## 🎯 Exemples d'utilisation

### Exemple 1: Page de commandes

```python
# views.py
filter_config = {
    'title': 'Filtrer les commandes',
    'button_text': 'Filtres',
    'filters': [
        {'id': 'filterIdYz', 'label': 'N° Commande', 'type': 'text', 'data_field': 'idYz'},
        {'id': 'filterClient', 'label': 'Client', 'type': 'text', 'data_field': 'client'},
        {'id': 'filterPhone', 'label': 'Téléphone', 'type': 'text', 'data_field': 'phone'},
        {'id': 'filterVille', 'label': 'Ville', 'type': 'text', 'data_field': 'ville'},
        {'id': 'filterDate', 'label': 'Date', 'type': 'date', 'data_field': 'dateCommande'},
        {'id': 'filterTotalMin', 'label': 'Total Min', 'type': 'number', 'data_field': 'total', 'filter_type': 'min'},
        {'id': 'filterTotalMax', 'label': 'Total Max', 'type': 'number', 'data_field': 'total', 'filter_type': 'max'},
    ]
}
```

```django
{# template.html #}
<tr class="filterable-row"
    data-id-yz="212268"
    data-client="John Doe"
    data-phone="0612345678"
    data-ville="Casablanca"
    data-date-commande="19/11/2025"
    data-total="500">
    ...
</tr>
```

### Exemple 2: Page de livraisons avec statut

```python
# views.py
filter_config = {
    'title': 'Filtrer les livraisons',
    'filters': [
        {'id': 'filterIdLivraison', 'label': 'N° Livraison', 'type': 'text', 'data_field': 'idLivraison'},
        {'id': 'filterLivreur', 'label': 'Livreur', 'type': 'text', 'data_field': 'livreur'},
        {
            'id': 'filterStatut',
            'label': 'Statut',
            'type': 'select',
            'data_field': 'statut',
            'options': [
                {'value': 'En cours', 'label': 'En cours'},
                {'value': 'Livrée', 'label': 'Livrée'},
                {'value': 'Retournée', 'label': 'Retournée'},
            ]
        },
    ]
}
```

### Exemple 3: Page SAV avec dates multiples

```python
filter_config = {
    'title': 'Filtrer les tickets SAV',
    'filters': [
        {'id': 'filterTicket', 'label': 'N° Ticket', 'type': 'text', 'data_field': 'ticket'},
        {'id': 'filterClient', 'label': 'Client', 'type': 'text', 'data_field': 'client'},
        {'id': 'filterDateCreation', 'label': 'Date création', 'type': 'date', 'data_field': 'dateCreation'},
        {'id': 'filterDateResolution', 'label': 'Date résolution', 'type': 'date', 'data_field': 'dateResolution'},
        {
            'id': 'filterPriorite',
            'label': 'Priorité',
            'type': 'select',
            'data_field': 'priorite',
            'options': [
                {'value': 'Haute', 'label': 'Haute'},
                {'value': 'Moyenne', 'label': 'Moyenne'},
                {'value': 'Basse', 'label': 'Basse'},
            ]
        },
    ]
}
```

---

## 🔧 API JavaScript

### Méthodes disponibles

```javascript
// Initialiser le système
const filterSystem = initFilterSystem(config);

// Basculer l'affichage du panneau
toggleAdvancedFilters();

// Appliquer les filtres
applyAdvancedFilters();

// Effacer tous les filtres
clearAdvancedFilters();

// Accéder à l'instance globale
console.log(globalFilterSystem);

// Obtenir le nombre de lignes visibles
const count = globalFilterSystem.getVisibleRowsCount();

// Obtenir les filtres actifs
const filters = globalFilterSystem.getActiveFilters();
```

### Événements personnalisés

Vous pouvez écouter les événements du système de filtres :

```javascript
// Après application des filtres
document.addEventListener('filtersApplied', function(e) {
    console.log('Filtres appliqués:', e.detail.filters);
    console.log('Résultats:', e.detail.matchCount);
});

// Après effacement des filtres
document.addEventListener('filtersCleared', function(e) {
    console.log('Filtres effacés');
});
```

---

## 🎨 Personnalisation

### Personnaliser les couleurs

Modifiez les variables CSS dans `filter-system.css` :

```css
:root {
    --filter-primary: #3b82f6;           /* Couleur principale */
    --filter-primary-hover: #2563eb;     /* Couleur au survol */
    --filter-success: #10b981;           /* Couleur succès */
    --filter-danger: #ef4444;            /* Couleur erreur */
    --filter-gray: #6b7280;              /* Couleur grise */
}
```

### Personnaliser le bouton

```python
filter_config = {
    'button_text': 'Mes Filtres',
    'button_class': 'bg-purple-600 hover:bg-purple-700',  # Classes Tailwind personnalisées
    # ...
}
```

### Ajouter des styles personnalisés

```css
/* Dans votre fichier CSS */
#advancedFilters {
    border-radius: 1rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

#advancedFiltersBtn {
    font-weight: 600;
    letter-spacing: 0.05em;
}
```

---

## ⌨️ Raccourcis clavier

| Touche | Action |
|--------|--------|
| `Escape` | Fermer le panneau de filtres |
| `Enter` | Appliquer les filtres (quand le panneau est ouvert) |

---

## ♿ Accessibilité

Le système est entièrement accessible :

- ✅ Navigation au clavier
- ✅ Support des lecteurs d'écran (ARIA)
- ✅ Contraste élevé
- ✅ Focus visible
- ✅ Animations réduites pour `prefers-reduced-motion`

---

## 📱 Responsive

Le système s'adapte automatiquement à toutes les tailles d'écran :

- **Mobile** : Panneau pleine largeur
- **Tablet** : Panneau 500px
- **Desktop** : Panneau 600px+

---

## 🐛 Débogage

### Console de debug

```javascript
// Afficher l'état du système
console.log(globalFilterSystem);

// Voir les filtres actifs
console.log(globalFilterSystem.getActiveFilters());

// Voir le nombre de lignes visibles
console.log(globalFilterSystem.getVisibleRowsCount());
```

### Problèmes courants

| Problème | Solution |
|----------|----------|
| Les filtres ne fonctionnent pas | Vérifiez que les lignes ont la classe `filterable-row` et les `data-*` attributes |
| Le panneau ne s'ouvre pas | Vérifiez que le JavaScript est bien chargé |
| Les data-attributes ne correspondent pas | Utilisez `data-field` dans la config pour mapper correctement |
| Conversion de dates échoue | Utilisez le format `dd/mm/yyyy` ou `yyyy-mm-dd` |

---

## 🔄 Migration depuis l'ancien système

Si vous avez déjà un système de filtres, voici comment migrer :

### Avant (ancien système)

```html
<div id="advancedSearch" class="hidden ...">
    <input type="text" id="filterIdYz" ...>
    <button onclick="applyFilters()">Appliquer</button>
</div>

<script>
function applyFilters() {
    // Logique custom...
}
</script>
```

### Après (nouveau système)

```django
{% include 'common/advanced-filters.html' with filter_config=filter_config %}
```

```python
# Dans la vue
filter_config = {
    'filters': [
        {'id': 'filterIdYz', 'label': 'N° Commande', 'type': 'text', 'data_field': 'idYz'},
    ]
}
```

---

## 🤝 Contribuer

Pour ajouter de nouvelles fonctionnalités au système de filtres :

1. Modifier `filter-system.js` pour la logique
2. Modifier `filter-system.css` pour les styles
3. Modifier `advanced-filters.html` pour le template
4. Mettre à jour cette documentation

---

## 📄 Licence

© 2025 YZ-Rescue Team - Usage interne uniquement

---

## 🆘 Support

Pour toute question ou problème :

1. Consultez cette documentation
2. Vérifiez les exemples fournis
3. Contactez l'équipe technique

---

**Version:** 1.0.0
**Dernière mise à jour:** 19 Novembre 2025
**Auteur:** YZ-Rescue Team
