# 🔌 Mapping AJAX - JavaScript ↔ Backend

**Date de création :** 2 Janvier 2026
**Version :** 1.0

Ce document fait le mapping complet entre tous les appels AJAX dans les fichiers JavaScript et les handlers/APIs backend correspondants.

---

## 📊 Vue d'ensemble

Les fichiers JavaScript dans `static/js/Commande/` utilisent des appels AJAX pour communiquer avec le backend. Tous les handlers et APIs nécessaires ont été migrés dans le module `common/`.

### Fichiers JavaScript
- `gestion_articles.js` - 2913 lignes
- `remise.js` - 461 lignes
- `confirmation.js` - 399 lignes
- `detail_toggle.js` - Pas d'AJAX (UI uniquement)

---

## 🔄 Mapping Complet

### **1. Gestion des Articles** (`gestion_articles.js`)

#### 1.1. Charger la liste des articles disponibles

**JavaScript (ligne 652):**
```javascript
fetch('/operateur-confirme/api/articles-disponibles/', {
    method: 'GET',
    headers: {
        'X-CSRFToken': csrfToken.value,
        'X-Requested-With': 'XMLHttpRequest',
    }
})
```

**Backend:**
- **Fichier:** `common/api/article_api.py`
- **Fonction:** `api_articles_disponibles(request)`
- **Lignes:** 39-95
- **Retour:** JSON avec liste complète des articles

**Configuration URL requise:**
```python
# Dans votre urls.py (ex: operatConfirme/urls.py, operatPrepa/urls.py)
from common.api.article_api import api_articles_disponibles

urlpatterns = [
    path('api/articles-disponibles/', api_articles_disponibles, name='api_articles_disponibles'),
]
```

---

#### 1.2. Récupérer les variantes d'un article

**JavaScript (ligne 1029):**
```javascript
fetch(`/operateur-confirme/get-article-variants/${article.id}/`, {
    method: 'GET'
})
```

**Backend:**
- **Fichier:** `common/api/article_api.py`
- **Fonction:** `get_article_variants(request, article_id)`
- **Lignes:** 98-178
- **Retour:** JSON avec liste des variantes (couleur, taille, stock)

**Configuration URL requise:**
```python
from common.api.article_api import get_article_variants

urlpatterns = [
    path('get-article-variants/<int:article_id>/', get_article_variants, name='get_article_variants'),
]
```

---

#### 1.3. Rafraîchir la section articles

**JavaScript (ligne 2040):**
```javascript
fetch(`/operateur-confirme/api/commande/${window.commandeId}/rafraichir-articles/`)
```

**Backend:**
- **Fichier:** `common/api/article_api.py`
- **Fonction:** `rafraichir_articles_section(request, commande_id, template_path=None)`
- **Lignes:** 181-258
- **Retour:** JSON avec HTML de la section + données mises à jour

**Configuration URL requise:**
```python
from common.api.article_api import rafraichir_articles_section

urlpatterns = [
    path('api/commande/<int:commande_id>/rafraichir-articles/', rafraichir_articles_section, name='rafraichir_articles'),
]
```

---

#### 1.4. Ajouter un article

**JavaScript (ligne 1990):**
```javascript
const formData = new FormData();
formData.append('action', 'add_article');
formData.append('article_id', articleId);
formData.append('quantite', quantite);
formData.append('variante_id', varianteId); // optionnel

fetch(modifierArticle, {  // URL: /operateur-confirme/commandes/{id}/modifier/
    method: 'POST',
    body: formData
})
```

**Backend:**
- **Fichier:** `common/views/article_handlers.py`
- **Fonction:** `handle_add_article(request, commande, operateur=None)`
- **Lignes:** 34-218
- **Retour:** JSON avec status et données de l'article ajouté

**Configuration requise (dans votre vue principale):**
```python
from common.views.article_handlers import handle_add_article

def modifier_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    operateur = get_operateur(request)  # Votre fonction

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_article':
            return handle_add_article(request, commande, operateur)
        # ... autres actions
```

---

#### 1.5. Supprimer un article

**JavaScript (ligne 2357):**
```javascript
const formData = new FormData();
formData.append('action', 'delete_panier');
formData.append('panier_id', panierId);

fetch(modifierArticle, {
    method: 'POST',
    body: formData
})
```

**Backend:**
- **Fichier:** `common/views/article_handlers.py`
- **Fonction:** `handle_delete_article(request, commande, operateur=None)`
- **Lignes:** 221-333
- **Retour:** JSON avec status et données mise à jour

**Configuration requise (dans votre vue principale):**
```python
from common.views.article_handlers import handle_delete_article

if action == 'delete_panier':
    return handle_delete_article(request, commande, operateur)
```

---

#### 1.6. Modifier la quantité d'un article

**JavaScript (lignes 2578, 2782):**
```javascript
const formData = new FormData();
formData.append('action', 'update_quantity');
formData.append('panier_id', panierId);
formData.append('nouvelle_quantite', nouvelleQuantite);

fetch(modifierArticle, {
    method: 'POST',
    body: formData
})
```

**Backend:**
- **Fichier:** `common/views/article_handlers.py`
- **Fonction:** `handle_update_quantity(request, commande, operateur=None)`
- **Lignes:** 336-482
- **Retour:** JSON avec status et données mise à jour

**Configuration requise (dans votre vue principale):**
```python
from common.views.article_handlers import handle_update_quantity

if action == 'update_quantity':
    return handle_update_quantity(request, commande, operateur)
```

---

### **2. Gestion des Remises** (`remise.js`)

#### 2.1. Aperçu de remise (preview)

**JavaScript (ligne 95):**
```javascript
fetch(`/operateur-confirme/calculer-remise-preview/${panierId}/?type_remise=${typeRemise}&valeur_remise=${valeurRemise}`)
```

**Backend:**
- **Fichier:** `common/api/remise_api.py`
- **Fonction:** `calculer_remise_panier_preview(request, panier_id)`
- **Lignes:** 238-321
- **Retour:** JSON avec calculs de remise sans application

**Configuration URL requise:**
```python
from common.api.remise_api import calculer_remise_panier_preview

urlpatterns = [
    path('calculer-remise-preview/<int:panier_id>/', calculer_remise_panier_preview, name='calculer_remise_preview'),
]
```

---

#### 2.2. Appliquer une remise

**JavaScript (ligne 184):**
```javascript
fetch(`/operateur-confirme/appliquer-remise/${panierId}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        type_remise: 'POURCENTAGE',
        valeur_remise: valeurRemise,
        raison_remise: raisonRemise
    })
})
```

**Backend:**
- **Fichier:** `common/api/remise_api.py`
- **Fonction:** `appliquer_remise_panier(request, panier_id, operateur=None)`
- **Lignes:** 37-167
- **Retour:** JSON avec status et nouveaux totaux

**Configuration URL requise:**
```python
from common.api.remise_api import appliquer_remise_panier

urlpatterns = [
    path('appliquer-remise/<int:panier_id>/', appliquer_remise_panier, name='appliquer_remise'),
]
```

**⚠️ Note importante:** Si vous utilisez cette API directement dans les URLs (pas dans une vue), vous devrez passer l'opérateur via un wrapper :

```python
# Option 1: Wrapper pour injecter l'opérateur
def appliquer_remise_wrapper(request, panier_id):
    operateur = get_object_or_404(Operateur, user=request.user)
    return appliquer_remise_panier(request, panier_id, operateur)

urlpatterns = [
    path('appliquer-remise/<int:panier_id>/', appliquer_remise_wrapper, name='appliquer_remise'),
]

# Option 2: Dans une vue principale (recommandé)
def gerer_remises(request, panier_id):
    operateur = get_operateur(request)
    return appliquer_remise_panier(request, panier_id, operateur)
```

---

#### 2.3. Retirer une remise

**JavaScript (ligne 235):**
```javascript
fetch(`/operateur-confirme/retirer-remise/${panierId}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    }
})
```

**Backend:**
- **Fichier:** `common/api/remise_api.py`
- **Fonction:** `retirer_remise_panier(request, panier_id, operateur=None)`
- **Lignes:** 170-235
- **Retour:** JSON avec status et totaux restaurés

**Configuration URL requise:**
```python
from common.api.remise_api import retirer_remise_panier

urlpatterns = [
    path('retirer-remise/<int:panier_id>/', retirer_remise_panier, name='retirer_remise'),
]
```

---

### **3. Confirmation de Commande** (`confirmation.js`)

⚠️ **IMPORTANT:** Les endpoints de confirmation sont **spécifiques à chaque application** (operatConfirme, operatPrepa, etc.) et ne doivent **PAS être migrés** dans `common/`.

Ces fonctions gèrent des workflows métier spécifiques et des changements d'état de commande propres à chaque type d'opérateur.

#### 3.1. Confirmer une commande

**JavaScript (ligne 103):**
```javascript
fetch(`/operateur-confirme/commandes/${commandeId}/confirmer-ajax/`, {
    method: 'POST'
})
```

**Backend:**
- ❌ **Non migré** - Reste dans `operatConfirme/views.py`
- Raison: Gère le workflow spécifique de confirmation

---

#### 3.2. Lancer la confirmation

**JavaScript (ligne 257):**
```javascript
fetch(`/operateur-confirme/commandes/${commandeId}/lancer-confirmation/`, {
    method: 'POST'
})
```

**Backend:**
- ❌ **Non migré** - Reste dans `operatConfirme/views.py`
- Raison: Gère le workflow spécifique de confirmation

---

#### 3.3. Annuler une commande

**JavaScript (ligne 388):**
```javascript
fetch(`/operateur-confirme/commandes/${commandeId}/annuler-confirmation/`, {
    method: 'POST'
})
```

**Backend:**
- ❌ **Non migré** - Reste dans `operatConfirme/views.py`
- Raison: Gère le workflow spécifique d'annulation

---

## 📋 Résumé des Handlers/APIs Disponibles

### **Handlers (dans les vues)** - `common/views/`

| Fonction | Fichier | Action JS | Description |
|----------|---------|-----------|-------------|
| `handle_add_article()` | `article_handlers.py` | `add_article` | Ajoute article au panier |
| `handle_delete_article()` | `article_handlers.py` | `delete_panier` | Supprime article |
| `handle_update_quantity()` | `article_handlers.py` | `update_quantity` | Modifie quantité |
| `handle_save_client_info()` | `client_livraison_handlers.py` | `save_client_info` | Sauvegarde client |
| `handle_save_livraison()` | `client_livraison_handlers.py` | `save_livraison` | Sauvegarde livraison |
| `handle_toggle_frais_livraison()` | `client_livraison_handlers.py` | `toggle_frais_livraison` | Toggle frais |
| `handle_create_operation()` | `operation_handlers.py` | `create_operation` | Crée opération |
| `handle_update_operation()` | `operation_handlers.py` | `update_operation` | Modifie opération |
| `handle_delete_operation()` | `operation_handlers.py` | `delete_operation` | Supprime opération |

### **APIs (endpoints directs)** - `common/api/`

| Fonction | Fichier | URL Recommandée | Méthode |
|----------|---------|-----------------|---------|
| `api_articles_disponibles()` | `article_api.py` | `/api/articles-disponibles/` | GET |
| `get_article_variants()` | `article_api.py` | `/get-article-variants/<id>/` | GET |
| `rafraichir_articles_section()` | `article_api.py` | `/api/commande/<id>/rafraichir-articles/` | GET |
| `appliquer_remise_panier()` | `remise_api.py` | `/appliquer-remise/<id>/` | POST |
| `retirer_remise_panier()` | `remise_api.py` | `/retirer-remise/<id>/` | POST |
| `calculer_remise_panier_preview()` | `remise_api.py` | `/calculer-remise-preview/<id>/` | GET |

---

## 🔧 Guide d'Intégration

### **Option 1: Utilisation dans une vue principale (Recommandé)**

```python
# Dans votre app/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from commande.models import Commande

# Import des handlers
from common.views.article_handlers import (
    handle_add_article,
    handle_delete_article,
    handle_update_quantity
)
from common.views.client_livraison_handlers import (
    handle_save_client_info,
    handle_save_livraison,
    handle_toggle_frais_livraison
)
from common.views.operation_handlers import (
    handle_create_operation,
    handle_update_operation,
    handle_delete_operation
)

def modifier_commande(request, commande_id):
    """Vue principale de modification de commande"""
    commande = get_object_or_404(Commande, id=commande_id)
    operateur = get_operateur(request)  # Votre logique

    if request.method == 'POST':
        action = request.POST.get('action')

        # Router vers le bon handler
        if action == 'add_article':
            return handle_add_article(request, commande, operateur)
        elif action == 'delete_panier':
            return handle_delete_article(request, commande, operateur)
        elif action == 'update_quantity':
            return handle_update_quantity(request, commande, operateur)
        elif action == 'save_client_info':
            return handle_save_client_info(request, commande, operateur)
        elif action == 'save_livraison':
            return handle_save_livraison(request, commande, operateur)
        elif action == 'toggle_frais_livraison':
            return handle_toggle_frais_livraison(request, commande, operateur)
        elif action == 'create_operation':
            return handle_create_operation(request, commande, operateur)
        elif action == 'update_operation':
            return handle_update_operation(request, commande, operateur)
        elif action == 'delete_operation':
            return handle_delete_operation(request, commande, operateur)

    # GET: Afficher le formulaire
    context = {
        'commande': commande,
        # ... autres données
    }
    return render(request, 'votre_template.html', context)
```

### **Option 2: URLs directes vers les APIs**

```python
# Dans votre app/urls.py
from django.urls import path
from common.api.article_api import (
    api_articles_disponibles,
    get_article_variants,
    rafraichir_articles_section
)
from common.api.remise_api import (
    appliquer_remise_panier,
    retirer_remise_panier,
    calculer_remise_panier_preview
)

urlpatterns = [
    # APIs Articles
    path('api/articles-disponibles/', api_articles_disponibles, name='api_articles_disponibles'),
    path('get-article-variants/<int:article_id>/', get_article_variants, name='get_article_variants'),
    path('api/commande/<int:commande_id>/rafraichir-articles/', rafraichir_articles_section, name='rafraichir_articles'),

    # APIs Remises
    path('calculer-remise-preview/<int:panier_id>/', calculer_remise_panier_preview, name='calculer_remise_preview'),
    path('appliquer-remise/<int:panier_id>/', appliquer_remise_panier, name='appliquer_remise'),
    path('retirer-remise/<int:panier_id>/', retirer_remise_panier, name='retirer_remise'),
]
```

---

## ⚠️ Points d'Attention

### 1. **URLs hardcodées dans le JavaScript**

Les fichiers JS utilisent des URLs hardcodées pour `operateur-confirme`. Pour réutiliser dans d'autres apps :

**Solution A: Injecter les URLs depuis le template**
```django
<!-- Dans votre template -->
<script>
    window.urlBase = "{% url 'votre_app:modifier_commande' commande.id %}";
    window.urlApiArticles = "{% url 'votre_app:api_articles_disponibles' %}";
    window.urlRafraichir = "{% url 'votre_app:rafraichir_articles' commande.id %}";
</script>
<script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
```

**Solution B: Modifier les fonctions getUrlModifier() dans le JS**
```javascript
function getUrlModifier() {
    // Priorité 1: Variable injectée par le template
    if (typeof window !== 'undefined' && window.urlModifier) {
        return window.urlModifier;
    }

    // Priorité 2: Construction dynamique
    const id = getCommandeId();
    const appName = window.appName || 'operateur-confirme';  // Paramétrable
    return `/${appName}/commandes/${id}/modifier/`;
}
```

### 2. **Paramètre operateur optionnel**

Toutes les fonctions acceptent `operateur=None`. Si votre app requiert l'opérateur, passez-le :

```python
# Récupérer l'opérateur selon votre logique
operateur = get_object_or_404(Operateur, user=request.user)

# Passer aux handlers
return handle_add_article(request, commande, operateur)
```

### 3. **Template paths personnalisables**

La fonction `rafraichir_articles_section()` accepte un paramètre `template_path` :

```python
# Utiliser votre template spécifique
rafraichir_articles_section(
    request,
    commande_id,
    template_path='operatPrepa/partials/_articles_section.html'
)
```

---

## ✅ Checklist d'Intégration

Pour intégrer le module `common/` dans votre application :

- [ ] Copier les fichiers JS de `static/js/Commande/` vers votre projet
- [ ] Copier les templates de `templates/common/commande/` vers votre projet
- [ ] Importer les handlers dans votre vue principale
- [ ] Router les actions POST vers les bons handlers
- [ ] Configurer les URLs pour les APIs
- [ ] Injecter les URLs dans vos templates (voir Solution A)
- [ ] Tester chaque fonctionnalité AJAX
- [ ] Vérifier les logs backend pour les erreurs

---

## 📞 Support

Pour toute question sur l'intégration AJAX :
- Consulter ce guide
- Voir les exemples dans `common/README.md`
- Lire `static/js/Commande/QUICK_START.md`

---

**Version :** 1.0
**Dernière mise à jour :** 2 Janvier 2026
**Auteur :** YZ-RESCUE
