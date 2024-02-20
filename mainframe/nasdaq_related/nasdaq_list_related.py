import numpy as np
import pandas as pd
import pandas_datareader.data as web
#docu: https://pandas-datareader.readthedocs.io/en/latest/ 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# %matplotlib inline
import datetime as dt
import mplfinance as mpf
import datetime as dt
import time
import yfinance as yf
import json
import pyarrow

#just to test how to import modules across project. will be removed pre-production.
# def mod_test():
#     print("you loaded correctly!")
    
# Iterate through NASDAQ CSV, Name column, IF containing 'Common Stock', we keep it and add it to new, returned, df
def filter_onlyCommonStocks(df_full):
    df2 = df_full[df_full['Name'].str.contains('Common Stock')]#pd.DataFrame()    
    return df2

# Load Full downloaded list of every equity in USA, from NASDAQ Screener
# df_SymbolsAndNames = pd.read_csv('./nasdaq_related/full_nasdaq_stocklist.csv', usecols=['Symbol','Name'])

#Filter only common stock shares, save it to csv
# df_FilteredList = filter_onlyCommonStocks(df_SymbolsAndNames)
# df_FilteredList.to_csv('./nasdaq_related/full_commonstock_names.csv', index=False)


