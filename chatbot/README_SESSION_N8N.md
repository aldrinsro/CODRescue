# 🔐 Configuration du Session ID dans n8n pour la Mémoire Conversationnelle

Ce guide explique comment utiliser le `sessionId` dans n8n pour maintenir le contexte des conversations entre plusieurs messages.

---

## 🎯 Qu'est-ce que le Session ID ?

Le **sessionId** est un identifiant unique généré par Django pour chaque utilisateur. Il permet à n8n de :
- ✅ **Mémoriser** les conversations précédentes
- ✅ **Maintenir le contexte** entre plusieurs messages
- ✅ **Personnaliser** les réponses selon l'historique
- ✅ **Distinguer** les conversations de différents utilisateurs

### Format du Session ID envoyé

```json
{
  "sessionId": "django-abc123def456...",
  "chatInput": "Question de l'utilisateur",
  "interfaceType": "PREPARATION",
  "operatorName": "Mohammed Bennis",
  ...
}
```

Le format est : `django-{session_key}` où `session_key` est généré par Django.

---

## 📊 Configuration dans n8n

### Étape 1 : Activer la Mémoire dans l'AI Agent

Dans votre workflow n8n, configurez le nœud **AI Agent** :

1. **Ouvrir le nœud AI Agent**
2. **Aller dans l'onglet "Options"**
3. **Trouver la section "Memory"**
4. **Cliquer sur "Add Option" → "Memory"**

### Étape 2 : Configurer Window Buffer Memory

**Option 1 : Configuration Simple (Recommandée)**

```
Memory Type: Window Buffer Memory
Session Key: {{ $json.sessionId }}
Context Window Size: 10
```

⚠️ **IMPORTANT** : Utilisez `{{ $json.sessionId }}` et **PAS** `{{ $json.body.sessionId }}` car Django envoie le sessionId directement dans le corps JSON.

**Explication** :
- `Session Key` : Utilise le sessionId envoyé depuis Django
- `Context Window Size` : Nombre de messages à mémoriser (10 = 5 échanges)

**Option 2 : Configuration Avancée**

Si vous utilisez un nœud intermédiaire pour traiter les données :

```javascript
// Dans un nœud "Code" avant l'AI Agent
return {
  json: {
    chatInput: $input.item.json.chatInput,
    sessionId: $input.item.json.sessionId || 'anonymous',
    // ... autres champs
  }
};
```

Puis dans l'AI Agent :
```
Session Key: {{ $json.sessionId }}
```

---

## 🔧 Configuration Complète du Workflow n8n

### Architecture Recommandée

```
┌─────────────┐
│  Webhook    │
│  (Trigger)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Extract Session │ (optionnel)
│  & Context      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   AI Agent      │
│  + Memory       │ ← Utilise sessionId ici
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Response      │
└─────────────────┘
```

### Configuration du Nœud "Extract Session" (Optionnel)

Ce nœud peut enrichir ou valider le sessionId :

```javascript
// Extraire et valider le sessionId
const sessionId = $input.item.json.sessionId || $input.item.json.body?.sessionId;
const interfaceType = $input.item.json.interfaceType || 'ADMIN';
const operatorName = $input.item.json.operatorName || 'Invité';

// Créer un sessionId enrichi si nécessaire
const enrichedSessionId = `${sessionId}-${interfaceType}`;

return {
  json: {
    sessionId: sessionId,
    enrichedSessionId: enrichedSessionId,
    chatInput: $input.item.json.chatInput,
    interfaceType: interfaceType,
    operatorType: $input.item.json.operatorType,
    operatorName: operatorName,
  }
};
```

Ensuite dans l'AI Agent :
```
Session Key: {{ $json.sessionId }}
```

---

## 📋 Configuration Détaillée de l'AI Agent

### Paramètres de Base

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Prompt (User Message)** | `{{ $json.chatInput }}` | Message de l'utilisateur |
| **System Message** | Voir prompt système complet ci-dessous | Instructions pour l'IA |

### Options de Mémoire

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Memory** | Window Buffer Memory | Type de mémoire |
| **Session Key** | `{{ $json.sessionId }}` | Identifiant unique de session |
| **Context Window Size** | `10` | Nombre de messages à mémoriser |

### Configuration du Prompt Système

Utilisez le prompt système amélioré que je vous ai fourni :

```
IMPORTANT: Tu DOIS utiliser les outils disponibles pour chaque question...

=== CONTEXTE UTILISATEUR ===
Session ID: {{ $json.sessionId }}
Interface active: {{ $json.interfaceType }}
Type opérateur: {{ $json.operatorType }}
Nom opérateur: {{ $json.operatorName }}

[... reste du prompt]
```

---

## 🧪 Test de la Mémoire Conversationnelle

### Test 1 : Vérifier que le sessionId est reçu

Dans n8n, ajoutez un nœud "Set" après le Webhook pour vérifier :

```javascript
// Afficher le sessionId reçu
return {
  json: {
    receivedSessionId: $input.item.json.sessionId,
    chatInput: $input.item.json.chatInput,
    timestamp: new Date().toISOString()
  }
};
```

### Test 2 : Conversation avec Contexte

**Message 1** :
```
"Quel est le stock de l'article YZ3000 ?"
```

**Réponse attendue** :
```
L'article YZ3000 a 45 paires en stock.
```

**Message 2** (dans la même session) :
```
"Et combien de variantes ?"
```

**Réponse attendue** :
```
L'article YZ3000 a 3 variantes disponibles :
- Rouge (38) : 12 paires
- Noir (39) : 18 paires
- Beige (37) : 15 paires
```

✅ Si l'IA se souvient de "YZ3000" sans que vous le répétiez, la mémoire fonctionne !

### Test 3 : Nouvelle Session

Ouvrez un nouvel onglet (nouveau sessionId) et posez :
```
"Et combien de variantes ?"
```

**Réponse attendue** :
```
De quel article parlez-vous ? Veuillez préciser la référence.
```

✅ Si l'IA ne se souvient pas, c'est normal : nouvelle session = nouveau contexte.

---

## 🔍 Debug du Session ID

### Vérifier le sessionId côté Django

Ajoutez dans `chatbot/views.py` :

```python
print(f"[chatbot] Session ID: {request.session.session_key}")
print(f"[chatbot] Payload: {n8n_payload}")
```

### Vérifier le sessionId côté n8n

Dans un nœud "Code" après le Webhook :

```javascript
console.log('Session ID reçu:', $input.item.json.sessionId);
console.log('Tous les champs:', $input.item.json);

return {
  json: $input.item.json
};
```

### Logs à surveiller

**Django (console serveur)** :
```
[chatbot] Session ID: abc123def456...
[chatbot] Payload envoyé à n8n: {
  "sessionId": "django-abc123def456...",
  ...
}
```

**n8n (exécution du workflow)** :
```
Session ID reçu: django-abc123def456...
```

---

## ⚙️ Configuration Avancée

### Mémoire Partagée entre Interfaces

Si vous voulez que l'utilisateur ait une mémoire **unique** à travers toutes les interfaces :

```javascript
// Dans un nœud "Code" avant l'AI Agent
const baseSessionId = $input.item.json.sessionId.replace('django-', '');
return {
  json: {
    sessionId: baseSessionId, // Session unique pour toutes les interfaces
    ...
  }
};
```

### Mémoire Séparée par Interface

Si vous voulez une mémoire **différente** pour chaque interface :

```javascript
// Dans un nœud "Code" avant l'AI Agent
const sessionId = $input.item.json.sessionId;
const interfaceType = $input.item.json.interfaceType;
const enrichedSessionId = `${sessionId}-${interfaceType}`;

return {
  json: {
    sessionId: enrichedSessionId, // Session différente par interface
    ...
  }
};
```

---

## 📊 Exemple de Configuration Complète

### Configuration JSON du Nœud AI Agent

```json
{
  "name": "AI Agent Chatbot",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "promptType": "define",
    "text": "={{ $json.chatInput }}",
    "systemMessage": "IMPORTANT: Tu DOIS utiliser les outils...",
    "options": {
      "memory": {
        "memoryType": "windowBufferMemory",
        "sessionKey": "={{ $json.sessionId }}",
        "contextWindowLength": 10
      }
    }
  },
  "typeVersion": 1.6
}
```

---

## 🐛 Dépannage

### Problème : L'IA ne se souvient pas des messages précédents

**Solutions** :

1. **Vérifier que le sessionId est bien passé** :
   ```javascript
   console.log('Session ID:', $json.sessionId);
   ```

2. **Vérifier la configuration Memory** :
   - Memory Type : `Window Buffer Memory`
   - Session Key : `{{ $json.sessionId }}`
   - Context Window Size : `10` (ou plus)

3. **Vérifier que le même sessionId est utilisé** :
   - Dans Django : `request.session.session_key`
   - Dans n8n : `$json.sessionId`

### Problème : sessionId est null ou undefined

**Solutions** :

1. **Vérifier que Django génère bien une session** :
   ```python
   if not request.session.session_key:
       request.session.create()
   ```

2. **Modifier chatbot/views.py** :
   ```python
   # Forcer la création de session si nécessaire
   if not request.session.session_key:
       request.session.create()

   n8n_payload = {
       "sessionId": f"django-{request.session.session_key or 'anonymous'}",
       ...
   }
   ```

### Problème : Mémoire partagée entre utilisateurs différents

**Cause** : Tous les utilisateurs ont le même sessionId.

**Solution** : Vérifier que chaque utilisateur a bien sa propre session Django.

---

## ✅ Checklist de Validation

- [ ] sessionId est envoyé depuis Django dans le payload
- [ ] sessionId est reçu dans n8n (vérifier dans les logs)
- [ ] Memory est configurée dans le nœud AI Agent
- [ ] Session Key utilise `{{ $json.sessionId }}`
- [ ] Context Window Size est défini (10 minimum)
- [ ] Test de conversation multi-tours effectué
- [ ] Nouvelle session ne conserve pas l'ancien contexte

---

## 📚 Ressources

- [Documentation n8n AI Agent](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/)
- [Window Buffer Memory](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorybufferwindow/)
- [Django Sessions](https://docs.djangoproject.com/en/5.1/topics/http/sessions/)

---

## 🎯 Résumé

1. ✅ Django envoie automatiquement `sessionId` dans le payload
2. ✅ n8n utilise ce `sessionId` pour la mémoire conversationnelle
3. ✅ Chaque utilisateur a sa propre mémoire isolée
4. ✅ La mémoire garde les 10 derniers messages (configurable)
5. ✅ Le contexte est maintenu entre les messages successifs

**Configuration minimale dans n8n** :
- Memory Type : `Window Buffer Memory`
- Session Key : `{{ $json.sessionId }}`
- Context Window Size : `10`

C'est tout ! 🎉
