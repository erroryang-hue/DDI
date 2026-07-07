import pandas as pd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
repo=ROOT.parents[1]
print('backend root',ROOT)
print('repo root',repo)
# load synthetic from repo root
synth=None
cur=ROOT
for _ in range(4):
    candidate=cur/'synthetic_drugs_50_with_half_life.csv'
    if candidate.exists():
        synth=candidate
        break
    cur=cur.parent

if synth is None:
    print('synthetic file missing')
else:
    df=pd.read_csv(synth)
    print('synthetic rows',len(df))
    print(df[['drug_name','half_life_hours']].head().to_string(index=False))

# load drugs.csv
drugs=ROOT/'data'/'drugs.csv'
if drugs.exists():
    ddf=pd.read_csv(drugs)
    print('drugs.csv sample half_life column names',list(ddf.columns)[:10])
    # show lookup for first synthetic drug in drugs.csv by name
    if synth is not None:
        name=df.iloc[0]['drug_name']
        match=ddf[ddf['drug_name'].str.lower()==str(name).lower()]
        print('match in drugs.csv for',name, '->', len(match))

