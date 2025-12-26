# 📦 Gestion des Frais de Livraison dans le CA

## Vue d'ensemble

Le système calcule maintenant le **CA Net** (Chiffre d'Affaires hors frais de livraison) pour avoir une vision plus précise de la performance commerciale réelle.

---

## 🎯 Pourquoi calculer le CA sans les frais de livraison ?

### Avantages métier

✅ **Vision réelle du CA produits** : Séparer le CA des produits des frais logistiques
✅ **Analyse de marge plus précise** : Les frais de livraison ne sont pas de la marge produit
✅ **Comparaison objective** : Comparer les performances sans biais des frais de transport
✅ **Pilotage commercial** : Se concentrer sur la valeur réelle des ventes

### Exemple concret

```
Commande #12345:
  - Articles : 500 DH
  - Frais de livraison : 30 DH
  - Total facturé : 530 DH

→ CA Net affiché : 500 DH (sans les 30 DH de frais)
→ CA Brut : 530 DH (avec frais)
```

---

## 🔧 Comment ça fonctionne ?

### 1. Stockage dans la base de données

**Modèle `Commande` (ligne 90):**
```python
frais_livraison = models.BooleanField(default=True)  # Indique si la commande a des frais
```

**Modèle `Ville`:**
```python
frais_livraison = models.FloatField()  # Montant des frais par ville
```

### 2. Calcul automatique

**Fichier:** `kpis/utils/calcul_ca.py`

**Méthode active (ligne 35):**
```python
METHODE_ACTIVE = TOTAL_SANS_FRAIS
```

**Logique de calcul (lignes 98-111):**
```python
elif methode == MethodeCalculCA.TOTAL_SANS_FRAIS:
    from django.db.models import Case, When, F, Value, FloatField

    queryset_annote = queryset.annotate(
        frais=Case(
            When(frais_livraison=True, ville__isnull=False,
                 then=F('ville__frais_livraison')),
            default=Value(0),
            output_field=FloatField()
        ),
        ca_sans_frais=F('total_cmd') - F('frais')
    )
    ca_total = queryset_annote.aggregate(total=Sum('ca_sans_frais'))['total'] or 0
```

**Explication:**
1. Pour chaque commande, on récupère les frais de livraison de la ville
2. Si `frais_livraison = True` → on déduit les frais
3. Si `frais_livraison = False` → frais = 0
4. CA Net = `total_cmd` - `frais`

---

## 🎨 Affichage dans l'interface

### Modifications visuelles

**Fichier:** `templates/kpis/tabs/ventes.html`

#### 1. Badge dans l'en-tête
```html
<span class="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700">
  <i class="fas fa-info-circle"></i>
  <span>CA Net (HT Livraison)</span>
</span>
```

#### 2. Badge sur la carte CA
```html
<div class="absolute top-2 right-2">
  <span class="px-2 py-1 bg-blue-50 text-blue-600 text-[10px]"
        title="Chiffre d'affaires calculé hors frais de livraison">
    <i class="fas fa-calculator"></i>
    <span>HT Livraison</span>
  </span>
</div>
```

#### 3. Titre modifié
- **Avant:** "CA Total"
- **Après:** "CA Net"

#### 4. Sous-titre explicatif
```html
<p class="text-xs text-gray-500">Ce mois (hors frais livraison)</p>
```

---

## 📊 Méthodes de calcul disponibles

Le système propose **3 méthodes** de calcul du CA :

| Méthode | Description | Usage |
|---------|-------------|-------|
| `TOTAL_COMMANDE` | Somme des `total_cmd` (avec frais) | CA Brut total facturé |
| `SUM_PANIERS` | Somme des `sous_total` des paniers | CA détaillé par article |
| `TOTAL_SANS_FRAIS` ✅ | `total_cmd` - frais de livraison | **CA Net (actif)** |

---

## 🔄 Comment changer de méthode ?

### Modification rapide

**Fichier:** `kpis/utils/calcul_ca.py` (ligne 35)

```python
# Pour revenir au CA Brut (avec frais)
METHODE_ACTIVE = TOTAL_COMMANDE

# Pour utiliser le CA Net (sans frais) - RECOMMANDÉ
METHODE_ACTIVE = TOTAL_SANS_FRAIS

# Pour utiliser la somme des paniers
METHODE_ACTIVE = SUM_PANIERS
```

**Résultat:** Tous les KPIs utiliseront automatiquement la nouvelle méthode !

---

## 📈 Impact sur les KPIs

### KPIs affectés

| KPI | Impact | Note |
|-----|--------|------|
| **CA Période** | ✅ Calculé sans frais | CA Net affiché |
| **Panier Moyen** | ✅ Calculé sans frais | Montant moyen réel des produits |
| **Nb Commandes** | ❌ Pas d'impact | Nombre inchangé |
| **Évolution CA** | ✅ Calculé sans frais | Tendances basées sur CA Net |
| **Top Modèles** | ❌ Déjà basé sur paniers | Pas de frais dans les paniers |
| **Top Régions** | ✅ Calculé sans frais | CA Net par région |

---

## 🧪 Tests et Vérification

### Vérifier le calcul

**Test manuel dans Django shell:**
```python
from kpis.utils.calcul_ca import calcul_ca_periode, MethodeCalculCA
from datetime import date

# Calculer le CA Net
result_net = calcul_ca_periode(
    date_debut=date(2024, 12, 1),
    date_fin=date(2024, 12, 31),
    methode=MethodeCalculCA.TOTAL_SANS_FRAIS
)

# Calculer le CA Brut
result_brut = calcul_ca_periode(
    date_debut=date(2024, 12, 1),
    date_fin=date(2024, 12, 31),
    methode=MethodeCalculCA.TOTAL_COMMANDE
)

print(f"CA Net (HT Livraison): {result_net['ca_total']:,.2f} DH")
print(f"CA Brut (TTC): {result_brut['ca_total']:,.2f} DH")
print(f"Frais de livraison totaux: {result_brut['ca_total'] - result_net['ca_total']:,.2f} DH")
```

### Résultat attendu
```
CA Net (HT Livraison): 125,430.00 DH
CA Brut (TTC): 129,850.00 DH
Frais de livraison totaux: 4,420.00 DH
```

---

## 🎓 Cas d'usage

### Cas 1 : Commande avec frais

```python
Commande #001:
  frais_livraison = True
  ville = Casablanca (frais: 30 DH)
  total_cmd = 530 DH

→ CA Net = 530 - 30 = 500 DH ✅
```

### Cas 2 : Commande sans frais (promotion)

```python
Commande #002:
  frais_livraison = False  # Client VIP, livraison offerte
  ville = Rabat (frais: 35 DH)
  total_cmd = 450 DH

→ CA Net = 450 - 0 = 450 DH ✅
```

### Cas 3 : Commande sans ville

```python
Commande #003:
  frais_livraison = True
  ville = None
  total_cmd = 600 DH

→ CA Net = 600 - 0 = 600 DH ✅
```

---

## 🚀 Avantages de cette implémentation

### Pour le business

✅ **Transparence** : Séparation claire entre CA produits et frais logistiques
✅ **Décisions éclairées** : Analyse de performance basée sur les ventes réelles
✅ **Optimisation des prix** : Ajuster les prix sans être biaisé par les frais de livraison
✅ **Comparaisons fiables** : Comparer les performances entre périodes/régions équitablement

### Pour les développeurs

✅ **Flexible** : 3 méthodes de calcul disponibles
✅ **Configurable** : Changement de méthode en 1 ligne
✅ **Réutilisable** : Fonctions isolées dans `calcul_ca.py`
✅ **Maintenable** : Code clair et bien documenté

---

## 📝 Notes importantes

### Données requises

Pour que le calcul fonctionne correctement :

1. ✅ Chaque ville doit avoir un `frais_livraison` défini
2. ✅ Chaque commande doit être liée à une ville
3. ✅ Le champ `frais_livraison` (boolean) doit être correctement renseigné

### Comportement par défaut

- Si `ville` est `None` → frais = 0 DH
- Si `frais_livraison` = `False` → frais = 0 DH
- Si `frais_livraison` = `True` et `ville` existe → frais = `ville.frais_livraison`

---

## 🔍 Références

- **Code backend:** `kpis/utils/calcul_ca.py` (lignes 31-35, 98-111)
- **Modèles:** `commande/models.py` (ligne 90, 311-314)
- **Interface:** `templates/kpis/tabs/ventes.html` (lignes 11-14, 48-52)
- **Documentation:** `kpis/utils/README_CALCUL_CA.md`

---

**Version:** 1.0.0
**Date:** Décembre 2024
**Statut:** ✅ En production
