# Configuration et état complet du Chatbot (n8n) — CODRescue

Dernière mise à jour : 9 décembre 2025

Ce document rassemble l'ensemble des éléments nécessaires pour rendre le workflow n8n « Chatbot Webhook SQL query - Compatible Version » robuste et reproductible. Il contient :
- le diagnostic du problème rencontré
- le prompt système et utilisateur recommandés
- le JSON Schema à exiger pour les sorties de l'agent
- des exemples (few-shot)
- paramètres recommandés du modèle
- mapping `Respond to Webhook`
- checklist de tests et debugging
- bonnes pratiques mémoire / sessions
- **schéma complet de la base de données CODRescue**

---

## 1) Résumé du problème

Symptômes observés :
- n8n renvoyait l'erreur « Could not parse LLM output » ou « réponse non JSON ou vide ». Le modèle renvoyait du texte libre (ex : "Je suis prêt..."), et non un objet JSON structuré attendu par l'agent/les outils.
- Les réponses côté frontend pouvaient paraître « illogiques » ou incohérentes lorsque l'agent n'était pas contraint.

Cause principale : absence d'un prompt système précis et du format de sortie forcé (Require Specific Output Format). Le modèle produisait du texte naturel au lieu d'une structure JSON utilisable par n8n/LangChain.

---

## 2) Objectifs de la configuration

- Forcer des réponses structurées (JSON) pour permettre : exécution automatique de requêtes SQL, parsing fiable par n8n, et affichage stable côté frontend.
- Eviter les hallucinations et sorties non déterministes.
- Préserver la sécurité (pas d'UPDATE/DELETE sans validation).

---

## 3) Schéma complet de la base de données CODRescue

### 3.1) App `commande` - Commandes et Opérations

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `commande_enumetatcmd` | `id`, `libelle`, `ordre`, `couleur` | Définitions des états de commande |
| `commande_commande` | `id`, `num_cmd`, `id_yz`, `date_cmd`, `total_cmd`, `adresse`, `motif_annulation`, `date_creation`, `date_modification`, `last_sync_date`, `client_id`, `ville_init`, `ville_id`, `produit_init`, `source`, `compteur`, `payement`, `frais_livraison`, `Date_livraison`, `Date_paiement`, `envoi_id`, `origine` | Table principale des commandes |
| `commande_panier` | `id`, `commande_id`, `article_id`, `variante_id`, `quantite`, `prix_panier`, `sous_total`, `sous_total_remise`, `remise_appliquer`, `type_remise_appliquee`, `type_prix_gele` | Articles dans le panier (lignes de commande) |
| `commande_remisepanier` | `id`, `panier_id`, `type_remise`, `valeur_remise`, `montant_applique`, `raison_remise`, `date_application`, `operateur_id` | Remises personnalisées sur les paniers |
| `commande_etatcommande` | `id`, `commande_id`, `enum_etat_id`, `date_debut`, `date_fin`, `commentaire`, `operateur_id`, `date_fin_delayed` | Historique et suivi des états de commande |
| `commande_operation` | `id`, `type_operation`, `date_operation`, `conclusion`, `commande_id`, `operateur_id`, `commentaire` | Opérations des opérateurs (appels, SMS, WhatsApp) |
| `commande_envoi` | `id`, `commande_id`, `region_id`, `date_envoi`, `date_livraison_prevue`, `date_livraison_effective`, `status`, `numero_envoi`, `operateur_creation_id`, `date_creation`, `date_modification`, `nb_commandes` | Lots d'envoi/expédition |
| `commande_etatarticlerenvoye` | `id`, `commande_id`, `article_id`, `etat_id`, `quantite`, `date_maj` | États des articles renvoyés |
| `commande_etiquettetemplate` | `id`, `name`, `width`, `height`, `margin_*`, `font_*`, `color_*`, `barcode_*`, `qr_size`, `show_*`, `is_active` | Templates d'étiquettes pour impression |
| `commande_articleretourne` | `id`, `commande_id`, `article_id`, `variante_id`, `quantite_retournee`, `prix_unitaire_origine`, `raison_retour`, `date_retour`, `operateur_retour_id`, `statut_retour`, `date_traitement`, `operateur_traitement_id`, `commentaire_traitement` | Suivi des articles retournés |

**Valeurs importantes :**
- `commande_commande.source` : 'Appel', 'Whatsapp ', 'SMS', 'Email', 'Facebook', 'Youcan', 'Shopify'
- `commande_commande.payement` : 'Non payé', 'Payé', 'Remboursée'
- `commande_commande.origine` : 'OC' (Opérateur Confirmation), 'ADMIN', 'SYNC' (Synchronisation)
- `commande_operation.type_operation` : 'APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'Vocal Whatsapp', 'ENVOI_SMS'
- `commande_articleretourne.statut_retour` : 'en_attente', 'reintegre_stock', 'renvoye_preparation', 'defectueux', 'traite'

### 3.2) App `article` - Produits et Stock

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `article_categorie` | `id`, `nom`, `description`, `actif`, `date_creation`, `date_modification` | Catégories d'articles |
| `article_genre` | `id`, `nom`, `description`, `actif`, `date_creation`, `date_modification` | Genres cibles |
| `article_pointure` | `id`, `pointure`, `description`, `ordre`, `actif`, `date_creation`, `date_modification` | Pointures disponibles |
| `article_couleur` | `id`, `nom`, `code_hex`, `description`, `actif`, `date_creation`, `date_modification` | Couleurs avec codes hex |
| `article_article` | `id`, `nom`, `reference`, `modele`, `prix_unitaire`, `prix_achat`, `prix_actuel`, `categorie_id`, `genre_id`, `phase`, `description`, `image`, `image_url`, `date_creation`, `date_modification`, `actif`, `isUpsell`, `prix_upsell_1`, `prix_upsell_2`, `prix_upsell_3`, `prix_upsell_4`, `Prix_liquidation`, `prix_remise_1`, `prix_remise_2`, `prix_remise_3`, `prix_remise_4` | Table principale des produits |
| `article_variantearticle` | `id`, `article_id`, `reference_variante`, `couleur_id`, `pointure_id`, `qte_disponible`, `actif`, `date_creation`, `date_modification` | Variantes (combinaisons couleur/pointure) |
| `article_mouvementstock` | `id`, `article_id`, `variante_id`, `type_mouvement`, `quantite`, `qte_apres_mouvement`, `date_mouvement`, `commentaire`, `commande_associee_id`, `operateur_id` | Historique des mouvements de stock |
| `article_promotion` | `id`, `nom`, `description`, `pourcentage_reduction`, `date_debut`, `date_fin`, `active`, `cree_par_id`, `date_creation`, `date_modification` | Campagnes promotionnelles |
| `article_promotion_articles` | `id`, `promotion_id`, `article_id` | Relation M2M promotions <-> articles |

**Valeurs importantes :**
- `article_categorie.nom` : 'SANDALES', 'SABOT', 'CHAUSSURES', 'ESPARILLE', 'BASKET', 'MULES', 'PACK_SAC', 'BOTTE', 'ESCARPINS'
- `article_genre.nom` : 'HOMME', 'FEMME', 'FILLE', 'GARCON'
- `article_article.phase` : 'EN_COURS', 'LIQUIDATION', 'EN_TEST', 'PROMO'
- `article_mouvementstock.type_mouvement` : 'entree', 'sortie', 'ajustement_pos', 'ajustement_neg', 'inventaire', 'retour_client'

### 3.3) App `client` - Clients

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `client_client` | `id`, `nom`, `prenom`, `numero_tel` (UNIQUE), `email`, `adresse`, `date_creation`, `date_modification`, `note`, `is_active` | Fiches clients |

### 3.4) App `parametre` - Configuration système

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `parametre_region` | `id`, `nom_region`, `actif` | Régions de livraison |
| `parametre_ville` | `id`, `nom`, `frais_livraison`, `Delai_livraison_min`, `Delai_livraison_max`, `region_id` | Villes avec frais de livraison |
| `parametre_livreur` | `id`, `nom` | Livreurs |
| `parametre_operateur` | `id`, `user_id`, `nom`, `prenom`, `mail`, `type_operateur`, `photo`, `adresse`, `telephone`, `date_creation`, `date_modification`, `actif` | Opérateurs/utilisateurs du système |
| `parametre_historiquemotdepasse` | `id`, `operateur_id`, `administrateur_id`, `date_modification`, `adresse_ip`, `commentaire` | Audit des changements de mot de passe |

**Valeurs importantes :**
- `parametre_operateur.type_operateur` : 'CONFIRMATION', 'LOGISTIQUE', 'PREPARATION', 'ADMIN', 'SUPERVISEUR_PREPARATION'

### 3.5) App `synchronisation` - Intégration Google Sheets

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `synchronisation_googlesheetconfig` | `id`, `sheet_url`, `sheet_name`, `is_active`, `created_at`, `updated_at`, `last_processed_row` | Configuration connexion Google Sheets |
| `synchronisation_synclog` | `id`, `sync_date`, `status`, `records_imported`, `errors`, `sheet_config_id`, `triggered_by`, `start_time`, `end_time`, `total_rows`, `processed_rows`, `skipped_rows`, `sheet_title`, `execution_details`, `new_orders_created`, `existing_orders_updated`, `existing_orders_skipped`, `duplicate_orders_found`, `protected_orders_count` | Logs de synchronisation |

**Valeurs importantes :**
- `synchronisation_synclog.status` : 'success', 'error', 'partial'

### 3.6) App `kpis` - Métriques de performance

| Table | Colonnes principales | Description |
|-------|---------------------|-------------|
| `kpis_kpiconfiguration` | `id`, `nom_parametre`, `categorie`, `valeur`, `description`, `unite`, `valeur_min`, `valeur_max`, `modifie_par_id`, `date_modification`, `date_creation` | Configuration des seuils KPI |

**Valeurs importantes :**
- `kpis_kpiconfiguration.categorie` : 'seuils', 'calcul', 'affichage'

### 3.7) Tables Django système

| Table | Description |
|-------|-------------|
| `auth_user` | Utilisateurs Django (lié à `parametre_operateur` via `user_id`) |
| `auth_group` | Groupes : operateur_confirme, operateur_logistique, operateur_preparation, superviseur, admin |
| `django_session` | Sessions utilisateurs |
| `yz_cache_table` | Cache base de données |

### 3.8) Relations clés entre tables

```
commande_commande.client_id → client_client.id
commande_commande.ville_id → parametre_ville.id
commande_commande.envoi_id → commande_envoi.id
commande_panier.commande_id → commande_commande.id
commande_panier.article_id → article_article.id
commande_panier.variante_id → article_variantearticle.id
commande_etatcommande.commande_id → commande_commande.id
commande_etatcommande.enum_etat_id → commande_enumetatcmd.id
commande_etatcommande.operateur_id → parametre_operateur.id
article_article.categorie_id → article_categorie.id
article_article.genre_id → article_genre.id
article_variantearticle.article_id → article_article.id
article_variantearticle.couleur_id → article_couleur.id
article_variantearticle.pointure_id → article_pointure.id
parametre_ville.region_id → parametre_region.id
parametre_operateur.user_id → auth_user.id
```

### 3.9) États de commande (commande_enumetatcmd.libelle)

Flux principal :
1. `Non affectée` → `Affectée` → `En cours de confirmation` → `Confirmée`
2. Alternatives : `Erronée`, `Doublon`, `Report de confirmation`, `Confirmation décalée`
3. États livraison : `À imprimer` → `En préparation` → `Collectée` → `Emballée` → `Validée` → `En livraison` → `Livrée` / `Retournée`

---

## 4) Configuration du ReAct Agent n8n (avec outils Postgres)

### 4.1) Architecture du workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Webhook   │────▶│  AI Agent   │────▶│ Respond to Webhook  │
│    POST     │     │ ReAct Agent │     │       JSON          │
└─────────────┘     └──────┬──────┘     └─────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
   ┌───────────┐   ┌────────────┐   ┌─────────────┐
   │  Google   │   │  Postgres  │   │  3 Outils   │
   │  Gemini   │   │Chat Memory │   │  Postgres   │
   └───────────┘   └────────────┘   └─────────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                          ▼               ▼               ▼
                   ┌────────────┐  ┌────────────┐  ┌────────────┐
                   │Tables liste│  │Table schema│  │Execute query│
                   └────────────┘  └────────────┘  └────────────┘
```

### 4.2) Configuration du nœud AI Agent

| Paramètre | Valeur |
|-----------|--------|
| **Agent** | `ReAct Agent` ✅ |
| **Source for Prompt** | `Define below` |
| **Prompt (User Message)** | `{{ $json.body.chatInput }}` |

#### Options à ajouter (cliquer sur "Add Option")

1. **System Message** ✅ (OBLIGATOIRE)
2. **Max Iterations** : `10`
3. **Return Intermediate Steps** : `false` (en production)

### 4.3) System Message (à coller dans "System Message")

```
Tu es CODRescue Assistant, un assistant SQL pour l'analyse de données e-commerce.

OUTILS DISPONIBLES :
- "Tables liste" : Liste toutes les tables de la base de données
- "Table schema" : Affiche la structure d'une table (colonnes, types)
- "Execute query" : Exécute une requête SQL SELECT

PROCESSUS POUR CHAQUE QUESTION :
1. Si tu ne connais pas les tables, utilise "Tables liste"
2. Si tu as besoin de connaître les colonnes, utilise "Table schema"
3. Construis ta requête SQL SELECT
4. Exécute avec "Execute query"
5. Réponds en français avec les résultats

RÈGLES OBLIGATOIRES :
- Réponds TOUJOURS en français
- Formate les montants avec "DH" (ex: 1500 DH)
- Formate les dates en JJ/MM/AAAA
- LIMITE toujours à 50 lignes (LIMIT 50)
- N'exécute JAMAIS de DELETE, UPDATE, ALTER, DROP
- Sois concis et précis

TABLES PRINCIPALES :
- commande_commande : Commandes (id, num_cmd, total_cmd, date_cmd, client_id, ville_id)
- commande_panier : Lignes de commande (commande_id, article_id, quantite, prix_panier)
- commande_etatcommande : États des commandes (commande_id, enum_etat_id, date_debut, date_fin)
- commande_enumetatcmd : Définition des états (id, libelle)
- article_article : Produits (id, nom, reference, prix_unitaire, categorie_id)
- article_variantearticle : Variantes (article_id, couleur_id, pointure_id, qte_disponible)
- client_client : Clients (id, nom, prenom, numero_tel)
- parametre_ville : Villes (id, nom, frais_livraison)
- parametre_operateur : Opérateurs (id, nom, prenom, type_operateur)

RÈGLES SQL IMPORTANTES :
- L'état ACTUEL d'une commande : WHERE date_fin IS NULL dans commande_etatcommande
- Jointure états : commande_etatcommande e JOIN commande_enumetatcmd ee ON e.enum_etat_id = ee.id
- Articles actifs : WHERE actif = true
- Recherche texte : utiliser ILIKE '%terme%'

VALEURS DES ÉTATS DE COMMANDE (commande_enumetatcmd.libelle) :
'Non affectée', 'Affectée', 'En cours de confirmation', 'Confirmée', 'Erronée', 'Doublon', 'À imprimer', 'En préparation', 'En livraison', 'Livrée', 'Retournée'

VALEURS SOURCES (commande_commande.source) :
'Appel', 'Whatsapp ', 'SMS', 'Email', 'Facebook', 'Youcan', 'Shopify'

EXEMPLES DE REQUÊTES :

Commandes par état :
SELECT COUNT(*) FROM commande_commande c
JOIN commande_etatcommande e ON e.commande_id = c.id
JOIN commande_enumetatcmd ee ON e.enum_etat_id = ee.id
WHERE ee.libelle = 'Non affectée' AND e.date_fin IS NULL;

Chiffre d'affaires du jour :
SELECT SUM(total_cmd) AS ca FROM commande_commande WHERE date_cmd = CURRENT_DATE;

Top articles vendus :
SELECT a.nom, SUM(p.quantite) AS qte FROM commande_panier p
JOIN article_article a ON p.article_id = a.id
GROUP BY a.id, a.nom ORDER BY qte DESC LIMIT 10;

Si la question n'est pas claire, demande une précision.
```

### 4.4) Human Message / Prompt (User Message)

Dans le champ **"Prompt (User Message)"**, mettez cette expression :

```
{{ $json.body.chatInput }}
```

Cela récupère la question envoyée par le frontend.

### 4.5) Configuration des 3 outils Postgres

#### Outil 1 : Tables liste

| Paramètre | Valeur |
|-----------|--------|
| **Credential** | `Postgres account` (votre connexion yzrescue_db) |
| **Tool Description** | `Set Manually` |
| **Description** | `Liste toutes les tables disponibles dans la base de données` |
| **Operation** | `Execute Query` |
| **Query** | `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name` |

#### Outil 2 : Table schema

| Paramètre | Valeur |
|-----------|--------|
| **Credential** | `Postgres account` |
| **Tool Description** | `Set Manually` |
| **Description** | `Affiche les colonnes et types d'une table. Paramètre: table_name (nom de la table)` |
| **Operation** | `Execute Query` |
| **Query** | `SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position` |
| **Query Parameters** | `{{ $fromAI('table_name', 'nom de la table') }}` |

#### Outil 3 : Execute query

| Paramètre | Valeur |
|-----------|--------|
| **Credential** | `Postgres account` |
| **Tool Description** | `Set Manually` |
| **Description** | `Exécute une requête SQL SELECT. Paramètres: fields (colonnes), table_name (table), condition (WHERE optionnel), group_by (GROUP BY optionnel), order_by (ORDER BY optionnel), limit (LIMIT, défaut 50)` |
| **Operation** | `Execute Query` |
| **Query** | Voir ci-dessous |

**Query pour Execute query :**
```sql
SELECT {{ $fromAI('fields', '*') }}
FROM {{ $fromAI('table_name', 'commande_commande') }}
{{ $fromAI('joins', '') }}
{{ $fromAI('condition') && $fromAI('condition').trim() ? 'WHERE ' + $fromAI('condition') : '' }}
{{ $fromAI('group_by') && $fromAI('group_by').trim() ? 'GROUP BY ' + $fromAI('group_by') : '' }}
{{ $fromAI('order_by') && $fromAI('order_by').trim() ? 'ORDER BY ' + $fromAI('order_by') : '' }}
LIMIT {{ $fromAI('limit', '50') }}
```

### 4.6) Configuration Postgres Chat Memory

| Paramètre | Valeur |
|-----------|--------|
| **Credential** | `Postgres account` |
| **Session ID** | `{{ $json.body.sessionId }}` |
| **Context Window Length** | `10` (derniers messages) |

### 4.7) Configuration Respond to Webhook

| Paramètre | Valeur |
|-----------|--------|
| **Respond With** | `JSON` |
| **Response Body** | `{{ { "output": $json.output } }}` |

---

## 5) Schéma de la base (pour référence - déjà découvert par le SQL Agent)

---

## 5) Prompt utilisateur recommandé (champ `Prompt` / User Message)

Le prompt utilisateur peut rester court (il sera complété par le system prompt). Exemple :

```
Vous êtes un assistant SQL spécialisé dans l'analyse de données e-commerce pour CODRescue. Répondez en français et soyez précis.
```

Mais il est préférable de fournir quelques détails additionnels ou un contexte (ex : période demandée) depuis le frontend dans `chatInput`.

---

## 6) JSON Schema (Require Specific Output Format)

Collez ce JSON Schema dans l'option "Require Specific Output Format" du nœud `AI Agent` :

```json
{
  "type": "object",
  "properties": {
    "answer": { "type": "string", "minLength": 1 },
    "sql": { "anyOf": [{ "type": "string" }, { "type": "null" }] },
    "rows": { "anyOf": [{ "type": "array", "items": { "type": "object" } }, { "type": "null" }] },
    "question": { "anyOf": [{ "type": "string" }, { "type": "null" }] }
  },
  "required": ["answer","sql","rows"],
  "additionalProperties": false
}
```

Ce schéma force un objet JSON exact contenant `answer`, `sql` et `rows` (ou `question` pour clarifications). n8n / LangChain valideront le format et échoueront si le modèle produit du texte libre.

---

## 7) Few‑shot : exemples à inclure dans le prompt (apprendre au modèle)

Ajoutez ces exemples après le prompt système pour guider l'agent :

```
Exemple 1 - Comptage simple:
User: "Combien d'articles existe-t-il dans le catalogue ?"
Réponse attendue:
{"answer":"Le nombre total d'articles est 1234.","sql":"SELECT COUNT(*) AS cnt FROM article_article WHERE actif = true;","rows":[{"cnt":1234}]}

Exemple 2 - Articles les plus vendus:
User: "Quels sont les 3 articles les plus vendus ce mois ?"
Réponse attendue:
{"answer":"Les 3 articles les plus vendus ce mois sont...","sql":"SELECT a.nom, a.reference, SUM(p.quantite) AS total_vendu FROM commande_panier p JOIN article_article a ON p.article_id = a.id JOIN commande_commande c ON p.commande_id = c.id WHERE c.date_cmd >= date_trunc('month', CURRENT_DATE) GROUP BY a.id, a.nom, a.reference ORDER BY total_vendu DESC LIMIT 3;","rows":[{"nom":"Sandale X","reference":"SAND-001","total_vendu":50}]}

Exemple 3 - Commandes par état:
User: "Combien de commandes sont en attente de livraison ?"
Réponse attendue:
{"answer":"Il y a 45 commandes en attente de livraison.","sql":"SELECT COUNT(*) AS cnt FROM commande_commande c JOIN commande_etatcommande e ON e.commande_id = c.id JOIN commande_enumetatcmd ee ON e.enum_etat_id = ee.id WHERE ee.libelle = 'En livraison' AND e.date_fin IS NULL;","rows":[{"cnt":45}]}

Exemple 4 - Chiffre d'affaires:
User: "Quel est le chiffre d'affaires du mois ?"
Réponse attendue:
{"answer":"Le chiffre d'affaires du mois est de 125000 DH.","sql":"SELECT SUM(total_cmd) AS ca FROM commande_commande WHERE date_cmd >= date_trunc('month', CURRENT_DATE);","rows":[{"ca":125000}]}

Exemple 5 - Stock faible:
User: "Quels articles ont un stock inférieur à 10 ?"
Réponse attendue:
{"answer":"Voici les articles avec un stock faible...","sql":"SELECT a.nom, a.reference, SUM(v.qte_disponible) AS stock FROM article_article a JOIN article_variantearticle v ON v.article_id = a.id WHERE a.actif = true GROUP BY a.id, a.nom, a.reference HAVING SUM(v.qte_disponible) < 10 ORDER BY stock ASC LIMIT 20;","rows":[{"nom":"Article X","reference":"REF-001","stock":5}]}

Exemple 6 - Clarification:
User: "Montre-moi les ventes."
Réponse attendue:
{"answer":"clarify","sql":null,"rows":null,"question":"Veuillez préciser la période souhaitée (ex: aujourd'hui, cette semaine, ce mois) et ce que vous voulez voir (nombre de commandes, chiffre d'affaires, articles vendus)."}

Exemple 7 - Performance opérateur:
User: "Combien de commandes a traité l'opérateur Ahmed aujourd'hui ?"
Réponse attendue:
{"answer":"L'opérateur Ahmed a traité 23 commandes aujourd'hui.","sql":"SELECT COUNT(*) AS cnt FROM commande_etatcommande e JOIN parametre_operateur o ON e.operateur_id = o.id WHERE o.prenom ILIKE '%Ahmed%' AND e.date_debut::date = CURRENT_DATE;","rows":[{"cnt":23}]}
```

---

## 8) Paramètres modèle recommandés

- Temperature : 0.0 → 0.2 (0.0 pour production, comportement déterministe)
- Max tokens / length : 1024 (ou selon modèle disponible)
- Top_p : 0.8 (optionnel)
- Max iterations (si agent plan/execute) : 5–10
- Timeout : 30–60s (si les requêtes SQL peuvent être longues)

Réduire la temperature réduit le risque de réponses non structurées.

---

## 9) Mapping `Respond to Webhook` (exemples d'expressions)

Dans le nœud `Respond to Webhook` :
- `Respond With` → `JSON`
- `Response Body` (mode expression) :

Si l'objet final est exposé par le nœud `AI Agent` dans la propriété `output` :

```
{{ $node["AI Agent"].json["output"] }}
```

Si l'AI retourne du texte dans une structure `response.generations...text` (format modèle), et que vous voulez renvoyer ce texte brut temporairement :

```
{{ { "output": $node["AI Agent"].json["response"]["generations"][0].generations[0].text } }}
```

Remarque : préférez renvoyer l'objet JSON validé par le schéma. Le fallback texte est uniquement pour debug rapide.

---

## 10) Mémoire / Session

- Assurez-vous que le nœud Memory (ex : `Simple Memory` ou `Postgres Chat Memory`) possède une Session ID valide. Exemple d'expression :

```
{{ $json.body.sessionId }}
```

- Conservez une fenêtre contextuelle courte (context window = 10 derniers messages) pour éviter que l'agent ne soit surchargé.

---

## 11) Tests et procédure de debugging (pas à pas)

1. Exécutez localement le nœud `AI Agent` (bouton `Execute Step`) et inspectez `Output` et `intermediateSteps`.
2. Vérifiez que la propriété exposée (`output`) contient un JSON valide conforme au schema.
3. Si la sortie n'est pas JSON :
   - baissez `temperature` à 0.0
   - ajoutez en tête du prompt : "REPLY WITH ONLY THE JSON OBJECT AND NOTHING ELSE." (en majuscules si besoin)
   - réexécutez.
4. Si le modèle répond par une question de clarification (format `answer: "clarify"`), redirigez la question vers le frontend puis renvoyez la nouvelle requête.
5. Test d'intégration : envoyez une requête depuis le frontend (ex : powershell ou via l'UI) et vérifiez affichage correct dans le chat.

Exemple PowerShell pour tester webhook :

```powershell
$body = @{ chatInput = 'je veux le nombre total des articles'; sessionId = 'test-session-001' } | ConvertTo-Json

Invoke-WebRequest -Uri 'https://YOUR_WEBHOOK_URL' -Method POST -Body $body -ContentType 'application/json'
```

Vérifiez la réponse retournée par n8n : JSON conforme, puis le frontend affichera le champ `answer` ou formatera `rows`.

---

## 12) Checklist de production

- [ ] System Prompt collé (avec schéma DB complet)
- [ ] JSON Schema activé
- [ ] Few-shot ajouté (7 exemples)
- [ ] Temperature réglée à 0.0–0.2
- [ ] Memory Session configurée
- [ ] Tools SQL (Execute Query, Table Schema, Table List) connectés & sélectionnés
- [ ] Respond to Webhook mappe l'objet JSON validé
- [ ] Tests unitaires et d'intégration effectués

---

## 13) Bonnes pratiques et recommandations

- Le schéma complet de la base est maintenant inclus dans le prompt système pour réduire les erreurs de noms de tables/colonnes.
- Ne pas exposer les credentials en clair dans les prompts ou logs.
- Journaliser (`logging`) chaque `sql` exécutée et son résultat pour audit.
- Pour des requêtes lourdes, considérer la mise en cache des réponses fréquemment demandées.
- Utiliser `ILIKE` pour les recherches texte insensibles à la casse (PostgreSQL).
- Toujours filtrer par `actif = true` pour les articles/variantes sauf si demandé explicitement.

---

## 14) Requêtes SQL utiles (templates)

### Commandes du jour
```sql
SELECT c.id_yz, c.num_cmd, c.total_cmd, cl.nom, cl.prenom, ee.libelle AS etat
FROM commande_commande c
JOIN client_client cl ON c.client_id = cl.id
JOIN commande_etatcommande e ON e.commande_id = c.id AND e.date_fin IS NULL
JOIN commande_enumetatcmd ee ON e.enum_etat_id = ee.id
WHERE c.date_cmd = CURRENT_DATE
ORDER BY c.date_creation DESC;
```

### Top 10 articles vendus (période)
```sql
SELECT a.nom, a.reference, cat.nom AS categorie, SUM(p.quantite) AS qte_vendue
FROM commande_panier p
JOIN article_article a ON p.article_id = a.id
JOIN article_categorie cat ON a.categorie_id = cat.id
JOIN commande_commande c ON p.commande_id = c.id
WHERE c.date_cmd >= '2025-01-01'
GROUP BY a.id, a.nom, a.reference, cat.nom
ORDER BY qte_vendue DESC
LIMIT 10;
```

### Commandes par région
```sql
SELECT r.nom_region, COUNT(*) AS nb_commandes, SUM(c.total_cmd) AS ca
FROM commande_commande c
JOIN parametre_ville v ON c.ville_id = v.id
JOIN parametre_region r ON v.region_id = r.id
WHERE c.date_cmd >= date_trunc('month', CURRENT_DATE)
GROUP BY r.nom_region
ORDER BY nb_commandes DESC;
```

### Performance opérateurs (confirmations du jour)
```sql
SELECT o.prenom || ' ' || o.nom AS operateur, COUNT(*) AS confirmations
FROM commande_etatcommande e
JOIN parametre_operateur o ON e.operateur_id = o.id
JOIN commande_enumetatcmd ee ON e.enum_etat_id = ee.id
WHERE ee.libelle = 'Confirmée' AND e.date_debut::date = CURRENT_DATE
GROUP BY o.id, o.prenom, o.nom
ORDER BY confirmations DESC;
```

### Stock critique (< 5 unités)
```sql
SELECT a.nom, a.reference, v.qte_disponible, c.nom AS couleur, pt.pointure
FROM article_variantearticle v
JOIN article_article a ON v.article_id = a.id
JOIN article_couleur c ON v.couleur_id = c.id
JOIN article_pointure pt ON v.pointure_id = pt.id
WHERE v.qte_disponible < 5 AND v.actif = true AND a.actif = true
ORDER BY v.qte_disponible ASC;
```

---

## Contacts / Ressources

- Documentation LangChain troubleshooting: https://js.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE/
- n8n Docs: https://docs.n8n.io/

---

Fichier généré par l'assistant : `docs/n8n_agent_full_state.md` — collez les blocs dans vos nœuds n8n et testez.
