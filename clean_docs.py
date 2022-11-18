# -*- coding: utf-8 -*-
"""
Created on 2 November 2022

@author: Amin
"""

# Import libraries and functions
from data import load_data, nlp_clean, bigram
import argparse
from time import strftime, gmtime
import spacy

"""
=============================================================================
Clean Risk Factors and implement bigram transformation.

To run:
    >>> python clean_docs.py --RF_df Data/W2V_train.csv
=============================================================================
"""
parser = argparse.ArgumentParser(description='RFs prepration')

parser.add_argument('--RF_df', type=str, default='Data/RF_no_fin.csv', help='directory of dataframe containing risk factors')
parser.add_argument('--clean_docs', type=str, default="Data/clean_docs.csv", help='directory to save cleaned documents')

parser.add_argument('--Qup', type=float, default=0.005, help='Upper quantile to filter too long docs (risk factors)')
parser.add_argument('--Qlow', type=float, default=1, help='Lower quantile to filter too short docs (risk factors)')
parser.add_argument('--min_count', type=float, default=0.0001, help='min count of bigrams (ratio of number of RFs)')
parser.add_argument('--spacy', type=str, default="en_core_web_sm", help='spaCy model to be loaded')
parser.add_argument('--n_jobs', type=int, default=-1, help='Number of processors to process texts')

args = parser.parse_args()

print(args, "\n")

nlp = spacy.load(args.spacy)

print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Load raw text data
raw_data = load_data(args.RF_df, low_bnd=args.Qup, up_bnd=args.Qlow)

cleaned_data = raw_data.drop(columns=["Item 1A"]).copy()
RFs = raw_data['Item 1A'].str.lower().tolist()

print(f"{strftime('%D %H:%M', gmtime())} | Cleaning risk factor docs ...\n")
corpus = nlp.pipe(RFs, n_process=args.n_jobs)

clean_corpus = [list(d) for d in (nlp_clean(doc) for doc in corpus)]

print(f"{strftime('%D %H:%M', gmtime())} | Bigram transformation ...\n")
def token(text):
    return text

transformed_sents = bigram(
    raw_data = clean_corpus, 
    tokenizer=token,
    min_cnt = args.min_count 
)

cleaned_data.loc[:, 'cleaned_txt'] = [" ".join(d) for d in transformed_sents]

print(f"{strftime('%D %H:%M', gmtime())} | Saving cleaned documents ...\n")
cleaned_data.to_csv(args.clean_docs)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")


