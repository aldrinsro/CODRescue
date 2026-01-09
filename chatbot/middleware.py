from django.utils.deprecation import MiddlewareMixin
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

from .n8n_client import trigger_chatbot_webhook


class N8nChatbotMiddleware(MiddlewareMixin):
    """Middleware minimal qui intercepte les réponses à l'endpoint /chatbot/api/chatbot/

    - Si la réponse est JSON et contient une clé 'answer', envoie un event à n8n.
    - Silencieux en cas d'erreur (ne bloque pas la réponse au client).
    """

    def process_response(self, request, response):
        try:
            path = request.path or ''
            if path.startswith('/chatbot/api/chatbot'):
                # tenter parser le JSON de la réponse
                content_type = response.get('Content-Type', '')
                if 'application/json' in content_type:
                    try:
                        data = json.loads(response.content.decode('utf-8'))
                    except Exception:
                        data = None
                    if data and 'answer' in data:
                        event = {
                            'question': request.POST.get('question') or (request.body and json.loads(request.body.decode('utf-8')).get('question') if request.body else None),
                            'user': str(getattr(request, 'user', 'anonymous')),
                            'interface': (json.loads(request.body.decode('utf-8')).get('interface') if request.body else None),
                            'answer': data.get('answer'),
                            'error': bool(data.get('error', False))
                        }
                        # fire-and-forget
                        try:
                            trigger_chatbot_webhook(event)
                        except Exception as e:
                            logger.exception('n8n webhook trigger failed in middleware: %s', e)
        except Exception:
            # ne jamais interrompre la réponse
            logger.exception('Unexpected error in N8nChatbotMiddleware')
        return response


class N8nChatbotOptimizedMiddleware(MiddlewareMixin):
    """Middleware optimisé pour envoyer les événements chatbot à n8n.

    - Evite les envois répétés pour la même question via cache (QUERY_CACHE_DURATION).
    - Envoie le webhook en tâche de fond (thread) pour ne pas bloquer la requête.
    - Enregistre des métriques basiques via le logger si activé.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        try:
            from django.core.cache import caches
            self.cache = caches['default']
        except Exception:
            self.cache = None

        self.config = getattr(settings, 'CHATBOT_CONFIG', {}) or {}

    def _background_trigger(self, event):
        try:
            trigger_chatbot_webhook(event)
        except Exception as e:
            logger.exception('N8nChatbotOptimizedMiddleware background send failed: %s', e)

    def process_response(self, request, response):
        try:
            path = request.path or ''
            if not path.startswith('/chatbot/api/chatbot'):
                return response

            content_type = response.get('Content-Type', '')
            if 'application/json' not in content_type:
                return response

            try:
                payload = json.loads(response.content.decode('utf-8'))
            except Exception:
                payload = None

            # Only send if an answer is present
            if not payload or 'answer' not in payload:
                return response

            # Extract question from request body or POST
            question = None
            try:
                if request.body:
                    body_json = json.loads(request.body.decode('utf-8'))
                    question = body_json.get('question')
                    interface = body_json.get('interface')
                else:
                    question = request.POST.get('question')
                    interface = request.POST.get('interface')
            except Exception:
                question = request.POST.get('question') or None
                interface = request.POST.get('interface') or None

            # Build event
            event = {
                'question': question,
                'user': str(getattr(request, 'user', 'anonymous')),
                'interface': interface,
                'answer': payload.get('answer'),
                'error': bool(payload.get('error', False))
            }

            # Caching to avoid duplicate sends
            cache_duration = int(self.config.get('QUERY_CACHE_DURATION', 0) or 0)
            cache_key = None
            if question and self.cache and cache_duration > 0:
                try:
                    import hashlib
                    h = hashlib.sha256()
                    h.update(question.encode('utf-8'))
                    cache_key = f'chatbot:event:{h.hexdigest()}'
                    if self.cache.get(cache_key):
                        logger.debug('Skipping duplicate chatbot event (cached): %s', question)
                        return response
                    # set a flag to prevent duplicates
                    try:
                        self.cache.set(cache_key, True, timeout=cache_duration)
                    except Exception:
                        # cache set may fail; ignore
                        pass
                except Exception:
                    cache_key = None

            # Send in background thread so we don't block response
            try:
                import threading
                t = threading.Thread(target=self._background_trigger, args=(event,), daemon=True)
                t.start()
                if self.config.get('ENABLE_PERFORMANCE_MONITORING'):
                    logger.info('Chatbot event queued to n8n (async) for user=%s', event.get('user'))
            except Exception as e:
                logger.exception('Failed to queue chatbot event thread: %s', e)

        except Exception:
            logger.exception('Unexpected error in N8nChatbotOptimizedMiddleware')

        return response
