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
import pickle
import gc


"""
=============================================================================

To run:
>>> python T2V_HReduce.py --n_start 10 --n_limit 50 --optimization 1
=============================================================================
"""

parser = argparse.ArgumentParser(description='T2V H_Reduce')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/T2V_train.csv', help='path to cleaned documents')
parser.add_argument('--model', type=str, default='Models/T2V_model_4', help='Initially trained T2V model')
parser.add_argument('--save_model', type=str, default='Models/', help='directory to save tranied ETM model')

### arguments related to model and training
parser.add_argument('--n_start', type=int, default=20, help='min number of topics to be trained')
parser.add_argument('--n_limit', type=int, default=300, help='max number of topics to be trained')
parser.add_argument('--n_step', type=int, default=20, help='step for number of topics')
parser.add_argument('--topn', type=int, default=15, help='the number of top words to be extracted from each topic')

parser.add_argument('--optimization', type=int, default=1, help='optimization of N (1) or saving the model with optimal N')

args = parser.parse_args()

date = gmtime()
sys.stdout = open(f"T2V_HReduce_log_{strftime('%d%m%y', date)}.txt", "w")

print(args)
print("\n\t T2V model hierarchical reduction log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

print(f"{strftime('%D %H:%M', gmtime())} | Loading trained T2V model ... \n")

T2V_model = Top2Vec.load(args.model)

if args.optimization ==1:
    print(f"{strftime('%D %H:%M', gmtime())} | Loading cleaned text data ... \n")

    def get_docs():
        docs_df = pd.read_csv(args.documents, parse_dates=['report_dt'])

        # Modifying the sample
        docs_df = docs_df[(docs_df['filerCIK']==docs_df['CIK'])|(docs_df['ticker'].notna())]
        SIC_df = pd.read_csv("Data/SIC_df.csv", usecols=['cik', 'sic']).drop_duplicates().dropna().astype(int)
        SIC_df.rename(columns={'cik': "CIK", 'sic': "SIC"}, inplace=True)
        docs_df = pd.merge(
            left=docs_df, 
            right=SIC_df, 
            on="CIK", how='left'
        )

        fin_sic = [6021, 6022, 6029, 6035, 6036, 6099, 6111, 6141, 6153, 6159, 6162, 6163, 6172, 6189, 
                6199, 6200, 6211, 6221, 6282, 6311, 6321, 6324, 6331, 6351, 6361, 6399, 6411]

        docs_df = docs_df[
            (docs_df['report_dt']>"2006-01-01")
            &(docs_df['report_dt']<"2024-01-01")
            &(docs_df['SIC'].notna())
            &(~docs_df['SIC'].isin(fin_sic))
        ] 
        
        return docs_df["cleaned_txt"].to_list()

    train_docs = get_docs()

    print(f"{strftime('%D %H:%M', gmtime())} | Creating dictionary from traning documents ... \n")
    texts = [doc.split() for doc in train_docs]
    dictionary = Dictionary(documents=texts)

    num_topic_range = range(args.n_start, args.n_limit+1, args.n_step)

    gc.collect()

    def model_optimizer(num_topics):
        """
        Finding the best number of topics based on the topic quality measures.
        """
        # Create initial objects for model metrics and the best model
        
        T2V_model.hierarchical_topic_reduction(num_topics)
        topics = T2V_model.topic_words_reduced

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
        
        metrics = {'num_topics': num_topics, 'TC': TC, 'IRBO': IRBO}

        return metrics

    print(f"{strftime('%D %H:%M', gmtime())} | Topic reduction started ...\n")
    sys.stdout.flush()

    scores = []
    for N in num_topic_range:
        s = model_optimizer(N)
        print(f"\n{strftime('%D %H:%M', gmtime())} | Model with {N} topics >>>\
            \n\t Coherence: {s['TC']:.5f}\
            \n\t IRBO: {s['IRBO']:.5f}")
        sys.stdout.flush()
        scores.append(s)
        gc.collect()


    # Saving quality scores
    all_scores = pd.DataFrame(scores)
    all_scores.to_excel(f"T2V_HR_scores_{strftime('%d%m%y', date)}.xlsx")

else:
    T2V_model.hierarchical_topic_reduction(110)

    T2V_model.save(f"{args.save_model}")

    document_ids = T2V_model.document_ids.tolist()
    t2v_df = pd.DataFrame(data={"Docs": document_ids, "Topic": T2V_model.doc_top, "Score": T2V_model.doc_dist,
                                "Topic_H": T2V_model.doc_top_reduced, "Score_H": T2V_model.doc_dist_reduced})

    t2v_df[['CIK', 'Report_dt', 'Filing_dt', 'rf_seq']] = t2v_df["Docs"].str.split(" ", expand=True)

    t2v_df.to_csv("T2V_df_4.csv", index=False)

    topics = T2V_model.topic_words_reduced
    T2V_tw = pd.DataFrame(data=topics)
    T2V_tw.to_csv("T2V_tw_4.csv")

    topic_word_dist = T2V_model.topic_word_scores_reduced
    with open("T2V_wdist_4.pkl", 'wb') as f:
        pickle.dump(topic_word_dist, f)


print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

sys.stdout.close()

