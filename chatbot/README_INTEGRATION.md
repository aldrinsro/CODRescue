# 🔗 Intégration du Chatbot Multi-Interface

Ce guide explique comment le chatbot s'adapte automatiquement à chaque interface utilisateur (Confirmation, Préparation, Logistique, Supervision, Administration).

## 📋 Vue d'ensemble

Le système détecte automatiquement :
- ✅ **L'interface active** (CONFIRMATION, PREPARATION, LOGISTIQUE, SUPERVISION, ADMIN)
- ✅ **Le type d'opérateur** (depuis le modèle `Operateur`)
- ✅ **Le nom de l'opérateur** (prénom + nom)
- ✅ **L'ID de l'opérateur** et **l'ID utilisateur**

Ces informations sont automatiquement injectées dans **tous les templates** et envoyées au **workflow n8n**.

---

## 🏗️ Architecture

### 1. **Context Processor** (`chatbot/context_processors.py`)

Injecte automatiquement les variables suivantes dans **tous les templates** :

```python
{
    'chatbot_interface': 'CONFIRMATION',      # Interface active
    'chatbot_user_type': 'CONFIRMATION',      # Type opérateur
    'chatbot_user_name': 'Mohammed Bennis',   # Nom complet
    'chatbot_user_id': 42,                    # ID utilisateur Django
    'chatbot_operator_id': 15,                # ID opérateur
}
```

**Détection automatique de l'interface depuis l'URL :**
- `/operateur-confirme/` → `CONFIRMATION`
- `/operateur-preparation/` → `PREPARATION`
- `/operateur-logistique/` → `LOGISTIQUE`
- `/Superpreparation/` → `SUPERVISION`
- `/parametre/` ou `/admin/` → `ADMIN`

### 2. **Vue API** (`chatbot/views.py`)

La fonction `chatbot_api()` enrichit automatiquement le payload envoyé à n8n :

```python
n8n_payload = {
    "chatInput": "Question de l'utilisateur",
    "sessionId": "django-abc123...",
    # Nouvelles clés pour le prompt système amélioré
    "interfaceType": "CONFIRMATION",
    "operatorType": "CONFIRMATION",
    "operatorName": "Mohammed Bennis",
    "operatorId": 15,
    # Anciennes clés maintenues pour compatibilité
    "interface": "CONFIRMATION",
    "userType": "CONFIRMATION",
    "userName": "Mohammed Bennis",
    "userId": 42,
}
```

### 3. **Template Modal** (`templates/chatbot/modal.html`)

Le modal affiche automatiquement :
- 🎨 **Couleur adaptée** à l'interface
- 📛 **Badge** avec le nom de l'interface
- 🔤 **Icône** spécifique

**Exemple visuel :**
```
┌─────────────────────────────────────┐
│ 📦 Assistant IA    [Préparation]    │  ← Orange (#FF9800)
├─────────────────────────────────────┤
│ Messages du chat...                 │
└─────────────────────────────────────┘
```

---

## 🎨 Personnalisation par Interface

### Couleurs

| Interface      | Couleur   | Code      |
|----------------|-----------|-----------|
| CONFIRMATION   | Vert      | `#4CAF50` |
| PREPARATION    | Orange    | `#FF9800` |
| LOGISTIQUE     | Bleu      | `#2196F3` |
| SUPERVISION    | Violet    | `#9C27B0` |
| ADMIN          | Gris-bleu | `#607D8B` |

### Icônes

| Interface      | Icône |
|----------------|-------|
| CONFIRMATION   | ✓     |
| PREPARATION    | 📦    |
| LOGISTIQUE     | 🚚    |
| SUPERVISION    | 📊    |
| ADMIN          | ⚙️    |

---

## 📝 Utilisation dans n8n

### Configuration du Prompt Système

Dans le nœud **AI Agent** de n8n, utilisez ces variables :

```
Session ID: {{ $json.sessionId }}
Interface active: {{ $json.interfaceType }}
Type opérateur: {{ $json.operatorType }}
Nom opérateur: {{ $json.operatorName }}
```

### Exemple de Prompt Conditionnel

```
Tu es CODRescue Assistant.

Interface active: {{ $json.interfaceType }}
Opérateur: {{ $json.operatorName }} ({{ $json.operatorType }})

{{#if (eq $json.interfaceType "PREPARATION")}}
Focus sur : articles, stock, variantes, préparation de commandes
{{/if}}

{{#if (eq $json.interfaceType "CONFIRMATION")}}
Focus sur : validation commandes, états, communication clients
{{/if}}

{{#if (eq $json.interfaceType "LOGISTIQUE")}}
Focus sur : livraisons, retours, envois, tracking
{{/if}}
```

---

## 🔧 Template Tags Disponibles

Utilisez les filtres personnalisés dans vos templates :

```django
{% load chatbot_extras %}

{# Afficher le libellé #}
{{ chatbot_interface|interface_label }}
{# → "Préparation" #}

{# Afficher l'icône #}
{{ chatbot_interface|interface_icon }}
{# → "📦" #}

{# Afficher la couleur #}
{{ chatbot_interface|interface_color }}
{# → "#FF9800" #}
```

---

## 📦 Intégration dans un Template

### Méthode 1 : Inclusion du Modal

```django
{# Dans votre template de base (base.html) #}
{% include 'chatbot/modal.html' %}
```

Le modal détectera **automatiquement** l'interface active.

### Méthode 2 : Data Attributes Personnalisés

Si vous voulez passer des données custom :

```django
<body data-interface="{{ chatbot_interface }}"
      data-user-type="{{ chatbot_user_type }}"
      data-user-name="{{ chatbot_user_name }}"
      data-user-id="{{ chatbot_user_id }}"
      data-operator-id="{{ chatbot_operator_id }}">

    {# Votre contenu #}

    {% include 'chatbot/modal.html' %}
</body>
```

---

## 🧪 Test de l'Intégration

### 1. Vérifier le Context Processor

```bash
python manage.py shell
```

```python
from django.test import RequestFactory
from chatbot.context_processors import chatbot_context

factory = RequestFactory()
request = factory.get('/operateur-preparation/')
context = chatbot_context(request)
print(context)
# {'chatbot_interface': 'PREPARATION', ...}
```

### 2. Tester l'API Chatbot

```bash
curl -X POST http://localhost:8000/chatbot/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "Combien de commandes aujourd'\''hui ?"}'
```

### 3. Vérifier les Logs

Dans la console Django, vous devriez voir :

```
[chatbot] Appel n8n URL: https://...
[chatbot] Payload envoyé à n8n: {
  "chatInput": "...",
  "interfaceType": "PREPARATION",
  "operatorType": "PREPARATION",
  "operatorName": "Mohammed Bennis",
  ...
}
```

### 4. Test Frontend

Ouvrez la console du navigateur (F12) et regardez les logs :

```javascript
📋 Contexte utilisateur détecté: {
  interface: "PREPARATION",
  userType: "PREPARATION",
  userName: "Mohammed Bennis",
  userId: "42",
  operatorId: "15"
}
```

---

## 🐛 Dépannage

### Problème : L'interface n'est pas détectée correctement

**Solution** : Vérifiez que votre URL contient bien le bon préfixe :
- ✅ `/operateur-preparation/dashboard/` → PREPARATION
- ❌ `/custom-route/` → ADMIN (par défaut)

### Problème : Les data-attributes sont vides

**Vérification** :
1. Le context processor est-il bien ajouté dans `settings.py` ?
```python
'context_processors': [
    ...
    'chatbot.context_processors.chatbot_context',
],
```

2. L'utilisateur est-il authentifié ?
```python
if request.user.is_authenticated:
    # Les données utilisateur sont disponibles
```

### Problème : Template tags non reconnus

**Solution** : Vérifiez que le dossier `chatbot/templatetags/` existe et contient :
- `__init__.py`
- `chatbot_extras.py`

Puis rechargez le serveur :
```bash
python manage.py runserver
```

---

## 📚 Fichiers Créés/Modifiés

| Fichier | Description |
|---------|-------------|
| `chatbot/views.py` | Enrichissement du contexte utilisateur |
| `chatbot/context_processors.py` | Injection automatique dans les templates |
| `chatbot/templatetags/chatbot_extras.py` | Filtres personnalisés |
| `templates/chatbot/modal.html` | Modal adaptatif |
| `config/settings.py` | Enregistrement du context processor |

---

## ✅ Checklist de Validation

- [ ] Context processor ajouté dans `settings.py`
- [ ] Template tags créés dans `chatbot/templatetags/`
- [ ] Modal chatbot inclus dans les templates de base
- [ ] Workflow n8n mis à jour avec le nouveau prompt système
- [ ] Test de détection d'interface dans chaque URL
- [ ] Vérification des logs console (frontend + backend)
- [ ] Test de conversation dans chaque interface

---

## 🎯 Prochaines Étapes

1. **Tester dans toutes les interfaces** :
   - Confirmation (`/operateur-confirme/`)
   - Préparation (`/operateur-preparation/`)
   - Logistique (`/operateur-logistique/`)
   - Supervision (`/Superpreparation/`)
   - Administration (`/parametre/`)

2. **Mettre à jour le prompt système n8n** avec le nouveau format (voir `chatbot/README_CHATBOT.md`)

3. **Personnaliser les réponses** selon l'interface dans n8n

---

## 📞 Support

Pour toute question :
- **Email Backend** : codsuitebackend@gmail.com
- **Email Frontend** : codsuitefrontend@gmail.com
- **Documentation complète** : `chatbot/README_CHATBOT.md`
