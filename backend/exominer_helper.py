from astroquery.mast import Observations
import polars as pl


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


def build_results_table(path_to_result_csv: str) -> pl.DataFrame:
     return (
        pl.scan_csv(path_to_result_csv)
        .select(["target_id", "score"])
        .group_by("target_id")
        .agg(pl.col("score").max())
        .with_columns(
            pl.when(pl.col("score") <= 0.5).then(pl.lit("False Positive"))
            .when(pl.col("score") <= 0.9).then(pl.lit("Candidate"))
            .otherwise(pl.lit("Confirmed"))
            .alias("result")
        )
        .rename({"target_id": "tic"})
        .select(["tic", "result", "score"])
        .collect()
    )


if __name__ == "__main__":
    # print(build_results_table("../data/predictions_outputs.csv"))
    print(get_sectors_from_tic(51432))
