# -*- coding: utf-8 -*-
"""
Created on Thu May 26 2022

@author: Amin
"""

# Import liberaries
import pandas as pd
from time import gmtime, strftime
from gensim.models import Phrases, phrases


def load_data(path, low_bnd=0.1, up_bnd=1.0, col="Itam 1A", index=None):
    """
    Load the Risk Factors .csv file and apply filters on:
        > low_bound: min length of the doc in column "Itam 1A"
        > up_bound: max length of the doc in column "Itam 1A"
    """

    print("Loading data ...\n")

    RF_df = pd.read_csv(filepath_or_buffer=path, index_col=index).dropna()

    word_cnt = RF_df[col].astype('str').map(lambda x: len(x.split()))
    Qup = int(word_cnt.quantile(q=up_bnd))
    Qlow = int(word_cnt.quantile(q=low_bnd)
)
    print(f"Documents with less than {Qlow} and more than {Qup} words are dropped.\n")
    filtered_rf_df = RF_df[(word_cnt>Qlow) & (word_cnt<Qup)]

    return filtered_rf_df

def nlp_clean(doc, lemma=False):
    # To remove stop words, punctuations, numbers, etc.
    mask = lambda t: (t.is_alpha or t.pos==96) and not t.is_stop and t.shape_.lower()!='x'
    if lemma:
        tokens = (tok.lemma_.lower() for tok in filter(mask, doc))
    else:
        tokens = (tok.text.lower() for tok in filter(mask, doc))
    return tokens

def bigram(raw_data, tokenizer, min_cnt=0.001):
    """
    Transform texts to bigrams:
        > raw_data: list of "Itam 1A" column
        > min_cnt: min count of bigrams (ratio of number of RFs)
        > tokenizer: function to tokenize raw_data
    """

    # Memory friendly iterator
    class MyCorpus:
        """An iterator that yields sentences (lists of str)."""
        def __iter__(self):
            for doc in raw_data:
                yield tokenizer(doc)

    sentences = MyCorpus()

    print(f"{strftime('%D %H:%M', gmtime())} | Detecting bigrams in the corpus using a memory-friendly iterator ...\n")
    # Train a bigram detector.
    bigram_transformer = Phrases(sentences, min_count=min_cnt*len(raw_data), connector_words=phrases.ENGLISH_CONNECTOR_WORDS)
    bigram_freezed = bigram_transformer.freeze()

    print(f"{strftime('%D %H:%M', gmtime())} | Creating transformed sentences ...\n")
    # Apply the trained MWE detector to the corpus
    transformed_sents = bigram_freezed[sentences]

    return transformed_sents
    
    