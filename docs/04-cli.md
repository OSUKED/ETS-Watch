# CLI



This notebook includes helper functions and processes used in the development of the CLI for ETS-Watch

<br>

### Imports

```python
#exports
from etswatch import prices
from etswatch.eutl import accounts

import os
import typer
```

```python
import dotenv
```

<br>

### Loading Environment Variables

```python
use_dotenv = True

if use_dotenv == True:
    assert dotenv.load_dotenv(), 'environment variables could not be loaded'
```

<br>

### Initialising CLI 

```python
#exports
app = typer.Typer()
```

<br>

### Download Commands

We'll start by creating a function for downloading the market prices data

```python
#exports
@app.command()
def download_mkt_prices(data_dir='data', print_dataset_head=True):
    api_key = os.getenv('QUANDL_API_KEY')
    df_ets = prices.get_ets_mkt_data(api_key)
    
    df_ets.to_csv(f'{data_dir}/market_prices.csv')
    
    if print_dataset_head == True:
        print(f'Output Tail (n=3):\n\n{df_ets.tail(3)}')
    
    return
```

```python
download_mkt_prices(data_dir='../data')
```

    c:\users\ayrto\desktop\side projects\ets-watch\etswatch\prices.py:35: FutureWarning: The default value of regex will change from True to False in a future version. In addition, single character regular expressions will*not* be treated as literal strings when regex=True.
      df.columns = df.columns.str.lower().str.replace('.', '').str.replace(' ', '_')
    

    Output Tail (n=3):
    
                 open   high    low  settle  change   wave  volume  \
    datetime                                                         
    2021-04-14  43.87  43.88  43.47   43.73   -0.03  43.75    28.0   
    2021-04-15  43.84  44.32  43.84   44.08    0.35  44.22     5.0   
    2021-04-16  44.53  44.53  44.53   44.33    0.25  44.53     1.0   
    
                prev_day_open_interest  efp_volume  efs_volume  block_volume  \
    datetime                                                                   
    2021-04-14                  4865.0         NaN         NaN        2290.0   
    2021-04-15                  2881.0         NaN         NaN         598.0   
    2021-04-16                  2483.0         NaN         NaN           NaN   
    
                close  
    datetime           
    2021-04-14  43.84  
    2021-04-15  44.19  
    2021-04-16  44.78  
    

<br>

Next we'll download the aircraft data

```python
#exports
@app.command()
def download_aircraft_accounts(data_dir='data', redownload=True, print_dataset_heads=True):
    df_search = accounts.get_search_df(data_dir=f'{data_dir}/..', redownload=redownload)   
    
    aircraft_dfs = accounts.get_aircraft_dfs(
        df_search, 
        data_dir=data_dir, 
        redownload=redownload
    )
    
    if print_dataset_heads == True:
        for dataset_name, df in aircraft_dfs.items():
            print(f'{dataset_name} (head, n=3):\n\n{df.head(3)}\n\n\n')
    
    return
```

```python
download_aircraft_accounts(data_dir='../data/aircraft', redownload=False)
```

    aircraft (head, n=3):
    
       account_id  aircraft_operator_id Unnamed: 2             monitoring_plan_id  \
    0       90574                200103      27702  BMLFUW-UW.1.3.2/0354-V/4/2009   
    1       90727                200108        194  BMFLUW-UW.1.3.2/0084-V/4/2010   
    2       90728                200109      36057         UW.1.3.2/0085-V/4/2011   
    
      monitoring_plan_start_date  monitoring_plan_expiration_Date  \
    0                 2010-01-01                              NaN   
    1                 2010-01-01                              NaN   
    2                 2010-01-01                              NaN   
    
       subsidiary_undertaking_name  parent_undertaking_name  EPRTR_id call_sign  \
    0                          NaN                      NaN       NaN       JAG   
    1                          NaN                      NaN       NaN       NaN   
    2                          NaN                      NaN       NaN       NaN   
    
       initial_emissions_year  first_address_line  second_address_line  postcode  \
    0                    2013                 NaN                  NaN       NaN   
    1                    2012                 NaN                  NaN       NaN   
    2                    2012                 NaN                  NaN       NaN   
    
       city country  lat  lon                    main_activity  
    0   NaN      AT  NaN  NaN  10-Aircraft operator activities  
    1   NaN      AT  NaN  NaN  10-Aircraft operator activities  
    2   NaN      AT  NaN  NaN  10-Aircraft operator activities  
    
    
    
    allocated_allowances (head, n=3):
    
       account_id  2005  2006  2007  2008  2009  2010  2011       2012    2013  \
    0     1020625   NaN   NaN   NaN   NaN   NaN   NaN   NaN        NaN     NaN   
    1      106049   NaN   NaN   NaN   NaN   NaN   NaN   NaN       75.0    41.0   
    2      106068   NaN   NaN   NaN   NaN   NaN   NaN   NaN  4586700.0  1297.0   
    
       ...  2021  2022  2023 2024 2025 2026 2027  2028  2029  2030  
    0  ...   NaN   NaN   NaN  NaN  NaN  NaN  NaN   NaN   NaN   NaN  
    1  ...  36.0  35.0  35.0  NaN  NaN  NaN  NaN   NaN   NaN   NaN  
    2  ...   NaN   NaN   NaN  NaN  NaN  NaN  NaN   NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    compliance_code (head, n=3):
    
       account_id  2005  2006  2007  2008  2009  2010  2011 2012 2013  ... 2021  \
    0     1020625   NaN   NaN   NaN   NaN   NaN   NaN   NaN  NaN  NaN  ...  NaN   
    1      106049   NaN   NaN   NaN   NaN   NaN   NaN   NaN   A*    A  ...  NaN   
    2      106068   NaN   NaN   NaN   NaN   NaN   NaN   NaN    A    A  ...  NaN   
    
      2022 2023 2024 2025 2026  2027  2028  2029  2030  
    0  NaN  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    1  NaN  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    2  NaN  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    owners (head, n=3):
    
       account_id national_administrator         account_type  \
    0       90574                Austria  100-Holding Account   
    1       90727                Austria  100-Holding Account   
    2       90728                Austria  100-Holding Account   
    
                 account_holder_name  aircraft_operator_id  \
    0  Jetalliance Flugbetriebs GmbH                200103   
    1                     Glock GmbH                200108   
    2            Glock Services GmbH                200109   
    
      company_registration_number account_status            type  \
    0                  FN 203001g         closed  Account holder   
    1                    FN64142b         closed  Account holder   
    2                   FN329154a         closed  Account holder   
    
                                name legal_entity_identifier  \
    0  Jetalliance Flugbetriebs GmbH                     NaN   
    1                     Glock GmbH                     NaN   
    2            Glock Services GmbH                     NaN   
    
         first_address_line second_address_line postcode                     city  \
    0           Flugplatz 1                 NaN     2542             Kottingbrunn   
    1        Loibstrasse 16                 NaN     9170                  Ferlach   
    2  Schneeweisshofweg 32                 NaN     9521  Treffen am Ossiachersee   
    
       country  telephone_1  telephone_2  email  
    0  Austria          NaN          NaN    NaN  
    1  Austria          NaN          NaN    NaN  
    2  Austria          NaN          NaN    NaN  
    
    
    
    units_surrendered (head, n=3):
    
       account_id  2005  2006  2007  2008  2009  2010  2011    2012    2013  ...  \
    0     1020625   NaN   NaN   NaN   NaN   NaN   NaN   NaN     NaN     NaN  ...   
    1      106049   NaN   NaN   NaN   NaN   NaN   NaN   NaN  1945.0  2523.0  ...   
    2      106068   NaN   NaN   NaN   NaN   NaN   NaN   NaN  2130.0     NaN  ...   
    
       2021  2022  2023  2024  2025  2026  2027  2028  2029  2030  
    0   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN  
    1   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN  
    2   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    verified_emissions (head, n=3):
    
       account_id  2005  2006  2007  2008  2009  2010  2011  2012  2013  ...  \
    0     1020625   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN   NaN  ...   
    1      106049   NaN   NaN   NaN   NaN   NaN   NaN   NaN  1991  1949  ...   
    2      106068   NaN   NaN   NaN   NaN   NaN   NaN   NaN  2130  2507  ...   
    
           2021 2022 2023 2024 2025 2026 2027 2028  2029  2030  
    0       NaN  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   NaN  
    1  Excluded  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   NaN  
    2       NaN  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    

<br>

We'll then do the same for the installation accounts

```python
#exports
@app.command()
def download_installation_accounts(data_dir='data', redownload=True, print_dataset_heads=True):
    df_search = accounts.get_search_df(data_dir=f'{data_dir}/..', redownload=redownload)   
    
    installation_dfs = accounts.get_installation_dfs(
        df_search, 
        data_dir=data_dir, 
        redownload=redownload
    )
    
    if print_dataset_heads == True:
        for dataset_name, df in installation_dfs.items():
            print(f'{dataset_name} (head, n=3):\n\n{df.head(3)}\n\n\n')
    
    return
```

```python
download_installation_accounts(data_dir='../data/installations', redownload=False)
```

    allocated_allowances (head, n=3):
    
       account_id      2005      2006      2007      2008      2009      2010  \
    0      100000  269940.0  269941.0  269941.0  153922.0  153922.0  153922.0   
    1      100001  146438.0  146438.0  146438.0  131200.0  131197.0  131197.0   
    2      100002      10.0      11.0       0.0       NaN       NaN       NaN   
    
           2011      2012   2013  ... 2021 2022 2023 2024 2025 2026 2027  2028  \
    0  153922.0  153922.0   3167  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    1  131197.0  131197.0  16892  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    2       NaN       NaN    NaN  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    
       2029  2030  
    0   NaN   NaN  
    1   NaN   NaN  
    2   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    compliance_code (head, n=3):
    
       account_id 2005 2006 2007 2008 2009 2010 2011 2012 2013  ... 2021 2022  \
    0      100000    A    A    A    A    A    A    A    A    A  ...  NaN  NaN   
    1      100001    A    A    A    A    A    A    A    A    A  ...  NaN  NaN   
    2      100002    A    A  NaN  NaN    C    C  NaN  NaN  NaN  ...  NaN  NaN   
    
      2023 2024 2025 2026  2027  2028  2029  2030  
    0  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    1  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    2  NaN  NaN  NaN  NaN   NaN   NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    installations (head, n=3):
    
       account_id  installation_id installation_name permit_id permit_entry_date  \
    0       93707               47      AGRANA Gmünd    ILE166        2005-01-26   
    1       93708               50    AGRANA Aschach    ILE165        2005-10-18   
    2       93709               51      AGRANA Tulln    ILE161        2005-07-01   
    
      permit_expiration_Date subsidiary_undertaking_name parent_undertaking_name  \
    0                    NaN                         NaN                     NaN   
    1                    NaN                         NaN                     NaN   
    2                    NaN                         NaN                     NaN   
    
          EPRTR_id  initial_emissions_year  final_emissions_year  \
    0          NaN                    2005                     0   
    1  20000.00442                    2005                     0   
    2  20000.00320                    2005                     0   
    
                first_address_line second_address_line postcode     city country  \
    0             Conrathstrasse 7                 NaN     3953    Gmünd      AT   
    1            Raiffeisenweg 2-6                 NaN     4082  Aschach      AT   
    2  Josef-Reither-Strasse 21-23                 NaN     3430    Tulln      AT   
    
       lat  lon           main_activity  
    0  NaN  NaN  20-Combustion of fuels  
    1  NaN  NaN  20-Combustion of fuels  
    2  NaN  NaN  20-Combustion of fuels  
    
    
    
    owners (head, n=3):
    
       account_id national_administrator         account_type account_holder_name  \
    0       93707                Austria  100-Holding Account  AGRANA Stärke GmbH   
    1       93708                Austria  100-Holding Account  AGRANA Stärke GmbH   
    2       93709                Austria  100-Holding Account  AGRANA Zucker GmbH   
    
       installation_id company_registration_number account_status            type  \
    0               47                 FN 252477 s           open  Account holder   
    1               50                 FN 252477 s           open  Account holder   
    2               51                  FN 51929 t           open  Account holder   
    
                     name legal_entity_identifier  \
    0  AGRANA Stärke GmbH                     NaN   
    1  AGRANA Stärke GmbH                     NaN   
    2  AGRANA Zucker GmbH                     NaN   
    
                         first_address_line second_address_line postcode  city  \
    0  Friedrich-Wilhelm-Raiffeisen-Platz 1                 NaN     1020  Wien   
    1  Friedrich-Wilhelm-Raiffeisen-Platz 1                 NaN     1020  Wien   
    2  Friedrich-Wilhelm-Raiffeisen-Platz 1                 NaN     1020  Wien   
    
       country  telephone_1 telephone_2  email  
    0  Austria          NaN         NaN    NaN  
    1  Austria          NaN         NaN    NaN  
    2  Austria          NaN         NaN    NaN  
    
    
    
    units_surrendered (head, n=3):
    
       account_id      2005      2006      2007      2008      2009      2010  \
    0      100000   87923.0  106745.0  117404.0  205430.0  105795.0   25900.0   
    1      100001  134139.0  138143.0  170415.0  143182.0  149405.0  142121.0   
    2      100002       NaN       NaN       NaN       NaN       NaN       NaN   
    
           2011      2012      2013  ...  2021  2022  2023  2024  2025  2026  \
    0  101784.0   21384.0    5671.0  ...   NaN   NaN   NaN   NaN   NaN   NaN   
    1  119263.0  102751.0  101881.0  ...   NaN   NaN   NaN   NaN   NaN   NaN   
    2       NaN       NaN       NaN  ...   NaN   NaN   NaN   NaN   NaN   NaN   
    
       2027  2028  2029  2030  
    0   NaN   NaN   NaN   NaN  
    1   NaN   NaN   NaN   NaN  
    2   NaN   NaN   NaN   NaN  
    
    [3 rows x 27 columns]
    
    
    
    verified_emissions (head, n=3):
    
       account_id    2005    2006    2007    2008          2009          2010  \
    0      100000   87923  106745  117404  126296        105795        105034   
    1      100001  134139  138143  170415  143182        149405        142121   
    2      100002       0     NaN     NaN     NaN  Not Reported  Not Reported   
    
         2011    2012    2013  ... 2021 2022 2023 2024 2025 2026 2027 2028  2029  \
    0  101784   21384    5671  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    1  119263  102751  101881  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    2     NaN     NaN     NaN  ...  NaN  NaN  NaN  NaN  NaN  NaN  NaN  NaN   NaN   
    
       2030  
    0   NaN  
    1   NaN  
    2   NaN  
    
    [3 rows x 27 columns]
    
    
    
    

<br>

Lastly we'll create a function for downloading all of the accounts data in one step (including the accounts search data)

```python
#exports
@app.command()
def download_all_accounts_data(data_dir='data', search=True, installations=True, aircraft=True):
    all_dfs = accounts.retrieve_all_data(data_dir=data_dir, redownload_search=search, redownload_installations=installations, redownload_aircraft=aircraft)   
    
    return
```

```python
download_all_accounts_data(data_dir='../data', search=False, installations=False, aircraft=False)
```

<br>

### Context Handling

Finally we need to ensure the CLI app is available when the module is loaded.

N.b. we've included the condition `'__file__' in globals()` to make sure this isn't when inside the notebook

```python
#exports
if __name__ == '__main__' and '__file__' in globals():
    app()
```
