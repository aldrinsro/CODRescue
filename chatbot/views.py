# Code réindenté proprement
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .services import ChatbotDataService

GREETING_KEYWORDS = {"salut", "bonjour", "hello", "bonsoir", "hi"}


def _build_interface_hint(user_type: str | None) -> str:
    mapping = {
        'ADMIN': "En tant qu'utilisateur de l'interface Administration, je peux vous offrir une vision globale et proactive sur les commandes, les KPI, les régions et les opérateurs.",
        'CONFIRMATION': "En interface Confirmation, je peux vous aider sur tout ce qui concerne les validations et les paiements.",
        'LOGISTIQUE': "En interface Logistique, je vous accompagne sur les livraisons, les envois, les retours et le SAV.",
        'PREPARATION': "En interface Préparation, je mets l'accent sur les commandes à préparer, les articles et les stocks.",
        'SUPERVISEUR_PREPARATION': "En interface Supervision Préparation, je garde un œil global sur les équipes de préparation, leurs performances et les urgences à traiter.",
    }
    return mapping.get(user_type or '', "Adaptons-nous au contexte de votre interface pour avancer efficacement.")


def _build_greeting_response(user_name: str | None, user_type: str | None) -> str:
    name_part = f" {user_name}" if user_name else ""
    lines = [
        f"Bonjour{name_part} ! Je suis IA YZRescue, votre assistant virtuel, prêt à vous aider dans votre système de gestion de commandes.",
        _build_interface_hint(user_type),
        "Comment puis-je vous assister aujourd'hui ?",
    ]
    return "\n\n".join(lines)


data_service = ChatbotDataService()


def _post_to_n8n_with_retries(n8n_url: str, n8n_payload: dict, retries: int = 2, timeout: int = 30):
    """Post to n8n with simple retries for transient errors (5xx) and network issues.

    Returns a requests.Response or raises the last exception encountered.
    """
    import time
    last_exc = None

    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                n8n_url,
                json=n8n_payload,
                timeout=timeout,
                headers={"ngrok-skip-browser-warning": "true"}
            )

            if 500 <= resp.status_code < 600:
                last_exc = requests.exceptions.HTTPError(response=resp)
                if attempt < retries:
                    sleep_time = 1 * (2 ** attempt)
                    print(f"[chatbot] tentative {attempt+1} échouée (status {resp.status_code}), retry dans {sleep_time}s")
                    time.sleep(sleep_time)
                    continue
                resp.raise_for_status()

            return resp

        except requests.exceptions.RequestException as ex:
            last_exc = ex
            if attempt < retries:
                sleep_time = 1 * (2 ** attempt)
                print(f"[chatbot] erreur réseau tentative {attempt+1}: {ex}. Retry dans {sleep_time}s")
                time.sleep(sleep_time)
                continue
            raise


def _get_interface_from_path(request):
    """Détecte l'interface active à partir du chemin de la requête."""
    referer = request.META.get('HTTP_REFERER', '')
    path = request.path_info

    if 'operateur-confirme' in referer or 'operateur-confirme' in path:
        return 'CONFIRMATION'
    elif 'operateur-preparation' in referer or 'operateur-preparation' in path:
        return 'PREPARATION'
    elif 'operateur-logistique' in referer or 'operateur-logistique' in path:
        return 'LOGISTIQUE'
    elif 'Superpreparation' in referer or 'Superpreparation' in path:
        return 'SUPERVISION'
    elif 'parametre' in referer or 'admin' in referer:
        return 'ADMIN'

    return 'ADMIN'


def _get_user_context(request):
    """Extrait le contexte utilisateur complet pour le chatbot."""
    context = {
        'interface': _get_interface_from_path(request),
        'userType': 'ANONYMOUS',
        'userName': 'Invité',
        'userId': None,
        'operatorId': None,
    }

    if request.user.is_authenticated:
        context['userId'] = request.user.id
        context['userName'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username

        try:
            from parametre.models import Operateur
            operateur = Operateur.objects.filter(user=request.user, actif=True).first()
            if operateur:
                context['operatorId'] = operateur.id
                context['userType'] = operateur.type_operateur
                context['userName'] = f"{operateur.prenom} {operateur.nom}".strip()

        except Exception as e:
            print(f"[chatbot] Erreur lors de la récupération de l'opérateur: {e}")
            if request.user.is_superuser:
                context['userType'] = 'ADMIN'

    return context


@csrf_exempt
def chatbot_api(request):
    """Endpoint POST pour recevoir les questions du frontend et appeler le webhook n8n."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        payload = {}

    question = (payload.get('question') or payload.get('chatInput') or '').strip()

    if not question:
        return JsonResponse({'error': 'Aucune question fournie.'}, status=400)

    user_context = _get_user_context(request)

    user_type = payload.get('user_type') or payload.get('userType') or user_context['userType']
    user_name = payload.get('user_name') or payload.get('userName') or user_context['userName']
    user_id = payload.get('user_id') or payload.get('userId') or user_context['userId']
    operator_id = payload.get('operator_id') or user_context['operatorId']
    interface = user_context['interface']

    n8n_url = f"{settings.N8N_WEBHOOK_BASE.rstrip('/')}/{settings.N8N_CHATBOT_WEBHOOK.lstrip('/')}"

    try:
        system_prompt = payload.get('systemPrompt') or payload.get('system_message') or payload.get('systemMessage')

        body_data = {
            "question": question,
            "chatInput": question,
            "user": user_name,
            "interface": interface,
            "userType": user_type,
            "userId": user_id,
            "operatorId": operator_id,
        }

        # Ajouter le system prompt s'il est fourni
        if system_prompt:
            body_data["systemPrompt"] = system_prompt
            body_data["system_message"] = system_prompt

        normalized_status = payload.get('normalizedStatus')
        if normalized_status:
            known_statuses = [
                "Non affectee", "Affectee", "En cours de confirmation", "Confirmee",
                "A imprimer", "En preparation", "Collectee", "Emballee", "Validee",
                "En livraison", "Livree", "Retournee", "Erronee", "Doublon",
                "Report de confirmation", "Confirmation decalee"
            ]

            import unicodedata

            def strip_accents(s):
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

            def canon(s):
                return strip_accents(s).replace(' ', '').upper()

            canon_normalized = canon(normalized_status)

            for ks in known_statuses:
                if canon(ks) == canon_normalized:
                    body_data['normalizedStatus'] = ks
                    break

        n8n_payload = {
            "body": body_data,
            "sessionId": f"django-{request.session.session_key or 'anonymous'}",
            "interfaceType": interface,
            "operatorType": user_type,
            "operatorName": user_name,
            "operatorId": operator_id,
            "interface": interface,
            "userType": user_type,
            "userName": user_name,
            "userId": user_id,
            # Liste canonique des états de commande (fournie à n8n pour matching / normalisation)
            "knownStatuses": [
                "Non affectee", "Affectee", "En cours de confirmation", "Confirmee",
                "A imprimer", "En preparation", "Collectee", "Emballee", "Validee",
                "En livraison", "Livree", "Retournee", "Erronee", "Doublon",
                "Report de confirmation", "Confirmation decalee"
            ],
        }

        resp = _post_to_n8n_with_retries(n8n_url, n8n_payload)
        resp.raise_for_status()

        try:
            data = resp.json()
        except Exception:
            data = {"output": resp.text}

        return JsonResponse(data, status=200)

    except requests.exceptions.RequestException as e:
        print(f"[chatbot] Erreur requête n8n: {e}")
        return JsonResponse({
            'error': 'Erreur de communication avec le service de chat',
            'details': str(e)
        }, status=502)
    except Exception as e:
        print(f"[chatbot] Erreur inattendue: {e}")
        return JsonResponse({
            'error': 'Erreur interne du serveur',
            'details': str(e)
        }, status=500)


@csrf_exempt
def chatbot_data(request):
    """Endpoint pour récupérer des données structurées pour le chatbot.

    Note: Ce endpoint est déprécié. La logique de RAG est maintenant gérée par n8n.
    Cette fonction est conservée pour la compatibilité avec d'anciens clients.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        payload = {}

    question = payload.get('question', '').strip()

    if not question:
        return JsonResponse({'error': 'Aucune question fournie.'}, status=400)

    # Rediriger vers l'API principale du chatbot qui utilise n8n
    return JsonResponse({
        'deprecated': True,
        'message': 'Ce endpoint est déprécié. Utilisez /api/chatbot/ à la place.',
        'redirect_to': '/api/chatbot/'
    }, status=301)
