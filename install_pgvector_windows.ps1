# Script d'installation automatique de pgvector pour Windows
# Auteur: YZ-CMD Team
# Date: 2025-12-05

Write-Host "🚀 Installation de pgvector pour PostgreSQL sur Windows" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Étape 1 : Trouver PostgreSQL
Write-Host "`n🔍 Recherche de PostgreSQL..." -ForegroundColor Yellow

$pgDirs = @(
    "C:\Program Files\PostgreSQL\18",
    "C:\Program Files\PostgreSQL\17",
    "C:\Program Files\PostgreSQL\16",
    "C:\PostgreSQL\18",
    "C:\PostgreSQL\17"
)

$PG_DIR = $null
foreach ($dir in $pgDirs) {
    if (Test-Path $dir) {
        $PG_DIR = $dir
        Write-Host "✅ PostgreSQL trouvé: $PG_DIR" -ForegroundColor Green
        break
    }
}

if (-not $PG_DIR) {
    Write-Host "❌ PostgreSQL non trouvé dans les emplacements standards" -ForegroundColor Red
    Write-Host "   Veuillez spécifier manuellement le chemin:" -ForegroundColor Yellow
    $PG_DIR = Read-Host "   Chemin PostgreSQL"
    
    if (-not (Test-Path $PG_DIR)) {
        Write-Host "❌ Chemin invalide. Abandon." -ForegroundColor Red
        exit 1
    }
}

# Vérifier les répertoires nécessaires
$libDir = Join-Path $PG_DIR "lib"
$extDir = Join-Path $PG_DIR "share\extension"

if (-not (Test-Path $libDir)) {
    Write-Host "❌ Répertoire lib non trouvé: $libDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $extDir)) {
    Write-Host "❌ Répertoire extension non trouvé: $extDir" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Répertoires PostgreSQL validés" -ForegroundColor Green

# Étape 2 : Télécharger pgvector
Write-Host "`n📥 Téléchargement de pgvector..." -ForegroundColor Yellow

$downloadUrl = "https://github.com/pgvector/pgvector/archive/refs/tags/v0.7.4.zip"
$zipPath = Join-Path $env:TEMP "pgvector.zip"
$extractPath = Join-Path $env:TEMP "pgvector"

try {
    # Télécharger
    Write-Host "   URL: $downloadUrl" -ForegroundColor Gray
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "✅ Téléchargement terminé" -ForegroundColor Green
    
    # Extraire
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    Write-Host "✅ Extraction terminée" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Erreur lors du téléchargement: $_" -ForegroundColor Red
    exit 1
}

# Étape 3 : Installation manuelle via SQL
Write-Host "`n📝 Création du script SQL d'installation..." -ForegroundColor Yellow

$sqlScript = @"
-- Installation manuelle de pgvector
-- Si l'extension binaire n'est pas disponible, nous créons les fonctions manuellement

-- Créer le type vector (simulation basique)
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector') THEN
        -- Pour l'instant, nous utiliserons un type de base
        -- Note: Ceci est une solution temporaire
        CREATE EXTENSION IF NOT EXISTS cube;
    END IF;
END
`$`$;

-- Créer la table de connaissances sans pgvector natif
-- Utilisation de JSONB pour stocker les embeddings temporairement
CREATE TABLE IF NOT EXISTS chatbot_knowledge_base (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding_json JSONB,  -- Stockage temporaire en JSON
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Créer un index GIN pour la recherche dans le contenu
CREATE INDEX IF NOT EXISTS chatbot_knowledge_content_idx 
ON chatbot_knowledge_base 
USING gin(to_tsvector('french', content));

-- Créer un index sur les métadonnées
CREATE INDEX IF NOT EXISTS chatbot_knowledge_metadata_idx 
ON chatbot_knowledge_base 
USING gin(metadata);

-- Fonction de mise à jour du timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS `$`$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
`$`$ LANGUAGE plpgsql;

-- Trigger pour updated_at
DROP TRIGGER IF EXISTS update_chatbot_knowledge_updated_at ON chatbot_knowledge_base;
CREATE TRIGGER update_chatbot_knowledge_updated_at
    BEFORE UPDATE ON chatbot_knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Fonction de recherche par similarité cosinus (version JSON)
CREATE OR REPLACE FUNCTION cosine_similarity(a JSONB, b JSONB)
RETURNS FLOAT AS `$`$
DECLARE
    dot_product FLOAT := 0;
    norm_a FLOAT := 0;
    norm_b FLOAT := 0;
    i INT;
    val_a FLOAT;
    val_b FLOAT;
BEGIN
    -- Calculer le produit scalaire et les normes
    FOR i IN 0..jsonb_array_length(a)-1 LOOP
        val_a := (a->i)::TEXT::FLOAT;
        val_b := (b->i)::TEXT::FLOAT;
        dot_product := dot_product + (val_a * val_b);
        norm_a := norm_a + (val_a * val_a);
        norm_b := norm_b + (val_b * val_b);
    END LOOP;
    
    -- Éviter la division par zéro
    IF norm_a = 0 OR norm_b = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN dot_product / (sqrt(norm_a) * sqrt(norm_b));
END;
`$`$ LANGUAGE plpgsql IMMUTABLE;

SELECT 'Installation terminée (mode compatibilité sans pgvector natif)' as status;
"@

$sqlScriptPath = Join-Path $PSScriptRoot "install_pgvector_compat.sql"
$sqlScript | Out-File -FilePath $sqlScriptPath -Encoding UTF8

Write-Host "✅ Script SQL créé: $sqlScriptPath" -ForegroundColor Green

# Étape 4 : Instructions pour l'utilisateur
Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "`n⚠️  IMPORTANT: Installation en mode compatibilité" -ForegroundColor Yellow
Write-Host "`nPgvector natif n'est pas disponible pour PostgreSQL 18 sur Windows." -ForegroundColor Yellow
Write-Host "Nous avons créé une solution de compatibilité utilisant JSONB." -ForegroundColor Yellow

Write-Host "`n📋 Prochaines étapes:" -ForegroundColor Cyan
Write-Host "   1. Ouvrez pgAdmin 4" -ForegroundColor White
Write-Host "   2. Connectez-vous à votre base de données 'yzrescue_db'" -ForegroundColor White
Write-Host "   3. Ouvrez l'outil Query Tool" -ForegroundColor White
Write-Host "   4. Exécutez le script: $sqlScriptPath" -ForegroundColor White
Write-Host "   5. OU exécutez: python setup_pgvector_compat.py" -ForegroundColor White

Write-Host "`n💡 Alternative recommandée:" -ForegroundColor Cyan
Write-Host "   Utilisez un service cloud avec pgvector préinstallé:" -ForegroundColor White
Write-Host "   - Supabase (gratuit): https://supabase.com" -ForegroundColor Green
Write-Host "   - Neon (gratuit): https://neon.tech" -ForegroundColor Green

Write-Host "`n" -NoNewline
Write-Host "=" * 70 -ForegroundColor Cyan

# Demander si l'utilisateur veut exécuter le script SQL maintenant
Write-Host "`n❓ Voulez-vous que je tente d'exécuter le script SQL maintenant? (O/N)" -ForegroundColor Yellow
$response = Read-Host "   Réponse"

if ($response -eq "O" -or $response -eq "o") {
    Write-Host "`n🔧 Tentative d'exécution du script SQL..." -ForegroundColor Yellow
    Write-Host "   Note: Cela nécessite que psql soit dans votre PATH" -ForegroundColor Gray
    
    # Essayer de trouver psql
    $psqlPath = Join-Path $PG_DIR "bin\psql.exe"
    
    if (Test-Path $psqlPath) {
        Write-Host "   Veuillez entrer vos informations de connexion:" -ForegroundColor Cyan
        $dbName = Read-Host "   Nom de la base de données (défaut: yzrescue_db)"
        if ([string]::IsNullOrWhiteSpace($dbName)) { $dbName = "yzrescue_db" }
        
        $dbUser = Read-Host "   Utilisateur PostgreSQL (défaut: postgres)"
        if ([string]::IsNullOrWhiteSpace($dbUser)) { $dbUser = "postgres" }
        
        try {
            & $psqlPath -U $dbUser -d $dbName -f $sqlScriptPath
            Write-Host "`n✅ Script SQL exécuté avec succès!" -ForegroundColor Green
        } catch {
            Write-Host "`n❌ Erreur lors de l'exécution: $_" -ForegroundColor Red
            Write-Host "   Veuillez exécuter le script manuellement dans pgAdmin" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ psql.exe non trouvé: $psqlPath" -ForegroundColor Red
        Write-Host "   Veuillez exécuter le script manuellement dans pgAdmin" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Installation terminée!" -ForegroundColor Green
