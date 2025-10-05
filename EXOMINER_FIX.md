# Fix pour la popup des résultats ExoMiner

## Problème identifié

La popup ne fonctionnait pas car:
1. ✅ **Types TypeScript manquants** - Ajouté `ExoMinerPredictions` dans `frontend/lib/api.ts`
2. ✅ **Dépendance manquante** - `astroquery` n'était pas dans `requirements.txt`
3. ✅ **Import échoué** - Le backend ne pouvait pas importer `exominer_helper.py`

## Solution appliquée

### 1. Backend - Ajout de la dépendance

**Fichier:** `backend/requirements.txt`
```diff
+ astroquery==0.4.7
```

### 2. Frontend - Ajout des types TypeScript

**Fichier:** `frontend/lib/api.ts`
```typescript
export interface ExoMinerPrediction {
  tic_id: number;
  result: 'Confirmed' | 'Candidate' | 'False Positive';
  score: number;
}

export interface ExoMinerPredictions {
  confirmed: ExoMinerPrediction[];
  candidates: ExoMinerPrediction[];
  false_positives: ExoMinerPrediction[];
  total: number;
  confirmed_count: number;
  candidates_count: number;
  false_positives_count: number;
}

export interface ExoMinerResults {
  // ...
  results: {
    summary: { ... };
    predictions?: ExoMinerPredictions;  // ← Ajouté
    exominer_catalog?: { ... };
    files: Array<...>;
    total_files: number;
  };
}
```

### 3. Backend - Utilisation de `build_results_table`

**Fichier:** `backend/exominer_service.py`

```python
# Import
from exominer_helper import build_results_table

# Dans get_analysis_results():
predictions_file = next((f for f in files if f['name'] == 'predictions_outputs.csv'), None)

if predictions_file and build_results_table:
    results_df = build_results_table(predictions_file['path'])
    
    predictions_data = {
        'confirmed': results_df.filter(results_df['result'] == 'Confirmed').to_dicts(),
        'candidates': results_df.filter(results_df['result'] == 'Candidate').to_dicts(),
        'false_positives': results_df.filter(results_df['result'] == 'False Positive').to_dicts(),
        'confirmed_count': len(...),
        'candidates_count': len(...),
        'false_positives_count': len(...)
    }
```

## Comment appliquer le fix

### Étape 1: Reconstruire le backend

```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

### Étape 2: Vérifier l'import

```bash
docker-compose exec backend python -c "from exominer_helper import build_results_table; print('✅ Import successful')"
```

### Étape 3: Tester avec un nouveau job

1. Upload un CSV dans l'interface ExoMiner
2. Lancer l'analyse
3. Attendre la fin (status = `completed`)
4. Cliquer sur le job → La popup s'ouvre automatiquement

## Résultat attendu

### API Response
```json
{
  "results": {
    "predictions": {
      "confirmed": [
        {"tic_id": 239332587, "result": "Confirmed", "score": 0.99966115}
      ],
      "candidates": [
        {"tic_id": 167526485, "result": "Candidate", "score": 0.64429235}
      ],
      "false_positives": [
        {"tic_id": 167526485, "result": "False Positive", "score": 0.07883153}
      ],
      "confirmed_count": 1,
      "candidates_count": 1,
      "false_positives_count": 2,
      "total": 4
    }
  }
}
```

### Interface utilisateur

**Résumé (dans la page)**:
```
┌─────────────────────────────────────┐
│ Prédictions ExoMiner [Voir détails] │
├─────────┬─────────┬─────────────────┤
│    1    │    1    │       2         │
│Confirmées│Candidates│Faux Positifs   │
└─────────┴─────────┴─────────────────┘
```

**Popup automatique**:
- S'ouvre quand on sélectionne un job complété
- Affiche 3 sections colorées
- Liste tous les TIC IDs avec leurs scores
- Fermeture par clic extérieur ou bouton X

## Vérification post-fix

```bash
# 1. Vérifier que astroquery est installé
docker-compose exec backend pip list | grep astroquery

# 2. Vérifier les logs du backend
docker-compose logs backend | grep "exominer_helper"

# 3. Tester l'API
curl http://localhost:8000/exominer/jobs/{JOB_ID}/results | jq '.results.predictions'
```

## Logs attendus

```
INFO:exominer_service:Parsing predictions_outputs.csv: exominer_work/outputs/.../predictions_outputs.csv
INFO:exominer_service:✅ Résultats parsés: 1 confirmées, 1 candidates, 2 faux positifs
```

Au lieu de:
```
WARNING:exominer_service:exominer_helper non disponible, parsing des résultats limité
```
