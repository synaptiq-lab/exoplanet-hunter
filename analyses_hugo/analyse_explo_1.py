#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDA minimaliste (Polars-first) centrée sur:
1) Comprendre les données: structure, types, valeurs manquantes, distributions
2) Détecter les problèmes: outliers (IQR), duplicats, déséquilibre de classes
3) Relations entre variables: corrélations et redondances (paires très corrélées)

Entrées (par défaut):
  - datasets/KOI.csv
  - datasets/TOI.csv
Sorties:
  - analyses_hugo/outputs/tables/*.csv
  - analyses_hugo/outputs/figures/*.png
  - analyses_hugo/outputs/report.md
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

import importlib

# Polars prioritaire
pl: Any
POLARS_AVAILABLE = True
try:
    pl = importlib.import_module("polars")  # type: ignore[assignment]
except Exception:
    POLARS_AVAILABLE = False
    pl = None

# Fallback vers pandas si Polars absent
pd: Any
try:
    pd = importlib.import_module("pandas")  # type: ignore[assignment]
except Exception:
    pd = None

# Plot (histos, heatmap)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # type: ignore


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def sniff_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        return dialect.delimiter
    except Exception:
        return ","


def read_csv_polars(path: str) -> Tuple[Any, Dict[str, str]]:
    if not POLARS_AVAILABLE:
        raise RuntimeError("Polars n'est pas installé.")
    # Sniff séparateur sur un échantillon
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(64 * 1024)
    sep = sniff_delimiter(head)
    for enc in ("utf8", "utf8-lossy"):
        try:
            df = pl.read_csv(
                path,
                separator=sep,
                encoding=enc,
                infer_schema_length=5000,
                ignore_errors=True,
            )
            return df, {"engine": "polars", "encoding": enc, "separator": sep}
        except Exception:
            continue
    raise RuntimeError("Impossible de lire le CSV avec Polars")


def read_csv_pandas_then_to_polars(path: str) -> Tuple[Any, Dict[str, str]]:
    if pd is None:
        raise RuntimeError("Ni Polars ni Pandas disponibles.")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(64 * 1024)
    sep = sniff_delimiter(head)
    df_pd = pd.read_csv(path, sep=sep, on_bad_lines="skip")
    if POLARS_AVAILABLE:
        return pl.from_pandas(df_pd), {"engine": "pandas->polars", "separator": sep}  # type: ignore[attr-defined]
    return df_pd, {"engine": "pandas", "separator": sep}


def get_numeric_columns(df: Any) -> List[str]:
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        return [c for c, dt in zip(df.columns, df.dtypes) if pl.datatypes.is_numeric(dt)]
    return [c for c in df.columns if str(df[c].dtype).startswith(("int", "float"))]


def get_categorical_columns(df: Any, max_unique: int = 50) -> List[str]:
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        cats: List[str] = []
        for c, dt in zip(df.columns, df.dtypes):
            if pl.datatypes.is_utf8(dt) or pl.datatypes.is_boolean(dt):
                n_unique = int(df.select(pl.col(c).n_unique()).item())
                if n_unique <= max_unique:
                    cats.append(c)
        return cats
    cat_cols_pd: List[str] = []
    for c in df.columns:
        if str(df[c].dtype) in ("object", "bool"):
            nunique = int(df[c].nunique(dropna=True))
            if nunique <= max_unique:
                cat_cols_pd.append(c)
    return cat_cols_pd


def schema_and_missing(df: Any) -> Any:
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        rows: List[Dict[str, Any]] = []
        n = df.height
        for c, dt in zip(df.columns, df.dtypes):
            nulls = int(df.select(pl.col(c).is_null().sum()).item())
            rows.append({"column": c, "dtype": str(dt), "null_count": nulls, "null_pct": (nulls / n) if n else 0.0})
        return pl.DataFrame(rows)
    total = len(df)
    rows = []
    for c in df.columns:
        nulls = int(df[c].isna().sum())
        rows.append({"column": c, "dtype": str(df[c].dtype), "null_count": nulls, "null_pct": (nulls / total) if total else 0.0})
    return pd.DataFrame(rows)


def numeric_distributions(df: Any, numeric_cols: Sequence[str]) -> Any:
    qs = [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0]
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        out_rows: List[Dict[str, Any]] = []
        for c in numeric_cols:
            desc = df.select([
                pl.col(c).count().alias("count"),
                pl.col(c).mean().alias("mean"),
                pl.col(c).std().alias("std"),
                pl.col(c).min().alias("min"),
                pl.col(c).max().alias("max"),
            ]).to_dicts()[0]
            quants = df.select(pl.col(c).quantile(qs)).to_series().to_list()
            row = {"column": c, **desc}
            for q, val in zip(qs, quants):
                row[f"q{int(q*100):02d}"] = val
            out_rows.append(row)
        return pl.DataFrame(out_rows)
    rows = []
    for c in numeric_cols:
        s = df[c]
        desc = {
            "count": int(s.count()),
            "mean": float(s.mean()) if s.count() else None,
            "std": float(s.std()) if s.count() else None,
            "min": float(s.min()) if s.count() else None,
            "max": float(s.max()) if s.count() else None,
        }
        quants = s.quantile(qs).values.tolist()
        row = {"column": c, **desc}
        for q, val in zip(qs, quants):
            row[f"q{int(q*100):02d}"] = val
        rows.append(row)
    return pd.DataFrame(rows)


def outliers_iqr(df: Any, numeric_cols: Sequence[str]) -> Any:
    rows: List[Dict[str, Any]] = []
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        n = df.height
        for c in numeric_cols:
            q1 = df.select(pl.col(c).quantile(0.25)).item()
            q3 = df.select(pl.col(c).quantile(0.75)).item()
            if q1 is None or q3 is None:
                rows.append({"column": c, "lower": None, "upper": None, "outliers": 0, "outlier_pct": 0.0})
                continue
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            cnt = int(df.select(((pl.col(c) < lower) | (pl.col(c) > upper)).sum()).item())
            rows.append({"column": c, "lower": lower, "upper": upper, "outliers": cnt, "outlier_pct": (cnt / n) if n else 0.0})
        return pl.DataFrame(rows)
    n = len(df)
    for c in numeric_cols:
        q1 = df[c].quantile(0.25)
        q3 = df[c].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        cnt = int(((df[c] < lower) | (df[c] > upper)).sum())
        rows.append({"column": c, "lower": lower, "upper": upper, "outliers": cnt, "outlier_pct": (cnt / n) if n else 0.0})
    return pd.DataFrame(rows)


def duplicates_summary(df: Any) -> Dict[str, Any]:
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        n = df.height
        n_unique_rows = int(df.unique().height)
        dup_count = n - n_unique_rows
        sample = None
        if dup_count > 0:
            sample = (
                df.with_row_count()
                  .groupby(df.columns)
                  .len()
                  .filter(pl.col("len") > 1)
                  .limit(50)
            )
        return {"total": n, "duplicates": dup_count, "sample": sample}
    n = len(df)
    dup_mask = df.duplicated(keep=False)
    dup_count = int(dup_mask.sum())
    sample = df[dup_mask].head(50) if dup_count > 0 else None
    return {"total": n, "duplicates": dup_count, "sample": sample}


def class_imbalance(df: Any, categorical_cols: Sequence[str]) -> Any:
    rows: List[Dict[str, Any]] = []
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        for c in categorical_cols:
            vc = df.group_by(c).len().sort("len", descending=True)
            total = int(vc.select(pl.col("len").sum()).item())
            if total == 0:
                continue
            top = vc.row(0)
            top_label = top[0]
            top_count = int(top[1])
            rows.append({"column": c, "top_value": str(top_label), "top_count": top_count, "top_pct": top_count / total})
        return pl.DataFrame(rows)
    for c in categorical_cols:
        vc = df[c].value_counts(dropna=True)
        total = int(vc.sum())
        if total == 0:
            continue
        rows.append({"column": c, "top_value": str(vc.index[0]), "top_count": int(vc.iloc[0]), "top_pct": int(vc.iloc[0]) / total})
    return pd.DataFrame(rows)


def correlations(df: Any, numeric_cols: Sequence[str]) -> Tuple[Any, Optional[str]]:
    if len(numeric_cols) == 0:
        return (pl.DataFrame([]) if POLARS_AVAILABLE else pd.DataFrame()), None
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        if pd is None:
            return pl.DataFrame([]), None
        corr = df.select(numeric_cols).to_pandas().corr(method="pearson")  # type: ignore[attr-defined]
        return pl.from_pandas(corr), "pandas"  # type: ignore[attr-defined]
    corr = df[numeric_cols].corr(method="pearson")
    return corr, "pandas"


def high_correlation_pairs(corr_df: Any, threshold: float = 0.9) -> Any:
    if POLARS_AVAILABLE and isinstance(corr_df, pl.DataFrame):
        cols = list(corr_df.columns)
        rows: List[Dict[str, Any]] = []
        pdf = corr_df.to_pandas()  # type: ignore[attr-defined]
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                r = pdf.iloc[i, j]
                if r is not None and abs(r) >= threshold:
                    rows.append({"var1": cols[i], "var2": cols[j], "corr": float(r)})
        return pl.DataFrame(rows)
    cols = list(corr_df.columns)
    rows = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr_df.iloc[i, j]
            if r is not None and abs(r) >= threshold:
                rows.append({"var1": cols[i], "var2": cols[j], "corr": float(r)})
    return pd.DataFrame(rows)


def save_table(df_any: Any, path: str) -> None:
    ensure_dir(os.path.dirname(path))
    if POLARS_AVAILABLE and hasattr(df_any, "write_csv"):
        df_any.write_csv(path)
    else:
        df_any.to_csv(path, index=False)


def save_histograms(df: Any, numeric_cols: Sequence[str], out_dir: str, max_plots: int = 8, name_prefix: str = "") -> List[str]:
    ensure_dir(out_dir)
    paths: List[str] = []
    # Sélection par variance décroissante
    variances: List[Tuple[str, float]] = []
    if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        for c in numeric_cols:
            try:
                var_val = df.select(pl.col(c).var()).item()
                if var_val is None:
                    continue
                variances.append((c, float(var_val)))
            except Exception:
                continue
    else:
        for c in numeric_cols:
            try:
                variances.append((c, float(df[c].var())))
            except Exception:
                continue
    variances.sort(key=lambda kv: kv[1], reverse=True)
    for c, _ in variances[:max_plots]:
        fig, ax = plt.subplots(figsize=(6, 4))
        try:
            data = df[c].drop_nulls().to_numpy() if POLARS_AVAILABLE and isinstance(df, pl.DataFrame) else df[c].dropna().values
            ax.hist(data, bins=50, color="#4a90e2", alpha=0.85)
            ax.set_title(f"Histogramme: {c}")
            ax.set_xlabel(c)
            ax.set_ylabel("Fréquence")
            fig.tight_layout()
            prefix = f"{name_prefix}_" if name_prefix else ""
            out_path = os.path.join(out_dir, f"{prefix}hist_{c}.png")
            fig.savefig(out_path, dpi=140)
            paths.append(out_path)
        finally:
            plt.close(fig)
    return paths


def save_barplots(df: Any, categorical_cols: Sequence[str], out_dir: str, top_k: int = 15, name_prefix: str = "") -> List[str]:
    ensure_dir(out_dir)
    paths: List[str] = []
    for c in categorical_cols:
        try:
            if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
                vc = df.group_by(c).len().sort("len", descending=True).limit(top_k)
                labels = [str(row[0]) for row in vc.iter_rows()]
                values = [int(row[1]) for row in vc.iter_rows()]
            else:
                vc = df[c].value_counts(dropna=True).head(top_k)
                labels = [str(x) for x in vc.index.tolist()]
                values = [int(x) for x in vc.values.tolist()]
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.barh(range(len(values)), values, color="#7b9acc")
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels, fontsize=8)
            ax.invert_yaxis()
            ax.set_title(f"Top catégories: {c}")
            ax.set_xlabel("Comptes")
            fig.tight_layout()
            prefix = f"{name_prefix}_" if name_prefix else ""
            safe_c = c.replace("/", "_").replace("\\", "_")
            out_path = os.path.join(out_dir, f"{prefix}bar_{safe_c}.png")
            fig.savefig(out_path, dpi=140)
            paths.append(out_path)
        finally:
            plt.close(fig)
    return paths


def save_corr_heatmap(corr_df_any: Any, out_path: str, name_prefix: str = "") -> Optional[str]:
    ensure_dir(os.path.dirname(out_path))
    try:
        if POLARS_AVAILABLE and isinstance(corr_df_any, pl.DataFrame):
            corr_pd = corr_df_any.to_pandas()  # type: ignore[attr-defined]
        else:
            corr_pd = corr_df_any
        if corr_pd is None or corr_pd.empty:
            return None
        fig, ax = plt.subplots(figsize=(9, 7))
        im = ax.imshow(corr_pd.values, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr_pd.columns)))
        ax.set_yticks(range(len(corr_pd.index)))
        ax.set_xticklabels(corr_pd.columns, rotation=90, fontsize=7)
        ax.set_yticklabels(corr_pd.index, fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        base_dir = os.path.dirname(out_path)
        base_name = os.path.basename(out_path)
        if name_prefix:
            base_name = f"{name_prefix}_" + base_name
        final_path = os.path.join(base_dir, base_name)
        fig.savefig(final_path, dpi=150)
        plt.close(fig)
        return final_path
    except Exception:
        return None


def generate_report(out_dir: str, name: str, artifacts: Dict[str, str]) -> str:
    ensure_dir(out_dir)
    path = os.path.join(out_dir, "report.md")
    lines: List[str] = []
    lines.append(f"# EDA Polars — {name}\n\n")
    lines.append("## 1) Comprendre les données\n")
    lines.append("- Table: `tables/schema_summary.csv`\n")
    lines.append("- Distributions numériques: `tables/numeric_summary.csv`\n\n")
    lines.append("## 2) Détecter les problèmes\n")
    lines.append("- Outliers IQR: `tables/outliers_iqr_summary.csv`\n")
    lines.append("- Duplicats (échantillon si présent): `tables/duplicates_sample.csv`\n")
    lines.append("- Déséquilibre de classes: `tables/class_balance_summary.csv`\n\n")
    lines.append("## 3) Relations\n")
    lines.append("- Corrélations: `tables/corr_matrix.csv`\n")
    lines.append("- Paires très corrélées: `tables/high_correlation_pairs.csv`\n")
    if artifacts.get("corr_heatmap"):
        rel = os.path.relpath(artifacts["corr_heatmap"], out_dir).replace("\\", "/")
        lines.append(f"- Heatmap: ![]({rel})\n")
    if artifacts.get("histo_one"):
        relh = os.path.relpath(artifacts["histo_one"], out_dir).replace("\\", "/")
        lines.append(f"- Exemple histogramme: ![]({relh})\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    return path


def process_one(name: str, path: str, out_root: str) -> Dict[str, List[str]]:
    print(f"Lecture {name}: {path}")
    tables_dir = os.path.join(out_root, "tables")
    figs_dir = os.path.join(out_root, "figures")
    ensure_dir(tables_dir)
    ensure_dir(figs_dir)

    try:
        df, meta = read_csv_polars(path)
    except Exception:
        df, meta = read_csv_pandas_then_to_polars(path)
    print(f"Lecture params: {meta}")

    schema_df = schema_and_missing(df)
    save_table(schema_df, os.path.join(tables_dir, "schema_summary.csv"))

    num_cols = get_numeric_columns(df)
    num_summary = numeric_distributions(df, num_cols)
    save_table(num_summary, os.path.join(tables_dir, "numeric_summary.csv"))

    out_iqr = outliers_iqr(df, num_cols)
    save_table(out_iqr, os.path.join(tables_dir, "outliers_iqr_summary.csv"))

    dups = duplicates_summary(df)
    if dups.get("sample") is not None:
        sample = dups["sample"]
        sample_path = os.path.join(tables_dir, "duplicates_sample.csv")
        if POLARS_AVAILABLE and isinstance(sample, pl.DataFrame):
            sample.write_csv(sample_path)
        else:
            sample.to_csv(sample_path, index=False)

    cat_cols = get_categorical_columns(df, max_unique=20)
    class_imb = class_imbalance(df, cat_cols)
    save_table(class_imb, os.path.join(tables_dir, "class_balance_summary.csv"))

    corr_df, _ = correlations(df, num_cols)
    save_table(corr_df, os.path.join(tables_dir, "corr_matrix.csv"))
    high_pairs = high_correlation_pairs(corr_df, threshold=0.9)
    save_table(high_pairs, os.path.join(tables_dir, "high_correlation_pairs.csv"))

    hist_paths = save_histograms(df, num_cols, figs_dir, max_plots=16, name_prefix=name)
    bar_paths = save_barplots(df, cat_cols, figs_dir, top_k=15, name_prefix=name)
    heatmap_path = save_corr_heatmap(corr_df, os.path.join(figs_dir, "corr_heatmap.png"), name_prefix=name)

    artifacts = {
        "corr_heatmap": heatmap_path or "",
        "histo_one": hist_paths[0] if hist_paths else "",
    }
    report_path = generate_report(out_root, name, artifacts)
    print(f"Fini {name}. Rapport: {report_path}")
    all_figs: List[str] = []
    if heatmap_path:
        all_figs.append(heatmap_path)
    all_figs.extend(hist_paths)
    all_figs.extend(bar_paths)
    return {"figs": all_figs}


def generate_report_all(out_dir: str, per_dataset_figs: Dict[str, List[str]]) -> str:
    ensure_dir(out_dir)
    path = os.path.join(out_dir, "report_all.md")
    lines: List[str] = []
    lines.append("# Toutes les figures — KOI & TOI\n\n")
    for dataset_name, fig_paths in per_dataset_figs.items():
        lines.append(f"## {dataset_name}\n\n")
        for p in fig_paths:
            rel = os.path.relpath(p, out_dir).replace("\\", "/")
            lines.append(f"![]({rel})\n\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    return path


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="EDA minimaliste (Polars-first): structure, problèmes, relations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--koi", default=os.path.join("datasets", "KOI.csv"), help="Chemin KOI.csv")
    p.add_argument("--toi", default=os.path.join("datasets", "TOI.csv"), help="Chemin TOI.csv")
    p.add_argument("--out", default=os.path.join("analyses_hugo", "outputs"), help="Dossier de sortie")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    missing = [p for p in [args.koi, args.toi] if not os.path.isfile(p)]
    if missing:
        print("Fichiers introuvables:")
        for m in missing:
            print(f" - {m}")
        return 2

    ensure_dir(args.out)
    try:
        koi_art = process_one("KOI", args.koi, args.out)
        toi_art = process_one("TOI", args.toi, args.out)
        per_dataset = {
            "KOI": koi_art.get("figs", []),
            "TOI": toi_art.get("figs", []),
        }
        all_path = generate_report_all(args.out, per_dataset)
        print(f"Rapport complet: {all_path}")
    except Exception as exc:
        print("Erreur pendant l'analyse:", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
