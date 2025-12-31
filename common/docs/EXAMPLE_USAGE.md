# 📘 Exemple d'utilisation - Page Commandes Préparées

Ce document montre comment adapter votre page `commandes_preparees.html` pour utiliser le nouveau système de filtres global.

---

## Étape 1: Modifier la vue (views.py)

```python
# Superpreparation/views.py

def commandes_preparees(request):
    # ... votre logique existante ...

    # Configuration des filtres avancés
    filter_config = {
        'title': 'Filtres avancés',
        'button_text': 'Filtres',
        'button_class': 'bg-blue-600 hover:bg-blue-700',
        'filters': [
            {
                'id': 'filterIdYz',
                'label': 'N° Commande',
                'type': 'text',
                'placeholder': 'Ex: 212268',
                'data_field': 'idYz'
            },
            {
                'id': 'filterNumCmd',
                'label': 'N° Externe',
                'type': 'text',
                'placeholder': 'Ex: YCN-000290',
                'data_field': 'numCmd'
            },
            {
                'id': 'filterClient',
                'label': 'Client',
                'type': 'text',
                'placeholder': 'Nom ou prénom...',
                'data_field': 'client'
            },
            {
                'id': 'filterPhone',
                'label': 'Téléphone',
                'type': 'text',
                'placeholder': 'N°...',
                'data_field': 'phone'
            },
            {
                'id': 'filterEmail',
                'label': 'Email',
                'type': 'email',
                'placeholder': 'Email...',
                'data_field': 'email'
            },
            {
                'id': 'filterAdresse',
                'label': 'Adresse',
                'type': 'text',
                'placeholder': 'Adresse client...',
                'data_field': 'adresse'
            },
            {
                'id': 'filterVilleClient',
                'label': 'Ville Client',
                'type': 'text',
                'placeholder': 'Ville client...',
                'data_field': 'villeClient'
            },
            {
                'id': 'filterVilleRegion',
                'label': 'Ville & Région',
                'type': 'text',
                'placeholder': 'Ville/région...',
                'data_field': 'villeRegion'
            },
            {
                'id': 'filterDatePreparation',
                'label': 'Date Préparation',
                'type': 'date',
                'data_field': 'datePreparation'
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
                'id': 'filterOperateur',
                'label': 'Opérateur',
                'type': 'text',
                'placeholder': 'Opérateur...',
                'data_field': 'operateur'
            },
        ]
    }

    context = {
        'commandes_preparees': commandes_preparees,
        'stats': stats,
        'filter_config': filter_config,  # Ajouter ceci
        # ... vos autres variables de contexte
    }

    return render(request, 'Superpreparation/commandes_preparees.html', context)
```

---

## Étape 2: Modifier le template HTML

### 2.1 Ajouter les fichiers CSS et JS

```django
{% block extra_css %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'css/common/filter-system.css' %}">

{# Vos styles existants... #}
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="{% static 'js/common/filter-system.js' %}"></script>

{# Vos scripts existants... #}
{% endblock %}
```

### 2.2 Remplacer l'ancien système de filtres

**❌ AVANT (lignes 738-850):**

```html
<!-- Ancien système de filtres -->
<div class="relative ml-auto">
    <div class="mb-3">
        <p class="text-gray-700 text-sm">
            Recherche intelligente et filtres avancés...
        </p>
    </div>
    <div class="flex items-center space-x-2">
        <!-- Barre de recherche -->
        <div class="relative">
            <input type="text" id="smartSearch" ...>
        </div>

        <!-- Bouton filtres ancien -->
        <button onclick="toggleAdvancedSearch()" ...>
            Filtres
        </button>
    </div>

    <!-- Panneau de filtres ancien -->
    <div id="advancedSearch" class="hidden ...">
        <!-- Beaucoup de code répétitif... -->
    </div>
</div>
```

**✅ APRÈS:**

```django
<!-- Nouveau système de filtres global -->
<div class="flex items-center space-x-2 flex-wrap gap-2">
    <!-- Votre barre de recherche existante (garder tel quel) -->
    <div class="relative">
        <input type="text" id="smartSearch"
               placeholder="Rechercher par N° Commande, client, téléphone..."
               class="block px-4 py-2 pr-10 border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm w-64 h-10"
               autocomplete="off">
        <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
            <i class="fas fa-search text-gray-400"></i>
        </div>
    </div>

    <!-- Bouton effacer recherche -->
    <button onclick="clearSmartSearch()"
            class="inline-flex items-center px-3 py-2 bg-gray-500 hover:bg-gray-600 text-white text-sm font-medium rounded transition-colors h-10">
        <i class="fas fa-times"></i>
    </button>

    <!-- Nouveau composant de filtres global -->
    {% include 'common/advanced-filters.html' with filter_config=filter_config %}

    <!-- Bouton colonnes (optionnel) -->
    <button id="columnToggle" onclick="toggleColumnVisibility()"
            class="inline-flex items-center px-3 py-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm font-medium rounded transition-colors h-10">
        <i class="fas fa-columns mr-2 text-gray-500"></i>
        Sélectionner les colonnes
    </button>
</div>

<!-- Indicateur de résultats (sera affiché par le système) -->
<div id="filterResults" class="hidden"></div>
```

### 2.3 Mettre à jour les lignes du tableau

**❌ AVANT:**

```html
<tr class="hover:bg-gray-50 transition-colors border-b border-gray-200 commande-row">
```

**✅ APRÈS:**

```django
<tr class="filterable-row hover:bg-gray-50 transition-colors border-b border-gray-200 commande-row"
    data-id-yz="{{ commande.id_yz }}"
    data-num-cmd="{{ commande.num_cmd|default:'' }}"
    data-client="{{ commande.client.nom }} {{ commande.client.prenom }}"
    data-phone="{{ commande.client.numero_tel|default:'' }}"
    data-email="{{ commande.client.email|default:'' }}"
    data-ville-client="{{ commande.ville_init|default:'' }}"
    data-ville-region="{% if commande.ville %}{{ commande.ville.nom }} {{ commande.ville.region.nom }}{% endif %}"
    data-adresse="{% if commande.client.adresse %}{{ commande.client.adresse }}{% endif %}"
    data-date-preparation="{% for etat in commande.etats.all %}{% if etat.enum_etat.libelle == 'Préparée' and not etat.date_fin %}{{ etat.date_debut|date:'d/m/Y' }}{% endif %}{% endfor %}"
    data-total="{{ commande.total_cmd }}"
    data-operateur="{% for etat in commande.etats.all %}{% if etat.enum_etat.libelle == 'Préparée' and not etat.date_fin %}{{ etat.operateur.prenom }} {{ etat.operateur.nom }}{% endif %}{% endfor %}">

    {# Vos colonnes existantes... #}
</tr>
```

### 2.4 Supprimer les anciennes fonctions JavaScript

**❌ SUPPRIMER:**

```javascript
// Supprimer toutes les fonctions liées aux filtres (lignes 1395-1480 environ)
function toggleAdvancedSearch() { ... }
function applyFilters() { ... }
function clearFilters() { ... }
function performAdvancedFiltering(filters) { ... }
// etc.
```

**✅ GARDER:**

```javascript
// Garder uniquement la recherche intelligente si vous voulez la garder
function handleSmartSearch(e) { ... }
function performSmartSearch(query) { ... }
function clearSmartSearch() { ... }
```

### 2.5 Initialiser le nouveau système

À la fin de votre fichier, ajouter :

```javascript
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le nouveau système de filtres
    initFilterSystem({
        rowSelector: '.filterable-row'
    });

    console.log('✅ Système de filtres global initialisé');
});
</script>
```

---

## Étape 3: Tester

1. Rechargez la page
2. Cliquez sur le bouton "Filtres"
3. Saisissez des valeurs dans les champs
4. Cliquez sur "Appliquer"
5. Vérifiez que le tableau se filtre correctement
6. Vérifiez que le badge affiche le nombre de filtres actifs
7. Testez le bouton "Effacer"

---

## Avantages de la migration

✅ **Code réduit** : ~300 lignes supprimées
✅ **Maintenabilité** : Un seul endroit pour les corrections
✅ **Cohérence** : Même UX sur toutes les pages
✅ **Accessibilité** : Support ARIA et clavier
✅ **Performance** : Code optimisé
✅ **Évolutivité** : Ajout facile de nouveaux filtres

---

## Résolution de problèmes

### Les filtres ne fonctionnent pas

1. Vérifiez que les fichiers CSS et JS sont bien chargés
2. Vérifiez que les lignes ont la classe `filterable-row`
3. Vérifiez que les `data-*` attributes correspondent aux `data_field` de la config
4. Ouvrez la console et cherchez les erreurs

### Les data-attributes ne correspondent pas

Utilisez le format camelCase dans la config et kebab-case dans le HTML :

```python
# Config
'data_field': 'villeRegion'
```

```html
<!-- HTML -->
data-ville-region="Casablanca"
```

Le système convertit automatiquement.

---

## Prochaines étapes

1. ✅ Migrer `commandes_preparees.html`
2. Migrer d'autres pages similaires:
   - `commandes_confirmees.html`
   - `commandes_a_imprimer.html`
   - `commandes_en_preparation.html`
   - etc.

3. Personnaliser selon vos besoins

---

**Besoin d'aide ?** Consultez `README_ADVANCED_FILTERS.md` pour la documentation complète.
