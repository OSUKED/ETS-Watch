# ETS Watch

> `etswatch` provides a Python client for retrieving the latest data on the EU ETS market and its participants

Last updated: 2021-12-11 01:35

<br>

To install the library you can run:

`pip install etswatch`

To then download all of the EUTL accounts data you can run:

`python -m etswatch.cli download-all-accounts-data`

N.b. this will create a sub-directory called `data` in the directory that you run the command

<br>

### Long-Term Average Price

![Long-term average](https://github.com/OSUKED/ETS-Watch/raw/master/img/long_term_avg.png)

<br>

### Candle-Stick Chart for Last 8-Weeks

![Open, High, Low, Close & Volume](https://github.com/OSUKED/ETS-Watch/raw/master/img/ohlc_vol.png)
