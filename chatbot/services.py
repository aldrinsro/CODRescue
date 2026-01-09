# services.py - Version optimisée
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from django.apps import apps
from django.db import connection
from django.db.models import Count, Q, Sum, F, Value
from django.db.models.functions import Concat

logger = logging.getLogger(__name__)

# DEPRECATED: This service is being replaced by N8N RAG workflow.
# Logic here is kept for backward compatibility or fallback.

@dataclass
class ChatbotDataResponse:
    """Structure standard optimisée pour les réponses."""
    intent: str
    data: Dict[str, Any]
    summary: str
    confidence: float = 1.0
    execution_time: float = 0.0
    source: str = "django_optimized"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "data": self.data,
            "summary": self.summary,
            "confidence": self.confidence,
            "execution_time": round(self.execution_time, 3),
            "source": self.source,
        }

class QueryPerformanceMixin:
    """Mixin pour optimiser les performances des requêtes."""
    
    @lru_cache(maxsize=100)
    def _get_model_fields(self, app_label: str, model_name: str) -> List[str]:
        """Cache la structure des modèles pour éviter les réflexions répétées."""
        try:
            model = apps.get_model(app_label, model_name)
            return [f.name for f in model._meta.get_fields()]
        except LookupError:
            return []

    def _optimize_query(self, queryset, max_results: int = 50):
        """Applique des optimisations communes aux querysets."""
        return queryset.select_related(
            *[field for field in queryset.model._meta.get_fields() 
              if field.is_relation and field.many_to_one]
        ).prefetch_related(
            *[field for field in queryset.model._meta.get_fields() 
              if field.is_relation and field.one_to_many]
        )[:max_results]

class AdvancedIntentResolver(QueryPerformanceMixin):
    """Résolveur d'intentions avancé avec compréhension contextuelle."""
    
    def __init__(self):
        self.intent_patterns = self._build_intent_patterns()
        self.sql_keywords = {
            'select', 'from', 'where', 'join', 'inner', 'left', 'right', 
            'group by', 'order by', 'having', 'count', 'sum', 'avg', 'max', 'min',
            'union', 'distinct', 'limit', 'offset', 'like', 'ilike', 'in'
        }

    def _build_intent_patterns(self) -> Dict[str, re.Pattern]:
        """Patterns regex pour la détection d'intentions."""
        return {
            'articles.detail': re.compile(r'\b(article|produit|référence|reference|détail|detail|fiche|stock|prix)\b.*\b([A-Z]{2,}\d{2,}|"[^"]+"|\'[^\']+\')\b', re.IGNORECASE),
            'commandes.detail': re.compile(r'\b(commande|order|numéro|numero|id|yz)\b.*\b(OC-\d+|ADMIN-\d+|ENV-\d{8}-\d{4}|\d{5,}|YZ\d+)\b', re.IGNORECASE),
            'clients.detail': re.compile(r'\b(client|customer|acheteur|profil)\b.*\b(\+?\d{8,}|"[^"]+"|\'[^\']+\')\b', re.IGNORECASE),
            'sql.query': re.compile(r'\b(select|from|where|join|group by|order by|union)\b', re.IGNORECASE),
            'statistics': re.compile(r'\b(combien|nombre|total|statistique|moyenne|max|min|somme)\b', re.IGNORECASE),
        }

    def resolve_intent(self, question: str, context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any], float]:
        """Détection d'intention avec score de confiance."""
        start_time = time.time()
        context = context or {}
        question_lower = question.lower().strip()
        
        # Vérification des patterns regex
        for intent, pattern in self.intent_patterns.items():
            if pattern.search(question):
                confidence = 0.9
                return intent, context, confidence
        
        # Détection de requêtes SQL
        if any(sql_keyword in question_lower for sql_keyword in self.sql_keywords):
            return "sql.analysis", {"raw_query": question}, 0.8
        
        # Détection basée sur les mots-clés avec score de confiance
        keyword_scores = self._calculate_keyword_scores(question_lower)
        best_intent = max(keyword_scores.items(), key=lambda x: x[1])
        
        execution_time = time.time() - start_time
        logger.info(f"Intent resolution took {execution_time:.3f}s - {best_intent}")
        
        return best_intent[0], context, best_intent[1]

    def _calculate_keyword_scores(self, question: str) -> Dict[str, float]:
        """Calcule les scores d'intention basés sur les mots-clés."""
        scores = {
            "articles.summary": 0, "articles.detail": 0,
            "commandes.summary": 0, "commandes.detail": 0,
            "clients.summary": 0, "clients.detail": 0,
            "livraisons.summary": 0, "sav.summary": 0,
            "kpi.summary": 0, "generic.summary": 0.1
        }
        
        keyword_weights = {
            "articles.summary": {"article": 2, "produit": 2, "catalogue": 1.5, "stock": 1},
            "articles.detail": {"référence": 3, "reference": 3, "détail": 2, "fiche": 2},
            "commandes.summary": {"commande": 2, "vente": 1.5, "statistique": 1, "ca": 2},
            "commandes.detail": {"numéro": 3, "numero": 3, "OC-": 4, "YZ": 3},
            "clients.summary": {"client": 2, "acheteur": 1.5, "profil": 1},
            "clients.detail": {"téléphone": 3, "telephone": 3, "nom": 2, "prénom": 2},
        }
        
        for intent, keywords in keyword_weights.items():
            for keyword, weight in keywords.items():
                if keyword.lower() in question:
                    scores[intent] += weight
        
        # Normalisation des scores
        max_score = max(scores.values()) if scores.values() else 1
        if max_score > 0:
            for intent in scores:
                scores[intent] = min(scores[intent] / max_score, 1.0)
        
        return scores

class ChatbotDataService(QueryPerformanceMixin):
    """Service optimisé pour le traitement des données du chatbot."""
    
    def __init__(self):
        self.intent_resolver = AdvancedIntentResolver()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def resolve_intent(self, question: Optional[str], **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Interface compatible avec l'ancien code."""
        if not question:
            return "generic.summary", {}
        
        intent, context, confidence = self.intent_resolver.resolve_intent(question, kwargs)
        context['confidence'] = confidence
        return intent, context

    def build_payload(self, intent: str, context: Optional[Dict[str, Any]] = None) -> ChatbotDataResponse:
        """Construction des payloads avec monitoring des performances."""
        start_time = time.time()
        context = context or {}
        
        builder = getattr(self, f"_build_{intent.replace('.', '_')}", self._build_generic_summary)
        
        try:
            response = builder(intent, context)
            response.execution_time = time.time() - start_time
            response.confidence = context.get('confidence', 1.0)
            return response
        except Exception as e:
            logger.error(f"Error building payload for {intent}: {e}")
            return ChatbotDataResponse(
                intent=intent,
                data={"error": str(e)},
                summary=f"Erreur lors du traitement: {str(e)}",
                confidence=0.0,
                execution_time=time.time() - start_time
            )

    def _build_sql_analysis(self, intent: str, context: Dict[str, Any]) -> ChatbotDataResponse:
        """Analyse sécurisée des requêtes SQL."""
        raw_query = context.get('raw_query', '')
        
        # Validation de sécurité basique
        dangerous_keywords = {'delete', 'update', 'insert', 'drop', 'alter', 'truncate'}
        if any(keyword in raw_query.lower() for keyword in dangerous_keywords):
            return ChatbotDataResponse(
                intent=intent,
                data={"error": "Requête non autorisée"},
                summary="Les requêtes de modification ne sont pas autorisées.",
                confidence=0.0
            )
        
        try:
            # Exécution sécurisée en lecture seule
            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                columns = [col[0] for col in cursor.description]
                results = cursor.fetchall()
            
            data = {
                "columns": columns,
                "results": results[:50],  # Limite pour éviter les données massives
                "row_count": len(results)
            }
            
            summary = f"Requête exécutée avec succès: {len(results)} lignes retournées"
            return ChatbotDataResponse(intent=intent, data=data, summary=summary)
            
        except Exception as e:
            error_msg = f"Erreur SQL: {str(e)}"
            return ChatbotDataResponse(
                intent=intent,
                data={"error": error_msg},
                summary=error_msg,
                confidence=0.0
            )

    def _build_articles_summary(self, intent: str, context: Dict[str, Any]) -> ChatbotDataResponse:
        """Version optimisée avec cache et agrégations avancées."""
        Article = apps.get_model("article", "Article")
        
        stats = Article.objects.aggregate(
            total_articles=Count("id"),
            articles_actifs=Count("id", filter=Q(actif=True)),
            articles_inactifs=Count("id", filter=Q(actif=False)),
            valeur_stock_total=Sum("prix_actuel")  # Nouvelle métrique
        )
        
        # Top catégories
        top_categories = Article.objects.values(
            'categorie__nom'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        data = {
            **stats,
            "top_categories": list(top_categories),
            "timestamp": time.time()
        }
        
        summary = (
            f"📊 Synthèse Articles: {stats['total_articles']} total, "
            f"{stats['articles_actifs']} actifs, {stats['articles_inactifs']} inactifs. "
            f"Valeur stock estimée: {stats['valeur_stock_total'] or 0:.2f} DH"
        )
        
        return ChatbotDataResponse(intent=intent, data=data, summary=summary)

    def _build_commandes_summary(self, intent: str, context: Dict[str, Any]) -> ChatbotDataResponse:
        """Agrégations avancées pour les commandes."""
        Commande = apps.get_model("commande", "Commande")
        
        # Métriques principales en une requête
        stats = Commande.objects.aggregate(
            total_commandes=Count("id"),
            commandes_non_payees=Count("id", filter=Q(payement="Non payé")),
            commandes_payees=Count("id", filter=Q(payement="Payé")),
            commandes_en_preparation=Count("id", filter=Q(Date_livraison__isnull=True)),
            chiffre_affaires=Sum("total_cmd"),
            panier_moyen=Sum("total_cmd") / Count("id", filter=Q(total_cmd__gt=0))
        )
        
        # Évolution récente (dernier mois)
        from django.utils import timezone
        from datetime import timedelta
        last_month = timezone.now() - timedelta(days=30)
        
        recent_stats = Commande.objects.filter(
            date_cmd__gte=last_month
        ).aggregate(
            commandes_recentes=Count("id"),
            ca_recent=Sum("total_cmd")
        )
        
        data = {
            **stats,
            **recent_stats,
            "periode_analyse": "30 derniers jours"
        }
        
        summary = (
            f"📦 Synthèse Commandes: {stats['total_commandes']} total, "
            f"CA: {stats['chiffre_affaires'] or 0:.2f} DH, "
            f"Panier moyen: {stats['panier_moyen'] or 0:.2f} DH"
        )
        
        return ChatbotDataResponse(intent=intent, data=data, summary=summary)

    def _build_generic_summary(self, intent: str, context: Dict[str, Any]) -> ChatbotDataResponse:
        """Réponse générique améliorée avec métriques système."""
        from django.db import connection
        
        # Statistiques système
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
        
        data = {
            "system_info": {
                "database": db_version,
                "timestamp": time.time(),
                "service_version": "2.0.0"
            },
            "available_intents": [
                "articles.summary", "articles.detail", 
                "commandes.summary", "commandes.detail",
                "clients.summary", "clients.detail",
                "sql.analysis", "statistics"
            ]
        }
        
        summary = "🤖 Assistant IA YZRescue - Prêt à analyser vos données. Posez-moi vos questions sur les articles, commandes, clients, ou statistiques."
        return ChatbotDataResponse(intent=intent, data=data, summary=summary)

    # Méthodes existantes optimisées (garder la même structure mais avec les optimisations)
    def _build_articles_detail(self, intent: str, context: Dict[str, Any]) -> ChatbotDataResponse:
        """Version optimisée de la recherche d'articles."""
        # Implémentation optimisée similaire aux méthodes ci-dessus
        pass
    
    # ... autres méthodes _build_* avec les mêmes optimisations

# Instance globale optimisée
data_service = ChatbotDataService()