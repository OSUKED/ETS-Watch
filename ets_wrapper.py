# Imports
import pandas as pd
import requests

import os
import dotenv

# Loading API key
dotenv.load_dotenv()
api_key = os.getenv('QUANDL_API_KEY')

# Parsers
def get_ets_mkt_data():
    # Constructing endpoint
    api_root = 'https://www.quandl.com/api/v3/datasets'
    quandl_code = 'CHRIS/ICE_C1'
    endpoint_url = f'{api_root}/{quandl_code}.json'

    # Making the data request
    params = {'api_key': api_key}
    r = requests.get(endpoint_url, params=params)

    # Converting to a dataframe
    dataset = r.json()['dataset']
    df = pd.DataFrame(dataset['data'], columns=dataset['column_names'])

    # Cleaning the dataframe
    df.columns = df.columns.str.lower().str.replace('.', '').str.replace(' ', '_')
    df = df.rename(columns={'date': 'datetime'}).set_index('datetime')
    df['close'] = df['open'] + df['change']
    df.index = pd.to_datetime(df.index)
    
    return df