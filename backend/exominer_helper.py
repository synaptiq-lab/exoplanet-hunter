from astroquery.mast import Observations
import polars as pl


def format_inputs(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.explode("sectors")
        .with_columns(pl.format("{}-{}", pl.col("sectors"), pl.col("sectors")).alias("sector_run"))
        .select(["tic_id", "sector_run"])
    )


def get_sectors_from_tic(tic: int) -> list[int]:
    try:
        obs = Observations.query_criteria(
            provenance_name="TESS-SPOC",
            target_name=tic
        )
    except Exception:
        return []

    if len(obs) > 0:
        return [int(x) for x in list(obs["sequence_number"])]

    return []


def build_results_table(path_to_predictions_csv: str) -> pl.DataFrame:
    predictions_df = (
        pl.scan_csv(path_to_predictions_csv)
        .select(["target_id", "score"])
        .group_by("target_id")
        .agg(pl.col("score").max())
        .with_columns(
            pl.when(pl.col("score") <= 0.5).then(pl.lit("False positive"))
            .when(pl.col("score") <= 0.9).then(pl.lit("Planetary candidate"))
            .otherwise(pl.lit("Confirmed planet"))
            .alias("result")
        )
        .rename({"target_id": "tic_id"})
        .select(["tic_id", "result", "score"])
    )

    tess_analyzed_df = (
        pl.scan_parquet("data/tess-analyzed.parquet")
        .rename({"TIC": "tic_id", "TOI Disposition": "official_disposition"})
    )

    results_df = (
        predictions_df.join(tess_analyzed_df, on="tic_id")
        .with_columns(
            pl.col("official_disposition").fill_null("Not officially analyzed yet")
        )
    )

    return results_df.collect()


if __name__ == "__main__":
    # print(build_results_table("../data/predictions_outputs.csv"))
    # print(get_sectors_from_tic(51432))
    unformatted_inputs_df = pl.scan_parquet("../data/tics-with-sectors.parquet").head(3).collect()
    print(format_inputs(unformatted_inputs_df))
