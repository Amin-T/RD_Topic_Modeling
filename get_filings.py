import pandas as pd
import json
from tqdm.auto import tqdm
from multiprocessing import Pool
import glob


all_submissions = glob.glob('subs/*')

columns = ['cik', 'entityType', 'sic', 'name', 'category', 'tickers', 'exchanges']

def get_filings(submission):
    try:
        with open(submission, 'rb') as f:
            sub = json.load(f)
        
        if sub.get('filings'):
            filings = sub.get('filings')
            temp = pd.DataFrame(filings['recent'])
            
            if filings.get('files'):
                add_files_names = [f['name'] for f in filings['files']]
                for name in add_files_names:
                    with open(f'subs/{name}', 'rb') as f:
                        add_files = json.load(f)
                    temp = pd.concat([temp, pd.DataFrame(add_files)])

            for col in columns:
                try:
                    temp[col] = sub.get(col)
                except:
                    continue
            
            temp.drop(
                columns=['acceptanceDateTime', 'act', 'fileNumber', 'filmNumber', 
                'items', 'size', 'isXBRL', 'isInlineXBRL', 'primaryDocDescription'],
                inplace=True
            )

            return temp

        else:
            return None

    except:
        return None
    
print("<< START >>\n")

with Pool(processes=30) as p:
    output = p.map(get_filings, all_submissions)
p.join()

filings_df = pd.concat(output)

filings_df = filings_df[filings_df["form"]=="10-K"]

print(filings_df.shape)

filings_df.to_csv('filings_df.csv', index=False)

