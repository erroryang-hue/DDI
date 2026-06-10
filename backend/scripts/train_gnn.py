from pathlib import Path

import random
import numpy as np
import torch
from sklearn.metrics import roc_auc_score

from ml.gnn_dataset import build_graph
from ml.gnn_model import DDI_GNN

ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "models" / "gnn_model.pt"


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def negative_sampling(num_nodes, pos_set, k):
    negs = set()
    while len(negs) < k:
        u = random.randrange(num_nodes)
        v = random.randrange(num_nodes)
        if (u, v) in pos_set:
            continue
        negs.add((u, v))
    return list(negs)


def train(epochs=200, neg_ratio=1):
    set_seed(42)

    data, node_map = build_graph()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    x = data.x.to(device)
    edge_index = data.edge_index.to(device)
    num_nodes = x.size(0)

    model = DDI_GNN(x.size(1), 64).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    # prepare positive edge set
    src_list = edge_index[0].cpu().tolist()
    dst_list = edge_index[1].cpu().tolist()
    pos_pairs = list(zip(src_list, dst_list))
    pos_set = set(pos_pairs)
    pos_count = len(pos_pairs)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        z = model.encode(x, edge_index)

        # positive logits
        src = torch.tensor([p[0] for p in pos_pairs], dtype=torch.long, device=device)
        dst = torch.tensor([p[1] for p in pos_pairs], dtype=torch.long, device=device)
        pos_logits = model.predict(z, src, dst)

        # negative sampling
        neg_needed = pos_count * neg_ratio
        neg_pairs = negative_sampling(num_nodes, pos_set, neg_needed)
        nsrc = torch.tensor([p[0] for p in neg_pairs], dtype=torch.long, device=device)
        ndst = torch.tensor([p[1] for p in neg_pairs], dtype=torch.long, device=device)
        neg_logits = model.predict(z, nsrc, ndst)

        logits = torch.cat([pos_logits, neg_logits], dim=0)
        labels = torch.cat([torch.ones_like(pos_logits), torch.zeros_like(neg_logits)], dim=0)

        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()

        if epoch % 20 == 0 or epoch == epochs - 1:
            model.eval()
            with torch.no_grad():
                probs = torch.sigmoid(logits).cpu().numpy()
                y_true = labels.cpu().numpy()
                try:
                    auc = roc_auc_score(y_true, probs)
                except Exception:
                    auc = float("nan")
            print(f"Epoch {epoch}, Loss {loss.item():.6f}, AUC {auc:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    train()
    