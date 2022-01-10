# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import re
import spacy
from spacy.attrs import SENT_START

nlp = spacy.load('en_core_web_sm')

def file_preprocess(file, format='htm'):
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
    
    if format in ['htm', 'html']:
        # parse html data
        html = BeautifulSoup(file, 'html.parser')
        # regex to remove (non-word characters)|(empty strings)|(page numbers)
        regex = re.compile("(\W+)|^(?![\s\S])|(\W*\d+\W*)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
        # get a list of all string items after removing unwanted strings
        str_list = [re.sub('\s+', ' ', item.strip()) 
                    for item in list(html.strings) 
                    if not bool(regex.fullmatch(item.lower()))]
        
    else:
        regex = re.compile(b"(\W+)|^(?![\s\S])|(\s*\d+\s*<.*>)|(\W*(item)?\W*(1a)?\W*(risk factor[s]?)?\W*)|(\W*table of content[s]?\W*)")
        str_list = [re.sub('\s+', ' ', item.decode('utf-8').strip()) 
                    for item in re.split(b'\n *\n', file) 
                    if not bool(regex.fullmatch(item.lower()))]
        
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
