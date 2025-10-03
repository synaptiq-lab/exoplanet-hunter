"""
Pipeline de Machine Learning flexible pour la détection d'exoplanètes.
S'adapte automatiquement aux 3 formats: Kepler, TESS, K2.
Conserve toutes les colonnes originales et utilise toutes les features numériques disponibles.
"""

import polars as pl
import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Tuple, Optional, Any
import pickle
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExoplanetMLPipeline:
    """
    Pipeline ML flexible qui s'adapte automatiquement au format du dataset.
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.label_column = None
        self.planet_name_column = None
        self.format_type = None
        self.model_stats = {}
        self.feature_importance = {}
        self.trained = False
        
    def identify_features(self, df: pl.DataFrame, label_column: str, 
                         planet_name_column: str) -> List[str]:
        """
        Identifie automatiquement toutes les colonnes numériques utilisables comme features.
        Exclut la colonne de label et la colonne d'identification de la planète.
        """
        numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, 
                        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                        pl.Float32, pl.Float64]
        
        feature_columns = []
        
        for col in df.columns:
            # Exclure label et planet_name
            if col == label_column or col == planet_name_column:
                continue
            
            # Prendre toutes les colonnes numériques
            if df[col].dtype in numeric_types:
                # Vérifier que la colonne n'est pas complètement vide
                if df[col].null_count() < df.shape[0]:
                    feature_columns.append(col)
        
        logger.info(f"Features identifiées: {len(feature_columns)} colonnes numériques")
        logger.info(f"Exemples: {feature_columns[:10]}")
        
        return feature_columns
    
    def preprocess_data(self, df: pl.DataFrame, label_column: str, 
                       planet_name_column: str, is_training: bool = False) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Préprocesse les données en conservant toutes les features numériques.
        
        Args:
            df: DataFrame Polars
            label_column: Nom de la colonne de label
            planet_name_column: Nom de la colonne d'identification
            is_training: Si True, extrait aussi la colonne de label
            
        Returns:
            (X, y) où X est le DataFrame des features et y la série des labels (si is_training)
        """
        try:
            # 1. Identifier les features si pas déjà fait
            if not self.feature_columns:
                self.feature_columns = self.identify_features(df, label_column, planet_name_column)
                self.label_column = label_column
                self.planet_name_column = planet_name_column
            
            # 2. Sélectionner les features
            X_df = df.select(self.feature_columns)
            
            # 3. Gérer les valeurs manquantes (remplir avec la moyenne ou 0)
            for col in X_df.columns:
                if X_df[col].null_count() > 0:
                    mean_val = X_df[col].mean()
                    if mean_val is not None and not np.isnan(mean_val):
                        X_df = X_df.with_columns(pl.col(col).fill_null(mean_val))
                    else:
                        X_df = X_df.with_columns(pl.col(col).fill_null(0.0))
            
            # 4. Convertir en pandas pour sklearn
            X = X_df.to_pandas()
            
            # 5. Extraire les labels si entraînement
            y = None
            if is_training:
                y_series = df[label_column].to_pandas()
                # Nettoyer les labels (supprimer espaces, etc.)
                y = y_series.str.strip() if y_series.dtype == 'object' else y_series
            
            logger.info(f"Préprocessing terminé: {X.shape[0]} lignes, {X.shape[1]} features")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Erreur lors du préprocessing: {e}")
            raise
    
    def train_model(self, df: pl.DataFrame, label_column: str, planet_name_column: str,
                   format_type: str, test_size: float = 0.2, random_state: int = 42, 
                   hyperparameters: Dict = None) -> Dict[str, Any]:
        """
        Entraîne le modèle XGBoost sur toutes les features numériques disponibles.
        
        Args:
            df: DataFrame Polars avec toutes les colonnes originales
            label_column: Nom de la colonne de label
            planet_name_column: Nom de la colonne d'identification
            format_type: Type de format ('kepler', 'tess', 'k2')
            test_size: Proportion du test set
            random_state: Seed pour la reproductibilité
            hyperparameters: Paramètres XGBoost personnalisés
            
        Returns:
            Dictionnaire avec les résultats de l'entraînement
        """
        try:
            logger.info(f"Début de l'entraînement pour le format: {format_type}")
            
            # Réinitialiser les feature_columns pour ce nouveau format
            # (important pour éviter les conflits avec un format précédent)
            self.feature_columns = []
            self.format_type = format_type
            
            # 1. Préprocessing
            X, y = self.preprocess_data(df, label_column, planet_name_column, is_training=True)
            
            if y is None or len(y) == 0:
                raise ValueError(f"Colonne de label '{label_column}' manquante ou vide")
            
            # 2. Encoder les labels (transformation string → numérique)
            y_encoded = self.label_encoder.fit_transform(y)
            label_names = self.label_encoder.classes_.tolist()
            n_classes = len(label_names)
            
            logger.info(f"Classes détectées ({n_classes}): {label_names}")
            logger.info(f"Distribution: {pd.Series(y).value_counts().to_dict()}")
            
            # 3. Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_encoded, test_size=test_size, random_state=random_state, stratify=y_encoded
            )
            
            logger.info(f"Train set: {X_train.shape[0]} échantillons")
            logger.info(f"Test set: {X_test.shape[0]} échantillons")
            
            # 4. Paramètres XGBoost par défaut
            default_params = {
                'objective': 'multi:softprob' if n_classes > 2 else 'binary:logistic',
                'num_class': n_classes if n_classes > 2 else None,
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': random_state,
                'eval_metric': 'mlogloss' if n_classes > 2 else 'logloss'
            }
            
            if hyperparameters:
                default_params.update(hyperparameters)
            
            # Retirer num_class si binary
            if default_params['objective'] == 'binary:logistic':
                default_params.pop('num_class', None)
            
            # 5. Entraînement XGBoost
            logger.info("Entraînement du modèle XGBoost...")
            self.model = xgb.XGBClassifier(**default_params)
            self.model.fit(X_train, y_train)
            self.format_type = format_type
            self.trained = True
            
            # 6. Prédictions sur le test set
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)
            
            # 7. Décoder les prédictions pour les métriques
            y_test_labels = self.label_encoder.inverse_transform(y_test)
            y_pred_labels = self.label_encoder.inverse_transform(y_pred)
            
            # 8. Calcul des métriques
            accuracy = accuracy_score(y_test, y_pred)
            
            # Métriques par classe
            precision = precision_score(y_test, y_pred, average=None, zero_division=0).tolist()
            recall = recall_score(y_test, y_pred, average=None, zero_division=0).tolist()
            f1 = f1_score(y_test, y_pred, average=None, zero_division=0).tolist()
            
            # Rapport de classification
            class_report = classification_report(y_test_labels, y_pred_labels, output_dict=True, zero_division=0)
            
            # Matrice de confusion
            conf_matrix = confusion_matrix(y_test, y_pred).tolist()
            
            # Feature importance
            feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_.tolist()))
            # Trier par importance
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            self.feature_importance = feature_importance
            
            # 9. Sauvegarder les stats
            self.model_stats = {
                'format_type': format_type,
                'label_column': label_column,
                'planet_name_column': planet_name_column,
                'n_features': len(self.feature_columns),
                'feature_columns': self.feature_columns,
                'label_names': label_names,
                'n_classes': n_classes,
                'n_train_samples': X_train.shape[0],
                'n_test_samples': X_test.shape[0],
                'accuracy': float(accuracy),
                'precision_by_class': {label_names[i]: float(precision[i]) for i in range(n_classes)},
                'recall_by_class': {label_names[i]: float(recall[i]) for i in range(n_classes)},
                'f1_by_class': {label_names[i]: float(f1[i]) for i in range(n_classes)},
                'classification_report': class_report,
                'confusion_matrix': conf_matrix,
                'feature_importance': dict(list(feature_importance.items())[:20]),  # Top 20
                'hyperparameters': default_params,
                'trained_at': datetime.now().isoformat()
            }
            
            logger.info(f"Entraînement terminé - Accuracy: {accuracy:.4f}")
            logger.info(f"Top 5 features: {list(feature_importance.keys())[:5]}")
            
            return self.model_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement: {e}")
            raise
    
    def predict(self, df: pl.DataFrame) -> List[Dict[str, Any]]:
        """
        Prédit les labels pour un nouveau dataset.
        
        Args:
            df: DataFrame Polars avec les mêmes colonnes que le dataset d'entraînement
            
        Returns:
            Liste de dictionnaires avec les prédictions pour chaque planète
        """
        try:
            if not self.trained or self.model is None:
                raise ValueError("Le modèle n'est pas entraîné. Veuillez d'abord entraîner le modèle.")
            
            # 1. Récupérer les noms des planètes
            planet_names = df[self.planet_name_column].to_list()
            
            # 2. Préprocessing (sans extraction de labels)
            X, _ = self.preprocess_data(df, self.label_column, self.planet_name_column, is_training=False)
            
            # 3. Prédictions
            y_pred_encoded = self.model.predict(X)
            y_pred_proba = self.model.predict_proba(X)
            
            # 4. Décoder les prédictions
            y_pred_labels = self.label_encoder.inverse_transform(y_pred_encoded)
            
            # 5. Construire les résultats
            predictions = []
            for i in range(len(planet_names)):
                pred_dict = {
                    'planet_name': planet_names[i],
                    'predicted_label': y_pred_labels[i],
                    'confidence': float(np.max(y_pred_proba[i])),
                    'probabilities': {
                        label: float(prob) 
                        for label, prob in zip(self.label_encoder.classes_, y_pred_proba[i])
                    }
                }
                
                # Ajouter le label original si présent
                if self.label_column in df.columns:
                    original_label = df[self.label_column][i]
                    pred_dict['original_label'] = original_label if original_label is not None else 'UNKNOWN'
                
                predictions.append(pred_dict)
            
            logger.info(f"Prédictions terminées pour {len(predictions)} objets")
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {e}")
            raise
    
    def save_model(self, model_dir: str = "models"):
        """Sauvegarde le modèle et ses métadonnées (un modèle par format)"""
        try:
            os.makedirs(model_dir, exist_ok=True)
            
            # Utiliser un nom de fichier spécifique au format
            format_suffix = f"_{self.format_type}" if self.format_type else ""
            
            # Sauvegarder le modèle XGBoost
            model_path = os.path.join(model_dir, f"exoplanet_model{format_suffix}.json")
            self.model.save_model(model_path)
            
            # Sauvegarder le label encoder
            encoder_path = os.path.join(model_dir, f"label_encoder{format_suffix}.pkl")
            with open(encoder_path, 'wb') as f:
                pickle.dump(self.label_encoder, f)
            
            # Sauvegarder les métadonnées
            metadata = {
                'feature_columns': self.feature_columns,
                'label_column': self.label_column,
                'planet_name_column': self.planet_name_column,
                'format_type': self.format_type,
                'model_stats': self.model_stats,
                'trained': self.trained
            }
            metadata_path = os.path.join(model_dir, f"model_metadata{format_suffix}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Modèle {self.format_type} sauvegardé dans {model_dir}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {e}")
            raise
    
    def load_model(self, model_dir: str = "models", format_type: str = None):
        """
        Charge le modèle et ses métadonnées pour un format spécifique.
        
        Args:
            model_dir: Répertoire contenant les modèles
            format_type: Format à charger ('kepler', 'tess', 'k2'). Si None, charge le dernier modèle utilisé.
        """
        try:
            # Utiliser un nom de fichier spécifique au format
            format_suffix = f"_{format_type}" if format_type else ""
            
            # Charger le modèle XGBoost
            model_path = os.path.join(model_dir, f"exoplanet_model{format_suffix}.json")
            if not os.path.exists(model_path):
                logger.warning(f"Modèle non trouvé: {model_path}")
                return False
            
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            
            # Charger le label encoder
            encoder_path = os.path.join(model_dir, f"label_encoder{format_suffix}.pkl")
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            # Charger les métadonnées
            metadata_path = os.path.join(model_dir, f"model_metadata{format_suffix}.json")
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.feature_columns = metadata['feature_columns']
            self.label_column = metadata['label_column']
            self.planet_name_column = metadata['planet_name_column']
            self.format_type = metadata['format_type']
            self.model_stats = metadata['model_stats']
            self.trained = metadata['trained']
            
            logger.info(f"Modèle {self.format_type} chargé depuis {model_dir}")
            logger.info(f"Features: {len(self.feature_columns)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            return False

# Instance globale
ml_pipeline = ExoplanetMLPipeline()
