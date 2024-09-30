import pandas as pd
import json
from tqdm.auto import tqdm
from multiprocessing import Pool
import glob
import os

all_submissions = glob.glob('submissions/*')

print("Number of files: ", len(all_submissions))

columns = ['cik', 'entityType', 'sic', 'category']

def get_filings(submission):
    try:
        with open(submission, 'rb') as f:
            sub = json.load(f)
        
        output = dict([(key, sub.get(key)) for key in columns])

    except:
        output = dict([(key, 0) for key in columns])

    return output


        # if sub.get('filings'):
        #     filings = sub.get('filings')
        #     temp = pd.DataFrame(filings['recent'])
            
        #     if filings.get('files'):
        #         add_files_names = [f['name'] for f in filings['files']]
        #         for name in add_files_names:
        #             with open(f'subs/{name}', 'rb') as f:
        #                 add_files = json.load(f)
        #             temp = pd.concat([temp, pd.DataFrame(add_files)])

        #     for col in columns:
        #         try:
        #             temp[col] = sub.get(col)
        #         except:
        #             continue
            
        #     temp.drop(
        #         columns=['acceptanceDateTime', 'act', 'fileNumber', 'filmNumber', 
        #         'items', 'size', 'isXBRL', 'isInlineXBRL', 'primaryDocDescription'],
        #         inplace=True
        #     )

        #     return temp

        # else:
        #     return None

    # except:
    #     return None
    
print("<< START >>\n")

with Pool(processes=os.cpu_count()) as p:
    output = p.map(get_filings, all_submissions[:100])
p.join()

# filings_df = pd.concat(output)

# filings_df = filings_df[filings_df["form"]=="10-K"]

filings_df = pd.DataFrame(output).drop_duplicates()

print(filings_df.shape)

filings_df.to_csv('SIC_df.csv', index=False)

