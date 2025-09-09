# 🚀 Système de Génération Automatique d'Étiquettes en Temps Réel

## 📋 Vue d'ensemble

Le système de génération automatique d'étiquettes permet de créer automatiquement des étiquettes pour toutes les commandes qui ont des articles dans leur panier. Le système fonctionne en temps réel et s'actualise automatiquement toutes les 30 secondes.

## 🎯 Fonctionnalités

### ✅ Génération Automatique
- **Détection automatique** : Le système détecte automatiquement les nouvelles commandes avec paniers
- **Génération en temps réel** : Les étiquettes sont générées automatiquement sans intervention manuelle
- **Actualisation continue** : La page se met à jour automatiquement toutes les 30 secondes

### 🔧 Génération Manuelle
- **Bouton "Générer Toutes les Étiquettes"** : Génère les étiquettes pour toutes les commandes sans étiquettes
- **Génération individuelle** : Possibilité de générer une étiquette pour une commande spécifique
- **Actualisation manuelle** : Bouton pour forcer l'actualisation des données

### 📊 Interface Utilisateur
- **Compteur en temps réel** : Affiche le nombre de commandes sans étiquettes
- **Compteur de temps** : Indique le temps restant avant la prochaine actualisation automatique
- **Notifications** : Messages de succès/erreur pour les actions utilisateur
- **Design responsive** : Interface adaptée à tous les écrans

## 🛠️ Architecture Technique

### Backend (Django)
- **Vue API** : `get_commandes_with_paniers()` - Récupère les commandes sans étiquettes
- **Génération** : `generate_etiquettes_manually()` - Génère les étiquettes
- **Template par défaut** : Utilise "Template Livraison Standard"

### Frontend (JavaScript)
- **Classe principale** : `RealtimeCommandesManager`
- **Actualisation automatique** : Timer de 30 secondes
- **Compteur de temps** : Affichage du temps restant
- **Gestion des événements** : Boutons et interactions utilisateur

### Commandes de Management
- **`auto_generate_etiquettes`** : Génération en lot avec options
- **`watch_commandes`** : Surveillance continue des nouvelles commandes
- **`create_test_commande`** : Création de commandes de test

## 🚀 Utilisation

### 1. Interface Web
1. Accédez à la page "Mes étiquettes"
2. La section "Commandes avec Paniers" s'affiche automatiquement
3. Le système se met à jour toutes les 30 secondes
4. Utilisez les boutons pour générer manuellement si nécessaire

### 2. Commandes de Management

#### Génération en lot
```bash
# Test (dry-run)
python manage.py auto_generate_etiquettes --dry-run

# Génération réelle
python manage.py auto_generate_etiquettes

# Forcer la génération (même si étiquettes existent)
python manage.py auto_generate_etiquettes --force
```

#### Surveillance continue
```bash
# Surveillance avec intervalle personnalisé
python manage.py watch_commandes --interval 60

# Exécution unique
python manage.py watch_commandes --once

# Limiter le nombre d'exécutions
python manage.py watch_commandes --max-runs 10
```

#### Création de commandes de test
```bash
# Créer une commande de test
python manage.py create_test_commande

# Créer plusieurs commandes
python manage.py create_test_commande --count 5
```

## 📁 Fichiers Impliqués

### Backend
- `etiquettes_pro/views.py` - Vues API et génération
- `etiquettes_pro/urls.py` - Routes API
- `etiquettes_pro/management/commands/` - Commandes de management

### Frontend
- `templates/etiquettes_pro/etiquette_list.html` - Interface utilisateur
- `static/js/etiquettes_pro/realtime-commandes.js` - Logique JavaScript

### Modèles
- `EtiquetteTemplate` - Template d'étiquette
- `Etiquette` - Étiquette générée
- `Commande` - Commande avec paniers
- `Panier` - Articles de la commande

## 🔄 Flux de Données

1. **Détection** : Le système détecte les commandes avec paniers
2. **Vérification** : Vérifie si des étiquettes existent déjà
3. **Génération** : Crée les étiquettes manquantes
4. **Mise à jour** : Actualise l'interface utilisateur
5. **Répétition** : Le cycle se répète automatiquement

## ⚙️ Configuration

### Template par Défaut
Le système utilise le template "Template Livraison Standard". Assurez-vous qu'il existe et est actif.

### Intervalle d'Actualisation
- **Interface web** : 30 secondes (configurable dans le JavaScript)
- **Surveillance** : Configurable via les paramètres de commande

### Permissions
- **`@superviseur_required`** : Accès aux fonctionnalités de génération
- **`@can_print_etiquettes`** : Permission d'impression

## 🐛 Dépannage

### Problèmes Courants

1. **Template non trouvé**
   - Vérifiez que "Template Livraison Standard" existe
   - Assurez-vous qu'il est marqué comme actif

2. **Aucune commande détectée**
   - Vérifiez que des commandes ont des paniers
   - Vérifiez les permissions utilisateur

3. **Actualisation ne fonctionne pas**
   - Vérifiez la console JavaScript pour les erreurs
   - Vérifiez la connexion réseau

### Logs
- **Console JavaScript** : Messages de débogage du frontend
- **Logs Django** : Messages du backend
- **Commandes** : Sortie des commandes de management

## 🎉 Avantages

- ✅ **Automatisation complète** : Plus besoin de génération manuelle
- ✅ **Temps réel** : Mise à jour continue des données
- ✅ **Interface intuitive** : Facile à utiliser
- ✅ **Flexibilité** : Génération manuelle disponible
- ✅ **Performance** : Optimisé pour de gros volumes
- ✅ **Fiabilité** : Gestion d'erreurs robuste

## 🔮 Évolutions Futures

- **Notifications push** : Alertes en temps réel
- **Statistiques avancées** : Métriques de performance
- **Templates multiples** : Support de plusieurs templates
- **API REST** : Intégration avec des systèmes externes
- **Planification** : Génération programmée
