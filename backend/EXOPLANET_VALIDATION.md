# 🪐 Guide de Validation d'Exoplanètes

## Objectif

Ce système permet de **confirmer automatiquement des exoplanètes** en analysant les planètes marquées comme `CANDIDATE` ou `FALSE POSITIVE` pour déterminer lesquelles ont les caractéristiques d'une vraie exoplanète `CONFIRMED`.

## 🔄 Workflow Simplifié

### 1. **Entraînement du Modèle** (Une seule fois)
```bash
# Uploader un dataset avec des planètes CONFIRMED pour entraîner le modèle
POST /datasets/upload
# Fichier: dataset_avec_planetes_confirmees.csv

# Entraîner le modèle sur ces données
POST /datasets/{dataset_id}/train
```

### 2. **Validation de Nouvelles Planètes** (Répétable)
```bash
# Uploader un dataset avec des planètes CANDIDATE/FALSE POSITIVE
POST /validate/upload  
# Fichier: nouvelles_planetes_a_analyser.csv

# Lancer la validation
POST /validate/{dataset_id}
```

### 3. **Résultat**
Le système retourne :
- ✅ **Liste des planètes confirmées** avec leurs noms
- ❌ **Liste des planètes rejetées** 
- 📊 **Statistiques de validation**

## 📋 Format des Données

### Colonnes Requises
```csv
kepoi_name,koi_disposition,koi_period,koi_duration,koi_depth,koi_prad
K00752.01,CANDIDATE,9.488036,2.9575,615.8,2.26
K00753.01,FALSE POSITIVE,19.899140,1.7822,10829.0,14.60
```

### Description des Colonnes
- `kepoi_name`: Nom de la planète (ex: K00752.01)
- `koi_disposition`: Statut actuel (CANDIDATE, FALSE POSITIVE, CONFIRMED)
- `koi_period`: Période orbitale en jours
- `koi_duration`: Durée du transit en heures  
- `koi_depth`: Profondeur du transit en ppm
- `koi_prad`: Rayon planétaire en rayons terrestres

## 🎯 Exemple d'Utilisation

### Étape 1: Entraînement
```bash
curl -X POST "http://localhost:8000/datasets/upload" \
     -F "file=@kepler_confirmed_planets.csv"

curl -X POST "http://localhost:8000/datasets/abc123/train" \
     -F "config={\"algorithm\":\"xgboost\"}"
```

### Étape 2: Validation
```bash
curl -X POST "http://localhost:8000/validate/upload" \
     -F "file=@new_candidates.csv"

curl -X POST "http://localhost:8000/validate/def456"
```

### Étape 3: Résultat
```json
{
  "message": "Analyse terminée: 3 planètes peuvent être confirmées",
  "confirmed_planets": [
    {
      "name": "K00752.01",
      "original_status": "CANDIDATE", 
      "predicted_status": "CONFIRMED",
      "confidence": 0.89,
      "characteristics": {
        "period": 9.488036,
        "duration": 2.9575,
        "depth": 615.8,
        "radius": 2.26
      }
    }
  ],
  "analysis_summary": {
    "total_analyzed": 10,
    "confirmed_count": 3,
    "rejected_count": 7,
    "confirmation_rate": 0.3
  }
}
```

## 🔍 Détails d'une Planète

Pour obtenir plus d'informations sur une planète spécifique :

```bash
curl -X GET "http://localhost:8000/validate/def456/planet/K00752.01"
```

## 📈 Méthode des Transits

Le système analyse les caractéristiques du transit pour déterminer si c'est une vraie exoplanète :

- **Période orbitale** : Régularité du passage
- **Durée du transit** : Temps de passage devant l'étoile  
- **Profondeur** : Diminution de luminosité
- **Rayon planétaire** : Taille calculée de la planète

## ✅ Critères de Confirmation

Une planète est confirmée si :
- Le modèle prédit `CONFIRMED` avec confiance > 70%
- Les caractéristiques du transit sont cohérentes
- Les paramètres orbitaux sont stables
