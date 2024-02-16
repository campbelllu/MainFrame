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

#save any data frame into a csv for later use. Param's: save location, df to be saved, name of csv as string
def simple_saveDF_to_csv(folder, df, name, index_flag):
    try:
        df.to_csv(folder + name + '.csv', index = index_flag)
        print("DF saved to CSV in location: " + folder + name + '.csv.')
    except Exception as err:
        print("Simple Save to CSV Error Message:")
        print(err)

#load csv's into dataframe
def simple_get_df_from_csv(folder, name):#, index_flag):
    try:
        df = pd.read_csv(folder + name + '.csv')#, index_col = index_flag)
    except FileNotFoundError as err:
        print("File Does Not Exist")
    else:
        return df

#Returns Named Column Data from CSV
def get_column_from_csv(file, col_name):
    #Get file, else throw a warning
    try:
        df = pd.read_csv(file)
    except FileNotFoundError:
        print("File Does Not Exist")
        # print("Error message: \n" + err)
    else:
        return df[col_name]

# Function returns a dataframe by providing a ticker and starting date, and saves it to csv
def save_to_csv_from_yahoo(folder, ticker, syear, smonth, sday, eyear, emonth, eday):
    # Defines the time periods to use
    # start = int(dt.datetime(syear, smonth, sday).strftime("%Y%m%d"))
    # end = int(dt.datetime(eyear, emonth, eday).strftime("%Y%m%d%H%M%S"))
    start = dt.datetime(syear, smonth, sday)
    end = dt. datetime(eyear, emonth, eday)
    try:
        print("Getting Data for: ", ticker)

        # #DEBUG
        # print("debugging s2csvfyahoo: st, end, df : ")
        # print(start)
        # print(end)
        # Reads data into a dataframe
        # df = web.DataReader(ticker, 'yahoo', start, end)#['Adj Close']
        df = yf.download(ticker, start, end)
        # #DEBUG
        # print("debugging s2csvfyahoo: st, end, df : ")
        # print(start)
        # print(end)
        # print(df)

        #Wait to avoid kick
        time.sleep(3)
        # Save data to a CSV file
        # For Windows
        # df.to_csv('C:/Users/derek/Documents/Python Finance/Python/' + ticker + '.csv')
        # For MacOS/Unix
        df.to_csv(folder + ticker + '.csv')
    except Exception as err:
        stocks_not_downloaded.append(ticker)
        print("Couldn't Get Data for :", ticker)
        print("Error message:")
        print(err)
    # return df

# Reads a dataframe from the CSV file, changes index to date and returns it
def get_df_from_csv(folder, ticker):
    # Try to get the file and if it doesn't exist issue a warning
    try:
        # For Windows
        # df = pd.read_csv('C:/Users/derek/Documents/Python Finance/Python/' + ticker + '.csv')
        # For MacOS
        df = pd.read_csv(folder + ticker + '.csv')
    except FileNotFoundError as err:
        print("File Does Not Exist")
        # print("Error message: \n" + err)
    else:
        return df

#hold stocks not downloaded on original pass through-download
stocks_not_downloaded = []
missing_stocks = []

### USING THE ABOVE
# tickers = get_column_from_csv("./full_commonstock_names.csv", "Symbol")
# print(tickers)

# folder = "./stock_data/"
# 
# for x in range(1):
#     save_to_csv_from_yahoo(folder, tickers[x],2020,1,1,2024,1,1)
# print("stocks not dl'd:")
# print(stocks_not_downloaded)
# print("missing stocks:")
# print(missing_stocks)

# msft = yf.Ticker("MSFT", period="10y")
# incStatTest = pd.DataFrame(msft.income_stmt)

# # print(incStatTest)
# incStatTest.to_csv("./stock_data/msftIncTest.csv")


# 
# 
#####