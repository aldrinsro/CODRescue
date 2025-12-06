# Module Common - Utilitaires réutilisables

Ce module contient des utilitaires génériques réutilisables dans toute l'application.

## 📅 Date Utils (`date_utils.py`)

Fonctions pour parser et rechercher des dates de manière flexible.

### Fonctions disponibles

#### `try_parse_date(value: str) -> date`

Parse une chaîne de caractères en objet `date` Python.

**Formats supportés :**
- `YYYY-MM-DD` (ISO)
- `DD/MM/YYYY`
- `DD-MM-YYYY`
- `YYYY/MM/DD`
- `DDMMYYYY` (8 chiffres)
- `YYYYMMDD` (8 chiffres)

**Exemple :**
```python
from common.date_utils import try_parse_date

date_obj = try_parse_date("2025-11-12")
date_obj = try_parse_date("12/11/2025")
date_obj = try_parse_date("12112025")
```

---

#### `parse_date_input(date_input: str) -> Tuple[date, date]`

Parse une saisie utilisateur et retourne un tuple `(date_début, date_fin)`.

**Formats supportés :**

**Dates uniques :**
```python
parse_date_input("2025-11-12")  # (2025-11-12, 2025-11-12)
```

**Plages de dates :**
```python
parse_date_input("2025-11-01 - 2025-11-10")  # (2025-11-01, 2025-11-10)
parse_date_input("2025-11-01 to 2025-11-10")  # (2025-11-01, 2025-11-10)
```

**Mois complet :**
```python
parse_date_input("2025-11")  # (2025-11-01, 2025-11-30)
```

**Expressions naturelles (FR/EN) :**
```python
parse_date_input("aujourd'hui")         # Aujourd'hui
parse_date_input("hier")                # Hier
parse_date_input("cette semaine")       # Du lundi à aujourd'hui
parse_date_input("7 derniers jours")    # 7 derniers jours
parse_date_input("30 derniers jours")   # 30 derniers jours
parse_date_input("ce mois")             # Du 1er à aujourd'hui
parse_date_input("le mois dernier")     # Tout le mois précédent
```

---

#### `search_by_date(model_class, date_input: str, field: str) -> QuerySet`

Fonction générique pour filtrer n'importe quel modèle Django par date.

**Paramètres :**
- `model_class` : La classe du modèle Django
- `date_input` : Saisie utilisateur (voir formats ci-dessus)
- `field` : Nom du champ de date à filtrer

**Retourne :** QuerySet Django filtré (non-évalué)

---

### Exemples d'utilisation

#### Pour le modèle Commande

```python
from common.date_utils import search_by_date
from commande.models import Commande

# Recherche par date unique
commandes = search_by_date(Commande, "2025-11-12")

# Recherche par plage
commandes = search_by_date(Commande, "2025-11-01 - 2025-11-10")

# Recherche par expression naturelle
commandes = search_by_date(Commande, "cette semaine")
commandes = search_by_date(Commande, "7 derniers jours")

# Recherche sur un champ spécifique
commandes = search_by_date(Commande, "hier", field="date_modification")
```

#### Pour le modèle Livraison

```python
from common.date_utils import search_by_date
from livraison.models import Livraison

# Livraisons d'aujourd'hui
livraisons = search_by_date(Livraison, "aujourd'hui", field="date_livraison")

# Livraisons du mois
livraisons = search_by_date(Livraison, "ce mois", field="date_livraison")
```

#### Créer des utilitaires spécifiques

Vous pouvez créer des wrappers spécifiques dans les modules de votre application :

**Exemple : `livraison/utils.py`**
```python
from django.db.models import QuerySet
from common.date_utils import search_by_date
from .models import Livraison

def search_livraisons_by_date(date_input: str, field: str = 'date_livraison') -> QuerySet:
    """Recherche des livraisons par date."""
    return search_by_date(Livraison, date_input, field)
```

---

### Intégration dans les vues

#### Vue AJAX
```python
from django.http import JsonResponse
from common.date_utils import search_by_date
from .models import MonModele

def ajax_search_by_date(request):
    date_input = request.GET.get('date', '').strip()
    try:
        qs = search_by_date(MonModele, date_input, field='date_creation')
        results = [{'id': obj.id, 'date': str(obj.date_creation)} for obj in qs[:100]]
        return JsonResponse({'ok': True, 'results': results})
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
```

#### Vue classique
```python
from django.shortcuts import render
from common.date_utils import search_by_date
from .models import MonModele

def liste_filtree(request):
    date_filter = request.GET.get('date', 'cette semaine')
    try:
        objets = search_by_date(MonModele, date_filter)
        return render(request, 'liste.html', {'objets': objets})
    except ValueError:
        # Fallback si le format est invalide
        objets = MonModele.objects.all()
        return render(request, 'liste.html', {'objets': objets, 'error': 'Format de date invalide'})
```

---

## Configuration

Pour utiliser ce module, assurez-vous qu'il est ajouté dans `INSTALLED_APPS` de votre `settings.py` :

```python
INSTALLED_APPS = [
    # ...
    'common',
    # ...
]
```

---

## Avantages

- **Réutilisable** : Fonctionne avec tous les modèles Django
- **Flexible** : Supporte de nombreux formats de saisie
- **Bilingue** : Expressions naturelles en français et anglais
- **Robuste** : Gestion d'erreurs et fallbacks
- **Lazy** : Retourne des QuerySets non-évalués pour la performance
- **DRY** : Une seule implémentation pour toute l'application
