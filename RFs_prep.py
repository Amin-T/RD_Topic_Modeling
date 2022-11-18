# -*- coding: utf-8 -*-
"""
Created on 8 February 2022

@author: Amin
"""

# Import liberaries and functions
from multiprocessing.dummy import freeze_support
import pandas as pd
import numpy as np
from file_preprocess import multi_file_process
from multiprocessing import Pool
import argparse
import sys
from time import strftime, gmtime
from functools import partial

"""
=============================================================================
Clean and transform Risk Report files into a DataFrame of risk factors.

To run:
    with splitting reports to risk factors:
    >>> python RFs_prep.py --njobs 8

    without splitting:
    >>> python LDA\RFs_prep.py --njobs 10 --tokens Item1A_tokens.txt --dictionary Item1A_lda_dict --RF_df Item1A_df.csv --Qlow 0.1

=============================================================================
"""

parser = argparse.ArgumentParser(description='RFs prepration')

### data and file related arguments
parser.add_argument('--files', type=str, default='Data/files.csv', help='folder containing list of risk reports')
parser.add_argument('--RF_df', type=str, default='RF_df.csv', help='directory to save dataframe containing risk factors')
parser.add_argument('--rf_split', type=int, choices=[0,1], default=1, help='preprocess with (1) or without (0) splitting risk factors')

### parameters
parser.add_argument('--njobs', type=int, default=4, help='number of cpu cores to be used for training')

args = parser.parse_args()

sys.stdout = open(f"RFs_prep_log_{strftime('%d%m%y', gmtime())}.txt", "w")
print(args, "\n")

print(f"{strftime('%D %H:%M', gmtime())} | <<< START >>> \n")
rfsplit = bool(args.rf_split)

if rfsplit:
    print("*** Pre-processing by spliting reports to risk factors ***\n")
else:
    print("*** Pre-processing of risk reports witout spliting ***\n")

# Save the clean DataFrame
print(f"{strftime('%D %H:%M', gmtime())} | Start reading HTML/TXT files ...")

# Import list of all raw html/text files
all_files = pd.read_csv(args.files)

n_jobs = args.njobs
batchs = np.array_split(all_files, 2*n_jobs)
    
if __name__ == "__main__":
    with Pool(processes=n_jobs) as p:
        output = p.map(partial(multi_file_process, rf_split=rfsplit), batchs)
    p.join()

    RF_df = pd.concat(output)

    # Remove empty reports
    RF_df.dropna(inplace=True)

    # Remove duplicates
    RF_df = (
        RF_df.sort_values(by=['CIK', 'report_dt', 'filing_dt']).drop_duplicates()
    )

    # Save the clean DataFrame
    print(f"{strftime('%D %H:%M', gmtime())} | Saving processed docs as CSV file ...")
    RF_df.to_csv(args.RF_df)

    sys.stdout.close()

