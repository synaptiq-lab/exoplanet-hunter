## Audit de l’application Exoplanet Hunter

### Vue d’ensemble
- **Backend (FastAPI)**: endpoints pour prédire (`/predict`), entraîner (`/train`, `/datasets/{id}/train`), gérer les datasets (upload/list/delete/analyze/explore), analyser une ligne (`/analyze/single`), workflow auto (`/analyze`) et valider des exoplanètes (`/validate/*`).
- **Pipeline ML (XGBoost + Polars)**: détection automatique des features numériques, `LabelEncoder`, sauvegarde/chargement par format (`kepler`/`tess`/`k2`) dans `models/`.
- **Données**: CSV chargés en mémoire; stockage sous `data/` avec métadonnées JSON.
- **Frontend (Next.js)**: réécriture `/api/*` vers `NEXT_PUBLIC_API_URL`.
- **Infra (Docker + Nginx)**: `docker-compose` avec 3 services (`backend`/`frontend`/`nginx`), proxy `/api/` → backend, le reste → frontend.

### Endpoints clés (exemples)
- `GET /health`, `GET /model/stats`
- `POST /predict`, `POST /train`
- `POST /datasets/upload`, `GET /datasets`, `DELETE /datasets/{dataset_id}`
- `POST /datasets/{dataset_id}/analyze`, `POST /datasets/{dataset_id}/train`, `GET /datasets/{dataset_id}/explore`
- `POST /validate/upload`, `POST /validate/{dataset_id}`, `GET /validate/{dataset_id}/planet/{planet_name}`
- `POST /analyze` (workflow complet)

### Principales failles et risques
- **Critiques**
  - **Pas d’authentification/autorisation**: toutes les routes d’écriture (upload, entraînement, suppression) sont publiques.
  - **Path traversal**: 
    - `dataset_id` est interpolé dans des chemins sous `data/` sans validation stricte.
    - `UploadFile.filename` est réutilisé pour écrire sous `data/datasets/{id}/{filename}` sans normalisation (risque `../`).
  - **Téléversements non bornés**: aucune limite de taille ni contrôle MIME; lecture intégrale en mémoire → risque DoS.

- **Majeures**
  - **CORS trop permissif**: `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True`; origines codées en dur.
  - **Nginx sans garde-fous**: pas de `client_max_body_size`, rate limiting, ni timeouts renforcés.
  - **Exécution en mode dev** en prod: `--reload` et montage du code hôte; surface d’attaque accrue.
  - **Conteneur root** avec toolchain (`gcc/g++`) installée; non nécessaire en prod.

- **Fiabilité / bugs**
  - **Incohérence `csv_to_polars`**: la fonction retourne un seul `DataFrame`, mais plusieurs endpoints font `df, mapping_info = csv_to_polars(...)` → crash.
  - **Sauvegarde modèle**: `/train` appelle `ml_pipeline.save_model("models/exoplanet_model.pkl")` alors que `save_model` attend un dossier (ex. `"models"`).
  - **Validation/colonnes**: `validate_exoplanet_data` attend des colonnes standardisées alors que le pipeline conserve les colonnes d’origine; risque d’incohérence selon le flux.
  - **Concurrence**: état global `ml_pipeline` partagé; entraînement/prédictions simultanés sans verrou.
  - **Schémas d’entrée**: `/analyze/single` accepte `Dict[str, float]` sans modèle Pydantic dédié.

- **Divers**
  - Journaux verbeux pouvant divulguer des infos.
  - Dépendances non utilisées (`python-jose`, `passlib`).

### Recommandations (priorisées)
- **Sécurité**
  - Ajouter AuthN/AuthZ (JWT) et rôles; protéger toute écriture/suppression/entraînement.
  - Bloquer le path traversal:
    - Valider `dataset_id` via regex stricte (ex. `^[a-zA-Z0-9_-]{1,32}$`).
    - Forcer `os.path.basename(file.filename)` et générer un nom interne.
    - Construire les chemins via `pathlib` et vérifier qu’ils restent sous un répertoire racine attendu.
  - Durcir les uploads: limites (ex. 10–50 Mo), contrôle MIME, parsing en streaming, quotas.
  - CORS via variables d’environnement; whitelists strictes; désactiver `allow_credentials` si inutile.
  - Nginx: `client_max_body_size`, `proxy_read_timeout`, rate limiting (ex. `limit_req`), en-têtes de sécurité, TLS si exposé.
  - Docker: image prod sans toolchain, exécution sous utilisateur non-root, retirer `--reload`, pas de montage de code en prod.

- **Fiabilité**
  - Corriger `csv_to_polars` vs appels (retourner `(df, mapping_info)` ou adapter les endpoints pour n’utiliser que `df`).
  - Corriger `save_model` dans `/train` pour lui passer un dossier (`"models"`) ou ajuster la signature.
  - Introduire des schémas Pydantic pour les payloads et valider类型/contraintes.
  - Ajouter des verrous (threading/async) ou déporter l’entraînement dans une file de tâches (ex. RQ/Celery/Arq).
  - Tests d’intégration couvrant `upload → validate → train → analyze` sur Kepler/K2/TESS.

- **Observabilité**
  - Journalisation mesurée (pas d’infos sensibles), métriques (temps, tailles, taux d’erreurs), alertes.

- **Déploiement**
  - Unifier l’accès API via Nginx (`/api`) et aligner CORS.
  - CI/CD avec scans de sécurité et tests automatisés.

### Bugs à corriger en priorité
1. Remplacer tous les usages `df, mapping_info = csv_to_polars(...)` par un appel cohérent (ou faire retourner `(df, mapping_info)`).
2. Changer `ml_pipeline.save_model("models/exoplanet_model.pkl")` en `ml_pipeline.save_model("models")`.
3. Valider et normaliser `dataset_id` et `UploadFile.filename` (basename + regex).
4. Ajouter limite de taille upload côté Nginx et FastAPI; vérifier le MIME.
5. Protéger les endpoints d’écriture (authentification) et retirer `--reload` en prod.

### Check-list rapide
- [ ] AuthN/AuthZ activées pour routes sensibles
- [ ] Validation stricte des chemins (`dataset_id`, `filename`)
- [ ] Limites d’upload + rate limiting Nginx
- [ ] CORS durci et piloté par env
- [ ] Process d’entraînement isolé et thread-safe
- [ ] Sauvegarde/chargement de modèle cohérents


