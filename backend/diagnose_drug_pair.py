from app.services.drug_meta import load_drug_catalog
from app.services.interaction_engine import score_interaction
from app.services.risk_engine import compute_risk

if __name__ == '__main__':
    drug1 = 'Lupin Acp 100mg/325mg Tablet'
    drug2 = 'Warfarin'
    df = load_drug_catalog()
    print('catalog rows', len(df))
    print('drug1 exact', len(df[df['drug_name'].astype(str).str.lower() == drug1.lower()]))
    print('drug2 exact', len(df[df['drug_name'].astype(str).str.lower() == drug2.lower()]))
    print('drug1 contains', df['drug_name'].dropna().astype(str).str.contains('Lupin Acp', case=False).sum())
    print('drug2 contains', df['drug_name'].dropna().astype(str).str.contains('Warfarin', case=False).sum())
    print('drug1 rows', df[df['drug_name'].astype(str).str.lower() == drug1.lower()].head(5).to_dict(orient='records'))
    print('drug2 rows', df[df['drug_name'].astype(str).str.lower() == drug2.lower()].head(5).to_dict(orient='records'))
    from app.services.interaction_engine import _load_drug
    d1 = _load_drug(df, drug1)
    d2 = _load_drug(df, drug2)
    print('drug1 parsed', d1)
    print('drug2 parsed', d2)
    score, mech = score_interaction(drug1, drug2)
    print('interaction score', score, 'mechanisms', mech)
    risk, details = compute_risk(drug1, drug2, 0.5, score, age=55, weight=70, dose1=325, dose2=5, poor_metabolizer=False)
    print('risk', risk)
    print('details', details)
    base = 0.0
    weights = {'rf_score': 0.25, 'gnn_score': 0.35, 'interaction_score': 0.3, 'temporal_overlap': 0.1}
    avail = {k: details['components'][k] for k in weights if details['components'][k] is not None}
    total_w = sum(weights[k] for k in avail)
    if total_w > 0:
        base = sum(avail[k] * weights[k] for k in avail) / total_w
    print('recomputed base', base)
    print('modifier', details['modifier'])
    import math
    print('recomputed final', 1 - math.exp(-base * details['modifier']))
