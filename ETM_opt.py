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
import argparse
from embedded_topic_model.models.etm import ETM
from utils import create_etm_datasets
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
from octis.evaluation_metrics.diversity_metrics import InvertedRBO
import matplotlib.pyplot as plt
plt.style.use('seaborn')
plt.rc('figure', autolayout=True)

"""
=============================================================================
Multiple ETM models are trained to find the best model based on the topics' overall Quality.
Training is done in 2 stapes:
    Initial Training: Search for the optimal number of topics over a large interval, by training ETM models on a
        fraction of the whole dataset. A large step size is used.
    Fine Tuning: The more precise optimal number of topics is found by searching around the intial number of topics
        using a smaller step size and training the ETM models on the dataset.

To run:
>>> python ETM_opt.py --n_start 10 --n_limit 50 --n_step 10 --train_size 0.8 --epochs 10 --batch_size 2000
=============================================================================
"""

parser = argparse.ArgumentParser(description='ETM model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/clean_docs.csv', help='path to cleaned documents')
parser.add_argument('--embeddings', type=str, default='Models/embedding.wordvectors', help='path to word vectors (trained embeddings)')
parser.add_argument('--save_model', type=str, default='Models/ETM_model', help='directory to save tranied ETM model')

### arguments related to data
parser.add_argument('--min_df', type=float, default=100, help='Minimum document-frequency for terms. Removes terms with a frequency below this threshold')
parser.add_argument('--max_df', type=float, default=0.95, help='Maximum document-frequency for terms. Removes terms with a frequency above this threshold')
parser.add_argument('--train_size', type=float, default=0.8, help='fraction of the original corpus to be used for the train dataset')

### arguments related to model and training
parser.add_argument('--epochs', type=int, default=50, help='number of epochs to train')
parser.add_argument('--batch_size', type=int, default=5000, help='input batch size for training')
parser.add_argument('--perplexity', type=int, default=1, help='whether to compute perplexity on document completion task')
parser.add_argument('--n_start', type=int, default=10, help='min number of topics to be trained')
parser.add_argument('--n_limit', type=int, default=250, help='max number of topics to be trained')
parser.add_argument('--n_step', type=int, default=20, help='step for number of topics')
parser.add_argument('--topn', type=int, default=10, help='the number of top words to be extracted from each topic')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"ETM_opt_log_{strftime('%d%m%y', date)}.txt", "w")

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
    train_size=args.train_size
)

with open(f"ETM_idx_train_{strftime('%d%m%y', date)}.pkl", 'wb') as f:
    pickle.dump(idx_train, f)

if args.train_size >= 1:
    texts = [doc.split() for doc in train_docs]
else:
    texts = [[vocabulary[i] for i in doc] for doc in train_dataset["tokens"]]
dictionary = Dictionary(documents=texts)

del train_docs_df
del train_docs

print(f"{strftime('%D %H:%M', gmtime())} | Load word vectors with memory-mapping ... \n")
wv = KeyedVectors.load(args.embeddings, mmap='r')

def model_optimizer(vocab, embs, train_data, limit, start, step, test_data=None):
    """
    Finding the best number of topics based on the overall quality of models' topics
    >>> Quality = product of topic coherence and inverse topic perplexity

    Parameters:
    ----------
    vocab (list of str): training dataset vocabulary
    embs (str or KeyedVectors): KeyedVectors instance containing word-vector mapping for embeddings, or its path
    train_data (dict): BOW training dataset, split in tokens and counts
    limit (int): max number of topics to be trained
    start (int): min number of topics to be trained
    step (int): step for number of topics
    test_data (dict): optional. BOW testing dataset, split in tokens and counts. Used for perplexity calculation, if activated

    Returns:
    -------
    metrics : dict > keys: number of topics, values: (topic coherance, topic perplexity, topic quality)
    best_model : the model with the best quality
    """

    # Create initial objects for model metrics and the best model
    metrics = {}
    best_model = None
    a_epochs = args.epochs
    a_batch_size = args.batch_size
    a_perplexity = bool(args.perplexity)

    # Training an ETM instance for the range of topics   
    for num_topics in range(start, limit, step):
        etm_instance = ETM(
            vocabulary = vocab,
            embeddings = embs, 
            num_topics = num_topics,
            epochs = a_epochs,
            batch_size = a_batch_size,
            debug_mode = False,
            train_embeddings = False,
            eval_perplexity = a_perplexity
        )

        etm_instance.fit(train_data, test_data)

        topics = {'topics': etm_instance.get_topics(50)}

        print(".....")
        TC_metric = CoherenceModel(
            topics=topics['topics'], 
            texts=texts, 
            dictionary=dictionary, 
            coherence='c_v', 
            topn=args.topn, 
            processes=os.cpu_count()
        )
        TC = TC_metric.get_coherence()

        TP = etm_instance._perplexity(test_data)/1000

        # IRBO takes values in the range [0, 1]. Higher mean more diversified
        IRBO_metric = InvertedRBO(topk=args.topn)
        IRBO = IRBO_metric.score(topics)
        
        TQ = TC/TP

        metrics[num_topics] = (TC, TP, TQ, IRBO)

        print(f"{strftime('%D %H:%M', gmtime())} | Model with {num_topics} topics >>>\
            \n\t Coherence: {TC:.5f}\
            \n\t Perplexity: {TP:.5f}\
            \n\t IRBO: {IRBO:.5f}\
            \n\t Quality: {TQ:.5f}")

        # Only keep the best model so far
        if TQ >= max(m[2] for m in metrics.values()):
            best_model = etm_instance

        sys.stdout.flush()

    return metrics, best_model

print(f"{strftime('%D %H:%M', gmtime())} | Training ETM models started ...\n")
sys.stdout.flush()

scores, etm_model = model_optimizer(
    vocab=vocabulary, 
    embs=wv, 
    train_data=train_dataset, 
    limit=args.n_limit+1, start=args.n_start, step=args.n_step, 
    test_data=test_dataset
)

print(f"\n{strftime('%D %H:%M', gmtime())} | Training ETM models ended.")

# Identifying the best model based on topic quality
best_num_topics = max(scores, key=lambda n: scores[n][2])
print(f" --> Number of topics for the best model: {best_num_topics}\n")

print(f"{strftime('%D %H:%M', gmtime())} | Saving best ETM model ...\n")
with open(f"{args.save_model}_{strftime('%d%m%y', date)}.pkl", "wb") as f:
    pickle.dump(etm_model, f)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()

num_topics = scores.keys()
TS = scores.values()
Coherence = [x[0] for x in TS]
inv_Perplexity = [1/x[1] for x in TS]
Quality = [x[2] for x in TS]

fig, ax = plt.subplots(figsize=(12,8))
ax.plot(num_topics, Coherence, label="Coherence")
ax.plot(num_topics, inv_Perplexity, ls='-.', label="inv_Perplexity")
ax.plot(num_topics, Quality, ls='--', label="Quality")
plt.xlabel("Num Topics")
ax.legend(loc='best')
ax.grid(alpha=1)
plt.savefig(f"ETM_models_{strftime('%d%m%y', date)}.png")

