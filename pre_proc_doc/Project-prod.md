# Détection d’exoplanètes — **Fusion méthodologique LightGBM (features TSFresh) + Ensembles (bagging/stacking)**

Document destiné à guider une **implémentation complémentaire** et **cohérente** des deux approches issues :  
 1) de *Malik et al.* « Exoplanet Detection using Machine Learning » (LightGBM + TSFresh), et  
 2) de *Luz et al.* « Assessment of Ensemble-Based ML Algorithms for Exoplanet Identification » (bagging/stacking sur KOI).  
 
 La pipeline ci-dessous harmonise **le pré-processing** (en une section unique) puis **la modélisation** (deux familles de modèles compatibles), afin de **tester et comparer** proprement ces méthodes dans un ordre logique, sans mélanger des étapes incompatibles.  
 
 Sources principales : Malik et al. 2021 (arXiv) ; Luz et al. 2024 (Electronics).  
 Références outils : TSFresh ; LightGBM (NIPS).

---

## 1) Objectif & périmètre

- **But** : produire un pipeline réplicable qui permette de **tester deux familles complémentaires** :
  - **Méthode A – LightGBM + TSFresh** (features extraites des **courbes de lumière** → modèle **Gradient Boosted Trees** léger). Issue de Malik et al.
  - **Méthode B – Ensembles (bagging/stacking)** sur **données tabulaires** (type KOI), avec **Random Forest (bagging)**, **ExtraTrees**, **AdaBoost** et **Stacking**. Issue de Luz et al.
- **Principe de compatibilité** :  
  Les deux approches **aboutissent à une matrice de features tabulaires** (X) + labels (y). On **ne mélange pas** leurs prétraitements *incompatibles*, mais on **aligne les sorties** pour comparer les modèles **sur un même format**.
- **Cas d’usage** :
  - Vous disposez **soit** de **courbes de lumière** (TESS/Kepler/K2) → utilisez **Pré-proc A** (sections 2.1–2.2) puis testez **modèles A et B** sur les **features TSFresh** (parfaitement compatibles avec LightGBM, RF, ExtraTrees, Stacking).
  - Vous disposez **soit** d’un **CSV KOI** (données tabulaires) → utilisez **Pré-proc B** (section 2.3) puis testez **modèles B** (et, si souhaité, LightGBM aussi, car c’est un GBDT sur tabulaire).

---

## 2) Pré-processing **unifié** (choisir la branche adaptée aux données d’entrée)

 **Sortie attendue dans tous les cas** :  
 `X` = DataFrame numérique (features), `y` = vecteur de labels binaires/multi-classes, **split CV** propre, **scaling** cohérent.

### 2.1. Pré-proc A — **Courbes de lumière** (d’après Malik et al.)

1) **Nettoyage photométrique & variabilité stellaire**  
   - Suppression artéfacts (cosmic rays), lissage, binning, **splines cubiques**, **clip** des outliers négatifs (-3σ), itératif jusqu’à convergence.  
   - **Resampling uniforme** (fenêtre **1h**) + **interpolation** des gaps.  

2) (**Option simulation**)  
   - Retirer systèmes connus, filtrer S/N > 12, **injecter** des transits aléatoires (moitié des courbes) → labellisation binaire.

3) **Extraction de features TSFresh**  
   - **789 caractéristiques** (énergie absolue, nb valeurs > moyenne, **coefficients FFT**, etc.).  
   - Nettoyage des features : colonnes constantes out, imputation NA, **RobustScaler**.

4) **Split CV**  
   - **K-fold (k=10)**, stratifié, avec un **jeu test hold-out** séparé.  
   - Optimiser AUC puis fixer un **seuil** pour **prioriser recall**.

---

### 2.2. **Sortie du Pré-proc A → Format tabulaire**  

- **X** = matrice (≈ 700–790 colonnes) ; **y** = {0/1}.  
- Compatible **LightGBM** + **RF/ExtraTrees/Stacking**.

---

### 2.3. Pré-proc B — **Données KOI (tabulaires)** (d’après Luz et al.)

1) **Chargement** du KOI `cumulative.csv` et **nettoyage colonnes** (identifiants, doublons, NA).  
2) **Classes** : confirmed vs candidate (false positives retirés).  
3) **Traitement NA & encodage** → StandardScaler.  
4) **Validation** : **K-fold (k=10)**, métriques multiples (accuracy, recall, specificity, precision, F1).

---

## 3) Modélisation

### 3.1. Méthode A — **LightGBM sur features TSFresh**

- **Algorithme** : Gradient Boosted Trees (LightGBM).  
- **HP clés** : `num_leaves`, `max_depth`, `learning_rate`, `n_estimators`.  
- **Optimisation** : AUC → fixer seuil pour recall.  
- **Performance publiée** : AUC ≈ 0.948, recall ≈ 0.96 (Kepler).

### 3.2. Méthode B — **Ensembles : bagging & stacking**

- **Bagging** = RF, ExtraTrees ; **Boosting** = AdaBoost.  
- **Stacking** = méta-modèle (LogisticRegression) combinant plusieurs learners.  
- **Résultats publiés** : >80% sur KOI, stacking meilleur.

---

## 4) Ordre de mise en œuvre

1) Pré-proc A (courbes) → TSFresh → `X_ts`, `y`.  
2) Pré-proc B (KOI) → `X_koi`, `y`.  
3) Entraînement :  
   - LightGBM (A1).  
   - RF/ExtraTrees/AdaBoost (B1).  
   - Stacking (B2).  
4) Comparaison via matrices de confusion, PR-curve.  

---

## 5) Notes pratiques

- **TSFresh** : `extract_features()` ; possibilité de réduire via relevance table.  
- **Scaling** : RobustScaler (TSFresh), StandardScaler (KOI).  
- **Validation** : StratifiedKFold(k=10).  

---

## 6) Compatibilité des deux approches

- **Entrées différentes, sortie commune tabulaire**.  
- **LightGBM** rapide, interprétable.  
- **Bagging/Stacking** robustes, complémentaires.  

---

## 7) Réglages conseillés

- **LightGBM** : `lr=0.05–0.1`, `n_estimators=500–1500`, `feature_fraction=0.7–1.0`.  
- **RF/ExtraTrees** : `n_estimators≥500`, `max_features=sqrt`.  
- **AdaBoost** : tuning n_estimators/learning_rate.  
- **Stacking** : base learners divers (RF+LGBM+GB).

---

## 8) Références

- Malik et al. (2021), *Exoplanet Detection using Machine Learning*.  
- Luz et al. (2024), *Assessment of Ensemble-Based ML Algorithms for Exoplanet Identification*.  
- TSFresh documentation.  
- LightGBM paper (NIPS).
