# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 2022

@author: Amin
"""

# Import liberaries
import pandas as pd
import os
from time import gmtime, strftime
import sys
import argparse
from top2vec import Top2Vec
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
from octis.evaluation_metrics.diversity_metrics import InvertedRBO


"""
=============================================================================

To run:
>>> python T2V_HReduce.py --n_start 10 --n_limit 50
=============================================================================
"""

parser = argparse.ArgumentParser(description='T2V H_Reduce')

### data and file related arguments
parser.add_argument('--model', type=str, default='Models/T2V_model_3', help='Initially trained T2V model')
parser.add_argument('--save_model', type=str, default='Models/T2V_model_3_H', help='directory to save tranied ETM model')

### arguments related to model and training
parser.add_argument('--n_start', type=int, default=10, help='min number of topics to be trained')
parser.add_argument('--n_limit', type=int, default=310, help='max number of topics to be trained')
parser.add_argument('--n_step', type=int, default=20, help='step for number of topics')
parser.add_argument('--topn', type=int, default=15, help='the number of top words to be extracted from each topic')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"T2V_HReduce_log_{strftime('%d%m%y', date)}.txt", "w")

print(args)
print("\n\t T2V model hierarchical reduction log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print(f"{strftime('%D %H:%M', gmtime())} | Loading trained T2V model ... \n")

T2V_model = Top2Vec.load(args.model)

print(f"{strftime('%D %H:%M', gmtime())} | Creating dictionary from traning documents ... \n")
texts = [doc.split() for doc in T2V_model.documents]
dictionary = Dictionary(documents=texts)

def model_optimizer(model, limit, start, step):
    """
    Finding the best number of topics based on the topic quality measures.
    """

    # Create initial objects for model metrics and the best model
    metrics = {}
    best_model = None

    # Training an ETM instance for the range of topics   
    for num_topics in range(start, limit, step):
        model.hierarchical_topic_reduction(num_topics)
        topics = model.topic_words_reduced

        print(".....")
        TC_metric = CoherenceModel(
            topics=topics, 
            texts=texts, 
            dictionary=dictionary, 
            coherence='c_v', 
            topn=args.topn, 
            processes=os.cpu_count()
        )
        TC = TC_metric.get_coherence()

        # IRBO takes values in the range [0, 1]. Higher mean more diversified
        IRBO_metric = InvertedRBO(topk=args.topn)
        IRBO = IRBO_metric.score({"topics": topics})
        
        metrics[num_topics] = (TC, IRBO)

        print(f"{strftime('%D %H:%M', gmtime())} | Model with {num_topics} topics >>>\
            \n\t Coherence: {TC:.5f}\
            \n\t IRBO: {IRBO:.5f}")

        sys.stdout.flush()

    return metrics

print(f"{strftime('%D %H:%M', gmtime())} | Topic reduction started.\n")
sys.stdout.flush()

print(f"{strftime('%D %H:%M', gmtime())} | Results  ...\n")
scores = model_optimizer(
    model=T2V_model,
    limit=args.n_limit+1, 
    start=args.n_start, 
    step=args.n_step, 
)

# Saving quality scores
all_scores = pd.DataFrame(scores)
all_scores.to_excel(f"ETM_opt_scores_{strftime('%d%m%y', date)}.xlsx")

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()


