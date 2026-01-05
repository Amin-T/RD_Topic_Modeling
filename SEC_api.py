# -*- coding: utf-8 -*-
"""
Created on 17 June 2024

@author: Amin
"""

# Import liberaries and functions
from sec_api import QueryApi, ExtractorApi, MappingApi
import html
import gc
import pandas as pd
from tqdm.auto import tqdm
import os
import multiprocessing


"""
=============================================================================
download_all_urls: Downloads and saves all 10-K filing URLs.

extract_item1As: Extracts Item 1A of all filings from the URLs.
=============================================================================
"""

extractorApi = ExtractorApi("API KEY")
queryApi = QueryApi(api_key="API KEY")
mappingApi = MappingApi(api_key='API KEY')

def download_all_urls():
    base_query = {
    "query": { 
        "query_string": { 
            "query": "PLACEHOLDER", # this will be set during runtime 
            "time_zone": "America/New_York"
        } 
    },
    "from": "0", # starting point in the list of urls
    "size": "200", # number of data points returned in every call
    # sort by filedAt
    "sort": [{ "filedAt": { "order": "desc" } }]
    }


    urls_list = []

    for year in tqdm(range(2024, 2005, -1)):
        # a single search universe is represented as a month of the given year
        for month in range(1, 13, 1):
            # get 10-K and 10-K/A filings filed in year and month
            universe_query = \
                "formType:\"10-K\" " + "AND NOT formType:\"NT 10-K\" " + \
                f"AND filedAt:[{year}-{month:02d}-01 TO {year}-{month:02d}-31]"
        
            print(universe_query)
            # set new query universe for year-month combination
            base_query["query"]["query_string"]["query"] = universe_query;

            # paginate through results by increasing "from" parameter until we don't find any matches anymore
            for from_batch in range(0, 100000, 200): 
                base_query["from"] = from_batch;

                response = queryApi.get_filings(base_query)

                # no more filings in search universe
                if len(response["filings"]) == 0:
                    break;

                # for each filing, only save the URL pointing to the filing itself 
                # the URL is set in the dict key "linkToFilingDetails"
                urls_list = urls_list + list(map(
                    lambda x: [x.get(key) for key in ['linkToFilingDetails', 'cik', 'ticker', 
                                                    'filedAt', 'periodOfReport', 'formType']], 
                    response["filings"]
                ))

    urls10K_df = pd.DataFrame(urls_list, columns=['linkToFilingDetails', 'cik', 'ticker', 'filedAt', 'periodOfReport', 'formType'])
    urls10K_df['filedAt'] = urls10K_df['filedAt'].apply(lambda x: x.split('T')[0])

    print("Saving URL list ...")
    urls10K_df.to_csv("Data/10Kurls.csv", index=False)


def extract_item1As():
    urls10K_df = pd.read_csv("10Kurls.csv")

    def item1A(filing):
        """
        This function extracts and stores the Item 1A corresponding to every 10-K URL
        """

        saving_path = "./Item1As/" + "_".join([str(x).replace('/', '') for x in filing[1:]])

        try:
            section_text = extractorApi.get_section(filing_url=filing[0],
                                                    section='1A',
                                                    return_type='html')

            with open(saving_path + ".html", 'w') as f:
                f.write(section_text)

        except:
            try:
                section_text = extractorApi.get_section(filing_url=filing[0],
                                                        section='1A',
                                                        return_type='text')
                # Remove HTML enteties
                section_text = html.unescape(section_text)

                with open(saving_path + ".txt", 'w') as f:
                    f.write(section_text)

            except Exception as e:
                print(filing[0], " : ", e)

        gc.collect() # let the garbage collection release memory frequently.


    number_of_processes = os.cpu_count()

    print("Start downloading all Item1As")

    with multiprocessing.Pool(number_of_processes) as pool:
        pool.map(item1A, urls10K_df.values)



