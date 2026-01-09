# chatbot/n8n_client.py
# Petit client pour déclencher un webhook n8n depuis le backend Django
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

N8N_BASE = getattr(settings, 'N8N_WEBHOOK_BASE', 'http://localhost:5678')
CHATBOT_WEBHOOK = getattr(settings, 'N8N_CHATBOT_WEBHOOK', 'chatbot')
BASIC_USER = getattr(settings, 'N8N_BASIC_AUTH_USER', '')
BASIC_PASS = getattr(settings, 'N8N_BASIC_AUTH_PASSWORD', '')
TIMEOUT = 8


def trigger_chatbot_webhook(payload: dict) -> bool:
    """Envoie un événement au webhook n8n configuré pour le chatbot.

    Le workflow n8n peut être configuré pour écouter le chemin `/webhook/{CHATBOT_WEBHOOK}`.
    """
    # Normalize CHATBOT_WEBHOOK to accept several formats:
    # - raw id: "7bbe2d..."
    # - "webhook/<id>" or "/webhook/<id>"
    # - full URL: "https://.../webhook/<id>"
    if isinstance(CHATBOT_WEBHOOK, str) and CHATBOT_WEBHOOK.startswith(('http://', 'https://')):
        url = CHATBOT_WEBHOOK
    else:
        webhook_path = str(CHATBOT_WEBHOOK).lstrip('/')
        # if the configured value contains the 'webhook/' prefix, remove it
        if webhook_path.startswith('webhook/'):
            webhook_path = webhook_path.split('/', 1)[1]
        url = f"{N8N_BASE.rstrip('/')}/webhook/{webhook_path}"
    headers = {'Content-Type': 'application/json'}
    auth = None
    if BASIC_USER and BASIC_PASS:
        auth = (BASIC_USER, BASIC_PASS)
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT, auth=auth)
        r.raise_for_status()
        logger.debug('Trigger n8n webhook %s successful, status=%s', url, r.status_code)
        return True
    except Exception as e:
        logger.exception('Failed to trigger n8n webhook %s: %s', url, e)
        return False
