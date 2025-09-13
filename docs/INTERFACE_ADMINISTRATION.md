# 🛠️ Interface Administration

## 📋 Vue d'ensemble

L'interface d'administration de CODRescue est l'interface principale pour la gestion du système, des utilisateurs et des paramètres globaux.

## 🎯 Fonctionnalités principales

### 👥 **Gestion des Utilisateurs**
- Création et modification des opérateurs
- Gestion des rôles et permissions
- Réinitialisation des mots de passe
- Profils détaillés des utilisateurs

### 🌍 **Gestion Géographique**
- **Régions** : Création et gestion des régions
- **Villes** : Gestion des villes par région
- **Répartition automatique** : Système de répartition des commandes

### 📊 **Dashboard 360°**
- Vue d'ensemble complète du système
- KPIs en temps réel
- Statistiques détaillées
- Monitoring des performances

### ⚙️ **Paramètres Système**
- Configuration générale
- Gestion des mots de passe
- Paramètres de sécurité
- Configuration des notifications

## 🚀 Accès

**URL** : `/admin/` ou `/parametre/`

## 📱 Modules disponibles

### 🏢 **Module Paramètres** (`parametre/`)
- Configuration du système
- Gestion des utilisateurs
- Paramètres métier
- Dashboard administratif

### 📊 **Module KPIs** (`kpis/`)
- Indicateurs de performance
- Tableaux de bord
- Rapports détaillés
- Métriques en temps réel

## 🔧 Utilisation

### 1. **Connexion**
```bash
# Accès via l'URL d'administration
http://localhost:8000/admin/
```

### 2. **Gestion des Opérateurs**
- Créer un nouvel opérateur
- Modifier les informations
- Gérer les permissions
- Réinitialiser les mots de passe

### 3. **Configuration Géographique**
- Ajouter des régions
- Gérer les villes
- Configurer la répartition automatique

### 4. **Monitoring**
- Consulter les KPIs
- Analyser les performances
- Gérer les alertes

## 📋 Pages principales

| Page | URL | Description |
|------|-----|-------------|
| Dashboard 360° | `/parametre/360/` | Vue d'ensemble complète |
| Gestion Opérateurs | `/parametre/operateurs/` | Liste et gestion des utilisateurs |
| Gestion Régions | `/parametre/regions/` | Gestion des régions |
| Gestion Villes | `/parametre/villes/` | Gestion des villes |
| Paramètres | `/parametre/parametre/` | Configuration système |

## 🔐 Permissions requises

- **Administrateur** : Accès complet
- **Superviseur** : Accès limité aux KPIs
- **Opérateur** : Accès refusé

## 🎨 Interface

- **Design** : Interface moderne et intuitive
- **Responsive** : Compatible mobile et desktop
- **Navigation** : Menu latéral avec icônes
- **Thème** : Couleurs professionnelles

## 📞 Support

Pour toute question sur l'interface d'administration :
- **Email** : codsuitebackend@gmail.com
- **Téléphone** : +212 779 635 687