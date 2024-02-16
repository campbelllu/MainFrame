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



# Iterate through NASDAQ CSV, Name column, IF containing 'Common Stock', we keep it and add it to new, returned, df
def filter_onlyCommonStocks(df_full):
    df2 = df_full[df_full['Name'].str.contains('Common Stock')]#pd.DataFrame()    
    return df2
# df_FilteredList = filter_onlyCommonStocks(df_SymbolsAndNames)
# df_FilteredList.to_csv('full_commonstock_names.csv', index=False)
# Load Full downloaded list of every equity in USA, from NASDAQ Screener
# df_SymbolsAndNames = pd.read_csv('./full_stock_list.csv', usecols=['Symbol','Name'])
# df_FilteredList = pd.DataFrame() #unused, feels cute, might delete later
# print(df)
