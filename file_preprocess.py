# -*- coding: utf-8 -*-
"""
Created on:  Mar 20, 2022

@author: Amin
"""

# Import liberaries and functions
from bs4 import BeautifulSoup
import re
import spacy
from spacy.attrs import SENT_START
import time
import pandas as pd
from tqdm.auto import tqdm

nlp = spacy.load('en_core_web_sm')

def file_preprocess(file, format='htm', paragraphs=True):
    """
    This function gets the content of a file and its extension as input and returns the list of paragraphs in the "risk Factors" report.

    Parameters
    ----------
    file : file object

    format : str, optional
        The default is 'htm'.

    Returns
    -------
    RF_list : list of strings
    
    """
    
    # Split the text
    # Create a list of string elements in the HTML files
    if format in ['htm', 'html']:
        # parse html data
        html = BeautifulSoup(file, 'html.parser')
        # regex to remove (non-word characters)|(empty strings)|(page numbers)
        regex = re.compile("(\W+)|^(?![\s\S])|(\W*\d+\W*)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
        # get a list of all string items after removing unwanted strings
        str_list = [re.sub('\s+', ' ', item.strip()) 
                    for item in list(html.strings) 
                    if not bool(regex.fullmatch(item.lower()))]
        
    # Create a list of paragraphs (seperated by \n\n) in the TXT files
    else:
        regex = re.compile(b"(\W+)|^(?![\s\S])|(\s*\d+\s*<.*>)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
        str_list = [re.sub('\s+', ' ', item.decode('utf-8').strip()) 
                    for item in re.split(b'\n *\n', file) 
                    if not bool(regex.fullmatch(item.lower()))]
        
    # Merge text segments

    if paragraphs:
        # Merging titles to its related content, text which is continued to the next page, and bullet points
        RF_list = []
        try:
            new_rf = str_list[0]
            # Iterate through the text segments to extract paragraphs and lists
            for rf in str_list[1:]:
                rf_striped = re.sub(pattern='^\W*', repl='', string=rf)
                doc = nlp(new_rf)
                # Identify titles and bullet points
                if doc.count_by(SENT_START)[1] <= 1:
                    # Merge bullet points and lists in text
                    if rf_striped[0].islower():
                        new_rf = new_rf + ' ' + rf
                    else: # Merge title with the following paragraph
                        new_rf = new_rf + '\n' + rf
                # Check if text is continued to the next text segment
                elif rf_striped[0].islower():
                    new_rf = new_rf + ' ' + rf
                else:
                    RF_list.append(new_rf)
                    new_rf = rf
            # add the last item in the list        
            RF_list.append(new_rf)
            
            return RF_list
        
        except IndexError:
            return None

    else:
        # Return the document as a whole
        try:
            RD_doc = ' '.join(str_list)
            return RD_doc
        
        except IndexError:
            return None        


def multi_file_process(file_chunk, rf_split=False):
    """
    Function to preprocess risk reports in a batch.

    Parameters
    ----------
    file_chunk : list
        list of paths to risk report files.

    Returns
    -------
    Item1A_df : pd.DataFrame
        DataFrame with columns 'cik', 'reporting year', 'filing date' and 'Item 1A'.
    """
    
    print(f"\nProcess started | {time.ctime()}")
    
    # Create an empty pandas DataFrame
    Item1A_df = pd.DataFrame()
    
    for file in tqdm(file_chunk):
        # Read file
        with open(file, 'rb') as f:
            f_name = f.name.split('\\')[-1]
            cik = f_name.split('-')[0]
            r_year = f_name.split('-')[2][1:5]
            f_date = f_name.split('-')[1][1:]
            f_ext = f.name.split('.')[-1]
            
            # Convert the textual data into the required format
            item_1a = file_preprocess(f.read(), format=f_ext, paragraphs=rf_split)

        if rf_split:
            if item_1a is not None:
                # Add the file and correspomding data to the list in DataFrame
                Item1A_df = Item1A_df.append(
                    pd.DataFrame(data={'cik': cik, 'reporting year': r_year, 'filing date': f_date, 'Item 1A': item_1a})
                )
            else:
                pass

        else:
            if item_1a is not None:
                # Add the file and correspomding data to the list in DataFrame
                Item1A_df = pd.concat(
                    [Item1A_df,
                    pd.DataFrame(data={'cik': cik, 'reporting year': r_year, 'filing date': f_date, 'Item 1A': [item_1a]})]
                )
            else:
                pass
        
    print(f"\nProcess ended   | {time.ctime()}")
    return Item1A_df