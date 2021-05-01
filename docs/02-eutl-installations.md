# Installation Allocations



```python
#exports
import pandas as pd
import numpy as np

import requests
from bs4 import BeautifulSoup as bs
import urllib.parse as urlparse
from urllib.parse import parse_qs

import re
from warnings import warn

from ipypb import track
```

```python
from IPython.display import JSON
```

<br>

### Retrieving Installation Table Links

In this first section we'll set out to retrieve the urls for the installations databases across different ETS phases and each country.

We'll start by retrieving the raw results for a single country

```python
#exports
def get_country_raw_search(country_code='AT'):
    url = 'https://ec.europa.eu/clima/ets/nap.do'

    params = {
        'languageCode': 'en',
        'nap.registryCodeArray': country_code,
        'periodCode': '-1',
        'search': 'Search',
        'currentSortSettings': ''
    }

    r = requests.get(url, params=params)

    return r
```

```python
r = get_country_raw_search('IS')

r
```




    <Response [200]>



<br>

From the response we can extract a table containing the relevant information on the installation databases

```python
#exports
def extract_search_df(r):
    soup = bs(r.text)
    results_table = soup.find('table', attrs={'id': 'tblNapSearchResult'})

    df_search = (pd
                 .read_html(str(results_table))
                 [0]
                 .iloc[2:, :-3]
                 .reset_index(drop=True)
                 .T
                 .set_index(0)
                 .T
                 .reset_index(drop=True)
                 .rename(columns={
                     'National Administrator': 'country',
                     'EU ETS Phase': 'phase',
                     'For issuance to not new entrants': 'non_new_entrants',
                     'From NER': 'new_entrants_reserve'
                 })
                )

    df_search['installations_link'] = ['https://ec.europa.eu/'+a['href'] for a in soup.findAll('a', text=re.compile('Installations linked to this Allocation Table'))]

    return df_search
```

```python
df_search_country = extract_search_df(r)

df_search_country
```




|    | country   | phase               |   non_new_entrants |   new_entrants_reserve | installations_link                                |
|---:|:----------|:--------------------|-------------------:|-----------------------:|:--------------------------------------------------|
|  0 | Iceland   | Phase 3 (2013-2020) |           11527090 |                 172828 | https://ec.europa.eu//clima/ets/napInstallatio... |</div>



<br>

It's all good doing this for Austria but we want European-wide coverage. We can identify the countries we can query from the option box on the main search page.

```python
#exports
def get_country_codes():
    r = get_country_raw_search()

    soup = bs(r.text)

    registry_code_to_country = {
        option['value']: option.text
        for option 
        in soup.find('select', attrs={'name': 'nap.registryCodeArray'}).findAll('option')
    }
    
    return registry_code_to_country
```

```python
registry_code_to_country = get_country_codes()

JSON([registry_code_to_country])
```




    <IPython.core.display.JSON object>



<br>

We can now use these to repeat our search for each country and concatenate the results

```python
#exports
def get_installation_links_dataframe():
    df_search = pd.DataFrame()

    for registry_code in registry_code_to_country.keys():
        r = get_country_raw_search(registry_code)
        df_search_country = extract_search_df(r)
        df_search = df_search.append(df_search_country)

    df_search = df_search.reset_index(drop=True)
    null_values_present = df_search.isnull().sum().sum() > 0

    if null_values_present == True:
        warn('There are null values present in the dataframe')
        
    return df_search
```

```python
df_search = get_installation_links_dataframe()
    
df_search.head()
```




|    | country   | phase               |   non_new_entrants |   new_entrants_reserve | installations_link                                |
|---:|:----------|:--------------------|-------------------:|-----------------------:|:--------------------------------------------------|
|  0 | Austria   | Phase 1 (2005-2007) |           97791309 |                 990150 | https://ec.europa.eu//clima/ets/napInstallatio... |
|  1 | Austria   | Phase 2 (2008-2012) |          160218569 |                2000000 | https://ec.europa.eu//clima/ets/napInstallatio... |
|  2 | Austria   | Phase 3 (2013-2020) |          160295499 |                1893669 | https://ec.europa.eu//clima/ets/napInstallatio... |
|  3 | Belgium   | Phase 1 (2005-2007) |          178690906 |                7653297 | https://ec.europa.eu//clima/ets/napInstallatio... |
|  4 | Belgium   | Phase 2 (2008-2012) |          283317829 |                9153852 | https://ec.europa.eu//clima/ets/napInstallatio... |</div>



<br>

### Retrieving Installation Allocation Data

In this section we'll start by separating the root url and the parameters from each of the installation links

```python
#exports
def get_url_root_and_params(installations_link):
    url_root = installations_link.split('?')[0]
    parsed = urlparse.urlparse(installations_link)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    
    return url_root, params
```

```python
installations_link = df_search.loc[0, 'installations_link']

url_root, params = get_url_root_and_params(installations_link)

JSON(params)
```




    <IPython.core.display.JSON object>



<br>

We also need to pass the page number to the parameters, to do this we need to first know how many pages there are

```python
#exports
def get_num_pages(root_url, params): 
    soup = bs(requests.get(root_url, params=params).text)
    soup_pn = soup.find('input', attrs={'name': 'resultList.lastPageNumber'})
    
    if soup_pn is not None:
        num_pages = int(soup_pn['value'])
    else:
        num_pages = 1
        
    return num_pages
```

```python
num_pages = get_num_pages(root_url, params)

num_pages
```




    11



<br>

We're now ready to iterate over multiple pages and combine the results for a single ETS phase in a single country

```python
#exports
def extract_installation_allocations_df(r):
        soup = bs(r.text)
        table = soup.find('table', attrs={'id': 'tblNapList'})

        df_installation_allocations = (pd
                                       .read_html(str(table))
                                       [0]
                                       .drop([0, 1])
                                       .reset_index(drop=True)
                                       .T
                                       .set_index(0)
                                       .T
                                       .drop(columns=['Options'])
                                      )
        
        return df_installation_allocations
    
def retry_request(root_url, params, n_retries=5, **kwargs):
    for i in range(n_retries):
        try:
            r = requests.get(root_url, params=params, **kwargs)
            return r
        except Exception as e:
            continue

    raise e

def get_installation_allocations_df(root_url, params, n_retries=5):
    df_installation_allocations = pd.DataFrame()

    num_pages = get_num_pages(root_url, params)
    params['nextList'] = 'Next'

    for page_num in range(num_pages):
        params['resultList.currentPageNumber'] = page_num            
        r = retry_request(root_url, params, n_retries=n_retries)
        
        df_installation_allocations_page = extract_installation_allocations_df(r)
        df_installation_allocations = df_installation_allocations.append(df_installation_allocations_page)

    df_installation_allocations = df_installation_allocations.reset_index(drop=True)
    
    return df_installation_allocations
```

```python
df_installation_allocations = get_installation_allocations_df(root_url, params)

print(f'DataFrame shape: {df_installation_allocations.shape}')

df_installation_allocations.head(3)
```

    DataFrame shape: (201, 11)
    




|    |   Installation ID | Installation Name                     | Address City   | Account Holder Name               | Account Status   | Permit ID   | Latest Update       |   2005 |   2006 |   2007 | Status   |
|---:|------------------:|:--------------------------------------|:---------------|:----------------------------------|:-----------------|:------------|:--------------------|-------:|-------:|-------:|:---------|
|  0 |                 1 | Baumit Baustoffe Bad Ischl            | Bad Ischl      | Calmit GmbH                       | open             | IKA119      | 2009-05-08 09:13:58 |  44894 |  44894 |  44894 | Active   |
|  1 |                 2 | Breitenfelder Edelstahl Mitterdorf    | Mitterdorf     | Breitenfeld Edelstahl AG          | open             | IES069      | 2009-05-08 09:13:58 |   8492 |   8492 |   8492 | Active   |
|  2 |                 3 | Ziegelwerk Danreiter Ried im Innkreis | Ried           | Ziegelwerk Danreiter GmbH & Co KG | open             | IZI155      | 2009-05-08 09:13:58 |   7397 |   7397 |   7397 | Active   |</div>



<br>

The next step is to repeat this for all countries and ETS phases, then combine the resulting dataframes

```python
#exports
def get_all_installation_allocations_df(df_search):
    col_renaming_map = {
        'Installation ID': 'installation_id', 
        'Installation Name': 'installation_name', 
        'Address City': 'installation_city', 
        'Account Holder Name': 'account_holder', 
        'Account Status': 'account_status', 
        'Permit ID': 'permit_id', 
        'Status': 'status'
    }

    df_installation_allocations = pd.DataFrame()

    # Retrieving raw data
    for country in track(df_search['country'].unique()):
        df_installation_allocations_country = pd.DataFrame()
        country_installations_links = df_search.loc[df_search['country']==country, 'installations_link']

        for installations_link in track(country_installations_links, label=country):
            url_root, params = get_url_root_and_params(installations_link)
            df_installation_allocations_country_phase = get_installation_allocations_df(root_url, params)

            if df_installation_allocations_country.size > 0:
                df_installation_allocations_country = pd.merge(df_installation_allocations_country, df_installation_allocations_country_phase, how='outer', on=list(col_renaming_map.keys()))
            else:
                df_installation_allocations_country = df_installation_allocations_country_phase

        df_installation_allocations_country['country'] = country
        df_installation_allocations = df_installation_allocations.append(df_installation_allocations_country)

    # Collating update datetimes
    update_cols = df_installation_allocations.columns[df_installation_allocations.columns.str.contains('Latest Update')]
    df_installation_allocations['latest_update'] = df_installation_allocations[update_cols].fillna('').max(axis=1)
    df_installation_allocations = df_installation_allocations.drop(columns=update_cols)

    # Renaming columns
    df_installation_allocations = (df_installation_allocations
                                   .reset_index(drop=True)
                                   .rename(columns=col_renaming_map)
                                  )

    # Sorting column order
    non_year_cols = ['country'] + list(col_renaming_map.values()) + ['latest_update']
    year_cols = sorted(list(set(df_installation_allocations.columns) - set(non_year_cols)))
    df_installation_allocations = df_installation_allocations[non_year_cols+year_cols]

    # Dropping header rows
    idxs_to_drop = df_installation_allocations['permit_id'].str.contains('\*').replace(False, np.nan).dropna().index
    df_installation_allocations = df_installation_allocations.drop(idxs_to_drop)
    
    return df_installation_allocations
```

```python
df_installation_allocations = get_all_installation_allocations_df(df_search)
        
df_installation_allocations.head()
```


<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="32" value="32" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">32/32</span>
<span class="Time-label">[24:25<01:34, 45.78s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Austria</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:16<00:05, 5.35s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Belgium</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:24<00:10, 7.95s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Bulgaria</span>
<progress style="width:45ex" max="2" value="2" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">2/2</span>
<span class="Time-label">[00:07<00:03, 3.37s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Croatia</span>
<progress style="width:45ex" max="1" value="1" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">1/1</span>
<span class="Time-label">[00:01<00:01, 1.26s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Cyprus</span>
<progress style="width:45ex" max="2" value="2" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">2/2</span>
<span class="Time-label">[00:01<00:01, 0.64s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Czech Republic</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:33<00:12, 11.09s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Denmark</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:30<00:11, 10.07s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Estonia</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:04<00:01, 1.21s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Finland</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[01:04<00:19, 21.32s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">France</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[02:50<01:18, 56.52s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Germany</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[06:22<03:02, 127.24s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Greece</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:09<00:03, 3.03s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Hungary</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:18<00:07, 5.88s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Iceland</span>
<progress style="width:45ex" max="1" value="1" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">1/1</span>
<span class="Time-label">[00:01<00:01, 0.63s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Ireland</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:08<00:02, 2.58s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Italy</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[02:45<01:22, 54.94s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Latvia</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:06<00:02, 1.88s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Liechtenstein</span>
<progress style="width:45ex" max="2" value="2" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">2/2</span>
<span class="Time-label">[00:01<00:00, 0.49s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Lithuania</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:07<00:03, 2.46s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Luxembourg</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:02<00:01, 0.54s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Malta</span>
<progress style="width:45ex" max="1" value="1" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">1/1</span>
<span class="Time-label">[00:00<00:00, 0.47s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Netherlands</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:33<00:15, 10.85s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Northern Ireland</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:01<00:00, 0.46s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Norway</span>
<progress style="width:45ex" max="2" value="2" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">2/2</span>
<span class="Time-label">[00:06<00:03, 3.00s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Poland</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[01:48<00:41, 36.07s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Portugal</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:16<00:05, 5.37s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Romania</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:16<00:05, 5.45s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Slovakia</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:11<00:04, 3.60s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Slovenia</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[00:05<00:01, 1.74s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Spain</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[02:11<00:48, 43.72s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">Sweden</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[01:35<00:30, 31.67s/it]</span></div>



<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:15ex; max-width:15ex; vertical-align:middle; text-align:right">United Kingdom</span>
<progress style="width:45ex" max="3" value="3" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">3/3</span>
<span class="Time-label">[01:34<00:31, 31.37s/it]</span></div>





|    | country   |   installation_id | installation_name                         | installation_city   | account_holder                    | account_status   | permit_id   | status         | latest_update       |   2005 | ...   |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |
|---:|:----------|------------------:|:------------------------------------------|:--------------------|:----------------------------------|:-----------------|:------------|:---------------|:--------------------|-------:|:------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
|  0 | Austria   |                 1 | Baumit Baustoffe Bad Ischl                | Bad Ischl           | Calmit GmbH                       | open             | IKA119      | Active         | 2013-12-19 15:47:52 |  44894 | ...   |  43171 |  43171 |  42159 |  41426 |  40685 |  39937 |  39180 |  38416 |  37643 |  36866 |
|  1 | Austria   |                 2 | Breitenfelder Edelstahl Mitterdorf        | Mitterdorf          | Breitenfeld Edelstahl AG          | open             | IES069      | Active         | 2013-12-19 15:48:16 |   8492 | ...   |  26429 |  26429 |  15118 |  14856 |  14590 |  14322 |  14051 |  13776 |  13499 |  13221 |
|  2 | Austria   |                 3 | Ziegelwerk Danreiter Ried im Innkreis     | Ried                | Ziegelwerk Danreiter GmbH & Co KG | open             | IZI155      | Active         | 2013-12-19 15:48:12 |   7397 | ...   |   5927 |   5927 |   3494 |   3434 |   3373 |   3311 |   3248 |   3185 |   3120 |   3056 |
|  3 | Austria   |                 4 | Wienerberger Blindenmarkt                 | Blindenmarkt        | Wienerberger Österreich GmbH     | closed           | IZI146-1    | Account Closed | 2009-05-08 09:13:58 |   8335 | ...   |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |
|  4 | Austria   |                 5 | Isomax Dekorative Laminate Wiener Neudorf | Wiener Neudorf      | FunderMax GmbH                    | open             | ICH113      | Active         | 2013-12-19 15:47:46 |  24003 | ...   |  27343 |  27343 |  26223 |  25697 |  25167 |  24636 |  24102 |  23566 |  23026 |  22488 |</div>



<br>

A quick check reveals some issues with the dataset, for example there are several permit ids that have duplicate entries

```python
permit_ids_with_duplicate_idxs = (df_installation_allocations['permit_id'].value_counts()>1).replace(False, np.nan).dropna().index
df_dupe_permit_ids = df_installation_allocations[df_installation_allocations['permit_id'].isin(permit_ids_with_duplicate_idxs)].sort_values('permit_id')

print(f"There are {df_dupe_permit_ids['permit_id'].unique().size} permit ids which have duplicate entries due to inconsistent values (e.g. for `installation_id`)\n")

df_dupe_permit_ids.head(6)
```

    There are 109 permit ids which have duplicate entries due to inconsistent values (e.g. for `installation_id`)
    
    




|      | country   |   installation_id | installation_name                  | installation_city   | account_holder                     | account_status   |   permit_id | status         | latest_update       |   2005 | ...   |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |
|-----:|:----------|------------------:|:-----------------------------------|:--------------------|:-----------------------------------|:-----------------|------------:|:---------------|:--------------------|-------:|:------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| 4184 | France    |            204319 | ARKEMA FRANCE- Usine de Mont       | Orthez              | ARKEMA FRANCE                      | open             |     5202690 | Active         | 2014-01-27 16:54:18 |    nan | ...   |    nan |    nan |  26157 |  25703 |  25242 |  24779 |  24308 |  23835 |  23355 |  22873 |
| 2937 | France    |               102 | ARKEMA FRANCE - Usine de Mont      | MONT                | ARKEMA FRANCE                      | closed           |     5202690 | Account Closed | 2012-11-29 14:18:52 |  32802 | ...   |      0 |      0 |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |
| 4165 | France    |            204063 | SOCIETE FROMAGERE DE SAINTE CECILE | SAINTE-CECILE       | SOCIETE FROMAGERE DE SAINTE CECILE | open             |     5301510 | Active         | 2014-01-27 16:57:52 |    nan | ...   |    nan |    nan |   3864 |   3458 |   3063 |   2680 |   2309 |   1949 |   1602 |   1267 |
| 3913 | France    |              1121 | SOCIETE FROMAGERE DE SAINTE CECILE | Sainte Cécile      | BOUVIER                            | closed           |     5301510 | Account Closed | 2009-05-08 09:13:58 |   7790 | ...   |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |
| 4162 | France    |            204060 | SOCIETE FROMAGERE DE DOMFRONT      | Domfront            | SOCIETE FROMAGERE DE DOMFRONT      | open             |     5302209 | Active         | 2014-01-27 16:54:24 |    nan | ...   |    nan |    nan |   5780 |   5173 |   4582 |   4009 |   3454 |   2916 |   2396 |   1895 |
| 2961 | France    |               127 | SOCIETE FROMAGERE DE DOMFRONT      | Domfront            | SCOTTO                             | closed           |     5302209 | Account Closed | 2009-05-08 09:13:58 |  11326 | ...   |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |    nan |</div>



<br>

Lastly we'll wrap these steps in a function that will retrieve/download our data to/from the specified directory

```python
#exports
def get_installation_allocations_df(data_dir='data', redownload=False):    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    if redownload == True:
        df_search = get_installation_links_dataframe()
        df_installation_allocations = get_all_installation_allocations_df(df_search)
        df_installation_allocations.to_csv(f'{data_dir}/installation_allocations.csv', index=False)
    else:
        df_installation_allocations = pd.read_csv(f'{data_dir}/installation_allocations.csv')
        
    return df_installation_allocations
```

```python
redownload_installation_allocations = False

df_installation_allocations = get_installation_allocations_df(
    data_dir='../data', 
    redownload=redownload_installation_allocations
)
```
