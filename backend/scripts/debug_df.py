import pandas as pd
from pathlib import Path
p=Path(__file__).resolve().parents[1]
print('cwd',p)
df_list=[]
if (p/'data'/'drugs.csv').exists():
    df_list.append(pd.read_csv(p/'data'/'drugs.csv'))
if (p/'data'/'drugs_generated.csv').exists():
    df_list.append(pd.read_csv(p/'data'/'drugs_generated.csv'))
if not df_list:
    print('no files')
else:
    df=pd.concat(df_list, ignore_index=True)
    print('columns', df.columns.tolist())
    if 'drug_id' not in df.columns:
        df=df.reset_index(drop=True)
        df['drug_id']=['ID'+str(i) for i in range(len(df))]
    print('total rows', len(df))
    print('first 10 drug_ids', df['drug_id'].head(10).tolist())
    from itertools import combinations
    ids=df['drug_id'].tolist()
    pairs=list(combinations(ids,2))
    print('pairs', len(pairs))
    # show any duplicates
    print('duplicate drug_id count', df['drug_id'].duplicated().sum())
    print('sample rows where drug_id missing?')
    print(df[df['drug_id'].isnull()].head())
