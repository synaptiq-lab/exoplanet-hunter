# 🚀 Exoplanet Hunter - Détection IA d'Exoplanètes

Application web de détection d'exoplanètes utilisant l'intelligence artificielle et les données ouvertes des missions spatiales NASA (Kepler, K2, TESS).

## 🌟 Fonctionnalités

### 🔍 **Analyse de Données**
- **Upload CSV** : Téléchargez vos fichiers de données astronomiques
- **Prédictions IA** : Classification automatique (Confirmée, Candidate, Faux Positif)
- **Scores de Confiance** : Évaluation de la fiabilité des prédictions
- **Visualisations** : Graphiques interactifs des résultats
- **Export** : Téléchargement des résultats au format CSV

### 🧠 **Intelligence Artificielle**
- **Modèles Multiples** : Random Forest, Réseaux de Neurones, SVM, Gradient Boosting
- **Réentraînement** : Amélioration continue avec de nouvelles données
- **Hyperparamètres** : Configuration avancée des algorithmes
- **Métriques** : Suivi des performances (Précision, Recall, F1-Score)

### 📊 **Interface Moderne**
- **Design Responsive** : Optimisé mobile, tablette et desktop
- **Animations Fluides** : Interface interactive avec Framer Motion
- **Thème Spatial** : Design immersif inspiré de l'espace
- **UX Intuitive** : Navigation simple pour experts et novices

## 🛠️ Architecture Technique

### **Frontend - Next.js 14**
- **Framework** : Next.js avec App Router
- **UI** : React 18 + TypeScript
- **Styling** : Tailwind CSS avec thème personnalisé
- **Animations** : Framer Motion
- **Graphiques** : Recharts pour les visualisations
- **API** : Axios pour les communications

### **Backend - FastAPI**
- **Framework** : FastAPI avec Python 3.11
- **ML** : Scikit-learn pour les modèles
- **Data** : Pandas + NumPy pour le traitement
- **API** : Routes RESTful avec validation Pydantic
- **CORS** : Configuration pour le développement

### **Infrastructure**
- **Containerisation** : Docker + Docker Compose
- **Proxy** : Nginx pour le routage
- **Volumes** : Persistance des données et modèles

## 🚀 Démarrage Rapide

### Prérequis
- Docker et Docker Compose
- Git

### Installation

1. **Cloner le repository**
   ```bash
   git clone <repo-url>
   cd exoplanet-hunter
   ```

2. **Lancer avec Docker**
   ```bash
   docker-compose up --build
   ```

3. **Accéder à l'application**
   - **Frontend** : http://localhost:3000
   - **Backend API** : http://localhost:8000
   - **Documentation API** : http://localhost:8000/docs

### Développement Local

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📡 Utilisation

### 1. **Analyser des Données**
- Préparez un fichier CSV avec les colonnes requises :
  - `koi_period` : Période orbitale (jours)
  - `koi_duration` : Durée du transit (heures)
  - `koi_depth` : Profondeur du transit (ppm)
  - `koi_prad` : Rayon planétaire (rayons terrestres)
  - Colonnes optionnelles : `koi_srad`, `koi_stemp`, `koi_smass`

- Glissez-déposez votre fichier dans la zone d'upload
- Visualisez les résultats avec graphiques et statistiques
- Exportez les prédictions

### 2. **Réentraîner le Modèle**
- Préparez des données étiquetées avec la colonne `koi_disposition`
- Choisissez l'algorithme et les hyperparamètres
- Lancez le réentraînement
- Consultez les nouvelles métriques de performance

### 3. **Consulter les Statistiques**
- Précision, Recall et F1-Score du modèle
- Nombre d'échantillons d'entraînement
- Date du dernier entraînement

## 🔬 Données Scientifiques

### **Sources de Données**
- **Kepler** (2009-2017) : 9,564 observations
- **K2** (2014-2018) : 2,394 observations  
- **TESS** (2018-présent) : 5,829 observations

### **Méthode du Transit**
L'application détecte les exoplanètes via la méthode du transit :
- Mesure de la baisse de luminosité stellaire
- Analyse des courbes de lumière
- Classification basée sur les paramètres orbitaux

### **Variables Clés**
- **Période orbitale** : Temps pour une orbite complète
- **Durée du transit** : Temps de passage devant l'étoile
- **Profondeur** : Amplitude de la baisse de luminosité
- **Rayon planétaire** : Taille relative à la Terre
- **Paramètres stellaires** : Caractéristiques de l'étoile hôte

## 🎯 Objectifs du Hackathon

### **Performance du Modèle**
- Automatisation de la détection manuelle
- Haute précision pour minimiser les faux positifs
- Traitement rapide de grandes quantités de données

### **Expérience Utilisateur**
- Interface accessible aux chercheurs et novices
- Visualisations claires et informatives
- Explications pédagogiques des résultats

### **Considérations Scientifiques**
- Interprétabilité des prédictions IA
- Gestion de l'incertitude et des scores intermédiaires
- Respect des standards de validation scientifique

## 🛡️ API Endpoints

### **Analyse**
- `POST /predict` : Prédiction par fichier CSV
- `POST /analyze/single` : Analyse d'un objet unique

### **Modèle**
- `GET /model/stats` : Statistiques du modèle
- `POST /train` : Réentraînement avec nouvelles données

### **Informations**
- `GET /datasets/info` : Informations sur les datasets
- `GET /health` : Vérification de santé

## 🔧 Configuration

### **Variables d'Environnement**

#### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Backend
```
PYTHONPATH=/app
CORS_ORIGINS=http://localhost:3000
```

### **Personnalisation**
- Modifiez `tailwind.config.js` pour le thème
- Ajustez les hyperparamètres dans `TrainingConfig`
- Configurez les seuils de confiance selon vos besoins

## 🤝 Contribution

### **Structure du Projet**
```
exoplanet-hunter/
├── frontend/          # Application Next.js
│   ├── app/          # Pages et layouts
│   ├── components/   # Composants React
│   ├── lib/          # Utilitaires et API
│   └── types/        # Définitions TypeScript
├── backend/          # API FastAPI
│   ├── main.py       # Point d'entrée
│   └── requirements.txt
├── data/             # Données et modèles
├── docker-compose.yml
└── nginx.conf
```

### **Standards de Code**
- **Frontend** : TypeScript strict, ESLint, Prettier
- **Backend** : Python 3.11, Type hints, Pydantic
- **Git** : Commits conventionnels, branches feature

## 📄 Licence

Ce projet est développé dans le cadre du NASA Space Apps Challenge 2024.

## 🌌 Remerciements

- **NASA** pour les données ouvertes des missions spatiales
- **Space Apps Challenge** pour l'opportunité de contribuer
- **Communauté Open Source** pour les outils et bibliothèques

---

**🚀 Explorez l'univers, découvrez des mondes ! 🪐**