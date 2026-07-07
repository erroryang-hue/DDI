from pathlib import Path
from typing import List
import re
import pandas as pd

from app.services.drug_meta import load_drug_catalog

ROOT = Path(__file__).resolve().parents[2]


def _parse(cell):
    if pd.isna(cell) or cell is None:
        return set()
    return set([s.strip() for s in re.split(r"[;,]", str(cell)) if s.strip()])


def _resolve_drug_row(df: pd.DataFrame, drug_key: str):
    if df.empty or not drug_key:
        return None
    key = str(drug_key).strip().lower()
    for col in ("drug_id", "drug_name", "generic_name", "canonical_id"):
        if col in df.columns:
            row = df[df[col].astype(str).str.lower() == key]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "enzymes": _parse(r.get("enzymes", "")),
                    "targets": _parse(r.get("targets", "")),
                    "transporters": _parse(r.get("transporters", "")),
                    "pathways": _parse(r.get("pathways", "")),
                    "side_effects": _parse(r.get("side_effects", "")),
                }
    return None


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
    # load drug reference from the combined drug catalog
    df = load_drug_catalog()
    d1 = _resolve_drug_row(df, drug1)
    d2 = _resolve_drug_row(df, drug2)

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
