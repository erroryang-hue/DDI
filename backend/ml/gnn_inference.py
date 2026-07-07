from pathlib import Path
import re

import torch
import pandas as pd

from app.services.drug_meta import load_drug_catalog
from ml.gnn_dataset import build_graph
from ml.gnn_model import DDI_GNN

ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "models" / "gnn_model.pt"
DRUGS_CSV = ROOT_DIR / "data" / "drugs.csv"

graph, node_map = build_graph()

model = DDI_GNN(graph.num_features, 64)
model_loaded = False

if MODEL_PATH.exists():
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        model.eval()
        model_loaded = True
    except Exception:
        model_loaded = False


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in re.split(r"[;,]", str(cell)) if s.strip()])


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni > 0 else 0.0


def _heuristic_score(drug1: str, drug2: str) -> float:
    """Fallback heuristic when the trained GNN model isn't available.

    Uses Jaccard overlaps across enzymes/targets/pathways/transporters/side effects.
    """
    try:
        df = load_drug_catalog()
        if df.empty:
            if not DRUGS_CSV.exists():
                return 0.0
            df = pd.read_csv(DRUGS_CSV)
        r1 = df[df["drug_name"].astype(str).str.lower() == drug1.lower()]
        r2 = df[df["drug_name"].astype(str).str.lower() == drug2.lower()]
        if r1.empty or r2.empty:
            return 0.0
        r1 = r1.iloc[0]
        r2 = r2.iloc[0]

        enzymes1 = _parse(r1.get("enzymes", ""))
        enzymes2 = _parse(r2.get("enzymes", ""))
        targets1 = _parse(r1.get("targets", ""))
        targets2 = _parse(r2.get("targets", ""))
        pathways1 = _parse(r1.get("pathways", ""))
        pathways2 = _parse(r2.get("pathways", ""))
        transport1 = _parse(r1.get("transporters", ""))
        transport2 = _parse(r2.get("transporters", ""))
        se1 = _parse(r1.get("side_effects", ""))
        se2 = _parse(r2.get("side_effects", ""))

        overlaps = [
            _jaccard(enzymes1, enzymes2),
            _jaccard(targets1, targets2),
            _jaccard(pathways1, pathways2),
            _jaccard(transport1, transport2),
            _jaccard(se1, se2),
        ]
        # weighted average (more emphasis on enzymes/targets)
        weights = [0.25, 0.25, 0.2, 0.15, 0.15]
        score = sum(o * w for o, w in zip(overlaps, weights))
        return float(max(0.0, min(1.0, score)))
    except Exception:
        return 0.0


def predict_interaction(drug1: str, drug2: str):
    """Return a score in [0,1]. Use trained GNN if available, otherwise heuristic."""
    if model_loaded:
        try:
            if drug1 in node_map and drug2 in node_map:
                with torch.no_grad():
                    z = model.encode(graph.x, graph.edge_index)
                    src = torch.tensor([node_map[drug1]], dtype=torch.long)
                    dst = torch.tensor([node_map[drug2]], dtype=torch.long)
                    score = model.predict(z, src, dst)
                    return float(torch.sigmoid(score).item())
        except Exception:
            # fallthrough to heuristic
            pass

    # fallback heuristic when model not loaded or nodes missing
    return _heuristic_score(drug1, drug2)
