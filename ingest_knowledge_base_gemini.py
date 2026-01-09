"""
Script d'ingestion de données avec Google Gemini (SANS OpenAI)
Utilise l'API Google Gemini pour générer les embeddings
"""

import os
import sys
import django
import json
from typing import List, Dict, Any

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from article.models import Article
from parametre.models import Categorie, SousCategorie


def get_gemini_embedding(text: str, model: str = "models/text-embedding-004") -> List[float]:
    """
    Génère un embedding avec Google Gemini
    
    Args:
        text: Texte à convertir en embedding
        model: Modèle d'embedding à utiliser
    
    Returns:
        Liste de floats représentant l'embedding
    """
    try:
        import google.generativeai as genai
        
        # Récupérer la clé API depuis les variables d'environnement
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY ou GEMINI_API_KEY non définie dans les variables d'environnement")
        
        # Configurer Gemini
        genai.configure(api_key=api_key)
        
        # Nettoyer le texte
        text = text.replace("\n", " ").strip()
        
        # Générer l'embedding
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
        
    except ImportError:
        print("❌ Erreur: Le package 'google-generativeai' n'est pas installé")
        print("   Installez-le avec: pip install google-generativeai")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la génération de l'embedding: {e}")
        raise


def prepare_article_content(article: Article) -> Dict[str, Any]:
    """Prépare le contenu d'un article pour l'ingestion"""
    content_parts = [
        f"Article: {article.nom_article}",
        f"Code: {article.code_article}",
    ]
    
    if article.description:
        content_parts.append(f"Description: {article.description}")
    
    if hasattr(article, 'categorie') and article.categorie:
        content_parts.append(f"Catégorie: {article.categorie.nom_categorie}")
    
    if hasattr(article, 'sous_categorie') and article.sous_categorie:
        content_parts.append(f"Sous-catégorie: {article.sous_categorie.nom_sous_categorie}")
    
    content_parts.append(f"Statut: {'Actif' if article.actif else 'Inactif'}")
    
    if hasattr(article, 'prix_unitaire') and article.prix_unitaire:
        content_parts.append(f"Prix unitaire: {article.prix_unitaire} DH")
    
    content = "\n".join(content_parts)
    
    metadata = {
        "source": "article_database",
        "article_id": article.id,
        "code_article": article.code_article,
        "type": "article",
        "actif": article.actif,
        "categorie_id": article.categorie.id if hasattr(article, 'categorie') and article.categorie else None,
        "sous_categorie_id": article.sous_categorie.id if hasattr(article, 'sous_categorie') and article.sous_categorie else None,
    }
    
    return {
        "content": content,
        "metadata": metadata
    }


def prepare_category_content(categorie: Categorie) -> Dict[str, Any]:
    """Prépare le contenu d'une catégorie pour l'ingestion"""
    article_count = Article.objects.filter(categorie=categorie, actif=True).count()
    
    content_parts = [
        f"Catégorie: {categorie.nom_categorie}",
        f"Nombre d'articles actifs: {article_count}",
    ]
    
    if hasattr(categorie, 'description') and categorie.description:
        content_parts.append(f"Description: {categorie.description}")
    
    sous_categories = SousCategorie.objects.filter(categorie=categorie)
    if sous_categories.exists():
        sous_cat_names = [sc.nom_sous_categorie for sc in sous_categories]
        content_parts.append(f"Sous-catégories: {', '.join(sous_cat_names)}")
    
    content = "\n".join(content_parts)
    
    metadata = {
        "source": "category_database",
        "categorie_id": categorie.id,
        "type": "categorie",
        "article_count": article_count,
    }
    
    return {
        "content": content,
        "metadata": metadata
    }


def insert_into_knowledge_base(content: str, metadata: Dict, embedding: List[float]):
    """Insère un document dans la table (mode compatibilité JSONB)"""
    with connection.cursor() as cursor:
        # Convertir l'embedding en JSONB
        embedding_json = json.dumps(embedding)
        
        cursor.execute("""
            INSERT INTO chatbot_knowledge_base (content, metadata, embedding_json)
            VALUES (%s, %s, %s::jsonb)
            ON CONFLICT DO NOTHING
        """, [content, json.dumps(metadata), embedding_json])


def ingest_articles(limit: int = None):
    """Ingère les articles dans la base vectorielle"""
    print("📦 Ingestion des articles...")
    
    articles = Article.objects.all()
    if limit:
        articles = articles[:limit]
    
    total = articles.count()
    print(f"   Total d'articles à traiter: {total}")
    
    success_count = 0
    error_count = 0
    
    for i, article in enumerate(articles, 1):
        try:
            data = prepare_article_content(article)
            embedding = get_gemini_embedding(data["content"])
            insert_into_knowledge_base(data["content"], data["metadata"], embedding)
            
            success_count += 1
            
            if i % 10 == 0:
                print(f"   Progression: {i}/{total} articles traités...")
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Erreur pour l'article {article.code_article}: {e}")
    
    print(f"✅ Articles ingérés: {success_count}/{total}")
    if error_count > 0:
        print(f"❌ Erreurs: {error_count}")


def ingest_categories():
    """Ingère les catégories dans la base vectorielle"""
    print("📂 Ingestion des catégories...")
    
    categories = Categorie.objects.all()
    total = categories.count()
    print(f"   Total de catégories à traiter: {total}")
    
    success_count = 0
    error_count = 0
    
    for i, categorie in enumerate(categories, 1):
        try:
            data = prepare_category_content(categorie)
            embedding = get_gemini_embedding(data["content"])
            insert_into_knowledge_base(data["content"], data["metadata"], embedding)
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Erreur pour la catégorie {categorie.nom_categorie}: {e}")
    
    print(f"✅ Catégories ingérées: {success_count}/{total}")
    if error_count > 0:
        print(f"❌ Erreurs: {error_count}")


def clear_knowledge_base():
    """Vide la base de connaissances"""
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM chatbot_knowledge_base")
        print("🗑️  Base de connaissances vidée")


def show_stats():
    """Affiche les statistiques de la base de connaissances"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM chatbot_knowledge_base")
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT metadata->>'type' as type, COUNT(*) as count
            FROM chatbot_knowledge_base
            GROUP BY metadata->>'type'
        """)
        by_type = cursor.fetchall()
        
        print("\n📊 Statistiques de la base de connaissances:")
        print(f"   Total de documents: {total}")
        print("   Par type:")
        for type_name, count in by_type:
            print(f"      - {type_name}: {count}")


def test_search(query: str, limit: int = 5):
    """Teste la recherche vectorielle"""
    print(f"\n🔍 Test de recherche: '{query}'")
    print("=" * 60)
    
    try:
        # Générer l'embedding de la requête
        query_embedding = get_gemini_embedding(query)
        query_embedding_json = json.dumps(query_embedding)
        
        # Rechercher les documents les plus similaires
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    content,
                    metadata,
                    cosine_similarity(embedding_json, %s::jsonb) as similarity
                FROM chatbot_knowledge_base
                WHERE embedding_json IS NOT NULL
                ORDER BY similarity DESC
                LIMIT %s
            """, [query_embedding_json, limit])
            
            results = cursor.fetchall()
            
            if not results:
                print("❌ Aucun résultat trouvé")
                return
            
            print(f"✅ {len(results)} résultats trouvés:\n")
            
            for i, (doc_id, content, metadata, similarity) in enumerate(results, 1):
                print(f"[{i}] Similarité: {similarity:.4f}")
                print(f"    Type: {metadata.get('type', 'N/A')}")
                print(f"    Contenu: {content[:200]}...")
                print()
    
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingestion de données avec Google Gemini")
    parser.add_argument('--clear', action='store_true', help="Vider la base avant l'ingestion")
    parser.add_argument('--articles', action='store_true', help="Ingérer les articles")
    parser.add_argument('--categories', action='store_true', help="Ingérer les catégories")
    parser.add_argument('--all', action='store_true', help="Ingérer toutes les données")
    parser.add_argument('--limit', type=int, help="Limiter le nombre d'articles")
    parser.add_argument('--stats', action='store_true', help="Afficher les statistiques")
    parser.add_argument('--test', type=str, help="Tester la recherche avec une requête")
    
    args = parser.parse_args()
    
    print("🚀 Ingestion de données avec Google Gemini")
    print("=" * 60)
    
    # Vérifier la clé API Google
    if not (os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')) and not args.stats:
        print("❌ Erreur: GOOGLE_API_KEY ou GEMINI_API_KEY non définie")
        print("   Obtenez votre clé sur: https://makersuite.google.com/app/apikey")
        print("   Puis ajoutez-la dans votre environnement:")
        print("   [System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'votre-cle', 'User')")
        sys.exit(1)
    
    try:
        if args.clear:
            clear_knowledge_base()
        
        if args.all or args.articles:
            ingest_articles(limit=args.limit)
        
        if args.all or args.categories:
            ingest_categories()
        
        if args.test:
            test_search(args.test)
        
        if args.stats or args.all:
            show_stats()
        
        if not any([args.clear, args.articles, args.categories, args.all, args.stats, args.test]):
            parser.print_help()
        
        print("=" * 60)
        print("✅ Processus terminé!")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
