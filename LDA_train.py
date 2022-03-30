# -*- coding: utf-8 -*-
"""
Created on  10 March 2022

@author: Amin
"""

# Import liberaries and functions
import argparse
import pickle
import numpy as np
import matplotlib.pyplot as plt
import gensim.corpora as corpora
from gensim.models import CoherenceModel, LdaMulticore
import gc
import sys
from random import sample
from time import strftime, gmtime

sys.stdout = open("LDA_train_log.txt", "w")

"""
=============================================================================
This module trains multiple LDA models on the corpora and finds the best model based on the Coherence measure.
Training is done in 2 stapes:
    Initial Training: Search for the optimal number of topics over a large interval, by training LDA models on a
        fraction of the whole dataset. A large step size is used.
    Fine Tuning: The more precise optimal number of topics is found by searching around the intial number of topics
        using a smaller step size and training the LDA models on the dataset.

To run:
>>> python LDA_train.py --dictionary RF_lda_dict --tokens RF_tokens.txt --passes 10 --chunksize 0.25 --njobs 15
=============================================================================
"""

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--dictionary', type=str, default='RF_lda_dict', help='directory containing dictionary object')
parser.add_argument('--tokens', type=str, default='RF_tokens.txt', help='directory containing tokenized text data')
parser.add_argument('--save_model', type=str, default='RF_lda_model', help='directory to save tranied LDA model')

### arguments related to Initial Training
parser.add_argument('--num_topics_start', type=int, default=100, help='min number of topics to be trained')
parser.add_argument('--num_topics_limit', type=int, default=500, help='max number of topics to be trained')
parser.add_argument('--topic_lr_L', type=int, default=25, help='step of number of topics for initial training')
parser.add_argument('--init_passes', type=int, default=2, help='Number of passes through the corpus during initial training')
parser.add_argument('--sample_size', type=float, default=0.25, help='fraction of documents to be used in initial training stage')

### arguments related to Fine Tuning
parser.add_argument('--topic_lr_s', type=int, default=5, help='step for number of topics fine tuning')
parser.add_argument('--passes', type=int, default=10, help='Number of passes through the corpus during fine tuning')
parser.add_argument('--chunksize', type=float, default=None, help='fraction of documents to be used in each training chunk')

### Model and optimization arguments
parser.add_argument('--stop_factor', type=int, default=3, help='stopping criteria')
parser.add_argument('--njobs', type=int, default=None, help='number of cpu cores to be used for training')

args = parser.parse_args()

print(f"{strftime('%D %H:%M', gmtime())} | Loading data ...\n")
# Load saved dictionary object
lda_dict = corpora.Dictionary.load(args.dictionary)

# Load text data tokens
with open(args.tokens, "rb") as fp:
    tokens = pickle.load(fp)

# Create corpus from Dictionary
lda_corpus = [lda_dict.doc2bow(text) for text in tokens]

if args.chunksize:
    # Set number of documents to be used in each training chunk
    chunksize = int(len(tokens)*args.chunksize)


def coherence_optimizer(dictionary, corpus, limit, start, step, npass = args.init_passes, init_train=False):
    """
    Compute coherence for num_topics in a specific range

    Parameters:
    ----------
    dictionary : Gensim dictionary
    corpus : Gensim corpus
    limit : Max num of topics

    Returns:
    -------
    coherence_models : Coherence values corresponding to the LDA model with respective number of topics
    """

    # Create initial list of coherence scores
    CVs = args.stop_factor*[np.inf]

    coherence_models = {}
    
    for num_topics in range(start, limit, step):

        # Train ensemble LDA model
        model = LdaMulticore(
            corpus=corpus, id2word=dictionary, num_topics=num_topics, 
            random_state=101, workers=args.njobs,
            alpha='asymmetric', passes = npass, 
            chunksize=4000, decay=0.5, offset=64 # best params from Hoffman paper
            )
        
        cm = CoherenceModel(model=model, corpus=corpus, dictionary=dictionary, coherence='u_mass')
        cm_score = cm.get_coherence()
        CVs.append(cm_score)

        if init_train:
            coherence_models[num_topics] = cm_score
        else:
            coherence_models[num_topics] = (cm_score, model)

        
        print(f"{strftime('%D %H:%M', gmtime())} | Model with {num_topics} topics >>> Coherence score: {cm_score:.5f}")

        # Check the stopping criteria
        if all(cm_score > i for i in CVs[-args.stop_factor-1:-1]):
            print(f"\n {strftime('%D %H:%M', gmtime())} | Stopping criteria met ... \n")
            break
        else:
            continue

    return coherence_models

print(f"{strftime('%D %H:%M', gmtime())} | Training LDA model started.\n")

print(f"Finding optimal number of topics with learning rate = {args.topic_lr_L}\n")

# Create a random sample of the corpus
init_lda_corpus = sample(lda_corpus, k=int(args.sample_size*len(lda_corpus)))

init_coherences = coherence_optimizer(
    lda_dict, init_lda_corpus, 
    limit=args.num_topics_limit, start=args.num_topics_start, step=args.topic_lr_L,
    npass=args.init_passes, init_train=True
    )

# Identifying the initial optimal number of topics on coherence scores
init_best_NT = min(init_coherences, key=lambda x: init_coherences[x])

print(f"{strftime('%D %H:%M', gmtime())} | Fine tuning the number of topics with learning rate = {args.topic_lr_s}\n")
# Set new range for number of topics
num_topics_start = max(int(init_best_NT - args.topic_lr_L), 2)
num_topics_limit = int(init_best_NT + args.topic_lr_L) + 1

coherence_model = coherence_optimizer(
    lda_dict, lda_corpus, 
    limit=num_topics_limit, start=num_topics_start, step=args.topic_lr_s,
    npass=args.passes, init_train=False
    )

print(f"{strftime('%D %H:%M', gmtime())} | Training ended.\n")

# Identifying the best model based on coherence scores
best_num_topics = min(coherence_model, key=lambda x: coherence_model[x][0])
print(f"Number of topics for the best model: {best_num_topics}\n")

best_model = coherence_model[best_num_topics][1]

best_model.save(args.save_model)

print(f"{strftime('%D %H:%M', gmtime())} | Best LDA model saved to disk.\n")

sys.stdout.close()

num_topics = list(coherence_model.keys())
coherence_values = [-x[0] for x in coherence_model.values()]

fig = plt.figure(figsize=(10,6))
plt.plot(num_topics, coherence_values, alpha=0.5)
plt.xlabel("Num Topics")
plt.ylabel("Coherence score")
plt.legend(("coherence_values"), loc='best')
plt.savefig('models.png')
plt.show()
