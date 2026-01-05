This repository contains Python and Stata codes used in my PhD research project **"Essays on the Determinants and Consequences of Corporate Risk Disclosures"**. Using topic modeling and other textual analysis techniques, in this PhD project, I explore the determinants, dissemination, and consequences of corporate risk disclosures among publicly listed firms. Understanding the mechanisms that shape the differences in the content, quality, and informativeness of these disclosures across firms and over time, and their implications for market participants is crucial for advancing both theory and policy in financial reporting and disclosure research. 

The full dissertation is available at this [link](https://kuleuven.limo.libis.be/discovery/search?query=any,contains,LIRIAS4262431&tab=LIRIAS&search_scope=lirias_profile&vid=32KUL_KUL:Lirias&offset=0).

## Usage

1. **Collect Item 1A sections**: Use `SEC_api.py` to download the Item 1A sections of the 10-K filings from edgar database using [SEC EDGAR Filings API](https://sec-api.io/)
2. **Extracting risk factors**: Run the script in `RFs_prep.py` to read the collected Item 1A files and extract the individual risk factors and save them in a pandas DataFrame
3. **Data Preprocessing**: Run the scripts `clean_docs.py` to preprocess the raw risk factors: extract named entities and transform risk factors into a list of tokens after removing numbers, stop words and special charactors.
4. **Train Top2Vec model**: Run the script in `Top2Vec_train.py` to train the Top2Vec model on the cleaned risk factors.
5. **T2V reduction**: Run the script in `T2V_HReduce.py` to find the optimal number of risk topics based on Topic coherence and diversity
4. **Train BERTopic model**: Run the script in `BERTopic_train.py` to train the BERTopic model on the cleaned risk factors.
