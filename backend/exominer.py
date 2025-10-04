from astroquery.mast import Observations
import polars as pl


def keep_tics_with_lc(tics: pl.Series | list[int]) -> pl.DataFrame:
    """Keeps only TICs with light curves by querying Astroquery, and get sectors."""
    results = []
    for tic_id in tics:
        try:
            obs = Observations.query_criteria(
                provenance_name="TESS-SPOC",
                target_name=tic_id
            )
        except Exception:
            print("Couldn't query TIC", tic_id)
            continue

        if len(obs) > 0:
            results.append({
                "tic": tic_id,
                "sectors": list(obs["sequence_number"])
            })
            print(f"TIC {tic_id}, Sectors: {list(obs["sequence_number"])}")

    return pl.from_dicts(results)


if __name__ == "__main__":
    tics = (
        pl.scan_csv("../data/lc_targets_filtered.csv")
        .select("tic")
        .collect()
        .get_column("tic")
    )

    df = keep_tics_with_lc(tics)
    df.write_parquet("../data/tics-with-sectors.parquet")
    print(df)
