# -*- coding: utf-8 -*-
"""
Created on Thu May 26 2022

@author: Amin
"""

# Import liberaries
import pandas as pd
import os
import pickle
from time import gmtime, strftime
import sys
from gensim.models import KeyedVectors
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
import argparse
from embedded_topic_model.models.etm import ETM
from utils import create_etm_datasets


"""
=============================================================================
To run:
>>> python ETM_train.py --opt_N 160
=============================================================================
"""

parser = argparse.ArgumentParser(description='ETM model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/clean_docs.csv', help='path to cleaned documents')
parser.add_argument('--embeddings', type=str, default='Models/embedding.wordvectors', help='path to word vectors (trained embeddings)')
parser.add_argument('--save_model', type=str, default='Models/ETM_best_model.pkl', help='directory to save tranied ETM model')

### arguments related to data
parser.add_argument('--min_df', type=float, default=100, help='Minimum document-frequency for terms. Removes terms with a frequency below this threshold')
parser.add_argument('--max_df', type=float, default=0.95, help='Maximum document-frequency for terms. Removes terms with a frequency above this threshold')

### arguments related to model and training
parser.add_argument('--epochs', type=int, default=50, help='number of epochs to train')
parser.add_argument('--batch_size', type=int, default=1000, help='input batch size for training')
parser.add_argument('--opt_N', type=int, default=None, help='optimal number of topics obtained')
parser.add_argument('--topn', type=int, default=10, help='the number of top words to be extracted from each topic')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"ETM_train_log_{strftime('%d%m%y', date)}.txt", "w")

print(args)
print("\n\t ETM topic model training log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print(f"{strftime('%D %H:%M', gmtime())} | Loading cleaned text data ... \n")
train_docs_df = pd.read_csv(args.documents)
train_docs = train_docs_df["cleaned_txt"].to_list()

# Create vocabulary and datasets compatible to embedded_topic_model package
vocabulary, train_dataset, test_dataset, idx_train, idx_test = create_etm_datasets(
    train_docs,
    min_df=args.min_df, 
    max_df=args.max_df, 
    train_size=1
)

with open(f"ETM_idx_train_{strftime('%d%m%y', date)}.pkl", 'wb') as f:
    pickle.dump(idx_train, f)

texts = [doc.split() for doc in train_docs]
dictionary = Dictionary(documents=texts)

del train_docs_df
del train_docs

print(f"{strftime('%D %H:%M', gmtime())} | Load word vectors with memory-mapping ... \n")
wv = KeyedVectors.load(args.embeddings, mmap='r')

# Create initial objects for model metrics and the best model
a_epochs = args.epochs
a_batch_size = args.batch_size

print(f"{strftime('%D %H:%M', gmtime())} | Training ETM models started ...\n")
sys.stdout.flush()

best_model = ETM(
    vocabulary = vocabulary,
    embeddings = wv, 
    num_topics = args.opt_N,
    epochs = a_epochs,
    batch_size = a_batch_size,
    debug_mode = True,
    visualize_every = 50,
    train_embeddings = False,
)

best_model.fit(train_dataset)

print(f"{strftime('%D %H:%M', gmtime())} | Training ETM models ended.\n")

print(f"{strftime('%D %H:%M', gmtime())} | Saving best ETM model ...\n")
sys.stdout.flush()

with open(args.save_model, "wb") as f:
    pickle.dump(best_model, f)

topics = {'topics': best_model.get_topics(30)}

print(f"{strftime('%D %H:%M', gmtime())} | Calculating topics coherence ...")
sys.stdout.flush()

TC_metric = CoherenceModel(
    topics=topics['topics'], 
    texts=texts, 
    dictionary=dictionary, 
    coherence='c_v', 
    topn=args.topn, 
    processes=os.cpu_count()
)

TC = TC_metric.get_coherence()

print(f" --> Coherence = {TC:.5f}\n")

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()

