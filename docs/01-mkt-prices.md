# Title



```python
#exports
import json
import pandas as pd

import matplotlib.pyplot as plt
import mplfinance as mpf
import FEAutils as hlp

import os
import requests
```

```python
import dotenv
from IPython.display import JSON
```

```python
dotenv.load_dotenv()
api_key = os.getenv('QUANDL_API_KEY')
```

```python
#exports
def get_ets_mkt_data(
    api_key, 
    api_root='https://www.quandl.com/api/v3/datasets', 
    quandl_code='CHRIS/ICE_C1'
):
    # Constructing endpoint
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
    df = df.sort_index()
    
    return df
```

```python
%%time

df_ets = get_ets_mkt_data(api_key)

df_ets.head()
```

    Wall time: 1.36 s
    

    C:\Users\Ayrto\anaconda3\envs\ETSWatch\lib\site-packages\ipykernel_launcher.py:19: FutureWarning: The default value of regex will change from True to False in a future version. In addition, single character regular expressions will*not* be treated as literal strings when regex=True.
    




| ('Unnamed: 0_level_0', 'datetime')   |   ('open', 'Unnamed: 1_level_1') |   ('high', 'Unnamed: 2_level_1') |   ('low', 'Unnamed: 3_level_1') |   ('settle', 'Unnamed: 4_level_1') |   ('change', 'Unnamed: 5_level_1') |   ('wave', 'Unnamed: 6_level_1') |   ('volume', 'Unnamed: 7_level_1') |   ('prev_day_open_interest', 'Unnamed: 8_level_1') |   ('efp_volume', 'Unnamed: 9_level_1') |   ('efs_volume', 'Unnamed: 10_level_1') |   ('block_volume', 'Unnamed: 11_level_1') |   ('close', 'Unnamed: 12_level_1') |
|:-------------------------------------|---------------------------------:|---------------------------------:|--------------------------------:|-----------------------------------:|-----------------------------------:|---------------------------------:|-----------------------------------:|---------------------------------------------------:|---------------------------------------:|----------------------------------------:|------------------------------------------:|-----------------------------------:|
| 2008-04-08                           |                            24.87 |                            24.87 |                           24.87 |                              24.87 |                              24.87 |                              nan |                                nan |                                                  0 |                                    nan |                                     nan |                                       nan |                              49.74 |
| 2008-04-09                           |                            25.05 |                            25.05 |                           25.05 |                              25.05 |                               0.18 |                              nan |                                nan |                                                  0 |                                    nan |                                     nan |                                       nan |                              25.23 |
| 2008-04-10                           |                            25.79 |                            25.79 |                           25.79 |                              25.79 |                               0.74 |                              nan |                                nan |                                                  0 |                                    nan |                                     nan |                                       nan |                              26.53 |
| 2008-04-11                           |                            25.7  |                            25.7  |                           25.7  |                              25.7  |                              -0.09 |                              nan |                                nan |                                                  0 |                                    nan |                                     nan |                                       nan |                              25.61 |
| 2008-04-14                           |                            26.34 |                            26.34 |                           26.34 |                              26.34 |                               0.64 |                              nan |                                nan |                                                  0 |                                    nan |                                     nan |                                       nan |                              26.98 |</div>



```python
#exports
def plot_long_term_avg(df):
    fig, ax = plt.subplots(dpi=250, figsize=(10, 4))

    df['settle'].plot(ax=ax, color='#AE0019', linewidth=1)

    ax.set_ylim(0)
    ax.set_xlim(df.index.min(), df.index.max())
    ax.set_xlabel('')
    ax.set_ylabel('Price (EUR/tonne CO2)')
    hlp.hide_spines(ax)
    
    return fig, ax
```

```python
fig, ax = plot_long_term_avg(df_ets)
```


![png](img/nbs/output_6_0.png)


```python
#exports
def plot_ohlc_vol(df):
    fig, axs = plt.subplots(dpi=250, nrows=2, figsize=(8, 8))

    mpf.plot(df, type='candle', ax=axs[0], volume=axs[1], show_nontrading=True, style='sas')

    ax = axs[0]
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.set_ylabel('Price (EUR/tonne CO2)')
    ax.yaxis.set_label_position('left')
    ax.yaxis.tick_left()
    hlp.hide_spines(ax, positions=['top', 'bottom', 'right'])

    ax = axs[1]
    ax.set_ylabel('Volume (tonne CO2)')
    hlp.hide_spines(ax, positions=['top', 'right'])
    
    return fig, axs

def plot_recent_ohlc_vol(df, weeks=8, latest_date=None):
    if latest_date is None:
        latest_date = df.index.max()
        
    earliest_date = latest_date - pd.Timedelta(weeks=weeks)

    cols = ['open', 'high', 'low', 'close', 'volume']
    df_recent = df[cols].sort_index().dropna().loc[earliest_date:latest_date]
    
    fig, axs = plot_ohlc_vol(df_recent)
    
    return fig, axs
```

```python
fig, axs = plot_recent_ohlc_vol(df_ets)
```


![png](img/nbs/output_8_0.png)


```python
fig, ax = plt.subplots(dpi=150)

df_ets['volume'].resample('14D').mean().dropna()['2012':].plot(ax=ax)

hlp.hide_spines(ax)
ax.set_xlabel('')
ax.set_ylabel('Average Daily Volume (tonne CO2)')
```




    Text(0, 0.5, 'Average Daily Volume (tonne CO2)')




![png](img/nbs/output_9_1.png)


```python
fig, ax = plt.subplots(dpi=150)

df_ets['volume'].groupby(df_ets.index.dayofyear).mean().plot()

hlp.hide_spines(ax)
ax.set_xlim(0, 365)
ax.set_ylim(0)
ax.set_xlabel('Day of the Year')
ax.set_ylabel('Average Daily Volume (tonne CO2)')
```




    Text(0, 0.5, 'Average Daily Volume (tonne CO2)')




![png](img/nbs/output_10_1.png)

