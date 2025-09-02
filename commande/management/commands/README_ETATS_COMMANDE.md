# 📋 Scripts de Gestion des États de Commande

Ce dossier contient des scripts Django pour gérer les états de commande par défaut dans la base de données.

## 🚀 Scripts Disponibles

### 1. `load_default_etats_commande.py`
**Objectif** : Charge tous les états de commande par défaut dans la base de données.

**Fonctionnalités** :
- Crée les états manquants
- Met à jour les états existants si nécessaire
- Évite les doublons
- Assigne automatiquement les couleurs et l'ordre

**Utilisation** :
```bash
python manage.py load_default_etats_commande
```

### 2. `verify_etats_commande.py`
**Objectif** : Vérifie que tous les états de commande par défaut sont présents.

**Fonctionnalités** :
- Liste tous les états présents
- Identifie les états manquants
- Vérifie l'intégrité (doublons, ordre)
- Fournit un rapport détaillé

**Utilisation** :
```bash
python manage.py verify_etats_commande
```

### 3. `reset_etats_commande.py`
**Objectif** : Réinitialise complètement les états de commande.

**⚠️ ATTENTION** : Ce script supprime TOUS les états existants !

**Fonctionnalités** :
- Supprime tous les états existants
- Recharge les états par défaut
- Demande confirmation (sauf avec `--force`)
- Vérification automatique après rechargement

**Utilisation** :
```bash
# Avec confirmation
python manage.py reset_etats_commande

# Sans confirmation (dangerous)
python manage.py reset_etats_commande --force
```

## 📊 États de Commande Par Défaut

| Ordre | État | Couleur | Description |
|-------|------|---------|-------------|
| 1 | Non affectée | #6B7280 | Commande créée mais non assignée |
| 2 | Affectée | #3B82F6 | Commande assignée à un opérateur |
| 3 | En cours de confirmation | #F59E0B | En attente de confirmation |
| 4 | Confirmée | #10B981 | Commande confirmée |
| 5 | En préparation | #06B6D4 | En cours de préparation |
| 6 | Préparée | #14B8A6 | Préparation terminée |
| 7 | Collectée | #6B7280 | Article collecté |
| 8 | Emballée | #6B7280 | Article emballé |
| 9 | En livraison | #8B5CF6 | En cours de livraison |
| 10 | Livrée | #22C55E | Livraison terminée |
| 11 | Annulée | #EF4444 | Commande annulée |
| 12 | Doublon | #EF4444 | Commande en double |
| 13 | Erronée | #F97316 | Commande avec erreur |

## 🔧 Utilisation Recommandée

### Première Installation
```bash
# 1. Charger les états par défaut
python manage.py load_default_etats_commande

# 2. Vérifier que tout est correct
python manage.py verify_etats_commande
```

### Mise à Jour
```bash
# 1. Vérifier l'état actuel
python manage.py verify_etats_commande

# 2. Charger les nouveaux états (met à jour automatiquement)
python manage.py load_default_etats_commande

# 3. Vérifier le résultat
python manage.py verify_etats_commande
```

### Réinitialisation Complète
```bash
# ⚠️ ATTENTION : Supprime tout !
python manage.py reset_etats_commande
```

## 📝 Logs et Sortie

### Exemple de Sortie - Chargement
```
🚀 Début du chargement des états de commande par défaut...
✅ Créé: Non affectée (Couleur: #6B7280, Ordre: 1)
✅ Créé: Affectée (Couleur: #3B82F6, Ordre: 2)
🔄 Mis à jour: Confirmée (Couleur: #10B981, Ordre: 4)
ℹ️  Existant: En préparation (déjà à jour)

============================================================
📊 RÉSUMÉ DU CHARGEMENT:
   • États créés: 2
   • États mis à jour: 1
   • États déjà existants: 10
   • Total traité: 13
============================================================

🎯 Total des états dans la base de données: 13
✅ Chargement terminé avec succès !
```

### Exemple de Sortie - Vérification
```
🔍 Vérification des états de commande dans la base de données...

📊 ÉTATS ATTENDUS: 13
📊 ÉTATS PRÉSENTS: 13
✅ Non affectée - Couleur: #6B7280 - Ordre: 1
✅ Affectée - Couleur: #3B82F6 - Ordre: 2
✅ En cours de confirmation - Couleur: #F59E0B - Ordre: 3

============================================================
📋 RÉSUMÉ DE LA VÉRIFICATION:
   • États trouvés: 13
   • États manquants: 0
   • Total attendu: 13
============================================================

🎉 Tous les états de commande sont présents !

🔧 VÉRIFICATION DE L'INTÉGRITÉ:
   ✅ Aucun doublon détecté
   ✅ Ordre des états valide

🎯 VÉRIFICATION TERMINÉE AVEC SUCCÈS !
```

## ⚠️ Précautions

1. **Sauvegarde** : Toujours faire une sauvegarde de la base avant d'utiliser `reset_etats_commande`
2. **Environnement** : Tester d'abord en développement
3. **Dépendances** : Vérifier que le modèle `EnumEtatCmd` existe
4. **Permissions** : S'assurer d'avoir les droits d'écriture en base

## 🐛 Dépannage

### Erreur "Model not found"
```bash
# Vérifier que le modèle est bien importé
python manage.py shell
>>> from commande.models import EnumEtatCmd
>>> EnumEtatCmd.objects.count()
```

### Erreur de permissions
```bash
# Vérifier les permissions de la base de données
# S'assurer que l'utilisateur peut créer/modifier des tables
```

### États manquants après chargement
```bash
# Vérifier les logs d'erreur
python manage.py verify_etats_commande

# Recharger si nécessaire
python manage.py load_default_etats_commande
```

## 📞 Support

En cas de problème :
1. Vérifier les logs Django
2. Exécuter `verify_etats_commande` pour diagnostiquer
3. Consulter la documentation Django sur les management commands
4. Vérifier la structure de la base de données
