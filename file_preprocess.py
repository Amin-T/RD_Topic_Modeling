# -*- coding: utf-8 -*-
"""
Created on December 2021

@author: Amin
"""

# Import liberaries and functions
from bs4 import BeautifulSoup
import re
import spacy
from spacy.attrs import SENT_START
from time import strftime, gmtime
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
    
    def parse_alter():
        # parse html data
        html = BeautifulSoup(file, 'html.parser')
        # regex to remove (non-word characters)|(empty strings)|(page numbers)
        regex = re.compile("(\W+)|^(?![\s\S])|(\W*\d+\W*)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
        # get a list of all string items after removing unwanted strings
        str_list = list(filter(
            lambda x: not bool(regex.fullmatch(x.lower())),
            (re.sub('\s+', ' ', item.strip()) for item in list(html.strings))
        ))

        if len(str_list) > 2:
            # Merge text segments
            # Merging titles to its related content, text which is continued to the next page, and bullet points
            RF_list = []
            new_rf = "\n"
            # Iterate through the text segments to extract paragraphs and lists
            for rf in str_list:
                rf_striped = re.sub(pattern='^\W*', repl='', string=rf)
                doc = nlp(rf_striped)
                islower = doc[0].is_lower
                # Identify titles
                if doc.count_by(SENT_START)[1] <= 1:
                    if islower:
                        # add bullet points and lists to the risk factor
                        new_rf = "\n".join([new_rf, rf])
                    else: 
                        if nlp(new_rf).count_by(SENT_START)[1] >1:
                            RF_list.append(new_rf) # add the previous risk factor to the list
                            new_rf = rf
                        else:
                            new_rf = "\n".join([new_rf, rf])
                else:
                    new_rf = "\n".join([new_rf, rf])
                
            # add the last item in the list        
            RF_list.append(new_rf)
            return RF_list

        else:
            return None

    if paragraphs:

        # Split file into subsections
        if format in ['htm', 'html']:
            # Read file as raw test
            html_text = file

            # Pattern to capture the subsections in HTML files
            pattern = re.compile(
                b"(<b[\W]+)|(<strong>)|(<i>)|(<u>)|(<(font|p|div)\W+(?:\w+\W+){0,25}font-weight\W*(700|bold))|(<(p|div)\W+(?:\w+\W+){0,50}font-style\W*italic)"
            )
            matches = [m.start() for m in pattern.finditer(html_text.lower())]
            matches.append(len(html_text))

            # regex to remove (non-word characters)|(empty strings)|(page numbers)
            regex = re.compile("(\W+)|^(?![\s\S])|(\W*\d+\W*)|(\W*(item)?\W*(1a)?\W*(risk\s+factor[s]?)?\W*)|(\W*table\s+of\s+content[s]?\W*)")

            # get a list of all subsections after removing unwanted strings
            str_list = list(filter(
                lambda x: not bool(regex.fullmatch(x.lower())),
                (
                    BeautifulSoup(html_text[matches[i]: matches[i+1]], 'html.parser').text.strip() 
                    for i in range(len(matches)-1)
                )
            ))

            if len(str_list) > 1:
                # Merging string that are incorrectely seperated
                RF_list = []
                new_rf = str_list[0]
                # Iterate through the text segments to extract paragraphs and lists
                for rf in str_list[1:]:
                    rf_striped = re.sub(pattern='^\W*', repl='', string=rf)
                    doc = nlp(rf_striped)
                    islower = doc[0].is_lower
                    
                    if islower:
                        new_rf = " ".join([new_rf, rf])
                    else:
                        RF_list.append(new_rf) # add the previous risk factor to the list
                        new_rf = rf
                    
                # add the last item in the list        
                RF_list.append(new_rf)
                
                if len(RF_list) > 1:
                    return RF_list
                else:
                    return parse_alter()

            else:
                return parse_alter()


        # Create a list of paragraphs (seperated by \n\n) in the TXT files
        else:
            regex = re.compile("(\W+)|^(?![\s\S])|(\s*\d+\s*<.*>)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
            str_list = list(filter(
                lambda x: not bool(regex.fullmatch(x.lower())),
                (
                    re.sub('\s+', ' ', item.decode('utf-8').strip()) 
                    for item in re.split(b'\n *\n', file)
                )
            ))
            
            # To filter reports that do not disclose any information 
            # (mainly empty reports or smaller reporting companies)
            if len(str_list) > 1:
                # Merge text segments
                # Merging titles to its related content, text which is continued to the next page, and bullet points
                RF_list = []
                new_rf = "\n"
                # Iterate through the text segments to extract paragraphs and lists
                for rf in str_list:
                    rf_striped = re.sub(pattern='^\W*', repl='', string=rf)
                    doc = nlp(rf_striped)
                    islower = doc[0].is_lower
                    # Identify titles
                    if doc.count_by(SENT_START)[1] <= 1:
                        if islower:
                            # add bullet points and lists to the risk factor
                            new_rf = "\n".join([new_rf, rf])
                        else: 
                            if nlp(new_rf).count_by(SENT_START)[1] >1:
                                RF_list.append(new_rf) # add the previous risk factor to the list
                                new_rf = rf
                            else:
                                new_rf = "\n".join([new_rf, rf])
                    else:
                        new_rf = "\n".join([new_rf, rf])
                    
                # add the last item in the list        
                RF_list.append(new_rf)
                
                return RF_list
            
            else:
                return None

    else:
        # Return the document as a whole
        if format in ['htm', 'html']:
            # Read file as raw test
            return BeautifulSoup(file, 'html.parser').text
        else:
            return file
            


def multi_file_process(file_chunk,  rf_split=True):
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
    
    print(f"\nProcess started | {strftime('%D %H:%M', gmtime())}")
    
    # Create an empty pandas DataFrame
    Item1A_df = pd.DataFrame()
    
    for i, file in tqdm(file_chunk.iterrows()):
        # Read file
        with open(file['path'], 'rb') as f:
            # Convert the textual data into the required format
            item_1a = file_preprocess(f.read(), format=file['extension'], paragraphs=rf_split)

        cik = file['CIK']

        if rf_split:
            if item_1a is not None:
                # Add the file and correspomding data to the list in DataFrame
                Item1A_df = pd.concat(
                    [Item1A_df,
                    pd.DataFrame(data={
                        'CIK': cik, 
                        'report_dt': file['report_dt'], 
                        'filing_dt': file['filing_dt'], 
                        'Item 1A': item_1a
                    })]
                )
            else:
                pass

        else:
            if item_1a is not None:
                # Add the file and correspomding data to the list in DataFrame
                Item1A_df = pd.concat(
                    [Item1A_df,
                    pd.DataFrame(data={
                        'CIK': cik, 
                        'report_dt': file['report_dt'], 
                        'filing_dt': file['filing_dt'], 
                        'Item 1A': [item_1a]
                    })]
                )
            else:
                pass
        
    print(f"\nProcess ended   | {strftime('%D %H:%M', gmtime())}")

    return Item1A_df


