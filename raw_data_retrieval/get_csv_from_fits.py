"""
Script de test pour générer UN SEUL CSV avec tous les fichiers FITS
"""

from pathlib import Path
import re
import time
import gc

import pandas as pd
from tqdm import tqdm
import concurrent.futures
import lightkurve as lk


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


def process_all_fits_single_csv(fits_dir, output_file='all_lightcurves.csv', max_workers=3, progress_bar=True, batch_size=100, keep_batches=False):
    """
    Traite tous les fichiers FITS et génère UN SEUL fichier CSV avec toutes les données.
    Stratégie optimisée : crée des fichiers CSV intermédiaires par batch, puis les fusionne.
    Cette approche est plus résiliente aux crashes et permet de reprendre en cas d'erreur.
    
    Args:
        fits_dir (Path or str): Dossier contenant les fichiers FITS
        output_file (str): Nom du fichier CSV de sortie final
        max_workers (int): Nombre de threads parallèles (défaut: 3, max recommandé: 4)
        progress_bar (bool): Afficher la barre de progression
        batch_size (int): Nombre de DataFrames à accumuler avant d'écrire un batch CSV (défaut: 100)
        keep_batches (bool): Garder les fichiers batch temporaires après fusion (défaut: False)
    
    Returns:
        dict: Résultats du traitement avec statistiques
    """
    fits_dir = Path(fits_dir)
    output_path = Path(output_file)
    
    # Créer un dossier temporaire pour les fichiers batch
    batch_dir = output_path.parent / 'temp_batches'
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # Trouver tous les fichiers FITS
    fits_files = list(fits_dir.glob('*.fits'))
    
    print(f"Trouvé {len(fits_files)} fichiers FITS à traiter")
    print(f"Fichier de sortie final: {output_file}")
    print(f"Dossier temporaire: {batch_dir}")
    print(f"Batch size: {batch_size} fichiers (pour optimiser la mémoire)")
    
    # Statistiques
    stats = {
        'total': len(fits_files),
        'success': 0,
        'failed': 0,
        'total_rows': 0
    }
    
    # Nettoyer les anciens fichiers batch s'ils existent
    for old_batch in batch_dir.glob('batch_*.csv'):
        old_batch.unlink()
    
    # S'assurer que le dossier parent du fichier final existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_dataframes = []
    batches_written = 0
    batch_files = []  # Liste des fichiers batch créés
    failed_files = []  # Stocker uniquement les noms de fichiers échoués
    
    # Traitement en parallèle avec écriture par batch dans des fichiers séparés
    if progress_bar:
        with tqdm(total=len(fits_files), desc="Extraction FITS → Batch CSV") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(extract_dataframe_from_fits, fits_file): fits_file 
                    for fits_file in fits_files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    df, result = future.result()
                    
                    if result['status'] == 'success' and df is not None:
                        all_dataframes.append(df)
                        stats['success'] += 1
                        stats['total_rows'] += len(df)
                        pbar.set_postfix_str(f"✓ Batch: {len(all_dataframes)}/{batch_size} | Batches: {batches_written}")
                    else:
                        stats['failed'] += 1
                        failed_files.append(result['filename'])
                        pbar.set_postfix_str(f"✗ Failed: {stats['failed']}")
                    
                    # Écrire le batch dans un fichier séparé quand il atteint la taille définie
                    if len(all_dataframes) >= batch_size:
                        batches_written += 1
                        batch_file = batch_dir / f'batch_{batches_written:04d}.csv'
                        
                        batch_df = pd.concat(all_dataframes, ignore_index=True)
                        batch_df.to_csv(batch_file, index=False)
                        batch_files.append(batch_file)
                        
                        pbar.set_postfix_str(f"💾 Batch {batches_written} écrit ({len(batch_df)} rows) | Nettoyage...")
                        
                        # Libération agressive de la mémoire
                        del all_dataframes
                        del batch_df
                        all_dataframes = []
                        gc.collect()  # Force garbage collection
                        
                        # Petit délai pour laisser le système respirer
                        time.sleep(0.3)
                    
                    pbar.update(1)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(extract_dataframe_from_fits, fits_file) for fits_file in fits_files]
            for future in concurrent.futures.as_completed(futures):
                df, result = future.result()
                
                if result['status'] == 'success' and df is not None:
                    all_dataframes.append(df)
                    stats['success'] += 1
                    stats['total_rows'] += len(df)
                    
                    # Écrire le batch dans un fichier séparé quand il atteint la taille définie
                    if len(all_dataframes) >= batch_size:
                        batches_written += 1
                        batch_file = batch_dir / f'batch_{batches_written:04d}.csv'
                        
                        batch_df = pd.concat(all_dataframes, ignore_index=True)
                        batch_df.to_csv(batch_file, index=False)
                        batch_files.append(batch_file)
                        
                        print(f"💾 Batch {batches_written} écrit ({len(batch_df)} rows) | Nettoyage mémoire...")
                        
                        # Libération agressive de la mémoire
                        del all_dataframes
                        del batch_df
                        all_dataframes = []
                        gc.collect()  # Force garbage collection
                        time.sleep(0.3)
                else:
                    stats['failed'] += 1
                    failed_files.append(result['filename'])
    
    # Écrire le dernier batch restant (s'il y en a un)
    if all_dataframes:
        batches_written += 1
        batch_file = batch_dir / f'batch_{batches_written:04d}.csv'
        
        print(f"\n💾 Écriture du dernier batch ({len(all_dataframes)} DataFrames)...")
        batch_df = pd.concat(all_dataframes, ignore_index=True)
        batch_df.to_csv(batch_file, index=False)
        batch_files.append(batch_file)
        
        # Libération finale de la mémoire
        del all_dataframes
        del batch_df
        gc.collect()
    
    # PHASE 2 : Fusion de tous les fichiers batch en un seul CSV
    print(f"\n{'='*70}")
    print(f"📦 PHASE 2 : FUSION DES BATCHES")
    print(f"{'='*70}")
    print(f"Nombre de fichiers batch à fusionner : {len(batch_files)}")
    print(f"Fichier de sortie final : {output_file}")
    
    if batch_files:
        # Supprimer l'ancien fichier de sortie s'il existe
        if output_path.exists():
            output_path.unlink()
        
        # Fusionner tous les fichiers batch
        first_batch = True
        with tqdm(total=len(batch_files), desc="Fusion des batch CSV → Fichier final") as pbar:
            for batch_file in batch_files:
                # Lire le batch par chunks pour économiser la mémoire
                for chunk in pd.read_csv(batch_file, chunksize=10000):
                    chunk.to_csv(
                        output_file,
                        mode='a' if not first_batch else 'w',
                        header=first_batch,
                        index=False
                    )
                    first_batch = False
                
                pbar.update(1)
                pbar.set_postfix_str(f"Fusionné {pbar.n}/{len(batch_files)} batches")
        
        # Nettoyer les fichiers batch temporaires (sauf si keep_batches=True)
        if not keep_batches:
            print(f"\n🧹 Nettoyage des fichiers temporaires...")
            for batch_file in batch_files:
                batch_file.unlink()
            
            # Supprimer le dossier temporaire s'il est vide
            try:
                batch_dir.rmdir()
                print(f"✅ Dossier temporaire supprimé : {batch_dir}")
            except:
                print(f"⚠️  Le dossier temporaire contient encore des fichiers : {batch_dir}")
        else:
            print(f"\n📦 Fichiers batch conservés dans : {batch_dir}")
            print(f"   • Nombre de fichiers : {len(batch_files)}")
        
        gc.collect()  # Dernier nettoyage mémoire
    
    # Vérifier et afficher les résultats
    if output_path.exists():
        print(f"\n✅ Fichier CSV créé: {output_file}")
        print(f"   • Taille: {output_path.stat().st_size / (1024**2):.2f} MB")
        print(f"   • Batches écrits: {batches_written}")
        print(f"   • Lignes totales: {stats['total_rows']:,}")
        
        # Compter les colonnes en lisant juste l'en-tête
        sample_df = pd.read_csv(output_file, nrows=0)
        print(f"   • Colonnes: {len(sample_df.columns)}")
        del sample_df
    else:
        print("\n❌ Aucun fichier CSV généré")
    
    # Afficher quelques fichiers échoués si nécessaire
    if failed_files:
        print(f"\n⚠️  Fichiers échoués: {len(failed_files)}")
        if len(failed_files) <= 10:
            for f in failed_files:
                print(f"   • {f}")
        else:
            for f in failed_files[:5]:
                print(f"   • {f}")
            print(f"   ... et {len(failed_files) - 5} autres")
    
    return {
        'stats': stats,
        'failed_files': failed_files[:100] if len(failed_files) > 100 else failed_files,  # Limiter à 100
        'output_file': output_file if output_path.exists() else None
    }


def get_csv_from_fits():
    # Configuration ULTRA-OPTIMISÉE pour éviter les crashes WSL
    FITS_DIR = Path("data/TESS/fits")
    OUTPUT_FILE = 'data/final/all_lightcurves.csv'
    # Configuration très conservatrice pour garantir la stabilité
    WORKERS = 3  # Nombre réduit pour stabilité maximale
    BATCH_SIZE = 100  # Batch réduit pour libération fréquente de la mémoire
    
    if not FITS_DIR.exists():
        print("❌ Dossier FITS introuvable: data/TESS/fits/")
        return
    
    # Compter les fichiers FITS
    fits_files = list(FITS_DIR.glob("*.fits"))
    
    print("=" * 70)
    print("TEST : EXTRACTION EN UN SEUL CSV (STRATÉGIE MULTI-FICHIERS)")
    print("=" * 70)
    print(f"\n📁 Dossier FITS: {FITS_DIR}")
    print(f"📊 Nombre de fichiers FITS: {len(fits_files)}")
    print(f"📄 Fichier de sortie: {OUTPUT_FILE}")
    print(f"\n⚙️  Stratégie d'optimisation:")
    print(f"   • Phase 1: Extraction FITS → Fichiers batch CSV")
    print(f"   • Phase 2: Fusion des batches → Fichier final unique")
    print(f"\n🔧 Configuration:")
    print(f"   • Workers: {WORKERS} (stabilité maximale)")
    print(f"   • Batch size: {BATCH_SIZE} fichiers/batch")
    print(f"   • Garbage collection: Activé après chaque batch")
    print(f"   • Délai entre batches: 0.3s")
    print(f"   • Nombre de batches attendus: ~{len(fits_files) // BATCH_SIZE + 1}")
    
    if len(fits_files) == 0:
        print("\n❌ Aucun fichier FITS trouvé!")
        return
    
    # Lancer le traitement
    print(f"\n⏳ Traitement en cours (optimisé pour éviter les crashes WSL)...\n")
    
    result = process_all_fits_single_csv(
        fits_dir=FITS_DIR,
        output_file=OUTPUT_FILE,
        max_workers=WORKERS,
        progress_bar=True,
        batch_size=BATCH_SIZE
    )
    
    # Afficher les résultats
    stats = result['stats']
    
    print("\n" + "=" * 70)
    print("RÉSULTATS")
    print("=" * 70)
    print(f"\n📊 Statistiques:")
    print(f"   • Fichiers FITS traités: {stats['success']} / {stats['total']}")
    print(f"   • Échecs: {stats['failed']}")
    print(f"   • Lignes totales: {stats['total_rows']:,}")
    
    # Vérifier le fichier CSV généré
    if result.get('output_file') and Path(result['output_file']).exists():
        print(f"\n✅ Fichier CSV créé: {result['output_file']}")
        
        # Charger et analyser le CSV
        df = pd.read_csv(result['output_file'])
        
        print(f"\n🔍 Analyse du CSV:")
        print(f"   • Nombre de lignes: {len(df):,}")
        print(f"   • Nombre de colonnes: {len(df.columns)}")
        print(f"   • Colonnes: {list(df.columns)}")
        
        # Vérifications
        print(f"\n✅ Vérifications:")
        print(f"   • Colonne 'time' présente: {'time' in df.columns or 'TIME' in df.columns}")
        print(f"   • Colonne 'TIC' présente: {'TIC' in df.columns}")
        print(f"   • Colonne 'SECTOR' présente: {'SECTOR' in df.columns}")
        
        if 'TIC' in df.columns:
            unique_tics = df['TIC'].nunique()
            print(f"   • Nombre de TIC uniques: {unique_tics}")
            print(f"   • TIC min: {df['TIC'].min()}")
            print(f"   • TIC max: {df['TIC'].max()}")
        
        if 'SECTOR' in df.columns:
            unique_sectors = df['SECTOR'].nunique()
            print(f"   • Nombre de SECTOR uniques: {unique_sectors}")
            print(f"   • Secteurs: {sorted(df['SECTOR'].unique())}")
        
        # Afficher un échantillon
        print(f"\n📋 Échantillon de données (3 premières lignes):")
        # Afficher quelques colonnes importantes
        cols_to_show = []
        for col in ['time', 'TIME', 'flux', 'FLUX', 'TIC', 'SECTOR']:
            if col in df.columns:
                cols_to_show.append(col)
        
        if cols_to_show:
            print(df[cols_to_show].head(3).to_string(index=False))
        else:
            print(df.head(3).to_string(index=False))
        
        # Taille du fichier
        file_size = Path(result['output_file']).stat().st_size
        print(f"\n💾 Taille du fichier: {file_size / (1024**2):.2f} MB")
        
    else:
        print("\n❌ Aucun fichier CSV généré")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    get_csv_from_fits()
