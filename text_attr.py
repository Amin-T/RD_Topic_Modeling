# -*- coding: utf-8 -*-
"""
Created on April 2024

@author: Amin
"""

# Import liberaries and functions
from data import load_data
import pandas as pd
import numpy as np
from multiprocessing import  Pool
from functools import partial
import os
import gc
from time import strftime, gmtime
import spacy
nlp = spacy.load('en_core_web_sm')

from nltk.sentiment.vader import SentimentIntensityAnalyzer

from readability import Readability

# multiprocessing pandas apply function
def parallelize(data, func, num_of_processes=8):
    data_split = np.array_split(data, num_of_processes)
    pool = Pool(num_of_processes)
    data = pd.concat(pool.map(func, data_split))
    pool.close()
    pool.join()
    return data

def run_on_subset(func, data_subset):
    return data_subset.apply(func)

def parallelize_on_rows(data, func, num_of_processes=8):
    return parallelize(data, partial(run_on_subset, func), num_of_processes)


print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Import data
print(f"{strftime('%D %H:%M', gmtime())} | Loading data ...\n")

All_RFs = load_data("Data/RFs_all2.csv")

All_RFs['rf_length'] = All_RFs['Item 1A'].map(lambda x: len(x.split()))

print(f"{strftime('%D %H:%M', gmtime())} | Named entities in risk factors ...\n")

def NER_func(RF):
    """
    This function determins named entity tags in the RF.
    """
    Doc = nlp(RF)
    NERs = [ent.label_ for ent in Doc.ents]
    NE_joined = [" ".join(d) for d in NERs]
    return NE_joined

NERs = parallelize_on_rows(All_RFs["Item 1A"], NER_func, num_of_processes=os.cpu_count())
All_RFs['NERs'] = NERs

del NERs
gc.collect()

## Time orientation
print(f"{strftime('%D %H:%M', gmtime())} | Computing time orientation \n")
def det_tense(RF):
    """
    This function counts the number of verbs in past, present, and futur tenses.
    """
    Doc = nlp(RF)
    verbs = [tok.tag_ for tok in Doc]
    Pa = len([v for v in verbs if v in ["VBD", "VBN"]]) #Past
    Pr = len([v for v in verbs if v in ["VBP", "VBZ", "VBG"]]) #Present
    Fu = len([v for v in verbs if v in ["MD", "VBC", "VBF"]]) #Future

    return (Pa, Pr, Fu)

Time = parallelize_on_rows(All_RFs["Item 1A"], det_tense, num_of_processes=os.cpu_count()).to_list()
All_RFs[['Pa', 'Pr', 'Fu']] = Time

del Time
gc.collect()

## Sentiment
print(f"{strftime('%D %H:%M', gmtime())} | Computing sentiment \n")
sid = SentimentIntensityAnalyzer()

def sent_func(RF):
    return sid.polarity_scores(RF)['compound']

Sentiment = parallelize_on_rows(All_RFs["Item 1A"], sent_func, num_of_processes=os.cpu_count())
All_RFs['Sentiment'] = Sentiment

del Sentiment
gc.collect()

## Readability
def read_func(doc):
    try:
        return Readability(doc).gunning_fog().score 
    except:
        return None

# Readability per individual RF
print(f"{strftime('%D %H:%M', gmtime())} | Computing readability for individual RFs \n")
FOG = parallelize_on_rows(All_RFs["Item 1A"], read_func, num_of_processes=os.cpu_count())
All_RFs['FOG'] = FOG

# Readability for Item 1A section
print(f"{strftime('%D %H:%M', gmtime())} | Computing readability for Item 1A sections \n")
Item1A_df = All_RFs.groupby(['CIK', 'report_dt', 'filing_dt'])['Item 1A'].apply(lambda x: ' '.join(x)).reset_index()

with Pool(processes=os.cpu_count()) as pool:
    FOG = pool.map(read_func, Item1A_df["Item 1A"].tolist())
pool.join()
Item1A_df['Item1AFOG'] = FOG

Item1A_df.drop(columns=['Item 1A'], inplace=True)
All_RFs.drop(columns=['Item 1A'], inplace=True)

All_RFs.merge(
    right = Item1A_df,
    on = ['CIK', 'report_dt', 'filing_dt'],
    how = "left"
)

print(f"{strftime('%D %H:%M', gmtime())} | Saving output to disk | \n")
All_RFs.to_csv('Data/RF_text_attr2.csv', index=False)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

with Pool(processes=os.cpu_count()) as pool:
    output = pool.map(read_func, Item1A_df_sample["Item 1A"].tolist())
pool.join()