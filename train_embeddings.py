# -*- coding: utf-8 -*-
"""
Created on 15 October 2022

@author: Amin
"""

# Import libraries
import pandas as pd
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
import argparse
from time import strftime, gmtime
from Data.data import bigram
import os

"""
=============================================================================
Train Word2Vec model.

To run:
    >>> python train_embeddings.py
=============================================================================
"""
parser = argparse.ArgumentParser(description='Train W2V')

parser.add_argument('--RF_df', type=str, default='Data\W2V_train.csv', help='directory of dataframe containing risk factors')
parser.add_argument('--W2V_model', type=str, default="Models\W2V_model.model", help='directory to save trained W2V model')
parser.add_argument('--embedding', type=str, default="Models\embedding.wordvectors", help='directory to save wordvectors')

parser.add_argument('--min_count', type=float, default=0.0001, help='min count of bigrams (ratio of number of RFs)')
parser.add_argument('--n_jobs', type=int, default=36, help='Number of processors to process texts')
parser.add_argument('--epochs', type=int, default=10, help='Number of ecpochs to train the model')

args = parser.parse_args()

print(args, "\n")

print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print("Loading data ...\n")
# Loading data
rf_df = pd.read_csv(args.RF_df, index_col=0).dropna()
# Create a list of lowercase strings as training data
train_docs = rf_df['cleaned_txt'].tolist()


def token(text):
    return text.split(" ")

transformed_sents = bigram(
    raw_data = train_docs, 
    tokenizer=token,
    min_cnt = 0.0001 
)

print(f"{strftime('%D %H:%M', gmtime())} | Training word2vec embeddings ...\n")

class callback(CallbackAny2Vec):
    '''Callback to print loss after each epoch.'''

    def __init__(self):
        self.epoch = 0

    def on_epoch_end(self, model):
        if self.epoch % 5 == 0:
            model.save(f"Models\W2V_model_{self.epoch}.model")
          
        loss = model.get_latest_training_loss()
        print(f'Loss after epoch {self.epoch}: {loss}')
        self.epoch += 1


model = Word2Vec(
    transformed_sents, 
    window=5,
    min_count=5, 
    epochs=args.epochs, 
    workers=args.n_jobs,
    vector_size=300,
    sg=1,
    negative=10,
    compute_loss=True, 
    callbacks=[callback()],
    )

print("Saving Word2Vec model and trained embeddings ...\n")
model.save(args.W2V_model)

# Store just the words + their trained embeddings.
word_vectors = model.wv
word_vectors.save(args.embedding)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

