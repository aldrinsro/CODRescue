# 🔄 Guide de Migration - Système de Filtres Global

Guide rapide pour migrer vos pages existantes vers le nouveau système de filtres global.

---

## ✅ Checklist de migration

- [ ] Inclure les fichiers CSS et JS
- [ ] Créer la configuration des filtres dans la vue
- [ ] Inclure le composant template
- [ ] Ajouter la classe `filterable-row` sur les lignes
- [ ] Ajouter les `data-*` attributes sur les lignes
- [ ] Supprimer l'ancien code de filtres
- [ ] Tester le fonctionnement
- [ ] Vérifier l'accessibilité

---

## 🚀 Migration en 5 minutes

### Étape 1: Inclure les fichiers (30 secondes)

```django
{% block extra_css %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'css/common/filter-system.css' %}">
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="{% static 'js/common/filter-system.js' %}"></script>
{% endblock %}
```

### Étape 2: Configurer dans la vue (2 minutes)

```python
# Dans votre views.py
filter_config = {
    'title': 'Filtres avancés',
    'filters': [
        {'id': 'filterIdYz', 'label': 'N° Commande', 'type': 'text', 'data_field': 'idYz'},
        {'id': 'filterClient', 'label': 'Client', 'type': 'text', 'data_field': 'client'},
        # Ajoutez vos autres filtres...
    ]
}

context['filter_config'] = filter_config
```

### Étape 3: Inclure le composant (30 secondes)

```django
{# Remplacer votre ancien panneau de filtres par: #}
{% include 'common/advanced-filters.html' with filter_config=filter_config %}
```

### Étape 4: Mettre à jour les lignes (1 minute)

```django
<tr class="filterable-row"
    data-id-yz="{{ obj.id }}"
    data-client="{{ obj.client.nom }}"
    data-total="{{ obj.total }}">
```

### Étape 5: Nettoyer l'ancien code (1 minute)

Supprimez les anciennes fonctions JavaScript : `toggleAdvancedSearch()`, `applyFilters()`, etc.

---

## 📊 Tableau de correspondance

### Types de filtres

| Ancien code | Nouveau type | filter_type |
|-------------|--------------|-------------|
| `<input type="text">` | `'text'` | `'text'` |
| `<input type="number">` (min) | `'number'` | `'min'` |
| `<input type="number">` (max) | `'number'` | `'max'` |
| `<input type="date">` | `'date'` | `'date'` |
| `<select>` | `'select'` | `'text'` |

### Noms de champs

| camelCase (config) | kebab-case (HTML) |
|--------------------|-------------------|
| `idYz` | `data-id-yz` |
| `villeRegion` | `data-ville-region` |
| `datePreparation` | `data-date-preparation` |
| `totalCmd` | `data-total-cmd` |

---

## 🔍 Exemples de migration

### Exemple 1: Filtre simple

**Avant:**
```html
<input type="text" id="filterClient" placeholder="Client...">
<script>
function applyFilters() {
    const client = document.getElementById('filterClient').value;
    // 50 lignes de code...
}
</script>
```

**Après:**
```python
# views.py
filter_config = {
    'filters': [
        {'id': 'filterClient', 'label': 'Client', 'type': 'text', 'data_field': 'client'}
    ]
}
```

```django
{% include 'common/advanced-filters.html' with filter_config=filter_config %}
<tr class="filterable-row" data-client="{{ client.nom }}">
```

### Exemple 2: Filtre numérique (min/max)

**Avant:**
```html
<input type="number" id="filterTotalMin">
<input type="number" id="filterTotalMax">
<script>
function checkRange(value, min, max) {
    // Logique complexe...
}
</script>
```

**Après:**
```python
filter_config = {
    'filters': [
        {'id': 'filterTotalMin', 'label': 'Total Min', 'type': 'number', 'data_field': 'total', 'filter_type': 'min'},
        {'id': 'filterTotalMax', 'label': 'Total Max', 'type': 'number', 'data_field': 'total', 'filter_type': 'max'},
    ]
}
```

```django
<tr class="filterable-row" data-total="{{ commande.total }}">
```

### Exemple 3: Filtre de date

**Avant:**
```html
<input type="date" id="filterDate">
<script>
function compareDates(date1, date2) {
    // Conversion et comparaison...
}
</script>
```

**Après:**
```python
filter_config = {
    'filters': [
        {'id': 'filterDate', 'label': 'Date', 'type': 'date', 'data_field': 'datePreparation'}
    ]
}
```

```django
<tr class="filterable-row" data-date-preparation="{{ date|date:'d/m/Y' }}">
```

### Exemple 4: Select/Dropdown

**Avant:**
```html
<select id="filterStatut">
    <option value="">Tous</option>
    <option value="En cours">En cours</option>
    <option value="Terminé">Terminé</option>
</select>
```

**Après:**
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
        }
    ]
}
```

---

## 🐛 Problèmes courants et solutions

### Problème 1: Les filtres ne fonctionnent pas

**Symptôme:** Rien ne se passe quand on clique sur "Appliquer"

**Solutions:**
- ✅ Vérifiez que le JS est bien chargé (console: `globalFilterSystem`)
- ✅ Vérifiez que les lignes ont la classe `filterable-row`
- ✅ Vérifiez les `data-*` attributes dans le HTML
- ✅ Vérifiez que les noms correspondent (camelCase → kebab-case)

### Problème 2: Certains filtres ne marchent pas

**Symptôme:** Certains champs filtrent, d'autres non

**Solutions:**
- ✅ Vérifiez le `data_field` dans la config
- ✅ Vérifiez le `data-*` attribute sur la ligne
- ✅ Pour les nombres, utilisez `filter_type: 'min'` ou `'max'`
- ✅ Pour les dates, format `dd/mm/yyyy` ou `yyyy-mm-dd`

### Problème 3: Le badge ne s'affiche pas

**Symptôme:** Pas de compteur de filtres actifs

**Solutions:**
- ✅ Vérifiez que l'élément `#filterBadge` existe
- ✅ Vérifiez que vous utilisez bien le nouveau template

### Problème 4: Erreurs de console

**Symptôme:** Erreurs JavaScript dans la console

**Solutions:**
- ✅ Supprimez les anciennes fonctions (toggleAdvancedSearch, applyFilters, etc.)
- ✅ Ne gardez pas deux systèmes de filtres en même temps
- ✅ Vérifiez qu'il n'y a pas de conflits d'IDs

---

## 📈 Bénéfices après migration

| Avant | Après |
|-------|-------|
| ~300 lignes de code par page | ~30 lignes |
| Code dupliqué | Code réutilisable |
| Difficile à maintenir | Maintenance centralisée |
| Pas d'accessibilité | ARIA complet |
| Pas de tests | Testé une fois pour toutes |
| Bugs différents par page | Bugs corrigés globalement |

---

## 🎯 Pages à migrer en priorité

### Haute priorité
- [ ] `commandes_preparees.html`
- [ ] `commandes_confirmees.html`
- [ ] `commandes_a_imprimer.html`
- [ ] `commandes_en_preparation.html`

### Moyenne priorité
- [ ] `livraisons_en_cours.html`
- [ ] `livraisons_retournees.html`
- [ ] `tickets_sav.html`

### Basse priorité
- [ ] Pages avec peu de filtres
- [ ] Pages peu utilisées

---

## 🧪 Tests après migration

### Checklist de tests

- [ ] Ouverture/fermeture du panneau (clic et ESC)
- [ ] Filtrage par chaque champ individuellement
- [ ] Filtrage avec plusieurs champs combinés
- [ ] Validation des nombres (min > max)
- [ ] Validation des dates
- [ ] Badge de compteur
- [ ] Bouton "Effacer"
- [ ] Responsive mobile
- [ ] Navigation au clavier
- [ ] Lecteur d'écran (si nécessaire)

### Tests de régression

- [ ] La pagination fonctionne toujours
- [ ] Les autres boutons fonctionnent
- [ ] L'export fonctionne
- [ ] Les actions en masse fonctionnent
- [ ] Pas d'erreurs dans la console

---

## 📞 Besoin d'aide ?

1. **Documentation complète:** `common/README_ADVANCED_FILTERS.md`
2. **Exemple détaillé:** `common/EXAMPLE_USAGE.md`
3. **README templates:** `templates/common/README.md`

---

## 🎓 Formation

**Durée:** 15 minutes

1. Lire ce guide (5 min)
2. Migrer une page simple (5 min)
3. Tester (5 min)

**Ressources:**
- Documentation complète
- Exemples de code
- Support équipe technique

---

**Bonne migration! 🚀**

---

**Version:** 1.0.0
**Dernière mise à jour:** 19 Novembre 2025
**Auteur:** YZ-Rescue Team
