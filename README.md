# 🌌 Exoplanet Hunter

Application web d'analyse et de détection automatique d'exoplanètes par Intelligence Artificielle.

## 🎯 Fonctionnalités

- **Upload Drag & Drop** : Téléversez facilement vos fichiers CSV
- **Détection automatique** : Support des formats Kepler (KOI), K2 et TESS (TOI)
- **Pipeline ML complète** : Entraînement + Validation automatiques
- **Résultats détaillés** : Tableau interactif des planètes confirmées
- **Export CSV** : Téléchargez la liste complète des découvertes

## 🚀 Démarrage Rapide

### Prérequis

- Docker
- Docker Compose

### Installation

```bash
# Cloner le projet
git clone <votre-repo>
cd exoplanet-hunter

# Démarrer l'application
docker-compose up --build
```

L'application sera accessible sur :
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000

## 📊 Utilisation

1. Accédez à http://localhost:3000/dashboard/analyze
2. Glissez-déposez un fichier CSV (Kepler, K2 ou TESS)
3. Attendez l'analyse automatique (10-30 secondes)
4. Consultez les résultats et exportez la liste des planètes confirmées

## 🔬 Formats Supportés

### Kepler (KOI)
- Fichiers : `cumulative.csv`, `cumulative_*.csv`
- Label : `koi_pdisposition` ou `koi_disposition`
- Colonnes requises : `kepoi_name`, `koi_period`

### K2
- Fichiers : `k2pandc_*.csv`
- Label : `disposition`
- Colonnes requises : `pl_name`, `pl_orbper`

### TESS (TOI)
- Fichiers : `TOI_*.csv`
- Label : `tfopwg_disp`
- Colonnes requises : `toi`, `pl_orbper`

## 🏗️ Architecture

```
exoplanet-hunter/
├── frontend/              # Next.js + React + TailwindCSS
│   ├── app/
│   │   └── dashboard/
│   │       └── analyze/   # Page principale d'analyse
│   ├── components/        # Composants réutilisables
│   └── lib/              # Utilitaires et API client
│
├── backend/              # FastAPI + ML Pipeline
│   ├── main.py           # Routes API
│   ├── ml_pipeline.py    # Entraînement XGBoost
│   ├── column_mapper.py  # Détection de format
│   ├── exoplanet_validator.py  # Validation des planètes
│   └── data_utils.py     # Utilitaires CSV
│
└── docker-compose.yml    # Orchestration
```

## 🤖 Pipeline ML

1. **Upload** : Lecture et validation du CSV
2. **Détection** : Identification automatique du format (Kepler/K2/TESS)
3. **Preprocessing** : Nettoyage et sélection des features
4. **Training** : Entraînement XGBoost sur toutes les features numériques
5. **Validation** : Prédiction sur les candidats (PC, CANDIDATE, FP)
6. **Filtrage** : Sélection des planètes avec confiance > 70%

## 📈 Résultats

Le système identifie les exoplanètes "confirmables" parmi les candidats :
- **Statut original** : PC (Planetary Candidate), CANDIDATE, FP (False Positive)
- **Prédiction** : CONFIRMED, CP (Confirmed Planet)
- **Confiance** : Score de probabilité (> 70% pour validation)

## 🛠️ Technologies

### Frontend
- Next.js 14
- React 18
- TailwindCSS
- Framer Motion
- React Dropzone

### Backend
- FastAPI
- XGBoost
- Polars / Pandas
- NumPy
- Scikit-learn

## 📝 API Endpoints

### POST `/analyze`
Analyse complète automatique d'un fichier CSV

**Request** : `multipart/form-data` avec fichier CSV

**Response** :
```json
{
  "csv_info": {
    "filename": "TOI_2025.csv",
    "format": "tess",
    "format_name": "TESS Objects of Interest (TOI)",
    "row_count": 7699,
    "column_count": 65,
    "has_labels": true,
    "label_column": "tfopwg_disp"
  },
  "training": {
    "accuracy": 0.7251,
    "n_features": 53,
    "n_classes": 6,
    "classes": ["APC", "CP", "FA", "FP", "KP", "PC"]
  },
  "validation": {
    "message": "✅ 347 planète(s) confirmées !",
    "analysis_summary": {
      "total_analyzed": 7699,
      "confirmed_count": 347,
      "rejected_count": 7352,
      "confirmation_rate": 0.045
    },
    "confirmed_planets": [...]
  }
}
```

## 🎓 Crédits

Développé pour le **NASA Space Apps Challenge 2024**

Datasets :
- [Kepler Objects of Interest](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=cumulative)
- [K2 Planets and Candidates](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=k2pandc)
- [TESS Objects of Interest](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=TOI)

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails
