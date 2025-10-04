#!/usr/bin/env python3
"""
Script de test ExoMiner - Communication avec conteneur existant
Utilise le conteneur Docker ExoMiner déjà en cours d'exécution
"""

import subprocess
import os
import pandas as pd
import json
from datetime import datetime

# Configuration
CONTAINER_ID = "47a5850a2338b4f5759edba9a74f76749444c313d1f71ce5d94093f3d005420d"
CSV_FILE = "tics_tbl.csv"

def check_container_status():
    """Vérifie le statut du conteneur ExoMiner"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"id={CONTAINER_ID}", "--format", "{{.Status}}"],
            capture_output=True, text=True, check=True
        )
        status = result.stdout.strip()
        if status:
            print(f"Conteneur ExoMiner: {status}")
            return True
        else:
            print("Conteneur ExoMiner non trouvé ou arrêté")
            return False
    except subprocess.CalledProcessError:
        print("Erreur lors de la vérification du conteneur")
        return False

def validate_csv():
    """Valide le fichier CSV d'entrée"""
    if not os.path.exists(CSV_FILE):
        print(f"ERREUR: Fichier {CSV_FILE} non trouvé!")
        return False
    
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"CSV valide: {len(df)} entrées")
        print(f"Colonnes: {list(df.columns)}")
        
        # Vérifier les colonnes requises
        required = ['tic_id', 'sector_run']
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"ERREUR: Colonnes manquantes: {missing}")
            return False
        
        print("Échantillon des données:")
        print(df.head())
        return True
        
    except Exception as e:
        print(f"ERREUR validation CSV: {e}")
        return False

def copy_csv_to_container():
    """Copie le fichier CSV dans le conteneur"""
    try:
        print("Copie du fichier CSV dans le conteneur...")
        subprocess.run([
            "docker", "cp", CSV_FILE, f"{CONTAINER_ID}:/tics_tbl.csv"
        ], check=True)
        print("Fichier CSV copié avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERREUR copie CSV: {e}")
        return False

def run_exominer_analysis():
    """Exécute l'analyse ExoMiner dans le conteneur"""
    try:
        print("Lancement de l'analyse ExoMiner...")
        print("ATTENTION: L'analyse peut prendre 5-15 minutes!")
        
        # Commande ExoMiner dans le conteneur
        cmd = [
            "docker", "exec", CONTAINER_ID,
            "python", "-m", "exominer.run_pipeline",
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
        
        print("Commande ExoMiner:")
        print(" ".join(cmd))
        
        # Exécution avec suivi en temps réel
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Afficher la sortie en temps réel
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
        return return_code == 0, output_lines
        
    except Exception as e:
        print(f"ERREUR exécution ExoMiner: {e}")
        return False, []

def copy_results_from_container():
    """Copie les résultats du conteneur vers l'hôte"""
    try:
        # Créer un répertoire de sortie local
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"exominer_results_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Copie des résultats vers {output_dir}...")
        
        # Copier tout le répertoire outputs du conteneur
        subprocess.run([
            "docker", "cp", f"{CONTAINER_ID}:/outputs/.", output_dir
        ], check=True)
        
        print(f"Résultats copiés dans {output_dir}")
        return output_dir
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR copie résultats: {e}")
        return None

def analyze_results(output_dir):
    """Analyse les résultats générés"""
    if not output_dir or not os.path.exists(output_dir):
        print("Aucun répertoire de résultats à analyser")
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
                'path': filepath,
                'size_mb': round(size_mb, 2)
            })
    
    print(f"Fichiers générés ({len(files)}):")
    for file_info in files:
        print(f"  - {file_info['name']} ({file_info['size_mb']} MB)")
    
    # Chercher le catalogue principal
    catalog_files = [f for f in files if 'catalog' in f['name'].lower() and f['name'].endswith('.csv')]
    
    if catalog_files:
        catalog_file = catalog_files[0]
        print(f"\nCatalogue ExoMiner: {catalog_file['name']}")
        
        try:
            df = pd.read_csv(catalog_file['path'])
            print(f"Objets analysés: {len(df)}")
            print(f"Colonnes: {list(df.columns)}")
            
            if len(df) > 0:
                print(f"Étoiles uniques: {df['tic_id'].nunique()}")
                
                # Chercher les scores
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
    print("TEST EXOMINER - CONTENEUR EXISTANT")
    print("=" * 80)
    print(f"Conteneur ID: {CONTAINER_ID}")
    print(f"Fichier CSV: {CSV_FILE}")
    print("=" * 80)
    
    # 1. Vérifier le conteneur
    if not check_container_status():
        print("ERREUR: Conteneur ExoMiner non disponible")
        return False
    
    # 2. Valider le CSV
    if not validate_csv():
        print("ERREUR: Validation CSV échouée")
        return False
    
    # 3. Copier le CSV dans le conteneur
    if not copy_csv_to_container():
        print("ERREUR: Copie CSV échouée")
        return False
    
    # 4. Exécuter l'analyse
    success, output = run_exominer_analysis()
    
    if not success:
        print("ERREUR: Analyse ExoMiner échouée")
        print("Dernières lignes de sortie:")
        for line in output[-10:]:
            print(f"  {line}")
        return False
    
    # 5. Copier les résultats
    output_dir = copy_results_from_container()
    
    # 6. Analyser les résultats
    analyze_results(output_dir)
    
    print("\n" + "=" * 80)
    print("TEST EXOMINER TERMINE AVEC SUCCES!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\nTEST ECHOUÉ!")
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
    except Exception as e:
        print(f"\nERREUR FATALE: {e}")
