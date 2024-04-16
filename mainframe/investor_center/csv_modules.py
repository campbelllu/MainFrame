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
import os

def mod_test():
    print("you loaded correctly!")

#save any data frame into a csv for later use. Param's: save location, df to be saved, name of csv as string
# #It appears that saving to csv with indicies set to false, doesn't create the index row multiplier effect.
def simple_appendTo_csv(folder, df, name, index_flag):
    try:
        output_path = folder + name + '.csv'
        df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=index_flag)
        print("DF appended to CSV in location: " + folder + name + '.csv')
    except Exception as err:
        print("Simple Append to CSV Error Message:")
        print(err)

#save any data frame into a csv for later use. Param's: save location, df to be saved, name of csv as string
# #It appears that saving to csv with indicies set to false, doesn't create the index row multiplier effect.
def simple_saveDF_to_csv(folder, df, name, index_flag):
    try:
        df.to_csv(folder + name + '.csv', index = index_flag)
        print("DF saved to CSV in location: " + folder + name + '.csv')
    except Exception as err:
        print("Simple Save to CSV Error Message:")
        print(err)

#load csv's into dataframe
def simple_get_df_from_csv(folder, name, index_flag):
    try:
        df = pd.read_csv(folder + name + '.csv', dtype={'start':str}, index_col = index_flag) #dtype={'start':str} added to silence a dtype error, could cause issues down the line? (https://stackoverflow.com/questions/24251219/pandas-read-csv-low-memory-and-dtype-options)
    except FileNotFoundError as err:
        print("File Does Not Exist")
    else:
        return df

#load csv's into dataframe with type settings
def get_df_from_csv_with_typeset(folder, name, dict1):#, index_flag):
    try:
        df = pd.read_csv(folder + name + '.csv', converters = dict1)#, index_col = index_flag)
    except FileNotFoundError as err:
        print("File Does Not Exist")
        print(err)
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

