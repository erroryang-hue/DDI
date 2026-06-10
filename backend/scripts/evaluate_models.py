"""Evaluate Random Forest and GraphSAGE models and save metrics to reports/"""
from pathlib import Path
import json
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import torch

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

# RF evaluation
def eval_rf():
    csv = ROOT / "ddi_dataset.csv"
    model_path = ROOT / "models" / "rf_model.pkl"
    if not csv.exists() or not model_path.exists():
        return None
    df = pd.read_csv(csv)
    # derive interaction target as before
    if "interaction" not in df.columns:
        if "risk_score" in df.columns:
            df["interaction"] = (df["risk_score"].astype(float) >= 0.5).astype(int)
        elif "severity" in df.columns:
            df["interaction"] = df["severity"].astype(str).str.upper().map(lambda s: 1 if s in ("HIGH","MEDIUM") else 0)

    features = [
        "enzyme_overlap",
        "target_overlap",
        "pathway_overlap",
        "transporter_overlap",
        "side_effect_overlap",
    ]
    for f in features:
        if f not in df.columns:
            df[f] = 0.0

    X = df[features]
    y = df["interaction"].astype(int)
    model = joblib.load(model_path)
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
        preds = (probs >= 0.5).astype(int)
    else:
        preds = model.predict(X)
        probs = preds

    metrics = {
        "accuracy": accuracy_score(y, preds),
        "precision": precision_score(y, preds, zero_division=0),
        "recall": recall_score(y, preds, zero_division=0),
        "f1": f1_score(y, preds, zero_division=0),
    }
    try:
        metrics["roc_auc"] = roc_auc_score(y, probs)
    except Exception:
        metrics["roc_auc"] = None

    out = REPORTS / "rf_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    return metrics


# GNN evaluation (link prediction)
def eval_gnn():
    edges_csv = DATA_DIR / "graph_edges.csv"
    model_path = ROOT / "models" / "gnn_model.pt"
    if not edges_csv.exists() or not model_path.exists():
        return None

    from ml.gnn_dataset import build_graph
    from ml.gnn_model import DDI_GNN

    data, node_map = build_graph()
    model = DDI_GNN(data.num_features, 64)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    # positives
    df = pd.read_csv(edges_csv)
    pos_pairs = []
    for _, r in df.iterrows():
        s = r["source"]
        t = r["target"]
        if s in node_map and t in node_map:
            pos_pairs.append((node_map[s], node_map[t]))

    # sample negatives
    import random
    num_nodes = data.x.size(0)
    neg_pairs = set()
    while len(neg_pairs) < len(pos_pairs):
        u = random.randrange(num_nodes)
        v = random.randrange(num_nodes)
        if (u, v) in pos_pairs:
            continue
        neg_pairs.add((u, v))
    neg_pairs = list(neg_pairs)

    # compute scores
    def score_pairs(pairs):
        with torch.no_grad():
            z = model.encode(data.x, data.edge_index)
            src = torch.tensor([p[0] for p in pairs], dtype=torch.long)
            dst = torch.tensor([p[1] for p in pairs], dtype=torch.long)
            logits = model.predict(z, src, dst)
            probs = torch.sigmoid(logits).numpy()
            return probs

    pos_probs = score_pairs(pos_pairs)
    neg_probs = score_pairs(neg_pairs)

    y_true = [1] * len(pos_probs) + [0] * len(neg_probs)
    y_scores = list(pos_probs) + list(neg_probs)
    preds = [1 if s >= 0.5 else 0 for s in y_scores]

    metrics = {
        "accuracy": accuracy_score(y_true, preds),
        "precision": precision_score(y_true, preds, zero_division=0),
        "recall": recall_score(y_true, preds, zero_division=0),
        "f1": f1_score(y_true, preds, zero_division=0),
    }
    try:
        metrics["roc_auc"] = roc_auc_score(y_true, y_scores)
    except Exception:
        metrics["roc_auc"] = None

    out = REPORTS / "gnn_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    return metrics


def main():
    r1 = eval_rf()
    r2 = eval_gnn()
    print("RF metrics:", r1)
    print("GNN metrics:", r2)


if __name__ == "__main__":
    main()
