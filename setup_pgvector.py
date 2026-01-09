"""
Script d'installation de pgvector pour le chatbot RAG
Exécute le script SQL d'installation de pgvector dans la base de données PostgreSQL
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line


def install_pgvector():
    """Installe l'extension pgvector et crée la table de connaissances"""
    
    print("🚀 Installation de pgvector...")
    print("=" * 60)
    
    sql_commands = """
    -- 1. Créer l'extension pgvector
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- 2. Créer la table de connaissances pour le RAG
    CREATE TABLE IF NOT EXISTS chatbot_knowledge_base (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB DEFAULT '{}',
        embedding vector(768),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- 3. Créer un index pour la recherche vectorielle rapide
    CREATE INDEX IF NOT EXISTS chatbot_knowledge_embedding_hnsw_idx 
    ON chatbot_knowledge_base 
    USING hnsw (embedding vector_cosine_ops);
    
    -- 4. Créer une fonction pour mettre à jour updated_at automatiquement
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    -- 5. Créer un trigger pour updated_at
    DROP TRIGGER IF EXISTS update_chatbot_knowledge_updated_at ON chatbot_knowledge_base;
    CREATE TRIGGER update_chatbot_knowledge_updated_at
        BEFORE UPDATE ON chatbot_knowledge_base
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        with connection.cursor() as cursor:
            # Exécuter les commandes SQL
            cursor.execute(sql_commands)
            
            # Vérifier l'installation
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            extension = cursor.fetchone()
            
            if extension:
                print("✅ Extension pgvector installée avec succès!")
                print(f"   Version: {extension}")
            else:
                print("❌ Erreur: L'extension pgvector n'a pas pu être installée")
                return False
            
            # Vérifier la table
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'chatbot_knowledge_base';
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("✅ Table chatbot_knowledge_base créée avec succès!")
                
                # Compter les documents
                cursor.execute("SELECT COUNT(*) FROM chatbot_knowledge_base;")
                count = cursor.fetchone()[0]
                print(f"   Documents actuels: {count}")
            else:
                print("❌ Erreur: La table chatbot_knowledge_base n'a pas pu être créée")
                return False
            
            # Vérifier l'index
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'chatbot_knowledge_base';
            """)
            indexes = cursor.fetchall()
            print(f"✅ Index créés: {len(indexes)}")
            for idx in indexes:
                print(f"   - {idx[0]}")
            
        print("=" * 60)
        print("✅ Installation terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        print("\n💡 Assurez-vous que:")
        print("   1. PostgreSQL est en cours d'exécution")
        print("   2. L'extension pgvector est disponible (sudo apt install postgresql-<version>-pgvector)")
        print("   3. Vous avez les droits superuser sur la base de données")
        return False


if __name__ == "__main__":
    success = install_pgvector()
    sys.exit(0 if success else 1)
