# -*- coding: utf-8 -*-
"""
Created on 15 October 2022

@author: Amin
"""

# Import libraries
import pandas as pd
from Data.data import load_data
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
import argparse
from time import strftime, gmtime
import os
import sys

"""
=============================================================================
Train Word2Vec model.

To run:
    >>> python train_embeddings.py
=============================================================================
"""
parser = argparse.ArgumentParser(description='Train W2V')

parser.add_argument('--data', type=str, default='Data\W2V_train_2.csv', help='directory of dataframe containing risk factors')
parser.add_argument('--W2V_model', type=str, default="Models\W2V_model_2.model", help='directory to save trained W2V model')
parser.add_argument('--embedding', type=str, default="Models\embedding_2.wordvectors", help='directory to save wordvectors')

parser.add_argument('--min_count', type=float, default=0.0001, help='min count of bigrams (ratio of number of RFs)')
parser.add_argument('--n_jobs', type=int, default=-1, help='Number of processors to process texts')
parser.add_argument('--epochs', type=int, default=50, help='Number of ecpochs to train the model')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"W2V_train_log_{strftime('%d%m%y', date)}.txt", "w")

print(args, "\n") 

print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print("Loading data ...\n")
# Loading data
data = load_data(args.data, low_bnd=0.08, col='cleaned_txt', index=0)

# Create a list of lowercase strings as training data
train_docs = data['cleaned_txt'].tolist()

def tokenizer(text):
    return text.split(" ")

tokenized_sents = [tokenizer(text) for text in train_docs]

print(f"{strftime('%D %H:%M', gmtime())} | Training word2vec embeddings ...\n")

class callback(CallbackAny2Vec):
    '''Callback to print loss after each epoch.'''

    def __init__(self):
        self.epoch = 0

    def on_epoch_end(self, model):
        loss = model.get_latest_training_loss()
        print(f'Loss after epoch {self.epoch}: {loss}')
        self.epoch += 1
        sys.stdout.flush()

if args.n_jobs == -1:
    njobs = os.cpu_count()
else:
    njobs = args.njobs

model = Word2Vec(
    tokenized_sents, 
    window=5,
    min_count=10, 
    epochs=args.epochs, 
    workers=njobs,
    vector_size=300,
    sg=1,
    negative=15,
    compute_loss=True, 
    callbacks=[callback()],
    )

print("Saving Word2Vec model and trained embeddings ...\n")
model.save(args.W2V_model)

# Store just the words + their trained embeddings.
word_vectors = model.wv
word_vectors.save(args.embedding)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()

