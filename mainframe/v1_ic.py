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

# Full downloaded list of every equity in USA
df_SymbolsAndNames = pd.read_csv('./full_stock_list.csv', usecols=['Symbol','Name'])
# df_FilteredList = pd.DataFrame() #unused, feels cute, might delete later
# print(df)

# Iterate through CSV, Name column, IF containing 'Common Stock', we keep it and add it to new, returned, df
def filter_onlyCommonStocks(df_full):
    df2 = df_full[df_full['Name'].str.contains('Common Stock')]#pd.DataFrame()    
    return df2
# df_FilteredList = filter_onlyCommonStocks(df_SymbolsAndNames)
# df_FilteredList.to_csv('full_commonstock_names.csv', index=False)
# print('csv created!')

#We have to parse full SEC CIK list and append CIK's to full_commonstock_names.csv
#add column to fcsn for CIK
# df_fcsn = pd.read_csv("./full_commonstock_names.csv")
# df_fcsn['CIK'] = "" 
# df_fcsn.to_csv('./full_commonstock_names2.csv', index=False)

#make fcl.json into a python dictionary
json_path = './full_cik_list.json'
with open(json_path, 'r') as j:
    fcl_dict = json.loads(j.read())
# print(fcl_dict["0"]['cik_str'])
def addCIKtoStockNameList():

    return 0
#for y in fcl, get "ticker" value=y
#for x in fcsn, if df['Ticker'] == y
#

#From Video 1

dgro = yf.Ticker("MSFT")
dict = dgro.info
df = pd.DataFrame.from_dict(dict,orient='index')
df = df.reset_index()
df.to_csv('./stock_data/msftTest.csv', index=False)
# print(df)

        


