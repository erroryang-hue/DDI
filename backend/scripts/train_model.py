from pathlib import Path
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DDI_CSV = DATA / "ddi_dataset.csv"
MODEL_OUT = ROOT / "models" / "ddi_model.pkl"


def train():
    if not DDI_CSV.exists():
        raise FileNotFoundError(f"Dataset not found: {DDI_CSV}")
    df = pd.read_csv(DDI_CSV)

    feature_cols = [
        "enzyme_overlap",
        "target_overlap",
        "pathway_overlap",
        "transporter_overlap",
        "side_effect_overlap",
        "inhibition",
        "induction",
        "additive_toxicity",
    ]
    for c in feature_cols:
        if c not in df.columns:
            df[c] = 0

    X = df[feature_cols].fillna(0)
    y = df["interaction"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print("Accuracy on test set:", acc)
    print(classification_report(y_test, preds))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_OUT)
    print(f"Saved ML model to {MODEL_OUT}")


if __name__ == "__main__":
    train()