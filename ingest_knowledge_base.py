"""
Script d'ingestion de données dans la base vectorielle pgvector
Convertit les données Django (articles, KPIs, etc.) en embeddings et les stocke dans pgvector
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


def get_openai_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Génère un embedding avec OpenAI
    
    Args:
        text: Texte à convertir en embedding
        model: Modèle d'embedding à utiliser
    
    Returns:
        Liste de floats représentant l'embedding
    """
    try:
        from openai import OpenAI
        
        # Récupérer la clé API depuis les variables d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY non définie dans les variables d'environnement")
        
        client = OpenAI(api_key=api_key)
        
        # Nettoyer le texte
        text = text.replace("\n", " ").strip()
        
        # Générer l'embedding
        response = client.embeddings.create(
            input=text,
            model=model
        )
        
        return response.data[0].embedding
        
    except ImportError:
        print("❌ Erreur: Le package 'openai' n'est pas installé")
        print("   Installez-le avec: pip install openai")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la génération de l'embedding: {e}")
        raise


def prepare_article_content(article: Article) -> Dict[str, Any]:
    """
    Prépare le contenu d'un article pour l'ingestion
    
    Args:
        article: Instance du modèle Article
    
    Returns:
        Dictionnaire avec content et metadata
    """
    # Construire le contenu textuel
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
    
    # Métadonnées
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
    """
    Prépare le contenu d'une catégorie pour l'ingestion
    
    Args:
        categorie: Instance du modèle Categorie
    
    Returns:
        Dictionnaire avec content et metadata
    """
    # Compter les articles dans cette catégorie
    article_count = Article.objects.filter(categorie=categorie, actif=True).count()
    
    content_parts = [
        f"Catégorie: {categorie.nom_categorie}",
        f"Nombre d'articles actifs: {article_count}",
    ]
    
    if hasattr(categorie, 'description') and categorie.description:
        content_parts.append(f"Description: {categorie.description}")
    
    # Lister les sous-catégories
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


def insert_into_pgvector(content: str, metadata: Dict, embedding: List[float]):
    """
    Insère un document dans la table pgvector
    
    Args:
        content: Contenu textuel du document
        metadata: Métadonnées JSON
        embedding: Vecteur d'embedding
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO chatbot_knowledge_base (content, metadata, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, [content, json.dumps(metadata), embedding])


def ingest_articles(limit: int = None):
    """
    Ingère les articles dans la base vectorielle
    
    Args:
        limit: Nombre maximum d'articles à ingérer (None = tous)
    """
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
            # Préparer le contenu
            data = prepare_article_content(article)
            
            # Générer l'embedding
            embedding = get_openai_embedding(data["content"])
            
            # Insérer dans pgvector
            insert_into_pgvector(data["content"], data["metadata"], embedding)
            
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
            # Préparer le contenu
            data = prepare_category_content(categorie)
            
            # Générer l'embedding
            embedding = get_openai_embedding(data["content"])
            
            # Insérer dans pgvector
            insert_into_pgvector(data["content"], data["metadata"], embedding)
            
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingestion de données dans pgvector")
    parser.add_argument('--clear', action='store_true', help="Vider la base avant l'ingestion")
    parser.add_argument('--articles', action='store_true', help="Ingérer les articles")
    parser.add_argument('--categories', action='store_true', help="Ingérer les catégories")
    parser.add_argument('--all', action='store_true', help="Ingérer toutes les données")
    parser.add_argument('--limit', type=int, help="Limiter le nombre d'articles à ingérer")
    parser.add_argument('--stats', action='store_true', help="Afficher les statistiques")
    
    args = parser.parse_args()
    
    print("🚀 Ingestion de données dans pgvector")
    print("=" * 60)
    
    # Vérifier la clé API OpenAI
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Erreur: OPENAI_API_KEY non définie")
        print("   Ajoutez-la dans votre fichier .env ou exportez-la:")
        print("   export OPENAI_API_KEY='votre-clé-api'")
        sys.exit(1)
    
    try:
        if args.clear:
            clear_knowledge_base()
        
        if args.all or args.articles:
            ingest_articles(limit=args.limit)
        
        if args.all or args.categories:
            ingest_categories()
        
        if args.stats or args.all:
            show_stats()
        
        if not any([args.clear, args.articles, args.categories, args.all, args.stats]):
            parser.print_help()
        
        print("=" * 60)
        print("✅ Processus terminé!")
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
