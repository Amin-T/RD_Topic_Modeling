# -*- coding: utf-8 -*-
"""
Created on  8 February 2022

@author: Amin
"""

# Import liberaries and functions
from multiprocessing.dummy import freeze_support
import pandas as pd
import glob
import numpy as np
import pickle
from file_preprocess import multi_file_process
from text_tokenizer import tokenizer
from multiprocessing import Pool
from gensim import corpora
import argparse
import sys
from time import strftime, gmtime
from functools import partial

"""
=============================================================================
Prepare (pre-process) risk reports for LDA topic modeling.

To run:
    with splitting reports to risk factors:
    >>> python RFs_prep.py --njobs 15

    without splitting:
    >>> python LDA\RFs_prep.py --njobs 10 --tokens Item1A_tokens.txt --dictionary Item1A_lda_dict --RF_df Item1A_df.csv --Qlow 0.1

=============================================================================
"""

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--files', type=str, default='Data/Risk Factors 10k', help='folder containing risk reports')
parser.add_argument('--tokens', type=str, default='RF_tokens.txt', help='directory to save tokenized text data')
parser.add_argument('--dictionary', type=str, default='RF_lda_dict', help='directory to save dictionary object')
parser.add_argument('--RF_df', type=str, default='RF_df.csv', help='directory to save dataframe containing risk factors')
parser.add_argument('--rf_split', type=int, choices=[0,1], default=0, help='preprocess with (1) or without (0) splitting risk factors')

### parameters
parser.add_argument('--Qup', type=float, default=0.99, help='Upper quantile to filter too long docs (risk factors)')
parser.add_argument('--Qlow', type=float, default=0.05, help='Lower quantile to filter too short docs (risk factors)')
parser.add_argument('--njobs', type=int, default=15, help='number of cpu cores to be used for training')
parser.add_argument('--no_below', type=int, default=50, help='Keep tokens which are contained in at least no_below documents')
parser.add_argument('--no_above', type=float, default=0.95, help='Keep tokens which are contained in no more than no_above documents (fraction of total corpus size, not an absolute number)')

args = parser.parse_args()

sys.stdout = open("log_RFs_prep.txt", "w")

rfsplit = bool(args.rf_split)

if rfsplit:
    print("*** Pre-processing by spliting reports to risk reports ***\n")
else:
    print("*** Pre-processing of risk reports ***\n")

# Save the clean DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Start reading HTML/TXT files ...")

# Get all raw html/text file paths
all_files = glob.glob(args.files+'/*')

n_jobs = args.njobs
batchs = np.array_split(all_files, 2*n_jobs)
    
if __name__ == "__main__":
    freeze_support()
    with Pool(processes=n_jobs) as p:
        output = p.map(partial(multi_file_process, rf_split=rfsplit), batchs)
    p.join()

    RF_df = pd.concat(output)

# Remove empty reports
RF_df.dropna(inplace=True)

# Remove duplicates
RF_df = (
    RF_df.sort_values(by=['cik', 'reporting year', 'filing date']).drop_duplicates()
)

# Save the clean DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Saving processed docs as CSV file ...")
RF_df.to_csv(args.RF_df)

# Filter too short and too long docs (risk factors)
word_cnt = RF_df['Item 1A'].map(lambda x: len(x.split()))
Qup = word_cnt.quantile(q=args.Qup)
Qlow = word_cnt.quantile(q=args.Qlow)

print(f'Upper percentile: {Qup}')
print(f'Lower percentile: {Qlow}')

if rfsplit:
    filtered_rf_df = RF_df[(word_cnt>Qlow) & (word_cnt<Qup)]
else:
    filtered_rf_df = RF_df[(word_cnt>Qlow)]

raw_text_data = filtered_rf_df['Item 1A']

print(f"{strftime('%D %H:%M', gmtime())} | Starting text tokenization process ... \n")

# Tokenize raw text data
if __name__ == "__main__":
    tokens = tokenizer(raw_text_data, n_jobs=n_jobs)

with open(args.tokens, "wb") as fp:
    pickle.dump(tokens, fp)

print(f"{strftime('%D %H:%M', gmtime())} | Creating Gensim Dictionary and Corpus ... \n")
# Generate Dictionary
lda_dict = corpora.Dictionary(tokens)

# Filter most common and rare words
lda_dict.filter_extremes(no_below=args.no_below, no_above=args.no_above)

# Save lda_dict to disk
lda_dict.save(args.dictionary)
print(f"{strftime('%D %H:%M', gmtime())} | Gensim Dictionary saved to disk")


sys.stdout.close()


