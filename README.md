# 🚀 CODRescue - Système de Gestion E-commerce

<div align="center">

<!-- Logo YZ-PRESTATION pour GitHub (URL complète) -->

<img src="https://raw.githubusercontent.com/votre-username/CODRescue/main/static/logo-tickets/loging_logo.png" alt="YZ-PRESTATION Logo" width="200" height="200">

<!-- Alternative locale (décommentez si nécessaire) -->

<!-- <img src="./static/logo-tickets/loging_logo.png" alt="YZ-PRESTATION Logo" width="200" height="200"> -->

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Django](https://img.shields.io/badge/Django-5.1.7-green.svg)
![Python](https://img.shields.io/badge/Python-3.13+-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**Système de gestion complet pour e-commerce avec préparation de commandes, logistique et supervision**

[![Made with Django](https://img.shields.io/badge/Made%20with-Django-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Built with Python](https://img.shields.io/badge/Built%20with-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## 📋 Table des matières

- [🎯 Aperçu du projet](#-aperçu-du-projet)
- [✨ Fonctionnalités principales](#-fonctionnalités-principales)
- [🏗️ Architecture](#️-architecture)
- [🚀 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [📱 Modules disponibles](#-modules-disponibles)
- [🔧 Utilisation](#-utilisation)
- [📊 Technologies utilisées](#-technologies-utilisées)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

---

## 🎯 Aperçu du projet

**CODRescue** est une solution complète de gestion e-commerce développée avec Django, conçue pour optimiser les processus de préparation de commandes, de logistique et de supervision. Le système offre une interface moderne et intuitive pour gérer efficacement toutes les étapes du cycle de vie des commandes.

### 🎨 Interface utilisateur moderne

- Design responsive avec Tailwind CSS
- Interface intuitive et accessible
- Recherche globale intelligente
- Tableaux de bord en temps réel

---

## ✨ Fonctionnalités principales

### 🛒 **Gestion des Commandes**

- Création et suivi des commandes
- États de commande avancés
- Gestion des clients et adresses
- Système de validation automatique

### 📦 **Préparation de Commandes**

- Interface dédiée aux opérateurs de préparation
- Suivi en temps réel des commandes
- Gestion des articles et variantes
- Système de validation des préparations

### 🚚 **Logistique et Livraison**

- Gestion des livraisons
- Suivi des retours
- Service après-vente
- Optimisation des routes

### 👥 **Supervision**

- Tableau de bord 360° pour les superviseurs
- KPIs et métriques en temps réel
- Gestion des opérateurs
- Rapports détaillés

### 🔍 **Recherche Intelligente**

- Recherche globale multi-critères
- Suggestions automatiques
- Filtres avancés
- Recherche en temps réel

---

## 🏗️ Architecture

```
CODRescue/
├── 📁 article/              # Gestion des articles et variantes
├── 📁 client/               # Gestion des clients
├── 📁 commande/             # Module principal des commandes
├── 📁 kpis/                 # Indicateurs de performance
├── 📁 livraison/            # Gestion des livraisons
├── 📁 operatConfirme/       # Interface opérateur confirmé
├── 📁 operatLogistic/       # Interface logistique
├── 📁 parametre/            # Paramètres et configuration
├── 📁 Prepacommande/        # Interface préparation
├── 📁 Superpreparation/     # Interface supervision
├── 📁 synchronisation/      # Synchronisation externe
├── 📁 templates/            # Templates HTML
├── 📁 static/               # Fichiers statiques
└── 📁 config/               # Configuration Django
```

---

## 🚀 Installation

### Prérequis

- Python 3.13+
- PostgreSQL (recommandé) ou SQLite
- Node.js (pour Tailwind CSS)
- Git

### 1. Cloner le projet

```bash
git clone https://github.com/votre-username/CODRescue.git
cd CODRescue
```

### 2. Créer un environnement virtuel

```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 6. Collecter les fichiers statiques

```bash
python manage.py collectstatic
```

### 7. Lancer le serveur

```bash
python manage.py runserver
```

---

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
SECRET_KEY=votre_clé_secrète
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/codrescue
REDIS_URL=redis://localhost:6379/0
```

### Configuration de la base de données

Modifiez `config/settings.py` selon votre configuration :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'codrescue',
        'USER': 'votre_utilisateur',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 📱 Modules disponibles

### 🛒 **Module Commandes** (`commande/`)

- Gestion complète du cycle de vie des commandes
- États personnalisables
- Gestion des remises et promotions
- Export de données

### 📦 **Module Préparation** (`Prepacommande/`)

- Interface opérateur de préparation
- Suivi des commandes en cours
- Gestion des articles et variantes
- Validation des préparations

### 🚚 **Module Logistique** (`operatLogistic/`)

- Gestion des livraisons
- Suivi des retours
- Service après-vente
- Optimisation des routes

### 👥 **Module Supervision** (`Superpreparation/`)

- Tableau de bord 360°
- KPIs et métriques
- Gestion des équipes
- Rapports avancés

### ⚙️ **Module Paramètres** (`parametre/`)

- Configuration du système
- Gestion des utilisateurs
- Paramètres métier
- Dashboard administratif

---

## 🔧 Utilisation

### Accès aux interfaces

- **Administration** : `/admin/`
- **Préparation** : `/operateur-preparation/`
- **Logistique** : `/operateur-logistique/`
- **Supervision** : `/super-preparation/`
- **Paramètres** : `/parametre/`

### Commandes utiles

```bash
# Créer des données de test
python manage.py loaddata fixtures/initial_data.json

# Synchroniser avec Google Sheets
python manage.py sync_google_sheets

# Générer des rapports
python manage.py generate_reports

# Nettoyer les données
python manage.py cleanup_old_data
```

---

## 📊 Technologies utilisées

### Backend

- **Django 5.1.7** - Framework web principal
- **PostgreSQL** - Base de données relationnelle
- **Redis** - Cache et sessions
- **Celery** - Tâches asynchrones
- **Django REST Framework** - API REST

### Frontend

- **Tailwind CSS** - Framework CSS
- **JavaScript ES6+** - Interactivité
- **Chart.js** - Graphiques et visualisations
- **Font Awesome** - Icônes

### Outils de développement

- **Django Debug Toolbar** - Débogage
- **Pytest** - Tests unitaires
- **Black** - Formatage de code
- **Flake8** - Linting

### Déploiement

- **Gunicorn** - Serveur WSGI
- **Nginx** - Serveur web
- **Docker** - Conteneurisation
- **GitHub Actions** - CI/CD

---

## 🤝 Contribution

Nous accueillons les contributions ! Voici comment contribuer :

1. **Fork** le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add some AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une **Pull Request**

### Guidelines de contribution

- Suivre les conventions de code Python (PEP 8)
- Ajouter des tests pour les nouvelles fonctionnalités
- Documenter les changements importants
- Respecter la structure du projet

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Équipe

<div align="center">

![YZ-PRESTATION](https://img.shields.io/badge/YZ--PRESTATION-Enterprise-green?style=for-the-badge)

</div>

**Développé par COD$uite Team avec YZ-PRESTATION**

### 🏢 **Entreprise**

**YZ-PRESTATION** - Solutions logistiques et e-commerce
*Logo affiché ci-dessus*

### 👨‍💻 **Équipe de développement**

**COD$uite Team**

- **Frontend** : codsuitefrontend@gmail.com
- **Backend** : codsuitebackend@gmail.com
- **Téléphone** : +212 779 635 687 / +212 694 528 498

### 📋 **Informations du projet**

- **Version** : V.1.0.0
- **Dernière mise à jour** : 2025
- **Support technique** : codsuitebackend@gmail.com

---

## 📞 Support

### 🏢 **Support Entreprise**

- 📧 **Email Frontend** : codsuitefrontend@gmail.com
- 📧 **Email Backend** : codsuitebackend@gmail.com
- 📞 **Téléphone** : +212 779 635 687 / +212 694 528 498

### 🔧 **Support Technique**

- 🐛 **Issues** : [GitHub Issues](https://github.com/votre-username/CODRescue/issues)
- 📖 **Documentation** : [Wiki du projet](https://github.com/votre-username/CODRescue/wiki)
- 💬 **Support technique** : codsuitebackend@gmail.com

---

<div align="center">

**⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile ! ⭐**

[![GitHub stars](https://img.shields.io/github/stars/votre-username/CODRescue?style=social)](https://github.com/votre-username/CODRescue/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/votre-username/CODRescue?style=social)](https://github.com/votre-username/CODRescue/network)

</div>

---

# YZ-RescueV1

YZ-RescueV1 est une plateforme de gestion opérationnelle pour le suivi, la préparation et la logistique des commandes e-commerce, conçue pour les équipes de gestion, de confirmation et de livraison.

## Technologies utilisées
- **Python 3.x** : Langage principal pour le backend
- **Django** : Framework web principal (MVC, ORM, templates)
- **JavaScript (ES6+)** : Frontend dynamique, gestion des modales, filtres, interactions utilisateur
- **HTML/CSS (Tailwind, custom styles)** : Templates responsives et modernes
- **SQLite / PostgreSQL** : Base de données (configurable)
- **Bootstrap & FontAwesome** : UI, icônes et composants visuels

## Fonctionnalités principales

### 1. Gestion des commandes
- Création, modification et suivi des commandes clients
- Filtrage intelligent par ville, région, état, synchronisation, etc.
- Système de pagination et recherche avancée
- Historique complet des états et opérations sur chaque commande

### 2. Système de remises et upsell
- Application de remises personnalisées (pourcentage uniquement)
- Gestion dynamique des prix upsell selon le niveau du client
- Affichage contextuel des prix (promotion, liquidation, test, upsell, normal)

### 3. Préparation et logistique
- Module de préparation des commandes avec suivi d'état (en préparation, préparée, livrée, etc.)
- Génération d'étiquettes, export Excel pour la logistique
- Gestion des articles, variantes, stocks et opérations associées

## Structure du projet
- `article/` : Gestion des articles, modèles, variantes
- `commande/` : Logique de commande, états, opérations, remises
- `operatConfirme/` : Module opérateur confirmé (confirmation, suivi, modales)
- `Superpreparation/` : Module de préparation avancée, logistique, export
- `static/` : Fichiers JS, CSS, images
- `templates/` : Templates Django pour toutes les vues

## Démarrage rapide
1. Cloner le projet
2. Installer les dépendances Python : `pip install -r requirements.txt`
3. Configurer la base de données dans `config/settings.py`
4. Lancer le serveur : `python manage.py runserver`

## Auteur
Aldrin SRO

Pour toute question ou contribution, consultez la documentation dans le dossier `docs/` ou ouvrez une issue sur le dépôt.
