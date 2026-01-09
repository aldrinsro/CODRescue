import json
from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

@csrf_exempt
def sync_data(request):
    """
    Endpoint pour exposer les données à vectoriser par N8N.
    Retourne une liste d'objets avec un champ 'text' prêt à être embeddé.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    documents = []

    # 1. Articles
    try:
        Article = apps.get_model("article", "Article")
        articles = Article.objects.filter(actif=True)
        for art in articles:
            text = (
                f"Article: {art.nom} (Réf: {art.reference}). "
                f"Prix: {art.prix_actuel} DH. "
                f"Stock: {art.stock_total}. "
                f"Catégorie: {art.categorie.nom if art.categorie else 'N/A'}."
            )
            documents.append({
                "id": f"article_{art.id}",
                "type": "article",
                "text": text,
                "metadata": {
                    "source": "article",
                    "reference": art.reference,
                    "prix": float(art.prix_actuel) if art.prix_actuel else 0,
                    "stock": art.stock_total
                }
            })
    except LookupError:
        pass

    # 2. Commandes (Récentes - ex: 30 derniers jours pour ne pas surcharger)
    try:
        Commande = apps.get_model("commande", "Commande")
        # On pourrait filtrer sur les commandes récentes ici
        commandes = Commande.objects.all().order_by('-date_cmd')[:100] 
        for cmd in commandes:
            text = (
                f"Commande {cmd.id} (YZ ID: {cmd.id_yz}). "
                f"Client: {cmd.client}. Ville: {cmd.ville}. "
                f"Total: {cmd.total_cmd} DH. "
                f"Statut: {cmd.etat}. Paiement: {cmd.payement}."
            )
            documents.append({
                "id": f"commande_{cmd.id}",
                "type": "commande",
                "text": text,
                "metadata": {
                    "source": "commande",
                    "client": cmd.client,
                    "ville": cmd.ville,
                    "total": float(cmd.total_cmd) if cmd.total_cmd else 0,
                    "statut": cmd.etat
                }
            })
    except LookupError:
        pass

    # 3. Clients (Top clients ou récents)
    # (Optionnel - attention à la confidentialité)

    return JsonResponse({"documents": documents})
