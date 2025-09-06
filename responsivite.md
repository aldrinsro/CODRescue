# 📊 Règles de Responsivité pour Dashboard (Tailwind + JS(que tu vas coder en dur si necessaire +vendord qui dejà des js )

Ce document décrit les bonnes pratiques et conventions pour rendre un **dashboard responsive** et utilisable sur **tous types d’écrans** (mobile → ultra-wide).

---

## 1. Principes Généraux

- Utiliser **Mobile First** : on définit d’abord le style pour les petits écrans, puis on ajoute des breakpoints pour les plus grands.
- Utiliser les **unités relatives** (`%`, `rem`, `em`, `vw`, `vh`, `fr`) plutôt que des pixels fixes.
- Toujours prévoir un `max-w-screen-xl` ou `max-w-[1440px]` pour éviter que les contenus soient trop étirés sur grands écrans.
- Centraliser le contenu avec `mx-auto` sur les écrans larges.

---

## 2. Breakpoints (Tailwind par défaut)

- `sm` → ≥ 640px (mobile large)
- `md` → ≥ 768px (tablette portrait)
- `lg` → ≥ 1024px (tablette paysage / laptop)
- `xl` → ≥ 1280px (desktop standard)
- `2xl` → ≥ 1536px (grand écran / ultra-wide)

👉 Exemple :

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <!-- cartes dashboard -->
</div>
```

---

## 3. Layout du Dashboard

### Mobile (<768px)

- **1 seule colonne** (`grid-cols-1`).
- Sidebar masquée (`hidden`) et remplacée par un menu burger.
- Navigation en `fixed bottom-0` ou `top-0` si nécessaire.

### Tablette (768px–1023px)

- **2 colonnes** max (`md:grid-cols-2`).
- Sidebar visible mais **repliable**.

### Desktop (≥1024px)

- **3 à 4 colonnes** (`lg:grid-cols-3 xl:grid-cols-4`).
- Sidebar fixe (`lg:block`) + Topbar visible.

### Grand écran (≥1536px)

- Contenu centré avec `max-w-screen-2xl mx-auto`.
- Ne pas étirer les cartes/tables sur toute la largeur → utiliser `max-w-[1440px]`.

---

## 4. Composants

### Cartes (Cards)

- Largeur fluide (`w-full`).
- Espacement cohérent (`p-4 sm:p-6`).
- Arrondis et ombrages (`rounded-2xl shadow-md`).

### Tableaux

- Sur mobile → `overflow-x-auto` avec scroll horizontal.
- Colonnes réduites sur petit écran, toutes visibles sur grand écran.

```html
<div class="overflow-x-auto">
  <table class="min-w-full text-sm">
    ...
  </table>
</div>
```

### Graphiques

- Largeur en `%` (`w-full`) ou `flex-auto`.
- Hauteur définie en unités relatives (`h-64 sm:h-80 lg:h-96`).
- Légendes adaptées : masquées (`hidden sm:block`) sur mobile, visibles sur desktop.

---

## 5. Typographie & Icônes

- Police en `rem` (`text-sm md:text-base lg:text-lg`).
- Ligne de texte max : 65–75 caractères.
- Icônes minimum `w-6 h-6` (mobile), `w-8 h-8` (desktop).

---

## 6. Espacement & Hiérarchie

- Échelle d’espacement cohérente : `p-2`, `p-4`, `p-6`.
- Sur mobile → espacement vertical augmenté.
- Sur desktop → densité plus élevée mais lisible.

---

## 7. Intégration JavaScript (vendor.js)

### Sidebar Responsive

- Ajouter un bouton burger sur mobile (`sm:hidden`).
- En JS, toggle la sidebar :

```js
document.querySelector('#menu-toggle').addEventListener('click', () => {
  document.querySelector('#sidebar').classList.toggle('hidden');
});
```

### Dropdowns et Filtres

- Gérer l’ouverture/fermeture via `classList.toggle('hidden')`.
- Fermer automatiquement en cliquant à l’extérieur.

### Tableaux / Graphes

- Activer le scroll horizontal si nécessaire.
- Ajouter des listeners pour redimensionnement (`window.resize`) afin d’ajuster dynamiquement certains graphes.

---

## 8. Performance & Accessibilité

- Charger les graphiques en lazy-loading si lourds.
- Toujours prévoir un **Dark Mode** (`dark:` classes Tailwind).
- Vérifier les contrastes (`bg-gray-900 text-white` en dark).
- Utiliser `aria-expanded` et `role="navigation"` pour accessibilité.

---

## ✅ Résumé

- **Mobile-first avec Tailwind breakpoints.**
- **Grid fluide (1 → 4 colonnes).**
- **Sidebar repliable avec JS.**
- **Tables et graphes scrollables.**
- **Max-width pour ultra-wide.**
- **Accessibilité et dark mode inclus.**
