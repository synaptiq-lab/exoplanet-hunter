#!/usr/bin/env python3
"""
Script pour extraire le contenu d'un fichier FITS TESS dans un dossier séparé.
Le script extrait:
- Les métadonnées (header) en format texte et JSON
- Les données de la courbe de lumière en CSV
- Les informations sur chaque extension

Dépendances:
    pip install astropy pandas numpy pyarrow

Usage:
    python test_fits.py [fichier_fits] [dossier_sortie]
    
Exemples:
    python test_fits.py
    python test_fits.py data/TESS/fits/mon_fichier.fits output
"""

from pathlib import Path
import json
import sys

from astropy.io import fits
import pandas as pd
import numpy as np


def extract_fits_content(fits_file: Path, output_dir: Path):
    """
    Extrait tout le contenu d'un fichier FITS dans un dossier de sortie.
    
    Args:
        fits_file (Path): Chemin vers le fichier FITS
        output_dir (Path): Dossier de sortie pour les fichiers extraits
    """
    # Créer le dossier de sortie
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nom de base pour les fichiers de sortie
    base_name = fits_file.stem  # Sans l'extension .fits
    
    print(f"📂 Extraction du fichier FITS: {fits_file.name}")
    print(f"📁 Dossier de sortie: {output_dir.resolve()}")
    print("-" * 80)
    
    # Ouvrir le fichier FITS
    with fits.open(fits_file) as hdul:
        # Afficher les informations générales
        print(f"\n{'='*80}")
        print(f"INFORMATIONS GÉNÉRALES")
        print(f"{'='*80}")
        print(f"Nombre d'extensions HDU: {len(hdul)}")
        print("\nStructure du fichier FITS:")
        hdul.info()
        
        # Sauvegarder la structure
        structure_file = output_dir / f"{base_name}_structure.txt"
        with open(structure_file, 'w') as f:
            f.write(f"Structure du fichier FITS: {fits_file.name}\n")
            f.write("="*80 + "\n\n")
            for i, hdu in enumerate(hdul):
                f.write(f"Extension {i}: {hdu.name}\n")
                f.write(f"  Type: {type(hdu).__name__}\n")
                if hasattr(hdu, 'data') and hdu.data is not None:
                    f.write(f"  Shape: {hdu.data.shape if hasattr(hdu.data, 'shape') else 'N/A'}\n")
                f.write("\n")
        print(f"✅ Structure sauvegardée: {structure_file.name}")
        
        # Extraire chaque extension
        for i, hdu in enumerate(hdul):
            extension_name = hdu.name if hdu.name else f"HDU_{i}"
            print(f"\n{'='*80}")
            print(f"EXTENSION {i}: {extension_name}")
            print(f"{'='*80}")
            
            # 1. Extraire le header (métadonnées)
            header_file = output_dir / f"{base_name}_{extension_name}_header.txt"
            with open(header_file, 'w') as f:
                f.write(f"Header de l'extension {i}: {extension_name}\n")
                f.write("="*80 + "\n\n")
                for card in hdu.header.cards:
                    f.write(f"{card}\n")
            print(f"✅ Header sauvegardé: {header_file.name}")
            
            # 2. Extraire le header en JSON
            header_json = {}
            for key in hdu.header:
                value = hdu.header[key]
                comment = hdu.header.comments[key]
                # Convertir les types numpy en types Python pour JSON
                if isinstance(value, (np.integer, np.floating)):
                    value = value.item()
                elif isinstance(value, np.bool_):
                    value = bool(value)
                elif isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore')
                header_json[key] = {
                    'value': value,
                    'comment': comment
                }
            
            json_file = output_dir / f"{base_name}_{extension_name}_header.json"
            with open(json_file, 'w') as f:
                json.dump(header_json, f, indent=2, default=str)
            print(f"✅ Header JSON sauvegardé: {json_file.name}")
            
            # 3. Extraire les données si présentes
            if hdu.data is not None:
                if isinstance(hdu, fits.BinTableHDU):
                    # C'est une table binaire (comme LIGHTCURVE)
                    print(f"📊 Extension de type table binaire")
                    print(f"   Colonnes: {hdu.columns.names}")
                    print(f"   Nombre de lignes: {len(hdu.data)}")
                    
                    # Convertir en DataFrame pandas
                    data_dict = {}
                    for col in hdu.columns.names:
                        data_dict[col] = hdu.data[col]
                    
                    df = pd.DataFrame(data_dict)
                    
                    # Sauvegarder en CSV
                    csv_file = output_dir / f"{base_name}_{extension_name}_data.csv"
                    df.to_csv(csv_file, index=False)
                    print(f"✅ Données CSV sauvegardées: {csv_file.name}")
                    
                    # Sauvegarder aussi en Parquet (plus compact et rapide)
                    parquet_file = output_dir / f"{base_name}_{extension_name}_data.parquet"
                    df.to_parquet(parquet_file, index=False)
                    print(f"✅ Données Parquet sauvegardées: {parquet_file.name}")
                    
                    # Créer un résumé statistique
                    stats_file = output_dir / f"{base_name}_{extension_name}_stats.txt"
                    with open(stats_file, 'w') as f:
                        f.write(f"Statistiques de l'extension {extension_name}\n")
                        f.write("="*80 + "\n\n")
                        f.write(f"Nombre de lignes: {len(df)}\n")
                        f.write(f"Colonnes: {', '.join(df.columns)}\n\n")
                        f.write("Statistiques descriptives:\n")
                        f.write("-"*80 + "\n")
                        f.write(str(df.describe()))
                    print(f"✅ Statistiques sauvegardées: {stats_file.name}")
                    
                elif isinstance(hdu, fits.ImageHDU) or isinstance(hdu, fits.PrimaryHDU):
                    # C'est une image
                    if hdu.data.size > 0:
                        print(f"🖼️  Extension de type image")
                        print(f"   Shape: {hdu.data.shape}")
                        
                        # Sauvegarder en numpy array
                        npy_file = output_dir / f"{base_name}_{extension_name}_data.npy"
                        np.save(npy_file, hdu.data)
                        print(f"✅ Données numpy sauvegardées: {npy_file.name}")
            else:
                print(f"ℹ️  Pas de données dans cette extension (header seulement)")
    
    # Créer un README récapitulatif
    readme_file = output_dir / f"{base_name}_README.txt"
    with open(readme_file, 'w') as f:
        f.write(f"Extraction du fichier FITS: {fits_file.name}\n")
        f.write("="*80 + "\n\n")
        f.write("FICHIERS EXTRAITS:\n")
        f.write("-"*80 + "\n\n")
        
        # Lister tous les fichiers créés
        for file in sorted(output_dir.glob(f"{base_name}*")):
            size_mb = file.stat().st_size / (1024**2)
            f.write(f"  • {file.name:60s} ({size_mb:6.2f} MB)\n")
        
        f.write("\n\nDESCRIPTION DES FICHIERS:\n")
        f.write("-"*80 + "\n\n")
        f.write("*_structure.txt      : Structure générale du fichier FITS\n")
        f.write("*_header.txt         : Métadonnées brutes (format FITS)\n")
        f.write("*_header.json        : Métadonnées en JSON (plus facile à parser)\n")
        f.write("*_data.csv           : Données de la courbe de lumière en CSV\n")
        f.write("*_data.parquet       : Données en format Parquet (plus compact)\n")
        f.write("*_stats.txt          : Statistiques descriptives des données\n")
        f.write("*_README.txt         : Ce fichier\n")
    
    print(f"\n{'='*80}")
    print(f"✅ EXTRACTION TERMINÉE!")
    print(f"{'='*80}")
    print(f"📁 Tous les fichiers ont été extraits dans: {output_dir.resolve()}")
    print(f"📄 Consultez {readme_file.name} pour un résumé complet")
    
    # Afficher un résumé des fichiers créés
    print(f"\n📊 Fichiers créés:")
    total_size = 0
    for file in sorted(output_dir.glob(f"{base_name}*")):
        size_mb = file.stat().st_size / (1024**2)
        total_size += size_mb
        print(f"   • {file.name:60s} ({size_mb:6.2f} MB)")
    print(f"\n💾 Taille totale: {total_size:.2f} MB")


def main():
    """Point d'entrée principal du script."""
    
    # Configuration par défaut
    DEFAULT_FITS_FILE = "data/TESS/fits/tess2018206045859-s0001-0000000008195886-0120-s_lc.fits"
    DEFAULT_OUTPUT_DIR = "final"
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        fits_file = Path(sys.argv[1])
    else:
        fits_file = Path(DEFAULT_FITS_FILE)
    
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path(DEFAULT_OUTPUT_DIR)
    
    # Vérifier que le fichier FITS existe
    if not fits_file.exists():
        print(f"❌ Erreur: Le fichier FITS '{fits_file}' n'existe pas!")
        print(f"\nUsage: python {sys.argv[0]} [fichier_fits] [dossier_sortie]")
        print(f"   fichier_fits   : Chemin vers le fichier FITS (défaut: {DEFAULT_FITS_FILE})")
        print(f"   dossier_sortie : Dossier de sortie (défaut: {DEFAULT_OUTPUT_DIR})")
        sys.exit(1)
    
    # Extraire le contenu
    try:
        extract_fits_content(fits_file, output_dir)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

