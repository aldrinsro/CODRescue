"""
Script d'installation de la base de connaissances en mode compatibilité
Fonctionne SANS pgvector natif en utilisant JSONB pour stocker les embeddings
"""

import os
import sys
import django
import json

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection


def install_knowledge_base_compat():
    """Installe la base de connaissances en mode compatibilité (sans pgvector natif)"""
    
    print("🚀 Installation de la base de connaissances (mode compatibilité)")
    print("=" * 60)
    print("ℹ️  Ce mode fonctionne SANS pgvector natif")
    print("   Les embeddings sont stockés en JSONB")
    print("=" * 60)
    
    sql_commands = """
    -- Créer la table de connaissances sans pgvector natif
    CREATE TABLE IF NOT EXISTS chatbot_knowledge_base (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB DEFAULT '{}',
        embedding_json JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Index pour la recherche full-text
    CREATE INDEX IF NOT EXISTS chatbot_knowledge_content_idx 
    ON chatbot_knowledge_base 
    USING gin(to_tsvector('french', content));
    
    -- Index sur les métadonnées
    CREATE INDEX IF NOT EXISTS chatbot_knowledge_metadata_idx 
    ON chatbot_knowledge_base 
    USING gin(metadata);
    
    -- Fonction de mise à jour du timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Trigger pour updated_at
    DROP TRIGGER IF EXISTS update_chatbot_knowledge_updated_at ON chatbot_knowledge_base;
    CREATE TRIGGER update_chatbot_knowledge_updated_at
        BEFORE UPDATE ON chatbot_knowledge_base
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    
    -- Fonction de recherche par similarité cosinus (version JSON)
    CREATE OR REPLACE FUNCTION cosine_similarity(a JSONB, b JSONB)
    RETURNS FLOAT AS $$
    DECLARE
        dot_product FLOAT := 0;
        norm_a FLOAT := 0;
        norm_b FLOAT := 0;
        i INT;
        val_a FLOAT;
        val_b FLOAT;
    BEGIN
        FOR i IN 0..jsonb_array_length(a)-1 LOOP
            val_a := (a->i)::TEXT::FLOAT;
            val_b := (b->i)::TEXT::FLOAT;
            dot_product := dot_product + (val_a * val_b);
            norm_a := norm_a + (val_a * val_a);
            norm_b := norm_b + (val_b * val_b);
        END LOOP;
        
        IF norm_a = 0 OR norm_b = 0 THEN
            RETURN 0;
        END IF;
        
        RETURN dot_product / (sqrt(norm_a) * sqrt(norm_b));
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """
    
    try:
        with connection.cursor() as cursor:
            # Exécuter les commandes SQL
            cursor.execute(sql_commands)
            
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
            
            # Vérifier les index
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'chatbot_knowledge_base';
            """)
            indexes = cursor.fetchall()
            print(f"✅ Index créés: {len(indexes)}")
            for idx in indexes:
                print(f"   - {idx[0]}")
            
            # Vérifier la fonction cosine_similarity
            cursor.execute("""
                SELECT proname 
                FROM pg_proc 
                WHERE proname = 'cosine_similarity';
            """)
            func_exists = cursor.fetchone()
            if func_exists:
                print("✅ Fonction cosine_similarity créée avec succès!")
            
        print("=" * 60)
        print("✅ Installation terminée avec succès!")
        print("\n💡 Prochaines étapes:")
        print("   1. Ajoutez OPENAI_API_KEY dans votre fichier .env")
        print("   2. Exécutez: python ingest_knowledge_base_compat.py --all")
        print("   3. Configurez votre workflow N8N")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        print("\n💡 Assurez-vous que:")
        print("   1. PostgreSQL est en cours d'exécution")
        print("   2. Vous avez les droits nécessaires sur la base de données")
        return False


if __name__ == "__main__":
    success = install_knowledge_base_compat()
    sys.exit(0 if success else 1)
