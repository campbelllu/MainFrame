import numpy as np
import pandas as pd
from pandas_datareader import data as web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# %matplotlib inline
import datetime as dt
import mplfinance as mpf

df_SymbolsAndNames = pd.read_csv('./full_stock_list.csv', usecols=['Symbol','Name'])
df_FilteredList = pd.DataFrame()
# print(df)
# Now we need to iterate through the CSV, Name column, IF containing 'Common Stock', we keep it and add it to new df
def filter_stocks():
    df2 = df_SymbolsAndNames[df_SymbolsAndNames['Name'].str.contains('Common Stock')]#pd.DataFrame()
    # for row in df_SymbolsAndNames:
    # if df_SymbolsAndNames["B"].str.contains('Common Stock'):
    #     df2.assign()
    # if df_SymbolsAndNames[df_SymbolsAndNames["B"].str.contains('Common Stock')]:
    #     df2.assign(row)
        # if row.contains('Common Stock'):
        #     df2.assign(row)
    
    return df2

df_FilteredList = filter_stocks()
df_FilteredList.to_csv('full_commonstock_names.csv', index=False)
print('csv created!')
# print(df_FilteredList)
# print(df_FilteredList)