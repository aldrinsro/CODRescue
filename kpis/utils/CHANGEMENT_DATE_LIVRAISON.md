# 📅 Changement: Utilisation de la Date de Livraison

**Date:** 4 Décembre 2025
**Impact:** ⚠️ **MAJEUR** - Modifie la logique de calcul de tous les KPIs Ventes
**Statut:** ✅ Implémenté

---

## 🎯 Objectif du Changement

### ❌ Avant
Le système calculait les KPIs en se basant sur la **date de création de la commande** (`date_cmd`).

**Problème:** Une commande créée le 1er décembre mais livrée le 15 décembre était comptabilisée dans le CA du 1er décembre.

### ✅ Après
Le système calcule les KPIs en se basant sur la **date de livraison** (`etats__date_debut` de l'état "Livrée").

**Avantage:** Une commande livrée le 15 décembre est comptabilisée dans le CA du 15 décembre, ce qui reflète la **réalité commerciale**.

---

## 📊 Impact sur les KPIs

| KPI | Impact | Explication |
|-----|--------|-------------|
| **CA Période** | ✅ Modifié | Basé sur la date de livraison |
| **Panier Moyen** | ✅ Modifié | Calculé sur commandes livrées dans la période |
| **Nb Commandes** | ✅ Modifié | Compte les livraisons dans la période |
| **Top Modèles** | ✅ Modifié | Ventes comptabilisées à la date de livraison |
| **Top Régions** | ✅ Modifié | CA régional basé sur date de livraison |
| **Évolution CA** | ✅ Modifié | Graphique par date de livraison |
| **Commande Max** | ✅ Modifié | Commande max livrée dans la période |

---

## 🔧 Modifications Techniques

### 1. Fichier `kpis/utils/calcul_ca.py`

#### Fonction `calcul_ca_periode()` (lignes 77-87)

**Avant:**
```python
queryset = Commande.objects.filter(
    date_cmd__gte=date_debut,
    date_cmd__lte=date_fin
)

if etats_inclus:
    etat_filter = Q()
    for etat in etats_inclus:
        etat_filter |= Q(etats__enum_etat__libelle__iexact=etat)
    queryset = queryset.filter(etat_filter)
```

**Après:**
```python
# Creer un filtre OR pour tous les etats avec leurs dates
etat_filter = Q()
for etat in etats_inclus:
    etat_filter |= Q(
        etats__enum_etat__libelle__iexact=etat,
        etats__date_debut__gte=date_debut,
        etats__date_debut__lte=date_fin
    )

queryset = Commande.objects.filter(etat_filter)
```

**Changement clé:** Le filtre de date est maintenant **intégré avec le filtre d'état**, utilisant `etats__date_debut`.

---

#### Fonction `calcul_ca_journalier()` (lignes 243-293)

**Avant:**
```python
queryset = Commande.objects.filter(
    date_cmd__gte=date_debut,
    date_cmd__lte=date_fin
)

# ...

commandes_par_jour = queryset.extra(
    select={'date_seule': 'DATE(date_cmd)'}
).values('date_seule').annotate(
    ca_jour=Sum('total_cmd')
).order_by('date_seule')
```

**Après:**
```python
etat_filter = Q()
for etat in etats_inclus:
    etat_filter |= Q(
        etats__enum_etat__libelle__iexact=etat,
        etats__date_debut__gte=date_debut,
        etats__date_debut__lte=date_fin
    )

queryset = Commande.objects.filter(etat_filter)

# ...

commandes_par_jour = queryset.extra(
    select={'date_seule': 'DATE(etats.date_debut)'},
    tables=['commande_etatcommande AS etats'],
    where=['commande_commande.id = etats.commande_id']
).values('date_seule').annotate(
    ca_jour=Sum('total_cmd')
).order_by('date_seule')
```

**Changement clé:**
1. Filtre par `etats__date_debut` au lieu de `date_cmd`
2. Groupe par `DATE(etats.date_debut)` au lieu de `DATE(date_cmd)`

---

#### Fonction `calcul_ca_par_article()` (lignes 396-406)

**Avant:**
```python
etat_filter = Q()
for etat in etats_inclus:
    etat_filter |= Q(
        paniers__commande__etats__enum_etat__libelle__iexact=etat
    )

articles = Article.objects.filter(
    paniers__commande__date_cmd__gte=date_debut,
    paniers__commande__date_cmd__lte=date_fin
).filter(etat_filter).annotate(...)
```

**Après:**
```python
etat_filter = Q()
for etat in etats_inclus:
    etat_filter |= Q(
        paniers__commande__etats__enum_etat__libelle__iexact=etat,
        paniers__commande__etats__date_debut__gte=date_debut,
        paniers__commande__etats__date_debut__lte=date_fin
    )

articles = Article.objects.filter(etat_filter).annotate(...)
```

**Changement clé:** Filtre directement par `etats__date_debut` dans le Q object.

---

#### Fonction `calcul_ca_par_region()` (lignes 478-496)

**Avant:**
```python
queryset = Commande.objects.filter(
    date_cmd__gte=date_debut,
    date_cmd__lte=date_fin,
    ville__isnull=False,
    ville__region__isnull=False
)

if 'etats_exclus' in locals():
    for etat in etats_exclus:
        queryset = queryset.exclude(
            etats__enum_etat__libelle__iexact=etat
        )
```

**Après:**
```python
etat_filter = Q()
for etat in etats_inclus:
    etat_filter |= Q(
        etats__enum_etat__libelle__iexact=etat,
        etats__date_debut__gte=date_debut,
        etats__date_debut__lte=date_fin
    )

queryset = Commande.objects.filter(
    etat_filter,
    ville__isnull=False,
    ville__region__isnull=False
)
```

**Changement clé:** Utilise `etats_inclus` (whitelist) au lieu de `etats_exclus` (blacklist) + filtre par date de livraison.

---

### 2. Fichier `kpis/views_ventes.py`

#### Fonction `ventes_data()` - Commande Max (lignes 131-136)

**Avant:**
```python
commande_max = Commande.objects.filter(
    date_cmd__gte=debut_periode,
    date_cmd__lte=fin_periode
).filter(
    Q(etats__enum_etat__libelle__iexact='Livrée') |
    Q(etats__enum_etat__libelle__iexact='Livrée Partiellement')
).aggregate(max_cmd=Max('total_cmd'))['max_cmd'] or 0
```

**Après:**
```python
commande_max = Commande.objects.filter(
    Q(etats__enum_etat__libelle__iexact='Livrée',
      etats__date_debut__gte=debut_periode,
      etats__date_debut__lte=fin_periode) |
    Q(etats__enum_etat__libelle__iexact='Livrée Partiellement',
      etats__date_debut__gte=debut_periode,
      etats__date_debut__lte=fin_periode)
).aggregate(max_cmd=Max('total_cmd'))['max_cmd'] or 0
```

---

#### Fonction `top_modeles_data()` (lignes 310-336)

**Avant:**
```python
top_modeles = Article.objects.annotate(
    ca_total=Sum(
        'paniers__sous_total',
        filter=Q(
            paniers__commande__date_cmd__gte=debut_date,
            paniers__commande__date_cmd__lte=fin_date,
            paniers__commande__etats__date_fin__isnull=False
        ) & (
            Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée') |
            Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée Partiellement')
        )
    ),
    # ... même logique pour nb_ventes
)
```

**Après:**
```python
top_modeles = Article.objects.annotate(
    ca_total=Sum(
        'paniers__sous_total',
        filter=Q(
            paniers__commande__etats__date_debut__gte=debut_date,
            paniers__commande__etats__date_debut__lte=fin_date,
            paniers__commande__etats__date_fin__isnull=False
        ) & (
            Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée') |
            Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée Partiellement')
        )
    ),
    # ... même logique pour nb_ventes
)
```

---

## 📋 Exemple Concret

### Scénario

```
Commande #12345
├─ Date création (date_cmd): 2024-12-01
├─ État: "En préparation" du 01/12 au 10/12
├─ État: "Expédiée" du 10/12 au 14/12
└─ État: "Livrée" (date_debut): 2024-12-15
   └─ Montant: 500 DH
```

### Impact sur les KPIs

#### CA du 1-7 Décembre

**Avant (date_cmd):**
- ✅ Commande #12345 incluse (créée le 01/12)
- CA = 500 DH

**Après (date livraison):**
- ❌ Commande #12345 NON incluse (livrée le 15/12)
- CA = 0 DH

#### CA du 15-21 Décembre

**Avant (date_cmd):**
- ❌ Commande #12345 NON incluse (créée le 01/12)
- CA = 0 DH

**Après (date livraison):**
- ✅ Commande #12345 incluse (livrée le 15/12)
- CA = 500 DH

---

## ✅ Avantages du Changement

### 1. Réalité Commerciale
Le CA est comptabilisé **au moment où le client reçoit effectivement ses produits**, pas au moment de la prise de commande.

### 2. Cohérence Comptable
Correspond mieux aux principes comptables de **reconnaissance du revenu** à la livraison.

### 3. Analyse Plus Précise
Les pics de CA correspondent aux **pics de livraison**, pas aux pics de commande.

### 4. Délais de Livraison Visibles
Un décalage entre commandes et livraisons devient visible dans les KPIs.

---

## ⚠️ Points d'Attention

### 1. Données Historiques
Les périodes passées seront **recalculées** avec la nouvelle logique lors du prochain chargement.

### 2. Comparaisons avec Anciennes Captures
Les captures d'écran des KPIs prises avant ce changement peuvent montrer des valeurs **différentes** pour les mêmes périodes.

### 3. Commandes en Transit
Les commandes créées mais **pas encore livrées** ne seront **pas comptabilisées** dans le CA tant qu'elles ne sont pas livrées.

---

## 🧪 Tests Recommandés

### Test 1: Vérification Date de Livraison
```sql
-- Dans Django shell
from commande.models import Commande
from datetime import date

# Trouver une commande livrée
cmd = Commande.objects.filter(
    etats__enum_etat__libelle='Livrée'
).first()

print(f"Date création: {cmd.date_cmd}")
print(f"Date livraison: {cmd.etats.filter(enum_etat__libelle='Livrée').first().date_debut}")
```

### Test 2: Comparaison KPIs
1. Noter les valeurs de CA actuelles
2. Redémarrer le serveur Django
3. Vérifier que les KPIs utilisent bien la date de livraison

### Test 3: Graphique Évolution
1. Ouvrir le graphique d'évolution du CA
2. Vérifier que les pics correspondent aux **dates de livraison**
3. Comparer avec les données brutes dans la base

---

## 📁 Fichiers Modifiés

| Fichier | Fonctions Modifiées | Lignes |
|---------|---------------------|--------|
| `kpis/utils/calcul_ca.py` | `calcul_ca_periode()` | 77-87 |
| | `calcul_ca_journalier()` | 243-293 |
| | `calcul_ca_par_article()` | 396-406 |
| | `calcul_ca_par_region()` | 478-496 |
| `kpis/views_ventes.py` | `ventes_data()` (commande_max) | 131-136 |
| | `top_modeles_data()` | 310-336 |

---

## 🔄 Rollback (si nécessaire)

Pour revenir à l'ancienne logique (date_cmd), remplacer dans tous les fichiers :

```python
# NOUVELLE LOGIQUE (date de livraison)
etats__date_debut__gte=date_debut,
etats__date_debut__lte=date_fin

# PAR ANCIENNE LOGIQUE (date de commande)
date_cmd__gte=date_debut,
date_cmd__lte=date_fin
```

**Note:** Le rollback n'est **pas recommandé** car la nouvelle logique est plus correcte d'un point de vue métier.

---

## 📈 Prochaines Étapes

1. **Monitorer** les KPIs pendant 1 semaine pour valider le changement
2. **Documenter** les nouvelles valeurs comme référence
3. **Former** les utilisateurs sur la signification des nouveaux KPIs
4. **Créer** des rapports comparatifs (date commande vs date livraison)

---

**Version:** 1.0.0
**Auteur:** Claude Code
**Validation:** ⏳ En attente de tests utilisateur
