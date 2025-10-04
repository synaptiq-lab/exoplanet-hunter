1. Exoplanet Detection Using Machine Learning (Approche par Extraction de Caractéristiques (Feature Engineering))

Le document 2011.14135v2 se concentre sur la création d'un système de Machine Learning classique et léger (par opposition au Deep Learning) pour surpasser la méthode traditionnelle BLS (Box-fitting Least Squares) et concurrencer les modèles d'apprentissage profond en termes de performance.

La recherche s'articule autour de l'idée que pour réussir avec le ML classique, il est essentiel de fournir au modèle des caractéristiques (features) très riches extraites des courbes de lumière (séries temporelles).

• Modèle Principal : Un classifieur unique de type Gradient Boosted Tree (GBT) utilisant le framework lightGBM.

• Méthodologie Clé : 
Les étapes fondamentales sont le traitrement des données brutes (Etape i) pour assurer l'efficacité du modèle 
et l'Extraction de Caractéristiques (Étape ii), où 789 caractéristiques généralisées de séries temporelles sont calculéespour chaque courbe de lumière à l'aide de la librairie TSFresh. 

Etape i : Traiter afin d'éliminer la variabilité et le bruit de basse fréquence, et d'échantillonner la courbe uniformément dans le temps 
    1.Données Simulées (basées sur la photométrie K2 ):
        - Nettoyage initial La photométrie K2 a été obtenue et nettoyée davantage pour identifier et supprimer les artefacts de rayons cosmiques restants. Un nouveau modèle de bruit a été créé
        - Suppression de la variabilité stellaire La variabilité stellaire a été supprimée grâce à un processus itératif qui comprenait le lissage des données, leur mise en classes (binning), l'ajustement de splines cubiques, l'écrêtage des valeurs aberrantes négatives de $3\sigma$, et la répétition jusqu'à convergence
        - Interpolation des courbes de lumière K2 qui présentaient parfois des lacunes (gaps), qui ont été interpolées pour échantillonner la série temporelle uniformément.
        - Retirer tous les systèmes planétaires connus de l'échantillon de données. Toutes les courbes de lumière avec un rapport signal/bruit (S/N) supérieur à 12 ont été supprimées. Des signaux de transit ont ensuite été injectés aléatoirement dans la moitié des courbes de lumière traitées.
        - Chaque courbe de lumière avec des planètes injectées a été étiquetée comme classe '1' (candidate exoplanète), et les courbes restantes ont été classées comme classe '0' (non-candidate)
    

 Etape ii : Ces 789 caractéristiques (telles que l'énergie absolue de la série ou les coefficients de la transformée de Fourier) capturent l'information sur les caractéristiques de la courbe de lumière.


• Objectif de Performance : Prouver qu'un modèle ML classique bien conçu, basé sur des caractéristiques solides, peut être aussi performant que les modèles de Deep Learning (DL) de pointe, tout en étant beaucoup plus efficace sur le plan computationnel (moins de 5 minutes d'entraînement contre plus de 5 heures pour le DL).

Analogie : Le processus est similaire à engager un critique musical sophistiqué (TSFresh) pour analyser une mélodie bruyante (la courbe de lumière). Le critique produit un rapport détaillé (les 789 caractéristiques) sur tous les aspects de la musique (rythme, tonalité, répétitions, etc.). Ce rapport est ensuite donné à un juge unique et entraîné (GBT) qui prend la décision finale. Le succès repose sur la qualité du rapport initial fourni par le critique.

2. Papier electronics-13-03950 (Luz et al.) : L'approche par Ensemble

Le document electronics-13-03950 ne propose pas une nouvelle méthode d'extraction de caractéristiques, mais se concentre sur l'évaluation comparative de l'architecture de classification elle-même. La recherche vise à déterminer si la combinaison de plusieurs algorithmes (méthodes Ensemble) peut systématiquement améliorer la classification des exoplanètes.
• Modèles Principaux : Cinq algorithmes Ensemble clés sont évalués : Adaboost, Random Forest, Stacking, Random Subspace Method et Extremely Randomized Trees.

• Méthodologie Clé : L'évaluation est comparative et repose sur le réglage fin (tuning) des hyperparamètres de chaque architecture Ensemble (par exemple, augmenter le nombre d'estimateurs ou ajuster le taux d'apprentissage) pour déterminer leur performance maximale sur le jeu de données KOI. Le jeu de données KOI est utilisé pour l'entraînement.
• Objectif de Performance : Démontrer que les algorithmes Ensemble sont supérieurs aux algorithmes traditionnels utilisés comme estimateurs.

Analogie de la recherche electronics-13-03950 (Luz et al.) : Le processus est comme réunir un Comité d'Experts (les algorithmes Ensemble). Au lieu de s'appuyer sur un seul type de jugement, le système combine des jugements multiples et diversifiés pour compenser les erreurs individuelles. Le modèle Stacking, par exemple, est le chef d'orchestre de ce comité : il reçoit les prédictions brutes de plusieurs experts (qui deviennent de nouvelles données d'entraînement) et utilise un méta-modèle pour déterminer la meilleure façon de fusionner ces prédictions, aboutissant à une décision collective plus fiable.

