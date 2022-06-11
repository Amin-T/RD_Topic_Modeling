# -*- coding: utf-8 -*-
"""
Created on Thu May 26 2022

@author: Amin
"""

# Import liberaries
import pandas as pd
import pickle
from time import gmtime, strftime
import spacy
nlp = spacy.load('en_core_web_sm')

from gensim.models import Phrases

def load_data(path, low_bound=0.1, up_bound=1.0, year=2000):
    """
    Load the Risk Factors .csv file and apply filters on:
        > low_bound: min length of the doc in column "Itam 1A"
        > up_bound: max length of the doc in column "Itam 1A"
        > year: keep annual report of after specified "year"
    """

    print("Loading data ...\n")

    RF_df = pd.read_csv(filepath_or_buffer=path, index_col=0)

    word_cnt = RF_df['Item 1A'].astype('str').map(lambda x: len(x.split()))
    Qup = word_cnt.quantile(q=up_bound)
    Qlow = word_cnt.quantile(q=low_bound)

    print(f"Documents with less than {Qlow} and more than {Qup}, and annual reports before {year+1} are dropped\n")
    filtered_rf_df = RF_df[(word_cnt>Qlow) & (word_cnt<Qup) & (RF_df["reporting year"]>year)]

    return filtered_rf_df

# print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# # Load raw text data
# filtered_rf_df = load_data("LDA\RF_model\V2\RF_df_V2.csv", up_bound=0.95, year=2004)
# train_docs = filtered_rf_df['Item 1A'].str.lower().tolist()

# del filtered_rf_df

# def clean(doc):
#     # To remove stop words, punctuations, numbers, etc.
#     mask = lambda t: (t.is_alpha or t.pos==96) and not t.is_stop 
#     tokens = (tok.text for tok in filter(mask, doc))
#     return tokens

# # Memory friendly iterator
# class MyCorpus:
#     """An iterator that yields sentences (lists of str)."""
#     def __iter__(self):
#         corpus = nlp.pipe(train_docs)
#         for doc in corpus:
#             yield clean(doc=doc)

# sentences = MyCorpus()

# print(f"{strftime('%D %H:%M', gmtime())} | Detecting bigrams in the corpus using a memory friendly iterator ...\n")
# # Train a bigram detector.
# bigram_transformer = Phrases(sentences, min_count=0.0005*len(train_docs))
# bigram_freezed = bigram_transformer.freeze()

# print(f"{strftime('%D %H:%M', gmtime())} | Creating transformed sentences ...\n")
# # Apply the trained MWE detector to the corpus
# transformed_sents = bigram_freezed[sentences]

# del bigram_transformer

# train_docs_T = [" ".join(doc) for doc in transformed_sents]

# print(f"{strftime('%D %H:%M', gmtime())} | Saving cleaned documents ...\n")
# with open("ETM\cleaned_docs.pkl", "wb") as f:
#     pickle.dump(train_docs_T, f)

# print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

