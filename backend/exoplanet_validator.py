"""
Module de validation d'exoplanètes
Analyse les planètes CANDIDATE et FALSE POSITIVE pour déterminer 
lesquelles peuvent être confirmées comme vraies exoplanètes
"""

import polars as pl
from typing import List, Dict, Tuple
import logging
from ml_pipeline import ml_pipeline

logger = logging.getLogger(__name__)

class ExoplanetValidator:
    """
    Validateur d'exoplanètes basé sur la méthode des transits
    """
    
    def __init__(self):
        self.required_columns = [
            'kepoi_name',  # Nom de la planète
            'koi_disposition',  # Statut actuel
            'koi_period',  # Période orbitale
            'koi_duration',  # Durée du transit
            'koi_depth',  # Profondeur du transit
            'koi_prad',  # Rayon planétaire
        ]
    
    def validate_dataset(self, df: pl.DataFrame) -> Dict:
        """
        Valide un dataset pour la confirmation d'exoplanètes
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # Vérifier les colonnes requises
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            validation['is_valid'] = False
            validation['errors'].append(f"Colonnes manquantes: {missing_cols}")
            return validation
        
        # Analyser les statuts des planètes
        if 'koi_disposition' in df.columns:
            disposition_counts = df['koi_disposition'].value_counts()
            validation['info']['disposition_distribution'] = {
                row['koi_disposition']: row['count'] 
                for row in disposition_counts.iter_rows(named=True)
            }
            
            # Filtrer les planètes à analyser (CANDIDATE et FALSE POSITIVE)
            candidates = df.filter(
                (pl.col('koi_disposition') == 'CANDIDATE') | 
                (pl.col('koi_disposition') == 'FALSE POSITIVE')
            )
            
            validation['info']['candidates_to_analyze'] = candidates.shape[0]
            validation['info']['total_planets'] = df.shape[0]
            
            if candidates.shape[0] == 0:
                validation['warnings'].append("Aucune planète CANDIDATE ou FALSE POSITIVE trouvée à analyser")
        
        return validation
    
    def predict_confirmations(self, df: pl.DataFrame) -> Dict:
        """
        Prédit quelles planètes CANDIDATE/FALSE POSITIVE peuvent être confirmées
        """
        if not ml_pipeline.is_trained():
            raise ValueError("Aucun modèle entraîné disponible. Entraînez d'abord un modèle sur des données avec des planètes CONFIRMED.")
        
        # Filtrer uniquement les planètes à analyser
        candidates = df.filter(
            (pl.col('koi_disposition') == 'CANDIDATE') | 
            (pl.col('koi_disposition') == 'FALSE POSITIVE')
        )
        
        if candidates.shape[0] == 0:
            return {
                'message': 'Aucune planète CANDIDATE ou FALSE POSITIVE à analyser',
                'confirmed_planets': [],
                'analysis_summary': {
                    'total_analyzed': 0,
                    'confirmed_count': 0,
                    'rejected_count': 0
                }
            }
        
        # Faire les prédictions
        predictions = ml_pipeline.predict(candidates)
        
        # Analyser les résultats
        confirmed_planets = []
        rejected_planets = []
        
        for i, prediction in enumerate(predictions):
            planet_data = candidates.row(i, named=True)
            planet_name = planet_data.get('kepoi_name', f"Planète {i+1}")
            
            result = {
                'name': planet_name,
                'original_status': planet_data['koi_disposition'],
                'predicted_status': prediction['classification'],
                'confidence': prediction['confidence_score'],
                'characteristics': {
                    'period': planet_data.get('koi_period'),
                    'duration': planet_data.get('koi_duration'), 
                    'depth': planet_data.get('koi_depth'),
                    'radius': planet_data.get('koi_prad')
                }
            }
            
            # Si le modèle prédit CONFIRMED avec une bonne confiance
            if (prediction['classification'] == 'CONFIRMED' and 
                prediction['confidence_score'] > 0.7):
                confirmed_planets.append(result)
            else:
                rejected_planets.append(result)
        
        return {
            'message': f'Analyse terminée: {len(confirmed_planets)} planètes peuvent être confirmées',
            'confirmed_planets': confirmed_planets,
            'rejected_planets': rejected_planets,
            'analysis_summary': {
                'total_analyzed': len(predictions),
                'confirmed_count': len(confirmed_planets),
                'rejected_count': len(rejected_planets),
                'confirmation_rate': len(confirmed_planets) / len(predictions) if predictions else 0
            }
        }
    
    def get_planet_details(self, df: pl.DataFrame, planet_name: str) -> Dict:
        """
        Récupère les détails d'une planète spécifique
        """
        planet = df.filter(pl.col('kepoi_name') == planet_name)
        
        if planet.shape[0] == 0:
            return {'error': f'Planète {planet_name} non trouvée'}
        
        planet_data = planet.row(0, named=True)
        
        return {
            'name': planet_name,
            'current_status': planet_data.get('koi_disposition'),
            'orbital_period_days': planet_data.get('koi_period'),
            'transit_duration_hours': planet_data.get('koi_duration'),
            'transit_depth_ppm': planet_data.get('koi_depth'),
            'planetary_radius_earth': planet_data.get('koi_prad'),
            'stellar_temperature_k': planet_data.get('koi_steff'),
            'kepler_magnitude': planet_data.get('koi_kepmag')
        }

# Instance globale du validateur
exoplanet_validator = ExoplanetValidator()
