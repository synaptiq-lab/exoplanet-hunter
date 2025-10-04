"""
Service ExoMiner pour l'intégration avec le pipeline NASA
Utilise Docker pour exécuter le conteneur ExoMiner
"""

import subprocess
import os
import tempfile
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import threading
import time

logger = logging.getLogger(__name__)

class ExoMinerService:
    """Service d'intégration avec ExoMiner de la NASA"""
    
    def __init__(self):
        self.image_name = "ghcr.io/nasa/exominer:amd64"
        self.work_dir = "/tmp/exominer_work"
        self.running_jobs = {}  # Stockage des jobs en cours
        self.ensure_work_dir()
    
    def ensure_work_dir(self):
        """Crée le répertoire de travail"""
        os.makedirs(self.work_dir, exist_ok=True)
        logger.info(f"Répertoire de travail ExoMiner: {self.work_dir}")
    
    def check_docker_and_image(self):
        """Vérifie que Docker et l'image ExoMiner sont disponibles"""
        try:
            # Vérifier Docker
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
            logger.info(f"Docker disponible: {result.stdout.strip()}")
            
            # Vérifier l'image ExoMiner
            result = subprocess.run(
                ["docker", "images", "-q", self.image_name],
                capture_output=True, text=True, check=True
            )
            
            if not result.stdout.strip():
                logger.info("Téléchargement de l'image ExoMiner...")
                subprocess.run(["docker", "pull", self.image_name], check=True)
                logger.info("Image ExoMiner téléchargée")
            else:
                logger.info("Image ExoMiner disponible")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur Docker/Image: {e}")
            return False
        except FileNotFoundError:
            logger.error("Docker non trouvé!")
            return False
    
    async def analyze_tics_csv(self, 
                              csv_content: str,
                              filename: str,
                              data_collection_mode: str = "2min",
                              num_processes: int = 2,
                              num_jobs: int = 1,
                              download_spoc_data_products: bool = True,
                              stellar_parameters_source: str = "ticv8",
                              ruwe_source: str = "gaiadr2",
                              exominer_model: str = "exominer++_single") -> Dict[str, Any]:
        """
        Analyse un fichier CSV de TIC IDs avec ExoMiner
        
        Args:
            csv_content: Contenu du fichier CSV
            filename: Nom du fichier original
            data_collection_mode: Mode de collecte de données
            num_processes: Nombre de processus parallèles
            num_jobs: Nombre de jobs
            download_spoc_data_products: Télécharger les produits SPOC DV
            stellar_parameters_source: Source des paramètres stellaires
            ruwe_source: Source des valeurs RUWE Gaia
            exominer_model: Modèle ExoMiner à utiliser
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
        """
        try:
            # Générer un ID de job unique
            job_id = f"exominer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Créer le répertoire de sortie
            output_dir = os.path.join(self.work_dir, job_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Sauvegarder le CSV avec un nom spécifique
            csv_path = os.path.join(output_dir, "tics_tbl.csv")
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            # Vérifier que le fichier a été créé correctement
            if not os.path.isfile(csv_path):
                raise ValueError(f"Le fichier CSV n'a pas été créé correctement: {csv_path}")
            
            # Vérifier le contenu du fichier comme dans exominer_run.py
            try:
                df_test = pd.read_csv(csv_path)
                logger.info(f"Fichier CSV créé et validé: {csv_path} ({os.path.getsize(csv_path)} bytes)")
                logger.info(f"Contenu CSV: {len(df_test)} lignes, colonnes: {list(df_test.columns)}")
            except Exception as e:
                logger.error(f"Erreur validation CSV: {e}")
                raise ValueError(f"Le fichier CSV créé n'est pas valide: {e}")
            
            logger.info(f"Démarrage analyse ExoMiner - Job ID: {job_id}")
            logger.info(f"Fichier CSV: {filename}")
            logger.info(f"Répertoire de sortie: {output_dir}")
            
            # Valider le CSV
            validation_result = self.validate_csv_format(csv_path)
            if not validation_result['valid']:
                raise ValueError(f"CSV invalide: {validation_result['error']}")
            
            # Marquer le job comme démarré
            self.running_jobs[job_id] = {
                'status': 'running',
                'start_time': datetime.now(),
                'output_dir': output_dir,
                'filename': filename,
                'progress': 0
            }
            
            # Exécuter ExoMiner en arrière-plan
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._run_exominer_container,
                csv_path, output_dir, job_id, {
                    'data_collection_mode': data_collection_mode,
                    'num_processes': num_processes,
                    'num_jobs': num_jobs,
                    'download_spoc_data_products': download_spoc_data_products,
                    'stellar_parameters_source': stellar_parameters_source,
                    'ruwe_source': ruwe_source,
                    'exominer_model': exominer_model
                }
            )
            
            # Mettre à jour le statut
            self.running_jobs[job_id]['status'] = 'completed' if result['success'] else 'failed'
            self.running_jobs[job_id]['end_time'] = datetime.now()
            self.running_jobs[job_id]['result'] = result
            
            return {
                'job_id': job_id,
                'success': result['success'],
                'output_directory': output_dir,
                'results': result,
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse ExoMiner: {str(e)}")
            if job_id in self.running_jobs:
                self.running_jobs[job_id]['status'] = 'failed'
                self.running_jobs[job_id]['error'] = str(e)
            raise
    
    def _run_exominer_container(self, csv_path: str, output_dir: str, job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute le conteneur ExoMiner (fonction synchrone)"""
        try:
            # Vérifier Docker et l'image ExoMiner
            if not self.check_docker_and_image():
                logger.error("Docker ou image ExoMiner non disponible")
                return {
                    'success': False,
                    'error': 'Docker ou image ExoMiner non disponible',
                    'return_code': -1
                }
            
            # Vérifier que les fichiers existent avant de construire la commande
            if not os.path.isfile(csv_path):
                logger.error(f"Fichier CSV non trouvé: {csv_path}")
                return {
                    'success': False,
                    'error': f'Fichier CSV non trouvé: {csv_path}',
                    'return_code': -1
                }
            
            if not os.path.isdir(output_dir):
                logger.error(f"Répertoire de sortie non trouvé: {output_dir}")
                return {
                    'success': False,
                    'error': f'Répertoire de sortie non trouvé: {output_dir}',
                    'return_code': -1
                }
            
            # Construire la commande Docker - utiliser la même approche que exominer_run.py qui fonctionne
            csv_abs_path = os.path.abspath(csv_path)
            output_abs_dir = os.path.abspath(output_dir)
            
            logger.info(f"CSV absolute path: {csv_abs_path}")
            logger.info(f"Output absolute dir: {output_abs_dir}")
            
            # Vérifier que le fichier existe vraiment
            if not os.path.isfile(csv_abs_path):
                logger.error(f"Fichier CSV non trouvé: {csv_abs_path}")
                return {
                    'success': False,
                    'error': f'Fichier CSV non trouvé: {csv_abs_path}',
                    'return_code': -1
                }
            
            # Utiliser la même approche que exominer_run.py qui fonctionne
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{csv_abs_path}:/tics_tbl.csv:rw",  # Monter directement le fichier comme dans exominer_run.py
                "-v", f"{output_abs_dir}:/outputs:rw",
                self.image_name,
                "--tic_ids_fp=/tics_tbl.csv",  # Chemin direct comme dans exominer_run.py
                "--output_dir=/outputs",
                f"--data_collection_mode={params['data_collection_mode']}",
                f"--num_processes={params['num_processes']}",
                f"--num_jobs={params['num_jobs']}",
                f"--download_spoc_data_products={str(params['download_spoc_data_products']).lower()}",
                f"--stellar_parameters_source={params['stellar_parameters_source']}",
                f"--ruwe_source={params['ruwe_source']}",
                f"--exominer_model={params['exominer_model']}"
            ]
            
            logger.info(f"Commande ExoMiner pour job {job_id}: {' '.join(cmd)}")
            
            # Exécution avec timeout comme dans exominer_run.py
            logger.info("Lancement ExoMiner...")
            logger.info("ATTENTION: L'analyse peut prendre 5-15 minutes!")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Suivi en temps réel et mise à jour du progrès
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    logger.info(f"[ExoMiner] {line}")
                    output_lines.append(line)
                    
                    # Mettre à jour le progrès basé sur les logs
                    if "Getting data products" in line:
                        self.running_jobs[job_id]['progress'] = min(50, self.running_jobs[job_id]['progress'] + 10)
                    elif "Finished running ExoMiner pipeline" in line:
                        self.running_jobs[job_id]['progress'] = 100
            
            return_code = process.wait()
            logger.info(f"ExoMiner terminé avec code: {return_code}")
            
            # Analyser les résultats
            results = self.analyze_exominer_output(output_dir, output_lines, return_code)
            
            return {
                'success': return_code == 0,
                'return_code': return_code,
                'output_lines': output_lines,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ExoMiner pour job {job_id}")
            return {
                'success': False,
                'error': 'Timeout - analyse trop longue',
                'return_code': -1
            }
        except Exception as e:
            logger.error(f"Erreur exécution ExoMiner job {job_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'return_code': -1
            }
    
    def validate_csv_format(self, csv_path: str) -> Dict[str, Any]:
        """Valide le format du fichier CSV"""
        try:
            df = pd.read_csv(csv_path)
            
            # Vérifier les colonnes requises
            required_columns = ['tic_id', 'sector_run']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'valid': False,
                    'error': f"Colonnes manquantes: {missing_columns}",
                    'columns': list(df.columns),
                    'row_count': len(df)
                }
            
            return {
                'valid': True,
                'columns': list(df.columns),
                'row_count': len(df),
                'sample_data': df.head(5).to_dict('records') if len(df) > 0 else []
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Erreur lecture CSV: {str(e)}",
                'columns': [],
                'row_count': 0
            }
    
    def analyze_exominer_output(self, output_dir: str, stdout_lines: list, return_code: int) -> Dict[str, Any]:
        """Analyse les résultats d'ExoMiner"""
        results = {
            'success': return_code == 0,
            'return_code': return_code,
            'files_generated': [],
            'exominer_catalog': None,
            'summary': {},
            'stdout': stdout_lines[-50:] if stdout_lines else []  # Dernières 50 lignes
        }
        
        try:
            if not os.path.exists(output_dir):
                logger.warning("Répertoire de sortie ExoMiner non trouvé")
                return results
            
            # Lister les fichiers générés
            all_files = []
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    all_files.append({
                        'name': file,
                        'path': file_path,
                        'size_bytes': file_size,
                        'size_mb': round(file_size / 1024 / 1024, 2),
                        'relative_path': os.path.relpath(file_path, output_dir)
                    })
            
            results['files_generated'] = all_files
            logger.info(f"ExoMiner généré {len(all_files)} fichiers")
            
            # Identifier le catalogue principal ExoMiner (comme dans exominer_run.py)
            catalog_files = [f for f in all_files if 'catalog' in f['name'].lower() and f['name'].endswith('.csv')]
            
            if catalog_files:
                catalog_file = catalog_files[0]
                logger.info(f"Catalogue ExoMiner: {catalog_file['name']}")
                
                try:
                    df = pd.read_csv(catalog_file['path'])
                    
                    results['exominer_catalog'] = {
                        'file_name': catalog_file['name'],
                        'file_size_mb': catalog_file['size_mb'],
                        'total_objects': len(df),
                        'columns': list(df.columns),
                        'sample_data': df.head(10).to_dict('records') if len(df) > 0 else []
                    }
                    
                    # Statistiques synthétiques (comme dans exominer_run.py)
                    if len(df) > 0:
                        stats = {
                            'total_tics_processed': len(df),
                            'total_tces_detected': len(df),
                            'unique_tic_ids': df['tic_id'].nunique() if 'tic_id' in df.columns else 'unknown'
                        }
                        
                        # Chercher scores ExoMiner (comme dans exominer_run.py)
                        score_columns = [col for col in df.columns if 'score' in col.lower()]
                        if score_columns and pd.api.types.is_numeric_dtype(df[score_columns[0]]):
                            score_col = score_columns[0]
                            high_conf = df[df[score_col] > 0.8]
                            stats.update({
                                'high_confidence_candidates': len(high_conf),
                                'avg_score': round(df[score_col].mean(), 3),
                                'max_score': round(df[score_col].max(), 3),
                                'min_score': round(df[score_col].min(), 3)
                            })
                        
                        results['summary'] = stats
                        
                        logger.info("Statistiques ExoMiner:")
                        for key, value in stats.items():
                            logger.info(f"  {key}: {value}")
                    
                except Exception as e:
                    logger.warning(f"Erreur lecture catalogue ExoMiner: {e}")
            
            # Chercher d'autres fichiers intéressants
            spoc_files = [f for f in all_files if 'spoc' in f['name'].lower()]
            log_files = [f for f in all_files if f['name'].endswith('.log')]
            
            if spoc_files:
                results['spoc_dv_reports'] = len(spoc_files)
                logger.info(f"SPOC reports: {len(spoc_files)} fichiers")
            
            if log_files:
                results['log_files'] = len(log_files)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur analyse résultats ExoMiner: {e}")
            results['error'] = str(e)
            return results
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'un job ExoMiner"""
        if job_id not in self.running_jobs:
            return None
        
        job = self.running_jobs[job_id].copy()
        
        # Calculer la durée
        if 'start_time' in job:
            if 'end_time' in job:
                duration = (job['end_time'] - job['start_time']).total_seconds()
            else:
                duration = (datetime.now() - job['start_time']).total_seconds()
            job['duration_seconds'] = round(duration, 2)
        
        return job
    
    def list_jobs(self) -> Dict[str, Any]:
        """Liste tous les jobs ExoMiner"""
        return {
            'total_jobs': len(self.running_jobs),
            'jobs': {job_id: self.get_job_status(job_id) for job_id in self.running_jobs.keys()}
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Nettoie les anciens jobs"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        jobs_to_remove = []
        for job_id, job in self.running_jobs.items():
            if job.get('start_time', datetime.now()).timestamp() < cutoff_time:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.running_jobs[job_id]
            logger.info(f"Job ExoMiner nettoyé: {job_id}")

# Instance globale du service ExoMiner
exominer_service = ExoMinerService()
