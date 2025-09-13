# 🛒 Interface Commandes

## 📋 Vue d'ensemble

L'interface de gestion des commandes est le cœur du système e-commerce. Elle permet de gérer l'ensemble du cycle de vie des commandes, de la création à la livraison.

## 🎯 Fonctionnalités principales

### 🛒 **Gestion du Cycle de Vie**
- **Création** : Saisie de nouvelles commandes
- **Validation** : Contrôle et validation des données
- **Préparation** : Suivi de la préparation
- **Livraison** : Gestion des expéditions
- **Suivi** : Tracking complet des commandes

### 📊 **États des Commandes**
- **Nouvelle** : Commande créée, en attente
- **Confirmée** : Validée, prête pour préparation
- **En préparation** : En cours de préparation
- **Préparée** : Prête pour expédition
- **Livrée** : Expédiée au client
- **Retournée** : Retour en cours
- **Annulée** : Commande annulée

### 🔍 **Recherche et Filtrage**
- **Recherche globale** : Multi-critères
- **Filtres par état** : Commandes par statut
- **Filtres par client** : Recherche par client
- **Filtres par date** : Période spécifique
- **Filtres géographiques** : Par région/ville

### 📈 **Analytics et Rapports**
- **Statistiques en temps réel** : KPIs instantanés
- **Rapports détaillés** : Analyses approfondies
- **Tendances** : Évolution des commandes
- **Performance** : Métriques d'efficacité

## 🚀 Accès

**URL** : `/commandes/`

## 📱 Modules disponibles

### 🛒 **Module Commandes** (`commande/`)
- Gestion complète du cycle de vie
- États personnalisables
- Gestion des remises et promotions
- Export de données

### 📊 **Module KPIs** (`kpis/`)
- Indicateurs de performance
- Tableaux de bord
- Rapports détaillés
- Métriques en temps réel

## 🔧 Utilisation

### 1. **Connexion**
```bash
# Accès via l'URL des commandes
http://localhost:8000/commandes/
```

### 2. **Création d'une Commande**
1. Accéder au formulaire de création
2. Sélectionner le client
3. Ajouter les articles souhaités
4. Définir les variantes (couleur, pointure)
5. Calculer les totaux et remises
6. Valider la commande

### 3. **Suivi d'une Commande**
1. Rechercher la commande
2. Consulter l'état actuel
3. Voir l'historique des modifications
4. Suivre le processus de préparation
5. Tracker la livraison

### 4. **Gestion des États**
1. Sélectionner la commande
2. Changer l'état selon le processus
3. Ajouter des commentaires
4. Notifier les équipes concernées
5. Mettre à jour le suivi

## 📋 Pages principales

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/commandes/` | Vue d'ensemble des commandes |
| Liste | `/commandes/liste/` | Liste complète des commandes |
| Créer | `/commandes/creer/` | Formulaire de création |
| Détail | `/commandes/detail/<id>/` | Fiche détaillée |
| À traiter | `/commandes/a-traiter/` | Commandes en attente |
| Confirmées | `/commandes/confirmees/` | Commandes validées |
| En préparation | `/commandes/preparees/` | Commandes préparées |
| Livrées | `/commandes/livrees/` | Commandes expédiées |
| Annulées | `/commandes/annulees/` | Commandes annulées |
| Statistiques | `/commandes/statistiques/` | Analyses et rapports |

## 🔐 Permissions requises

- **Gestionnaire Commandes** : Accès complet à l'interface
- **Opérateur** : Accès limité selon le rôle
- **Superviseur** : Accès complet + validation
- **Administrateur** : Accès complet + configuration

## 🎨 Interface

- **Design** : Interface moderne et fonctionnelle
- **Responsive** : Optimisée pour tous les écrans
- **Navigation** : Menu spécialisé commandes
- **Couleurs** : Thème professionnel (bleu/vert)

## 📊 Workflow des Commandes

### 🔄 **Processus Standard**
1. **Création** → Commande saisie
2. **Validation** → Contrôle des données
3. **Confirmation** → Validation finale
4. **Préparation** → Préparation des articles
5. **Expédition** → Envoi au client
6. **Livraison** → Réception confirmée

### ⚠️ **Processus Exceptionnels**
- **Annulation** : Commande annulée
- **Retour** : Retour client
- **Modification** : Ajustements post-création
- **Remboursement** : Traitement des remboursements

## 🔧 Fonctionnalités Avancées

### 💰 **Gestion des Prix et Remises**
- **Prix de base** : Tarif standard
- **Remises automatiques** : Promotions applicables
- **Remises manuelles** : Ajustements personnalisés
- **Frais de port** : Calcul automatique
- **TVA** : Gestion de la fiscalité

### 📦 **Gestion des Paniers**
- **Articles multiples** : Plusieurs produits
- **Variantes** : Couleur, pointure, etc.
- **Quantités** : Gestion des stocks
- **Prix unitaires** : Tarification détaillée
- **Totaux** : Calculs automatiques

### 🏷️ **Étiquettes et Documents**
- **Génération d'étiquettes** : Étiquettes de préparation
- **Factures** : Documents de vente
- **Bons de livraison** : Documents d'expédition
- **Récapitulatifs** : Synthèses de commande

## 🔧 Commandes utiles

```bash
# Lister les commandes
GET /commandes/api/liste/

# Créer une commande
POST /commandes/api/creer/

# Modifier une commande
PUT /commandes/api/modifier/<id>/

# Changer l'état
POST /commandes/api/changer-etat/<id>/

# Générer une étiquette
GET /commandes/api/etiquette/<id>/

# Exporter les données
GET /commandes/api/export/?format=csv&periode=2025-01
```

## 📋 Checklist de Création de Commande

### ✅ **Informations Client**
- [ ] Client sélectionné ou créé
- [ ] Adresse de livraison complète
- [ ] Coordonnées de contact
- [ ] Moyen de paiement

### 📦 **Articles et Variantes**
- [ ] Articles sélectionnés
- [ ] Variantes définies (couleur, pointure)
- [ ] Quantités vérifiées
- [ ] Stocks disponibles

### 💰 **Prix et Remises**
- [ ] Prix de base corrects
- [ ] Remises appliquées
- [ ] Frais de port calculés
- [ ] Total final validé

## 📊 Métriques Commandes

### 📈 **Volume et Performance**
- **Nombre de commandes** : Volume total
- **Valeur moyenne** : Panier moyen
- **Taux de conversion** : Efficacité commerciale
- **Temps de traitement** : Rapidité de traitement

### 📊 **Qualité et Satisfaction**
- **Taux d'annulation** : Commandes annulées
- **Taux de retour** : Retours clients
- **Satisfaction client** : Indicateurs de qualité
- **Temps de livraison** : Performance logistique

## 📞 Support

Pour toute question sur l'interface des commandes :
- **Email Frontend** : codsuitefrontend@gmail.com
- **Email Backend** : codsuitebackend@gmail.com
- **Téléphone** : +212 779 635 687