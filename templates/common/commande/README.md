# 📄 Templates Commande - Documentation

Templates réutilisables pour l'affichage et la gestion des articles dans les commandes.

---

## 📁 Fichiers Disponibles

```
templates/common/commande/
├── section_articles.html        # Template principal complet
├── _articles_section.html       # Partial pour chaque article
└── README.md                    # Cette documentation
```

---

## 🎯 Utilisation

### **Template Principal : `section_articles.html`**

Ce template affiche la section complète des articles avec :
- En-tête avec compteur d'articles
- Badge upsell (si compteur > 0)
- Bouton "Ajouter un article" (optionnel)
- Liste des articles
- Résumé financier (sous-total, frais, total)

#### Utilisation basique :

```django
{% include 'common/commande/section_articles.html' with commande=commande %}
```

#### Utilisation avec options :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    show_add_button=True
    animation_delay='0.5s'
    color_primary='#4B352A'
    color_secondary='#6d4b3b'
    articles_partial='mon_app/mon_partial.html'
%}
```

---

### **Partial : `_articles_section.html`**

Ce partial génère le HTML pour **chaque article** individuellement.

Il est appelé automatiquement par `section_articles.html` mais peut être utilisé indépendamment.

#### Utilisation indépendante :

```django
{% for panier in commande.paniers.all %}
    {% include 'common/commande/_articles_section.html' with panier=panier %}
{% endfor %}
```

---

## 🔧 Paramètres Disponibles

### Pour `section_articles.html` :

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `commande` | Object | ✅ Oui | - | Objet Commande Django |
| `show_add_button` | Boolean | ❌ Non | `True` | Afficher bouton "Ajouter un article" |
| `animation_delay` | String | ❌ Non | `'0.8s'` | Délai animation CSS |
| `color_primary` | String | ❌ Non | `'#4B352A'` | Couleur primaire texte |
| `color_secondary` | String | ❌ Non | `'#6d4b3b'` | Couleur secondaire |
| `articles_partial` | String | ❌ Non | `'common/commande/_articles_section.html'` | Chemin du partial |

---

## 🎨 Personnalisation

### **1. Changer les couleurs**

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    color_primary='#1a202c'
    color_secondary='#2d3748'
%}
```

### **2. Masquer le bouton Ajouter**

Utile en mode lecture seule :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    show_add_button=False
%}
```

### **3. Utiliser un partial personnalisé**

Si vous avez besoin d'un affichage différent pour les articles :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    articles_partial='mon_app/partials/_mes_articles.html'
%}
```

Votre partial doit recevoir :
- `commande` : l'objet commande
- `panier` : chaque objet panier (dans la boucle)

---

## 📊 Structure HTML Générée

### Section principale :

```html
<div class="verification-item bg-white rounded-xl shadow-lg p-4">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
        <h3>Articles de la Commande (X articles)</h3>
        <button onclick="ajouterNouvelArticle()">Ajouter un article</button>
    </div>

    <!-- Liste des articles -->
    <div id="articles-container" class="space-y-3 mb-6">
        <!-- Articles générés par _articles_section.html -->
    </div>

    <!-- Résumé financier -->
    <div class="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-6">
        <!-- Sous-total, frais, total -->
    </div>
</div>
```

### Chaque article (partial) :

```html
<div class="article-card p-4 bg-white rounded-lg border"
     data-article-id="{{ panier.id }}"
     data-article='{ "id": ..., "nom": ..., ... }'>

    <!-- Image + Infos -->
    <div class="flex items-center">
        <img src="..." />
        <div>Nom, référence, badges</div>
    </div>

    <!-- Quantité -->
    <div>
        <button onclick="modifierQuantite(...)">-</button>
        <input type="number" />
        <button onclick="modifierQuantite(...)">+</button>
    </div>

    <!-- Prix unitaire -->
    <div id="prix-unitaire-{{ panier.id }}">XX.XX DH</div>

    <!-- Sous-total -->
    <div id="sous-total-{{ panier.id }}">XX.XX DH</div>

    <!-- Section remise (si appliquée) -->
    <div class="remise-info-container">...</div>

    <!-- Actions -->
    <button onclick="ouvrirModalRemise(...)">Remise</button>
    <button onclick="supprimerArticle(...)">Supprimer</button>
</div>
```

---

## 🔑 IDs et Classes Importants

Le JavaScript utilise ces IDs pour mettre à jour l'interface :

### IDs globaux :
- `#articles-container` : Conteneur de la liste des articles
- `#articles-count` : Compteur d'articles
- `#total-commande` : Total de la commande
- `#sous-total-panier` : Sous-total sans frais
- `#frais-livraison-actifs` : Section frais (si activés)
- `#frais-livraison-inactifs` : Section frais (si désactivés)

### IDs dynamiques (par article) :
- `#quantite-{panier_id}` : Input quantité
- `#prix-unitaire-{panier_id}` : Prix unitaire
- `#prix-libelle-{panier_id}` : Libellé du prix
- `#sous-total-{panier_id}` : Sous-total

### Classes importantes :
- `.article-card` : Chaque carte article
- `.remise-info-container` : Conteneur info remise
- `.remise-appliquee-badge` : Badge "Remise Appliquée"
- `.btn-appliquer-remise` : Bouton appliquer remise

---

## 🧩 Filtres Django Requis

Ces filtres doivent être définis dans vos `templatetags` :

### `commande_filters.py` :

```python
from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Soustraction : {{ value|subtract:arg }}"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
```

### `remise_filters.py` :

```python
from django import template

register = template.Library()

@register.filter
def get_prix_effectif_panier(panier):
    """
    Retourne les infos de prix effectif pour l'affichage
    Returns: {
        'libelle': 'Prix upsell 2',
        'couleur_classe': 'text-green-600',
        'sous_total': 150.00
    }
    """
    # ... logique de calcul
    return {
        'libelle': libelle,
        'couleur_classe': couleur,
        'sous_total': sous_total
    }
```

Chargement dans le template :

```django
{% load commande_filters %}
{% load remise_filters %}
```

---

## 📦 Modèle Django Requis

### Modèle `Commande` :

```python
class Commande(models.Model):
    numero = models.CharField(max_length=50)
    total_cmd = models.DecimalField(max_digits=10, decimal_places=2)
    frais_livraison = models.BooleanField(default=False)
    montant_frais_livraison = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    compteur = models.IntegerField(default=0)  # Compteur articles upsell
    produit_init = models.TextField(blank=True)  # Produit initial (Sheets)

    def get_sous_total_articles(self):
        """Retourne le sous-total sans les frais de livraison"""
        return sum(p.get_sous_total() for p in self.paniers.all())
```

### Modèle `Panier` :

```python
class Panier(models.Model):
    commande = models.ForeignKey(Commande, related_name='paniers', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    quantite = models.IntegerField(default=1)
    prix_panier = models.DecimalField(max_digits=10, decimal_places=2)  # Prix gelé
    type_prix_gele = models.CharField(max_length=50, blank=True)
    couleur = models.CharField(max_length=50, blank=True)
    pointure = models.CharField(max_length=20, blank=True)
    variante = models.ForeignKey(VarianteArticle, null=True, blank=True, on_delete=models.SET_NULL)
    remise_personnalisee = models.ForeignKey(RemisePersonnalisee, null=True, blank=True, on_delete=models.SET_NULL)

    def get_sous_total(self):
        """Calcule le sous-total avec ou sans remise"""
        if self.remise_personnalisee:
            return self.prix_panier * self.quantite - self.remise_personnalisee.montant_applique
        return self.prix_panier * self.quantite
```

---

## 🎯 Exemples d'Utilisation

### **Exemple 1 : Affichage simple**

```django
<div class="container">
    {% include 'common/commande/section_articles.html' with commande=commande %}
</div>
```

### **Exemple 2 : Mode lecture seule**

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    show_add_button=False
%}
```

### **Exemple 3 : Style personnalisé**

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    color_primary='#2563eb'
    color_secondary='#1e40af'
    animation_delay='0.3s'
%}
```

### **Exemple 4 : Partial personnalisé**

Créez `mon_app/partials/_articles_simple.html` :

```django
{% for panier in commande.paniers.all %}
<div class="simple-article">
    <span>{{ panier.article.nom }}</span>
    <span>Qté: {{ panier.quantite }}</span>
    <span>{{ panier.prix_panier }} DH</span>
</div>
{% endfor %}
```

Utilisez-le :

```django
{% include 'common/commande/section_articles.html' with
    commande=commande
    articles_partial='mon_app/partials/_articles_simple.html'
%}
```

---

## 🔄 Rafraîchissement Dynamique

Le conteneur `#articles-container` est rafraîchi automatiquement via AJAX après :
- Ajout d'un article
- Modification de quantité
- Suppression d'un article
- Application/retrait de remise

Le JavaScript appelle :
```javascript
rafraichirSectionArticles()
```

Qui charge :
```
GET /operateur-confirme/api/commande/{id}/rafraichir-articles/
```

Et remplace le contenu de `#articles-container` par le nouveau HTML.

---

## 🎨 Styles CSS Requis

Le template utilise **Tailwind CSS**. Assurez-vous qu'il est chargé :

```html
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2/dist/tailwind.min.css" rel="stylesheet">
```

Et Font Awesome pour les icônes :

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

---

## ✅ Checklist d'Intégration

- [ ] Filtres Django créés (`commande_filters`, `remise_filters`)
- [ ] Modèles Commande et Panier conformes
- [ ] Tailwind CSS et Font Awesome chargés
- [ ] JavaScript modules chargés (`gestion_articles.js`, `remise.js`)
- [ ] Template inclus avec `data-commande-id`
- [ ] Endpoints backend configurés

---

## 🐛 Dépannage

### Template ne s'affiche pas

**Vérifiez :**
1. Le template existe bien dans `templates/common/commande/`
2. L'objet `commande` est passé au contexte
3. Les filtres sont chargés (`{% load commande_filters %}`)

### Articles ne s'affichent pas

**Vérifiez :**
1. `commande.paniers.all()` retourne des résultats
2. Le partial `_articles_section.html` existe
3. Les relations ForeignKey sont correctes

### Erreur de filtre

**Vérifiez :**
1. Les filtres sont enregistrés dans `templatetags/`
2. Le dossier `templatetags/` contient `__init__.py`
3. Les filtres sont chargés au début du template

---

## 📚 Ressources

- [README.md](../../../static/js/Commande/README.md) - Documentation JavaScript complète
- [QUICK_START.md](../../../static/js/Commande/QUICK_START.md) - Guide de démarrage rapide

---

**Version :** 2.0 (Module Global)
**Dernière mise à jour :** 1er Janvier 2026
