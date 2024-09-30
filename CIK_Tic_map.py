# -*- coding: utf-8 -*-
"""
Created on 18 June 2024

@author: Amin
"""

# Import liberaries and functions
from sec_api import MappingApi
import pandas as pd
import os
import multiprocessing

mappingApi = MappingApi(api_key='355b10a7c3b55716e8d0ec69c6b24c724d99b050369b066d94fe94dce289b65e')

df = pd.read_csv("Data/T2V_train.csv")
CIKs = df['CIK'].unique()

def cik_tic_map(cik):
    return mappingApi.resolve('cik', str(cik))

with multiprocessing.Pool(os.cpu_count()) as pool:
    output = pool.map(cik_tic_map, CIKs)

cik_ticker_df = pd.DataFrame([x for X in output for x in X]).drop_duplicates(subset=['cik', 'ticker'])
cik_ticker_df['cik'] = cik_ticker_df['cik'].astype(int)

cik_ticker_df = cik_ticker_df[cik_ticker_df['cik'].isin(CIKs)].reset_index(drop=True)

cik_ticker_df.to_csv('CIK_Ticker_CUSIP.csv', index=False)