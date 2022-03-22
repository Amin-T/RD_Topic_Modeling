# -*- coding: utf-8 -*-
"""
Created on:  Mar 20, 2022

@author: Amin
"""

# Import liberaries and functions
import time
import spacy
nlp = spacy.load('en_core_web_sm')
from multiprocessing import Pool
from tqdm.auto import tqdm

def clean(doc):
    # Identify named entities
    ents = [ent.lemma_.lower() for ent in doc.ents]
    # To remove stop words, punctuations, and currency tokens
    mask = lambda t: not (t.is_stop or t.is_punct or t.is_currency or t.is_space)
    tokens = [tok.lemma_.lower() for tok in filter(mask, doc)]

    tokens.extend(ents)
    return tokens

def split_dataframe(df, batch_size = 1000): 
    chunks = list()
    num_chunks = len(df) // batch_size + 1
    for i in range(num_chunks):
        chunks.append(df[i*batch_size:(i+1)*batch_size])
    return chunks

def tokenizer(data, n_jobs = 8, batch_size = 1000):
    """
    Extract tokens from the spaCy doc object.

    Parameters
    ----------
    data : pandas Series object of text segments

    n_jobs : int, number of cpu cores to be used
        The default is 5.

    Returns
    -------
    list of tokens per text segment

    """
    print(f"Process started | {time.ctime()}\n")

    # Prepare for the parallel computing
    batches = split_dataframe(data, batch_size)

    output = []
    for batch in tqdm(batches):
        # Covert texts to spaCy doc objects
        docs = nlp.pipe(batch.tolist())
        with Pool(processes=n_jobs) as p:
            temp = p.map(clean, docs)
        p.join()
        output.extend(temp)
        
    print(f"Process ended   | {time.ctime()}\n")
    return output