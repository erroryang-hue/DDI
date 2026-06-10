from pathlib import Path
from typing import List
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DRUGS_CSV = DATA_DIR / "drugs.csv"


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in str(cell).split(";") if s.strip()])


def _load_drug_row(df, drug_id: str):
    row = df[df["drug_id"] == drug_id]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "enzymes": _parse(r.get("enzymes", "")),
        "targets": _parse(r.get("targets", "")),
        "transporters": _parse(r.get("transporters", "")),
        "pathways": _parse(r.get("pathways", "")),
        "side_effects": _parse(r.get("side_effects", "")),
    }


def _severity_label(score: float) -> str:
    try:
        s = float(score)
    except Exception:
        return "UNKNOWN"
    if s < 0.33:
        return "LOW"
    if s < 0.66:
        return "MEDIUM"
    return "HIGH"


def generate_explanation(
    drug1: str,
    drug2: str,
    mechanisms: List[str],
    graph_paths: List[str],
    risk_score: float,
) -> str:
    """Generate a concise clinical explanation for the interaction between two drugs.

    Signature: (drug1, drug2, mechanisms, graph_paths, risk_score) -> str
    """
    # load drug reference
    df = pd.read_csv(DRUGS_CSV)
    d1 = _load_drug_row(df, drug1)
    d2 = _load_drug_row(df, drug2)

    parts = []
    parts.append(f"Potential interaction between {drug1} and {drug2}.")

    if not d1 or not d2:
        parts.append("One or both drugs are missing from the drug reference; verify identifiers.")
        parts.append(f"Estimated risk: {risk_score:.2f} ({_severity_label(risk_score)})")
        return " ".join(parts)

    # Enzyme interactions
    if "enzyme_overlap" in mechanisms or "enzyme_interaction" in mechanisms:
        enzymes = sorted(list(d1["enzymes"] & d2["enzymes"]))
        if enzymes:
            parts.append(
                f"Both drugs interact with enzyme(s) {', '.join(enzymes)}; co-administration may alter metabolism and exposure."
            )
        else:
            parts.append("Enzyme-mediated interaction likely (shared metabolic pathways).")

    # Transporter interactions
    if "transporter_overlap" in mechanisms or "transporter_interaction" in mechanisms:
        trans = sorted(list(d1["transporters"] & d2["transporters"]))
        if trans:
            parts.append(
                f"Both are associated with transporter(s) {', '.join(trans)}; this can affect absorption/distribution."
            )
        else:
            parts.append("Transporter-mediated interaction suspected.")

    # Shared pathways
    if "pathway_overlap" in mechanisms or "shared_pathway" in mechanisms:
        pws = sorted(list(d1["pathways"] & d2["pathways"]))
        if pws:
            parts.append(f"Shared pathway(s): {', '.join(pws)} — possible additive pharmacodynamic effects.")
        else:
            parts.append("Overlap in biological pathways suggests potential additive effects.")

    # Shared side effects
    if "side_effect_overlap" in mechanisms or "side_effect_overlap" in mechanisms:
        ses = sorted(list(d1["side_effects"] & d2["side_effects"]))
        if ses:
            parts.append(
                f"Both drugs are linked to {', '.join(ses)}; monitor closely for increased adverse effect risk."
            )
        else:
            parts.append("Overlapping adverse event profiles increase combined risk.")

    # Add graph-based reasoning if present
    if graph_paths:
        sample = graph_paths[:3]
        parts.append("Knowledge graph suggests mechanistic paths: " + " | ".join(sample))

    parts.append(f"Estimated risk: {risk_score:.2f} ({_severity_label(risk_score)}). Consider monitoring or dose adjustment.")

    # Compose concise explanation (limit to 4 sentences)
    text = " ".join(parts)
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if len(sentences) > 4:
        text = ". ".join(sentences[:4]) + "."
    else:
        text = ". ".join(sentences) + "."

    return text


if __name__ == "__main__":
    print(
        generate_explanation(
            "DrugA",
            "DrugB",
            ["enzyme_overlap"],
            ["DrugA -> INHIBITS -> CYP3A4 -> METABOLIZES -> DrugB"],
            0.5,
        )
    )
