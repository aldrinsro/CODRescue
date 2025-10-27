# 🔄 Workflow Complet - Application CODRescue

## 📊 Vue d'ensemble du système

**CODRescue** est une application de gestion e-commerce développée avec Django, permettant de gérer l'ensemble du cycle de vie des commandes, de la création à la livraison et au service après-vente.

---

## 🎯 Architecture des Interfaces

### 1️⃣ **Interface Commandes** (`/commandes/`)
**Rôle** : Point d'entrée pour la gestion des commandes  
**Utilisateurs** : Gestionnaires de commandes, Administrateurs

#### Fonctionnalités principales :
- ✅ Création de nouvelles commandes
- 📊 Vue d'ensemble de toutes les commandes
- 🔍 Recherche et filtrage avancés
- 📈 Analytics et KPIs
- 🏷️ Génération d'étiquettes

#### États gérés :
- **Nouvelle** : Commande créée, en attente de traitement
- **À traiter** : Prête pour confirmation
- **Confirmée** : Validée, prête pour préparation
- **En préparation** : En cours de préparation
- **Préparée** : Prête pour expédition
- **Livrée** : Expédiée au client
- **Retournée** : Retour en cours
- **Annulée** : Commande annulée

---

### 2️⃣ **Interface Confirmation** (`/operateur-confirmation/`)
**Rôle** : Validation et confirmation des commandes  
**Utilisateurs** : Opérateurs de confirmation

#### Workflow de confirmation :
```
1. Réception de la commande
   ├─ Vérification des données client (nom, téléphone, adresse)
   ├─ Contrôle des articles et variantes (couleur, pointure)
   └─ Validation de la disponibilité des stocks

2. Analyse et validation
   ├─ Contrôles automatiques de cohérence
   ├─ Vérification du montant total
   ├─ Application des remises et promotions
   └─ Validation de l'adresse de livraison

3. Modification si nécessaire
   ├─ Ajout/suppression d'articles
   ├─ Modification des variantes
   ├─ Ajustement des quantités
   └─ Modification des données client

4. Confirmation finale
   ├─ Validation définitive
   ├─ Changement d'état → "Confirmée"
   ├─ Notification à l'équipe de préparation
   └─ Génération des documents de préparation
```

#### Modèles utilisés :
- **Commande** : Données principales de la commande
- **Panier** : Articles de la commande avec variantes
- **EtatCommande** : Historique des changements d'état
- **Operation** : Actions effectuées sur la commande

---

### 3️⃣ **Interface Préparation** (`/operateur-preparation/`)
**Rôle** : Préparation physique des commandes  
**Utilisateurs** : Opérateurs de préparation (Prepacommande)

#### Workflow de préparation :
```
1. Réception commande confirmée
   ├─ Consultation de la liste des commandes à préparer
   ├─ Sélection d'une commande
   └─ Visualisation des articles à préparer

2. Démarrage de la préparation
   ├─ Changement d'état → "En préparation"
   ├─ Récupération des articles du stock
   ├─ Vérification des variantes (couleur, pointure)
   └─ Contrôle qualité des produits

3. Préparation des articles
   ├─ Validation article par article
   ├─ Scan des codes-barres (optionnel)
   ├─ Vérification des quantités
   └─ Signalement des anomalies

4. Finalisation
   ├─ Emballage de la commande
   ├─ Changement d'état → "Préparée" ou "Emballée"
   ├─ Génération de l'étiquette de livraison
   └─ Transfert à la logistique
```

#### Pages principales :
- `/operateur-preparation/liste/` : Commandes confirmées à préparer
- `/operateur-preparation/preparation/` : Commandes en cours
- `/operateur-preparation/livrees/` : Livraisons partielles
- `/operateur-preparation/retournees/` : Retours à traiter

---

### 4️⃣ **Interface Supervision** (`/super-preparation/`)
**Rôle** : Vue 360° et management du système  
**Utilisateurs** : Superviseurs, Managers

#### Fonctionnalités de supervision :
```
1. Dashboard 360°
   ├─ KPIs en temps réel
   │  ├─ Nombre de commandes par état
   │  ├─ Taux de confirmation
   │  ├─ Temps moyen de préparation
   │  └─ Taux de retour
   ├─ Graphiques interactifs
   └─ Alertes automatiques

2. Gestion des équipes
   ├─ Performance individuelle des opérateurs
   ├─ Répartition des tâches
   ├─ Suivi des temps de traitement
   └─ Évaluations de performance

3. Gestion avancée des commandes
   ├─ Commandes confirmées
   ├─ Commandes préparées
   ├─ Commandes emballées
   ├─ Envois (exports journaliers)
   └─ Articles retournés

4. Analytics et rapports
   ├─ Rapports détaillés
   ├─ Analyses prédictives
   ├─ Export de données
   └─ Comparaisons de périodes
```

#### Pages spécifiques :
- `/super-preparation/commande_confirmees/` : Suivi confirmations
- `/super-preparation/commandes_preparees/` : Suivi préparations
- `/super-preparation/commandes_emballees/` : Suivi emballages
- `/super-preparation/envois/` : Exports journaliers
- `/super-preparation/articles_retournes/` : Gestion des retours
- `/super-preparation/liste_prepa/` : Vue d'ensemble préparations

---

### 5️⃣ **Interface Logistique** (`/operateur-logistique/`)
**Rôle** : Gestion des livraisons et SAV  
**Utilisateurs** : Opérateurs logistiques

#### Workflow logistique :
```
1. Gestion des livraisons
   ├─ Réception des commandes préparées
   ├─ Planification des tournées
   ├─ Assignation aux livreurs
   ├─ Suivi GPS (optionnel)
   └─ Confirmation de livraison

2. Traitement des retours
   ├─ Réception de la demande de retour
   ├─ Validation des conditions de retour
   ├─ Autorisation du retour
   ├─ Collecte du produit
   ├─ Analyse de l'état du produit
   └─ Décision : remboursement, échange ou réparation

3. Service Après-Vente (SAV)
   ├─ Réception des réclamations
   ├─ Classification par type de problème
   ├─ Attribution à un opérateur SAV
   ├─ Analyse et diagnostic
   ├─ Proposition de solution
   ├─ Suivi de la résolution
   └─ Validation de la satisfaction client

4. Gestion des articles retournés
   ├─ Articles défectueux
   ├─ Articles en attente de traitement
   ├─ Articles réintégrés en stock
   └─ Articles traités
```

#### Modules SAV :
- `/operateur-logistique/sav/commandes_livrees/` : Livraisons réussies
- `/operateur-logistique/sav/commandes_livrees_partiellement/` : Livraisons partielles
- `/operateur-logistique/sav/commandes_retournees/` : Retours clients
- `/operateur-logistique/sav/commandes_reportees/` : Livraisons reportées

---

### 6️⃣ **Interface Articles** (`/articles/`)
**Rôle** : Gestion du catalogue produits  
**Utilisateurs** : Gestionnaires d'articles

#### Workflow de gestion d'articles :
```
1. Création d'un article
   ├─ Informations de base
   │  ├─ Nom de l'article
   │  ├─ Description
   │  ├─ Catégorie
   │  └─ Référence de base
   ├─ Gestion des variantes
   │  ├─ Couleurs disponibles
   │  ├─ Pointures disponibles
   │  └─ Références uniques par variante
   ├─ Tarification
   │  ├─ Prix normal
   │  ├─ Prix promotion
   │  ├─ Prix liquidation
   │  ├─ Prix upsell (niveaux 1-4)
   │  └─ Prix remises (niveaux 1-4)
   └─ Gestion des stocks
      ├─ Stock initial
      ├─ Seuil d'alerte
      └─ Stock par variante

2. Gestion des promotions
   ├─ Définition de l'offre
   ├─ Sélection des articles
   ├─ Dates de validité
   ├─ Conditions d'application
   └─ Activation de la promotion

3. Suivi des stocks
   ├─ Alertes de rupture
   ├─ Réapprovisionnement
   ├─ Inventaire périodique
   └─ Historique des mouvements
```

#### Types de prix :
- **normal** : Prix de base
- **promotion** : Prix promotionnel
- **liquidation** : Prix de liquidation
- **test** : Prix de test
- **upsell_niveau_1** à **upsell_niveau_4** : Prix d'upsell
- **remise_1** à **remise_4** : Prix avec remise

---

### 7️⃣ **Interface Administration** (`/admin/` et `/parametre/`)
**Rôle** : Configuration système et gestion des utilisateurs  
**Utilisateurs** : Administrateurs

#### Modules d'administration :
```
1. Gestion des utilisateurs
   ├─ Création d'opérateurs
   ├─ Attribution des rôles
   ├─ Gestion des permissions
   └─ Suivi des activités

2. Paramétrage système
   ├─ Gestion des régions et villes
   ├─ Configuration des états de commandes
   ├─ Templates d'étiquettes
   ├─ Paramètres de remise
   └─ Configuration des prix

3. Synchronisation
   ├─ Import/Export Google Sheets
   ├─ Synchronisation des commandes
   ├─ Synchronisation des articles
   └─ Synchronisation des clients
```

---

## 🔄 Flux de Données Complet

### Cycle de vie d'une commande :

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRÉATION DE LA COMMANDE                       │
│  Sources : Appel, WhatsApp, SMS, Email, Facebook, Youcan, Shopify│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTERFACE COMMANDES (/commandes/)                   │
│  • Saisie des données client                                     │
│  • Ajout des articles et variantes                               │
│  • Application des remises                                       │
│  • État : "Nouvelle" → "À traiter"                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│      INTERFACE CONFIRMATION (/operateur-confirmation/)           │
│  • Vérification des données                                      │
│  • Contrôle de cohérence                                         │
│  • Validation des stocks                                         │
│  • Modification si nécessaire                                    │
│  • État : "À traiter" → "Confirmée"                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│      INTERFACE PRÉPARATION (/operateur-preparation/)             │
│  • Récupération des articles                                     │
│  • Vérification des variantes                                    │
│  • Contrôle qualité                                              │
│  • Emballage                                                     │
│  • État : "Confirmée" → "En préparation" → "Préparée"/"Emballée"│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         INTERFACE SUPERVISION (/super-preparation/)              │
│  • Validation finale                                             │
│  • Génération d'étiquettes                                       │
│  • Export journalier (Envoi)                                     │
│  • État : "Emballée" → "Validée"                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│       INTERFACE LOGISTIQUE (/operateur-logistique/)              │
│  • Planification des tournées                                    │
│  • Assignation aux livreurs                                      │
│  • Suivi de la livraison                                         │
│  • État : "Validée" → "En livraison" → "Livrée"                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
          ┌─────────────────┐   ┌─────────────────┐
          │   LIVRÉE        │   │   RETOURNÉE     │
          │   (Succès)      │   │   (Retour SAV)  │
          └─────────────────┘   └────────┬────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │  TRAITEMENT SAV          │
                          │  • Analyse du retour     │
                          │  • Remboursement/Échange │
                          │  • Réintégration stock   │
                          └──────────────────────────┘
```

---

## 📊 Modèles de Données Principaux

### 1. **Commande** (`commande.models.Commande`)
```python
- num_cmd : Numéro unique de commande
- id_yz : Identifiant YZ unique
- origine : Source de création (OC, ADMIN, SYNC)
- date_cmd : Date de la commande
- total_cmd : Montant total
- adresse : Adresse de livraison
- client : Relation avec Client
- ville : Relation avec Ville
- source : Canal d'acquisition (Appel, WhatsApp, etc.)
- payement : Statut de paiement
- frais_livraison : Frais de port inclus
- Date_livraison : Date effective de livraison
- Date_paiement : Date de paiement
- envoi : Relation avec Envoi (export journalier)
```

### 2. **Panier** (`commande.models.Panier`)
```python
- commande : Relation avec Commande
- article : Relation avec Article
- variante : Relation avec VarianteArticle
- couleur : Couleur choisie
- pointure : Pointure choisie
- quantite : Nombre d'unités
- prix_unitaire : Prix par unité
- type_prix_gele : Type de prix appliqué
- prix_panier : Prix total du panier
```

### 3. **EtatCommande** (`commande.models.EtatCommande`)
```python
- commande : Relation avec Commande
- etat : Relation avec EnumEtatCmd
- date_changement : Date du changement
- utilisateur : Qui a effectué le changement
- commentaire : Détails du changement
```

### 4. **Operation** (`commande.models.Operation`)
```python
- commande : Relation avec Commande
- operateur : Opérateur ayant effectué l'action
- type_operation : Type d'opération effectuée
- date_operation : Date de l'opération
- details : Détails de l'opération
```

### 5. **ArticleRetourne** (`commande.models.ArticleRetourne`)
```python
- commande : Relation avec Commande
- article : Article retourné
- etat : État du retour (En attente, Défectueux, Traité, Réintégré)
- raison : Motif du retour
- date_retour : Date du retour
- traite_par : Opérateur ayant traité le retour
```

---

## 🔐 Matrice des Permissions

| Interface           | Admin | Superviseur | Opérateur Confirmation | Opérateur Préparation | Opérateur Logistique |
|---------------------|-------|-------------|------------------------|----------------------|---------------------|
| Commandes           | ✅ RWD | ✅ RW       | ✅ RW                  | ✅ R                 | ✅ R                |
| Confirmation        | ✅ RWD | ✅ RW       | ✅ RWD                 | ❌                   | ❌                  |
| Préparation         | ✅ RWD | ✅ RW       | ✅ R                   | ✅ RWD               | ❌                  |
| Supervision         | ✅ RWD | ✅ RWD      | ❌                     | ❌                   | ❌                  |
| Logistique          | ✅ RWD | ✅ RW       | ❌                     | ❌                   | ✅ RWD              |
| Articles            | ✅ RWD | ✅ RWD      | ✅ R                   | ✅ R                 | ✅ R                |
| Administration      | ✅ RWD | ✅ R        | ❌                     | ❌                   | ❌                  |

**Légende** : R = Lecture, W = Écriture, D = Suppression

---

## 📈 KPIs et Métriques

### Métriques Opérationnelles :
- **Taux de confirmation** : % de commandes confirmées
- **Temps moyen de confirmation** : Durée moyenne entre création et confirmation
- **Temps moyen de préparation** : Durée moyenne de préparation
- **Taux de livraison réussie** : % de livraisons abouties
- **Taux de retour** : % de commandes retournées

### Métriques Business :
- **Volume de commandes** : Nombre total de commandes
- **Panier moyen** : Valeur moyenne des commandes
- **Chiffre d'affaires** : CA total
- **Coût opérationnel** : Coûts de traitement
- **ROI** : Retour sur investissement

### Métriques de Qualité :
- **Taux d'erreur** : % de commandes avec erreurs
- **Satisfaction client** : Score de satisfaction
- **Taux de réclamation** : % de réclamations
- **Taux de réintégration stock** : % d'articles retournés remis en stock

---

## 🔧 Technologies Utilisées

### Backend :
- **Framework** : Django 5.1.7
- **Base de données** : PostgreSQL (psycopg2-binary)
- **API** : Django REST Framework
- **Authentification** : Django Allauth
- **Cache** : Redis (django-redis)
- **Tâches asynchrones** : Celery + Redis

### Frontend :
- **Framework CSS** : Tailwind CSS (django-tailwind)
- **JavaScript** : Vanilla JS + modules ES6
- **Icônes** : Font Awesome
- **Charts** : Chart.js (pour les KPIs)

### Intégrations :
- **Google Sheets** : gspread (synchronisation)
- **Cloud Storage** : Cloudinary (images)
- **Génération PDF** : ReportLab, pdfkit
- **Codes-barres** : python-barcode
- **QR Codes** : qrcode[pil]

### Serveur Production :
- **WSGI** : Gunicorn
- **Reverse Proxy** : Nginx (recommandé)
- **Tunnel** : Cloudflare Tunnel (optionnel)

---

## 🚀 Démarrage Rapide

### 1. Installation :
```bash
# Cloner le repository
git clone https://github.com/aldrinsro/CODRescue.git
cd CODRescue

# Créer l'environnement virtuel
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres
```

### 2. Configuration de la base de données :
```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

### 3. Lancement :
```bash
# Mode développement
python manage.py runserver

# Mode production (avec Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 4. Accès :
- **Interface Admin** : http://localhost:8000/admin/
- **Interface Commandes** : http://localhost:8000/commandes/
- **Interface Confirmation** : http://localhost:8000/operateur-confirmation/
- **Interface Préparation** : http://localhost:8000/operateur-preparation/
- **Interface Supervision** : http://localhost:8000/super-preparation/
- **Interface Logistique** : http://localhost:8000/operateur-logistique/

---

## 📞 Support et Contact

### Équipe de Développement :
- **Frontend** : codsuitefrontend@gmail.com
- **Backend** : codsuitebackend@gmail.com
- **Téléphone** : +212 779 635 687 / +212 694 528 498

### Développé par :
**COD$uite Team** avec **YZ-PRESTATION**

---

## 📝 Notes Importantes

### États de Commande Disponibles :
Les états sont configurables via le modèle `EnumEtatCmd`. Les états par défaut incluent :
- Non affectée
- Affectée
- En cours de confirmation
- Confirmée
- Erronnée
- Doublon
- À imprimer
- En préparation
- Collectée
- Emballée
- Validée
- En livraison
- Livrée
- Retournée

### Types de Prix :
Le système supporte plusieurs types de prix pour la tarification flexible :
- Prix normal
- Prix promotion
- Prix liquidation
- Prix test
- Prix upsell (4 niveaux)
- Prix remise (4 niveaux)

### Synchronisation :
L'application supporte la synchronisation bidirectionnelle avec Google Sheets pour :
- Import des commandes
- Export des données
- Mise à jour des stocks
- Synchronisation des clients

---

**Dernière mise à jour** : 22 octobre 2025  
**Version** : 1.0.0
