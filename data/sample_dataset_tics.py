import polars as pl

# Charger le fichier CSV d'origine
df = pl.read_csv("exominer-tics-with-sectors.csv")

# Sélectionner 50 lignes aléatoires
sample_df = df.sample(n=50, with_replacement=False, shuffle=True, seed=79)

# Sauvegarder le résultat dans un nouveau CSV
sample_df.write_csv("sample_50.csv")

print("Fichier 'sample_50.csv' cree avec 50 exemples aleatoires.")
