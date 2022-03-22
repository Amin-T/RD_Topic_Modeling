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

sys.stdout = open("LDA_train_log.txt", "w")

# =============================================================================
# This module trains multiple LDA models on the corpora and finds the best model 
# based on the Coherence measure.

# To run:
# >>> python LDA_train.py --dictionary RF_lda_dict --tokens RF_tokens.txt --passes 10 --chunksize 0.25 --njobs 15
# =============================================================================

parser = argparse.ArgumentParser(description='LDA model trainer')

### data and file related arguments
parser.add_argument('--dictionary', type=str, default='RF_lda_dict', help='directory containing dictionary object')
parser.add_argument('--tokens', type=str, default='RF_tokens.txt', help='directory containing tokenized text data')
parser.add_argument('--save_model', type=str, default='RF_lda_model', help='directory to save tranied LDA model')
parser.add_argument('--batch_size', type=int, default=1000, help='input batch size for training')

### model and optimization related arguments
parser.add_argument('--num_topics_start', type=int, default=50, help='min number of topics to be trained')
parser.add_argument('--num_topics_limit', type=int, default=500, help='max number of topics to be trained')
parser.add_argument('--topic_lr_L', type=int, default=25, help='step of number of topics for initial training')
parser.add_argument('--topic_lr_s', type=int, default=5, help='step for number of topics fine tuning')
parser.add_argument('--passes', type=int, default=10, help='Number of passes through the corpus during training')
parser.add_argument('--chunksize', type=float, default=0.25, help='fraction of documents to be used in each training chunk')
parser.add_argument('--stop_factor', type=int, default=3, help='stopping criteria')

parser.add_argument('--njobs', type=int, default=None, help='number of cpu cores to be used for training')

args = parser.parse_args()

# Load saved dictionary object
lda_dict = corpora.Dictionary.load(args.dictionary)

# Load text data tokens
with open(args.tokens, "rb") as fp:
    tokens = pickle.load(fp)

# Create corpus from Dictionary
lda_corpus = [lda_dict.doc2bow(text) for text in tokens]

# Set number of documents to be used in each training chunk
chunksize = int(len(tokens)*args.chunksize)


def coherence_optimizer(dictionary, corpus, limit, start, step, npass = args.passes):
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
            alpha='asymmetric', passes = npass, chunksize=chunksize,
            decay=0.5, offset=64 # best params from Hoffman paper
            )
        
        cm = CoherenceModel(model=model, corpus=corpus, dictionary=dictionary, coherence='u_mass')
        cm_score = cm.get_coherence()
        coherence_models[num_topics] = (cm_score, model)
        CVs.append(cm_score)
        
        print(f'Model with {num_topics} topics >>> Coherence score: {cm_score:.5f}')

        # Check the stopping criteria
        if all(cm_score > i for i in CVs[-args.stop_factor-1:-1]):
            print("Stopping criteria met ... \n")
            break
        else:
            continue

    return coherence_models

print("Training LDA model started.\n")

print(f"Finding optimal number of topics with learning rate = {args.topic_lr_L}")
init_coherence_model = coherence_optimizer(
    lda_dict, lda_corpus, 
    limit=args.num_topics_limit, start=args.num_topics_start, step=args.topic_lr_L,
    npass=3
    )

# Identifying the initial optimal number of topics on coherence scores
init_best_NT = min(init_coherence_model, key=lambda x: init_coherence_model[x][0])

del init_coherence_model
gc.collect()

print(f"Fine tuning the number of topics with learning rate = {args.topic_lr_s}")
# Set new range for number of topics
num_topics_start = max(int(init_best_NT - 2*args.topic_lr_L), 0)
num_topics_limit = int(init_best_NT + 2*args.topic_lr_L)

coherence_model = coherence_optimizer(
    lda_dict, lda_corpus, 
    limit=num_topics_limit, start=num_topics_start, step=args.topic_lr_s
    )

print("Training ended.\n")

# Identifying the best model based on coherence scores
best_num_topics = min(coherence_model, key=lambda x: coherence_model[x][0])
print(f"Number of topics for the best model: {best_num_topics}\n")

best_model = coherence_model[best_num_topics][1]

best_model.save(args.save_model)

print('Best LDA model saved to disk.\n')

sys.stdout.close()

# num_topics = [len(x[1].stable_topics) for x in coherence_model.values()]
# coherence_values = [-x[0] for x in coherence_model.values()]

# fig = plt.figure(figsize=(10,6))
# plt.scatter(num_topics, coherence_values, alpha=0.5)
# plt.xlabel("Num Topics")
# plt.ylabel("Coherence score")
# plt.legend(("coherence_values"), loc='best')
# plt.savefig('models2.png')
# plt.show()


