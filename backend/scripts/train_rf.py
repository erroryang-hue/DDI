"""Train a RandomForest classifier on ddi_dataset.csv and save the model.

Features used:
- enzyme_overlap
- target_overlap
- pathway_overlap
- transporter_overlap
- side_effect_overlap

Target: interaction

Saves model to `models/rf_model.pkl` and prints accuracy.
"""
from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    data_path = base / "ddi_dataset.csv"
    models_dir = base / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)

    # If overlap features aren't present, compute them from data/drugs.csv
    data_dir = base / "data"
    drugs_csv = data_dir / "drugs.csv"
    if not drugs_csv.exists():
        raise FileNotFoundError(f"Reference drugs.csv not found: {drugs_csv}")

    drugs_df = pd.read_csv(drugs_csv)

    # build lookup by drug_name (and fallback to drug_id)
    def _parse_set(cell):
        if pd.isna(cell):
            return set()
        if isinstance(cell, (int, float)):
            return set()
        return set([s.strip() for s in str(cell).split(";") if s.strip()])

    lookup = {}
    for _, r in drugs_df.iterrows():
        name = str(r.get("drug_name") or r.get("drug_id"))
        lookup[name] = {
            "enzymes": _parse_set(r.get("enzymes", "")),
            "targets": _parse_set(r.get("targets", "")),
            "pathways": _parse_set(r.get("pathways", "")),
            "transporters": _parse_set(r.get("transporters", "")),
            "side_effects": _parse_set(r.get("side_effects", "")),
        }

    def jaccard(a, b):
        if not a and not b:
            return 0.0
        inter = a.intersection(b)
        union = a.union(b)
        return len(inter) / len(union) if union else 0.0

    # compute overlap columns if missing
    overlap_cols = {
        "enzyme_overlap": ("enzymes",),
        "target_overlap": ("targets",),
        "pathway_overlap": ("pathways",),
        "transporter_overlap": ("transporters",),
        "side_effect_overlap": ("side_effects",),
    }

    for col, keys in overlap_cols.items():
        if col not in df.columns:
            values = []
            for _, row in df.iterrows():
                d1 = str(row.get("drug1"))
                d2 = str(row.get("drug2"))
                a = lookup.get(d1, {}).get(keys[0], set())
                b = lookup.get(d2, {}).get(keys[0], set())
                values.append(jaccard(a, b))
            df[col] = values

    features = [
        "enzyme_overlap",
        "target_overlap",
        "pathway_overlap",
        "transporter_overlap",
        "side_effect_overlap",
    ]

    for f in features:
        if f not in df.columns:
            raise KeyError(f"Required feature column missing: {f}")

    # Derive target 'interaction' if missing: prefer 'risk_score' threshold, fallback to 'severity'
    if "interaction" not in df.columns:
        if "risk_score" in df.columns:
            df["interaction"] = (df["risk_score"].astype(float) >= 0.5).astype(int)
            print("Derived 'interaction' from 'risk_score' using threshold 0.5")
        elif "severity" in df.columns:
            # map HIGH/MEDIUM -> 1, LOW -> 0
            df["interaction"] = df["severity"].astype(str).str.upper().map(lambda s: 1 if s in ("HIGH", "MEDIUM") else 0)
            print("Derived 'interaction' from 'severity' (HIGH/MEDIUM -> 1, LOW -> 0)")
        else:
            raise KeyError("Target column 'interaction' not found and no fallback column available")

    X = df[features]
    y = df["interaction"]

    # Encode target if it's non-numeric
    label_encoder_path = models_dir / "rf_label_encoder.pkl"
    if y.dtype == object or y.dtype.name == "category":
        le = LabelEncoder()
        y = le.fit_transform(y.astype(str))
        joblib.dump(le, label_encoder_path)
    else:
        # ensure numpy array
        y = y.values

    # Stratify only when there are at least 2 classes
    stratify = y if len(set(y)) > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    acc = clf.score(X_test, y_test)

    model_path = models_dir / "rf_model.pkl"
    joblib.dump(clf, model_path)

    print(f"Saved model to {model_path}")
    print(f"Accuracy: {acc:.4f}")


if __name__ == "__main__":
    main()
