"""Preprocess `data/drugs.csv` into exploded lists and numeric counts.

Writes `data/drugs_processed.parquet` and `data/drug_lookup.csv`.
"""
from pathlib import Path
import pandas as pd


def parse_multi(cell):
    if pd.isna(cell):
        return []
    return [s.strip() for s in str(cell).split(";") if s.strip()]


def main():
    base = Path(__file__).resolve().parents[1]
    data_dir = base / "data"
    drugs_csv = data_dir / "drugs.csv"
    out_parquet = data_dir / "drugs_processed.parquet"
    out_csv = data_dir / "drugs_processed.csv"
    lookup_csv = data_dir / "drug_lookup.csv"

    if not drugs_csv.exists():
        raise FileNotFoundError(drugs_csv)

    df = pd.read_csv(drugs_csv)

    # Ensure columns exist
    for col in ["targets", "enzymes", "transporters", "pathways", "side_effects"]:
        if col not in df.columns:
            df[col] = ""

    df["targets_list"] = df["targets"].apply(parse_multi)
    df["enzymes_list"] = df["enzymes"].apply(parse_multi)
    df["transporters_list"] = df["transporters"].apply(parse_multi)
    df["pathways_list"] = df["pathways"].apply(parse_multi)
    df["side_effects_list"] = df["side_effects"].apply(parse_multi)

    df["target_count"] = df["targets_list"].apply(len)
    df["enzyme_count"] = df["enzymes_list"].apply(len)
    df["transporter_count"] = df["transporters_list"].apply(len)
    df["pathway_count"] = df["pathways_list"].apply(len)
    df["side_effect_count"] = df["side_effects_list"].apply(len)

    # Keep canonical id and name
    df["canonical_id"] = df["drug_id"]
    df["canonical_name"] = df["drug_name"]

    out_cols = [
        "canonical_id",
        "canonical_name",
        "half_life",
        "targets_list",
        "enzymes_list",
        "transporters_list",
        "pathways_list",
        "side_effects_list",
        "target_count",
        "enzyme_count",
        "transporter_count",
        "pathway_count",
        "side_effect_count",
    ]

    df_out = df[out_cols].copy()

    # write CSV (parquet optional)
    try:
        df_out.to_parquet(out_parquet, index=False)
        print(f"Wrote processed drugs to {out_parquet}")
    except Exception:
        df_out.to_csv(out_csv, index=False)
        print(f"Wrote processed drugs to {out_csv}")

    # create lookup CSV: canonical_name -> canonical_id
    df[["canonical_id", "canonical_name"]].to_csv(lookup_csv, index=False)

    print(f"Wrote lookup to {lookup_csv}")
    print(f"Wrote lookup to {lookup_csv}")


if __name__ == "__main__":
    main()
