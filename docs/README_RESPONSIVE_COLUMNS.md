# 📱 README - Responsivité et Masquage de Colonnes

## 🎯 Vue d'ensemble

Ce document décrit la refactorisation complète de la responsivité et l'implémentation du système de masquage de colonnes pour les tableaux dans l'application YZ-CMD. Cette approche standardisée doit être appliquée à toutes les pages contenant des tableaux de données.

## 📋 Table des matières

1. [Architecture Responsive](#architecture-responsive)
2. [Système de Masquage de Colonnes](#système-de-masquage-de-colonnes)
3. [Structure HTML Standardisée](#structure-html-standardisée)
4. [Classes CSS Responsives](#classes-css-responsives)
5. [JavaScript Standardisé](#javascript-standardisé)
6. [Implémentation par Étapes](#implémentation-par-étapes)
7. [Exemples de Code](#exemples-de-code)
8. [Checklist de Validation](#checklist-de-validation)

---

## 🏗️ Architecture Responsive

### 📱 Breakpoints Tailwind Utilisés

```css
/* Mobile First Approach */
- Mobile: < 640px (sm)
- Tablet: 640px - 1024px (sm, md, lg)
- Desktop: > 1024px (lg, xl, 2xl)
```

### 🎯 Stratégie d'Adaptation

1. **Mobile (< 640px)** : Cartes empilées verticalement
2. **Tablet (640px - 1024px)** : Cartes en grille 2 colonnes
3. **Desktop (> 1024px)** : Tableau complet avec colonnes masquables

---

## 🔧 Système de Masquage de Colonnes

### 🎨 Composants Requis

#### 1. Bouton de Contrôle
```html
<!-- Contrôles du tableau -->
<div class="hidden lg:flex justify-end mb-4">
    <button id="columnToggle" onclick="toggleColumnVisibility()" 
            class="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-300"
            title="Sélectionner les colonnes">
        <i class="fas fa-columns mr-2 text-gray-500"></i>
        Sélectionner les colonnes
    </button>
</div>
```

#### 2. Classes CSS pour Colonnes
```html
<!-- En-têtes -->
<th class="column-[nom-colonne] ...">Titre Colonne</th>

<!-- Cellules -->
<td class="column-[nom-colonne] ...">Contenu</td>
```

#### 3. Modal de Sélection
- Interface moderne avec checkboxes
- Boutons Annuler/Appliquer
- Sauvegarde dans localStorage

---

## 📐 Structure HTML Standardisée

### 🎯 Template de Base

```html
<!-- Version mobile/tablette : Cartes -->
<div class="block lg:hidden space-y-3">
    {% for item in items %}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-3 hover:shadow-md transition-shadow duration-200">
        <!-- En-tête de la carte -->
        <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
                <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span class="text-blue-600 font-bold text-xs">{{ item.id }}</span>
                </div>
                <div>
                    <h3 class="font-semibold text-gray-900 text-sm">{{ item.title }}</h3>
                    <p class="text-xs text-gray-500">{{ item.subtitle }}</p>
                </div>
            </div>
            <div class="text-right">
                <div class="text-sm font-bold text-green-600">{{ item.value }}</div>
                <div class="text-xs text-gray-500">{{ item.count }} éléments</div>
            </div>
        </div>
        
        <!-- Informations détaillées -->
        <div class="grid grid-cols-2 gap-2 mb-2 text-xs">
            <div>
                <span class="text-gray-500">Label:</span>
                <div class="font-medium">{{ item.detail1 }}</div>
            </div>
            <div>
                <span class="text-gray-500">Label:</span>
                <div class="font-medium">{{ item.detail2 }}</div>
            </div>
        </div>
        
        <!-- États -->
        <div class="flex flex-wrap gap-1 mb-2">
            <span class="px-1.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                <i class="fas fa-icon mr-1"></i>État
            </span>
        </div>
        
        <!-- Actions -->
        <div class="flex items-center justify-between pt-2 border-t border-gray-200">
            <div class="flex items-center space-x-1">
                <button class="inline-flex items-center px-2 py-1 rounded-md shadow-sm text-white text-xs bg-blue-600">
                    <i class="fas fa-action mr-1"></i>
                    Action
                </button>
            </div>
            <div class="flex items-center space-x-1">
                <a href="#" class="inline-flex items-center justify-center w-7 h-7 rounded-md shadow-sm text-white text-xs bg-blue-600">
                    <i class="fas fa-eye"></i>
                </a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Contrôles du tableau -->
<div class="hidden lg:flex justify-end mb-4">
    <button id="columnToggle" onclick="toggleColumnVisibility()" 
            class="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all duration-300"
            title="Sélectionner les colonnes">
        <i class="fas fa-columns mr-2 text-gray-500"></i>
        Sélectionner les colonnes
    </button>
</div>

<!-- Version desktop : Tableau -->
<div class="hidden lg:block overflow-x-auto rounded-lg shadow-sm border border-gray-200">
    <table class="w-full divide-y divide-gray-200 table-auto">
        <thead style="background-color: var(--primary-color);">
            <tr>
                <th class="column-col1 px-2 py-3 text-left text-xs font-medium text-white uppercase tracking-wider" style="width: 8%;">Colonne 1</th>
                <th class="column-col2 px-2 py-3 text-left text-xs font-medium text-white uppercase tracking-wider" style="width: 10%;">Colonne 2</th>
                <!-- ... autres colonnes ... -->
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
            {% for item in items %}
            <tr class="hover:bg-gray-50">
                <td class="column-col1 px-2 py-3 text-sm font-medium text-gray-900 truncate">
                    {{ item.field1 }}
                </td>
                <td class="column-col2 px-2 py-3 text-sm text-gray-500 truncate">
                    {{ item.field2 }}
                </td>
                <!-- ... autres cellules ... -->
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

---

## 🎨 Classes CSS Responsives

### 📱 Cartes Mobiles
```css
/* Container des cartes */
.space-y-3                    /* Espacement vertical entre cartes */

/* Carte individuelle */
.p-3                          /* Padding compact */
.hover:shadow-md              /* Effet hover */
.transition-shadow            /* Animation fluide */

/* En-tête de carte */
.mb-2                         /* Marge bottom réduite */
.space-x-2                    /* Espacement horizontal */
.w-8.h-8                      /* Icône compacte */
.text-sm                      /* Texte principal */
.text-xs                      /* Texte secondaire */

/* Informations détaillées */
.grid.grid-cols-2            /* Grille 2 colonnes */
.gap-2                        /* Espacement réduit */
.text-xs                      /* Texte petit */

/* États */
.gap-1                        /* Espacement minimal */
.px-1.5.py-0.5               /* Padding compact pour badges */

/* Actions */
.pt-2                         /* Padding top */
.space-x-1                    /* Espacement horizontal minimal */
.w-7.h-7                      /* Boutons compacts */
.text-xs                      /* Texte petit */
```

### 🖥️ Tableau Desktop
```css
/* Container du tableau */
.overflow-x-auto              /* Scroll horizontal si nécessaire */
.rounded-lg                   /* Coins arrondis */
.shadow-sm                    /* Ombre légère */
.border.border-gray-200       /* Bordure */

/* Tableau */
.w-full                       /* Largeur complète */
.divide-y.divide-gray-200     /* Séparateurs entre lignes */
.table-auto                   /* Largeur automatique des colonnes */

/* En-têtes */
.px-2.py-3                    /* Padding compact */
.text-xs                      /* Texte petit */
.font-medium                   /* Poids de police */
.uppercase.tracking-wider     /* Style en-tête */

/* Cellules */
.px-2.py-3                    /* Padding compact */
.text-sm                      /* Taille de texte */
.truncate                     /* Texte tronqué si trop long */
```

---

## ⚡ JavaScript Standardisé

### 🔧 Fonctions Requises

```javascript
// Fonction pour masquer/afficher les colonnes
function toggleColumnVisibility() {
    const button = document.getElementById('columnToggle');
    
    // Créer le modal de sélection des colonnes
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Sélectionner les colonnes</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="space-y-3">
                <!-- Checkboxes pour chaque colonne -->
                <label class="flex items-center">
                    <input type="checkbox" class="column-checkbox" data-column="column-col1" checked>
                    <span class="ml-2 text-sm text-gray-700">Nom Colonne</span>
                </label>
                <!-- ... autres colonnes ... -->
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md">
                    Annuler
                </button>
                <button onclick="applyColumnVisibility(this.closest('.fixed'))" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md">
                    Appliquer
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    loadColumnVisibility();
}

// Charger l'état actuel des colonnes
function loadColumnVisibility() {
    const hiddenColumns = JSON.parse(localStorage.getItem('hiddenColumns') || '[]');
    const checkboxes = document.querySelectorAll('.column-checkbox');
    
    checkboxes.forEach(checkbox => {
        const column = checkbox.dataset.column;
        checkbox.checked = !hiddenColumns.includes(column);
    });
}

// Appliquer la visibilité des colonnes
function applyColumnVisibility(modal) {
    const checkboxes = modal.querySelectorAll('.column-checkbox');
    const hiddenColumns = [];
    
    checkboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            hiddenColumns.push(checkbox.dataset.column);
        }
    });
    
    // Sauvegarder dans localStorage
    localStorage.setItem('hiddenColumns', JSON.stringify(hiddenColumns));
    
    // Appliquer la visibilité
    updateColumnVisibility(hiddenColumns);
    
    // Fermer le modal
    modal.remove();
}

// Mettre à jour la visibilité des colonnes
function updateColumnVisibility(hiddenColumns) {
    // Liste des colonnes disponibles (à adapter selon la page)
    const columns = [
        'column-col1', 'column-col2', 'column-col3',
        // ... autres colonnes
    ];
    
    columns.forEach(column => {
        const elements = document.querySelectorAll(`.${column}`);
        elements.forEach(element => {
            if (hiddenColumns.includes(column)) {
                element.style.display = 'none';
            } else {
                element.style.display = '';
            }
        });
    });
}

// Charger la visibilité des colonnes au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const hiddenColumns = JSON.parse(localStorage.getItem('hiddenColumns') || '[]');
    updateColumnVisibility(hiddenColumns);
});
```

---

## 🚀 Implémentation par Étapes

### 📋 Étape 1 : Préparation
1. **Identifier les colonnes** du tableau existant
2. **Définir les classes CSS** pour chaque colonne (`column-[nom]`)
3. **Préparer la liste** des colonnes dans le JavaScript

### 📋 Étape 2 : Structure HTML
1. **Ajouter les cartes mobiles** avec la structure standardisée
2. **Ajouter le bouton de contrôle** au-dessus du tableau
3. **Ajouter les classes CSS** aux en-têtes et cellules du tableau

### 📋 Étape 3 : JavaScript
1. **Copier les fonctions** JavaScript standardisées
2. **Adapter la liste des colonnes** dans `updateColumnVisibility()`
3. **Tester le fonctionnement** du masquage/afficage

### 📋 Étape 4 : Responsivité
1. **Vérifier l'affichage mobile** (cartes)
2. **Vérifier l'affichage tablette** (cartes en grille)
3. **Vérifier l'affichage desktop** (tableau avec colonnes)

### 📋 Étape 5 : Tests
1. **Tester le masquage** de différentes colonnes
2. **Vérifier la persistance** dans localStorage
3. **Tester la responsivité** sur différents écrans

---

## 📝 Exemples de Code

### 🎯 Cartes Statistiques Responsives
```html
<!-- Statistiques rapides -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 lg:mb-8">
    <div class="group bg-white rounded-xl shadow-lg p-3 sm:p-4 transition-all duration-300 hover:shadow-2xl hover:scale-105 border border-gray-100 h-full flex flex-col">
        <div class="flex items-center justify-between flex-grow">
            <div class="flex items-center flex-grow">
                <div class="p-2 sm:p-3 rounded-full bg-gradient-to-r from-blue-100 to-blue-200 text-blue-600 transition-all duration-300 group-hover:from-blue-500 group-hover:to-blue-600 group-hover:text-white group-hover:scale-110 flex-shrink-0">
                    <i class="fas fa-icon text-lg sm:text-xl"></i>
                </div>
                <div class="ml-2 sm:ml-3 flex-grow">
                    <p class="text-xs font-medium text-gray-600 group-hover:text-gray-700 transition-colors duration-300">Label</p>
                    <p class="text-xl sm:text-2xl font-bold text-gray-900 transition-all duration-300 group-hover:text-blue-600">{{ value }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 🎯 Onglets Responsives
```html
<!-- Onglets de filtrage -->
<div class="mb-4 sm:mb-6">
    <div class="border-b border-gray-200">
        <nav class="-mb-px flex flex-wrap sm:flex-nowrap space-x-2 sm:space-x-8 overflow-x-auto" aria-label="Tabs">
            <a href="#" class="{% if active %}border-blue-500 text-blue-600{% else %}border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300{% endif %} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-xs sm:text-sm transition-colors duration-200">
                <i class="fas fa-icon mr-1 sm:mr-2"></i>
                <span class="hidden sm:inline">Texte Complet</span>
                <span class="sm:hidden">Court</span>
                <span class="ml-1 sm:ml-2 bg-gray-100 text-gray-900 py-0.5 px-1.5 sm:px-2.5 rounded-full text-xs font-medium">{{ count }}</span>
            </a>
        </nav>
    </div>
</div>
```

---

## ✅ Checklist de Validation

### 📱 Responsivité
- [ ] **Mobile (< 640px)** : Cartes empilées verticalement
- [ ] **Tablet (640px - 1024px)** : Cartes en grille 2 colonnes
- [ ] **Desktop (> 1024px)** : Tableau complet visible
- [ ] **Transitions fluides** entre les breakpoints
- [ ] **Texte lisible** sur tous les écrans
- [ ] **Boutons accessibles** sur mobile

### 🔧 Masquage de Colonnes
- [ ] **Bouton visible** uniquement sur desktop
- [ ] **Modal fonctionnel** avec checkboxes
- [ ] **Persistance** dans localStorage
- [ ] **Chargement automatique** des préférences
- [ ] **Classes CSS** correctement appliquées
- [ ] **Toutes les colonnes** peuvent être masquées

### 🎨 Design
- [ ] **Cohérence visuelle** avec le design system
- [ ] **Couleurs** respectées (variables CSS)
- [ ] **Espacements** uniformes
- [ ] **Animations** fluides
- [ ] **États hover** fonctionnels
- [ ] **Accessibilité** respectée

### ⚡ Performance
- [ ] **Chargement rapide** sur mobile
- [ ] **Pas de scroll horizontal** indésirable
- [ ] **JavaScript optimisé** sans erreurs
- [ ] **localStorage** utilisé efficacement
- [ ] **DOM manipulation** minimale

---

## 🔄 Maintenance et Évolutions

### 📋 Mise à Jour des Colonnes
1. **Ajouter la classe CSS** `column-[nouvelle-colonne]`
2. **Mettre à jour la liste** dans `updateColumnVisibility()`
3. **Ajouter la checkbox** dans le modal
4. **Tester le fonctionnement**

### 📋 Ajout de Nouvelles Pages
1. **Suivre la structure** HTML standardisée
2. **Adapter les classes CSS** selon le contenu
3. **Copier le JavaScript** et adapter la liste des colonnes
4. **Tester la responsivité** sur tous les écrans

### 📋 Optimisations Futures
- **Virtualisation** des tableaux pour de grandes quantités de données
- **Filtres avancés** intégrés au système de colonnes
- **Export** des préférences de colonnes
- **Thèmes** adaptatifs selon les préférences utilisateur

---

## 📞 Support et Contact

Pour toute question ou problème d'implémentation :
- **Documentation** : Ce README
- **Exemples** : `liste_prepa.html` comme référence
- **Tests** : Utiliser la checklist de validation

---

**Version** : 1.0  
**Date** : 2024  
**Auteur** : Équipe YZ-CMD  
**Statut** : ✅ Approuvé et Prêt pour Production
