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
import uuid

# Import des modules ML personnalisés
from ml_pipeline import ml_pipeline
from data_utils import csv_to_polars, validate_exoplanet_data, format_prediction_results
from exoplanet_validator import exoplanet_validator
from column_mapper import column_mapper
from exominer_service import exominer_service

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
    if ml_pipeline.trained:
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
        if not ml_pipeline.trained:
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des labels."
            )
        
        # Lecture du fichier CSV
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Conversion en DataFrame Polars avec validation
        try:
            df, mapping_info = csv_to_polars(csv_content, auto_map=True)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV: {str(e)}"
            )
        
        # Validation des données
        validation = validate_exoplanet_data(df, for_training=False, mapping_info=mapping_info)
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
            df, mapping_info = csv_to_polars(csv_content, auto_map=True)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV d'entraînement: {str(e)}"
            )
        
        # Validation des données d'entraînement
        validation = validate_exoplanet_data(df, for_training=True, mapping_info=mapping_info)
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
        if not ml_pipeline.trained:
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
    Upload et validation d'un dataset (Kepler, TESS ou K2).
    Conserve TOUTES les colonnes originales.
    """
    try:
        # Lecture du fichier
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Lecture du CSV avec Polars (SANS mapping)
        try:
            df = csv_to_polars(csv_content, auto_map=False)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erreur lors de la lecture du CSV: {str(e)}"
            )
        
        # Validation et détection du format
        df_processed, validation_info = column_mapper.process_dataframe(df)
        
        if not validation_info['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset invalide: {', '.join(validation_info['errors'])}"
            )
        
        # Génération d'un ID unique
        import uuid
        dataset_id = str(uuid.uuid4())[:8]
        
        # Sauvegarde du dataset (avec TOUTES les colonnes originales)
        dataset_path = f"data/{dataset_id}.csv"
        df_processed.write_csv(dataset_path)
        
        # Métadonnées
        metadata = {
            'id': dataset_id,
            'filename': file.filename,
            'upload_date': datetime.now().isoformat(),
            'format': validation_info['format'],
            'format_name': validation_info['format_name'],
            'rows': validation_info['total_rows'],
            'columns': validation_info['total_columns'],
            'has_labels': validation_info['has_labels'],
            'label_column': validation_info['label_column'],
            'label_distribution': validation_info['label_distribution'],
            'planet_name_column': validation_info['planet_name_column'],
            'numeric_columns': validation_info['numeric_columns'],
            'documentation': validation_info['documentation'],
            'expected_labels': validation_info['expected_labels'],
            'path': dataset_path
        }
        
        # Sauvegarde des métadonnées
        metadata_path = f"data/{dataset_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(clean_for_json(metadata), f, indent=2)
        
        logger.info(f"Dataset uploadé: {dataset_id} ({validation_info['format_name']})")
        
        return {
            'dataset_id': dataset_id,
            'message': f"Dataset {validation_info['format_name']} uploadé avec succès",
            'metadata': clean_for_json(metadata)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.get("/datasets")
async def list_datasets():
    """
    Liste tous les datasets uploadés
    """
    try:
        datasets = []
        data_dir = "data"
        
        if os.path.exists(data_dir):
            # Lister tous les fichiers *_metadata.json
            for filename in os.listdir(data_dir):
                if filename.endswith('_metadata.json'):
                    metadata_path = os.path.join(data_dir, filename)
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        datasets.append(metadata)
                    except Exception as e:
                        logger.warning(f"Erreur lecture metadata {filename}: {e}")
                        continue
        
        # Trier par date d'upload (plus récent en premier)
        datasets.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        return {'datasets': datasets}
        
    except Exception as e:
        logger.error(f"Erreur liste datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des datasets: {str(e)}")

@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """
    Supprime un dataset
    """
    try:
        # Supprimer le fichier CSV
        csv_path = f"data/{dataset_id}.csv"
        metadata_path = f"data/{dataset_id}_metadata.json"
        training_path = f"data/{dataset_id}_training.json"
        
        files_deleted = []
        
        if os.path.exists(csv_path):
            os.remove(csv_path)
            files_deleted.append("CSV")
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            files_deleted.append("metadata")
        
        if os.path.exists(training_path):
            os.remove(training_path)
            files_deleted.append("training")
        
        if not files_deleted:
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        logger.info(f"Dataset {dataset_id} supprimé: {', '.join(files_deleted)}")
        
        return {'message': f'Dataset {dataset_id} supprimé avec succès'}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@app.post("/datasets/{dataset_id}/analyze")
async def analyze_dataset(dataset_id: str):
    """
    Analyse un dataset avec le modèle entraîné
    """
    try:
        # Vérification que le modèle est entraîné
        if not ml_pipeline.trained:
            raise HTTPException(
                status_code=503,
                detail="Aucun modèle entraîné disponible. Veuillez d'abord entraîner un modèle sur un dataset avec des labels."
            )
        
        # Chargement des métadonnées
        metadata_path = f"data/{dataset_id}_metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du fichier CSV
        df = pl.read_csv(metadata['path'])
        
        logger.info(f"Analyse du dataset {dataset_id} - {df.shape[0]} objets")
        
        # Prédictions
        predictions = ml_pipeline.predict(df)
        
        # Organiser les résultats par classe prédite
        results_by_class = {}
        for pred in predictions:
            predicted_label = pred['predicted_label']
            if predicted_label not in results_by_class:
                results_by_class[predicted_label] = []
            results_by_class[predicted_label].append(pred)
        
        result = {
            'dataset_id': dataset_id,
            'total_analyzed': len(predictions),
            'predictions_by_class': {label: len(preds) for label, preds in results_by_class.items()},
            'predictions': predictions[:100],  # Limiter à 100 pour la performance
            'all_predictions_count': len(predictions)
        }
        
        # Sauvegarde des résultats d'analyse
        analysis_path = f"data/{dataset_id}_analysis.json"
        analysis_data = {
            'analysis_date': datetime.now().isoformat(),
            'dataset_id': dataset_id,
            'results': result
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
    Entraîne le modèle sur un dataset spécifique (Kepler, TESS ou K2).
    Utilise automatiquement TOUTES les colonnes numériques du dataset.
    """
    try:
        # Parse de la configuration
        training_config = TrainingConfig(**json.loads(config))
        
        # Chargement des métadonnées
        metadata_path = f"data/{dataset_id}_metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Vérification que le dataset a des labels
        if not metadata.get('has_labels', False):
            raise HTTPException(
                status_code=400,
                detail=f"Ce dataset ne contient pas de colonne de label ({metadata.get('label_column', 'disposition')}) nécessaire pour l'entraînement"
            )
        
        # Chargement du dataset
        df = pl.read_csv(metadata['path'])
        
        logger.info(f"Entraînement sur {metadata['format_name']} - {df.shape[0]} lignes, {df.shape[1]} colonnes")
        logger.info(f"Colonne de label: {metadata['label_column']}")
        
        # Entraînement avec le nouveau pipeline
        training_results = ml_pipeline.train_model(
            df,
            label_column=metadata['label_column'],
            planet_name_column=metadata['planet_name_column'],
            format_type=metadata['format'],
            test_size=training_config.test_size,
            random_state=training_config.random_state,
            hyperparameters=training_config.hyperparameters
        )
        
        # Sauvegarde du modèle
        ml_pipeline.save_model("models")
        
        # Sauvegarde des résultats d'entraînement
        training_path = f"data/{dataset_id}_training.json"
        training_data = {
            'training_date': datetime.now().isoformat(),
            'dataset_id': dataset_id,
            'format': metadata['format'],
            'config': training_config.dict(),
            'results': training_results
        }
        
        with open(training_path, 'w') as f:
            json.dump(clean_for_json(training_data), f, indent=2)
        
        logger.info(f"Modèle entraîné - Accuracy: {training_results['accuracy']:.4f}")
        
        result = {
            "message": f"Modèle entraîné avec succès sur {metadata['format_name']}",
            "dataset_id": dataset_id,
            "format": metadata['format'],
            "accuracy": training_results['accuracy'],
            "n_features": training_results['n_features'],
            "n_classes": training_results['n_classes'],
            "label_names": training_results['label_names'],
            "top_features": list(training_results['feature_importance'].keys())[:10],
            "training_config": training_config.dict()
        }
        
        return clean_for_json(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur entraînement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'entraînement: {str(e)}")

@app.get("/datasets/{dataset_id}/explore")
async def explore_dataset(dataset_id: str):
    """
    Récupère les données détaillées d'un dataset pour exploration
    """
    try:
        metadata_path = f"data/{dataset_id}_metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du fichier CSV
        df = pl.read_csv(metadata['path'])
        
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
        
        # Conversion en DataFrame avec mapping automatique
        df, mapping_info = csv_to_polars(csv_content, auto_map=True)
        
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
        # Chargement du dataset
        metadata_path = f"data/{dataset_id}_metadata.json"
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lecture du CSV
        df = pl.read_csv(metadata['path'])
        
        # Charger le modèle correspondant au format du dataset
        dataset_format = metadata.get('format', 'unknown')
        logger.info(f"Validation du dataset {dataset_id} (format: {dataset_format}) - {df.shape[0]} objets")
        
        # Essayer de charger le modèle pour ce format
        model_loaded = ml_pipeline.load_model(format_type=dataset_format)
        if not model_loaded:
            raise HTTPException(
                status_code=503,
                detail=f"Aucun modèle entraîné pour le format {dataset_format}. Veuillez d'abord entraîner un modèle sur un dataset {dataset_format}."
            )
        
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
        validation_path = f"data/{dataset_id}_validation.json"
        validation_data = {
            'validation_date': datetime.now().isoformat(),
            'results': clean_for_json(results)
        }
        
        with open(validation_path, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        logger.info(f"Validation terminée - {results['analysis_summary']['confirmed_count']} planètes confirmables")
        
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
        
        df, mapping_info = csv_to_polars(csv_content, auto_map=True)
        
        # Récupération des détails de la planète
        details = exoplanet_validator.get_planet_details(df, planet_name)
        
        return clean_for_json(details)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")

# ================================
# GESTION DES MODÈLES LOCALSTORAGE
# ================================

@app.get("/models/localStorage/list")
async def list_localStorage_models():
    """
    Liste les modèles disponibles sur le serveur pour download localStorage
    """
    try:
        models_dir = "models"
        available_models = []
        
        if os.path.exists(models_dir):
            # Chercher les fichiers de modèles JSON
            for filename in os.listdir(models_dir):
                if filename.startswith('exoplanet_model_') and filename.endswith('.json'):
                    # Extraire le format du nom de fichier
                    format_type = filename.replace('exoplanet_model_', '').replace('.json', '')
                    
                    # Construire les chemins attendus
                    model_path = os.path.join(models_dir, filename)
                    
                    model_info = {
                        'format_type': format_type,
                        'filename': filename,
                        'available': os.path.exists(model_path),
                        'last_modified': None
                    }
                    
                    # Récupérer la date de modification si le fichier existe
                    if os.path.exists(model_path):
                        import time
                        model_info['last_modified'] = time.ctime(os.path.getmtime(model_path))
                    
                    available_models.append(model_info)
        
        return {
            'available_models': available_models,
            'message': f'{len(available_models)} modèles disponibles pour localStorage'
        }
        
    except Exception as e:
        logger.error(f"Erreur liste models localStorage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des modèles: {str(e)}")

@app.get("/models/localStorage/download/{format_type}")
async def download_model_for_localStorage(format_type: str):
    """
    Télécharge un modèle spécifique pour localStorage (JSON + métadonnées)
    """
    try:
        model_file = f"models/exoplanet_model_{format_type}.json"
        
        if not os.path.exists(model_file):
            raise HTTPException(
                status_code=404, 
                detail=f"Aucun modèle disponible pour le format {format_type}"
            )
        
        # Lire le modèle JSON
        with open(model_file, 'r') as f:
            model_json = json.load(f)
        
        # Charger temporairement le modèle pour récupérer les métadonnées
        ml_pipeline.load_model(format_type=format_type)
        metadata = {
            'format_type': format_type,
            'trained': ml_pipeline.trained,
            'feature_columns': ml_pipeline.feature_columns,
            'label_encoder_classes': list(ml_pipeline.label_encoder.classes_) if ml_pipeline.label_encoder else []
        }
        
        return {
            'model_json': model_json,
            'metadata': metadata,
            'format_type': format_type,
            'message': f'Modèle {format_type} préparé pour localStorage'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur download model {format_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")

@app.post("/models/localStorage/upload")
async def upload_model_from_localStorage(model_data: Dict[str, Any]):
    """
    Upload un modèle depuis localStorage vers le serveur
    """
    try:
        format_type = model_data.get('format_type')
        model_json = model_data.get('model_json')
        
        if not format_type or not model_json:
            raise HTTPException(
                status_code=400,
                detail="format_type et model_json sont requis"
            )
        
        # Créer le répertoire models s'il n'existe pas
        os.makedirs("models", exist_ok=True)
        
        # Sauvegarder le modèle JSON
        model_file = f"models/exoplanet_model_{format_type}.json"
        with open(model_file, 'w') as f:
            json.dump(model_json, f, indent=2)
        
        logger.info(f"Modèle {format_type} uploadé depuis localStorage vers le serveur")
        
        return {
            'message': f'Modèle {format_type} uploadé avec succès vers le serveur',
            'format_type': format_type,
            'model_file': model_file
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur upload model localStorage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")

@app.post("/models/localStorage/load/{format_type}")
async def load_model_from_localStorage(format_type: str, model_data: Dict[str, Any]):
    """
    Charge un modèle depuis localStorage dans le pipeline ML pour l'analyse
    """
    try:
        model_json = model_data.get('model_json')
        feature_columns = model_data.get('feature_columns', [])
        
        if not model_json:
            raise HTTPException(
                status_code=400,
                detail="model_json est requis"
            )
        
        # Charger le modèle dans le pipeline
        ml_pipeline.load_model_from_json(model_json, feature_columns)
        
        logger.info(f"Modèle {format_type} chargé depuis localStorage pour analyse")
        
        return {
            'message': f'Modèle {format_type} chargé avec succès depuis localStorage',
            'format_type': format_type,
            'trained': ml_pipeline.trained,
            'feature_count': len(feature_columns)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur load model localStorage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement: {str(e)}")

@app.post("/analyze/withModel")
async def analyze_with_saved_model(file: UploadFile = File(...), format_type: str = Form(...)):
    """
    Analyse un CSV avec un modèle spécifique déjà chargé (format_type)
    Workflow: Upload → Validation des planètes (sans entraînement)
    """
    try:
        # Étape 1: Lecture et validation du CSV
        logger.info(f"📤 Analyse avec modèle {format_type} - Upload: {file.filename}")
        
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Lecture avec Polars
        df = csv_to_polars(csv_content, auto_map=False)
        
        # Validation et détection du format (pour info seulement)
        df_processed, validation_info = column_mapper.process_dataframe(df)
        
        if not validation_info['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"CSV invalide: {'; '.join(validation_info['errors'])}"
            )
        
        csv_info = {
            'filename': file.filename,
            'detected_format': validation_info['format'],
            'detected_format_name': validation_info['format_name'],
            'total_rows': validation_info['total_rows'],
            'total_columns': validation_info['total_columns'],
            'analysis_format': format_type
        }
        
        logger.info(f"✅ CSV validé - Analysé avec modèle {format_type}")
        
        # Étape 2: Validation des planètes avec le modèle chargé
        logger.info(f"🔍 Validation des exoplanètes avec modèle {format_type}...")
        
        validation_results = exoplanet_validator.predict_confirmations(df_processed)
        
        logger.info(f"✅ Analyse terminée - {validation_results['analysis_summary']['confirmed_count']} planètes confirmables")
        
        # Construire la réponse
        response = {
            'csv_info': csv_info,
            'model_format': format_type,
            'validation': validation_results
        }
        
        return clean_for_json(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur analyse avec modèle {format_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@app.post("/analyze")
async def analyze_full_workflow(file: UploadFile = File(...)):
    """
    Endpoint simplifié pour l'analyse complète automatique:
    1. Upload + validation du CSV
    2. Entraînement automatique du modèle
    3. Validation automatique des planètes
    4. Retour des résultats
    
    Ne stocke PAS les fichiers - traitement en mémoire uniquement
    """
    try:
        # Étape 1: Lecture et validation du CSV
        logger.info(f"📤 Analyse automatique - Upload: {file.filename}")
        
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Lecture avec Polars
        df = csv_to_polars(csv_content, auto_map=False)
        
        # Validation et détection du format
        df_processed, validation_info = column_mapper.process_dataframe(df)
        
        if not validation_info['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"CSV invalide: {'; '.join(validation_info['errors'])}"
            )
        
        csv_info = {
            'filename': file.filename,
            'format': validation_info['format'],
            'format_name': validation_info['format_name'],
            'row_count': validation_info['total_rows'],
            'column_count': validation_info['total_columns'],
            'has_labels': validation_info['has_labels'],
            'label_column': validation_info.get('label_column', '')
        }
        
        logger.info(f"✅ CSV validé: {csv_info['format_name']} - {csv_info['row_count']} objets")
        
        # Vérifier qu'il y a des labels pour l'entraînement
        if not csv_info['has_labels']:
            raise HTTPException(
                status_code=400,
                detail="Le dataset ne contient pas de labels nécessaires pour l'entraînement"
            )
        
        # Étape 2: Entraînement du modèle
        logger.info(f"🧠 Entraînement du modèle {csv_info['format']}...")
        
        training_results = ml_pipeline.train_model(
            df=df_processed,
            label_column=validation_info['label_column'],
            planet_name_column=validation_info['planet_name_column'],
            format_type=validation_info['format'],
            test_size=0.3,
            random_state=42
        )
        
        logger.info(f"✅ Modèle entraîné - Accuracy: {training_results['accuracy']:.4f}")
        
        # Étape 3: Validation des planètes
        logger.info(f"🔍 Validation des exoplanètes...")
        
        validation_results = exoplanet_validator.predict_confirmations(df_processed)
        
        logger.info(f"✅ Validation terminée - {validation_results['analysis_summary']['confirmed_count']} planètes confirmables")
        
        # Construire la réponse finale
        response = {
            'csv_info': csv_info,
            'training': {
                'accuracy': training_results['accuracy'],
                'n_features': training_results['n_features'],
                'n_classes': training_results['n_classes'],
                'classes': training_results['label_names']
            },
            'validation': validation_results
        }
        
        return clean_for_json(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur analyse automatique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

# ================================
# ENDPOINTS EXOMINER
# ================================

@app.get("/exominer/health")
async def exominer_health():
    """
    Vérifie l'état du système ExoMiner (Docker, image, etc.)
    """
    try:
        # Vérifier Docker
        docker_available, docker_msg = exominer_service.check_docker()
        
        # Vérifier l'image ExoMiner
        image_available, image_msg = exominer_service.check_image()
        
        return {
            'docker': {
                'available': docker_available,
                'message': docker_msg
            },
            'exominer_image': {
                'available': image_available,
                'message': image_msg
            },
            'status': 'ready' if (docker_available and image_available) else 'not_ready'
        }
        
    except Exception as e:
        logger.error(f"Erreur vérification ExoMiner: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/exominer/image/pull")
async def exominer_pull_image():
    """
    Télécharge l'image Docker ExoMiner
    """
    try:
        # Vérifier que Docker est disponible
        docker_available, docker_msg = exominer_service.check_docker()
        if not docker_available:
            raise HTTPException(
                status_code=503,
                detail=f"Docker non disponible: {docker_msg}"
            )
        
        # Télécharger l'image
        success, message = exominer_service.pull_image()
        
        if success:
            return {
                'success': True,
                'message': message
            }
        else:
            raise HTTPException(status_code=500, detail=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement image: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/exominer/upload")
async def exominer_upload_tics(file: UploadFile = File(...)):
    """
    Upload un fichier CSV contenant les TIC IDs pour analyse ExoMiner
    
    Format CSV requis:
    - tic_id: ID TIC de l'étoile (ex: 307210830)
    - sector_run: Secteur TESS (ex: s0001-s0013)
    """
    try:
        # Vérifier que l'extension est .csv
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être au format CSV"
            )
        
        # Lire le contenu
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Créer l'analyse
        success, message, analysis_id = exominer_service.create_analysis(
            csv_content=csv_content,
            filename=file.filename
        )
        
        if success:
            return {
                'success': True,
                'message': message,
                'analysis_id': analysis_id
            }
        else:
            raise HTTPException(status_code=400, detail=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur upload ExoMiner: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/exominer/analyze-from-tics")
async def exominer_analyze_from_tics(request: Dict[str, Any]):
    """
    Lance une analyse ExoMiner à partir de TIC IDs (avec ou sans secteurs)
    Si sectors n'est pas fourni, ils seront récupérés automatiquement via astroquery
    
    Body JSON:
        {
            "tic_ids": [12345, 67890],
            "sectors": ["1", "2"],  // Optionnel
            "params": { ... }       // Paramètres ExoMiner optionnels
        }
    """
    try:
        from exominer_helper import get_sectors_from_tic, format_inputs
        import polars as pl
        
        tic_ids = request.get('tic_ids', [])
        sectors = request.get('sectors')
        params = request.get('params', {})
        
        if not tic_ids:
            raise HTTPException(status_code=400, detail="tic_ids requis")
        
        # Créer un DataFrame avec les TIC IDs
        if sectors and len(sectors) == len(tic_ids):
            # Cas avec secteurs fournis
            logger.info(f"Analyse de {len(tic_ids)} TIC IDs avec secteurs fournis")
            data = {
                'tic_id': tic_ids,
                'sectors': [[int(s)] for s in sectors]
            }
        else:
            # Cas sans secteurs : récupération automatique
            logger.info(f"Récupération automatique des secteurs pour {len(tic_ids)} TIC IDs...")
            sectors_data = []
            for tic in tic_ids:
                try:
                    sectors_list = get_sectors_from_tic(tic)
                    if not sectors_list:
                        logger.warning(f"Aucun secteur trouvé pour TIC {tic}")
                        sectors_list = []
                    sectors_data.append(sectors_list)
                except Exception as e:
                    logger.error(f"Erreur récupération secteurs pour TIC {tic}: {e}")
                    sectors_data.append([])
            
            data = {
                'tic_id': tic_ids,
                'sectors': sectors_data
            }
        
        # Créer le DataFrame et le formater
        df = pl.DataFrame(data)
        formatted_df = format_inputs(df)
        
        # Sauvegarder le CSV formaté dans un buffer
        csv_buffer = io.StringIO()
        formatted_df.write_csv(csv_buffer)
        csv_content = csv_buffer.getvalue()
        
        logger.info(f"CSV généré: {len(formatted_df)} lignes")
        
        # Créer l'analyse avec le CSV
        filename = f"tics_{len(tic_ids)}_items.csv"
        success, message, analysis_id = exominer_service.create_analysis(
            csv_content=csv_content,
            filename=filename
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        logger.info(f"🚀 Lancement analyse ExoMiner depuis TIC IDs: {analysis_id}")
        
        # Préparer les paramètres ExoMiner avec valeurs par défaut
        data_collection_mode = params.get('data_collection_mode', '2min')
        num_processes = params.get('num_processes', 2)
        num_jobs_param = params.get('num_jobs', 1)
        download_spoc = params.get('download_spoc_data_products', True)
        stellar_params_source = params.get('stellar_parameters_source', 'ticv8')
        ruwe_src = params.get('ruwe_source', 'gaiadr2')
        exominer_model = params.get('exominer_model', 'exominer++_single')
        
        # Lancer l'analyse immédiatement
        success, run_message, logs = exominer_service.run_analysis(
            analysis_id=analysis_id,
            data_collection_mode=data_collection_mode,
            num_processes=num_processes,
            num_jobs=num_jobs_param,
            model=exominer_model,
            download_spoc_data_products=download_spoc,
            stellar_parameters_source=stellar_params_source,
            ruwe_source=ruwe_src
        )
        
        return {
            'success': success,
            'message': run_message,
            'job_id': analysis_id,
            'tic_count': len(tic_ids),
            'rows_generated': len(formatted_df),
            'logs': logs[-20:] if logs else []
        }
            
    except ImportError as e:
        logger.error(f"Erreur import exominer_helper: {e}")
        raise HTTPException(status_code=500, detail="Modules ExoMiner helper non disponibles")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur analyse depuis TIC IDs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/exominer/analyze")
async def exominer_analyze_workflow(
    file: UploadFile = File(...),
    data_collection_mode: str = Form("2min"),
    num_processes: int = Form(2),
    num_jobs: int = Form(1),
    download_spoc_data_products: bool = Form(True),
    stellar_parameters_source: str = Form("ticv8"),
    ruwe_source: str = Form("gaiadr2"),
    exominer_model: str = Form("exominer++_single")
):
    """
    Workflow complet ExoMiner: Upload + Run en une seule étape
    
    Args:
        file: Fichier CSV avec TIC IDs
        Autres: Paramètres ExoMiner
    """
    try:
        # Vérifier Docker et l'image
        docker_available, docker_msg = exominer_service.check_docker()
        if not docker_available:
            raise HTTPException(
                status_code=503,
                detail=f"Docker non disponible: {docker_msg}"
            )
        
        image_available, image_msg = exominer_service.check_image()
        if not image_available:
            raise HTTPException(
                status_code=503,
                detail=f"Image ExoMiner non disponible. Utilisez /exominer/image/pull pour la télécharger."
            )
        
        # Vérifier extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être au format CSV"
            )
        
        # Lire et créer l'analyse
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        success, message, analysis_id = exominer_service.create_analysis(
            csv_content=csv_content,
            filename=file.filename
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        logger.info(f"🚀 Lancement analyse ExoMiner: {analysis_id}")
        
        # Lancer l'analyse immédiatement
        success, message, logs = exominer_service.run_analysis(
            analysis_id=analysis_id,
            data_collection_mode=data_collection_mode,
            num_processes=num_processes,
            num_jobs=num_jobs,
            model=exominer_model,
            download_spoc_data_products=download_spoc_data_products,
            stellar_parameters_source=stellar_parameters_source,
            ruwe_source=ruwe_source
        )
        
        return {
            'success': success,
            'message': message,
            'job_id': analysis_id,
            'logs': logs[-20:] if logs else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur workflow ExoMiner: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/exominer/jobs")
async def exominer_list_jobs():
    """
    Liste tous les jobs ExoMiner avec format attendu par le frontend
    """
    try:
        analyses = exominer_service.list_analyses()
        
        # Convertir en format jobs avec informations détaillées
        jobs = {}
        for analysis in analyses:
            job_info = exominer_service.get_job_info(analysis['analysis_id'])
            if job_info:
                jobs[job_info['job_id']] = job_info
        
        return {
            'jobs': jobs,
            'total': len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Erreur liste jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/exominer/jobs/{job_id}/results")
async def exominer_get_job_results(job_id: str):
    """
    Récupère les résultats détaillés d'un job ExoMiner
    """
    try:
        success, message, results = exominer_service.get_analysis_results(job_id)
        
        if success:
            return clean_for_json(results)
        else:
            raise HTTPException(status_code=404, detail=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération résultats: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/exominer/jobs/{job_id}/status")
async def exominer_get_job_status(job_id: str):
    """
    Récupère le statut d'un job ExoMiner
    """
    try:
        job_info = exominer_service.get_job_info(job_id)
        
        if job_info:
            return clean_for_json(job_info)
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} non trouvé")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/exominer/jobs/{job_id}/download")
async def exominer_download_results(job_id: str):
    """
    Télécharge tous les résultats d'un job en ZIP
    """
    try:
        metadata_path = os.path.join(
            exominer_service.results_dir,
            f"{job_id}_metadata.json"
        )
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail=f"Job {job_id} non trouvé")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        output_dir = metadata['output_dir']
        
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail="Résultats non trouvés")
        
        # Créer un fichier ZIP des résultats
        import zipfile
        import tempfile
        
        zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(zip_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
        
        from fastapi.responses import FileResponse
        
        return FileResponse(
            path=zip_file.name,
            filename=f"exominer_results_{job_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur téléchargement résultats: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/exominer/{analysis_id}/status")
async def exominer_get_status(analysis_id: str):
    """
    Récupère le statut d'une analyse ExoMiner
    """
    try:
        metadata_path = os.path.join(
            exominer_service.results_dir,
            f"{analysis_id}_metadata.json"
        )
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail=f"Analyse {analysis_id} non trouvée")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            'analysis_id': analysis_id,
            'status': metadata.get('status', 'unknown'),
            'created_at': metadata.get('created_at'),
            'started_at': metadata.get('started_at'),
            'completed_at': metadata.get('completed_at'),
            'filename': metadata.get('filename'),
            'info': metadata.get('info', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.delete("/exominer/jobs/{job_id}")
async def exominer_delete_job(job_id: str):
    """
    Supprime un job ExoMiner et ses fichiers
    """
    try:
        success, message = exominer_service.delete_analysis(job_id)
        
        if success:
            return {
                'success': True,
                'message': message
            }
        else:
            raise HTTPException(status_code=404, detail=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression job: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/exominer/jobs/cleanup")
async def exominer_cleanup_jobs():
    """
    Nettoie les jobs terminés/échoués
    """
    try:
        analyses = exominer_service.list_analyses()
        deleted_count = 0
        
        for analysis in analyses:
            if analysis['status'] in ['completed', 'failed', 'error']:
                # Optionnel: ne supprimer que les anciens jobs (> 7 jours)
                try:
                    created = datetime.fromisoformat(analysis['created_at'])
                    age_days = (datetime.now() - created).days
                    
                    if age_days > 7:
                        success, _ = exominer_service.delete_analysis(analysis['analysis_id'])
                        if success:
                            deleted_count += 1
                except:
                    pass
        
        return {
            'success': True,
            'message': f"{deleted_count} jobs nettoyés",
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erreur nettoyage jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


