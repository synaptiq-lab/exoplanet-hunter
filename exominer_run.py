#!/usr/bin/env python3
"""
Script ExoMiner - Lancement et analyse avec conteneur Docker
Version simplifiée pour Windows
"""

import subprocess
import os
import pandas as pd
import tempfile
from datetime import datetime

# Configuration
IMAGE_NAME = "ghcr.io/nasa/exominer:amd64"
CSV_FILE = "tics_tbl.csv"

def check_docker():
    """Vérifie que Docker est disponible"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        print(f"Docker disponible: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("ERREUR: Docker non trouvé!")
        return False

def check_image():
    """Vérifie/installe l'image ExoMiner"""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", IMAGE_NAME],
            capture_output=True, text=True
        )
        
        if not result.stdout.strip():
            print("Téléchargement de l'image ExoMiner...")
            subprocess.run(["docker", "pull", IMAGE_NAME], check=True)
        
        print("Image ExoMiner disponible")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERREUR image: {e}")
        return False

def validate_csv():
    """Valide le fichier CSV"""
    if not os.path.exists(CSV_FILE):
        print(f"ERREUR: Fichier {CSV_FILE} non trouvé!")
        return False
    
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"CSV valide: {len(df)} entrées")
        print(f"Colonnes: {list(df.columns)}")
        
        required = ['tic_id', 'sector_run']
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"ERREUR: Colonnes manquantes: {missing}")
            return False
        
        print("Échantillon:")
        print(df.head())
        return True
        
    except Exception as e:
        print(f"ERREUR CSV: {e}")
        return False

def run_exominer_container():
    """Lance ExoMiner dans un nouveau conteneur"""
    try:
        # Répertoire de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(tempfile.gettempdir(), f"exominer_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Répertoire de sortie: {output_dir}")
        
        # Chemin absolu du CSV
        csv_path = os.path.abspath(CSV_FILE)
        
        # Commande Docker pour Windows
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{csv_path}:/tics_tbl.csv:rw",
            "-v", f"{output_dir}:/outputs:rw",
            IMAGE_NAME,
            "--tic_ids_fp=/tics_tbl.csv",
            "--output_dir=/outputs",
            "--data_collection_mode=2min",
            "--num_processes=2",
            "--num_jobs=1",
            "--download_spoc_data_products=true",
            "--stellar_parameters_source=ticv8",
            "--ruwe_source=gaiadr2",
            "--exominer_model=exominer++_single"
        ]
        
        print("Lancement ExoMiner...")
        print("ATTENTION: L'analyse peut prendre 5-15 minutes!")
        print("\nCommande:")
        print(" ".join(cmd))
        
        # Exécution
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Suivi en temps réel
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(f"[ExoMiner] {line}")
                output_lines.append(line)
        
        return_code = process.wait()
        return return_code == 0, output_dir, output_lines
        
    except Exception as e:
        print(f"ERREUR exécution: {e}")
        return False, None, []

def analyze_results(output_dir):
    """Analyse les résultats"""
    if not output_dir or not os.path.exists(output_dir):
        print("Aucun résultat à analyser")
        return
    
    print(f"\nAnalyse des résultats dans {output_dir}:")
    
    # Lister les fichiers
    files = []
    for root, dirs, filenames in os.walk(output_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            files.append({
                'name': filename,
                'size_mb': round(size_mb, 2)
            })
    
    print(f"Fichiers générés ({len(files)}):")
    for file_info in files:
        print(f"  - {file_info['name']} ({file_info['size_mb']} MB)")
    
    # Chercher le catalogue
    catalog_files = [f for f in files if 'catalog' in f['name'].lower() and f['name'].endswith('.csv')]
    
    if catalog_files:
        catalog_file = catalog_files[0]
        print(f"\nCatalogue ExoMiner: {catalog_file['name']}")
        
        try:
            df = pd.read_csv(os.path.join(output_dir, catalog_file['name']))
            print(f"Objets analysés: {len(df)}")
            print(f"Colonnes: {list(df.columns)}")
            
            if len(df) > 0:
                print(f"Étoiles uniques: {df['tic_id'].nunique()}")
                
                # Scores ExoMiner
                score_cols = [col for col in df.columns if 'score' in col.lower()]
                if score_cols and pd.api.types.is_numeric_dtype(df[score_cols[0]]):
                    score_col = score_cols[0]
                    high_conf = df[df[score_col] > 0.8]
                    print(f"Candidats haute confiance (>0.8): {len(high_conf)}")
                    print(f"Score moyen: {df[score_col].mean():.3f}")
                
                print("\nAperçu des résultats:")
                print(df.head().to_string(index=False))
                
        except Exception as e:
            print(f"Erreur lecture catalogue: {e}")

def main():
    """Fonction principale"""
    print("=" * 80)
    print("EXOMINER NASA PIPELINE")
    print("=" * 80)
    
    # Vérifications
    if not check_docker():
        return False
    
    if not check_image():
        return False
    
    if not validate_csv():
        return False
    
    # Exécution
    success, output_dir, output = run_exominer_container()
    
    if not success:
        print("ERREUR: ExoMiner échoué")
        print("Dernières lignes:")
        for line in output[-10:]:
            print(f"  {line}")
        return False
    
    # Analyse des résultats
    analyze_results(output_dir)
    
    print("\n" + "=" * 80)
    print("ANALYSE EXOMINER TERMINEE AVEC SUCCES!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\nECHEC!")
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\nERREUR: {e}")
