# -*- coding: utf-8 -*-
"""
Created on  8 February 2022

@author: Amin
"""

# Import liberaries and functions
import pandas as pd
import glob
import os
import numpy as np
import pickle
from file_preprocess import multi_file_process
from text_tokenizer import tokenizer
from multiprocessing import Pool
from gensim import corpora
import argparse
import sys
import time
from functools import partial

# =============================================================================
# Prepare (pre-process) risk reports for LDA topic modeling.

# To run:
# >>> python RFs_prep.py --files 'Data/Risk Factors 10k' --njobs 15
# =============================================================================

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--files', type=str, default='Data/Risk Factors 10k', help='folder containing risk reports')
parser.add_argument('--tokens', type=str, default='RF_tokens.txt', help='directory to save tokenized text data')
parser.add_argument('--dictionary', type=str, default='RF_lda_dict', help='directory to save dictionary object')
parser.add_argument('--RF_df', type=str, default='RF_df.csv', help='directory to save dataframe containing risk factors')

### parameters
parser.add_argument('--Qup', type=float, default=0.99, help='Upper quantile to filter too long docs (risk factors)')
parser.add_argument('--Qlow', type=float, default=0.05, help='Lower quantile to filter too short docs (risk factors)')
parser.add_argument('--njobs', type=int, default=15, help='number of cpu cores to be used for training')
parser.add_argument('--no_below', type=int, default=100, help='Keep tokens which are contained in at least no_below documents')
parser.add_argument('--no_above', type=float, default=0.99, help='Keep tokens which are contained in no more than no_above documents (fraction of total corpus size, not an absolute number)')

args = parser.parse_args()

sys.stdout = open("log_RFs_prep.txt", "w")

# Save the clean DataFrame
print(time.ctime() + " | Start reading HTML/TXT files ...")

# Get all raw html/text file paths
all_files = glob.glob(args.files+'\*')

n_jobs = args.njobs
batchs = np.array_split(all_files, 2*n_jobs)

if __name__ == "__main__":
    with Pool(processes=n_jobs) as p:
        output = p.map(partial(multi_file_process, rf_split=True), batchs)
    p.join()
    
    RF_df = pd.concat(output)
    
# Remove empty reports
RF_df.dropna(inplace=True)

# Remove duplicates
RF_df = (
    RF_df.sort_values(by=['cik', 'reporting year', 'filing date']).drop_duplicates()
)

# Save the clean DataFrame
print(time.ctime() + " | Saving processed docs as CSV file ...")
RF_df.to_csv(args.RF_df)

# Filter too short and too long docs (risk factors)
word_cnt = RF_df['Item 1A'].map(lambda x: len(x.split()))
Qup = word_cnt.quantile(q=args.Qup)
Qlow = word_cnt.quantile(q=args.Qlow)

print(f'Upper percentile: {Qup}')
print(f'Lower percentile: {Qlow}')

filtered_rf_df = RF_df[(word_cnt>Qlow) & (word_cnt<Qup)]

raw_text_data = filtered_rf_df['Item 1A']

print(time.ctime() + " | Starting text tokenization process ... \n")

# Tokenize raw text data
if __name__ == "__main__":
    tokens = tokenizer(raw_text_data, n_jobs=n_jobs)

with open(args.tokens, "wb") as fp:
    pickle.dump(tokens, fp)

print(time.ctime() + " | Creating Gensim Dictionary and Corpus ... \n")
# Generate Dictionary
lda_dict = corpora.Dictionary(tokens)

# Filter most common and rare words
lda_dict.filter_extremes(no_below=args.no_below, no_above=args.no_above)

# Create corpus from Dictionary
lda_corpus = [lda_dict.doc2bow(text) for text in tokens]

# Save lda_dict to disk
lda_dict.save(args.dictionary)
print(time.ctime() + " | Gensim Dictionary saved to disk")


sys.stdout.close()


