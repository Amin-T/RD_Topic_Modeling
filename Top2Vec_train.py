# -*- coding: utf-8 -*-
"""
Created on  14 March 2022

@author: Amin
"""

# Import liberaries and functions
import argparse
import pandas as pd
from top2vec import Top2Vec
import spacy
nlp = spacy.load('en_core_web_sm')
import gc
import sys

# =============================================================================
# This module trains the Top2Vec model on the corpora 

# To run:
# >>> python Top2Vec_train.py --speed deep-learn --njobs 15
# =============================================================================

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--data', type=str, default='RF_df.csv', help='directory containing text data in csv format')
parser.add_argument('--save_model', type=str, default='RF_T2V_model', help='directory to save tranied LDA model')

parser.add_argument('--batch_size', type=int, default=1000, help='input batch size for training')

### model and optimization related arguments
parser.add_argument('--speed', type=str, default='learn', help='determines how fast the model takes to train')

parser.add_argument('--njobs', type=int, default=None, help='number of cpu cores to be used for training')

args = parser.parse_args()

sys.stdout = open("log_Top2Vec_train.txt", "w")

def tokenizer_func(text):
    doc = nlp(text)

    # Identify named entities
    # ents = [ent.lemma_.lower() for ent in doc.ents]

    # To remove stop words, punctuations, and currency tokens
    mask = lambda t: not (t.is_stop or t.is_punct or t.is_currency or t.is_space)
    tokens = [tok.lemma_.lower() for tok in filter(mask, doc)]

    # tokens.extend(ents)
    return tokens

# Read preprocessed text data as Pandas DataFrame
RF_df = pd.read_csv(args.data, index_col=0)

# Filter too short and too long docs (risk factors)
# based on 5th and 99th percentiles
word_cnt = RF_df['Item 1A'].astype(str).map(lambda x: len(x.split()))
Q05 = word_cnt.quantile(q=0.05)
Q99 = word_cnt.quantile(q=0.99)

print(f'5-th percentile: {Q05}')
print(f'99-th percentile: {Q99}')

filtered_rf_df = RF_df[(word_cnt>Q05) & (word_cnt<Q99)]

# Create new index per document
new_ind = (filtered_rf_df['cik'].map(str) + '-' + 
           filtered_rf_df['reporting year'].map(str) + '-' + 
           filtered_rf_df['filing date'].map(str) + '-' + 
           filtered_rf_df.index.map(str))

raw_text_data = filtered_rf_df.set_index(new_ind)['Item 1A']

print("Training Top2Vec model started.\n")

top2vec_model = Top2Vec(
    documents=raw_text_data.tolist(), speed=args.speed, 
    workers=args.njobs, document_ids=raw_text_data.index.tolist(), tokenizer=tokenizer_func)

print("Training ended.\n")

print('Trained Top2Vec model saved to disk.\n')

top2vec_model.save(args.save_model)
