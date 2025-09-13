# 📦 Interface Articles

## 📋 Vue d'ensemble

L'interface de gestion des articles permet de gérer le catalogue de produits, les variantes, les promotions et les stocks de l'e-commerce.

## 🎯 Fonctionnalités principales

### 📦 **Gestion du Catalogue**
- **Création d'articles** : Ajout de nouveaux produits
- **Modification** : Mise à jour des informations
- **Suppression** : Gestion du cycle de vie
- **Duplication** : Création d'articles similaires

### 🎨 **Gestion des Variantes**
- **Couleurs** : Gestion des couleurs disponibles
- **Pointures** : Gestion des tailles
- **Références** : Codes de référence uniques
- **Prix** : Tarification par variante

### 🏷️ **Promotions et Remises**
- **Création de promotions** : Définition des offres
- **Gestion des remises** : Calculs automatiques
- **Périodes de validité** : Dates de début/fin
- **Conditions** : Règles d'application

### 📊 **Gestion des Stocks**
- **Suivi en temps réel** : Quantités disponibles
- **Alertes de rupture** : Notifications automatiques
- **Réapprovisionnement** : Gestion des commandes
- **Inventaire** : Contrôles périodiques

## 🚀 Accès

**URL** : `/articles/`

## 📱 Modules disponibles

### 📦 **Module Articles** (`article/`)
- Gestion du catalogue
- Variantes et promotions
- Gestion des stocks
- Interface d'administration

## 🔧 Utilisation

### 1. **Connexion**
```bash
# Accès via l'URL des articles
http://localhost:8000/articles/
```

### 2. **Création d'un Article**
1. Accéder au formulaire de création
2. Saisir les informations de base
3. Ajouter les variantes (couleur, pointure)
4. Définir les prix et stocks
5. Sauvegarder l'article

### 3. **Gestion des Variantes**
1. Sélectionner l'article
2. Accéder à la gestion des variantes
3. Ajouter/modifier les couleurs et pointures
4. Définir les références uniques
5. Mettre à jour les stocks par variante

### 4. **Création de Promotions**
1. Accéder à la gestion des promotions
2. Définir les conditions de l'offre
3. Sélectionner les articles concernés
4. Définir les dates de validité
5. Activer la promotion

## 📋 Pages principales

| Page | URL | Description |
|------|-----|-------------|
| Liste des Articles | `/articles/liste/` | Catalogue complet |
| Créer Article | `/articles/creer/` | Formulaire de création |
| Détail Article | `/articles/detail/<id>/` | Fiche détaillée |
| Variantes | `/articles/variantes/<id>/` | Gestion des variantes |
| Promotions | `/articles/promotions/` | Gestion des offres |
| Couleurs/Pointures | `/articles/couleurs-pointures/` | Gestion des attributs |

## 🔐 Permissions requises

- **Gestionnaire Articles** : Accès complet à l'interface
- **Opérateur** : Accès en lecture seule
- **Superviseur** : Accès complet + validation
- **Administrateur** : Accès complet + configuration

## 🎨 Interface

- **Design** : Interface moderne et intuitive
- **Responsive** : Optimisée pour tous les écrans
- **Navigation** : Menu spécialisé articles
- **Couleurs** : Thème professionnel (orange/bleu)

## 📊 Types d'Articles

### 👕 **Articles avec Variantes**
- **Couleurs** : Rouge, Bleu, Vert, Noir, Blanc
- **Pointures** : XS, S, M, L, XL, XXL
- **Références** : Code unique par combinaison
- **Stocks** : Gestion par variante

### 📱 **Articles Simples**
- **Pas de variantes** : Article unique
- **Référence unique** : Un seul code
- **Stock global** : Quantité totale
- **Prix fixe** : Tarification simple

## 🔧 Fonctionnalités Avancées

### 🏷️ **Système de Promotions**
- **Remises en pourcentage** : -10%, -20%, etc.
- **Remises fixes** : -5€, -10€, etc.
- **Promotions conditionnelles** : Achat minimum
- **Promotions croisées** : Articles liés

### 📊 **Gestion des Stocks**
- **Alertes automatiques** : Seuils de rupture
- **Réapprovisionnement** : Commandes automatiques
- **Inventaire** : Contrôles périodiques
- **Historique** : Suivi des mouvements

### 🔍 **Recherche et Filtrage**
- **Recherche textuelle** : Nom, description, référence
- **Filtres par catégorie** : Type d'article
- **Filtres par stock** : Disponibilité
- **Filtres par promotion** : Articles en promotion

## 🔧 Commandes utiles

```bash
# Lister tous les articles
GET /articles/api/liste/

# Créer un nouvel article
POST /articles/api/creer/

# Modifier un article
PUT /articles/api/modifier/<id>/

# Gérer les variantes
GET /articles/api/variantes/<id>/

# Créer une promotion
POST /articles/api/promotions/creer/
```

## 📋 Checklist de Création d'Article

### ✅ **Informations Obligatoires**
- [ ] Nom de l'article
- [ ] Description détaillée
- [ ] Prix de base
- [ ] Catégorie
- [ ] Image principale

### 🎨 **Variantes (si applicable)**
- [ ] Couleurs disponibles
- [ ] Pointures disponibles
- [ ] Références uniques
- [ ] Prix par variante
- [ ] Stocks par variante

### 🏷️ **Promotions (optionnel)**
- [ ] Type de remise
- [ ] Valeur de la remise
- [ ] Dates de validité
- [ ] Conditions d'application

## 📊 Métriques Articles

### 📈 **Performance du Catalogue**
- **Nombre total d'articles** : Taille du catalogue
- **Articles actifs** : Produits disponibles
- **Articles en promotion** : Offres en cours
- **Taux de rotation** : Popularité des articles

### 📊 **Gestion des Stocks**
- **Stock moyen** : Niveau de stock
- **Ruptures de stock** : Articles indisponibles
- **Réapprovisionnements** : Commandes fournisseurs
- **Pertes** : Articles endommagés/perdus

## 📞 Support

Pour toute question sur l'interface des articles :
- **Email Frontend** : codsuitefrontend@gmail.com
- **Email Backend** : codsuitebackend@gmail.com
- **Téléphone** : +212 779 635 687