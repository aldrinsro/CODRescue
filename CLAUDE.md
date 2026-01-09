# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CODRescue is a Django-based e-commerce order management system for YZ-PRESTATION. It handles the complete order lifecycle: order confirmation, preparation, logistics, and delivery tracking. The system is localized in French and operates on Morocco time (Africa/Casablanca).

## Common Commands

```bash
# Development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create cache table (required for caching)
python manage.py createcachetable

# Tailwind CSS development (in theme/static_src/)
cd theme/static_src && npm run dev   # Watch mode
cd theme/static_src && npm run build # Production build

# Run tests
pytest
pytest article/tests.py -v  # Single app

# Static files
python manage.py collectstatic
```

## Key Management Commands

```bash
# Order states initialization
python manage.py load_default_etats_commande
python manage.py populate_etats_commande

# Delayed confirmations (runs every 5 min in production)
python manage.py process_delayed_confirmations

# Article/Product management
python manage.py import_articles_csv
python manage.py init_categories_genres
python manage.py gerer_promotions

# Synchronization diagnostics
python manage.py diagnostic_etats
python manage.py sync_verbose
```

## Architecture

### Django Apps

| App | Purpose | URL Prefix |
|-----|---------|------------|
| `commande` | Core order model, states, operations | `/commande/` |
| `article` | Products, variants, categories, pricing | `/article/` |
| `client` | Customer management | `/client/` |
| `operatConfirme` | Confirmation operator interface | `/operateur-confirme/` |
| `operatLogistic` | Logistics operator interface | `/operateur-logistique/` |
| `Prepacommande` | Order preparation interface | `/operateur-preparation/` |
| `Superpreparation` | Supervisor dashboard | `/Superpreparation/` |
| `livraison` | Delivery tracking | `/livraison/` |
| `parametre` | System settings, operators, cities | `/parametre/` |
| `synchronisation` | External data sync (Google Sheets) | `/synchronisation/` |
| `kpis` | Performance metrics | `/kpis/` |
| `chatbot` | n8n webhook integration | `/chatbot/` |

## Database Schema - Complete Table Reference

### App `commande` - Orders & Operations

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `commande_enumetatcmd` | EnumEtatCmd | `id`, `libelle`, `ordre`, `couleur` | Order state definitions |
| `commande_commande` | Commande | `id`, `num_cmd`, `id_yz`, `date_cmd`, `total_cmd`, `adresse`, `client_id`, `ville_id`, `source`, `payement`, `frais_livraison`, `Date_livraison`, `Date_paiement`, `envoi_id` | Main orders table |
| `commande_panier` | Panier | `id`, `commande_id`, `article_id`, `variante_id`, `quantite`, `prix_panier`, `sous_total`, `remise_appliquer`, `type_remise_appliquee`, `type_prix_gele` | Order line items (cart) |
| `commande_remisepanier` | RemisePanier | `id`, `panier_id`, `type_remise`, `valeur_remise`, `montant_applique`, `raison_remise`, `operateur_id` | Custom discounts on cart items |
| `commande_etatcommande` | EtatCommande | `id`, `commande_id`, `enum_etat_id`, `date_debut`, `date_fin`, `commentaire`, `operateur_id`, `date_fin_delayed` | Order state history/tracking |
| `commande_operation` | Operation | `id`, `type_operation`, `date_operation`, `conclusion`, `commande_id`, `operateur_id`, `commentaire` | Operator actions (calls, SMS, etc.) |
| `commande_envoi` | Envoi | `id`, `numero_envoi`, `date_envoi`, `date_livraison_prevue`, `date_livraison_effective`, `status`, `region_id`, `nb_commandes` | Shipment batches |
| `commande_etatarticlerenvoye` | EtatArticleRenvoye | `id`, `commande_id`, `article_id`, `etat_id`, `quantite` | Returned article states |
| `commande_etiquettetemplate` | EtiquetteTemplate | `id`, `name`, `width`, `height`, margins, fonts, colors, barcode settings | Label printing templates |
| `commande_articleretourne` | ArticleRetourne | `id`, `commande_id`, `article_id`, `variante_id`, `quantite_retournee`, `prix_unitaire_origine`, `raison_retour`, `statut_retour` | Returned articles tracking |

### App `article` - Products & Inventory

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `article_categorie` | Categorie | `id`, `nom`, `description`, `actif` | Product categories (SANDALES, BASKET, etc.) |
| `article_genre` | Genre | `id`, `nom`, `description`, `actif` | Target genres (HOMME, FEMME, FILLE, GARCON) |
| `article_pointure` | Pointure | `id`, `pointure`, `ordre`, `actif` | Shoe sizes |
| `article_couleur` | Couleur | `id`, `nom`, `code_hex`, `actif` | Colors with hex codes |
| `article_article` | Article | `id`, `nom`, `reference`, `modele`, `prix_unitaire`, `prix_achat`, `prix_actuel`, `categorie_id`, `genre_id`, `phase`, `isUpsell`, `prix_upsell_1` to `prix_upsell_4`, `Prix_liquidation`, `prix_remise_1` to `prix_remise_4`, `image`, `image_url` | Main products table |
| `article_variantearticle` | VarianteArticle | `id`, `article_id`, `reference_variante`, `couleur_id`, `pointure_id`, `qte_disponible`, `actif` | Product variants (color+size combinations) |
| `article_mouvementstock` | MouvementStock | `id`, `article_id`, `variante_id`, `type_mouvement`, `quantite`, `qte_apres_mouvement`, `commande_associee_id`, `operateur_id` | Stock movement history |
| `article_promotion` | Promotion | `id`, `nom`, `pourcentage_reduction`, `date_debut`, `date_fin`, `active`, `cree_par_id` | Promotional campaigns |
| `article_promotion_articles` | M2M | `promotion_id`, `article_id` | Many-to-many: promotions <-> articles |

### App `client` - Customers

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `client_client` | Client | `id`, `nom`, `prenom`, `numero_tel` (unique), `email`, `adresse`, `note`, `is_active` | Customer records |

### App `parametre` - System Configuration

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `parametre_region` | Region | `id`, `nom_region`, `actif` | Delivery regions |
| `parametre_ville` | Ville | `id`, `nom`, `frais_livraison`, `Delai_livraison_min`, `Delai_livraison_max`, `region_id` | Cities with delivery fees |
| `parametre_livreur` | livreur | `id`, `nom` | Delivery drivers |
| `parametre_operateur` | Operateur | `id`, `user_id`, `nom`, `prenom`, `mail`, `type_operateur`, `photo`, `telephone`, `actif` | System operators/users |
| `parametre_historiquemotdepasse` | HistoriqueMotDePasse | `id`, `operateur_id`, `administrateur_id`, `date_modification`, `adresse_ip` | Password change audit log |

### App `synchronisation` - Google Sheets Integration

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `synchronisation_googlesheetconfig` | GoogleSheetConfig | `id`, `sheet_url`, `sheet_name`, `is_active`, `last_processed_row` | Google Sheets connection config |
| `synchronisation_synclog` | SyncLog | `id`, `sheet_config_id`, `sync_date`, `status`, `records_imported`, `new_orders_created`, `existing_orders_updated`, `errors` | Sync execution logs |

### App `kpis` - Performance Metrics

| Table Name | Model | Key Columns | Description |
|------------|-------|-------------|-------------|
| `kpis_kpiconfiguration` | KPIConfiguration | `id`, `nom_parametre`, `categorie`, `valeur`, `description`, `unite`, `valeur_min`, `valeur_max` | KPI thresholds and settings |

### Django Built-in Tables

| Table Name | Description |
|------------|-------------|
| `auth_user` | Django users (linked to `parametre_operateur` via `user_id`) |
| `auth_group` | User groups (operateur_confirme, operateur_logistique, etc.) |
| `django_session` | Session storage |
| `yz_cache_table` | Database cache table |

## Key Business Logic

### Order State Flow (EnumEtatCmd)
States defined in `commande_enumetatcmd.libelle`:
- Non affectee -> Affectee -> En cours de confirmation -> Confirmee
- Alternative paths: Erronee, Doublon, Report de confirmation, Confirmation decalee
- Delivery states: A imprimer -> En preparation -> Collectee -> Emballee -> Validee -> En livraison -> Livree/Retournee

### Pricing System (Article)
- `prix_unitaire`: Base price
- `prix_actuel`: Current price (after promotions)
- `prix_upsell_1` to `prix_upsell_4`: Tiered upsell prices based on `Commande.compteur`
- `Prix_liquidation`: Liquidation phase price
- `prix_remise_1` to `prix_remise_4`: Predefined discount prices

### Operator Types (parametre_operateur.type_operateur)
- `CONFIRMATION`: Order confirmation operators
- `LOGISTIQUE`: Logistics/delivery operators
- `PREPARATION`: Order preparation operators
- `SUPERVISEUR_PREPARATION`: Preparation supervisors
- `ADMIN`: System administrators

## User Types & Interfaces

Each operator type has a dedicated interface:
- CONFIRMATION operators: Order validation, client communication
- PREPARATION operators: Order assembly, stock management
- LOGISTIQUE operators: Shipping, delivery tracking, returns
- SUPERVISEUR_PREPARATION: Team oversight, KPIs
- ADMIN: Full system access via `/admin/` and `/parametre/`

## Technical Stack

- **Backend**: Django 5.1.7, Django REST Framework, PostgreSQL
- **Frontend**: Tailwind CSS 3.4, vanilla JavaScript
- **Caching**: Database cache (yz_cache_table)
- **Sessions**: Cached DB sessions with 24h timeout
- **External**: Google Sheets sync (gspread), n8n webhooks

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `GOOGLE_SHEET_URL`, `GOOGLE_APPLICATION_CREDENTIALS`
- `N8N_WEBHOOK_BASE`, `N8N_CHATBOT_WEBHOOK`

Settings in `config/settings.py` with `python-decouple` for env loading.

## Code Conventions

- French naming for business domain (commande, client, livraison, etc.)
- English for technical terms
- Models use verbose French names in Meta classes
- Templates in `templates/` directory organized by app
- Custom template tags in `app/templatetags/`
- Database table names follow Django convention: `appname_modelname` (lowercase)
