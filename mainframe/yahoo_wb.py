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

#From Video 1

# dgro = yf.Ticker("MSFT")
# dict = dgro.info
# df = pd.DataFrame.from_dict(dict,orient='index')
# df = df.reset_index()
# df.to_csv('./stock_data/msftTest.csv', index=False)
# # print(df)

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


# We calculate a percentage rate of return for each day to compare investments.
# Simple Rate of Return = (End Price - Beginning Price) / Beginning Price OR (EP / BP) - 1

# Shift provides the value from the previous day
# NaN is displayed because there was no previous day price for the 1st calculation
def add_daily_return_to_df(df, ticker):
    df['daily_return'] = (df['Adj Close'] / df['Adj Close'].shift(1)) - 1
    # Save data to a CSV file
    # For Windows
    # df.to_csv('C:/Users/derek/Documents/Python Finance/Python/' + ticker + '.csv')
    # For MacOS
    df.to_csv("/Users/derekbanas/Documents/Tutorials/Python for Finance/" + ticker + '.csv')
    return df  

def get_return_defined_time(df, syear, smonth, sday, eyear, emonth, eday):
    # Create string representations for the dates
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Use a mask to grab data between defined dates
    mask = (df['Date'] >= start) & (df['Date'] <= end)
    
    # Get the mean of the column named daily return
    daily_ret = df.loc[mask]['daily_return'].mean()
    
    # Get the number of days between 2 dates
    df2 = df.loc[mask]
    days = df2.shape[0]

    # Return the total return between 2 dates
    return (days * daily_ret)

# Receives a ticker and the date range for which to plot
def mplfinance_plot(ticker, chart_type, syear, smonth, sday, eyear, emonth, eday):
    # Create string representations for the dates
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    
    try:
        # For Windows
        # df = pd.read_csv('C:/Users/derek/Documents/Python Finance/Python/' + ticker + '.csv',index_col=0,parse_dates=True)
        # For MacOS
        df = pd.read_csv('/Users/derekbanas/Documents/Tutorials/Python for Finance/' + ticker + '.csv',index_col=0,parse_dates=True)
    except FileNotFoundError:
        print("File Doesn't Exist")
    else:
        
        # Set data.index as DatetimeIndex
        df.index = pd.DatetimeIndex(df['Date'])
        
        # Define to only use data between provided dates
        df_sub = df.loc[start:end]
        
        # A candlestick chart demonstrates the daily open, high, low and closing price of a stock
        mpf.plot(df_sub,type='candle')

        # Plot price changes
        mpf.plot(df_sub,type='line')

        # Moving averages provide trend information (Average of previous 4 observations)
        mpf.plot(df_sub,type='ohlc',mav=4)
        
        # Define a built in style
        s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 8})
        # Pass in the defined style to the whole canvas
        fig = mpf.figure(figsize=(12, 8), style=s) 
        # Candle stick chart subplot
        ax = fig.add_subplot(2,1,1) 
        # Volume chart subplot
        av = fig.add_subplot(2,1,2, sharex=ax)  

        # You can plot multiple MAVs, volume, non-trading days
        mpf.plot(df_sub,type=chart_type, mav=(3,5,7), ax=ax, volume=av, show_nontrading=True)

# Creates a simple price / date plot between dates
def price_plot(ticker, syear, smonth, sday, eyear, emonth, eday):
    # Create string representations for the dates
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    
    try:
        # For Windows
        # df = pd.read_csv('C:/Users/derek/Documents/Python Finance/Python/' + ticker + '.csv')
        # For MacOS
        df = pd.read_csv("/Users/derekbanas/Documents/Tutorials/Python for Finance/" + ticker + '.csv')
    except FileNotFoundError:
        print("File Doesn't Exist")
    else:
        
        # Set data.index as DatetimeIndex
        df.index = pd.DatetimeIndex(df['Date'])
        
        # Define to only use data between provided dates
        df_sub = df.loc[start:end]
        
        # Convert to Numpy array
        df_np = df_sub.to_numpy()
        
        # Get adjusted close data from the 5th column
        np_adj_close = df_np[:,5]
        
        # Get date from the 1st
        date_arr = df_np[:,1]
        
        # Defines area taken up by the plot
        fig = plt.figure(figsize=(12,8),dpi=100)
        axes = fig.add_axes([0,0,1,1])
        
        # Define the plot line color as navy
        axes.plot(date_arr, np_adj_close, color='navy')
        
        # Set max ticks on the x axis
        axes.xaxis.set_major_locator(plt.MaxNLocator(8))
        
        # Add a grid, color, dashes(5pts 1 pt dashes separated by 2pt space)
        axes.grid(True, color='0.6', dashes=(5, 2, 1, 2))
        
        # Set grid background color
        axes.set_facecolor('#FAEBD7')

def download_multiple_stocks(syear, smonth, sday, eyear, emonth, eday, *args):
    for x in args:
        save_to_csv_from_yahoo(x, syear, smonth, sday, eyear, emonth, eday)

def merge_df_by_column_name(col_name, syear, smonth, sday, eyear, emonth, eday, *tickers):
    # Will hold data for all dataframes with the same column name
    mult_df = pd.DataFrame()
    
    start = f"{syear}-{smonth}-{sday}"
    end = f"{eyear}-{emonth}-{eday}"
    
    for x in tickers:
        mult_df[x] = web.DataReader(x, 'yahoo', start, end)[col_name]
        
    return mult_df

def plot_return_mult_stocks(investment, stock_df):
    (stock_df / stock_df.iloc[0] * investment).plot(figsize = (15,6))

# Receives the dataframe with the Adj Close data along with the stock ticker
# Returns the mean and standard deviation associated with the ticker
def get_stock_mean_sd(stock_df, ticker):
    return stock_df[ticker].mean(), stock_df[ticker].std()

# Receives the dataframe with the stock ticker as the column name and
# the Adj Close values as the column data and returns the mean and 
# standard deviation
def get_mult_stock_mean_sd(stock_df):
    for stock in stock_df:
        mean, sd = get_stock_mean_sd(stock_df, stock)
        cov = sd / mean
        print("Stock: {:4} Mean: {:7.2f} Standard deviation: {:2.2f}".format(stock, mean, sd))
        print("Coefficient of Variation: {}\n".format(cov))

#Test all the above
# # Call to read the data from Yahoo into a CSV and then retrieve a Dataframe
# AMZN = save_to_csv_from_yahoo('AMZN', 2020, 1, 1, 2021, 1, 1)

# # Retrieve data from the CSV file
# AMZN = get_df_from_csv('AMZN')

# # Add daily return to function
# add_daily_return_to_df(AMZN, 'AMZN')

# # Get total return between dates
# tot_ret = get_return_defined_time(AMZN, 2020, 1, 1, 2021, 1, 1)
# print("Total Return :", tot_ret)

# # Use Matplotlib finance to print multiple charts
# # mplfinance_plot('AMZN', 'ohlc', 2020, 6, 1, 2021, 1, 1)

# price_plot('AMZN', 2020, 6, 1, 2021, 1, 1)

# # Download multiple stocks
# tickers = ["FB", "AAPL", "NFLX", "GOOG"]
# # download_multiple_stocks(2020, 1, 1, 2021, 1, 1, *tickers)

# # Merge dataframes from multiple stocks using the same column name
# tickers = ["FB", "AMZN", "AAPL", "NFLX", "GOOG"]
# mult_df = merge_df_by_column_name('Adj Close',  2020, 1, 1, 2021, 1, 1, *tickers)
# mult_df.tail()

# # Pass Investment Amount and Plot Returns using Multiple Stocks
# plot_return_mult_stocks(100, mult_df)

# # Pass multiple stocks with their adjusted close values to receive their
# # different means and standard deviations
# get_mult_stock_mean_sd(mult_df)
# mult_df

# # It is hard to compare stocks by standard deviation when their stock prices
# # are so different. The coefficient of variation is the ratio between the 
# # standard deviation and the mean and it provides a comparable standard deviation
# # We get it by dividing the standard deviation by the mean cov = std / mean
# # We see here that GOOG has the least amount of variability

#From Video 2
# #hold stocks not downloaded on original pass through-download
# stocks_not_downloaded = []
# missing_stocks = []