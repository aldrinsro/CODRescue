# Instructions pour les Agents de Codage IA - CODRescue

## Vue d'ensemble du projet

**CODRescue** est un système de gestion e-commerce développé avec Django 5.1.7, axé sur la préparation de commandes, la logistique et les flux de supervision. Développé par **COD$uite Team** avec **YZ-PRESTATION**, il gère le cycle de vie complet des commandes, de la création à la livraison et aux retours.

### Stack Technique
- **Backend** : Django 5.1.7 + Django REST Framework
- **Base de données** : PostgreSQL (dev : configurable via `.env`)
- **Frontend** : Tailwind CSS (via django-tailwind), patterns HTMX
- **Cache** : Cache basé sur la base de données (`yz_cache_table`)
- **Dépendances clés** : django-filters, crispy-forms, whitenoise, APScheduler, gspread, barcode

## Architecture & Concepts Fondamentaux

### Système Multi-Interfaces
Le système fonctionne via des interfaces spécifiques par rôle, chacune avec des URLs et types d'utilisateurs distincts :

1. **Commande** (`/commande/`) - Hub de gestion des commandes
2. **Confirmation** (`/operateur-confirme/`) - Validation des commandes par les opérateurs de confirmation
3. **Préparation** (`/operateur-preparation/`) - Préparation physique des commandes par les opérateurs d'entrepôt
4. **Logistique** (`/operateur-logistique/`) - Livraisons, retours, service après-vente
5. **Supervision** (`/Superpreparation/`) - Tableau de bord 360° pour les superviseurs
6. **Articles** (`/article/`) - Gestion du catalogue de produits
7. **Synchronisation** (`/synchronisation/`) - Intégration Google Sheets

### Architecture Machine à États
Les commandes évoluent à travers des états gérés par `EnumEtatCmd` (définitions d'états) et `EtatCommande` (historique des états) :

```python
# États clés : 'Non affectée' → 'Affectée' → 'En cours de confirmation' → 'Confirmée' 
# → 'En préparation' → 'Emballée' → 'En livraison' → 'Livrée'/'Retournée'
```

**CRITIQUE** : Toujours utiliser `EtatCommande.objects.create()` pour tracer les changements d'état. Chaque transition d'état crée un enregistrement d'historique avec `date_debut`, `date_fin`, `operateur`, et `enum_etat` (FK vers la définition d'état).

### Système de Types d'Opérateurs
`parametre.models.Operateur` lie les `User` Django aux rôles d'opérateurs :
- Choix `type_operateur` : `'CONFIRMATION'`, `'PREPARATION'`, `'LOGISTIQUE'`, `'SUPERVISEUR'`
- Les vues vérifient le type d'opérateur : `Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')`
- Les middlewares valident les profils d'opérateurs : `config.middleware.UserTypeValidationMiddleware`

### Logique Métier Pilotée par Signaux
Les signaux Django (`post_save`, `pre_save`) pilotent l'automatisation critique :

- `commande/signals.py` : Recalcule automatiquement les totaux de commande lorsque `compteur` (compteur d'upsell) ou `frais_livraison` changent
- `article/signals.py` : Crée les genres par défaut sur `post_migrate`
- Pattern : Stocker les anciennes valeurs dans `pre_save` (`instance._old_compteur`), comparer dans `post_save`, déclencher le recalcul avec flag `_recalcul_en_cours` pour éviter la récursion

### Stack de Middlewares Personnalisés
`config/middleware.py` et `commande/middleware.py` implémentent :
- **SessionTimeoutMiddleware** : Déconnexion automatique des utilisateurs inactifs
- **DelayedConfirmationMiddleware** : Traite les confirmations différées toutes les 10s (limité par cache)
- **CSRFDebugMiddleware** : Débogage des problèmes CSRF en développement
- **UserTypeValidationMiddleware** : Valide les profils d'opérateurs à chaque requête

## Workflows de Développement

### Configuration de la Base de Données
```powershell
# PostgreSQL requis (configuré dans .env)
python manage.py migrate
python manage.py createsuperuser
```

### Commandes de Gestion
Situées dans `commande/management/commands/` :
- `populate_etats_commande.py` - Initialiser les états de commande (exécuter après migration)
- `process_delayed_confirmations.py` - Traiter les confirmations différées (tâche cron)
- `recalculer_frais_livraison.py` - Recalculer les frais de livraison

**Pattern** : Les commandes personnalisées étendent `BaseCommand`, implémentent `handle()`, utilisent `self.stdout.write(self.style.SUCCESS('...'))`

### Lancement du Serveur
```powershell
python manage.py runserver
# Ou avec rechargement automatique Tailwind :
python manage.py tailwind start  # Terminal 1
python manage.py runserver       # Terminal 2
```

### Synchronisation avec Google Sheets
`synchronisation/google_sheet_sync.py` importe les commandes depuis Google Sheets :
- Nécessite `credentials.json` (compte de service Google)
- Détection des doublons via `num_cmd` et `id_yz`
- Les commandes protégées (déjà traitées) ne peuvent pas être mises à jour
- Imports encapsulés dans des transactions : `with transaction.atomic()`

## Conventions de Code

### Patterns de Modèles
```python
class MyModel(models.Model):
    class Meta:
        verbose_name = "Nom d'affichage"
        verbose_name_plural = "Noms d'affichage Pluriel"
        ordering = ['nom_champ']
```

Tous les modèles utilisent des champs `verbose_name` en français. Suivez cette convention systématiquement.

### Gestion des Transactions
Utilisez le décorateur `@transaction.atomic` ou `with transaction.atomic():` pour les opérations multi-étapes impliquant des changements d'état de commande, des mouvements de stock ou des modifications de panier.

### Journalisation (Logging)
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"[Contexte] Message: {data}")
logger.error(f"Erreur: {str(e)}")
```

La journalisation est configurée dans `config/settings.py` avec des gestionnaires de fichiers dans le répertoire `logs/`.

### Décorateurs de Vues
- `@login_required` - Toutes les vues nécessitent une authentification
- `@user_passes_test(is_admin)` - Vues réservées aux administrateurs (synchronisation, diagnostics)
- Gestion d'erreurs personnalisée : décorateur `Prepacommande.views.handle_ajax_errors` pour les vues AJAX

### Pattern de Réponse AJAX
```python
if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return JsonResponse({'success': True, 'data': result})
return redirect('nom_vue')
```

### Optimisation des Querysets
Toujours utiliser `select_related()` pour les FK, `prefetch_related()` pour les FK inverses/M2M :
```python
commandes = Commande.objects.select_related(
    'client', 'ville', 'ville__region'
).prefetch_related('paniers__article', 'etats__enum_etat')
```

## Pièges Critiques

### 1. Recalcul des Totaux de Commande
La modification de `Commande.compteur` ou `Commande.frais_livraison` déclenche un recalcul automatique des totaux via les signaux. Ne calculez jamais manuellement `total_cmd` sans considérer la chaîne de signaux.

### 2. Protection des Transitions d'État
Ne modifiez jamais directement `EtatCommande.date_fin`. Utilisez la logique de transition d'état appropriée :
```python
# Fermer l'état actuel
current_state.date_fin = timezone.now()
current_state.save()

# Créer un nouvel état
EtatCommande.objects.create(
    commande=order,
    enum_etat=new_state,
    operateur=operator,
    date_debut=timezone.now()
)
```

### 3. Variantes d'Articles dans le Panier
`commande.models.Panier` est lié à la fois à `Article` et `VarianteArticle`. Vérifiez toujours si une variante existe :
```python
if panier.variante:
    couleur = panier.variante.couleur
    pointure = panier.variante.pointure
```

### 4. Clés Étrangères Ville et Région
`Commande.ville` est une FK vers `Ville`, qui a une FK vers `Region`. L'import initial stocke `ville_init` (chaîne) - une conversion est nécessaire pour l'assignation FK appropriée.

### 5. Configuration CSRF
Nom de cookie CSRF personnalisé : `yz_csrf_token` (voir `settings.py`). Les requêtes AJAX doivent inclure l'en-tête `X-CSRFToken`.

### 6. Fichiers Statiques en Production
Utilise `whitenoise` pour servir les fichiers statiques. Exécutez `python manage.py collectstatic` avant le déploiement.

### 7. Contrôle d'Accès aux APIs
Les APIs (ex: `api_panier_commande`) vérifient l'autorisation de deux façons :
- Utilisateurs admin/staff : `request.user.is_staff` ou `request.user.is_superuser`
- Utilisateurs opérateurs : existence d'un profil `Operateur` lié à `request.user`

Toujours autoriser les deux types pour éviter les erreurs 403 avec les comptes administrateurs.

## Tests & Débogage

### Debug Toolbar
La barre d'outils de débogage Django est activée en développement. Accès via `/__debug__/`.

### Débogage CSRF
Définissez `DEBUG=True` et vérifiez les logs pour les entrées `[CSRF Debug]` provenant de `CSRFDebugMiddleware`.

### Débogage de la Synchronisation Google Sheets
Déclenchez une synchronisation manuelle depuis le tableau de bord `/synchronisation/`. Consultez le modèle `SyncLog` pour les logs d'exécution détaillés incluant le champ JSON `execution_details`.

## Raccourcis de Navigation

- **Modèle de commande & machine à états** : `commande/models.py`
- **Signaux de gestion d'état** : `commande/signals.py`
- **Logique middleware** : `config/middleware.py`, `commande/middleware.py`
- **Routage URL** : `config/urls.py` + `urls.py` au niveau des apps
- **Paramètres** : `config/settings.py`
- **Commandes de gestion** : `commande/management/commands/`
- **Workflows détaillés** : `docs/WORKFLOW_COMPLET.md`
- **Documentation des interfaces** : `docs/INTERFACE_*.md`

## Documentation Externe

- [Workflow Complet](../docs/WORKFLOW_COMPLET.md) - Cycle de vie complet des commandes
- [Configuration Cloudflare Tunnel](../docs/CLOUDFLARE_TUNNEL.md) - Déploiement avec tunneling
- [Documentation des Interfaces](../docs/README.md) - Descriptions de toutes les interfaces

## Lors des Modifications

1. **Changements d'état de commande** : Vérifier l'impact des signaux, valider la création de l'historique d'état
2. **Nouveaux modèles** : Ajouter `verbose_name` en français, implémenter `__str__()`, ajouter à l'admin
3. **Nouvelles vues** : Ajouter `@login_required`, vérifier le type d'opérateur si spécifique au rôle
4. **Requêtes de base de données** : Profiler avec Debug Toolbar, optimiser avec `select_related`/`prefetch_related`
5. **Calculs de totaux de commande** : Considérer `compteur`, `frais_livraison`, et le recalcul basé sur les signaux
6. **Commandes de gestion** : Documenter dans la docstring de la commande, ajouter au README pertinent
7. **Points de terminaison AJAX** : Retourner une structure JSON cohérente, gérer les requêtes AJAX et normales
