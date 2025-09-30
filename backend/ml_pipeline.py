"""
Pipeline de Machine Learning pour la détection d'exoplanètes
Basé sur le notebook Kaggle avec XGBoost et Polars
"""

import polars as pl
import polars.selectors as cs
import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from typing import Dict, List, Tuple, Optional, Any
import pickle
import os
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExoplanetMLPipeline:
    """Pipeline ML pour la classification d'exoplanètes"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'koi_pdisposition', 'koi_score', 'koi_fpflag_nt', 'koi_fpflag_ss',
            'koi_fpflag_co', 'koi_fpflag_ec', 'koi_period', 'koi_period_err1',
            'koi_period_err2', 'koi_time0bk', 'koi_time0bk_err1', 'koi_time0bk_err2',
            'koi_impact', 'koi_impact_err1', 'koi_impact_err2', 'koi_duration',
            'koi_duration_err1', 'koi_duration_err2', 'koi_depth', 'koi_depth_err1',
            'koi_depth_err2', 'koi_prad', 'koi_prad_err1', 'koi_prad_err2',
            'koi_teq', 'koi_teq_err1', 'koi_teq_err2', 'koi_insol',
            'koi_insol_err1', 'koi_insol_err2', 'koi_model_snr', 'koi_tce_plnt_num',
            'koi_tce_delivname', 'koi_steff', 'koi_steff_err1', 'koi_steff_err2',
            'koi_slogg', 'koi_slogg_err1', 'koi_slogg_err2', 'koi_srad',
            'koi_srad_err1', 'koi_srad_err2', 'ra', 'dec', 'koi_kepmag'
        ]
        self.target_names = ["CONFIRMED", "FALSE POSITIVE", "CANDIDATE"]
        self.label_mapping = {0: "CONFIRMED", 1: "FALSE POSITIVE", 2: "CANDIDATE"}
        self.reverse_label_mapping = {v: k for k, v in self.label_mapping.items()}
        self.model_stats = {}
        self.feature_importance = {}
        
    def preprocess_data(self, df: pl.DataFrame, is_training: bool = False) -> Tuple[pl.DataFrame, Optional[pl.Series]]:
        """
        Préprocesse les données selon la pipeline du notebook
        """
        try:
            # Suppression des colonnes non nécessaires si elles existent
            cols_to_drop = ["rowid", "kepid", "kepoi_name", "kepler_name"]
            existing_cols_to_drop = [col for col in cols_to_drop if col in df.columns]
            if existing_cols_to_drop:
                df = df.drop(existing_cols_to_drop)
            
            # Gestion de la colonne target
            y = None
            if is_training and "koi_disposition" in df.columns:
                y = df.get_column("koi_disposition")
                df = df.drop("koi_disposition")
            elif "koi_disposition" in df.columns:
                df = df.drop("koi_disposition")
            
            # Conversion des colonnes string en categorical puis en numérique
            string_cols = [col for col in df.columns if df[col].dtype == pl.Utf8]
            if string_cols:
                df = df.cast({col: pl.Categorical for col in string_cols})
                df = df.with_columns(cs.categorical().to_physical())
            
            # Gestion des valeurs manquantes
            df = df.fill_null(0)
            
            # Filtrer les colonnes disponibles
            available_features = [col for col in self.feature_columns if col in df.columns]
            if available_features:
                df = df.select(available_features)
            
            logger.info(f"Données préprocessées: {df.shape[0]} lignes, {df.shape[1]} colonnes")
            return df, y
            
        except Exception as e:
            logger.error(f"Erreur lors du préprocessing: {e}")
            raise
    
    def train_model(self, df: pl.DataFrame, algorithm: str = "xgboost", 
                   test_size: float = 0.3, random_state: int = 42, 
                   hyperparameters: Dict = None) -> Dict[str, Any]:
        """
        Entraîne le modèle selon la pipeline du notebook
        """
        try:
            # Préprocessing
            X_df, y = self.preprocess_data(df, is_training=True)
            
            if y is None:
                raise ValueError("Colonne 'koi_disposition' manquante pour l'entraînement")
            
            # Conversion en pandas pour sklearn
            X = X_df.to_pandas()
            y_pandas = y.to_pandas()
            
            # Conversion des labels string en numérique
            y_numeric = y_pandas.map(self.reverse_label_mapping)
            
            # Split train/validation
            X_train, X_val, y_train, y_val = train_test_split(
                X, y_numeric, test_size=test_size, random_state=random_state, stratify=y_numeric
            )
            
            # Configuration du modèle
            if algorithm == "xgboost":
                model_params = {
                    'random_state': random_state,
                    'eval_metric': 'mlogloss',
                    'objective': 'multi:softprob'
                }
                if hyperparameters:
                    model_params.update(hyperparameters)
                
                self.model = xgb.XGBClassifier(**model_params)
                
                # Entraînement avec validation
                self.model.fit(
                    X_train, y_train,
                    eval_set=[(X_train, y_train), (X_val, y_val)],
                    verbose=False
                )
            else:
                raise ValueError(f"Algorithme '{algorithm}' non supporté")
            
            # Évaluation
            y_pred = self.model.predict(X_val)
            
            # Calcul des métriques
            accuracy = accuracy_score(y_val, y_pred)
            precision = precision_score(y_val, y_pred, average='weighted')
            recall = recall_score(y_val, y_pred, average='weighted')
            f1 = f1_score(y_val, y_pred, average='weighted')
            
            # Conversion des prédictions en labels string pour le rapport
            y_val_str = [self.label_mapping[i] for i in y_val]
            y_pred_str = [self.label_mapping[i] for i in y_pred]
            
            # Feature importance
            if hasattr(self.model, 'feature_importances_'):
                self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
            
            # Sauvegarde des stats
            self.model_stats = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'training_samples': len(X_train),
                'last_trained': datetime.now().isoformat(),
                'algorithm': algorithm
            }
            
            # Rapport détaillé
            report = classification_report(y_val_str, y_pred_str, target_names=self.target_names, output_dict=True)
            
            logger.info(f"Modèle entraîné avec succès. Accuracy: {accuracy:.3f}")
            
            return {
                'model_stats': self.model_stats,
                'classification_report': report,
                'feature_importance': self.feature_importance,
                'samples_used': len(X_train)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement: {e}")
            raise
    
    def predict(self, df: pl.DataFrame) -> List[Dict[str, Any]]:
        """
        Effectue des prédictions sur de nouvelles données
        """
        if self.model is None:
            raise ValueError("Modèle non entraîné. Utilisez train_model() d'abord.")
        
        try:
            # Préprocessing
            X_df, _ = self.preprocess_data(df, is_training=False)
            X = X_df.to_pandas()
            
            # Assurer que toutes les colonnes nécessaires sont présentes
            missing_cols = set(self.model.feature_names_in_) - set(X.columns)
            if missing_cols:
                # Ajouter les colonnes manquantes avec des zéros
                for col in missing_cols:
                    X[col] = 0
            
            # Réorganiser les colonnes dans le bon ordre
            X = X[self.model.feature_names_in_]
            
            # Prédictions
            predictions = self.model.predict(X)
            probabilities = self.model.predict_proba(X)
            
            results = []
            for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
                # Classe prédite
                classification = self.label_mapping[pred]
                confidence_score = float(np.max(proba))
                
                # Feature importance pour cette prédiction
                if hasattr(self.model, 'feature_importances_'):
                    top_features = dict(sorted(
                        self.feature_importance.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:5])
                else:
                    top_features = {}
                
                # Explication
                explanation = self._generate_explanation(classification, confidence_score, top_features)
                
                results.append({
                    'classification': classification,
                    'confidence_score': confidence_score,
                    'probabilities': {
                        self.label_mapping[j]: float(prob) 
                        for j, prob in enumerate(proba)
                    },
                    'features_importance': top_features,
                    'explanation': explanation
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            raise
    
    def _generate_explanation(self, classification: str, confidence: float, features: Dict[str, float]) -> str:
        """
        Génère une explication pour la prédiction
        """
        top_feature = max(features.items(), key=lambda x: x[1])[0] if features else "paramètres orbitaux"
        
        explanations = {
            "CONFIRMED": f"Exoplanète confirmée avec {confidence:.1%} de confiance. Signal fort détecté principalement basé sur {top_feature}.",
            "CANDIDATE": f"Candidat exoplanète avec {confidence:.1%} de confiance. Signal détecté nécessitant validation supplémentaire, principalement basé sur {top_feature}.",
            "FALSE POSITIVE": f"Faux positif avec {confidence:.1%} de confiance. Le signal détecté n'est probablement pas dû à une exoplanète, analyse basée sur {top_feature}."
        }
        
        return explanations.get(classification, f"Classification: {classification} avec {confidence:.1%} de confiance.")
    
    def save_model(self, filepath: str):
        """Sauvegarde le modèle entraîné"""
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'target_names': self.target_names,
            'label_mapping': self.label_mapping,
            'model_stats': self.model_stats,
            'feature_importance': self.feature_importance
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Modèle sauvegardé: {filepath}")
    
    def load_model(self, filepath: str):
        """Charge un modèle pré-entraîné"""
        if not os.path.exists(filepath):
            logger.warning(f"Fichier de modèle non trouvé: {filepath}")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.feature_columns = model_data.get('feature_columns', self.feature_columns)
            self.target_names = model_data.get('target_names', self.target_names)
            self.label_mapping = model_data.get('label_mapping', self.label_mapping)
            self.model_stats = model_data.get('model_stats', {})
            self.feature_importance = model_data.get('feature_importance', {})
            
            logger.info(f"Modèle chargé: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            return False
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du modèle"""
        return self.model_stats
    
    def is_trained(self) -> bool:
        """Vérifie si le modèle est entraîné"""
        return self.model is not None

# Instance globale du pipeline
ml_pipeline = ExoplanetMLPipeline()
