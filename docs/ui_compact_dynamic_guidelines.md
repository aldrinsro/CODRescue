## Guide d'implémentation UI – Compacte, dynamique et uniforme (Superpréparation)

Ce document standardise l’UI/UX à appliquer sur toutes les pages de la zone Superpréparation afin d’obtenir une interface compacte, responsive et homogène, avec sélection dynamique des colonnes.

### 0) Pré-requis globaux
- Variables thème déjà définies dans `composant_generale/Superpreparation/base.html`:
  - `--preparation-primary`, `--preparation-dark`, `--preparation-light`, etc.
- Sidebar colorisée au niveau du template de base (pas dans les pages).
- Script global pour colonnes: `static/js/Superpreparation/global-columns-toggle.js` inclus dans le base.

### 1) Colonne – Sélecteur global (obligatoire)
- Donnez à la table l’id `cmdTable`.
- Ajoutez un bouton dans la barre d’outils:
  ```html
  <button id="columnToggle" onclick="toggleColumnVisibility()" class="...">
    <i class="fas fa-columns ..."></i>Sélectionner les colonnes
  </button>
  ```
- Le script global ouvre un panneau listant les colonnes (d’après le `thead`) et persiste l’état dans `localStorage` par page. Il s’applique automatiquement au chargement.

### 2) Recherche intelligente (smart search) uniforme
- Inclure le script:
  ```html
  <script src="{% static 'js/Superpreparation/Suivi_des_Commandes/suivi-commandes-smart-search.js' %}"></script>
  <script>document.addEventListener('DOMContentLoaded',()=>initSuiviCommandesSearch('TYPE')); </script>
  ```
  - `TYPE`: `confirmées`, `en_preparation`, `retournées`, etc.
- Champs requis dans la page:
  - `#smartSearch`, `#advancedSearch`, `#searchResults` + `#resultCount`.
  - Lignes du tableau avec classe `.commande-row` et attributs `data-*` (ex: `data-id-yz`, `data-num-cmd`, `data-client`, `data-phone`, `data-total`, …).
- Terminologie standardisée:
  - Placeholder principal: “Rechercher par Numéro Commande, client, téléphone…”.
  - Filtres: `Numéro Commande` (ex: 212268), `N° Externe` (ex: YCN-000290).

### 3) Mode compact (densification)
Appliquer la classe `compact-page` au conteneur racine de la page et ce bloc CSS (adapter si déjà présent):
```html
<div class="main-content compact-page" id="mainContent">
  <style>
    .compact-page table { font-size: 12px; }
    .compact-page thead th, .compact-page tbody td { padding: 6px 8px !important; }
    .compact-page .h-10 { height: 2rem !important; }
    .compact-page .text-sm { font-size: 0.75rem !important; }
    /* Optionnel: serrer marges/espaces */
    .compact-page .mb-8 { margin-bottom: 1rem !important; }
    .compact-page .p-6 { padding: .75rem !important; }
  </style>
</div>
```

### 4) Tableau – Responsivité et lisibilité
- Structure du tableau:
  - `id="cmdTable"` obligatoire pour le sélecteur de colonnes global.
  - `thead` sticky: `class="sticky top-0 z-10"` et fond `var(--preparation-primary)`.
  - Wrapper scroll horizontal: `overflow-x-auto`.
  - Tailles minimales recommandées (peuvent varier): `min-w-[800px] lg:min-w-[1000px] xl:min-w-[1200px]`.
  - Police compacte: `text-xs sm:text-sm`.
- En-têtes courts pour tout voir sans troncature:
  - “Numéro”, “N° Ext.”, “Client”, “Tél.”, “Ville Clt”, “Ville & Rég.”, “Date Affect.”, “Total”, “État”, “Prépa”, “Panier”, “Actions”.
- Option: ajouter ellipsis pour stabiliser l’affichage lorsque toutes les colonnes sont visibles:
  ```css
  .compact-page #cmdTable th, .compact-page #cmdTable td {
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: middle;
  }
  ```

### 5) Bouton “Appliquer” aligné au thème
- Utiliser la couleur primaire du thème:
  ```html
  <button style="background-color: var(--preparation-primary);" class="text-white ...">Appliquer</button>
  ```

### 6) Ajustement dynamique du tableau après masquage de colonnes
- Le script global `global-columns-toggle.js`:
  - Nettoie les `width` forcées et repasse `table-layout:auto`.
  - Force `table.style.width='100%'` et recalcul du scroll/ombres.
  - Applique la visibilité d’après `localStorage` au chargement de page.

### 7) Check-list pour porter sur une nouvelle page
- [ ] Donnez `id="cmdTable"` à la table.
- [ ] Ajoutez le bouton “Sélectionner les colonnes” → `toggleColumnVisibility()`.
- [ ] Incluez et initialisez la recherche intelligente + placeholders/labels standard.
- [ ] Appliquez `compact-page` et le bloc CSS compact.
- [ ] `thead` sticky + wrapper `overflow-x-auto` + `min-w` responsives.
- [ ] Renommez les libellés d’en-tête avec les formes abrégées.
- [ ] Assurez-vous que les lignes `.commande-row` exposent les `data-*` utilisés par la recherche.
- [ ] Utilisez `var(--preparation-primary)` pour tous les CTA (cohérence thème).

### 8) Références
- Page modèle (confirmées): `templates/Superpreparation/commande_confirmees.html`.
- Exemple appliqué (liste prépa): `templates/Superpreparation/liste_prepa.html`.
- Sélecteur colonnes global: `static/js/Superpreparation/global-columns-toggle.js`.


