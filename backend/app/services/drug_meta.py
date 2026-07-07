from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
KNOWN_HALF_LIFE_COLUMNS = ("half_life", "half_life_hours")
KNOWN_DRUG_KEY_COLUMNS = ("drug_id", "canonical_id", "drug_name", "generic_name")


def _read_csv_if_exists(path: Path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return None
    return None


def _is_drug_source(path: Path) -> bool:
    if not path.exists() or path.suffix.lower() != ".csv":
        return False
    try:
        df = pd.read_csv(path, nrows=0)
    except Exception:
        return False

    cols = [c.strip().lower() for c in df.columns]
    has_drug_key = any(key in cols for key in KNOWN_DRUG_KEY_COLUMNS)
    has_half_life = any(key in cols for key in KNOWN_HALF_LIFE_COLUMNS)
    return has_drug_key and has_half_life


def _resolve_drug_sources():
    paths = [DATA_DIR / "drugs.csv", DATA_DIR / "drugs_generated.csv"]
    seen = {p.resolve() for p in paths}

    cur = ROOT
    for _ in range(4):
        for candidate in cur.glob("*.csv"):
            if candidate.resolve() in seen:
                continue
            if _is_drug_source(candidate):
                paths.append(candidate)
                seen.add(candidate.resolve())
        cur = cur.parent

    return paths


def load_drug_catalog() -> pd.DataFrame:
    df_list = []
    for path in _resolve_drug_sources():
        df = _read_csv_if_exists(path)
        if df is None or df.empty:
            continue
        df_list.append(df)

    if not df_list:
        return pd.DataFrame()
    return pd.concat(df_list, ignore_index=True, sort=False)


def _find_drug_rows(drug_name: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    if not drug_name:
        return pd.DataFrame()
    if df is None:
        df = load_drug_catalog()
    if df.empty:
        return pd.DataFrame()

    name_l = str(drug_name).strip().lower()
    for col in KNOWN_DRUG_KEY_COLUMNS:
        if col in df.columns:
            matches = df[df[col].astype(str).str.lower() == name_l]
            if not matches.empty:
                return matches

    if "drug_name" in df.columns:
        return df[df["drug_name"].astype(str).str.lower() == name_l]

    return pd.DataFrame()


def get_half_life(drug_name: str) -> float | None:
    rows = _find_drug_rows(drug_name)
    if rows.empty:
        return None

    for _, row in rows.iterrows():
        for hl_col in KNOWN_HALF_LIFE_COLUMNS:
            if hl_col in row.index and pd.notna(row.get(hl_col)):
                try:
                    return float(row.get(hl_col))
                except Exception:
                    continue
    return None
