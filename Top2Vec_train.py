# -*- coding: utf-8 -*-
"""
Created on  14 March 2022

@author: Amin
"""

# Import liberaries and functions
import argparse
import pandas as pd
from top2vec import Top2Vec
from ETM.data import load_data
import sys
import pickle
from time import strftime, gmtime
import gc

# =============================================================================
# This module trains the Top2Vec model on the corpora 

# To run:
# >>> python Top2Vec_train.py --speed deep-learn --njobs 14
# =============================================================================

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--data', type=str, default='RF_df_V2.csv', help='directory containing text data in csv format')
parser.add_argument('--documents', type=str, default='cleaned_docs.pkl', help='path to cleaned documents')
parser.add_argument('--embeddings', type=str, default='W2V_model.model', help='path to trained word embedding model')
parser.add_argument('--save_model', type=str, default='RF_T2V_model', help='directory to save tranied LDA model')

### model and optimization related arguments
parser.add_argument('--speed', type=str, default='learn', help='determines how fast the model takes to train')
parser.add_argument('--njobs', type=int, default=10, help='number of cpu cores to be used for training')
parser.add_argument('--batch_size', type=int, default=1000, help='input batch size for training')

args = parser.parse_args()

sys.stdout = open(f"T2V_train_log_{strftime('%d%m%y', gmtime())}.txt", "w")

print(args)
print("\n\t Top2Vec topic model training log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print(f"{strftime('%D %H:%M', gmtime())} | Loading cleaned text data ... \n")
with open(args.documents, "rb") as f:
    train_docs = pickle.load(f)

print(f"{strftime('%D %H:%M', gmtime())} | Creating document index ... \n")
# Load raw text data as Pandas DataFrame
filtered_rf_df = load_data(args.data, up_bound=0.95, year=2004).reset_index()
filtered_rf_df['cik'] = filtered_rf_df['cik'].str.replace("Data/Risk Factors 10k/", '')
filtered_rf_df['filing year'] = filtered_rf_df['filing date'].map(lambda x: str(x)[:4])

# Create document index
new_ind = (filtered_rf_df['cik'].map(str) + '-' + 
           filtered_rf_df['reporting year'].map(str) + '-' + 
           filtered_rf_df['filing year'].map(str) + '-' + 
           filtered_rf_df["index"].map(str)).to_frame()
new_ind['tokens'] = train_docs
new_ind.drop_duplicates(subset=0, inplace=True)

del train_docs
del filtered_rf_df
gc.collect()

print(f"{strftime('%D %H:%M', gmtime())} | Training Top2Vec model started ...\n")

sys.stdout.flush()

def tokenizer_func(text):
    tokens = text.split()
    return tokens

embed_path = args.embeddings

top2vec_model = Top2Vec(
    documents=new_ind['tokens'].to_list(), embedding_model_path=embed_path, speed=args.speed, 
    workers=args.njobs, document_ids=new_ind[0].to_list(), tokenizer=tokenizer_func
    )

print(f"{strftime('%D %H:%M', gmtime())} | Training Top2Vec model ended.\n")

top2vec_model.save(args.save_model)

print(f"{strftime('%D %H:%M', gmtime())} | Trained Top2Vec model saved to disk.\n")


sys.stdout.close()


