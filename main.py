# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 09:22:48 2022

@author: u0147656
"""
# =============================================================================
# Implement the preprocessing on all files:
# Python's multiprocessing is used to run the preprocessing function in parallel on batches of html/txt files.
# =============================================================================

# Import liberaries and functions
from functools import total_ordering
import pandas as pd
import glob
import time
import numpy as np
from tqdm.auto import tqdm
from multiprocessing import Pool

from file_preprocess import file_preprocess

# Get all raw html/text file paths
all_files = glob.glob('Data/Risk Factors 10k/*')


def multi_file_process(file_chunk):
    """
    Function to preprocess risk reports in a batch.

    Parameters
    ----------
    file_chunk : list
        list of paths to risk report files.

    Returns
    -------
    RF_df : pd.DataFrame
        DataFrame with columns.
    """
    
    print(f"\nProcess started | {time.ctime()}")
    
    # Create an empty pandas DataFrame
    RF_df = pd.DataFrame()
    
    for file in tqdm(file_chunk):
        # Read file
        with open(file, 'rb') as f:
            f_name = f.name.split('\\')[-1]
            cik = f_name.split('-')[0]
            r_year = f_name.split('-')[2][1:5]
            f_date = f_name.split('-')[1][1:]
            f_ext = f.name.split('.')[-1]
            
            # Convert the textual data into the required format
            item_1a = file_preprocess(f.read(), format=f_ext)
            
        if item_1a is not None:
            # Add the file and correspomding data to the list in DataFrame
            RF_df = RF_df.append(
                pd.DataFrame(data={'cik': cik, 'reporting year': r_year, 'filing date': f_date, 'Item 1A': item_1a})
            )
        else:
            pass
        
    print(f"\nProcess ended   | {time.ctime()}")
    return RF_df

# Determine no. of processors to work simultaniously
processes = 10
batches = np.array_split(all_files, 2*processes)

if __name__ == "__main__":
    pool = Pool(processes=processes)
    output = pool.map(multi_file_process, batches)
    pool.close()
    pool.join()
    
    RF_df = pd.concat(output)
    
    # Remove empty reports
    RF_df.dropna(inplace=True)
    
    # Remove duplicates
    RF_df = (
        RF_df.sort_values(by=['cik', 'reporting year', 'filing date']).drop_duplicates()
    )
    
    # Save the clean DataFrame
    print("Saving final CSV file ...")
    RF_df.to_csv('RF_df.csv')


