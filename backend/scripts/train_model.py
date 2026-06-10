from pathlib import Path
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INTERACTIONS = DATA / "interactions.csv"
MODEL_OUT = ROOT / "models" / "ddi_model.pkl"


def featurize(df_inter, df_drugs):
    X = []
    y = []
    for _, r in df_inter.iterrows():
        d1 = df_drugs[df_drugs["drug_id"] == r["drug1"]].iloc[0]
        d2 = df_drugs[df_drugs["drug_id"] == r["drug2"]].iloc[0]
        # simple features: half-life sum and common enzyme flag
        h1 = float(d1.get("half_life", 0))
        h2 = float(d2.get("half_life", 0))
        enz1 = set(str(d1.get("enzymes", "")).split(";"))
        enz2 = set(str(d2.get("enzymes", "")).split(";"))
        common_enz = 1 if len(enz1 & enz2) > 0 else 0
        X.append([h1 + h2, common_enz])
        y.append(int(r["label"]))
    return X, y


def train():
    df_inter = pd.read_csv(INTERACTIONS)
    df_drugs = pd.read_csv(DATA / "drugs.csv")
    X, y = featurize(df_inter, df_drugs)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_OUT)
    print(f"Saved ML model to {MODEL_OUT}")


if __name__ == "__main__":
    train()
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
import joblib

# Load dataset
df = pd.read_csv("ddi_dataset.csv")

# Encode boolean
df["poor_metabolizer"] = df["poor_metabolizer"].astype(int)

# Drop non-numeric columns
df = df.drop(columns=["drug1", "drug2", "severity"])

# Features and target
X = df.drop(columns=["risk_score"])
y = df["risk_score"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
model = XGBRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05
)

model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
mse = mean_squared_error(y_test, preds)

print("MSE:", mse)

# Save model
joblib.dump(model, "ddi_model.pkl")
print("Model saved: ddi_model.pkl")