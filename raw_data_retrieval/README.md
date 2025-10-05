# 🌌 Raw Data Retrieval

Récupération des données bruts sur https://archive.stsci.edu/tess/bulk_downloads/bulk_downloads_ffi-tp-lc-dv.html

## 🎯 Ordre d'exécution

- **Notebook get_time_series** : Lancer toutes les cellules pour obtenir les fichiers fits
- **python test_fits.py** (Optionnel) : Extraire le contenu d'un des fichiers fits obtenus
- **python test_single_file.py** (Optionnel) : Tester la mise en CSV des données d'un fichier fits
- **python get_csv_from_fits.py** : Récupération par batch des données de l'ensemble des fichiers fits (WIP: risque de crash)
- **python merge_batches.py** : Merge de tout les batch.csv en un seul fichier CSV avec toutes les données