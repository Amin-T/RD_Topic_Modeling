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
import gc

# =============================================================================
# This module trains the Top2Vec model on the corpora 

# To run:
# >>> python Top2Vec_train.py --speed deep-learn
# =============================================================================

parser = argparse.ArgumentParser(description='Top2Vec model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/T2V_train.csv', help='path to cleaned documents')
parser.add_argument('--save_model', type=str, default='Models/T2V_model_4', help='directory to save tranied model')

### model and optimization related arguments
parser.add_argument('--speed', type=str, default='learn', help='determines how fast the model trains (fast-learn, learn, deep-learn)')
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

def get_docs():
    docs_df = pd.read_csv(args.documents, parse_dates=['report_dt'])

    # Modifying the sample
    docs_df = docs_df[(docs_df['filerCIK']==docs_df['CIK'])|(docs_df['ticker'].notna())]
    SIC_df = pd.read_csv("Data/SIC_df.csv", usecols=['cik', 'sic']).drop_duplicates().dropna().astype(int)
    SIC_df.rename(columns={'cik': "CIK", 'sic': "SIC"}, inplace=True)
    docs_df = pd.merge(
        left=docs_df, 
        right=SIC_df, 
        on="CIK", how='left'
    )

    fin_sic = [6021, 6022, 6029, 6035, 6036, 6099, 6111, 6141, 6153, 6159, 6162, 6163, 6172, 6189, 
               6199, 6200, 6211, 6221, 6282, 6311, 6321, 6324, 6331, 6351, 6361, 6399, 6411]

    docs_df = docs_df[
        (docs_df['report_dt']>"2006-01-01")
        &(docs_df['report_dt']<"2024-01-01")
        &(docs_df['SIC'].notna())
        &(~docs_df['SIC'].isin(fin_sic))
    ] 
    
    return docs_df

train_docs_df = get_docs()

train_docs = train_docs_df["cleaned_txt"].to_list()

# Create new index per document
new_idx = (
    train_docs_df[["CIK", "report_dt", "filing_dt", "rf_seq"]].astype(str)
    .apply(lambda x: " ".join(x), axis=1)
)

del train_docs_df
gc.collect()


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

print(f"{strftime('%D %H:%M', gmtime())} | Training Top2Vec model on {len(train_docs)} RFs.\n")
sys.stdout.flush()

top2vec_model = Top2Vec(
    documents=train_docs, 
    embedding_model="doc2vec", # "universal-sentence-encoder-large",
    tokenizer=tokenizer,
    keep_documents=False, 
    split_documents=True, 
    max_num_chunks=4, 
    topic_merge_delta=0.5,
    min_count=int(0.0005*len(train_docs)),
    embedding_batch_size=args.batch_size,
    speed=args.speed, 
    workers=njobs, 
    document_ids=new_idx.to_list(),
    gpu_hdbscan=True, 
    gpu_umap=True,
    umap_args={'unique': True},
    hdbscan_args = {'min_cluster_size': 20}
)

print(f"{strftime('%D %H:%M', gmtime())} | Saving trained Top2Vec model to disk ...\n")

top2vec_model.save(f"{args.save_model}")

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()


