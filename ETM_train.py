# -*- coding: utf-8 -*-
"""
Created on Thu May 26 2022

@author: Amin
"""

# Import liberaries
import pickle
from time import gmtime, strftime
import sys
from gensim.models import KeyedVectors
import argparse
from embedded_topic_model.models.etm import ETM
from utils import create_etm_datasets
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary
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
        using a smaller step size and training the LDA models on the dataset.

To run:
>>> python ETM_train_v2.py --n_start 90 --n_limit 130 --n_step 10 --train_size 0.8 --workers 16
=============================================================================
"""

parser = argparse.ArgumentParser(description='ETM model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='cleaned_docs.pkl', help='path to cleaned documents')
parser.add_argument('--embeddings', type=str, default='embeddings.wordvectors', help='path to word vectors (trained embeddings)')
parser.add_argument('--save_model', type=str, default='RF_etm_model.pkl', help='directory to save tranied ETM model')

### arguments related to data
parser.add_argument('--min_df', type=float, default=0.0005, help='Minimum document-frequency for terms. Removes terms with a frequency below this threshold')
parser.add_argument('--max_df', type=float, default=0.9, help='Maximum document-frequency for terms. Removes terms with a frequency above this threshold')
parser.add_argument('--train_size', type=float, default=1, help='fraction of the original corpus to be used for the train dataset')

### arguments related to model and training
parser.add_argument('--epochs', type=int, default=30, help='number of epochs to train')
parser.add_argument('--batch_size', type=int, default=5000, help='input batch size for training')
parser.add_argument('--workers', type=int, default=14, help='number of cpu cores for calculating coherence')
parser.add_argument('--perplexity', type=int, default=1, help='whether to compute perplexity on document completion task')
parser.add_argument('--n_start', type=int, default=10, help='min number of topics to be trained')
parser.add_argument('--n_limit', type=int, default=250, help='max number of topics to be trained')
parser.add_argument('--n_step', type=int, default=20, help='step for number of topics')

args = parser.parse_args()

if __name__ == '__main__':

    sys.stdout = open(f"ETM_train_log_{strftime('%d%m%y', gmtime())}.txt", "w")

    print(args)
    print("\n\t ETM topic model training log\n\n")
    print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

    print(f"{strftime('%D %H:%M', gmtime())} | Loading cleaned text data ... \n")
    with open(args.documents, "rb") as f:
        train_docs = pickle.load(f)

    # Create vocabulary and datasets compatible to embedded_topic_model package
    vocabulary, train_dataset, test_dataset, idx_train, idx_test = create_etm_datasets(
        train_docs,
        min_df=args.min_df, 
        max_df=args.max_df, 
        train_size=args.train_size
    )

    with open(f"ETM_idx_train_{args.train_size}.pkl", 'wb') as f:
        pickle.dump(idx_train, f)

    if args.train_size >= 1:
        texts = [doc.split() for doc in train_docs]
    else:
        texts = [[vocabulary[i] for i in doc] for doc in train_dataset["tokens"]]
    dictionary = Dictionary(documents=texts)

    del train_docs

    print(f"{strftime('%D %H:%M', gmtime())} | Load word vectors with memory-mapping ... \n")
    wv = KeyedVectors.load(args.embeddings, mmap='r')

    def model_optimizer(vocab, embs, train_data, limit, start, step, test_data=None):
        """
        Finding the best number of topics based on the overall quality of models' topics
        >>> Quality = product of topic coherence and inverse topic perplexity

        Parameters:
        ----------
        
        
        Returns:
        -------
        metrics : dict > keys: number of topics, values: (topic coherance, topic diversity, topic quality)
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
            
            topics = [l for l in etm_instance.get_topics(30)]

            print(".....")
            cm = CoherenceModel(topics=topics, texts=texts, dictionary=dictionary, coherence='c_v', topn=10, processes=args.workers)
            TC = cm.get_coherence()

            TP = etm_instance._perplexity(test_data)

            TQ = TC/TP
            metrics[num_topics] = (TC, TP, TQ)

            print(f"{strftime('%D %H:%M', gmtime())} | Model with {num_topics} topics >>> \n\t Quality: {TQ:.5f}\n\t Coherence: {TC:.5f}\n\t Perplexity: {TP:.5f}")

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
    with open(args.save_model, "wb") as f:
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
    plt.savefig(f"ETM_models_{strftime('%d%m%y', gmtime())}.png")

