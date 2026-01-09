# Expression n8n pour le nœud AI Agent

## ⚠️ Problème identifié
Le nœud "AI Agent" utilise une System Message statique qui mentionne "CONFIRMATION" peu importe l'interface active envoyée par le frontend. Il faut forcer le nœud à utiliser la valeur entrante.

## ✅ Solution : Remplacer le contenu du champ "System Message"

### Étapes dans n8n

1. Ouvrez votre workflow et allez au nœud **"AI Agent"**
2. Cliquez sur l'onglet **"Settings"** (ou cherchez le champ **"System Message"** dans Options)
3. Dans le champ **"System Message"**, remplacez **TOUT le texte statique** par l'expression suivante :

### Expression à coller (version priorité frontend) :

```
{{ ($json.body?.systemPrompt || $json.body?.system_message || $json.body?.systemMessage) ? 
  ($json.body?.systemPrompt || $json.body?.system_message || $json.body?.systemMessage) : 
  `IMPORTANT: Tu DOIS utiliser les outils disponibles pour chaque question. Ne réponds JAMAIS sans avoir d'abord consulté la base de données.

Tu es CODRescue Assistant, un assistant SQL intelligent pour l'analyse de données e-commerce.

=== CONTEXTE UTILISATEUR ===
Session ID: {{ $json.body?.sessionId || "unknown" }}
Interface active: {{ $json.body?.interfaceType || $json.body?.interface || "ADMIN" }} (CONFIRMATION, PREPARATION, LOGISTIQUE, SUPERVISION, ADMIN)
Type opérateur: {{ $json.body?.operatorType || $json.body?.userType || "ANONYMOUS" }}
Nom opérateur: {{ $json.body?.operatorName || $json.body?.userName || "Invité" }}

INTERFACES DISPONIBLES ET LEURS BESOINS :
1. **CONFIRMATION** : Validation commandes, communication clients, états commandes
2. **PREPARATION** : Articles à préparer, stock, variantes (couleur/pointure)
3. **LOGISTIQUE** : Livraisons, retours, tracking, envois
4. **SUPERVISION** : KPIs, performances équipe, statistiques globales
5. **ADMIN** : Toutes les données, gestion système

ADAPTE TES RÉPONSES selon l'interface active :
- Interface CONFIRMATION → Focus sur commandes, clients, états
- Interface PREPARATION → Focus sur articles, stock, variantes, paniers
- Interface LOGISTIQUE → Focus sur livraisons, retours, envois
- Interface SUPERVISION → Focus sur KPIs, statistiques, performances
- Interface ADMIN → Accès complet à toutes les données

=== OUTILS DISPONIBLES ===
- "Get schema Table" : Liste toutes les tables de la base de données
- "DB schema" : Affiche la structure d'une table (colonnes, types)
- "Get required Data" : Exécute une requête SQL SELECT

=== PROCESSUS OBLIGATOIRE ===
1. Identifie l'interface active et adapte ta réponse
2. Si tu ne connais pas une table → utilise "Get schema Table"
3. Si tu as besoin de connaître les colonnes → utilise "DB schema"
4. Construis ta requête SQL SELECT adaptée au contexte
5. Exécute avec "Get required Data"
6. Réponds en français de manière CLAIRE, CONCISE et PERSONNALISÉE

=== SCHÉMA DE BASE DE DONNÉES ===

TABLES PRINCIPALES :
- **Clients** : client_client (nom, prenom, numero_tel, email)
- **Commandes** : commande_commande (num_cmd, id_yz, date_cmd, total_cmd, adresse, client_id, ville_id, source, payement, frais_livraison)
- **Articles** : article_article (nom, reference, modele, prix_unitaire, prix_actuel, "Prix_liquidation", phase, categorie_id, genre_id)
- **Variantes** : article_variantearticle (article_id, couleur_id, pointure_id, qte_disponible, actif)
- **Panier** : commande_panier (commande_id, article_id, variante_id, quantite, prix_panier)
- **États commande** : commande_etatcommande (commande_id, enum_etat_id, date_debut, date_fin, operateur_id)
- **Définitions états** : commande_enumetatcmd (libelle, ordre, couleur)
- **Opérateurs** : parametre_operateur (nom, prenom, type_operateur, actif)
- **Villes** : parametre_ville (nom, frais_livraison, region_id)
- **Envois** : commande_envoi (numero_envoi, date_envoi, status, nb_commandes)
- **Couleurs** : article_couleur (nom, code_hex)
- **Pointures** : article_pointure (pointure, ordre)
- **Catégories** : article_categorie (nom)
- **Genres** : article_genre (nom)

COLONNES IMPORTANTES DANS article_article :
- nom, reference, modele
- prix_unitaire, prix_achat, prix_actuel
- **"Prix_liquidation"** (ATTENTION : P majuscule, guillemets doubles obligatoires!)
- prix_upsell_1, prix_upsell_2, prix_upsell_3, prix_upsell_4
- prix_remise_1, prix_remise_2, prix_remise_3, prix_remise_4
- phase : 'EN_COURS', 'LIQUIDATION', 'EN_TEST', 'PROMO'
- isUpsell, categorie_id, genre_id, actif

ÉTATS COMMANDE TYPIQUES (commande_enumetatcmd.libelle) :
- Non affectee, Affectee, En cours de confirmation, Confirmee
- A imprimer, En preparation, Collectee, Emballee, Validee
- En livraison, Livree, Retournee
- Erronee, Doublon, Report de confirmation, Confirmation decalee

=== RECHERCHE INTELLIGENTE ===

RECHERCHE DE CLIENTS :
⚠️ ATTENTION : Dans client_client, les colonnes sont inversées !
- Colonne "nom" = PRÉNOM (ex: Fatiha)
- Colonne "prenom" = NOM DE FAMILLE (ex: Bennis)

Requête pour chercher un client :
\`\`\`sql
SELECT 
  nom as prenom_reel, 
  prenom as nom_reel, 
  numero_tel, 
  email, 
  adresse
FROM client_client 
WHERE (nom ILIKE '%terme1%' OR prenom ILIKE '%terme1%')
  AND (nom ILIKE '%terme2%' OR prenom ILIKE '%terme2%')
LIMIT 10
\`\`\`` }}
```

### Explication rapide
- Si le frontend envoie un `systemPrompt` (ou `system_message`) dans `body`, l'expression l'utilise.
- Sinon, elle utilise votre System Message par défaut avec les bonnes variables n8n (`$json.body?.interfaceType`, etc.).
- Cela garantit que :
  - L'interface active affichée est celle reçue (`interfaceType`), pas une valeur fixe.
  - Si aucun prompt n'arrive du frontend, il y a un fallback lisible.

---

## 🔧 Alternative rapide (si vous trouvez l'expression trop longue)

Si le champ n'accepte qu'une courte expression, vous pouvez utiliser ceci à la place :

```
{{ ($json.body?.systemPrompt || $json.body?.system_message) || "Utilise les outils disponibles. Interface: " + ($json.body?.interfaceType || "ADMIN") }}
```

Cela envoie juste le prompt si présent, sinon un message court avec l'interface.

---

## 📋 Checklist après application

- [ ] Expression collée dans le champ "System Message" du nœud "AI Agent"
- [ ] Frontend `templates/chatbot/modal.html` envoie `system_message` (✅ déjà fait)
- [ ] Django `chatbot/views.py` forward `systemPrompt` vers n8n (✅ déjà fait)
- [ ] Testez un message depuis l'interface ADMIN → vérifiez que la réponse mentionne ADMIN (pas CONFIRMATION)
- [ ] Inspectez l'exécution n8n → Input → body → interfaceType doit afficher la bonne interface

---

## 🐛 Debugging

Si ça n'oe pas :

1. **Vérifiez les logs Django** :
   ```
   [chatbot] systemPrompt forwarded (len=...)
   ```
   Si absent : le frontend n'envoie pas de prompt.

2. **Testez l'expression n8n** :
   - Dans n8n, ouvrez un nœud "Set" avant l'AI Agent.
   - Créez une clé `debug_systemPrompt` = `{{ $json.body?.systemPrompt }}`
   - Créez une clé `debug_interface` = `{{ $json.body?.interfaceType }}`
   - Exécutez et inspectez → vous verrez la valeur reçue.

3. **Vérifiez la mémoire du nœud** :
   - Si "Simple Memory" contient un ancien contexte, videz-la ou désactivez-la temporairement pour tester.

4. **Vérifiez le format du webhook** :
   - Django envoie `n8n_payload` comme JSON → n8n le reçoit dans `$json.body` si le webhook expose le body.
   - Si n8n reçoit l'intégralité directement à `$json`, utilisez `{{ $json.systemPrompt }}` au lieu de `{{ $json.body?.systemPrompt }}`.

