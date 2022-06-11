from functools import partial
from multiprocessing import Pool, freeze_support
import numpy as np
from time import gmtime, strftime

def get_document_frequency(data, wi, wj=None):
    if wj is None:
        D_wi = 0
        for document in data:
            # FIXME: 'if' for original article's code, 'else' for updated
            doc = document.squeeze(0) if document.shape[0] == 1 else document

            if wi in doc:
                D_wi += 1
        return D_wi

    D_wj = 0
    D_wi_wj = 0
    for document in data:
        # FIXME: 'if' for original article's code, 'else' for updated version
        doc = document.squeeze(0) if document.shape[0] == 1 else document

        if wj in doc:
            D_wj += 1
            if wi in doc:
                D_wi_wj += 1
    return D_wj, D_wi_wj

def coherence(beta, data, top_n, D, k):
    beta_top_n = list(beta[k].argsort()[-top_n:][::-1])
    TC_k = 0
    counter = 0
    for i, word in enumerate(beta_top_n):
        # get D(w_i)
        D_wi = get_document_frequency(data, word)
        j = i + 1
        tmp = 0
        while j < len(beta_top_n) and j > i:
            # get D(w_j) and D(w_i, w_j)
            D_wj, D_wi_wj = get_document_frequency(
                data, word, beta_top_n[j])
            # get f(w_i, w_j)
            if D_wi_wj == 0:
                f_wi_wj = -1
            else:
                f_wi_wj = -1 + (np.log(D_wi) + np.log(D_wj) -
                                2.0 * np.log(D)) / (np.log(D_wi_wj) - np.log(D))
            # update tmp:
            tmp += f_wi_wj
            j += 1
            counter += 1
        # update TC_k
        TC_k += tmp
    return (TC_k, counter)


def get_topic_coherence(beta, data, top_n=10, n_jobs=4):
    D = len(data)  # number of docs...data is list of documents
    num_topics = len(beta)
    with Pool(processes=n_jobs) as p:
        TCs = p.map(partial(coherence, beta, data, top_n, D), range(num_topics))
    p.join()
    TC = np.mean([x[0] for x in TCs]) / TCs[-1][1]
    return TC

