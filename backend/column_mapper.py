"""
Module de détection et validation des 3 formats officiels NASA.
IMPORTANT: Ce module NE fait PAS de mapping des colonnes.
Il détecte uniquement le format et identifie la colonne de label.
"""

import polars as pl
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ColumnMapper:
    """
    Détecte le format du dataset et identifie la colonne de label.
    NE MAPPE PAS les colonnes - conserve toutes les colonnes originales.
    """
    
    def __init__(self):
        # Définition des 3 formats officiels avec leurs colonnes de label
        self.format_definitions = {
            'kepler': {
                'name': 'Kepler Objects of Interest (KOI)',
                'detection_columns': ['kepoi_name'],
                'label_column_candidates': ['koi_pdisposition', 'koi_disposition'],
                'planet_name_column': 'kepoi_name',
                'documentation': 'https://exoplanetarchive.ipac.caltech.edu/docs/API_kepcandidate_columns.html',
                'expected_labels': [
                    'CONFIRMED',
                    'CANDIDATE', 
                    'FALSE POSITIVE'
                ]
            },
            'tess': {
                'name': 'TESS Objects of Interest (TOI)',
                'detection_columns': ['toi'],
                'label_column_candidates': ['tfopwg_disp'],
                'planet_name_column': 'toi',
                'documentation': 'https://exoplanetarchive.ipac.caltech.edu/docs/API_TOI_columns.html',
                'expected_labels': [
                    'APC',  # Ambiguous Planetary Candidate
                    'CP',   # Confirmed Planet
                    'FA',   # False Alarm
                    'FP',   # False Positive
                    'KP',   # Known Planet
                    'PC'    # Planetary Candidate
                ]
            },
            'k2': {
                'name': 'K2 Planets and Candidates',
                'detection_columns': ['pl_name'],
                'label_column_candidates': ['disposition'],
                'planet_name_column': 'pl_name',
                'documentation': 'https://exoplanetarchive.ipac.caltech.edu/docs/API_k2pandc_columns.html',
                'expected_labels': [
                    'CANDIDATE',
                    'FALSE POSITIVE',
                    'CONFIRMED',
                    'FALSE POSITIVE CANDIDATE'
                ]
            }
        }
    
    def detect_format(self, df: pl.DataFrame) -> Optional[str]:
        """
        Détecte le format du dataset parmi les 3 formats officiels NASA.
        
        Returns:
            'kepler', 'tess', 'k2', ou None si non reconnu
        """
        columns = set(df.columns)
        
        # KEPLER: kepoi_name présent
        if 'kepoi_name' in columns:
            return 'kepler'
        
        # TESS: toi présent
        elif 'toi' in columns:
            return 'tess'
        
        # K2: pl_name + disposition + pl_orbper
        elif 'pl_name' in columns and 'pl_orbper' in columns:
            return 'k2'
        
        logger.warning(f"Format non reconnu. Colonnes trouvées: {list(columns)[:10]}")
        return None
    
    def identify_label_column(self, df: pl.DataFrame, format_type: str) -> Optional[str]:
        """
        Identifie la colonne de label pour le format détecté.
        
        Returns:
            Nom de la colonne de label, ou None si absente
        """
        if format_type not in self.format_definitions:
            return None
        
        format_def = self.format_definitions[format_type]
        label_candidates = format_def['label_column_candidates']
        
        for candidate in label_candidates:
            if candidate in df.columns:
                # Vérifier que la colonne n'est pas vide
                if df[candidate].null_count() < df.shape[0]:
                    logger.info(f"Colonne de label identifiée: {candidate}")
                    return candidate
        
        logger.warning(f"Aucune colonne de label trouvée parmi: {label_candidates}")
        return None
    
    def get_label_distribution(self, df: pl.DataFrame, label_column: str) -> Dict:
        """
        Retourne la distribution des labels dans le dataset.
        """
        if label_column not in df.columns:
            return {}
        
        value_counts = df[label_column].value_counts().to_dicts()
        distribution = {row[label_column]: row['count'] for row in value_counts}
        
        return distribution
    
    def validate_dataset(self, df: pl.DataFrame) -> Dict:
        """
        Valide un dataset et retourne ses métadonnées.
        NE MODIFIE PAS le DataFrame - le retourne tel quel.
        
        Returns:
            {
                'is_valid': bool,
                'format': str,
                'format_name': str,
                'label_column': str or None,
                'has_labels': bool,
                'label_distribution': dict,
                'planet_name_column': str,
                'total_rows': int,
                'total_columns': int,
                'columns': list,
                'numeric_columns': list,
                'documentation': str,
                'errors': list
            }
        """
        errors = []
        
        # 1. Détection du format
        format_type = self.detect_format(df)
        
        if not format_type:
            return {
                'is_valid': False,
                'errors': ['Format non reconnu. Formats supportés: Kepler (kepoi_name), TESS (toi), K2 (pl_name + pl_orbper)']
            }
        
        format_def = self.format_definitions[format_type]
        
        # 2. Identification de la colonne de label
        label_column = self.identify_label_column(df, format_type)
        has_labels = label_column is not None
        
        # 3. Distribution des labels
        label_distribution = {}
        if has_labels:
            label_distribution = self.get_label_distribution(df, label_column)
        
        # 4. Identifier les colonnes numériques
        numeric_columns = []
        for col in df.columns:
            dtype = df[col].dtype
            if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, 
                        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                        pl.Float32, pl.Float64]:
                numeric_columns.append(col)
        
        # 5. Vérification de la colonne planet_name
        planet_name_col = format_def['planet_name_column']
        if planet_name_col not in df.columns:
            errors.append(f"Colonne d'identification manquante: {planet_name_col}")
        
        return {
            'is_valid': len(errors) == 0,
            'format': format_type,
            'format_name': format_def['name'],
            'label_column': label_column,
            'has_labels': has_labels,
            'label_distribution': label_distribution,
            'planet_name_column': planet_name_col,
            'total_rows': df.shape[0],
            'total_columns': df.shape[1],
            'columns': df.columns,
            'numeric_columns': numeric_columns,
            'documentation': format_def['documentation'],
            'expected_labels': format_def['expected_labels'],
            'errors': errors
        }
    
    def process_dataframe(self, df: pl.DataFrame) -> Tuple[pl.DataFrame, Dict]:
        """
        Valide le DataFrame et retourne les métadonnées.
        IMPORTANT: Retourne le DataFrame SANS MODIFICATION.
        
        Returns:
            (df_original, validation_info)
        """
        # Filtrer les lignes de commentaires si présentes (première colonne commence par #)
        first_col = df.columns[0]
        if df[first_col].dtype == pl.Utf8:
            df = df.filter(~pl.col(first_col).str.starts_with('#'))
        
        validation_info = self.validate_dataset(df)
        
        logger.info(f"Dataset validé: {validation_info['format_name']}")
        logger.info(f"Total lignes: {validation_info['total_rows']}, colonnes: {validation_info['total_columns']}")
        if validation_info['has_labels']:
            logger.info(f"Colonne de label: {validation_info['label_column']}")
            logger.info(f"Distribution: {validation_info['label_distribution']}")
        
        return df, validation_info

# Instance globale
column_mapper = ColumnMapper()
