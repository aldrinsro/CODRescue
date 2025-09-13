#!/usr/bin/env python
"""
Script d'importation des régions et villes depuis le fichier CSV
Usage: python import_regions_villes.py
"""

import os
import sys
import django
import csv
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from parametre.models import Region, Ville

def clean_tarif(tarif_str):
    """Nettoie et convertit le tarif en float"""
    if not tarif_str or tarif_str.strip() == '' or tarif_str.strip() == 'DHs':
        return 0.0
    
    # Supprime les caractères non numériques sauf le point
    cleaned = ''.join(c for c in tarif_str if c.isdigit() or c == '.')
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def clean_delai(delai_str):
    """Nettoie et convertit le délai en entier"""
    if not delai_str or delai_str.strip() == '':
        return 0
    
    # Supprime les caractères non numériques
    cleaned = ''.join(c for c in delai_str if c.isdigit())
    
    try:
        return int(cleaned) if cleaned else 0
    except ValueError:
        return 0

def get_tarif_column_name(headers):
    """Trouve le nom correct de la colonne tarif"""
    for header in headers:
        if 'Tarif' in header:
            return header
    return None

def import_data():
    """Importe les données depuis le fichier CSV"""
    
    print("🚀 Début de l'importation des régions et villes...")
    
    # Compteurs
    regions_created = 0
    villes_created = 0
    villes_updated = 0
    errors = 0
    
    try:
        with open('CMD_REGION - CMD_REGION.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Trouver le nom correct de la colonne tarif
            tarif_column = get_tarif_column_name(reader.fieldnames)
            if not tarif_column:
                print("❌ Colonne 'Tarif' non trouvée dans le CSV!")
                print(f"   Colonnes disponibles: {reader.fieldnames}")
                return
            
            print(f"✅ Colonne tarif trouvée: '{tarif_column}'")
            
            for row_num, row in enumerate(reader, start=2):  # Start=2 car ligne 1 = headers
                try:
                    # Extraction des données
                    ville_nom = row['Ville'].strip()
                    region_nom = row['Region'].strip()
                    delai_min = clean_delai(row['Delai min'])
                    delai_max = clean_delai(row['Delai max'])
                    tarif = clean_tarif(row[tarif_column])
                    
                    # Skip les lignes vides
                    if not ville_nom or not region_nom:
                        print(f"⚠️  Ligne {row_num}: Ville ou région vide - ignorée")
                        continue
                    
                    # Validation des délais
                    if delai_min > delai_max:
                        print(f"⚠️  Ligne {row_num}: Délai min ({delai_min}) > Délai max ({delai_max}) - Délai max ajusté")
                        delai_max = delai_min
                    
                    # Créer ou récupérer la région
                    region, region_created = Region.objects.get_or_create(
                        nom_region=region_nom
                    )
                    
                    if region_created:
                        regions_created += 1
                        print(f"✅ Région créée: {region_nom}")
                    
                    # Créer ou récupérer la ville
                    ville, ville_created = Ville.objects.get_or_create(
                        nom=ville_nom,
                        region=region,
                        defaults={
                            'frais_livraison': tarif,
                            'Delai_livraison_min': delai_min,
                            'Delai_livraison_max': delai_max
                        }
                    )
                    
                    if ville_created:
                        villes_created += 1
                        print(f"✅ Ville créée: {ville_nom} ({region_nom}) - {tarif}DH - Délai: {delai_min}-{delai_max}j")
                    else:
                        # Mettre à jour si la ville existe déjà
                        ville.frais_livraison = tarif
                        ville.Delai_livraison_min = delai_min
                        ville.Delai_livraison_max = delai_max
                        ville.save()
                        villes_updated += 1
                        print(f"🔄 Ville mise à jour: {ville_nom} - {tarif}DH - Délai: {delai_min}-{delai_max}j")
                
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur ligne {row_num}: {str(e)}")
                    print(f"   Données: {row}")
                    continue
    
    except FileNotFoundError:
        print("❌ Fichier 'CMD_REGION - CMD_REGION.csv' non trouvé!")
        print("   Assurez-vous que le fichier est dans le même répertoire que ce script.")
        return
    
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
        return
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'IMPORTATION")
    print("="*60)
    print(f"✅ Régions créées: {regions_created}")
    print(f"✅ Villes créées: {villes_created}")
    print(f"🔄 Villes mises à jour: {villes_updated}")
    print(f"❌ Erreurs: {errors}")
    print(f"📈 Total régions en base: {Region.objects.count()}")
    print(f"📈 Total villes en base: {Ville.objects.count()}")
    
    # Affichage des régions créées
    if regions_created > 0:
        print("\n🌍 RÉGIONS CRÉÉES:")
        for region in Region.objects.all().order_by('nom_region'):
            ville_count = region.villes.count()
            print(f"   • {region.nom_region} ({ville_count} villes)")
    
    print("\n🎉 Importation terminée avec succès!")

def show_stats():
    """Affiche les statistiques de la base de données"""
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*60)
    
    regions = Region.objects.all().order_by('nom_region')
    
    for region in regions:
        villes = region.villes.all().order_by('nom')
        tarif_moyen = sum(v.frais_livraison for v in villes) / len(villes) if villes else 0
        delai_moyen_min = sum(v.Delai_livraison_min for v in villes) / len(villes) if villes else 0
        delai_moyen_max = sum(v.Delai_livraison_max for v in villes) / len(villes) if villes else 0
        
        print(f"\n🌍 {region.nom_region}")
        print(f"   📍 Nombre de villes: {villes.count()}")
        print(f"   💰 Tarif moyen: {tarif_moyen:.1f} DH")
        print(f"   ⏱️  Délai moyen: {delai_moyen_min:.1f}-{delai_moyen_max:.1f} jours")
        
        # Affiche quelques villes exemple
        if villes.count() > 0:
            print(f"   🏙️  Villes principales:")
            for ville in villes[:5]:  # Affiche les 5 premières
                print(f"      • {ville.nom} - {ville.frais_livraison}DH - Délai: {ville.Delai_livraison_min}-{ville.Delai_livraison_max}j")
            
            if villes.count() > 5:
                print(f"      ... et {villes.count() - 5} autres villes")

def validate_data():
    """Valide les données existantes dans la base"""
    print("\n" + "="*60)
    print("🔍 VALIDATION DES DONNÉES")
    print("="*60)
    
    villes = Ville.objects.all()
    errors = 0
    
    for ville in villes:
        # Vérifier que les délais sont cohérents
        if ville.Delai_livraison_min > ville.Delai_livraison_max:
            print(f"❌ {ville.nom} ({ville.region.nom_region}): Délai min ({ville.Delai_livraison_min}) > Délai max ({ville.Delai_livraison_max})")
            errors += 1
        
        # Vérifier que les frais sont positifs
        if ville.frais_livraison < 0:
            print(f"❌ {ville.nom} ({ville.region.nom_region}): Frais négatifs ({ville.frais_livraison})")
            errors += 1
    
    if errors == 0:
        print("✅ Toutes les données sont valides!")
    else:
        print(f"⚠️  {errors} erreurs de validation détectées")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            show_stats()
        elif sys.argv[1] == 'validate':
            validate_data()
        else:
            print("Usage: python import_regions_villes.py [stats|validate]")
    else:
        import_data()
        show_stats()
        validate_data() 