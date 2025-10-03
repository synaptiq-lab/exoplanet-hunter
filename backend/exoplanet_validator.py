"""
Module de validation d'exoplanètes - Version flexible
S'adapte automatiquement aux 3 formats NASA (Kepler, TESS, K2)
Utilise le modèle ML entraîné pour identifier les planètes confirmables
"""

import polars as pl
from typing import Dict, List, Any
import logging
from ml_pipeline import ml_pipeline

logger = logging.getLogger(__name__)

class ExoplanetValidator:
    """
    Valide et identifie les exoplanètes confirmables dans un dataset.
    Fonctionne avec n'importe quel format tant qu'un modèle est entraîné.
    """
    
    def __init__(self):
        pass
    
    def validate_dataset(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Valide qu'un dataset peut être analysé.
        Vérifie simplement que le DataFrame n'est pas vide.
        
        Args:
            df: DataFrame Polars
            
        Returns:
            Dictionnaire avec is_valid, errors, warnings, info
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # Vérification basique
        if df.shape[0] == 0:
            validation['is_valid'] = False
            validation['errors'].append("Dataset vide")
            return validation
        
        validation['info']['total_rows'] = df.shape[0]
        validation['info']['total_columns'] = df.shape[1]
        
        logger.info(f"Dataset validé: {df.shape[0]} lignes, {df.shape[1]} colonnes")
        
        return validation
    
    def predict_confirmations(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Prédit quelles planètes peuvent être confirmées en utilisant le modèle ML.
        S'adapte automatiquement au format du dataset.
        
        Args:
            df: DataFrame Polars avec les données originales
            
        Returns:
            Dictionnaire avec les résultats de validation
        """
        # Vérifier que le modèle est entraîné
        if not ml_pipeline.trained:
            raise ValueError("Aucun modèle entraîné disponible. Entraînez d'abord un modèle sur des données labellisées.")
        
        logger.info(f"Début de la validation - {df.shape[0]} objets")
        
        # Utiliser le modèle ML pour prédire
        predictions = ml_pipeline.predict(df)
        
        # Mapper les colonnes communes pour extraction des caractéristiques
        char_mappings = {
            'period': ['koi_period', 'pl_orbper', 'orbital_period'],
            'duration': ['koi_duration', 'pl_trandur', 'transit_duration'],
            'depth': ['koi_depth', 'pl_trandep', 'transit_depth'],
            'radius': ['koi_prad', 'pl_rade', 'planet_radius']
        }
        
        # Séparer les planètes par prédiction
        confirmed_planets = []
        rejected_planets = []
        
        for i, pred in enumerate(predictions):
            # Extraire les caractéristiques depuis le DataFrame original
            characteristics = {}
            try:
                row = df.row(i, named=True)
                for char_key, possible_cols in char_mappings.items():
                    for col in possible_cols:
                        if col in row:
                            val = row[col]
                            # Vérifier que la valeur est valide (pas None, pas NaN)
                            if val is not None and (not isinstance(val, float) or (val == val)):
                                characteristics[char_key] = float(val)
                                break
            except Exception as e:
                logger.warning(f"Impossible d'extraire caractéristiques pour {pred['planet_name']}: {e}")
            
            planet_data = {
                'name': pred['planet_name'],
                'original_status': pred.get('original_label', 'UNKNOWN'),
                'predicted_status': pred['predicted_label'],
                'confidence': pred['confidence'],
                'probabilities': pred['probabilities'],
                'characteristics': characteristics
            }
            
            # Déterminer si la planète est confirmable
            # Une planète est confirmable si:
            # 1. Elle est prédite comme CONFIRMED
            # 2. Avec une confiance > 70%
            is_confirmable = (
                pred['predicted_label'] in ['CONFIRMED', 'CP', 'Confirmed'] and
                pred['confidence'] > 0.70
            )
            
            if is_confirmable:
                confirmed_planets.append(planet_data)
            else:
                rejected_planets.append(planet_data)
        
        # Calculer les statistiques
        total_analyzed = len(predictions)
        confirmed_count = len(confirmed_planets)
        rejected_count = len(rejected_planets)
        
        # Utiliser analysis_summary pour correspondre à l'interface frontend
        analysis_summary = {
            'total_analyzed': total_analyzed,
            'confirmed_count': confirmed_count,
            'rejected_count': rejected_count,
            'confirmation_rate': confirmed_count / total_analyzed if total_analyzed > 0 else 0
        }
        
        # Message personnalisé
        if confirmed_count > 0:
            message = f"✅ {confirmed_count} planète(s) CANDIDATE/FALSE POSITIVE peuvent être confirmées !"
        else:
            message = "ℹ️ Aucune nouvelle planète confirmable trouvée dans ce dataset."
        
        results = {
            'message': message,
            'analysis_summary': analysis_summary,  # Nom corrigé pour le frontend
            'confirmed_planets': confirmed_planets,  # Toutes les planètes confirmées
            'rejected_planets': rejected_planets[:100],  # Limiter les rejetées à 100
            'total_confirmed': len(confirmed_planets),
            'total_rejected': len(rejected_planets)
        }
        
        logger.info(f"Validation terminée: {confirmed_count} confirmables sur {total_analyzed}")
        
        return results
    
    def get_planet_details(self, df: pl.DataFrame, planet_name: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une planète spécifique.
        
        Args:
            df: DataFrame Polars
            planet_name: Nom de la planète à rechercher
            
        Returns:
            Dictionnaire avec les détails de la planète
        """
        try:
            # Trouver la colonne de nom de planète
            planet_col = None
            for col in ['planet_name', 'kepoi_name', 'toi', 'pl_name']:
                if col in df.columns:
                    planet_col = col
                    break
            
            if not planet_col:
                return {'error': 'Colonne de nom de planète non trouvée'}
            
            # Filtrer pour la planète demandée
            planet_df = df.filter(pl.col(planet_col) == planet_name)
            
            if planet_df.shape[0] == 0:
                return {'error': f'Planète {planet_name} non trouvée'}
            
            # Convertir en dictionnaire
            planet_dict = planet_df.to_dicts()[0]
            
            # Nettoyer les valeurs nulles
            cleaned_dict = {
                k: (None if v is None or (isinstance(v, float) and (v != v)) else v)
                for k, v in planet_dict.items()
            }
            
            return {
                'planet_name': planet_name,
                'data': cleaned_dict
            }
            
        except Exception as e:
            logger.error(f"Erreur get_planet_details: {e}")
            return {'error': str(e)}

# Instance globale
exoplanet_validator = ExoplanetValidator()
