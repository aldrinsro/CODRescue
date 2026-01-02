# 📦 Module Global de Gestion des Commandes

Ce module fournit une solution réutilisable et complète pour la gestion des articles dans les commandes, incluant les remises et la confirmation.

## 📁 Structure des Fichiers

```
static/js/Commande/
├── gestion_articles.js    # Gestion CRUD des articles, variantes, prix upsell
├── remise.js              # Gestion des remises personnalisées
├── confirmation.js        # Validation et confirmation des commandes
├── detail_toggle.js       # Utilitaire pour toggle de détails
└── README.md              # Cette documentation

templates/common/commande/
├── section_articles.html      # Template principal de la section articles
└── _articles_section.html     # Partial pour le rendu de chaque article
```

---

## 🚀 Installation et Utilisation

### **Étape 1 : Inclure les fichiers JavaScript**

Dans votre template (ex: `modifier_commande.html`), ajoutez ces scripts **dans cet ordre** :

```django
{% load static %}

<!-- 1. Gestion des articles (doit être en premier) -->
<script src="{% static 'js/Commande/gestion_articles.js' %}"></script>

<!-- 2. Gestion des remises -->
<script src="{% static 'js/Commande/remise.js' %}"></script>

<!-- 3. Confirmation (optionnel, seulement si vous gérez la confirmation) -->
<script src="{% static 'js/Commande/confirmation.js' %}"></script>
```

### **Étape 2 : Inclure le template de la section articles**

Dans votre template, à l'endroit où vous voulez afficher les articles :

```django
<!-- Utilisation basique -->
{% include 'common/commande/section_articles.html' with commande=commande %}

<!-- Utilisation avancée avec options -->
{% include 'common/commande/section_articles.html' with
    commande=commande
    show_add_button=True
    animation_delay='0.5s'
    color_primary='#4B352A'
    color_secondary='#6d4b3b'
%}
```

### **Étape 3 : S'assurer que data-commande-id est défini**

Le module a besoin de l'ID de la commande pour fonctionner. Ajoutez cet attribut dans votre template :

```django
<div id="mainContent" data-commande-id="{{ commande.id }}">
    <!-- Votre contenu -->
</div>
```

Ou définissez-le en JavaScript :

```javascript
window.commandeId = {{ commande.id }};
```

---

## 🎨 Personnalisation du Template

Le template `section_articles.html` accepte plusieurs paramètres optionnels :

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `commande` | Object | **REQUIS** | L'objet commande à afficher |
| `articles_partial` | String | `'common/commande/_articles_section.html'` | Chemin vers le partial des articles |
| `show_add_button` | Boolean | `True` | Afficher le bouton "Ajouter un article" |
| `animation_delay` | String | `'0.8s'` | Délai d'animation CSS |
| `color_primary` | String | `'#4B352A'` | Couleur primaire du texte |
| `color_secondary` | String | `'#6d4b3b'` | Couleur secondaire |

### Exemple de personnalisation complète :

```django
{% include 'common/commande/section_articles.html' with
    commande=ma_commande
    articles_partial='mon_app/partials/_mes_articles.html'
    show_add_button=False
    animation_delay='0.3s'
    color_primary='#1a202c'
    color_secondary='#2d3748'
%}
```

---

## 📚 API JavaScript - Fonctions Principales

### **Gestion des Articles** (`gestion_articles.js`)

#### Ajout/Modification
```javascript
// Ouvrir le modal d'ajout d'un nouvel article
ajouterNouvelArticle()

// Modifier un article existant
modifierArticle(panierId)

// Sauvegarder l'article (ajout ou modification)
saveArticle()
```

#### Suppression
```javascript
// Supprimer un article du panier
supprimerArticle(panierId)
```

#### Variantes
```javascript
// Ouvrir le modal de sélection de variantes
ouvrirModalVariantes(article)

// Fermer le modal de variantes
fermerModalVariantes()
```

#### Mise à jour des totaux
```javascript
// Rafraîchir la section articles depuis le backend
rafraichirSectionArticles()

// Mettre à jour tous les totaux
mettreAJourTousLesTotaux(data)
```

#### Prix Upsell
```javascript
// Afficher les prix upsell dynamiques selon le compteur
afficherPrixUpsellDynamiques(compteurActuel)

// Protéger les libellés de prix gelés
protegerLibellesPrixGeles()
```

---

### **Gestion des Remises** (`remise.js`)

```javascript
// Ouvrir le modal de remise pour un panier
ouvrirModalRemise(panierId)

// Fermer le modal de remise
fermerModalRemise()

// Calculer et afficher l'aperçu en temps réel
calculerApercu()

// Appliquer la remise
appliquerRemise()

// Retirer une remise appliquée
retirerRemise(panierId)
```

---

### **Confirmation** (`confirmation.js`)

```javascript
// Confirmer la commande (valide et vérifie le stock)
confirmerCommande()

// Lancer le processus de confirmation (Affectée -> En cours)
lancerConfirmation()

// Annuler la commande avec motif
annulerCommande()
```

---

## 🔧 Configuration Backend Requise

### **Endpoints nécessaires**

Votre application Django doit fournir ces endpoints :

#### Pour les articles :
- `GET/POST /operateur-confirme/commandes/{id}/modifier/` - Modifier/ajouter article
- `GET /operateur-confirme/api/commande/{id}/rafraichir-articles/` - Rafraîchir articles
- `GET /operateur-confirme/articles/charger/` - Charger liste articles disponibles

#### Pour les remises :
- `GET /operateur-confirme/calculer-remise-preview/{panier_id}/` - Aperçu remise
- `POST /operateur-confirme/appliquer-remise/{panier_id}/` - Appliquer remise
- `POST /operateur-confirme/retirer-remise/{panier_id}/` - Retirer remise

#### Pour la confirmation :
- `POST /operateur-confirme/commandes/{id}/confirmer-ajax/` - Confirmer commande
- `POST /operateur-confirme/commandes/{id}/lancer-confirmation/` - Lancer confirmation
- `POST /operateur-confirme/commandes/{id}/annuler-confirmation/` - Annuler commande

### **Modèles Django requis**

Votre modèle `Commande` doit avoir :
- `paniers` (relation Many-to-Many via `Panier`)
- `total_cmd` (Decimal)
- `frais_livraison` (Boolean)
- `montant_frais_livraison` (Decimal)
- `compteur` (Integer) - compteur d'articles upsell

Votre modèle `Panier` doit avoir :
- `article` (ForeignKey)
- `quantite` (Integer)
- `prix_panier` (Decimal) - prix gelé au moment de l'ajout
- `type_prix_gele` (String) - type de prix appliqué
- `remise_personnalisee` (ForeignKey, nullable)
- `variante` (ForeignKey, nullable)

---

## 🎯 Fonctionnalités Avancées

### **1. Système de Prix Upsell**

Le module gère automatiquement les prix upsell selon le nombre d'articles upsell dans la commande :

- **Compteur 0** (0-1 articles) → Prix normal
- **Compteur 1** (2 articles) → Prix upsell 2
- **Compteur 2** (3 articles) → Prix upsell 3
- **Compteur 3** (4 articles) → Prix upsell 4
- **Compteur 4+** (5+ articles) → Prix gros

**⚠️ Important :** Les prix sont **gelés en base de données** lors de l'ajout au panier. Le module met à jour uniquement l'**affichage** frontend.

### **2. Protection des Prix Gelés**

Les prix en promotion, liquidation ou test sont **gelés** et **protégés** :

```javascript
// Cette fonction s'exécute automatiquement pour préserver l'intégrité
protegerLibellesPrixGeles()
```

Même si le compteur upsell change, ces prix restent fixes.

### **3. Gestion des Variantes**

Le module supporte les variantes (taille × couleur) avec affichage :
- Tableau croisé (si 2 dimensions)
- Tableau simple (si 1 dimension)
- Liste (fallback)

### **4. Remises Personnalisées**

Deux types de remises :
- **POURCENTAGE** : ex. 10%
- **MONTANT_FIXE** : ex. 50 DH

Avec prévisualisation en temps réel avant application.

---

## 🎨 Modals Requis dans votre Template

Pour que le module fonctionne, incluez ces modals dans votre template :

### **1. Modal d'ajout/modification d'article**
```html
<div id="articleModal" class="hidden">
    <!-- Structure du modal -->
</div>
```

### **2. Modal de remise**
```html
<div id="remiseModal" class="hidden">
    <!-- Structure du modal -->
</div>
```

### **3. Modal de stock insuffisant**
```html
<div id="stockInsuffisantModal" class="hidden">
    <div id="stockInsuffisantList"></div>
</div>
```

### **4. Modal de variantes**
```html
<div id="variantesModal" class="hidden">
    <div id="variantes-display"></div>
</div>
```

---

## 📊 Événements Personnalisés

Le module émet des événements que vous pouvez écouter :

```javascript
// Déclenché après rafraîchissement de la section articles
window.addEventListener('articlesRefreshed', (e) => {
    console.log('Articles mis à jour:', e.detail);
    // e.detail contient: { articles_count, total_commande, sous_total_articles, compteur }
});
```

---

## 🔍 Débogage

Le module affiche des logs détaillés dans la console :

```
✅ gestion_articles.js (GLOBAL) chargé - Version 3.0
✅ remise.js (GLOBAL) chargé - Version 2.0
✅ confirmation.js (GLOBAL) chargé - Version 2.0
```

Activez le mode verbose pour plus de détails :
```javascript
// Dans la console
localStorage.setItem('debug', 'true');
```

---

## 🚨 Dépannage

### Problème : "getCommandeId() retourne vide"
**Solution :** Vérifiez que `data-commande-id` est défini ou que `window.commandeId` existe.

### Problème : "Articles ne se rafraîchissent pas"
**Solution :** Vérifiez que l'endpoint `/api/commande/{id}/rafraichir-articles/` existe et retourne le bon format JSON.

### Problème : "Les prix ne s'affichent pas correctement"
**Solution :** Vérifiez que vos filtres Django `get_prix_effectif_panier` sont bien définis.

### Problème : "Modal ne s'ouvre pas"
**Solution :** Vérifiez que les IDs des modals correspondent : `articleModal`, `remiseModal`, etc.

---

## 📝 Exemple Complet d'Intégration

Voici un exemple complet d'intégration dans un template Django :

```django
{% extends "base.html" %}
{% load static %}

{% block extra_js %}
    <!-- Scripts globaux de gestion des commandes -->
    <script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
    <script src="{% static 'js/Commande/remise.js' %}"></script>
    <script src="{% static 'js/Commande/confirmation.js' %}"></script>
{% endblock %}

{% block content %}
<div id="mainContent" data-commande-id="{{ commande.id }}">

    <!-- Section Articles (Module Global) -->
    {% include 'common/commande/section_articles.html' with commande=commande %}

    <!-- Bouton de confirmation -->
    <div class="mt-6">
        <button onclick="confirmerCommande()" class="btn-primary">
            Confirmer la commande
        </button>
    </div>

</div>

<!-- Modals (copiez depuis operatConfirme/modifier_commande.html) -->
{% include 'common/commande/modals/_article_modal.html' %}
{% include 'common/commande/modals/_remise_modal.html' %}
{% include 'common/commande/modals/_stock_insuffisant_modal.html' %}
{% include 'common/commande/modals/_variantes_modal.html' %}

{% endblock %}
```

---

## 🔄 Migration depuis l'ancienne version

Si vous utilisez actuellement la version spécifique à `operatConfirme`, voici les étapes de migration :

### 1. Remplacer les imports JS

**Avant :**
```django
<script src="{% static 'js/operatConfirme/Confirmation_commande/Gestion_articles.js' %}"></script>
<script src="{% static 'js/operatConfirme/Confirmation_commande/Remise.js' %}"></script>
<script src="{% static 'js/operatConfirme/Confirmation_commande/confirmaton.js' %}"></script>
```

**Après :**
```django
<script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
<script src="{% static 'js/Commande/remise.js' %}"></script>
<script src="{% static 'js/Commande/confirmation.js' %}"></script>
```

### 2. Remplacer l'include du template

**Avant :**
```django
{% include 'operatConfirme/partials/_articles_section.html' %}
```

**Après :**
```django
{% include 'common/commande/section_articles.html' with commande=commande %}
```

### 3. Aucun changement côté Python/Backend requis !

Le module est 100% compatible avec votre backend existant.

---

## 📄 Licence

© 2025 YZ-RESCUE - Module interne réutilisable

---

## 👥 Support

Pour toute question ou problème, consultez :
- La console du navigateur (logs détaillés)
- Cette documentation
- Le code source commenté dans `static/js/Commande/`

---

**Version actuelle :** 3.0 (Module Global Réutilisable)
**Dernière mise à jour :** 1er Janvier 2026
