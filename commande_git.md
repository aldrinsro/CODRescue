# Commandes Git Essentielles

## 📋 Gestion des branches et récupération des mises à jour

### Récupérer les mises à jour de main avec des modifications locales
```bash
# 1. Vérifier le statut actuel
git status

# 2. Sauvegarder temporairement les modifications locales
git stash push -m "Description des modifications"

# 3. Basculer sur la branche main
git checkout main

# 4. Récupérer les dernières mises à jour
git pull

# 5. Retourner sur votre branche de travail
git checkout dev_jesse

# 6. Restaurer vos modifications
git stash pop
```

## 🔄 Commandes de base

### Vérification du statut
```bash
git status                    # Voir l'état du repository
git log --oneline -10        # Voir les 10 derniers commits
git branch -a                # Voir toutes les branches
```

### Gestion des modifications
```bash
git add .                    # Ajouter tous les fichiers modifiés
git add fichier.py           # Ajouter un fichier spécifique
git commit -m "Message"      # Commiter avec un message
git commit -am "Message"     # Ajouter et commiter en une fois
```

### Gestion des branches
```bash
git checkout -b nouvelle-branche    # Créer et basculer sur une nouvelle branche
git checkout branche-existante      # Basculer sur une branche existante
git branch -d nom-branche           # Supprimer une branche locale
git push origin nom-branche         # Pousser une branche vers le remote
```

## 📦 Gestion du stash

### Sauvegarder temporairement
```bash
git stash                    # Sauvegarder les modifications en cours
git stash push -m "Message"  # Sauvegarder avec un message descriptif
git stash list               # Voir la liste des stashes
```

### Restaurer les modifications
```bash
git stash pop                # Restaurer et supprimer le dernier stash
git stash apply              # Restaurer sans supprimer le stash
git stash apply stash@{0}    # Restaurer un stash spécifique
git stash drop               # Supprimer le dernier stash
```

## 🔄 Synchronisation avec le remote

### Récupérer les mises à jour
```bash
git pull                     # Récupérer et fusionner les changements
git fetch                    # Récupérer sans fusionner
git fetch --all              # Récupérer depuis tous les remotes
```

### Envoyer les modifications
```bash
git push                     # Pousser vers la branche courante
git push origin main         # Pousser vers une branche spécifique
git push -u origin nouvelle-branche  # Pousser et définir le tracking
```

## 🔀 Fusion et rebase

### Fusion
```bash
git merge branche-source     # Fusionner une branche dans la branche courante
git merge --no-ff branche    # Fusionner sans fast-forward
```

### Rebase
```bash
git rebase main              # Rebaser la branche courante sur main
git rebase -i HEAD~3         # Rebase interactif des 3 derniers commits
```

## 🚨 Annulation et récupération

### Annuler des modifications
```bash
git restore fichier.py       # Annuler les modifications d'un fichier
git restore .                # Annuler toutes les modifications
git reset --hard HEAD        # Annuler tous les changements (DANGEREUX)
```

### Annuler des commits
```bash
git reset --soft HEAD~1      # Annuler le dernier commit, garder les modifications
git reset --hard HEAD~1      # Annuler le dernier commit et les modifications
git revert HEAD              # Créer un commit qui annule le dernier commit
```

## 🔍 Recherche et historique

### Rechercher dans l'historique
```bash
git log --grep="mot-clé"     # Rechercher par message de commit
git log --author="nom"       # Rechercher par auteur
git log --oneline --graph    # Voir l'historique en graphique
```

### Rechercher dans les fichiers
```bash
git grep "texte"             # Rechercher du texte dans tous les fichiers
git log -S "texte"           # Voir l'historique d'un texte spécifique
```

## 🏷️ Gestion des tags

```bash
git tag v1.0.0               # Créer un tag
git tag -a v1.0.0 -m "Message"  # Créer un tag annoté
git push origin v1.0.0       # Pousser un tag
git tag -l                   # Lister tous les tags
```

## 🔧 Configuration

```bash
git config --global user.name "Votre Nom"
git config --global user.email "votre@email.com"
git config --list            # Voir la configuration
```

## 📝 Bonnes pratiques

1. **Toujours vérifier le statut** avant de faire des opérations importantes
2. **Utiliser des messages de commit descriptifs**
3. **Faire des commits fréquents et petits**
4. **Tester avant de pousser vers main**
5. **Utiliser le stash pour sauvegarder temporairement**
6. **Créer des branches pour chaque nouvelle fonctionnalité**

## 🚨 Commandes dangereuses

⚠️ **Attention** - Ces commandes peuvent causer une perte de données :
```bash
git reset --hard HEAD        # Perte de toutes les modifications non commitées
git clean -fd                # Suppression de tous les fichiers non trackés
git push --force             # Écrasement de l'historique remote
```

---
*Document créé le $(date) - Commandes Git essentielles pour le projet CODRescue*
