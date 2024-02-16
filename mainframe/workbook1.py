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

# from  ./csv_modules.py import *
import csv_modules as csv


#LUKE FIGURE OUT HOW TO REMOVE INDEX FROM DATAFRAME
#We have to parse full SEC CIK list into a df
def convert_CIKdict_to_df(dictionary):
    df = pd.DataFrame()
    cik = "cik_str"
    ticker = "ticker"
    name = "title"
    try:
        #make dict into lists, easier to add to df
        tlist = []
        nlist = []
        clist = []
        for x in dictionary:
            tlist.append(dictionary[x][ticker])
            nlist.append(dictionary[x][name])
            clist.append(dictionary[x][cik])
        #append lists into appropriate columns of df1
        df['Ticker'] = tlist
        df['Company Name'] = nlist
        df['CIK'] = clist
        df['CIK'] = df['CIK'].astype(str).str.zfill(10) #check indentation upon copy
    except Exception as err:
        print(err)
    else:
        print("DF made! Here it is!")
        # print(df)
        return df

#Manually saved json of tickers and cik's from SEC. Methods for automating download to be added later.
json_path = './sec_related/full_cik_list.json'
#turn it into a dict to feed into above function
with open(json_path, 'r') as j:
    fcl_dict = json.loads(j.read())
# print(fcl_dict)

#Turn that dict into a df, check how it looks
# df2 = convert_CIKdict_to_df(fcl_dict)
# print(df2)
# print("^^^ THE DF after formatting")


#Make the CSV, check name and save-location before executing!
# csv.simple_saveDF_to_csv('./sec_related/', df2, 'full_tickers_and_ciks2', False)

dftest1 = csv.simple_get_df_from_csv('./sec_related/', 'full_tickers_and_ciks')#, False)
# print(dftest1)
# print("^^^DF Made before index=false saving")
# print("VVVVDF Made AFTER index=false saving")
dftest2 = csv.simple_get_df_from_csv('./sec_related/', 'full_tickers_and_ciks2')#, False)
# print(dftest2)
# print("^^^DF Made AFTER index=false saving")

dftest3 = csv.simple_get_df_from_csv('./sec_related/', 'full_tickers_and_ciks2')#, None)

print(dftest1.loc[4])
print(" ")
print(dftest2.loc[4])
print(" ")
print(dftest3.loc[4])
#It appears that saving to csv with indicies set to false, doesn't create the index row multiplier effect.
# loading false, or none, in index_col param, doesn't seem to make any difference. deprecated for now.


#From Video 1

# dgro = yf.Ticker("MSFT")
# dict = dgro.info
# df = pd.DataFrame.from_dict(dict,orient='index')
# df = df.reset_index()
# df.to_csv('./stock_data/msftTest.csv', index=False)
# # print(df)

        


