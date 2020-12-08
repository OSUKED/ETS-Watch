## Imports
import pandas as pd
import numpy as np
import json

import matplotlib.pyplot as plt
import mplfinance as mpf
import FEAutils as hlp

from ets_wrapper import get_ets_mkt_data

## Plotting helpers
def plot_long_term_avg(df):
    fig, ax = plt.subplots(dpi=250, figsize=(10, 4))

    df['settle'].plot(ax=ax, color='#AE0019', linewidth=1)

    ax.set_ylim(0)
    ax.set_xlim(df.index.min(), df.index.max())
    ax.set_xlabel('')
    ax.set_ylabel('Price (EUR/tonne CO2)')
    hlp.hide_spines(ax)
    
    return fig, ax

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

# Retrieving, processing and saving data
df = get_ets_mkt_data()

data = df.fillna(-99999).reset_index().T.apply(list, axis=1).to_dict()
data = {k: [None if x==-99999 else x for x in v] for k, v in data.items()}
data['datetime'] = pd.to_datetime(data['datetime']).strftime('%Y-%m-%d %H:%M').to_list()

with open('data/ets_mkt.json', 'w') as fp:
    json.dump(data, fp)

## Visualising data
latest_date = df.index.max()
earliest_date = latest_date - pd.Timedelta(weeks=8)

cols = ['open', 'high', 'low', 'close', 'volume']
df_last_8wks = df[cols].sort_index().dropna().loc[earliest_date:latest_date]

fig, axs = plot_ohlc_vol(df_last_8wks)
fig.savefig('img/ohlc_vol.png')

fig, ax = plot_long_term_avg(df)
fig.savefig('img/long_term_avg.png')

## Updating README
def update_readme_time(readme_fp, 
                       splitter='Last updated: ', 
                       dt_format='%Y-%m-%d %H:%M'):
    
    with open(readme_fp, 'r') as readme:
        txt = readme.read()
    
    start, end = txt.split(splitter)
    old_date = end[:16]
    end = end.split(old_date)[1]
    new_date = pd.Timestamp.now().strftime(dt_format)
    
    new_txt = start + splitter + new_date + end
    
    with open(readme_fp, 'w') as readme:
        readme.write(new_txt)
        
    return

update_readme_time('README.md')