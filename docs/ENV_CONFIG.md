# Configuration pour le chatbot RAG avec N8N

## Variables d'environnement nécessaires

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```bash
# ===== OpenAI API =====
# Clé API OpenAI pour générer les embeddings et les réponses LLM
# Obtenez votre clé sur: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key-here

# ===== N8N Configuration =====
# URL de base de votre éditeur N8N (ngrok ou local)
EDITOR_BASE_URL=https://your-ngrok-url.ngrok-free.app

# URL du webhook N8N pour le chatbot
N8N_CHATBOT_WEBHOOK=https://your-ngrok-url.ngrok-free.app/webhook/chatbot

# ===== Embedding Configuration =====
# Modèle d'embedding à utiliser
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# ===== LLM Configuration =====
# Modèle LLM à utiliser pour les réponses
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500

# ===== RAG Configuration =====
# Nombre de documents à récupérer pour le contexte
RAG_TOP_K=5
# Seuil de similarité minimum (0-1)
RAG_SIMILARITY_THRESHOLD=0.5
```

## Comment obtenir votre clé OpenAI

1. Allez sur https://platform.openai.com/api-keys
2. Connectez-vous ou créez un compte
3. Cliquez sur "Create new secret key"
4. Copiez la clé et ajoutez-la dans votre fichier `.env`

## Coût estimé

- **text-embedding-3-small** : ~0.02$ pour 1000 documents
- **gpt-4o-mini** : ~0.15$ pour 1000 requêtes
- **Total pour 1000 articles + 1000 requêtes** : ~0.17$
