"""
Script de test rapide pour un seul fichier FITS
Utilisez ce script pour tester avant de traiter tous les fichiers
"""

from extract_fits_to_csv import process_single_fits, extract_tic_from_filename, extract_sector_from_filename
from pathlib import Path
import pandas as pd

def test_single_file():
    # Trouver le premier fichier FITS
    fits_dir = Path("data/TESS/fits")
    fits_files = list(fits_dir.glob("*.fits"))
    
    if not fits_files:
        print("❌ Aucun fichier FITS trouvé dans data/TESS/fits/")
        return
    
    # Prendre le premier fichier
    test_file = fits_files[0]
    output_dir = Path("test_final")
    
    print("=" * 70)
    print("TEST D'EXTRACTION D'UN FICHIER FITS")
    print("=" * 70)
    print(f"\n📁 Fichier de test: {test_file.name}")
    
    # Extraire le TIC et le secteur
    tic = extract_tic_from_filename(test_file.name)
    sector = extract_sector_from_filename(test_file.name)
    print(f"🎯 TIC extrait: {tic}")
    print(f"📡 Secteur extrait: {sector}")
    
    # Traiter le fichier
    result = process_single_fits(test_file, output_dir)
    
    # Afficher le résultat
    print(f"\n📊 Résultat:")
    if result['status'] == 'success':
        print(f"   ✅ Statut: {result['status']}")
        print(f"   📄 Fichier CSV: {result['output']}")
        print(f"   🎯 TIC: {result['tic']}")
        print(f"   📡 Secteur: {result['sector']}")
        print(f"   📏 Nombre de lignes: {result['rows']}")
        
        # Charger et afficher le CSV
        df = pd.read_csv(result['output'])
        print(f"\n📋 Aperçu du CSV généré:")
        print(f"   • Colonnes: {list(df.columns)}")
        print(f"   • Shape: {df.shape}")
        print(f"   • Dernières colonnes: {list(df.columns[-3:])}")
        print(f"\n   Premières lignes (avec colonnes TIC et SECTOR à la fin):")
        print(df.head(3).to_string(index=False))
        
        # Vérifications
        print(f"\n✅ Vérifications:")
        print(f"   • Colonne TIC présente: {'TIC' in df.columns}")
        print(f"   • Colonne SECTOR présente: {'SECTOR' in df.columns}")
        print(f"   • Valeur TIC: {df['TIC'].iloc[0]}")
        print(f"   • Valeur SECTOR: {df['SECTOR'].iloc[0]}")
        print(f"   • TIC unique dans le fichier: {df['TIC'].nunique() == 1}")
        print(f"   • SECTOR unique dans le fichier: {df['SECTOR'].nunique() == 1}")
        
    elif result['status'] == 'skipped':
        print(f"   ⏭️  Statut: fichier déjà existant")
        print(f"   📄 Fichier CSV: {result['output']}")
        
    else:
        print(f"   ❌ Statut: {result['status']}")
        print(f"   ⚠️  Erreur: {result.get('error', 'Erreur inconnue')}")
    print("=" * 70)

if __name__ == '__main__':
    test_single_file()
