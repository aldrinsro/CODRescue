## Contrat d'implémentation – Page Commandes Confirmées (à répliquer)

Objectif: servir de référence pour appliquer les mêmes règles (UI/UX, responsivité, terminologie, actions) aux autres pages de suivi/preparation.

### 1) Layout & Responsivité
- [x] Conteneur principal: `max-w-screen-2xl xl:max-w-[1440px] mx-auto px-3 sm:px-4 lg:px-6`.
- [x] Grille des stats: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`.
- [x] Barre d’outils/recherche enveloppée par un conteneur scrollable horizontal: `overflow-x-auto` (avec marges compensées sur mobile).
- [x] Tableau: wrapper `overflow-x-auto`; `thead` sticky (`sticky top-0 z-10`).
- [x] Largeurs minimales du tableau: `min-w-[1000px] lg:min-w-[1200px] xl:min-w-[1400px]`.
- [x] Taille de texte du tableau: `text-xs sm:text-sm`.
- [x] Ombres directionnelles lors du scroll horizontal (UX): box-shadow inset sur le conteneur.

### 2) Sidebar & Thème
- [x] Couleur unifiée via `var(--preparation-primary)` dans `composant_generale/Superpreparation/base.html`.
- [x] Texte sidebar en blanc; état actif avec fond blanc translucide; séparateurs harmonisés.
- [x] Adaptation dynamique du tableau à l’état `sidebar-open`/`sidebar-collapsed` (écouteurs toggle, transitionend, MutationObserver, resize debouncé).

### 3) Colonnes – Visibilité “admin-like”
- [x] Ciblage CSS par `#cmdTable` avec `nth-child` pour masquer/afficher selon breakpoints:
  - Mobile: masquer (3) N° Externe, (5) Téléphone, (6) Ville & Région, (8) Date Confirmation, (9) Opérateur Conf., (10) État Préparation.
  - `md` ≥768px: afficher 3 et 5.
  - `lg` ≥1024px: afficher 6.
  - `xl` ≥1280px: afficher 8, 9, 10.

### 4) Boutons d’actions
- [x] Bouton “Sélectionner les colonnes” positionné dans la barre d’actions, juste après “Imprimer QR articles”, `onclick="toggleColumnVisibility()"`.
- [x] Compteur de sélection visible `#selectionCountBadge` qui s’affiche si ≥1 ligne sélectionnée.

### 5) Pagination & Contrôles
- [x] Bouton “Appliquer” (plage personnalisée) stylé avec la couleur thème: `bg-[var(--preparation-primary)]` + `border-[var(--preparation-primary)]`.
- [x] Persistance “Éléments par page” via `localStorage` (clé `yz.itemsPerPage`).

### 6) Recherche intelligente & Filtres avancés
- [x] Inclure `static/js/Superpreparation/Suivi_des_Commandes/suivi-commandes-smart-search.js`.
- [x] Placeholder principal: “Rechercher par Numéro Commande, client, téléphone…”.
- [x] Filtres – renommage:
  - `ID YZ` → `Numéro Commande` (ex: 212268)
  - `N° Externe` (ex: YCN-000290)
- [x] Boutons de la toolbar: `Effacer` → `clearSmartSearch()`, `Filtres` → `toggleAdvancedSearch()`.
- [x] Initialisation page: `initSuiviCommandesSearch('confirmées')` (ou type adapté à la page).

### 7) Modales & Détails
- [x] Modale “Informations générales”: label `Numéro Commande` au lieu de `ID YZ`; `N° Externe` conservé.

### 8) Accessibilité & UX
- [x] Raccourcis: Ctrl+F focus recherche; Échap effacer recherche; Entrée applique filtres (quand le panneau est ouvert).
- [x] Header de page compact au scroll (réduction du padding vertical).

### 9) Intégration / Points d’attention pour autres pages
- [ ] Donner à la table l’id `cmdTable` pour appliquer les règles CSS admin-like.
- [ ] Vérifier présence des éléments requis par la recherche (`#smartSearch`, `#advancedSearch`, `#searchResults`, `#resultCount`, `.commande-row` avec `data-*`).
- [ ] Déplacer tout style global (sidebar/couleurs) vers un template de base commun plutôt que les pages spécifiques.

### 10) Check-list rapide à répliquer
- [ ] Conteneur max-width + paddings responsive
- [ ] Toolbar scrollable
- [ ] Table: sticky head, overflow-x, min-widths, text-xs/sm
- [ ] CSS colonnes par breakpoints (id table requis)
- [ ] Bouton “Sélectionner les colonnes” après “Imprimer QR articles”
- [ ] Couleur bouton “Appliquer” = couleur thème
- [ ] Recherche intelligente incluse + renommages labels/placeholder
- [ ] Modale: “Numéro Commande”
- [ ] Sidebar couleur = entête tableau (base template)


