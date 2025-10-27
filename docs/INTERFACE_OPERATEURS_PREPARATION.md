# 📦 Interface Opérateurs de Préparation - Documentation Complète

## 📋 Vue d'ensemble

L'interface des **Opérateurs de Préparation** est dédiée aux opérateurs qui préparent physiquement les commandes avant leur expédition. Cette interface permet de gérer l'ensemble du processus de préparation, de la réception des commandes confirmées jusqu'à leur emballage final.

---

## 🎯 Accès et Navigation

### URL Principale
**Base** : `/operateur-preparation/`

### Authentification Requise
- **Type d'opérateur** : PREPARATION
- **Permissions** : Opérateur de préparation actif
- **Redirection** : Page de connexion si non authentifié

---

## 🏠 Page d'Accueil - Dashboard

### URL
`/operateur-preparation/` ou `/operateur-preparation/home/`

### Statistiques Affichées

#### 1. **Commandes à préparer**
- État : "En préparation"
- Affectées à l'opérateur connecté
- États actifs uniquement (date_fin = NULL)

#### 2. **Commandes préparées aujourd'hui**
- Par l'opérateur connecté
- État : "Préparée"
- Filtrées par date du jour

#### 3. **Commandes en cours de préparation**
- État actuel : "En préparation"
- Affectées à l'opérateur

#### 4. **Performance hebdomadaire**
- Nombre de commandes préparées cette semaine
- Calcul depuis le lundi de la semaine en cours

### KPIs Visuels
```
┌─────────────────────────────────────────┐
│  📦 Total Affectées       │  💰 Valeur  │
│      15 commandes         │  45,000 DH  │
├─────────────────────────────────────────┤
│  ⚠️  Urgentes            │  ✅ Complètes│
│      3 commandes          │      12     │
└─────────────────────────────────────────┘
```

---

## 📋 Liste des Préparations

### URL
`/operateur-preparation/liste-prepa/`

### Vue : `liste_prepa(request)`

### Onglets de Filtrage

#### 1️⃣ **Toutes les commandes** (par défaut)
- **Filtre** : `?filter=all`
- **États inclus** : 
  - À imprimer
  - En préparation
  - Collectée
  - Emballée
- **Affectation** : Commandes affectées à l'opérateur
- **Badge** : Nombre total de commandes

#### 2️⃣ **Affectées par supervision**
- **Filtre** : `?filter=affectees_supervision`
- **Description** : Commandes affectées directement par un superviseur
- **Vérification** : Recherche d'opérations de type "affectation"
- **Badge** : Nombre de commandes affectées par supervision
- **Icône** : 🛡️ User-shield

#### 3️⃣ **Renvoyées par logistique**
- **Filtre** : `?filter=renvoyees_logistique`
- **Description** : Commandes retournées par les opérateurs logistiques
- **Historique** : Vérification des états "En cours de livraison" ou "Livrée Partiellement"
- **Badge** : Nombre de retours logistique
- **Icône** : 🚚 Truck
- **Couleur** : Rouge (alerte)

---

## 🔍 Fonctionnalités de Recherche

### Barre de Recherche
**Champs recherchés** :
- ID YZ (identifiant interne)
- Numéro externe de commande
- Nom du client
- Prénom du client
- Numéro de téléphone
- Ville du client
- Adresse

### Filtrage Avancé
```javascript
// Exemple de recherche
GET /operateur-preparation/liste-prepa/?filter=all&search=0612345678
```

### Sélection des Colonnes
Bouton "Colonnes" permettant de personnaliser l'affichage du tableau :
- Toggle de visibilité par colonne
- Sauvegarde dans localStorage
- Interface responsive

---

## 📊 Tableau des Commandes

### Colonnes Affichées

| Colonne | Description | Type |
|---------|-------------|------|
| **ID YZ** | Identifiant interne unique | Numérique |
| **N° Externe** | Numéro de commande externe | Texte |
| **Client** | Nom et prénom du client | Texte + Email |
| **Téléphone** | Numéro de téléphone | Lien cliquable |
| **Ville Client** | Ville d'origine du client | Texte |
| **Ville & Région** | Ville de livraison + région | Texte double |
| **Date Affectation** | Date d'affectation à l'opérateur | Date/Heure |
| **Total** | Montant total de la commande | Devise (DH) |
| **État** | État général de la commande | Badge coloré |
| **État Préparation** | État spécifique préparation | Badge |
| **Panier** | Nombre d'articles | Badge numérique |
| **Actions** | Boutons d'action | Boutons |

### États de Préparation

#### 🟡 À imprimer
```css
background: #FEF3C7; /* Jaune clair */
color: #92400E;      /* Marron foncé */
icon: fa-print
```

#### 🔵 En préparation
```css
background: #DBEAFE; /* Bleu clair */
color: #1E40AF;      /* Bleu foncé */
icon: fa-box-open
```

#### 🟢 Collectée
```css
background: #D1FAE5; /* Vert clair */
color: #065F46;      /* Vert foncé */
icon: fa-check-circle
```

#### 🟣 Emballée
```css
background: #E9D5FF; /* Violet clair */
color: #6B21A8;      /* Violet foncé */
icon: fa-box
```

---

## 📦 Détail d'une Préparation

### URL
`/operateur-preparation/detail-prepa/<int:pk>/`

### Vue : `detail_prepa(request, pk)`

### Sections de la Page

#### 1. **Informations Client**
```
┌───────────────────────────────────────────┐
│  👤 Informations Client                    │
├───────────────────────────────────────────┤
│  Nom complet  : Jean DUPONT                │
│  Téléphone    : 0612345678                 │
│  Email        : jean.dupont@email.com      │
├───────────────────────────────────────────┤
│  🏠 Ville Client (origine) : Casablanca    │
│  📍 Ville de livraison     : Rabat         │
│  💰 Frais de livraison     : 25.00 DH      │
└───────────────────────────────────────────┘
```

**Couleurs** :
- Ville client (origine) : Orange (bg-orange-50)
- Ville de livraison : Vert (bg-green-50)
- Frais activés : Vert, Frais désactivés : Gris

#### 2. **Informations Commande**
```
┌───────────────────────────────────────────┐
│  📋 Informations Commande                  │
├───────────────────────────────────────────┤
│  ID YZ        : 211971                     │
│  N° Externe   : OC-00123                   │
│  Date Cmd     : 22/10/2025                 │
│  Total        : 1,250.00 DH                │
│  Source       : WhatsApp                   │
│  État         : En préparation             │
└───────────────────────────────────────────┘
```

#### 3. **Adresse de Livraison**
```
┌───────────────────────────────────────────┐
│  🚚 Adresse de Livraison                   │
├───────────────────────────────────────────┤
│  📍 Adresse complète                       │
│  Quartier Hay Riad, Immeuble 12, Apt 5    │
│  Rabat, Maroc                              │
└───────────────────────────────────────────┘
```

#### 4. **Articles du Panier**
Tableau détaillé des articles à préparer :

| Article | Variante | Quantité | Prix Unit. | Total |
|---------|----------|----------|------------|-------|
| T-Shirt Nike | Bleu - M | 2 | 250 DH | 500 DH |
| Pantalon Adidas | Noir - L | 1 | 450 DH | 450 DH |
| Chaussures | Blanc - 42 | 1 | 300 DH | 300 DH |

**Informations affichées** :
- Nom de l'article
- Couleur et pointure
- Quantité à préparer
- Prix unitaire appliqué
- Prix total de la ligne
- **Stock disponible** (avec alerte si faible)

#### 5. **Actions de Préparation**

##### Changer l'état
```
┌──────────────────────────────────┐
│  🔄 Changer l'état               │
├──────────────────────────────────┤
│  [ ] À imprimer                  │
│  [•] En préparation   ← Actuel   │
│  [ ] Collectée                   │
│  [ ] Emballée                    │
└──────────────────────────────────┘
```

**États disponibles** :
- **À imprimer** → Première étape (génération étiquettes)
- **En préparation** → Préparation en cours
- **Collectée** → Articles rassemblés
- **Emballée** → Prête pour expédition

**Workflow** :
```
À imprimer → En préparation → Collectée → Emballée → Validée (Supervision)
```

---

## 🔄 Changement d'État via API

### Endpoint
`/operateur-preparation/api/changer-etat-commande/<int:commande_id>/`

### Méthode
POST (AJAX)

### Paramètres
```json
{
    "nouvel_etat": "Collectée",
    "commentaire": "Articles collectés et vérifiés"
}
```

### Réponse Success
```json
{
    "success": true,
    "message": "État changé avec succès",
    "nouvel_etat": "Collectée",
    "redirect_url": "/operateur-preparation/liste-prepa/"
}
```

### Validation Backend
1. Vérification de l'opérateur (type PREPARATION)
2. Vérification de l'affectation de la commande
3. Vérification de l'existence du nouvel état
4. Clôture de l'état actuel (date_fin = now())
5. Création du nouvel état

---

## 📱 Vues Supplémentaires

### 1. **Commandes en Préparation**
- **URL** : `/operateur-preparation/en-preparation/`
- **Description** : Vue filtrée sur les commandes actuellement en préparation
- **Affichage** : Tableau simplifié

### 2. **Commandes Livrées Partiellement**
- **URL** : `/operateur-preparation/livrees-partiellement/`
- **Description** : Commandes avec livraison partielle nécessitant un renvoi
- **Workflow** : Créer un nouveau panier avec articles manquants

### 3. **Commandes Retournées**
- **URL** : `/operateur-preparation/retournees/`
- **Description** : Commandes retournées par la logistique
- **Action** : Re-préparation et vérification

---

## 🛠️ APIs Disponibles

### 1. **Produits de la Commande**
```
GET /operateur-preparation/api/commande/<commande_id>/produits/
```
**Retourne** : Liste des articles du panier avec variantes

### 2. **Articles Disponibles**
```
GET /operateur-preparation/api/articles-disponibles-prepa/
```
**Retourne** : Catalogue des articles disponibles pour ajout

### 3. **Panier de la Commande**
```
GET /operateur-preparation/api/commande/<commande_id>/panier/
```
**Retourne** : Détails complets du panier

### 4. **Rafraîchir Articles**
```
POST /operateur-preparation/commande/<commande_id>/rafraichir-articles/
```
**Action** : Recharge les articles du panier (après modification)

### 5. **Prix Upsell**
```
GET /operateur-preparation/commande/<commande_id>/prix-upsell/
```
**Retourne** : Calcul des prix selon le niveau upsell

---

## 🎨 Thème Visuel

### Couleurs Principales
```css
:root {
    --preparation-primary: #4A5568;    /* Gris foncé */
    --preparation-dark: #2D3748;       /* Gris très foncé */
    --preparation-border-accent: #CBD5E0; /* Gris clair */
    --preparation-hover: #718096;      /* Gris moyen */
}
```

### Icônes Font Awesome
- 📦 `fa-boxes` : Commandes
- 📋 `fa-clipboard-list` : Liste
- 🚚 `fa-truck-loading` : Détail préparation
- ✅ `fa-check-circle` : Validation
- 🔄 `fa-sync-alt` : Rafraîchir
- 📍 `fa-map-marker-alt` : Adresse

---

## 📊 Statistiques et KPIs

### Carte "Total Affectées"
```
┌─────────────────────────┐
│  📦 Total Affectées     │
│        15               │
│  commandes affectées    │
└─────────────────────────┘
```
- **Couleur** : Teal (bleu-vert)
- **Animation** : Hover scale + gradient

### Carte "Valeur Totale"
```
┌─────────────────────────┐
│  💰 Valeur Totale       │
│     45,000 DH           │
│  montant total          │
└─────────────────────────┘
```
- **Couleur** : Vert
- **Animation** : Hover scale + gradient

### Carte "Urgentes"
```
┌─────────────────────────┐
│  ⚠️  Urgentes           │
│         3               │
│  à traiter rapidement   │
└─────────────────────────┘
```
- **Couleur** : Orange
- **Animation** : Hover scale + pulse

---

## 🔒 Restrictions et Permissions

### Opérateurs de Préparation NE PEUVENT PAS :
- ❌ Modifier les informations client
- ❌ Modifier les prix des articles
- ❌ Ajouter ou supprimer des articles du panier
- ❌ Changer la ville de livraison
- ❌ Annuler une commande
- ❌ Accéder aux commandes non affectées

### Opérateurs de Préparation PEUVENT :
- ✅ Voir les détails complets de leurs commandes affectées
- ✅ Changer l'état de préparation
- ✅ Ajouter des commentaires sur la préparation
- ✅ Consulter l'historique des états
- ✅ Rechercher dans leurs commandes
- ✅ Générer des étiquettes de préparation

---

## 📱 Responsive Design

### Desktop (> 1024px)
- Tableau complet avec toutes les colonnes
- Sidebar fixe
- Actions rapides visibles

### Tablette (768px - 1024px)
- Tableau avec colonnes essentielles
- Sidebar repliable
- Cartes optimisées

### Mobile (< 768px)
- Vue cartes uniquement
- Navigation hamburger
- Actions en modal

---

## 🔄 Workflow Complet de Préparation

```
┌────────────────────────────────────────────────────────┐
│  1. RÉCEPTION                                          │
│     État : "Confirmée" → "À imprimer"                  │
│     Action : Superviseur affecte la commande           │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  2. IMPRESSION ÉTIQUETTES                              │
│     État : "À imprimer"                                │
│     Action : Opérateur génère et imprime étiquettes    │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  3. DÉBUT PRÉPARATION                                  │
│     État : "À imprimer" → "En préparation"             │
│     Action : Opérateur commence la collecte            │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  4. COLLECTE DES ARTICLES                              │
│     État : "En préparation"                            │
│     Actions :                                          │
│     - Récupération des articles du stock               │
│     - Vérification des variantes (couleur, pointure)   │
│     - Contrôle qualité                                 │
│     - Vérification des quantités                       │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  5. VALIDATION COLLECTE                                │
│     État : "En préparation" → "Collectée"              │
│     Action : Tous les articles sont rassemblés         │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  6. EMBALLAGE                                          │
│     État : "Collectée" → "Emballée"                    │
│     Actions :                                          │
│     - Emballage des articles                           │
│     - Apposition des étiquettes                        │
│     - Vérification finale                              │
└──────────────────┬─────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  7. VALIDATION SUPERVISEUR                             │
│     État : "Emballée" → "Validée"                      │
│     Action : Superviseur valide la préparation         │
│     → Transfert vers LOGISTIQUE                        │
└────────────────────────────────────────────────────────┘
```

---

## 🚨 Cas Particuliers

### Retour depuis Logistique
```
Livraison échouée → Retour Préparation
│
├─ Vérification de l'état du colis
├─ Vérification des articles
├─ Mise à jour des quantités
└─ Remise en préparation ou stockage
```

### Livraison Partielle
```
Livraison partielle → Création commande RENVOI-XXX
│
├─ Articles non livrés → Nouveau panier
├─ Nouvelle préparation
├─ Nouvelle affectation
└─ Nouvelle livraison
```

---

## 📞 Support et Contact

### Équipe de Développement
- **Frontend** : codsuitefrontend@gmail.com
- **Backend** : codsuitebackend@gmail.com
- **Support** : +212 779 635 687

### Documentation Technique
- **Repository** : CODRescue
- **Branche** : dev_jesse
- **Owner** : aldrinsro

---

**Dernière mise à jour** : 24 octobre 2025  
**Version** : 1.0.0  
**Développé par** : COD$uite Team avec YZ-PRESTATION
