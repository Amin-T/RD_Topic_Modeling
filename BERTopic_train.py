# -*- coding: utf-8 -*-
"""
Created on  31 October 2024

@author: Amin
"""

# Import liberaries and functions
from bertopic import BERTopic
from data import load_data
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from time import strftime, gmtime
import argparse
import gc
import spacy
import os

# =============================================================================
# This module trains the BERTopic model on the corpora 

# To run:
# >>> python BERTopic.py
# =============================================================================

parser = argparse.ArgumentParser(description='BERTopic model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/RFs_all2.csv', help='path to cleaned documents')
parser.add_argument('--save_model', type=str, default='Models/BERT1', help='directory to save tranied model')
parser.add_argument('--ngram', type=int, default=2, help='ngram_range')

args = parser.parse_args()

date = gmtime()

print(args)
print("\n\t BERTopic topic model training log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Read preprocessed text data as Pandas DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Loading text data ... \n")

def get_docs():
    docs_df = load_data(args.documents, low_bnd=0.1)
    docs_df['report_dt'] = pd.to_datetime(docs_df['report_dt'])

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
        (docs_df['report_dt']>"2016-01-01")
        &(docs_df['report_dt']<"2024-01-01")
        &(docs_df['SIC'].notna())
        &(~docs_df['SIC'].isin(fin_sic))
    ] 
    
    return docs_df

train_docs_df = get_docs()

# Drop firms with only one report
train_docs_df = train_docs_df[train_docs_df.groupby('CIK')['report_dt'].transform('nunique')>1]

# Cut the identified RFs at 99% quantile for Item 1As that also include other parts or sections
train_docs_df.sort_values(['CIK', 'report_dt', 'filing_dt', 'rf_seq'], inplace=True)
rf_cnt = train_docs_df.groupby(['CIK', 'report_dt', 'filing_dt'])['rf_seq'].cumcount()
train_docs_df = train_docs_df[rf_cnt<rf_cnt.quantile(0.99)]

nlp = spacy.load("en_core_web_sm")

# Replace some unwanted patterns in the RFs
pattern = r"(table\s+of\s+contents?)|(item\s+1a\W\s+risk\s+factors?)"
train_docs_df["Item 1A"] = train_docs_df["Item 1A"].str.replace(pattern, " ", case=False, regex=True)

print(f"{strftime('%D %H:%M', gmtime())} | Cleaning risk factor docs ...\n")

def nlp_clean(doc):
    mask = lambda t: not t.is_digit and not t.is_punct
    tokens = [tok.lemma_.lower() for tok in filter(mask, doc)]
    return tokens

# train_docs = train_docs_df["Item 1A"].sample(frac=0.80, random_state=101).to_list()
train_docs = [nlp_clean(doc) for doc in nlp.pipe(train_docs_df['Item 1A'], n_process=os.cpu_count(), batch_size=100)]

train_docs_df['cleaned_txt'] = [" ".join(d) for d in train_docs]

print(f"{strftime('%D %H:%M', gmtime())} | Saving cleaned documents ...\n")
train_docs_df.to_csv("Data/BERT_train.csv", index=False)

gc.collect()

vectorizer_model = CountVectorizer(ngram_range=(1, args.ngram), stop_words="english", strip_accents="ascii", max_df=0.95, min_df=100)

del train_docs_df
gc.collect()

print(f"{strftime('%D %H:%M', gmtime())} | Training BERTopic model on {len(train_docs)} RFs.\n")

topic_model = BERTopic(
    embedding_model='all-MiniLM-L6-v2', vectorizer_model=vectorizer_model,
    top_n_words=15, min_topic_size=20, verbose=True, calculate_probabilities=True
)

topics, probs = topic_model.fit_transform(train_docs)

print(f"{strftime('%D %H:%M', gmtime())} | Saving trained Top2Vec model to disk ...\n")

topic_model.save(args.save_model, serialization="safetensors", save_ctfidf=True)

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")

# from bertopic.representation import KeyBERTInspired
# representation_model = KeyBERTInspired()
# topic_model = BERTopic(representation_model=representation_model, embedding_model='all-MiniLM-L6-v2', verbose=True, vectorizer_model=vectorizer_model)

# topic_model.get_document_info(docs)

# topic_model.get_topic(0)

# topic_model.get_topic_info()

# BERTopic.load("my_model")

# topic_model.topics_over_time(docs, timestamps)

# topic_model = BERTopic(
#     embedding_model='all-MiniLM-L6-v2', vectorizer_model=vectorizer_model,
#     top_n_words=15, min_topic_size=20, verbose=True
# )
# topics, probs = topic_model.fit_transform(train_docs)
def get_docs():
    docs_df = load_data("Data/RFs_all2.csv", low_bnd=0.1)
    docs_df['report_dt'] = pd.to_datetime(docs_df['report_dt'])
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
        (docs_df['report_dt']>"2014-01-01")
        &(docs_df['report_dt']<"2024-01-01")
        &(docs_df['SIC'].notna())
        &(~docs_df['SIC'].isin(fin_sic))
    ] 
    # Drop firms with only one report
    docs_df = docs_df[docs_df.groupby('CIK')['report_dt'].transform('nunique')>1]
    return docs_df


train_docs_df = pd.read_csv("Data/BERT_train.csv")

train_docs = train_docs_df['cleaned_txt']

model = BERTopic.load("Models/BERT2")

train_docs_df["Topic"] = model.topics_

train_docs_df["ryear"] = pd.to_datetime(train_docs_df["report_dt"]).dt.year
topic_info[topic_info["Representation"].apply(lambda x: "covid" in x)]
topic_info = model.get_topic_info()

new_topics = model.reduce_outliers(train_docs.tolist(), model.topics_, strategy="embeddings")

"""
reduce_outliers(documents: List[str], topics: List[int], strategy: str = 'distributions' or "c-tf-idf" or "embeddings", probabilities: numpy
.ndarray = None, threshold: float = 0, embeddings: numpy.ndarray = None, distributions_params: Mapping[str, Any] = {}) 
"""

hierarchical_topics = model.hierarchical_topics(train_docs.tolist(), use_ctfidf=True)

hierarchical_topics["Topics"] = hierarchical_topics["Topics"].apply(lambda x: re.findall(pattern="\d+", string=x))

"""
hierarchical_topics(docs: List[str], use_ctfidf: bool = True, linkage_function: Callable[[scipy.sparse._csr.csr_matrix], numpy.ndarray]
= None, distance_function: Callable[[scipy.sparse._csr.csr_matrix], scipy.sparse._csr.csr_matrix] = None)
"""

model.reduce_topics(train_docs, use_ctfidf=True)
"""
reduce_topics(docs: List[str], nr_topics: Union[int, str] = 20, images: List[str] = None, use_ctfidf: bool = False) 
"""
from bertopic import BERTopic
import pandas as pd
train_docs_df = pd.read_csv("Data/BERTopic_df.csv")
model = BERTopic.load("Models/BERT2")
train_docs_df["ryear"] = pd.to_datetime(train_docs_df["report_dt"]).dt.year
train_docs = train_docs_df['cleaned_txt']
DTM = model.topics_over_time(train_docs, timestamps=train_docs_df["ryear"].tolist(), topics=train_docs_df["Topic"].tolist())        8it
"""
topics_over_time(docs: List[str], timestamps: Union[List[str], List[int]], topics: List[int] = None, nr_bins: int = None, 
    datetime_format: str = None, evolution_tuning: bool = True, global_tuning: bool = True) -> pandas.core.frame.DataFrame method of bertopic._bertopic.BERTopic instance
"""




# -*- coding: utf-8 -*-
"""
Created on  31 October 2024

@author: Amin
"""

# Import liberaries and functions
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from time import strftime, gmtime
import argparse
import gc
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"


# =============================================================================
# This module trains the BERTopic model on the corpora 

# To run:
# >>> python BERTopic.py
# =============================================================================

parser = argparse.ArgumentParser(description='BERTopic model trainer')

### data and file related arguments
parser.add_argument('--documents', type=str, default='Data/BERT_train.csv', help='path to cleaned documents')
parser.add_argument('--save_model', type=str, default='Models/BERT3', help='directory to save tranied model')
parser.add_argument('--ngram', type=int, default=2, help='ngram_range')

args = parser.parse_args()

date = gmtime()

print(args)
print("\n\t BERTopic topic model training log\n\n")
print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")

# Read preprocessed text data as Pandas DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Loading text data ... \n")

train_docs_df = pd.read_csv("Data/BERT_train.csv")

train_docs = train_docs_df['cleaned_txt']

vectorizer_model = CountVectorizer(ngram_range=(1, args.ngram), stop_words="english", strip_accents="ascii", max_df=0.95, min_df=1000)

# Embedding (GPU)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
embed_model.max_seq_length = 512
# embeddings = embed_model.encode(train_docs, batch_size=256)

# UMAP (CPU)
umap_model = UMAP(n_components=5, n_neighbors=20, metric='cosine', n_jobs=-1)

# HDBSCAN (CPU)
hdbscan_model = HDBSCAN(min_cluster_size=20, min_samples=5, cluster_selection_epsilon=0.1,  core_dist_n_jobs=-1)

# Train BERTopic
print(f"{strftime('%D %H:%M', gmtime())} | Training BERTopic model on {len(train_docs)} RFs.\n")

topic_model = BERTopic(
    vectorizer_model=vectorizer_model, embedding_model=embed_model,
    top_n_words=15, verbose=True,
    umap_model=umap_model, hdbscan_model=hdbscan_model
)

topics, probs = topic_model.fit_transform(train_docs)

print(f"{strftime('%D %H:%M', gmtime())} | Saving trained BERTopic model to disk ...\n")

topic_model.save(args.save_model, serialization="pickle")

print(f"{strftime('%D %H:%M', gmtime())} | >>> END <<< \n")
