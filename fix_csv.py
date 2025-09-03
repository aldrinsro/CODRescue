#!/usr/bin/env python3
"""
Script de correction du fichier CSV mal formaté
"""

import csv
import sys
import os

def fix_csv_format(input_file, output_file):
    """Corrige le format CSV mal structuré"""
    
    if not os.path.exists(input_file):
        print(f"ERREUR: Fichier non trouvé: {input_file}")
        return
    
    print(f"Correction du fichier: {input_file}")
    print(f"Fichier de sortie: {output_file}")
    print("=" * 50)
    
    lignes_corrigees = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # Lire et traiter chaque ligne
            for line_num, row in enumerate(reader, 1):
                if line_num == 1:
                    # En-tête - garder tel quel
                    writer.writerow(row)
                    print(f"En-tête: {row}")
                else:
                    # Pour les données, si tout est dans la première colonne, séparer
                    if len(row) == 1 and ',' in row[0]:
                        # Tout est dans la première colonne, séparer manuellement
                        data_str = row[0]
                        # Parsing manuel plus intelligent
                        corrected_row = parse_malformed_row(data_str)
                        writer.writerow(corrected_row)
                        lignes_corrigees += 1
                        
                        if lignes_corrigees <= 5:  # Afficher les 5 premières pour vérification
                            print(f"Ligne {line_num} corrigée: {corrected_row[:6]}...")  # Afficher les 6 premiers champs
                    else:
                        # La ligne semble déjà correcte
                        writer.writerow(row)
    
    except Exception as e:
        print(f"ERREUR: {str(e)}")
        return
    
    print(f"\nTerminé! {lignes_corrigees} lignes corrigées")
    print(f"Fichier corrigé sauvé: {output_file}")

def parse_malformed_row(data_str):
    """Parse une ligne mal formatée en essayant de séparer intelligemment les champs"""
    
    # Cette fonction essaie de parser une ligne comme:
    # 'CHAUSS FEM YZ131,CHAUSSURE,FEMME,"239,00DH",37---41,BEIGE - BLEU MARINE...'
    
    parts = []
    current_part = ""
    in_quotes = False
    
    i = 0
    while i < len(data_str):
        char = data_str[i]
        
        if char == '"':
            in_quotes = not in_quotes
            current_part += char
        elif char == ',' and not in_quotes:
            parts.append(current_part.strip())
            current_part = ""
        else:
            current_part += char
        i += 1
    
    # Ajouter la dernière partie
    if current_part.strip():
        parts.append(current_part.strip())
    
    # Nettoyer les guillemets et assurer qu'on a 13 colonnes
    cleaned_parts = []
    for part in parts:
        cleaned_part = part.strip('"').strip()
        cleaned_parts.append(cleaned_part)
    
    # S'assurer qu'on a exactement 13 colonnes (selon l'analyse précédente)
    while len(cleaned_parts) < 13:
        cleaned_parts.append("")
    
    return cleaned_parts[:13]  # Garder seulement les 13 premières

def main():
    if len(sys.argv) != 3:
        print("Usage: python fix_csv.py <fichier_source.csv> <fichier_destination.csv>")
        print("Exemple: python fix_csv.py \"structure - article.csv\" \"structure - article - fixed.csv\"")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    fix_csv_format(input_file, output_file)

if __name__ == "__main__":
    main()