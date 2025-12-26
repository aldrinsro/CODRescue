# 📊 Documentation du Module de Calcul CA

## Vue d'ensemble

Le module `calcul_ca.py` isole toute la logique de calcul du Chiffre d'Affaires (CA) dans des fonctions réutilisables et facilement maintenables.

---

## 🎯 Avantages de cette architecture

✅ **Code modulaire** : La logique de calcul est séparée des vues
✅ **Facilité de maintenance** : Un seul endroit pour modifier les calculs
✅ **Réutilisabilité** : Les fonctions peuvent être utilisées partout
✅ **Testabilité** : Facile de créer des tests unitaires
✅ **Flexibilité** : Plusieurs méthodes de calcul disponibles

---

## 🔧 Configuration

### Méthodes de calcul disponibles

Le module propose **2 méthodes principales** :

```python
from kpis.utils.calcul_ca import MethodeCalculCA

# Méthode 1: Somme des total_cmd (montant global de la commande)
MethodeCalculCA.TOTAL_COMMANDE

# Méthode 2: Somme des sous_totaux des paniers (détail par article)
MethodeCalculCA.SUM_PANIERS

# Méthode active (modifiable facilement)
MethodeCalculCA.METHODE_ACTIVE  # = TOTAL_COMMANDE par défaut
```

### ⚙️ Comment changer la méthode de calcul ?

**Dans `calcul_ca.py`, ligne 23 :**
```python
# Actuellement:
METHODE_ACTIVE = TOTAL_COMMANDE

# Pour changer en somme des paniers:
METHODE_ACTIVE = SUM_PANIERS
```

**Résultat** : Tous les calculs utiliseront automatiquement la nouvelle méthode !

---

## 📚 Fonctions disponibles

### 1️⃣ `calcul_ca_periode()`

Calcule le CA sur une période donnée.

**Paramètres :**
- `date_debut` (date) : Date de début
- `date_fin` (date) : Date de fin
- `etats_inclus` (list, optionnel) : Liste des états à inclure (défaut: `['Livree']`)
- `methode` (str, optionnel) : Méthode de calcul (défaut: `METHODE_ACTIVE`)

**Retour :**
```python
{
    'ca_total': 150000.0,
    'nb_commandes': 45,
    'methode_calcul': 'total_commande',
    'periode': {
        'debut': '2024-12-01',
        'fin': '2024-12-31'
    }
}
```

**Exemple d'utilisation :**
```python
from datetime import date
from kpis.utils.calcul_ca import calcul_ca_periode

result = calcul_ca_periode(
    date_debut=date(2024, 12, 1),
    date_fin=date(2024, 12, 31),
    etats_inclus=['Livree']
)

print(f"CA du mois: {result['ca_total']} DH")
print(f"Nombre de commandes: {result['nb_commandes']}")
```

---

### 2️⃣ `calcul_ca_avec_tendance()`

Calcule le CA avec comparaison entre deux périodes.

**Paramètres :**
- `date_debut_actuel` (date)
- `date_fin_actuel` (date)
- `date_debut_precedent` (date)
- `date_fin_precedent` (date)
- `etats_inclus` (list, optionnel)
- `methode` (str, optionnel)

**Retour :**
```python
{
    'ca_actuel': 150000.0,
    'ca_precedent': 130000.0,
    'tendance_pourcent': 15.4,
    'variation_absolue': 20000.0,
    'nb_commandes_actuel': 45,
    'nb_commandes_precedent': 38,
    'methode_calcul': 'total_commande'
}
```

**Exemple d'utilisation :**
```python
from datetime import date
from kpis.utils.calcul_ca import calcul_ca_avec_tendance

result = calcul_ca_avec_tendance(
    date_debut_actuel=date(2024, 12, 1),
    date_fin_actuel=date(2024, 12, 31),
    date_debut_precedent=date(2024, 11, 1),
    date_fin_precedent=date(2024, 11, 30)
)

print(f"CA actuel: {result['ca_actuel']} DH")
print(f"Tendance: {result['tendance_pourcent']}%")
```

---

### 3️⃣ `calcul_ca_journalier()`

Calcule le CA jour par jour sur une période.

**Paramètres :**
- `date_debut` (date)
- `date_fin` (date)
- `etats_inclus` (list, optionnel)
- `methode` (str, optionnel)

**Retour :**
```python
{
    'evolution': [
        {
            'date': '2024-12-01',
            'date_formatee': '01/12',
            'ca': 5000.0,
            'ca_formate': '5 000 DH'
        },
        ...
    ],
    'statistiques': {
        'ca_total': 150000.0,
        'ca_moyen': 5000.0,
        'ca_max_jour': 12000.0,
        'ca_min_jour': 1500.0,
        'jours_avec_ventes': 28,
        'nb_jours_total': 31,
        'taux_activite': 90.3
    },
    'methode_calcul': 'total_commande'
}
```

**Exemple :**
```python
result = calcul_ca_journalier(
    date_debut=date(2024, 12, 1),
    date_fin=date(2024, 12, 31)
)

for jour in result['evolution']:
    print(f"{jour['date_formatee']}: {jour['ca_formate']}")
```

---

### 4️⃣ `calcul_ca_par_article()`

Calcule le CA par article (Top modèles).

**Paramètres :**
- `date_debut` (date)
- `date_fin` (date)
- `limite` (int, optionnel) : Nombre max d'articles (défaut: 10)
- `etats_inclus` (list, optionnel)

**Retour :**
```python
[
    {
        'article_id': 123,
        'article_nom': 'Chaussure Classic',
        'article_reference': 'CH-001',
        'ca_total': 45000.0,
        'ca_formate': '45 000 DH',
        'quantite_vendue': 150,
        'nb_commandes': 85,
        'prix_moyen': 300.0
    },
    ...
]
```

---

### 5️⃣ `calcul_ca_par_region()`

Calcule le CA par région géographique.

**Paramètres :**
- `date_debut` (date)
- `date_fin` (date)
- `limite` (int, optionnel) : Nombre max de régions (défaut: 10)
- `etats_inclus` (list, optionnel)
- `methode` (str, optionnel)

**Retour :**
```python
[
    {
        'region': 'Grand Casablanca',
        'ca_total': 85000.0,
        'ca_total_format': '85K DH',
        'nb_commandes': 120,
        'ca_moyen': 708.33,
        'pourcentage': 35.4
    },
    ...
]
```

---

### 6️⃣ `calcul_panier_moyen()`

Calcule le panier moyen sur une période.

**Paramètres :**
- `date_debut` (date)
- `date_fin` (date)
- `etats_inclus` (list, optionnel)

**Retour :**
```python
750.50  # Montant moyen en DH
```

---

## 🚀 Migration depuis l'ancienne version

### Avant (views_ventes.py)

```python
# Code complexe dans la vue
ca_mois_actuel = Commande.objects.filter(
    date_cmd__gte=debut_mois,
    date_cmd__lte=aujourd_hui,
    etats__enum_etat__libelle__iexact='Livrée'
).aggregate(total=Sum('total_cmd'))['total'] or 0
```

### Après (avec le nouveau module)

```python
# Simple et clair
from kpis.utils.calcul_ca import calcul_ca_periode

result = calcul_ca_periode(debut_mois, aujourd_hui)
ca_mois_actuel = result['ca_total']
```

---

## 🎨 Exemples complets

### Exemple 1: Dashboard mensuel

```python
from kpis.utils.calcul_ca import calcul_ca_avec_tendance
from datetime import date

# Calculer le CA du mois avec tendance
result = calcul_ca_avec_tendance(
    date_debut_actuel=date(2024, 12, 1),
    date_fin_actuel=date(2024, 12, 31),
    date_debut_precedent=date(2024, 11, 1),
    date_fin_precedent=date(2024, 11, 30),
    etats_inclus=['Livree']
)

# Afficher les résultats
print(f"CA décembre: {result['ca_actuel']:,.0f} DH")
print(f"CA novembre: {result['ca_precedent']:,.0f} DH")
print(f"Évolution: {result['tendance_pourcent']:+.1f}%")
```

### Exemple 2: Graphique d'évolution

```python
from kpis.utils.calcul_ca import calcul_ca_journalier
from datetime import date

# Obtenir les données pour un graphique
result = calcul_ca_journalier(
    date_debut=date(2024, 12, 1),
    date_fin=date(2024, 12, 31)
)

# Données prêtes pour Chart.js
labels = [jour['date_formatee'] for jour in result['evolution']]
values = [jour['ca'] for jour in result['evolution']]
```

### Exemple 3: Top 10 articles

```python
from kpis.utils.calcul_ca import calcul_ca_par_article
from datetime import date, timedelta

# Top 10 des 30 derniers jours
aujourd_hui = date.today()
il_y_a_30j = aujourd_hui - timedelta(days=30)

top_articles = calcul_ca_par_article(
    date_debut=il_y_a_30j,
    date_fin=aujourd_hui,
    limite=10
)

for i, article in enumerate(top_articles, 1):
    print(f"{i}. {article['article_nom']}: {article['ca_formate']}")
```

---

## 🔄 Comment modifier la méthode de calcul

### Option 1: Modifier globalement

**Fichier:** `kpis/utils/calcul_ca.py`

```python
class MethodeCalculCA:
    TOTAL_COMMANDE = 'total_commande'
    SUM_PANIERS = 'sum_paniers'

    # Changer ici pour tout le système:
    METHODE_ACTIVE = SUM_PANIERS  # ← Modification ici
```

### Option 2: Modifier localement

```python
from kpis.utils.calcul_ca import calcul_ca_periode, MethodeCalculCA

# Utiliser une méthode spécifique
result = calcul_ca_periode(
    date_debut=debut,
    date_fin=fin,
    methode=MethodeCalculCA.SUM_PANIERS  # ← Surcharge locale
)
```

---

## 📝 Notes importantes

1. **États par défaut** : Seules les commandes "Livrée" sont comptabilisées
2. **Jours sans ventes** : Affichent CA = 0 (pas de trous dans les données)
3. **Gestion des erreurs** : Toutes les fonctions retournent une structure valide même en cas d'erreur
4. **Performance** : Les requêtes sont optimisées avec des annotations Django

---

## ✅ Checklist de migration

- [ ] Lire cette documentation
- [ ] Tester les fonctions dans `views_ventes_NEW.py`
- [ ] Comparer les résultats avec l'ancienne version
- [ ] Choisir la méthode de calcul appropriée
- [ ] Remplacer l'ancien code dans `views_ventes.py`
- [ ] Mettre à jour les URLs si nécessaire
- [ ] Tester en production

---

## 🆘 Support

En cas de problème:
1. Vérifier les logs avec `logger.error()`
2. Vérifier la méthode de calcul active
3. Vérifier que les états sont correctement nommés
4. Vérifier les dates (format date, pas datetime)

---

**Version:** 1.0.0
**Dernière mise à jour:** Décembre 2024
**Auteur:** Équipe Yoozak
