# -*- coding: utf-8 -*-
"""
Created on Sun May 15 11:03:16 2022

@author: Amin
"""

# Import liberaries
from gensim.models import Word2Vec, Phrases, KeyedVectors
import pandas as pd
from time import strftime, gmtime
import sys
import spacy
nlp = spacy.load('en_core_web_sm')

sys.stdout = open(f"embeddings_log_{strftime('%d%m%y', gmtime())}.txt", "w")

print(f"START: {strftime('%D %H:%M', gmtime())}\n")

print("Loading data ...\n")
RF_df = pd.read_csv("RF_df.csv", index_col=0)

word_cnt = RF_df['Item 1A'].astype('str').map(lambda x: len(x.split()))
Qup = word_cnt.quantile(q=0.9)
Qlow = word_cnt.quantile(q=0.1)

print(f"Documents with less than {Qlow} and more than {Qup}, and annual reports of before 2006 are dropped.")
filtered_rf_df = RF_df[(word_cnt>Qlow) & (word_cnt<Qup) & (RF_df["reporting year"]>2005)]

train_docs = filtered_rf_df['Item 1A'].str.lower().tolist()

del RF_df
del filtered_rf_df

def clean(doc):
    # To remove stop words, punctuations, numbers, etc. and lowercase
    mask = lambda t: (t.is_alpha or t.pos==96) and not t.is_stop 
    tokens = (tok.text for tok in filter(mask, doc))
    return tokens

# Memory friendly iterator
class MyCorpus:
    """An iterator that yields sentences (lists of str)."""
    def __iter__(self):
        corpus = nlp.pipe(train_docs)
        for doc in corpus:
            yield clean(doc=doc)

sentences = MyCorpus()

print(f"{strftime('%D %H:%M', gmtime())} | Detecting bigrams in the corpus using a memory friendly iterator ...\n")
# Train a bigram detector.
bigram_transformer = Phrases(sentences, min_count=0.0005*len(train_docs))

# Apply the trained MWE detector to the corpus
transformed_sents = bigram_transformer[sentences]

print(f"{strftime('%D %H:%M', gmtime())} | Training word2vec embeddings ...\n")

model = Word2Vec(
    transformed_sents, 
    min_count=1, 
    epochs=10, 
    workers=15,
    vector_size=300,
    sg=1,
    negative=10,
    comment=1
    )

print("Saving Word2Vec model and trained embeddings ...\n")
model.save("W2V_model.model")
# Store just the words + their trained embeddings.
word_vectors = model.wv
word_vectors.save("embeddings.wordvectors")

print(f"END: {strftime('%D %H:%M', gmtime())}\n")

sys.stdout.close()


