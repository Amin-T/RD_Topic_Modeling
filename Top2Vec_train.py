# -*- coding: utf-8 -*-
"""
Created on  14 March 2022

@author: Amin
"""

# Import liberaries and functions
import argparse
import pandas as pd
from top2vec import Top2Vec
from time import strftime, gmtime
import sys
import os

# =============================================================================
# This module trains the Top2Vec model on the corpora 

# To run:
# >>> python Top2Vec_train.py --speed fast-learn
# =============================================================================

parser = argparse.ArgumentParser(description='Top2Vec model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/clean_docs_3.csv', help='path to cleaned documents')
parser.add_argument('--save_model', type=str, default='Models/T2V_model_3', help='directory to save tranied model')

### model and optimization related arguments
parser.add_argument('--speed', type=str, default='deep-learn', help='determines how fast the model trains (fast-learn, deep-learn)')
parser.add_argument('--njobs', type=int, default=-1, help='number of cpu cores to be used for training')
parser.add_argument('--batch_size', type=int, default=1000, help='input batch size for training')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"T2V_train_log_{strftime('%d%m%y', date)}.txt", "w")

print(args)
print("\n\t Top2Vec topic model training log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Read preprocessed text data as Pandas DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Loading cleaned text data ... \n")
train_docs_df = pd.read_csv(args.documents).reset_index()
train_docs = train_docs_df["cleaned_txt"].to_list()

# Create new index per document
new_ind = (
    train_docs_df[["CIK", "report_dt", "filing_dt", "index"]]
    .applymap(str)
    .apply(lambda x: " ".join(x), axis=1)
)


def tokenizer(text):
    """
    Tokenizer function to transform documents into lists of tokens.
    """
    tokens = text.split()
    return tokens

if args.njobs == -1:
    njobs = os.cpu_count()
else:
    njobs = args.njobs

print(f"{strftime('%D %H:%M', gmtime())} | Training Top2Vec model started.\n")
sys.stdout.flush()

top2vec_model = Top2Vec(
    documents=train_docs, 
    # embedding_model=model.model,
    min_count=100,
    embedding_batch_size = args.batch_size,
    speed=args.speed, 
    workers=njobs, 
    document_ids=new_ind.to_list(), 
    tokenizer=tokenizer,
    hdbscan_args = {
        'min_cluster_size': 20,
        'metric': 'euclidean',
        'cluster_selection_method': 'eom',
        'cluster_selection_epsilon' : 0.6
    }
)

print(f"{strftime('%D %H:%M', gmtime())} | Saving trained Top2Vec model to disk ...\n")

top2vec_model.save(f"{args.save_model}")

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()


