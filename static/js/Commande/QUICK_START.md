# 🚀 Guide de Démarrage Rapide - Module Commande

Ce guide vous permet d'intégrer le module de gestion des commandes en **5 minutes**.

---

## ✅ Checklist d'Installation

- [ ] Copier les fichiers JS dans `static/js/Commande/`
- [ ] Copier les templates dans `templates/common/commande/`
- [ ] Ajouter les imports JS dans votre template
- [ ] Inclure le template de section articles
- [ ] Définir `data-commande-id`
- [ ] Ajouter les modals nécessaires
- [ ] Tester !

---

## 📦 Installation Minimale (3 étapes)

### **Étape 1 : Imports JavaScript**

Ajoutez à la fin de votre template (avant `</body>`) :

```django
{% load static %}

<script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
<script src="{% static 'js/Commande/remise.js' %}"></script>
```

### **Étape 2 : Include de la Section**

Où vous voulez afficher les articles :

```django
<div id="mainContent" data-commande-id="{{ commande.id }}">
    {% include 'common/commande/section_articles.html' with commande=commande %}
</div>
```

### **Étape 3 : Copier les Modals**

Copiez les modals depuis `templates/operatConfirme/modifier_commande.html` :
- Modal article (#articleModal)
- Modal remise (#remiseModal)
- Modal variantes (#variantesModal)

---

## 🎯 Exemple Minimal Complet

```django
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
    <!-- Tailwind CSS (requis pour le style) -->
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
{% endblock %}

{% block content %}
<div class="container mx-auto p-6">
    <h1 class="text-3xl font-bold mb-6">Commande #{{ commande.numero }}</h1>

    <!-- Section Articles (Module Global) -->
    <div id="mainContent" data-commande-id="{{ commande.id }}">
        {% include 'common/commande/section_articles.html' with commande=commande %}
    </div>
</div>

<!-- Modals -->
<div id="articleModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <!-- Contenu du modal article -->
</div>

<div id="remiseModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <!-- Contenu du modal remise -->
</div>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
    <script src="{% static 'js/Commande/remise.js' %}"></script>

    <script>
        // Configuration optionnelle
        console.log('Module Commande chargé pour commande #{{ commande.id }}');
    </script>
{% endblock %}
```

---

## 🔧 Configuration Backend Minimale

### Views Django requises :

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def rafraichir_articles(request, commande_id):
    """Retourne le HTML rafraîchi des articles"""
    commande = get_object_or_404(Commande, id=commande_id)

    html = render_to_string('common/commande/_articles_section.html', {
        'commande': commande
    })

    return JsonResponse({
        'success': True,
        'html': html,
        'articles_count': commande.paniers.count(),
        'total_commande': float(commande.total_cmd),
        'sous_total_articles': float(commande.get_sous_total_articles()),
        'compteur': commande.compteur
    })

@require_http_methods(["POST"])
def modifier_commande(request, commande_id):
    """Ajoute ou modifie un article dans la commande"""
    commande = get_object_or_404(Commande, id=commande_id)
    action = request.POST.get('action')

    if action == 'add_article':
        # Logique d'ajout
        article_id = request.POST.get('article_id')
        quantite = int(request.POST.get('quantite', 1))
        # ... votre logique

        return JsonResponse({
            'success': True,
            'message': 'Article ajouté avec succès'
        })

    elif action == 'update_article':
        # Logique de modification
        # ... votre logique

        return JsonResponse({
            'success': True,
            'message': 'Article modifié avec succès'
        })
```

### URLs Django :

```python
urlpatterns = [
    path('operateur-confirme/api/commande/<int:commande_id>/rafraichir-articles/',
         rafraichir_articles, name='rafraichir_articles'),
    path('operateur-confirme/commandes/<int:commande_id>/modifier/',
         modifier_commande, name='modifier_commande'),
]
```

---

## 🎨 Personnalisation Rapide

### Changer les couleurs :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    color_primary='#1a202c'
    color_secondary='#2d3748'
%}
```

### Masquer le bouton "Ajouter" :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    show_add_button=False
%}
```

### Utiliser un partial personnalisé :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    articles_partial='mon_app/mon_partial.html'
%}
```

---

## 🧪 Test Rapide

Après installation, ouvrez la console du navigateur. Vous devriez voir :

```
✅ gestion_articles.js (GLOBAL) chargé - Version 3.0
✅ remise.js (GLOBAL) chargé - Version 2.0
```

Si oui, **félicitations !** Le module est correctement installé.

---

## 🐛 Problèmes Courants

### ❌ "getCommandeId() retourne vide"

**Solution :**
```django
<!-- Assurez-vous d'avoir ceci -->
<div id="mainContent" data-commande-id="{{ commande.id }}">
```

### ❌ "Modal ne s'ouvre pas"

**Vérifiez :**
1. Le modal existe dans le HTML
2. L'ID est correct (`articleModal`, `remiseModal`)
3. Les classes Tailwind sont chargées

### ❌ "Erreur 404 sur rafraichir-articles"

**Vérifiez :**
1. L'URL est bien définie dans `urls.py`
2. La vue existe et est importée
3. Le chemin correspond exactement

---

## 📞 Fonctions Principales à Connaître

```javascript
// Ajouter un article
ajouterNouvelArticle()

// Modifier un article
modifierArticle(panierId)

// Supprimer un article
supprimerArticle(panierId)

// Appliquer une remise
ouvrirModalRemise(panierId)

// Rafraîchir la section
rafraichirSectionArticles()
```

---

## 🎯 Prochaines Étapes

1. ✅ Installation de base → **Vous êtes ici**
2. 📚 Lire le [README.md](README.md) complet
3. 🎨 Personnaliser le style selon votre charte
4. 🔧 Adapter les endpoints backend à votre structure
5. 🚀 Déployer en production

---

## 💡 Astuce Pro

Pour activer les logs détaillés en développement :

```javascript
// Dans la console du navigateur
localStorage.setItem('debug', 'true');
// Puis rafraîchir la page
```

---

**Temps d'installation estimé :** 5-10 minutes
**Niveau de difficulté :** ⭐⭐ (Facile)
**Support :** Voir [README.md](README.md) pour la documentation complète

---

🎉 **Bon développement !**
