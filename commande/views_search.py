from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import Commande
from .utils import search_commandes_by_date

@login_required
@require_GET
def ajax_search_commandes_by_date(request):
    """
    AJAX endpoint: ?date=... (peut être une date, un intervalle, ou une expression naturelle)
    Retourne la liste des commandes filtrées (id, date, client, total...)
    """
    date_input = request.GET.get('date', '').strip()
    try:
        qs = search_commandes_by_date(date_input)
        # Limite le nombre de résultats pour éviter surcharge
        results = [
            {
                'id': c.id,
                'date': c.date_commande.strftime('%Y-%m-%d'),
                'client': str(getattr(c, 'client', '')),
                'total': float(getattr(c, 'total', 0)),
            }
            for c in qs[:100]
        ]
        return JsonResponse({'ok': True, 'results': results})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)