"""
Utilitaires pour la gestion des données d'exoplanètes
Supporte les formats Kepler, K2, TESS avec mapping automatique des colonnes
"""

import polars as pl
import pandas as pd
import io
from typing import Dict, List, Tuple, Optional
import logging
from column_mapper import column_mapper

logger = logging.getLogger(__name__)

def csv_to_polars(csv_content: str, required_columns: List[str] = None, auto_map: bool = False) -> pl.DataFrame:
    """
    Convertit le contenu CSV en DataFrame Polars.
    Par défaut, ne fait PAS de mapping des colonnes (conserve les colonnes originales).
    
    Args:
        csv_content: Contenu du fichier CSV
        required_columns: Colonnes requises (optionnel)
        auto_map: Si True, applique le mapping automatique (DEPRECATED - ne pas utiliser)
    
    Returns:
        DataFrame Polars avec colonnes originales
    """
    try:
        # Lecture avec Polars, en ignorant les lignes de commentaires
        lines = csv_content.strip().split('\n')
        
        # Filtrer les lignes de commentaires (commencent par #)
        data_lines = [line for line in lines if not line.strip().startswith('#')]
        clean_csv = '\n'.join(data_lines)
        
        df = pl.read_csv(io.StringIO(clean_csv))
        
        # Validation des colonnes requises si spécifiées
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Colonnes manquantes: {missing_columns}")
        
        logger.info(f"DataFrame créé: {df.shape[0]} lignes, {df.shape[1]} colonnes")
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion CSV: {e}")
        raise

def validate_exoplanet_data(df: pl.DataFrame, for_training: bool = False, mapping_info: Dict = None) -> Dict[str, any]:
    """
    Valide les données d'exoplanètes avec support des colonnes standardisées
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'info': {
            'rows': df.shape[0],
            'columns': df.shape[1],
            'column_names': df.columns,
            'format': mapping_info.get('format', 'unknown') if mapping_info else 'unknown'
        }
    }
    
    # Colonnes minimales requises pour les prédictions (format standardisé)
    min_required_cols = ['orbital_period', 'transit_duration', 'transit_depth', 'planet_radius']
    
    # Colonnes supplémentaires pour l'entraînement
    training_required_cols = min_required_cols + ['disposition']
    
    required_cols = training_required_cols if for_training else min_required_cols
    
    # Vérification des colonnes requises
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Colonnes manquantes: {missing_cols}")
    
    # Vérification du nombre de lignes
    if df.shape[0] == 0:
        validation_result['is_valid'] = False
        validation_result['errors'].append("Aucune donnée trouvée")
    elif df.shape[0] < 10 and for_training:
        validation_result['warnings'].append("Peu de données pour l'entraînement (< 10 lignes)")
    
    # Vérification des valeurs manquantes dans les colonnes critiques
    for col in [c for c in min_required_cols if c in df.columns]:
        null_count = df[col].null_count()
        if null_count > 0:
            validation_result['warnings'].append(
                f"Colonne '{col}': {null_count} valeurs manquantes sur {df.shape[0]}"
            )
    
    # Vérification des valeurs de disposition pour l'entraînement
    if for_training and 'disposition' in df.columns:
        valid_dispositions = ['CONFIRMED', 'FALSE POSITIVE', 'CANDIDATE']
        unique_dispositions = df['disposition'].unique().to_list()
        invalid_dispositions = [d for d in unique_dispositions if d not in valid_dispositions and d is not None]
        
        if invalid_dispositions:
            validation_result['errors'].append(
                f"Valeurs de disposition invalides: {invalid_dispositions}. "
                f"Valeurs acceptées: {valid_dispositions}"
            )
        
        # Distribution des classes
        disposition_counts = df['disposition'].value_counts().sort('disposition')
        validation_result['info']['class_distribution'] = {
            row['disposition']: row['count'] 
            for row in disposition_counts.iter_rows(named=True)
        }
    
    # Informations sur le mapping
    if mapping_info:
        validation_result['info']['mapping_info'] = mapping_info
    
    return validation_result


def get_column_info() -> Dict[str, str]:
    """
    Retourne les descriptions des colonnes principales
    """
    return {
        'koi_period': 'Période orbitale en jours',
        'koi_duration': 'Durée du transit en heures',
        'koi_depth': 'Profondeur du transit en parties par million (ppm)',
        'koi_prad': 'Rayon planétaire en rayons terrestres',
        'koi_srad': 'Rayon stellaire en rayons solaires',
        'koi_stemp': 'Température effective stellaire en Kelvin',
        'koi_smass': 'Masse stellaire en masses solaires',
        'koi_disposition': 'Classification: CONFIRMED, CANDIDATE, ou FALSE POSITIVE',
        'koi_score': 'Score de confiance du pipeline Kepler',
        'koi_fpflag_nt': 'Flag de faux positif - Not Transit-Like',
        'koi_fpflag_ss': 'Flag de faux positif - Stellar Eclipse',
        'koi_fpflag_co': 'Flag de faux positif - Centroid Offset',
        'koi_fpflag_ec': 'Flag de faux positif - Ephemeris Match Indicates Contamination'
    }

def format_prediction_results(predictions: List[Dict], total_samples: int) -> Dict:
    """
    Formate les résultats de prédiction pour l'API
    """
    # Comptage par classification
    classification_counts = {}
    total_confidence = 0
    
    for pred in predictions:
        classification = pred['classification']
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        total_confidence += pred['confidence_score']
    
    avg_confidence = total_confidence / len(predictions) if predictions else 0
    
    return {
        'predictions': predictions,
        'summary': {
            'total_samples': total_samples,
            'classifications': classification_counts,
            'average_confidence': round(avg_confidence, 3)
        },
        'processing_info': {
            'processed_samples': len(predictions),
            'success_rate': len(predictions) / total_samples if total_samples > 0 else 0
        }
    }

