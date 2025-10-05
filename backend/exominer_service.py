"""
Service ExoMiner - Intégration avec l'API Backend
Gère le lancement et l'analyse des résultats ExoMiner via Docker
"""

import subprocess
import os
import pandas as pd
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
import uuid
import json
import shutil

logger = logging.getLogger(__name__)

# Import de la fonction helper pour parser les résultats ExoMiner
try:
    from exominer_helper import build_results_table
except ImportError:
    logger.warning("exominer_helper non disponible, parsing des résultats limité")
    build_results_table = None

# Configuration
IMAGE_NAME = "ghcr.io/nasa/exominer:amd64"
EXOMINER_WORK_DIR = "exominer_work"

class ExoMinerService:
    """Service pour gérer les analyses ExoMiner"""
    
    def __init__(self, work_dir: str = EXOMINER_WORK_DIR):
        """
        Initialise le service ExoMiner
        
        Args:
            work_dir: Répertoire de travail pour les fichiers ExoMiner
        """
        self.work_dir = work_dir
        self.inputs_dir = os.path.join(work_dir, "inputs")
        self.outputs_dir = os.path.join(work_dir, "outputs")
        self.results_dir = os.path.join(work_dir, "results")
        
        # Chemin sur l'hôte pour les volumes Docker (depuis variable d'environnement)
        # Si on est dans un conteneur Docker, on a besoin du chemin de l'hôte
        self.host_work_dir = os.environ.get('HOST_EXOMINER_PATH', os.path.abspath(work_dir))
        logger.info(f"Chemin conteneur: {self.work_dir}")
        logger.info(f"Chemin hôte: {self.host_work_dir}")
        
        # Créer les répertoires s'ils n'existent pas
        for directory in [self.work_dir, self.inputs_dir, self.outputs_dir, self.results_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info(f"ExoMinerService initialisé - Répertoire: {self.work_dir}")
    
    def check_docker(self) -> Tuple[bool, str]:
        """
        Vérifie que Docker est disponible
        
        Returns:
            Tuple (disponible, message)
        """
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            version = result.stdout.strip()
            logger.info(f"Docker disponible: {version}")
            return True, version
        except FileNotFoundError:
            error_msg = "Docker n'est pas installé ou n'est pas dans le PATH"
            logger.error(error_msg)
            return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = "Timeout lors de la vérification de Docker"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur lors de la vérification de Docker: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_image(self) -> Tuple[bool, str]:
        """
        Vérifie que l'image ExoMiner est disponible
        
        Returns:
            Tuple (disponible, message)
        """
        try:
            result = subprocess.run(
                ["docker", "images", "-q", IMAGE_NAME],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                logger.info("Image ExoMiner non présente, téléchargement nécessaire")
                return False, "Image ExoMiner non présente, téléchargement nécessaire"
            
            logger.info("Image ExoMiner disponible")
            return True, "Image ExoMiner disponible"
            
        except Exception as e:
            error_msg = f"Erreur lors de la vérification de l'image: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def pull_image(self) -> Tuple[bool, str]:
        """
        Télécharge l'image ExoMiner
        
        Returns:
            Tuple (succès, message)
        """
        try:
            logger.info("Téléchargement de l'image ExoMiner...")
            result = subprocess.run(
                ["docker", "pull", IMAGE_NAME],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            
            if result.returncode == 0:
                logger.info("Image ExoMiner téléchargée avec succès")
                return True, "Image téléchargée avec succès"
            else:
                error_msg = f"Échec du téléchargement: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Timeout lors du téléchargement de l'image (>10 minutes)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur lors du téléchargement: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def validate_tics_csv(self, csv_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Valide le fichier CSV des TIC IDs
        
        Args:
            csv_path: Chemin vers le fichier CSV
            
        Returns:
            Tuple (valide, message, informations)
        """
        try:
            if not os.path.exists(csv_path):
                return False, f"Fichier {csv_path} non trouvé", None
            
            df = pd.read_csv(csv_path)
            
            # Vérifier les colonnes requises
            required = ['tic_id', 'sector_run']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                return False, f"Colonnes manquantes: {missing}", None
            
            # Informations
            info = {
                'total_tics': len(df),
                'columns': list(df.columns),
                'tic_ids': df['tic_id'].tolist()[:10],  # Premiers 10 TIC IDs
                'sectors': df['sector_run'].unique().tolist()
            }
            
            logger.info(f"CSV validé: {len(df)} TIC IDs")
            return True, f"CSV valide: {len(df)} TIC IDs", info
            
        except Exception as e:
            error_msg = f"Erreur lors de la validation du CSV: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def create_analysis(self, csv_content: str, filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        Crée une nouvelle analyse ExoMiner
        
        Args:
            csv_content: Contenu du fichier CSV
            filename: Nom original du fichier
            
        Returns:
            Tuple (succès, message, analysis_id)
        """
        try:
            # Générer un ID unique pour l'analyse
            analysis_id = f"exominer_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Créer le répertoire pour cette analyse
            analysis_dir = os.path.join(self.outputs_dir, analysis_id)
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Sauvegarder le fichier CSV d'entrée
            input_csv_path = os.path.join(self.inputs_dir, f"{analysis_id}_tics.csv")
            with open(input_csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            # Valider le CSV
            is_valid, message, info = self.validate_tics_csv(input_csv_path)
            if not is_valid:
                return False, message, None
            
            # Créer les métadonnées de l'analyse
            metadata = {
                'analysis_id': analysis_id,
                'filename': filename,
                'created_at': datetime.now().isoformat(),
                'status': 'created',
                'input_csv': input_csv_path,
                'output_dir': analysis_dir,
                'info': info
            }
            
            # Sauvegarder les métadonnées
            metadata_path = os.path.join(self.results_dir, f"{analysis_id}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Analyse créée: {analysis_id}")
            return True, f"Analyse créée avec succès", analysis_id
            
        except Exception as e:
            error_msg = f"Erreur lors de la création de l'analyse: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def run_analysis(
        self,
        analysis_id: str,
        data_collection_mode: str = "2min",
        num_processes: int = 2,
        num_jobs: int = 1,
        model: str = "exominer++_single",
        download_spoc_data_products: bool = True,
        stellar_parameters_source: str = "ticv8",
        ruwe_source: str = "gaiadr2"
    ) -> Tuple[bool, str, List[str]]:
        """
        Lance l'analyse ExoMiner dans un conteneur Docker
        
        Args:
            analysis_id: ID de l'analyse
            data_collection_mode: Mode de collecte (2min, 20sec, fast, FFI, etc.)
            num_processes: Nombre de processus parallèles
            num_jobs: Nombre de jobs
            model: Modèle ExoMiner à utiliser
            download_spoc_data_products: Télécharger les produits SPOC
            stellar_parameters_source: Source des paramètres stellaires
            ruwe_source: Source RUWE
            
        Returns:
            Tuple (succès, message, logs)
        """
        try:
            # Charger les métadonnées
            metadata_path = os.path.join(self.results_dir, f"{analysis_id}_metadata.json")
            if not os.path.exists(metadata_path):
                return False, f"Analyse {analysis_id} non trouvée", []
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Mettre à jour le statut
            metadata['status'] = 'running'
            metadata['started_at'] = datetime.now().isoformat()
            metadata['progress'] = 0
            metadata['params'] = {
                'data_collection_mode': data_collection_mode,
                'num_processes': num_processes,
                'num_jobs': num_jobs,
                'model': model
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Chemins dans le conteneur backend
            input_csv = metadata['input_csv']
            output_dir = metadata['output_dir']
            
            # Convertir les chemins du conteneur en chemins de l'hôte
            # Le backend tourne dans /app, mais ExoMiner a besoin du chemin sur l'hôte
            input_csv_rel = os.path.relpath(input_csv, self.work_dir)
            output_dir_rel = os.path.relpath(output_dir, self.work_dir)
            
            # Chemins sur l'hôte (pour les volumes Docker)
            host_input_csv = os.path.join(self.host_work_dir, input_csv_rel)
            host_output_dir = os.path.join(self.host_work_dir, output_dir_rel)
            
            # Normaliser les chemins pour Windows (remplacer \ par /)
            if os.name == 'nt':
                host_input_csv = host_input_csv.replace('\\', '/')
                host_output_dir = host_output_dir.replace('\\', '/')
            
            logger.info(f"Chemin input (conteneur): {input_csv}")
            logger.info(f"Chemin input (hôte): {host_input_csv}")
            logger.info(f"Chemin output (conteneur): {output_dir}")
            logger.info(f"Chemin output (hôte): {host_output_dir}")
            
            # Commande Docker avec les chemins de l'hôte
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{host_input_csv}:/tics_tbl.csv:rw",
                "-v", f"{host_output_dir}:/outputs:rw",
                IMAGE_NAME,
                "--tic_ids_fp=/tics_tbl.csv",
                "--output_dir=/outputs",
                f"--data_collection_mode={data_collection_mode}",
                f"--num_processes={num_processes}",
                f"--num_jobs={num_jobs}",
                f"--download_spoc_data_products={'true' if download_spoc_data_products else 'false'}",
                f"--stellar_parameters_source={stellar_parameters_source}",
                f"--ruwe_source={ruwe_source}",
                f"--exominer_model={model}"
            ]
            
            logger.info(f"Lancement ExoMiner: {analysis_id}")
            logger.info(f"Commande: {' '.join(cmd)}")
            
            # Exécution avec logs et progression
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Capturer les logs et estimer la progression
            output_lines = []
            progress = 0
            total_tics = metadata.get('info', {}).get('total_tics', 1)
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    logger.info(f"[ExoMiner] {line}")
                    
                    # Estimation de la progression basée sur les logs
                    if 'Processing TIC' in line or 'Analyzing' in line:
                        progress = min(progress + (80 / total_tics), 80)
                    elif 'Generating catalog' in line or 'Writing results' in line:
                        progress = 90
                    
                    # Mettre à jour la progression toutes les 10 lignes
                    if len(output_lines) % 10 == 0:
                        metadata['progress'] = int(progress)
                        with open(metadata_path, 'w') as f:
                            json.dump(metadata, f, indent=2)
            
            return_code = process.wait()
            
            # Calculer la durée
            started_at = datetime.fromisoformat(metadata['started_at'])
            duration_seconds = (datetime.now() - started_at).total_seconds()
            
            # Mettre à jour les métadonnées
            metadata['status'] = 'completed' if return_code == 0 else 'failed'
            metadata['completed_at'] = datetime.now().isoformat()
            metadata['duration_seconds'] = duration_seconds
            metadata['return_code'] = return_code
            metadata['progress'] = 100 if return_code == 0 else progress
            metadata['logs'] = output_lines[-50:]  # Garder les 50 dernières lignes
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            if return_code == 0:
                logger.info(f"Analyse terminée avec succès: {analysis_id}")
                return True, "Analyse terminée avec succès", output_lines
            else:
                logger.error(f"Analyse échouée: {analysis_id} (code: {return_code})")
                return False, f"Analyse échouée (code: {return_code})", output_lines
            
        except Exception as e:
            error_msg = f"Erreur lors de l'exécution: {str(e)}"
            logger.error(error_msg)
            
            # Mettre à jour le statut en erreur
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                metadata['status'] = 'failed'
                metadata['error'] = error_msg
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except:
                pass
            
            return False, error_msg, []
    
    def get_analysis_results(self, analysis_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Récupère les résultats d'une analyse avec format frontend
        
        Args:
            analysis_id: ID de l'analyse
            
        Returns:
            Tuple (succès, message, résultats)
        """
        try:
            # Charger les métadonnées
            metadata_path = os.path.join(self.results_dir, f"{analysis_id}_metadata.json")
            if not os.path.exists(metadata_path):
                return False, f"Analyse {analysis_id} non trouvée", None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Vérifier le statut
            if metadata['status'] not in ['completed', 'analyzing']:
                return False, f"Analyse en statut: {metadata['status']}", metadata
            
            # Lister les fichiers de sortie
            output_dir = metadata['output_dir']
            files = []
            
            if os.path.exists(output_dir):
                for root, dirs, filenames in os.walk(output_dir):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        size_mb = os.path.getsize(filepath) / 1024 / 1024
                        files.append({
                            'name': filename,
                            'path': filepath,
                            'size_mb': round(size_mb, 2)
                        })
            
            # Parser predictions_outputs.csv avec build_results_table
            predictions_data = None
            predictions_file = next((f for f in files if f['name'] == 'predictions_outputs.csv'), None)
            
            if predictions_file and build_results_table:
                try:
                    logger.info(f"Parsing predictions_outputs.csv: {predictions_file['path']}")
                    results_df = build_results_table(predictions_file['path'])
                    
                    # Convertir en dictionnaire pour le frontend
                    predictions_data = {
                        'confirmed': results_df.filter(results_df['result'] == 'Confirmed').to_dicts(),
                        'candidates': results_df.filter(results_df['result'] == 'Candidate').to_dicts(),
                        'false_positives': results_df.filter(results_df['result'] == 'False Positive').to_dicts(),
                        'total': len(results_df),
                        'confirmed_count': len(results_df.filter(results_df['result'] == 'Confirmed')),
                        'candidates_count': len(results_df.filter(results_df['result'] == 'Candidate')),
                        'false_positives_count': len(results_df.filter(results_df['result'] == 'False Positive'))
                    }
                    
                    logger.info(f"✅ Résultats parsés: {predictions_data['confirmed_count']} confirmées, "
                              f"{predictions_data['candidates_count']} candidates, "
                              f"{predictions_data['false_positives_count']} faux positifs")
                except Exception as e:
                    logger.error(f"Erreur parsing predictions_outputs.csv: {e}")
            
            # Chercher le catalogue de résultats (pour info supplémentaire)
            catalog_data = None
            summary = {
                'total_tics_processed': metadata.get('info', {}).get('total_tics', 0),
                'high_confidence_candidates': predictions_data['confirmed_count'] if predictions_data else 0,
                'avg_score': None
            }
            
            if predictions_data:
                # Calculer le score moyen
                all_scores = ([p['score'] for p in predictions_data['confirmed']] + 
                             [p['score'] for p in predictions_data['candidates']] + 
                             [p['score'] for p in predictions_data['false_positives']])
                summary['avg_score'] = sum(all_scores) / len(all_scores) if all_scores else None
            
            catalog_files = [f for f in files if 'catalog' in f['name'].lower() and f['name'].endswith('.csv')]
            
            if catalog_files:
                catalog_file = catalog_files[0]
                try:
                    df = pd.read_csv(catalog_file['path'])
                    
                    # Extraire les informations principales
                    catalog_data = {
                        'total_objects': len(df),
                        'unique_stars': df['tic_id'].nunique() if 'tic_id' in df.columns else 0,
                        'columns': list(df.columns),
                        'sample_data': df.head(20).to_dict('records')
                    }
                    
                    # Scores ExoMiner si disponibles
                    score_cols = [col for col in df.columns if 'score' in col.lower()]
                    if score_cols:
                        score_col = score_cols[0]
                        if pd.api.types.is_numeric_dtype(df[score_col]):
                            high_conf = df[df[score_col] > 0.8]
                            catalog_data['high_confidence_candidates'] = len(high_conf)
                            catalog_data['average_score'] = float(df[score_col].mean())
                    
                except Exception as e:
                    logger.warning(f"Erreur lecture catalogue: {e}")
            
            # Format attendu par le frontend
            results = {
                'job_id': analysis_id,
                'status': metadata['status'],
                'filename': metadata['filename'],
                'created_at': metadata['created_at'],
                'started_at': metadata.get('started_at'),
                'completed_at': metadata.get('completed_at'),
                'duration_seconds': metadata.get('duration_seconds', 0),
                'progress': metadata.get('progress', 100),
                'results': {
                    'summary': summary,
                    'predictions': predictions_data,  # Données parsées avec build_results_table
                    'exominer_catalog': catalog_data,
                    'files': files,
                    'total_files': len(files)
                }
            }
            
            return True, "Résultats récupérés", results
            
        except Exception as e:
            error_msg = f"Erreur lors de la récupération des résultats: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def get_job_info(self, analysis_id: str) -> Optional[Dict]:
        """
        Récupère les informations basiques d'un job pour la liste
        
        Args:
            analysis_id: ID de l'analyse
            
        Returns:
            Dictionnaire avec les informations du job ou None
        """
        try:
            metadata_path = os.path.join(self.results_dir, f"{analysis_id}_metadata.json")
            if not os.path.exists(metadata_path):
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Calculer la durée
            duration = metadata.get('duration_seconds', 0)
            if metadata['status'] == 'running' and metadata.get('started_at'):
                try:
                    started = datetime.fromisoformat(metadata['started_at'])
                    duration = (datetime.now() - started).total_seconds()
                except:
                    pass
            
            return {
                'job_id': analysis_id,
                'filename': metadata['filename'],
                'status': metadata['status'],
                'created_at': metadata['created_at'],
                'started_at': metadata.get('started_at'),
                'completed_at': metadata.get('completed_at'),
                'duration_seconds': duration,
                'progress': metadata.get('progress', 0),
                'info': metadata.get('info', {})
            }
        except Exception as e:
            logger.error(f"Erreur get_job_info {analysis_id}: {e}")
            return None
    
    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les analyses ExoMiner
        
        Returns:
            Liste des analyses avec leurs métadonnées
        """
        try:
            analyses = []
            
            if os.path.exists(self.results_dir):
                for filename in os.listdir(self.results_dir):
                    if filename.endswith('_metadata.json'):
                        metadata_path = os.path.join(self.results_dir, filename)
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            analyses.append(metadata)
                        except Exception as e:
                            logger.warning(f"Erreur lecture metadata {filename}: {e}")
            
            # Trier par date de création (plus récent en premier)
            analyses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return analyses
            
        except Exception as e:
            logger.error(f"Erreur liste analyses: {e}")
            return []
    
    def delete_analysis(self, analysis_id: str) -> Tuple[bool, str]:
        """
        Supprime une analyse et ses fichiers
        
        Args:
            analysis_id: ID de l'analyse
            
        Returns:
            Tuple (succès, message)
        """
        try:
            # Métadonnées
            metadata_path = os.path.join(self.results_dir, f"{analysis_id}_metadata.json")
            if not os.path.exists(metadata_path):
                return False, f"Analyse {analysis_id} non trouvée"
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Supprimer les fichiers
            files_deleted = []
            
            # Input CSV
            if os.path.exists(metadata['input_csv']):
                os.remove(metadata['input_csv'])
                files_deleted.append('input_csv')
            
            # Output directory
            if os.path.exists(metadata['output_dir']):
                shutil.rmtree(metadata['output_dir'])
                files_deleted.append('output_dir')
            
            # Metadata
            os.remove(metadata_path)
            files_deleted.append('metadata')
            
            logger.info(f"Analyse supprimée: {analysis_id}")
            return True, f"Analyse supprimée: {', '.join(files_deleted)}"
            
        except Exception as e:
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Instance globale
exominer_service = ExoMinerService()
