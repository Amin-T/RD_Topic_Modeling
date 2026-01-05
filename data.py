# -*- coding: utf-8 -*-
"""
Created on Thu May 26 2022

@author: Amin
"""

# Import liberaries
import pandas as pd
from time import gmtime, strftime
from gensim.models import Phrases, phrases
import re


def load_data(path, low_bnd=0.05, col="Item 1A", index=None):
    """
    Load the Risk Factors .csv file and apply filters on:
        > low_bound: quantile for min length of the risk factor in column "Item 1A"
    """

    print("Loading data ...\n")

    RF_df = pd.read_csv(
        filepath_or_buffer=path, index_col=index, 
        # usecols=['index', 'CIK', 'report_dt', 'filing_dt', 'Item 1A']
    ).dropna(subset=[col])

    rf_cnt = RF_df.groupby(['CIK', 'report_dt', 'filing_dt'])['index'].transform('count')
    rflow = rf_cnt.quantile(0.005)
    rfup = rf_cnt.quantile(0.995)

    print(f"Dropping Item1As with less than {rflow} and more than {rfup} identified RFs ...\n")
    filtered_rf_df = RF_df[(rf_cnt>=rflow)&(rf_cnt<=rfup)]

    word_cnt = filtered_rf_df[col].apply(lambda x: len(re.split(pattern=r'\s', string=x)))
    Qlow = word_cnt.quantile(q=low_bnd)

    print(f"Dropping documents with less than {Qlow} words ...\n")
    filtered_rf_df = filtered_rf_df[word_cnt>Qlow]

    filtered_rf_df['rf_seq'] = filtered_rf_df.groupby(['CIK', 'report_dt', 'filing_dt'])['index'].cumcount()

    filtered_rf_df.drop(columns=['index'], inplace=True)

    return filtered_rf_df


def nlp_clean(doc, lemma=False):
    # To remove stop words, punctuations, numbers, etc.
    mask = lambda t: (t.is_alpha or t.pos==96) and not t.is_stop and not re.fullmatch(pattern=r"[x\W]", string=t.shape_.lower())
    if lemma:
        tokens = [tok.lemma_.lower() for tok in filter(mask, doc)]
    else:
        tokens = [tok.text.lower() for tok in filter(mask, doc)]
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

    print(f"{strftime('%D %H:%M', gmtime())} | Detecting bigrams in the corpus using a memory-friendly iterator ...\n")
    # Train a bigram detector.
    bigram_transformer = Phrases(MyCorpus(), min_count=min_cnt*len(raw_data), connector_words=phrases.ENGLISH_CONNECTOR_WORDS)
    bigram_freezed = bigram_transformer.freeze()

    print(f"{strftime('%D %H:%M', gmtime())} | Creating transformed sentences ...\n")
    # Apply the trained MWE detector to the corpus
    transformed_sents = [d for d in bigram_freezed[MyCorpus()]]

    return transformed_sents
    
    