import numpy as np
import time
import spacy
nlp = spacy.load('en_core_web_sm')
from multiprocessing import Pool

def clean(doc):
    # Identify named entities
    ents = [ent.lemma_ for ent in doc.ents]
    # To remove stop words, punctuations, and currency tokens
    mask = lambda t: not (t.is_stop or t.is_punct or t.is_currency or t.is_space or t.ent_iob_ !='O')
    tokens = [tok.lemma_ for tok in filter(mask, doc)]
    tokens.extend(ents)
    return tokens


def tokenizer(data, n_jobs = 5):
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
    print(f"\nProcess started | {time.ctime()}")

    # Covert texts to spaCy doc objects
    docs = nlp.pipe(data.tolist())

    if __name__:
        with Pool(processes=n_jobs) as p:
            output = p.map(clean, docs)

        p.join()
        print(f"\nProcess ended   | {time.ctime()}")
        return output