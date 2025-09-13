# Système Upsell - YZ-CMD

## Vue d'ensemble

Le système upsell permet d'augmenter progressivement les prix des articles selon le niveau de la commande (compteur). Plus le compteur est élevé, plus les prix appliqués sont importants, permettant de maximiser le chiffre d'affaires.

## Architecture

### Modèle de données

Chaque article peut avoir jusqu'à 4 niveaux de prix upsell :
- `prix_unitaire` : Prix de base (niveau 0)
- `prix_upsell_1` : Prix niveau 1
- `prix_upsell_2` : Prix niveau 2
- `prix_upsell_3` : Prix niveau 3
- `prix_upsell_4` : Prix niveau 4 et plus

### Compteur de commande

Chaque commande possède un champ `compteur` qui détermine le niveau d'upsell actif :
- **Compteur 0** : Aucun upsell, prix normal
- **Compteur 1** : Niveau 1 d'upsell
- **Compteur 2** : Niveau 2 d'upsell
- **Compteur 3** : Niveau 3 d'upsell
- **Compteur 4+** : Niveau 4 d'upsell (maximum)

### Incrémentation du compteur

Le compteur s'incrémente automatiquement selon la **quantité totale d'articles upsell** dans la commande :

**Formule de calcul :**
```
compteur = max(0, total_quantite_upsell - 1)
```

**Règles d'incrémentation :**
- **0-1 unité upsell** → `compteur = 0` (pas d'upsell)
- **2 unités upsell** → `compteur = 1` (niveau 1)
- **3 unités upsell** → `compteur = 2` (niveau 2)
- **4 unités upsell** → `compteur = 3` (niveau 3)
- **5+ unités upsell** → `compteur = 4` (niveau maximum)

**Moments de recalcul :**
1. **Ajout d'article** : Si l'article ajouté est upsell
2. **Modification de quantité** : Si l'article modifié est upsell
3. **Suppression d'article** : Si l'article supprimé était upsell
4. **Remplacement d'article** : Recalcul complet

**Implémentation côté serveur :**
```python
from django.db.models import Sum

# Calculer la quantité totale d'articles upsell
total_quantite_upsell = commande.paniers.filter(
    article__isUpsell=True
).aggregate(total=Sum('quantite'))['total'] or 0

# Appliquer la formule
if total_quantite_upsell >= 2:
    commande.compteur = total_quantite_upsell - 1
else:
    commande.compteur = 0

commande.save()
```

## Fonctionnement

### 1. Application automatique des prix

Quand une commande a un compteur > 0, les prix upsell sont appliqués automatiquement :

```javascript
function getPrixUpsellAvecCompteur(article, compteur) {
    if (compteur === 0) return article.prix_unitaire;
    else if (compteur === 1 && article.prix_upsell_1) return article.prix_upsell_1;
    else if (compteur === 2 && article.prix_upsell_2) return article.prix_upsell_2;
    else if (compteur === 3 && article.prix_upsell_3) return article.prix_upsell_3;
    else if (compteur >= 4 && article.prix_upsell_4) return article.prix_upsell_4;
    return article.prix_unitaire; // Fallback si pas de prix défini
}
```

### 2. Identification des articles upsell

Les articles éligibles à l'upsell sont marqués avec le champ `isUpsell = True`. Seuls ces articles voient leur prix modifié selon le compteur.

### 3. Interface utilisateur

#### Affichage du niveau actuel
```html
<div class="text-xl font-bold" id="compteur-upsell-header">
    Niveau {{ commande.compteur }}
</div>
```

#### Filtre des articles upsell
```html
<span id="filter-upsell" onclick="filtrerArticles('upsell')">
    ⬆️ UPSELL
</span>
```

### 4. Mise à jour dynamique

Quand le compteur change, tous les éléments de l'interface sont mis à jour :

```javascript
function mettreAJourCompteurUpsell(nouveauCompteur) {
    // Met à jour l'affichage du compteur
    document.getElementById('compteur-upsell-header').textContent = `Niveau ${nouveauCompteur}`;
    
    // Met à jour les prix unitaires
    mettreAJourPrixUnitaires(nouveauCompteur);
    
    // Recalcule les totaux
    calculerTotalCommande();
}
```

## Exemples d'incrémentation du compteur

### Exemple 1: Commande progressive
```
Panier initial : Vide
Compteur : 0

1. Ajoute 1x Chaussures (isUpsell=True)
   → total_quantite_upsell = 1
   → compteur = max(0, 1-1) = 0

2. Ajoute 1x T-shirt (isUpsell=True) 
   → total_quantite_upsell = 2
   → compteur = max(0, 2-1) = 1

3. Modifie Chaussures : quantité = 3
   → total_quantite_upsell = 4 (3+1)
   → compteur = max(0, 4-1) = 3

4. Ajoute 1x Pantalon (isUpsell=False)
   → total_quantite_upsell = 4 (pas de changement)
   → compteur = 3 (inchangé)
```

### Exemple 2: Impact des suppressions
```
Panier : 3x Chaussures upsell + 2x T-shirts upsell
total_quantite_upsell = 5
Compteur : 4 (niveau maximum)

1. Supprime 1x T-shirt
   → total_quantite_upsell = 4
   → compteur = max(0, 4-1) = 3

2. Supprime complètement les Chaussures
   → total_quantite_upsell = 1
   → compteur = max(0, 1-1) = 0
```

## Exemples de prix appliqués

### Exemple 1: Article avec upsell complet
```
Article: Chaussures de sport
- Prix normal: 200 DH
- Prix upsell niveau 1: 250 DH
- Prix upsell niveau 2: 300 DH
- Prix upsell niveau 3: 350 DH
- Prix upsell niveau 4: 400 DH

Si compteur = 2 → Prix appliqué = 300 DH
```

### Exemple 2: Article sans upsell complet
```
Article: T-shirt
- Prix normal: 80 DH
- Prix upsell niveau 1: 100 DH
- Prix upsell niveau 2: non défini
- Prix upsell niveau 3: non défini
- Prix upsell niveau 4: non défini

Si compteur = 2 → Prix appliqué = 80 DH (fallback)
```

## Logique métier

### Règles d'application

1. **Priorité** : Si un prix upsell n'est pas défini pour un niveau, le système utilise le prix unitaire de base
2. **Articles non-upsell** : Les articles avec `isUpsell = False` gardent toujours leur prix unitaire
3. **Niveau maximum** : Tous les compteurs ≥ 4 utilisent le `prix_upsell_4`

### Calcul des totaux

```javascript
function calculerSousTotalArticle(article, quantite, compteur) {
    const prixUnitaire = article.isUpsell ? 
        getPrixUpsellAvecCompteur(article, compteur) : 
        article.prix_unitaire;
    
    return prixUnitaire * quantite;
}
```

## Interface de filtrage

### Raccourcis clavier
- **Touche 5** : Filtre rapide des articles upsell
- **Fonction** : `filtrerArticles('upsell')`

### Compteur d'articles
Le badge upsell affiche le nombre d'articles upsell disponibles en temps réel.

## Intégration avec d'autres modules

### Module de préparation
Quand une commande passe en préparation, les prix upsell sont définitivement appliqués selon le compteur au moment de la validation.

### Module logistique
Les opérateurs logistiques voient les prix finaux avec upsell déjà appliqués, ils ne peuvent pas les modifier.

### Service après-vente
Le SAV voit l'historique des niveaux upsell appliqués via les commentaires d'état de la commande.

## Debug et développement

### Variables de test
```javascript
// Tester le changement de niveau
function testerMiseAJourCompteur() {
    const compteurActuel = parseInt(document.getElementById('compteur-upsell-header').textContent.replace('Niveau ', '')) || 0;
    const nouveauCompteur = (compteurActuel + 1) % 5; // Cycle 0-4
    mettreAJourCompteurUpsell(nouveauCompteur);
}

// Tester les calculs de prix
function testerCalculsPrix() {
    const articles = getArticlesDisponibles();
    articles.forEach(article => {
        for(let i = 0; i <= 4; i++) {
            const prix = getPrixUpsellAvecCompteur(article, i);
            console.log(`${article.nom} - Niveau ${i}: ${prix} DH`);
        }
    });
}
```

### Logs de débogage
Le système génère des logs détaillés pour chaque calcul de prix :
```
📊 UPSELL: 2 article(s)
⬆️ UPSELL: Chaussures Nike (true), T-shirt Adidas (true)
🧪 Test de mise à jour des prix: 1 → 2
✅ Compteur upsell mis à jour vers: 2
```

## Bonnes pratiques

1. **Définir tous les niveaux** : Pour une expérience cohérente, définir les 4 niveaux d'upsell
2. **Progression logique** : S'assurer que prix_upsell_1 < prix_upsell_2 < prix_upsell_3 < prix_upsell_4
3. **Test systématique** : Utiliser les fonctions de test pour valider les calculs
4. **Documentation** : Commenter les changements de compteur dans l'historique des commandes