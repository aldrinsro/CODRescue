# 🏷️ Système d'Étiquettes Professionnelles Yoozak

## 📋 Vue d'ensemble

Le nouveau système d'étiquettes professionnelles utilise **ReportLab** pour générer des PDFs haute qualité avec des codes-barres et QR codes parfaitement scannables.

## 🚀 Installation et Configuration

### 1. Dépendances
```bash
pip install reportlab reportlab-graphics-barcode
```

### 2. Migrations
```bash
python manage.py makemigrations commande
python manage.py migrate
```

### 3. Créer les templates par défaut
```bash
python manage.py create_default_template
```

### 4. Test de l'installation
```bash
python test_reportlab.py
```

## 🎯 Fonctionnalités

### ✅ Avantages du nouveau système

- **Codes-barres haute qualité** : Générés avec ReportLab, parfaitement scannables
- **QR codes optimisés** : Taille et contraste optimaux
- **Templates configurables** : Dimensions, couleurs, polices personnalisables
- **Interface moderne** : Interface web intuitive et responsive
- **Performance** : Génération PDF rapide et efficace
- **Intégration Django** : Utilise les modèles Django existants
- **Aperçu en temps réel** : Prévisualisation avant impression

### 🔧 Templates disponibles

1. **Template Professionnel Standard** (180×260mm)
   - En-tête et pied de page
   - Code-barres CODE128B
   - Police Helvetica
   - Couleurs professionnelles

2. **Template QR Code Standard** (180×260mm)
   - QR codes haute résolution
   - Même design que le standard
   - Optimisé pour le scan mobile

3. **Template Compact** (100×150mm)
   - Format réduit
   - Idéal pour les petits articles
   - Code-barres adaptés

## 🖥️ Interface Utilisateur

### Accès
```
/commande/etiquettes/
```

### Fonctionnalités de l'interface

1. **Sélection de template**
   - Aperçu des dimensions
   - Options activées (en-tête, pied, codes)
   - Sélection visuelle

2. **Choix du format**
   - Code-barres (CODE128B)
   - QR codes
   - Basculement facile

3. **Sélection des commandes**
   - Liste des commandes récentes
   - Sélection multiple
   - Statistiques en temps réel

4. **Génération**
   - Bouton de génération
   - Aperçu avant impression
   - Téléchargement automatique

## 🔌 API Endpoints

### Génération d'étiquettes
```http
POST /commande/etiquettes/generate/
Content-Type: application/json

{
    "commande_ids": [1, 2, 3],
    "template_id": 1,
    "format": "barcode"
}
```

### Aperçu d'étiquette
```http
GET /commande/etiquettes/preview/{commande_id}/{template_id}/
```

### Articles d'une commande
```http
GET /commande/api/commande/{commande_id}/articles/
```

## 🎨 Personnalisation des Templates

### Modèle EtiquetteTemplate

```python
class EtiquetteTemplate(models.Model):
    name = models.CharField(max_length=100)
    width = models.FloatField(default=180)  # mm
    height = models.FloatField(default=260)  # mm
    
    # Marges
    margin_top = models.FloatField(default=10)
    margin_bottom = models.FloatField(default=10)
    margin_left = models.FloatField(default=10)
    margin_right = models.FloatField(default=10)
    
    # Styles
    font_family = models.CharField(default="Helvetica")
    font_size_title = models.IntegerField(default=16)
    font_size_text = models.IntegerField(default=12)
    
    # Couleurs
    color_header = models.CharField(default="#2c3e50")
    color_footer = models.CharField(default="#2c3e50")
    color_text = models.CharField(default="#333333")
    
    # Code-barres
    barcode_width = models.FloatField(default=4)  # mm
    barcode_height = models.FloatField(default=80)  # mm
    barcode_format = models.CharField(default="CODE128B")
    
    # QR Code
    qr_size = models.IntegerField(default=300)  # px
    
    # Options d'affichage
    show_header = models.BooleanField(default=True)
    show_footer = models.BooleanField(default=True)
    show_barcode = models.BooleanField(default=True)
    show_qr = models.BooleanField(default=False)
```

### Création d'un template personnalisé

```python
from commande.models import EtiquetteTemplate

template = EtiquetteTemplate.objects.create(
    name='Mon Template Personnalisé',
    width=200,
    height=300,
    font_family='Times-Roman',
    color_header='#1a365d',
    barcode_height=100,
    show_qr=True
)
```

## 🔄 Migration depuis l'ancien système

### JavaScript
L'ancien système JavaScript est automatiquement désactivé et redirige vers le nouveau :

```javascript
// Ancien système (désactivé)
window.printArticleLabels = function(articles, options) {
    window.location.href = '/commande/etiquettes/';
};
```

### Intégration
Le nouveau système s'intègre parfaitement avec :
- Les modèles `Commande` et `Panier` existants
- L'interface de gestion des commandes
- Les permissions utilisateur Django

## 🐛 Dépannage

### Problèmes courants

1. **Erreur "ReportLab not found"**
   ```bash
   pip install reportlab
   ```

2. **Codes-barres non scannables**
   - Vérifier la taille du code-barres
   - Augmenter `barcode_height` et `barcode_width`
   - Utiliser un fond blanc pur

3. **PDF vide**
   - Vérifier que les commandes ont des articles
   - Contrôler les marges du template
   - Vérifier les logs Django

4. **Erreur de permissions**
   - S'assurer que l'utilisateur est connecté
   - Vérifier les permissions Django

### Logs et débogage

```python
# Dans views_etiquettes.py
import logging
logger = logging.getLogger(__name__)

def generate_etiquettes_pdf(self, commandes, template, format_type):
    logger.info(f"Génération de {len(commandes)} étiquettes avec template {template.id}")
    # ...
```

## 📈 Performance

### Optimisations

1. **Requêtes optimisées**
   ```python
   commandes = Commande.objects.filter(
       id__in=commande_ids
   ).select_related('client').prefetch_related('paniers__article')
   ```

2. **Cache des templates**
   - Les templates sont mis en cache
   - Réutilisation des objets ReportLab

3. **Génération par lots**
   - Traitement de plusieurs commandes en une fois
   - Réduction des appels API

### Limites recommandées

- **Maximum 100 commandes** par génération
- **Maximum 500 articles** par PDF
- **Taille PDF** : ~2MB pour 50 étiquettes

## 🔮 Évolutions futures

### Fonctionnalités prévues

1. **Templates dynamiques**
   - Éditeur de templates en ligne
   - Sauvegarde de configurations

2. **Intégration imprimantes**
   - Support imprimantes Zebra
   - Formats ZPL/EPL

3. **Statistiques avancées**
   - Suivi des impressions
   - Métriques de performance

4. **API REST complète**
   - Endpoints pour toutes les opérations
   - Documentation Swagger

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs Django
2. Tester avec `python test_reportlab.py`
3. Consulter la documentation ReportLab
4. Contacter l'équipe de développement

---

**Version** : 1.0.0  
**Dernière mise à jour** : {{ date }}  
**Auteur** : Équipe Yoozak
