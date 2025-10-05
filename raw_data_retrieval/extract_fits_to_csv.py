"""
Script pour extraire les données de tous les fichiers FITS en CSV
avec le TIC (Target Identification) inclus.
"""

import re
from pathlib import Path
import pandas as pd
import lightkurve as lk
from tqdm import tqdm
import concurrent.futures
from threading import Lock

import warnings
from astropy.utils.exceptions import AstropyWarning
warnings.simplefilter('ignore', category=AstropyWarning)


def extract_tic_from_filename(filename):
    """
    Extrait le TIC depuis le nom de fichier TESS.
    Format: tess*-s*-*TIC*-*-s_lc.fits
    """
    pattern = r"-0+(\d+)-"
    match = re.search(pattern, filename)
    if match:
        return int(match.group(1))
    return None


def extract_sector_from_filename(filename):
    """
    Extrait le numéro de secteur depuis le nom de fichier TESS.
    Format: tess*-s0092-*-s_lc.fits où 0092 est le secteur
    """
    pattern = r"-s(\d+)-"
    match = re.search(pattern, filename)
    if match:
        return int(match.group(1))
    return None


def process_single_fits(fits_path, output_dir, stats_lock=None, stats=None):
    """
    Traite un seul fichier FITS et génère un CSV avec les données
    de la courbe de lumière et le TIC.
    
    Args:
        fits_path (Path): Chemin vers le fichier FITS
        output_dir (Path): Dossier de sortie pour les CSV
        stats_lock (Lock): Lock pour mise à jour thread-safe des stats
        stats (dict): Dictionnaire de statistiques
    
    Returns:
        dict: Résultat du traitement
    """
    try:
        # Extraire le TIC depuis le nom de fichier
        tic = extract_tic_from_filename(fits_path.name)
        
        if tic is None:
            return {
                'status': 'failed',
                'filename': fits_path.name,
                'error': 'Impossible d\'extraire le TIC'
            }
        
        # Extraire le secteur depuis le nom de fichier
        sector = extract_sector_from_filename(fits_path.name)
        
        if sector is None:
            return {
                'status': 'failed',
                'filename': fits_path.name,
                'error': 'Impossible d\'extraire le SECTOR'
            }
        
        # Créer le nom de fichier de sortie
        output_filename = fits_path.stem + '_LIGHTCURVE_data.csv'
        output_path = output_dir / output_filename
        
        # Si le fichier existe déjà, le skipper
        if output_path.exists():
            if stats_lock and stats:
                with stats_lock:
                    stats['skipped'] += 1
            return {
                'status': 'skipped',
                'filename': fits_path.name,
                'output': str(output_path)
            }
        
        # Lire le fichier FITS avec lightkurve
        lc = lk.read(str(fits_path))
        
        # Convertir en DataFrame pandas
        df = lc.to_pandas()
        
        # IMPORTANT: Réinitialiser l'index pour que 'time' devienne une colonne
        # Si l'index s'appelle 'time', on le transforme en colonne
        if df.index.name == 'time' or (hasattr(df.index, 'name') and df.index.name is not None):
            df = df.reset_index()
        
        # Ajouter les colonnes TIC et SECTOR à la fin (pas au début)
        # Cela préserve toutes les colonnes originales
        df['TIC'] = tic
        df['SECTOR'] = sector
        
        # Créer le dossier de sortie s'il n'existe pas
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder en CSV
        df.to_csv(output_path, index=False)
        
        if stats_lock and stats:
            with stats_lock:
                stats['success'] += 1
        
        return {
            'status': 'success',
            'filename': fits_path.name,
            'output': str(output_path),
            'tic': tic,
            'sector': sector,
            'rows': len(df)
        }
        
    except Exception as e:
        if stats_lock and stats:
            with stats_lock:
                stats['failed'] += 1
        return {
            'status': 'failed',
            'filename': fits_path.name,
            'error': str(e)
        }


def extract_dataframe_from_fits(fits_path):
    """
    Extrait le DataFrame d'un fichier FITS avec TIC et SECTOR.
    
    Args:
        fits_path (Path): Chemin vers le fichier FITS
    
    Returns:
        tuple: (DataFrame, dict) - DataFrame ou None si erreur, et résultat
    """
    try:
        # Extraire le TIC depuis le nom de fichier
        tic = extract_tic_from_filename(fits_path.name)
        
        if tic is None:
            return None, {
                'status': 'failed',
                'filename': fits_path.name,
                'error': 'Impossible d\'extraire le TIC'
            }
        
        # Extraire le secteur depuis le nom de fichier
        sector = extract_sector_from_filename(fits_path.name)
        
        if sector is None:
            return None, {
                'status': 'failed',
                'filename': fits_path.name,
                'error': 'Impossible d\'extraire le SECTOR'
            }
        
        # Lire le fichier FITS avec lightkurve
        lc = lk.read(str(fits_path))
        
        # Convertir en DataFrame pandas
        df = lc.to_pandas()
        
        # IMPORTANT: Réinitialiser l'index pour que 'time' devienne une colonne
        # Si l'index s'appelle 'time', on le transforme en colonne
        if df.index.name == 'time' or (hasattr(df.index, 'name') and df.index.name is not None):
            df = df.reset_index()
        
        # Ajouter les colonnes TIC et SECTOR à la fin (pas au début)
        # Cela préserve toutes les colonnes originales
        df['TIC'] = tic
        df['SECTOR'] = sector
        
        return df, {
            'status': 'success',
            'filename': fits_path.name,
            'tic': tic,
            'sector': sector,
            'rows': len(df)
        }
        
    except Exception as e:
        return None, {
            'status': 'failed',
            'filename': fits_path.name,
            'error': str(e)
        }


def process_all_fits_single_csv(fits_dir, output_file='all_lightcurves.csv', max_workers=5, progress_bar=True):
    """
    Traite tous les fichiers FITS et génère UN SEUL fichier CSV avec toutes les données.
    
    Args:
        fits_dir (Path or str): Dossier contenant les fichiers FITS
        output_file (str): Nom du fichier CSV de sortie
        max_workers (int): Nombre de threads parallèles
        progress_bar (bool): Afficher la barre de progression
    
    Returns:
        dict: Résultats du traitement avec statistiques
    """
    fits_dir = Path(fits_dir)
    
    # Trouver tous les fichiers FITS
    fits_files = list(fits_dir.glob('*.fits'))
    
    print(f"Trouvé {len(fits_files)} fichiers FITS à traiter")
    print(f"Fichier de sortie: {output_file}")
    
    # Statistiques
    stats = {
        'total': len(fits_files),
        'success': 0,
        'failed': 0,
        'total_rows': 0
    }
    
    all_dataframes = []
    results = []
    
    # Traitement en parallèle
    if progress_bar:
        with tqdm(total=len(fits_files), desc="Extraction FITS → DataFrame") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(extract_dataframe_from_fits, fits_file): fits_file 
                    for fits_file in fits_files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    df, result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'success' and df is not None:
                        all_dataframes.append(df)
                        stats['success'] += 1
                        stats['total_rows'] += len(df)
                        pbar.set_postfix_str(f"✓ {result['filename']} ({len(df)} rows)")
                    else:
                        stats['failed'] += 1
                        pbar.set_postfix_str(f"✗ {result['filename']} (failed)")
                    
                    pbar.update(1)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(extract_dataframe_from_fits, fits_file) for fits_file in fits_files]
            for future in concurrent.futures.as_completed(futures):
                df, result = future.result()
                results.append(result)
                if result['status'] == 'success' and df is not None:
                    all_dataframes.append(df)
                    stats['success'] += 1
                    stats['total_rows'] += len(df)
                else:
                    stats['failed'] += 1
    
    # Concaténer tous les DataFrames
    if all_dataframes:
        print(f"\n📊 Concaténation de {len(all_dataframes)} DataFrames...")
        final_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Sauvegarder en CSV
        print(f"💾 Sauvegarde du CSV ({len(final_df)} lignes)...")
        final_df.to_csv(output_file, index=False)
        
        print(f"✅ Fichier CSV créé: {output_file}")
        print(f"   • Taille: {Path(output_file).stat().st_size / (1024**2):.2f} MB")
        print(f"   • Lignes: {len(final_df):,}")
        print(f"   • Colonnes: {len(final_df.columns)}")
    else:
        print("❌ Aucun DataFrame à concaténer")
    
    return {
        'results': results,
        'stats': stats,
        'output_file': output_file if all_dataframes else None
    }


def process_all_fits(fits_dir, output_dir, max_workers=5, progress_bar=True):
    """
    Traite tous les fichiers FITS du dossier et génère des CSV.
    
    Args:
        fits_dir (Path or str): Dossier contenant les fichiers FITS
        output_dir (Path or str): Dossier de sortie pour les CSV
        max_workers (int): Nombre de threads parallèles
        progress_bar (bool): Afficher la barre de progression
    
    Returns:
        dict: Résultats du traitement avec statistiques
    """
    fits_dir = Path(fits_dir)
    output_dir = Path(output_dir)
    
    # Trouver tous les fichiers FITS
    fits_files = list(fits_dir.glob('*.fits'))
    
    print(f"Trouvé {len(fits_files)} fichiers FITS à traiter")
    print(f"Dossier de sortie: {output_dir.resolve()}")
    
    # Statistiques
    stats = {
        'total': len(fits_files),
        'success': 0,
        'skipped': 0,
        'failed': 0
    }
    
    stats_lock = Lock()
    results = []
    
    def process_with_stats(fits_path):
        return process_single_fits(fits_path, output_dir, stats_lock, stats)
    
    # Traitement en parallèle
    if progress_bar:
        with tqdm(total=len(fits_files), desc="Traitement FITS → CSV") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(process_with_stats, fits_file): fits_file 
                    for fits_file in fits_files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)
                    
                    # Afficher le statut dans la barre de progression
                    if result['status'] == 'success':
                        pbar.set_postfix_str(f"✓ {result['filename']}")
                    elif result['status'] == 'skipped':
                        pbar.set_postfix_str(f"- {result['filename']} (skipped)")
                    else:
                        pbar.set_postfix_str(f"✗ {result['filename']} (failed)")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_with_stats, fits_files))
    
    return {
        'results': results,
        'stats': stats
    }


def main():
    """
    Fonction principale pour exécuter le script en ligne de commande.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extrait les données des fichiers FITS en UN SEUL CSV avec TIC et SECTOR'
    )
    parser.add_argument(
        '--fits-dir',
        type=str,
        default='data/TESS/fits',
        help='Dossier contenant les fichiers FITS (défaut: data/TESS/fits)'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='all_lightcurves.csv',
        help='Nom du fichier CSV de sortie (défaut: all_lightcurves.csv)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Nombre de threads parallèles (défaut: 5)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("EXTRACTION DES FICHIERS FITS EN UN SEUL CSV")
    print("=" * 70)
    
    # Lancer le traitement
    result = process_all_fits_single_csv(
        fits_dir=args.fits_dir,
        output_file=args.output_file,
        max_workers=args.workers
    )
    
    # Afficher les résultats
    stats = result['stats']
    print(f"\n=== RÉSULTATS DU TRAITEMENT ===")
    print(f"📊 Statistiques:")
    print(f"   • Total fichiers FITS: {stats['total']} fichiers")
    print(f"   • ✅ Succès: {stats['success']} fichiers")
    print(f"   • ❌ Échecs: {stats['failed']} fichiers")
    print(f"   • 📏 Total de lignes: {stats['total_rows']:,} lignes")
    
    # Afficher les erreurs si nécessaire
    if stats['failed'] > 0:
        print(f"\n⚠️  {stats['failed']} fichiers ont échoué:")
        failed_results = [r for r in result['results'] if r['status'] == 'failed']
        for r in failed_results[:10]:  # Afficher les 10 premiers
            print(f"   • {r['filename']}: {r.get('error', 'Erreur inconnue')}")
        if len(failed_results) > 10:
            print(f"   ... et {len(failed_results) - 10} autres échecs")
    
    if result.get('output_file'):
        print(f"\n✅ Traitement terminé!")
        print(f"📄 Fichier généré: {result['output_file']}")
    else:
        print(f"\n❌ Aucun fichier généré")


if __name__ == '__main__':
    main()
