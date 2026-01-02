# 📚 Guide de Migration - Fonctions operatConfirme vers common

Ce guide détaille la migration des fonctions de `operatConfirme/views.py` vers des modules réutilisables dans `common/`.

---

## 📊 Vue d'ensemble de la Migration

### **Objectif**
Rendre réutilisables les fonctions de gestion des commandes pour qu'elles puissent être utilisées par d'autres applications (operatPrepa, OperteurSAV, etc.).

### **Structure créée**

```
common/
├── views/
│   ├── __init__.py
│   ├── commande_views.py       # Vue principale modifier_commande
│   ├── article_handlers.py     # Handlers AJAX pour articles
│   ├── operation_handlers.py   # Handlers AJAX pour opérations
│   └── livraison_handlers.py   # Handlers AJAX pour livraison
│
├── api/
│   ├── __init__.py
│   ├── article_api.py          # APIs de gestion des articles
│   ├── remise_api.py           # APIs de gestion des remises
│   └── commande_api.py         # APIs de gestion des commandes
│
└── utils/
    ├── __init__.py
    ├── upsell_utils.py         # ✅ TERMINÉ - Utilitaires compteur upsell
    └── prix_utils.py           # Utilitaires de calcul des prix
```

---

## ✅ Modules Déjà Migrés

### **1. common/utils/upsell_utils.py** - TERMINÉ

Fonctions migrées :
- ✅ `determiner_type_prix_gele(article, compteur)`
- ✅ `mettre_a_jour_types_prix_gele_upsell(commande)`
- ✅ `recalculer_remises_apres_changement_compteur(commande)`
- ✅ `recalculer_compteur_upsell(commande)`

**Utilisation :**
```python
from common.utils.upsell_utils import (
    determiner_type_prix_gele,
    recalculer_compteur_upsell
)

# Dans votre vue
type_prix = determiner_type_prix_gele(article, commande.compteur)
recalculer_compteur_upsell(commande)
```

---

## 📋 Modules à Migrer

### **2. common/views/article_handlers.py** - À FAIRE

**Fonctions à migrer depuis operatConfirme/views.py :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 1813 | `_handle_add_article(request, commande, operateur)` | Ajoute un article à la commande |
| 1981 | `_handle_delete_panier(request, commande, operateur)` | Supprime un article du panier |
| 2098 | `_handle_update_quantity(request, commande, operateur)` | Modifie la quantité d'un article |

**Structure proposée :**
```python
"""
Module de handlers pour la gestion des articles dans les commandes.
"""

def handle_add_article(request, commande, operateur=None):
    \"\"\"Handler générique pour ajout d'article\"\"\"
    # Code de _handle_add_article
    pass

def handle_delete_article(request, commande, operateur=None):
    \"\"\"Handler générique pour suppression d'article\"\"\"
    # Code de _handle_delete_panier
    pass

def handle_update_quantity(request, commande, operateur=None):
    \"\"\"Handler générique pour modification de quantité\"\"\"
    # Code de _handle_update_quantity
    pass
```

---

### **3. common/views/operation_handlers.py** - À FAIRE

**Fonctions à migrer depuis operatConfirme/views.py :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 2258 | `_handle_update_operation(request, commande, operateur)` | Modifie une opération |
| 2338 | `_handle_create_operation(request, commande, operateur)` | Crée une opération |
| 2412 | `_handle_delete_operation(request, commande, operateur)` | Supprime une opération |

---

### **4. common/views/livraison_handlers.py** - À FAIRE

**Fonctions à migrer depuis operatConfirme/views.py :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 2055 | `_handle_save_client_info(request, commande, operateur)` | Sauvegarde infos client |
| 2497 | `_handle_save_livraison(request, commande, operateur)` | Sauvegarde infos livraison |
| 2572 | `_handle_toggle_frais_livraison(request, commande, operateur)` | Active/désactive frais |

---

### **5. common/api/article_api.py** - À FAIRE

**Fonctions à migrer depuis operatConfirme/views.py :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 2997 | `api_articles_disponibles(request)` | Liste articles disponibles |
| 3683 | `get_article_variants(request, article_id)` | Récupère variantes d'un article |
| 3459 | `rafraichir_articles_section(request, commande_id)` | Rafraîchit section articles |

**Structure proposée :**
```python
"""
APIs pour la gestion des articles.
"""

def get_articles_disponibles(request, filtre=None):
    \"\"\"API générique - Liste articles disponibles\"\"\"
    pass

def get_article_variants(request, article_id):
    \"\"\"API générique - Récupère variantes\"\"\"
    pass

def rafraichir_articles_section(request, commande_id, template_path=None):
    \"\"\"API générique - Rafraîchit section articles\"\"\"
    pass
```

---

### **6. common/api/remise_api.py** - À FAIRE

**Fonctions à migrer depuis operatConfirme/views.py :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 3761 | `appliquer_remise_panier(request, panier_id)` | Applique une remise |
| 3923 | `retirer_remise_panier(request, panier_id)` | Retire une remise |
| 4019 | `calculer_remise_panier_preview(request, panier_id)` | Aperçu remise |

**Structure proposée :**
```python
"""
APIs pour la gestion des remises personnalisées.
"""

def appliquer_remise(request, panier_id):
    \"\"\"API générique - Applique une remise\"\"\"
    pass

def retirer_remise(request, panier_id):
    \"\"\"API générique - Retire une remise\"\"\"
    pass

def calculer_remise_preview(request, panier_id):
    \"\"\"API générique - Aperçu de remise\"\"\"
    pass
```

---

### **7. common/views/commande_views.py** - À FAIRE

**Fonction principale à migrer :**

| Ligne | Fonction | Description |
|-------|----------|-------------|
| 2631 | `modifier_commande(request, commande_id)` | Vue principale de modification |

**Structure proposée :**
```python
"""
Vue principale de modification de commande (générique).
"""

def modifier_commande_generic(
    request,
    commande_id,
    operateur_type='CONFIRMATION',
    success_redirect='operatConfirme:confirmation',
    template_name='common/commande/modifier_commande.html'
):
    \"\"\"
    Vue générique de modification de commande.

    Args:
        request: HttpRequest
        commande_id: ID de la commande
        operateur_type: Type d'opérateur (CONFIRMATION, PREPARATION, SAV)
        success_redirect: URL de redirection après succès
        template_name: Template à utiliser
    \"\"\"
    # Code de modifier_commande adapté
    pass
```

---

## 🔧 Étapes de Migration

### **Étape 1 : Copier le code source**

Pour chaque fonction, copier le code depuis `operatConfirme/views.py` vers le module approprié.

### **Étape 2 : Rendre générique**

Modifier le code pour le rendre réutilisable :

**Avant (spécifique) :**
```python
def _handle_add_article(request, commande, operateur):
    # Vérifie que l'opérateur est de type CONFIRMATION
    if operateur.type_operateur != 'CONFIRMATION':
        return JsonResponse({'error': 'Non autorisé'})
    # ...
```

**Après (générique) :**
```python
def handle_add_article(request, commande, operateur=None):
    # Pas de vérification spécifique au type d'opérateur
    # La vérification est faite dans la vue appelante si nécessaire
    # ...
```

### **Étape 3 : Utiliser les imports relatifs**

**Avant :**
```python
from operatConfirme.views import _recalculer_compteur_upsell
```

**Après :**
```python
from common.utils.upsell_utils import recalculer_compteur_upsell
```

### **Étape 4 : Paramétrer les redirections**

**Avant :**
```python
return redirect('operatConfirme:confirmation')
```

**Après :**
```python
return redirect(success_redirect)  # Paramètre passé à la fonction
```

### **Étape 5 : Paramétrer les templates**

**Avant :**
```python
template = 'operatConfirme/modifier_commande.html'
```

**Après :**
```python
template = template_name  # Paramètre avec défaut
```

---

## 💡 Exemple Complet de Migration

### **Fonction originale** (operatConfirme/views.py ligne 1813)

```python
def _handle_add_article(request, commande, operateur):
    from commande.models import Panier
    from article.models import Article

    article_id = request.POST.get('article_id')
    article = Article.objects.get(id=article_id)

    # ... logique métier ...

    _recalculer_compteur_upsell(commande)

    return JsonResponse({'success': True})
```

### **Fonction migrée** (common/views/article_handlers.py)

```python
from common.utils.upsell_utils import recalculer_compteur_upsell

def handle_add_article(request, commande, operateur=None):
    \"\"\"
    Handler générique pour l'ajout d'un article.

    Args:
        request: HttpRequest
        commande: Instance de Commande
        operateur: Instance d'Operateur (optionnel)

    Returns:
        JsonResponse
    \"\"\"
    from commande.models import Panier
    from article.models import Article

    article_id = request.POST.get('article_id')
    article = Article.objects.get(id=article_id)

    # ... même logique métier ...

    recalculer_compteur_upsell(commande)  # Import depuis common

    return JsonResponse({'success': True})
```

---

## 🚀 Utilisation dans operatConfirme

Une fois les modules migrés, mettre à jour `operatConfirme/views.py` :

**Avant :**
```python
def modifier_commande(request, commande_id):
    # ... tout le code ici ...

def _handle_add_article(request, commande, operateur):
    # ... tout le code ici ...
```

**Après :**
```python
from common.views import article_handlers
from common.utils.upsell_utils import recalculer_compteur_upsell

def modifier_commande(request, commande_id):
    # ... code réduit ...

    if action == 'add_article':
        return article_handlers.handle_add_article(request, commande, operateur)
```

---

## 📝 Checklist de Migration

- [x] Créer la structure `common/views/`, `common/api/`, `common/utils/`
- [x] Migrer `upsell_utils.py` - ✅ TERMINÉ
- [ ] Migrer `article_handlers.py`
- [ ] Migrer `operation_handlers.py`
- [ ] Migrer `livraison_handlers.py`
- [ ] Migrer `article_api.py`
- [ ] Migrer `remise_api.py`
- [ ] Migrer `commande_api.py`
- [ ] Migrer `commande_views.py`
- [ ] Mettre à jour `operatConfirme/views.py` pour utiliser les modules common
- [ ] Tester les fonctionnalités
- [ ] Documenter les changements

---

## 🧪 Tests Recommandés

Après chaque migration :

1. **Test unitaire** : Vérifier que la fonction migrée fonctionne isolément
2. **Test d'intégration** : Vérifier dans `operatConfirme` que tout fonctionne
3. **Test de réutilisabilité** : Essayer d'utiliser dans une autre app (ex: operatPrepa)

---

## 📞 Support

Pour toute question sur la migration :
- Consulter ce guide
- Voir les exemples dans `common/utils/upsell_utils.py`
- Lire la documentation des modules créés

---

**Version :** 1.0
**Dernière mise à jour :** 2 Janvier 2026
**Status :** Migration en cours (25% complété)
