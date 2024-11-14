# Informativeness of Textual Risk Disclosures

This repository contains Python code and data used for the research paper **"Distribution of Risk Information among Industry Peers and the Informativeness of Textual Risk Disclosures"**. The paper investigates how risk information is shared across industry peers and examines the informativeness of textual risk disclosures. The full paper is available on SSRN: [https://ssrn.com/abstract=4474130](https://ssrn.com/abstract=4474130).

## Usage
The Item 1A sections of the 10-K filings are collected from edgar database using [SEC EDGAR Filings API](https://sec-api.io/)
1. **Extracting risk factors**: Run the script in `RFs_prep.py` to read the collected Item 1A files and extract the individual risk factors and save them in a pandas DataFrame
2. **Data Preprocessing**: Run the scripts `clean_docs.py` to preprocess the raw risk factors: extract named entities and transform risk factors into a list of tokens after removing numbers, stop words and special charactors.
3. **Train Top2Vec model**: Run the script in `Top2Vec_train.py` to train the Top2Vec model on the cleaned risk factors.
