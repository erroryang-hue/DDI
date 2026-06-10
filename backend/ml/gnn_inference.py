from pathlib import Path

import torch

from ml.gnn_dataset import build_graph
from ml.gnn_model import DDI_GNN

ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "models" / "gnn_model.pt"

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


def predict_interaction(drug1: str, drug2: str):
    if not model_loaded:
        return None

    if drug1 not in node_map or drug2 not in node_map:
        return None

    with torch.no_grad():
        z = model.encode(graph.x, graph.edge_index)
        src = torch.tensor([node_map[drug1]], dtype=torch.long)
        dst = torch.tensor([node_map[drug2]], dtype=torch.long)
        score = model.predict(z, src, dst)
        return float(torch.sigmoid(score).item())
