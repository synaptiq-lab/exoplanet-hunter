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
    # tics = (
    #     pl.scan_csv("../data/lc_targets_filtered.csv")
    #     .select("tic")
    #     .collect()
    #     .get_column("tic")
    # )
    #
    # df = keep_tics_with_lc(tics)
    # df.write_parquet("../data/tics-with-sectors.parquet")
    # print(df)

    # Get the best disposition between both TOI datasets
    toi_catalog_df = pl.scan_csv("../data/toi-catalog.csv").select(["TIC", "TOI Disposition"])
    toi_nasa_df = (
        pl.scan_csv("../data/nasa-datasets/TOI_2025.10.04_01.44.44.csv")
        .select(["tid", "tfopwg_disp"])
        .rename({"tid": "TIC", "tfopwg_disp": "TOI Disposition"})
    )

    # Define priority mapping (lower number = higher priority)
    priority = ["KP", "APC", "PC", "CP", "FP", "EB", "FA"]
    priority_map = {val: idx for idx, val in enumerate(priority)}

    result = (
        toi_nasa_df
        .join(toi_catalog_df, on="TIC", how="full")
        .with_columns([
            pl.col("TOI Disposition").replace(priority_map).alias("priority_left"),
            pl.col("TOI Disposition_right").replace(priority_map).alias("priority_right")
        ])
        .with_columns(
            pl.when(pl.col("priority_left").is_null())
            .then(pl.col("TOI Disposition_right"))
            .when(pl.col("priority_right").is_null())
            .then(pl.col("TOI Disposition"))
            .when(pl.col("priority_left") <= pl.col("priority_right"))
            .then(pl.col("TOI Disposition"))
            .otherwise(pl.col("TOI Disposition_right"))
            .alias("TOI Disposition")
        )
        .drop(["TIC_right", "TOI Disposition_right", "priority_left", "priority_right"])
        .collect()
    )

    result.write_parquet("../data/tess-analyzed.parquet")
    print(result.sample(10))