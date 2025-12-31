# 📖 Exemples d'utilisation du système de filtres de commandes

Ce document fournit des exemples concrets d'utilisation du système de filtres globaux pour les commandes.

---

## 🎯 Exemple 1 : Intégration basique

### Template

```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Liste des Commandes{% endblock %}

{% block content %}
    <div class="container mx-auto px-4">
        <h1 class="text-2xl font-bold mb-6">Mes Commandes</h1>

        <!-- Filtres de commandes -->
        {% include 'common/commande-filters.html' %}

        <!-- Tableau des commandes -->
        <table id="cmdTable" class="w-full border">
            <thead>
                <tr>
                    <th>N° Commande</th>
                    <th>Client</th>
                    <th>Ville</th>
                    <th>Total</th>
                    <th>État</th>
                </tr>
            </thead>
            <tbody>
                {% for commande in page_obj %}
                <tr>
                    <td>{{ commande.id_yz }}</td>
                    <td>{{ commande.client.nom_complet }}</td>
                    <td>{{ commande.ville.nom }}</td>
                    <td>{{ commande.total_cmd }} DH</td>
                    <td>{{ commande.etat_actuel.enum_etat.libelle }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Pagination -->
        <div class="mt-4">
            {% if page_obj.has_previous %}
                <a href="?page={{ page_obj.previous_page_number }}">Précédent</a>
            {% endif %}
            <span>Page {{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
            {% if page_obj.has_next %}
                <a href="?page={{ page_obj.next_page_number }}">Suivant</a>
            {% endif %}
        </div>
    </div>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/common/commande-filters.js' %}"></script>
{% endblock %}
```

### Vue

```python
from django.shortcuts import render
from django.core.paginator import Paginator
from common.filter_utils import apply_commande_filters
from commande.models import Commande

def liste_commandes(request):
    """Liste toutes les commandes avec filtres."""

    # Récupérer toutes les commandes
    commandes = Commande.objects.all().select_related('client', 'ville')

    # Appliquer les filtres
    commandes = apply_commande_filters(commandes, request)

    # Pagination
    paginator = Paginator(commandes, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'commandes/liste.html', {
        'page_obj': page_obj
    })
```

### URL

```python
from django.urls import path
from . import views

urlpatterns = [
    path('commandes/', views.liste_commandes, name='liste_commandes'),
]
```

---

## 🎯 Exemple 2 : Filtres personnalisés

### Vue avec configuration

```python
from django.shortcuts import render
from common.filter_utils import apply_commande_filters
from commande.models import Commande

def commandes_confirmees(request):
    """Liste des commandes confirmées avec filtres personnalisés."""

    # Configuration des filtres
    filter_config = {
        'show_search': True,
        'show_info_base': True,
        'show_localisation': True,
        'show_dates': True,
        'show_montant': True,
        'search_placeholder': 'Rechercher par N° commande, client...',
        'title': 'Filtres Avancés',
        'description': 'Filtrez vos commandes confirmées.',
    }

    # Récupérer les commandes confirmées uniquement
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').distinct()

    # Appliquer les filtres utilisateur
    commandes = apply_commande_filters(commandes, request)

    # Trier par date de création (plus récent d'abord)
    commandes = commandes.order_by('-date_creation')

    return render(request, 'commandes/confirmees.html', {
        'commandes': commandes,
        'filter_config': filter_config
    })
```

### Template

```django
{% extends 'base.html' %}
{% load static %}

{% block content %}
    <h1>Commandes Confirmées</h1>

    <!-- Filtres avec configuration personnalisée -->
    {% include 'common/commande-filters.html' with filter_config=filter_config %}

    <!-- Liste des commandes -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {% for commande in commandes %}
        <div class="border rounded p-4">
            <h3 class="font-bold">{{ commande.id_yz }}</h3>
            <p>Client: {{ commande.client.nom_complet }}</p>
            <p>Ville: {{ commande.ville.nom }}</p>
            <p>Total: {{ commande.total_cmd }} DH</p>
        </div>
        {% endfor %}
    </div>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/common/commande-filters.js' %}"></script>
{% endblock %}
```

---

## 🎯 Exemple 3 : Sans certains filtres

### Vue (sans filtres de localisation et montant)

```python
def commandes_en_preparation(request):
    """Commandes en préparation - Filtres simplifiés."""

    filter_config = {
        'show_search': True,
        'show_info_base': True,
        'show_localisation': False,  # Masquer localisation
        'show_dates': True,
        'show_montant': False,       # Masquer montant
        'search_placeholder': 'Rechercher une commande...',
    }

    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct()

    commandes = apply_commande_filters(commandes, request)

    return render(request, 'preparation/liste.html', {
        'commandes': commandes,
        'filter_config': filter_config
    })
```

---

## 🎯 Exemple 4 : Avec filtres supplémentaires

### Vue avec filtres métier

```python
from django.db.models import Q
from common.filter_utils import apply_commande_filters

def commandes_retard(request):
    """Commandes en retard avec filtres avancés."""

    from django.utils import timezone
    from datetime import timedelta

    # Date limite (commandes de plus de 3 jours)
    date_limite = timezone.now() - timedelta(days=3)

    # Commandes en retard
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle__in=['En préparation', 'À imprimer'],
        etats__date_debut__lt=date_limite,
        etats__date_fin__isnull=True
    ).distinct()

    # Appliquer les filtres utilisateur
    commandes = apply_commande_filters(commandes, request)

    # Filtre métier supplémentaire (urgence)
    urgence = request.GET.get('urgence', '')
    if urgence == 'haute':
        commandes = commandes.filter(
            Q(client__ville__region__nom__icontains='Casablanca') |
            Q(total_cmd__gte=1000)
        )

    return render(request, 'commandes/retard.html', {
        'commandes': commandes,
        'date_limite': date_limite
    })
```

---

## 🎯 Exemple 5 : Avec statistiques

### Vue avec compteurs

```python
from django.db.models import Count, Sum
from common.filter_utils import apply_commande_filters

def tableau_bord_commandes(request):
    """Tableau de bord avec statistiques."""

    # Toutes les commandes
    all_commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).distinct()

    # Appliquer les filtres
    commandes_filtrees = apply_commande_filters(all_commandes, request)

    # Calculer les statistiques
    stats = commandes_filtrees.aggregate(
        total_commandes=Count('id'),
        total_montant=Sum('total_cmd'),
    )

    # Nombre par ville
    par_ville = commandes_filtrees.values('ville__nom').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    return render(request, 'dashboard/commandes.html', {
        'commandes': commandes_filtrees,
        'stats': stats,
        'par_ville': par_ville
    })
```

### Template avec statistiques

```django
{% extends 'base.html' %}
{% load static %}

{% block content %}
    <h1>Tableau de Bord</h1>

    <!-- Cartes statistiques -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-100 p-4 rounded">
            <h3>Total Commandes</h3>
            <p class="text-2xl font-bold">{{ stats.total_commandes }}</p>
        </div>
        <div class="bg-green-100 p-4 rounded">
            <h3>Total Montant</h3>
            <p class="text-2xl font-bold">{{ stats.total_montant|floatformat:2 }} DH</p>
        </div>
        <div class="bg-yellow-100 p-4 rounded">
            <h3>Moyenne</h3>
            <p class="text-2xl font-bold">
                {% widthratio stats.total_montant stats.total_commandes 1 %} DH
            </p>
        </div>
    </div>

    <!-- Filtres -->
    {% include 'common/commande-filters.html' %}

    <!-- Top 10 Villes -->
    <div class="bg-white p-4 rounded shadow mb-6">
        <h3 class="font-bold mb-4">Top 10 Villes</h3>
        <ul>
            {% for ville in par_ville %}
            <li>{{ ville.ville__nom }}: {{ ville.count }} commande(s)</li>
            {% endfor %}
        </ul>
    </div>

    <!-- Liste complète -->
    <table id="cmdTable" class="w-full">
        <!-- ... -->
    </table>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/common/commande-filters.js' %}"></script>
{% endblock %}
```

---

## 🎯 Exemple 6 : Export des résultats filtrés

### Vue avec export CSV

```python
import csv
from django.http import HttpResponse
from common.filter_utils import apply_commande_filters

def exporter_commandes(request):
    """Exporte les commandes filtrées en CSV."""

    # Récupérer et filtrer les commandes
    commandes = Commande.objects.all()
    commandes = apply_commande_filters(commandes, request)

    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="commandes.csv"'

    writer = csv.writer(response)
    writer.writerow(['N° Commande', 'Client', 'Ville', 'Total', 'Date'])

    for commande in commandes:
        writer.writerow([
            commande.id_yz,
            commande.client.nom_complet,
            commande.ville.nom,
            commande.total_cmd,
            commande.date_cmd
        ])

    return response
```

### Template avec bouton export

```django
<div class="flex justify-between items-center mb-4">
    <h1>Mes Commandes</h1>

    <!-- Bouton d'export -->
    <a href="{% url 'exporter_commandes' %}?{{ request.GET.urlencode }}"
       class="px-4 py-2 bg-green-600 text-white rounded">
        <i class="fas fa-download mr-2"></i>
        Exporter (CSV)
    </a>
</div>

{% include 'common/commande-filters.html' %}

<!-- Tableau... -->
```

---

## 💡 Conseils d'utilisation

### 1. Optimisation des performances

```python
# Toujours utiliser select_related et prefetch_related
commandes = Commande.objects.all() \
    .select_related('client', 'ville', 'ville__region') \
    .prefetch_related('etats', 'operations')

# Appliquer les filtres
commandes = apply_commande_filters(commandes, request)
```

### 2. Préserver les paramètres de pagination

```python
from django.core.paginator import Paginator

def ma_vue(request):
    commandes = Commande.objects.all()
    commandes = apply_commande_filters(commandes, request)

    paginator = Paginator(commandes, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'template.html', {
        'page_obj': page_obj,
        'query_params': request.GET.urlencode()  # Pour les liens
    })
```

### 3. Combiner avec d'autres filtres

```python
from django.db.models import Q

# Filtres métier fixes
commandes = Commande.objects.filter(
    Q(etats__enum_etat__libelle='Confirmée') |
    Q(etats__enum_etat__libelle='En préparation')
).distinct()

# Puis appliquer les filtres utilisateur
commandes = apply_commande_filters(commandes, request)
```

---

## 🔗 Liens utiles

- [Documentation complète](README_COMMANDE_FILTERS.md)
- [README Composants Communs](../templates/common/README.md)
- [Code source du template](../templates/common/commande-filters.html)
- [Code source JavaScript](../static/js/common/commande-filters.js)
- [Code source Python](filter_utils.py)

---

**Version :** 1.0.0
**Auteur :** YZ-Rescue Team
