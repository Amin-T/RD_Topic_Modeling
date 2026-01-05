# -*- coding: utf-8 -*-
"""
Created on 2 November 2022

@author: Amin
"""

# Import libraries and functions
from data import nlp_clean, bigram, load_data
import argparse
from time import strftime, gmtime
import spacy
import gc

"""
=============================================================================
Clean Risk Factors and implement bigram transformation.

To run:
    >>> python clean_docs.py
=============================================================================
"""
parser = argparse.ArgumentParser(description='RFs prepration')

parser.add_argument('--RF_df', type=str, default='Data/RFs_all2.csv', help='directory of dataframe containing risk factors')
parser.add_argument('--clean_docs', type=str, default="Data/T2V_train.csv", help='directory to save cleaned documents')

parser.add_argument('--Qlow', type=float, default=0.05, help='Lower quantile to filter too short docs (risk factors)')
parser.add_argument('--min_count', type=float, default=0.001, help='min count of bigrams (ratio of number of RFs)')
parser.add_argument('--spacy', type=str, default="en_core_web_sm", help='spaCy model to be loaded')
parser.add_argument('--n_jobs', type=int, default=-1, help='Number of processors to process texts')

args = parser.parse_args()

print(args, "\n")

nlp = spacy.load(args.spacy)

print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Load raw text data
print(f"{strftime('%D %H:%M', gmtime())} | Loading data ...\n")

RF_df = load_data(path=args.RF_df, low_bnd=args.Qlow)

# Replace some unwanted patterns in the RFs
pattern = r"(table\s+of\s+contents?)|(item\s+1a\s+risk\s+factors?)"
RF_df["Item 1A"] = RF_df["Item 1A"].str.replace(pattern, " ", case=False, regex=True)

print(f"{strftime('%D %H:%M', gmtime())} | Names entities in risk factors ...\n")

NERs = [[ent.label_ for ent in doc.ents] for doc in nlp.pipe(RF_df['Item 1A'], n_process=args.n_jobs, batch_size=100)]

gc.collect()

print(f"{strftime('%D %H:%M', gmtime())} | Cleaning risk factor docs ...\n")

clean_corpus = [nlp_clean(doc, lemma=True) for doc in nlp.pipe(RF_df['Item 1A'], n_process=args.n_jobs, batch_size=100)]

gc.collect()

print(f"{strftime('%D %H:%M', gmtime())} | Bigram transformation ...\n")
def token(text):
    return text

transformed_sents = bigram(
    raw_data = clean_corpus, 
    tokenizer=token,
    min_cnt = args.min_count 
)


cleaned_data = RF_df.drop(columns=["Item 1A"]).copy()
cleaned_data['cleaned_txt'] = [" ".join(d) for d in transformed_sents]

NE_joined = [" ".join(d) for d in NERs]
cleaned_data['NERs'] = NE_joined

word_cnt = cleaned_data["cleaned_txt"].apply(lambda x: len(x.split()))
Qlow = word_cnt.quantile(0.01)

print(f"Dropping documents with less than {Qlow} tokens ...\n")
cleaned_data = cleaned_data[word_cnt>Qlow]

# Cut the identified RFs at 98% quantile for Item 1As that also include other parts or sections
cleaned_data.sort_values(['CIK', 'report_dt', 'filing_dt', 'rf_seq'], inplace=True)
rf_cnt = cleaned_data.groupby(['CIK', 'report_dt', 'filing_dt'])['rf_seq'].cumcount()
cleaned_data = cleaned_data[rf_cnt<rf_cnt.quantile(0.99)]

print(f"{strftime('%D %H:%M', gmtime())} | Saving cleaned documents ...\n")
cleaned_data.to_csv(args.clean_docs, index=False)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")


