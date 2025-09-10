## Pagination et Recherche intelligentes (Contrat de données)

Ce document définit le contrat de données (DOM et API) pour réutiliser la pagination et la recherche intelligentes dans d’autres pages.

### Concepts
- **Modes d’affichage**:
  - Cartes: liste d’éléments sous forme de cartes.
  - Tableau: lignes d’un `<table>`.
- **Modules**:
  - Recherche: `smart-search.js` → expose `window.smartSearchEtiquettes` et insère l’UI `#smartSearchContainer` sous `#stats-cards`.
  - Pagination Cartes: `smart-pagination.js` → expose `window.smartPaginationEtiquettes`.
  - Pagination Tableau (Dashboard): script inline de `dashboard.html` → expose `window.smartPaginationTable`.

### Hooks DOM requis

1) En-tête et statistiques
- `#stats-cards`: conteneur des cartes statistiques (sert d’ancre pour placer la recherche).
- `#smartSearchContainer`: conteneur de l’UI de recherche (créé par `smart-search.js`).

2) Mode Cartes
- Chaque carte: `.etiquette-card`
- Champs internes pour l’indexation/recherche:
  - `.etiquette-reference`
  - `.etiquette-template`
  - `.etiquette-commande`
  - `.etiquette-date`
  - `.etiquette-statut` (texte, ou classes: `confirmee`→ready, `terminee`→printed, `en-preparation`→draft)

3) Mode Tableau
- Chaque ligne: `.etiquette-row`
- Cellules/classes internes:
  - `.column-reference`
  - `.column-template`
  - `.column-commande`
  - `.column-date`
  - `.etiquette-statut` (peut être un badge; les couleurs `bg-green-100`→ready, `bg-blue-100`→printed, `bg-yellow-100`→draft sont supportées)
- Id du tableau: `#etiquettes-table` (sert à insérer les contrôles de pagination en dessous).

4) Sélection multiple (optionnel)
- Checkboxes: `.etiquette-checkbox`
- Barre d’outils: `#bulk-actions-toolbar` (activée/affichée via JS)

### API publique

1) Recherche (`window.smartSearchEtiquettes`)
- `init()` → initialise collecte + UI
- `search()` → exécute la recherche courante
- `reset()` → réinitialise la recherche/filters
- `getStats()` → stats (totaux, requête en cours, filtres actifs)
- `getFilteredItems()` → liste filtrée (objets internes)

Intégration pagination:
- Si `window.smartPaginationEtiquettes` (cartes) existe: `filterItems(filtered)` est appelé
- Sinon, fallback: masque/affiche directement les éléments
- Sur tableau (dashboard), la recherche agit aussi en filtrage visuel lorsque la pagination tableau expose un équivalent (non requis par défaut)

2) Pagination Cartes (`window.smartPaginationEtiquettes`)
- Méthodes attendues:
  - `init()`
  - `filterItems(filtered)` → applique le jeu filtré provenant de la recherche
  - `resetPagination()`

3) Pagination Tableau (`window.smartPaginationTable`)
- Méthodes exposées (dashboard):
  - `init()` / `showPage(page)`
  - `filterRows(filteredRows)`
  - `resetPagination()`
  - `getFilteredRows()` → lignes courantes
  - `getStats()` → `{ currentPage, totalPages, itemsPerPage, totalItems, filteredItems, startIndex, endIndex }`
  - `setItemsPerPage(n)`

### Flux d’initialisation recommandé
1. La page rend le HTML avec:
   - `#stats-cards`
   - Soit des `.etiquette-card`, soit des `.etiquette-row` (avec classes internes ci‑dessus)
2. Scripts inclus (ordre):
   - `smart-pagination.js` (si mode cartes)
   - `smart-search.js`
   - Script pagination tableau (si mode tableau), déjà dans `dashboard.html`
3. Au `DOMContentLoaded`:
   - La recherche crée `#smartSearchContainer` et l’insère sous `#stats-cards`
   - La pagination initialise et rend ses contrôles

### Contrat de données (objets internes de recherche)
Chaque élément indexé produit un objet:
```
{
  element: HTMLElement,
  index: number,
  reference: string,
  template: string,
  statut: 'ready'|'printed'|'draft'|string,
  statutDisplay: string,
  date: string,
  commande: string,
  articles: string,
  client: string,
  numeroCommande: string,          // ex: ycn-000187
  referencesArticles: string[],     // refs détectées dans le texte des articles
  searchText: string                // concat normalisé pour la recherche full-text
}
```

Notes d’extraction:
- Le statut réel est déduit par classes (cartes/table), sinon par texte.
- `numeroCommande` est extrait de `commande` par regex `([a-z]+-\d+)`.

### Exigences d’accessibilité/UX
- Les contrôles de pagination doivent être insérés sous le tableau ou le conteneur des éléments, rester stables, et accessibles au clavier.
- Les modules ne doivent pas re-déplacer les blocs si déjà à la bonne position (idempotents).

### Bonnes pratiques d’intégration
- Conserver les ids/classes du contrat ci‑dessus pour éviter tout couplage fragile.
- Éviter d’avoir plusieurs scripts qui déplacent les mêmes blocs simultanément (préférer un seul responsable par page).
- En cas de nouveau design, fournir des alias de classes côté DOM pour rester compatible (`.column-reference` et `.etiquette-reference`, etc.).

### Dépannage rapide
- La recherche n’affiche rien: vérifier présence de `.etiquette-card` ou `.etiquette-row` et des sous-classes requises.
- La pagination tableau n’apparaît pas: vérifier `#etiquettes-table` et l’insertion des contrôles sous le bon nœud.
- Ordre recherche/statistiques instable: vérifier présence de `#stats-cards` et ne pas dupliquer les scripts de repositionnement.


