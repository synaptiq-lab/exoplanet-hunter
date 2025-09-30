from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import polars as pl
import io
import json
from datetime import datetime
import os
import logging
import math

# Import des modules ML personnalisés
from ml_pipeline import ml_pipeline
from data_utils import csv_to_polars, validate_exoplanet_data, format_prediction_results
from exoplanet_validator import exoplanet_validator

logger = logging.getLogger(__name__)

def clean_for_json(obj):
    """
    Nettoie les valeurs pour la sérialisation JSON
    Remplace NaN, inf, -inf par des valeurs JSON compatibles
    Gère les types numpy et polars
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        else:
            return float(obj)
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
        elif math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        else:
            return obj
    elif hasattr(obj, 'item'):  # Pour les types numpy/polars scalaires
        return clean_for_json(obj.item())
    else:
        return obj

# Configuration
app = FastAPI(
    title="Exoplanet Hunter API",
    description="API pour la détection d'exoplanètes utilisant l'IA",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic
class PredictionResult(BaseModel):
    classification: str
    confidence_score: float
    features_importance: Dict[str, float]
    explanation: str

class ModelStats(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    last_trained: str

class TrainingConfig(BaseModel):
    algorithm: str = "random_forest"
    test_size: float = 0.2
    random_state: int = 42
    hyperparameters: Dict[str, Any] = {}

# Initialisation du modèle ML au démarrage
# Le modèle sera chargé automatiquement lors du premier entraînement
# ou quand un modèle existant sera trouvé dans le répertoire models/

@app.get("/")
async def root():
    return {"message": "Exoplanet Hunter API - Prêt pour la détection d'exoplanètes!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/model/stats")
async def get_model_stats():
    """Récupère les statistiques du modèle actuel"""
    if ml_pipeline.is_trained():
        return ml_pipeline.get_model_stats()
    else:
        # Stats par défaut si le modèle n'est pas chargé
        return ModelStats(
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            training_samples=0,
            last_trained="Non entraîné"
        )

@app.post("/predict")
async def predict_exoplanet(file: UploadFile = File(...)):
    """
    Prédit la classification d'exoplanètes à partir d'un fichier CSV
    """
    try:
        # Vérification que le modèle est chargé
        if not ml_pipeline.is_trained():
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des labels."
            )
        
        # Lecture du fichier CSV
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Conversion en DataFrame Polars avec validation
        try:
            df = csv_to_polars(csv_content)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV: {str(e)}"
            )
        
        # Validation des données
        validation = validate_exoplanet_data(df, for_training=False)
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Données invalides: {'; '.join(validation['errors'])}"
            )
        
        # Prédictions avec le vrai modèle ML
        predictions = ml_pipeline.predict(df)
        
        # Formatage des résultats
        result = format_prediction_results(predictions, df.shape[0])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/train")
async def retrain_model(
    file: UploadFile = File(...),
    config: str = Form(...)
):
    """
    Réentraîne le modèle avec de nouvelles données
    """
    try:
        # Parse de la configuration
        training_config = TrainingConfig(**json.loads(config))
        
        # Lecture du fichier CSV
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Conversion en DataFrame Polars
        try:
            df = csv_to_polars(csv_content)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV d'entraînement: {str(e)}"
            )
        
        # Validation des données d'entraînement
        validation = validate_exoplanet_data(df, for_training=True)
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Données d'entraînement invalides: {'; '.join(validation['errors'])}"
            )
        
        # Réentraînement du modèle
        training_results = ml_pipeline.train_model(
            df,
            algorithm=training_config.algorithm,
            test_size=training_config.test_size,
            random_state=training_config.random_state,
            hyperparameters=training_config.hyperparameters
        )
        
        # Sauvegarde du nouveau modèle
        model_path = "models/exoplanet_model.pkl"
        os.makedirs("models", exist_ok=True)
        ml_pipeline.save_model(model_path)
        
        return {
            "message": "Modèle réentraîné avec succès",
            "new_stats": training_results['model_stats'],
            "training_config": training_config,
            "samples_used": training_results['samples_used'],
            "feature_importance": training_results['feature_importance']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du réentraînement: {str(e)}")

@app.get("/datasets/info")
async def get_datasets_info():
    """
    Retourne des informations sur les datasets disponibles
    """
    return {
        "available_datasets": [
            {
                "name": "Kepler",
                "description": "Données de la mission Kepler (2009-2017)",
                "samples": 9564,
                "confirmed_planets": 2662,
                "candidates": 4034,
                "false_positives": 2868
            },
            {
                "name": "K2",
                "description": "Données de la mission K2 (2014-2018)",
                "samples": 2394,
                "confirmed_planets": 479,
                "candidates": 889,
                "false_positives": 1026
            },
            {
                "name": "TESS",
                "description": "Données de la mission TESS (2018-présent)",
                "samples": 5829,
                "confirmed_planets": 375,
                "candidates": 4284,
                "false_positives": 1170
            }
        ],
        "key_features": [
            "koi_period - Période orbitale (jours)",
            "koi_duration - Durée du transit (heures)",
            "koi_depth - Profondeur du transit (ppm)",
            "koi_prad - Rayon planétaire (rayons terrestres)",
            "koi_srad - Rayon stellaire (rayons solaires)",
            "koi_stemp - Température stellaire (K)",
            "koi_smass - Masse stellaire (masses solaires)"
        ]
    }

@app.post("/analyze/single")
async def analyze_single_target(data: Dict[str, float]):
    """
    Analyse un seul objet astronomique
    """
    try:
        # Vérification que le modèle est chargé
        if not ml_pipeline.is_trained():
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des labels."
            )
        
        # Validation des champs requis
        required_fields = ['koi_period', 'koi_duration', 'koi_depth', 'koi_prad']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Champs manquants: {missing_fields}"
            )
        
        # Conversion en DataFrame Polars pour une seule ligne
        df = pl.DataFrame([data])
        
        # Prédiction
        predictions = ml_pipeline.predict(df)
        
        if predictions:
            prediction = predictions[0]
            return PredictionResult(
                classification=prediction['classification'],
                confidence_score=prediction['confidence_score'],
                features_importance=prediction['features_importance'],
                explanation=prediction['explanation']
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de la prédiction"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

# Routes pour la gestion des datasets
@app.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload et sauvegarde d'un dataset
    """
    try:
        # Lecture du fichier
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Validation du CSV
        try:
            df = csv_to_polars(csv_content)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV: {str(e)}"
            )
        
        # Validation des données
        validation = validate_exoplanet_data(df, for_training='koi_disposition' in df.columns)
        
        # Génération d'un ID unique pour le dataset
        import uuid
        dataset_id = str(uuid.uuid4())[:8]
        
        # Sauvegarde du fichier
        dataset_dir = f"data/datasets/{dataset_id}"
        os.makedirs(dataset_dir, exist_ok=True)
        
        dataset_path = f"{dataset_dir}/{file.filename}"
        with open(dataset_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Métadonnées du dataset
        metadata = {
            'id': dataset_id,
            'filename': file.filename,
            'upload_date': datetime.now().isoformat(),
            'rows': df.shape[0],
            'columns': df.shape[1],
            'has_labels': 'koi_disposition' in df.columns,
            'validation': validation,
            'path': dataset_path
        }
        
        # Sauvegarde des métadonnées
        import json
        with open(f"{dataset_dir}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'dataset_id': dataset_id,
            'message': 'Dataset uploadé avec succès',
            'metadata': metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/datasets")
async def list_datasets():
    """
    Liste tous les datasets uploadés
    """
    try:
        datasets = []
        datasets_dir = "data/datasets"
        
        if os.path.exists(datasets_dir):
            for dataset_id in os.listdir(datasets_dir):
                metadata_path = f"{datasets_dir}/{dataset_id}/metadata.json"
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    datasets.append(metadata)
        
        # Trier par date d'upload (plus récent en premier)
        datasets.sort(key=lambda x: x['upload_date'], reverse=True)
        
        return {'datasets': datasets}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des datasets: {str(e)}")

@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """
    Supprime un dataset
    """
    try:
        dataset_dir = f"data/datasets/{dataset_id}"
        
        if not os.path.exists(dataset_dir):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        import shutil
        shutil.rmtree(dataset_dir)
        
        return {'message': f'Dataset {dataset_id} supprimé avec succès'}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@app.post("/datasets/{dataset_id}/analyze")
async def analyze_dataset(dataset_id: str):
    """
    Analyse un dataset spécifique
    """
    try:
        # Vérification que le modèle est chargé
        if not ml_pipeline.is_trained():
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des labels."
            )
        
        # Chargement du dataset
        dataset_dir = f"data/datasets/{dataset_id}"
        metadata_path = f"{dataset_dir}/metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du fichier CSV
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        df = csv_to_polars(csv_content)
        
        # Prédictions
        predictions = ml_pipeline.predict(df)
        result = format_prediction_results(predictions, df.shape[0])
        
        # Sauvegarde des résultats d'analyse
        analysis_path = f"{dataset_dir}/analysis_results.json"
        analysis_data = {
            'analysis_date': datetime.now().isoformat(),
            'results': clean_for_json(result)
        }
        
        with open(analysis_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        return clean_for_json(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@app.post("/datasets/{dataset_id}/train")
async def train_on_dataset(dataset_id: str, config: str = Form(...)):
    """
    Entraîne le modèle sur un dataset spécifique
    """
    try:
        # Parse de la configuration
        training_config = TrainingConfig(**json.loads(config))
        
        # Chargement du dataset
        dataset_dir = f"data/datasets/{dataset_id}"
        metadata_path = f"{dataset_dir}/metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Vérification que le dataset a des labels
        if not metadata.get('has_labels', False):
            raise HTTPException(
                status_code=400,
                detail="Ce dataset ne contient pas de labels (colonne koi_disposition) nécessaires pour l'entraînement"
            )
        
        # Lecture du fichier CSV
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        df = csv_to_polars(csv_content)
        
        # Réentraînement
        training_results = ml_pipeline.train_model(
            df,
            algorithm=training_config.algorithm,
            test_size=training_config.test_size,
            random_state=training_config.random_state,
            hyperparameters=training_config.hyperparameters
        )
        
        # Sauvegarde du nouveau modèle
        model_path = "models/exoplanet_model.pkl"
        ml_pipeline.save_model(model_path)
        
        # Sauvegarde des résultats d'entraînement
        training_path = f"{dataset_dir}/training_results.json"
        training_data = {
            'training_date': datetime.now().isoformat(),
            'config': training_config.dict(),
            'results': clean_for_json(training_results)
        }
        
        with open(training_path, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        result = {
            "message": "Modèle entraîné avec succès sur le dataset",
            "dataset_id": dataset_id,
            "new_stats": training_results['model_stats'],
            "training_config": training_config,
            "samples_used": training_results['samples_used']
        }
        
        return clean_for_json(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'entraînement: {str(e)}")

@app.get("/datasets/{dataset_id}/explore")
async def explore_dataset(dataset_id: str):
    """
    Récupère les données détaillées d'un dataset pour exploration
    """
    try:
        dataset_dir = f"data/datasets/{dataset_id}"
        metadata_path = f"{dataset_dir}/metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du fichier CSV
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        df = csv_to_polars(csv_content)
        
        # Statistiques descriptives
        numeric_cols = [col for col in df.columns if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]]
        
        stats = {}
        for col in numeric_cols[:10]:  # Limiter à 10 colonnes pour éviter la surcharge
            col_data = df[col].drop_nulls()
            if len(col_data) > 0:
                mean_val = col_data.mean()
                std_val = col_data.std()
                min_val = col_data.min()
                max_val = col_data.max()
                
                stats[col] = {
                    'mean': float(mean_val) if mean_val is not None else None,
                    'std': float(std_val) if std_val is not None else None,
                    'min': float(min_val) if min_val is not None else None,
                    'max': float(max_val) if max_val is not None else None,
                    'null_count': df[col].null_count()
                }
            else:
                stats[col] = {
                    'mean': None,
                    'std': None,
                    'min': None,
                    'max': None,
                    'null_count': df[col].null_count()
                }
        
        # Échantillon de données (100 premières lignes)
        try:
            sample_data = df.head(100).to_pandas().to_dict('records')
            # Nettoyer les valeurs NaN/Inf dans l'échantillon
            sample_data = clean_for_json(sample_data)
        except Exception as e:
            logger.warning(f"Erreur conversion pandas pour sample_data: {e}")
            # Fallback: conversion manuelle
            sample_data = []
            for row in df.head(100).iter_rows(named=True):
                clean_row = clean_for_json(dict(row))
                sample_data.append(clean_row)
        
        # Distribution des classes si applicable
        class_distribution = {}
        if 'koi_disposition' in df.columns:
            distribution = df['koi_disposition'].value_counts().sort('koi_disposition')
            class_distribution = {
                row['koi_disposition']: row['count'] 
                for row in distribution.iter_rows(named=True)
            }
        
        result = {
            'metadata': metadata,
            'statistics': stats,
            'sample_data': sample_data,
            'class_distribution': class_distribution,
            'column_info': list(df.columns)
        }
        
        # Nettoyer les valeurs pour la sérialisation JSON
        return clean_for_json(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exploration: {str(e)}")

# ================================
# ENDPOINTS SPÉCIALISÉS VALIDATION EXOPLANÈTES
# ================================

@app.post("/validate/upload")
async def upload_for_validation(file: UploadFile = File(...)):
    """
    Upload d'un dataset pour validation d'exoplanètes CANDIDATE/FALSE POSITIVE
    """
    try:
        # Lecture du fichier
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Conversion en DataFrame
        df = csv_to_polars(csv_content)
        
        # Validation spécialisée pour les exoplanètes
        validation = exoplanet_validator.validate_dataset(df)
        
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset invalide: {'; '.join(validation['errors'])}"
            )
        
        # Génération d'un ID unique
        import uuid
        dataset_id = str(uuid.uuid4())[:8]
        
        # Sauvegarde
        dataset_dir = f"data/datasets/{dataset_id}"
        os.makedirs(dataset_dir, exist_ok=True)
        
        dataset_path = f"{dataset_dir}/{file.filename}"
        with open(dataset_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Métadonnées
        metadata = {
            'id': dataset_id,
            'filename': file.filename,
            'upload_date': datetime.now().isoformat(),
            'type': 'validation',
            'rows': df.shape[0],
            'columns': df.shape[1],
            'validation_info': validation['info'],
            'path': dataset_path
        }
        
        # Sauvegarde des métadonnées
        import json
        with open(f"{dataset_dir}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'dataset_id': dataset_id,
            'message': 'Dataset uploadé avec succès pour validation',
            'validation_info': validation['info']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.post("/validate/{dataset_id}")
async def validate_exoplanets(dataset_id: str):
    """
    Valide les planètes CANDIDATE/FALSE POSITIVE d'un dataset
    Retourne la liste des planètes qui peuvent être confirmées
    Fonctionne avec les datasets uploadés via /datasets/upload ou /validate/upload
    """
    try:
        # Vérification que le modèle est entraîné
        if not ml_pipeline.is_trained():
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des planètes CONFIRMED."
            )
        
        # Chargement du dataset
        dataset_dir = f"data/datasets/{dataset_id}"
        metadata_path = f"{dataset_dir}/metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du CSV
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        df = csv_to_polars(csv_content)
        
        # Validation du dataset pour la validation d'exoplanètes
        validation = exoplanet_validator.validate_dataset(df)
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset invalide pour la validation: {'; '.join(validation['errors'])}"
            )
        
        # Validation des exoplanètes
        results = exoplanet_validator.predict_confirmations(df)
        
        # Ajouter l'ID du dataset aux résultats
        results['dataset_id'] = dataset_id
        results['dataset_name'] = metadata.get('filename', 'Dataset')
        
        # Sauvegarde des résultats
        validation_path = f"{dataset_dir}/validation_results.json"
        validation_data = {
            'validation_date': datetime.now().isoformat(),
            'results': clean_for_json(results)
        }
        
        with open(validation_path, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        return clean_for_json(results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la validation: {str(e)}")

@app.get("/validate/{dataset_id}/planet/{planet_name}")
async def get_planet_details(dataset_id: str, planet_name: str):
    """
    Récupère les détails d'une planète spécifique
    """
    try:
        # Chargement du dataset
        dataset_dir = f"data/datasets/{dataset_id}"
        metadata_path = f"{dataset_dir}/metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du CSV
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        df = csv_to_polars(csv_content)
        
        # Récupération des détails de la planète
        details = exoplanet_validator.get_planet_details(df, planet_name)
        
        return clean_for_json(details)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


