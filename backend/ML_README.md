# Système ML Exoplanet Hunter

## Architecture

Le système ML d'Exoplanet Hunter est basé sur le notebook Kaggle et utilise :

- **XGBoost** : Modèle de gradient boosting pour la classification
- **Polars** : Manipulation rapide des données
- **Scikit-learn** : Métriques et validation
- **FastAPI** : API REST pour l'intégration

## Structure des fichiers

```
backend/
├── ml_pipeline.py      # Pipeline ML principal avec classe ExoplanetMLPipeline
├── data_utils.py       # Utilitaires pour la gestion des données
├── train_initial_model.py  # Script d'entraînement initial
├── init_model.py       # Script d'initialisation pour Docker
├── main.py            # API FastAPI avec intégration ML
└── models/            # Répertoire pour les modèles sauvegardés
```

## Pipeline ML

### 1. Préprocessing des données
- Conversion des colonnes string en categorical puis numérique
- Gestion des valeurs manquantes (remplacement par 0)
- Filtrage des colonnes disponibles

### 2. Entraînement
- Split train/validation (70/30 par défaut)
- Entraînement XGBoost avec validation
- Calcul des métriques (accuracy, precision, recall, F1)
- Sauvegarde du modèle et des statistiques

### 3. Prédiction
- Préprocessing des nouvelles données
- Prédictions avec scores de confiance
- Importance des features
- Explications générées automatiquement

## Utilisation

### Entraînement initial

```bash
cd backend
python train_initial_model.py
```

### API Endpoints

#### `/predict` - Prédiction sur fichier CSV
```python
# Upload d'un fichier CSV avec colonnes :
# koi_period, koi_duration, koi_depth, koi_prad, etc.
```

#### `/train` - Réentraînement du modèle
```python
# Upload d'un fichier CSV avec colonne koi_disposition
# Configuration : algorithm, test_size, hyperparameters
```

#### `/model/stats` - Statistiques du modèle
```python
# Retourne accuracy, precision, recall, F1-score
```

## Variables importantes

### Features principales (basées sur le notebook)
- `koi_period` : Période orbitale (jours)
- `koi_duration` : Durée du transit (heures)  
- `koi_depth` : Profondeur du transit (ppm)
- `koi_prad` : Rayon planétaire (rayons terrestres)
- `koi_srad` : Rayon stellaire (rayons solaires)
- `koi_stemp` : Température stellaire (K)
- `koi_smass` : Masse stellaire (masses solaires)

### Labels de classification
- `CONFIRMED` : Exoplanète confirmée
- `CANDIDATE` : Candidat exoplanète
- `FALSE POSITIVE` : Faux positif

## Performance attendue

Basé sur le notebook original :
- **Accuracy** : ~91%
- **Precision** : 
  - CONFIRMED: ~81%
  - FALSE POSITIVE: ~99%
  - CANDIDATE: ~85%

## Docker

Le container initialise automatiquement un modèle pré-entraîné au démarrage :

```dockerfile
CMD python init_model.py && uvicorn main:app --host 0.0.0.0 --port 8000
```

## Développement

### Ajout de nouveaux algorithmes

Modifier `ml_pipeline.py` dans la méthode `train_model()` :

```python
if algorithm == "nouveau_algo":
    self.model = NouveauAlgo(**model_params)
```

### Nouvelles features

Ajouter les colonnes dans `feature_columns` de `ExoplanetMLPipeline`.

### Tests

```bash
# Test de prédiction simple
curl -X POST "http://localhost:8000/analyze/single" \
  -H "Content-Type: application/json" \
  -d '{"koi_period": 9.48, "koi_duration": 2.96, "koi_depth": 615.8, "koi_prad": 2.26}'
```

