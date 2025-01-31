import numpy as np
import pandas as pd
# import pandas_datareader.data as web
#docu: https://pandas-datareader.readthedocs.io/en/latest/ 
import matplotlib as mpl
import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# %matplotlib inline
import datetime as dt
# import mplfinance as mpf
# import datetime as dt
import time
import yfinance as yf
# import json

#From Video 1

# dgro = yf.Ticker("DGRO")
# dict1 = dgro.info
# for x in dict1:
#     print(x)
    # print(dict[x])
# df = pd.DataFrame.from_dict(dict,orient='index')
# df = df.reset_index()
# df.to_csv('./stock_data/msftTest.csv', index=False)
# # print(df)

###################################################

# Define ETFs to compare 
etfs = ["SCHH", "RFI"] # # Example ETFs ; iwy==ymag

# Fetch historical price data for each ETF 
etf_data = {} 
for etf in etfs: 
    data = yf.Ticker(etf).history(period="20y") # Fetch 1 year of data 
    # for x in data:
    #     print(x)
    # etf_data[etf + '-Close'] = data["Close"] # Store only closing prices 
    etf_data[etf + '-AdjClose'] = data["Close"] - data["Dividends"]#.cumsum() # adjusted closing prices approximation #LUKE CUMSUM DROP IT I THINK
    etf_data[etf + '-TotalReturn'] = data['Close'] + data["Dividends"].cumsum() #everything drip'd
    etf_data[etf + '-Divs'] = data['Dividends']
    # etf_data[etf + '-Yield'] = etf_data[etf + '-Divs'] / etf_data[etf + '-AdjClose']

# Combine into a single DataFrame with dates aligned, drop nulls to avoid lack of data due to inception dates
df = pd.DataFrame(etf_data).dropna(how="any")
# Reset index to make Date a column 
df = df.reset_index() 
# Rename columns for clarity 
df.columns = ["Date"] + list(etf_data.keys())

# df['CloseComparison'] = df[etfs[1] + '-Close'] / df[etfs[0] + '-Close']
# df['CloseNorm_compare'] = df['CloseComparison'] / df['CloseComparison'].iloc[0]
df['AdjComparison'] = df[etfs[1] + '-AdjClose'] / df[etfs[0] + '-AdjClose']
df['AdjNorm_compare'] = df['AdjComparison'] / df['AdjComparison'].iloc[0]
df['TRComparison'] = df[etfs[1] + '-TotalReturn'] / df[etfs[0] + '-TotalReturn']
df['TRNorm_compare'] = df['TRComparison'] / df['TRComparison'].iloc[0]

# countOverOne = (df["AdjNorm_compare"] > 1).sum() 
percentOverOne = (df["AdjNorm_compare"] > 1).mean() * 100
percentOverOneLastTen = (df["AdjNorm_compare"].iloc[-10:] > 1).mean() * 100
TRpercentOverOne = (df["TRNorm_compare"] > 1).mean() * 100
TRpercentOverOneLastTen = (df["TRNorm_compare"].iloc[-10:] > 1).mean() * 100

etf1gain = df[etfs[1] + '-AdjClose'].iloc[-1] - df[etfs[1] + '-AdjClose'].iloc[0]
etf0gain = df[etfs[0] + '-AdjClose'].iloc[-1] - df[etfs[0] + '-AdjClose'].iloc[0]

df['PriceGrowthRate'] = df["AdjNorm_compare"].pct_change() * 100
df['TRGrowthRate'] = df["TRNorm_compare"].pct_change() * 100

# df['etf1_gr'] = df[etfs[0]].pct_change() * 100
# df['etf2_gr'] = df[etfs[1]].pct_change() * 100

# Display DataFrame 
# print(etfs)
# print(etfs[1])
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn', 'TRNorm_compare']].tail(20).to_string())
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn',  'AdjNorm_compare', 'TRNorm_compare']].to_string()) #etfs[0] + '-Divs', etfs[1] + '-Divs',
# print(df.to_string())

#LUKE
print('Average compare: ' + str(df['AdjNorm_compare'].mean()))
print('Average compare, last 10: ' + str(df['AdjNorm_compare'].iloc[-10:].mean()))
print('Percentage of beating the underlying: ' + str(percentOverOne))
print('Percentage of beating the underlying, last 10: ' + str(percentOverOneLastTen))
print('Price GR: ' +  str(df['PriceGrowthRate'].mean() * 100))
print('Percentage TR beating the underlying: ' + str(TRpercentOverOne))
print('Percentage TR beating the underlying, last 10: ' + str(TRpercentOverOneLastTen))
print('TR GR: ' +  str(df['TRGrowthRate'].mean() * 100))
print('Total Dividends & price gain target: ' + str(df[etfs[0] + '-Divs'].sum()) + ', ' + str(etf0gain))
# print('Target Yield: ' + str(df[etfs[0] + '-Yield'].iloc[-1]))
print('Total Dividends & price gain test: ' + str(df[etfs[1] + '-Divs'].sum()) + ', ' + str(etf1gain))
####
# print('Test Yield: ' + str(df[etfs[1] + '-Yield'].iloc[-1]))

# print('compare to check: ' + str(countOverOne / len(df["AdjNorm_compare"]) * 100))
# print(df.head(15))
# print(df.tail(15))
# print(df.to_string())

plt.figure(figsize=(10,5))

x_num = np.arange(len(df))
# print("checking nulls:")
# print(df['AdjNorm_compare'].isna().sum())
# print(df['TRNorm_compare'].isna().sum())
# print('checking uniques')
# print(df['AdjNorm_compare'].nunique())
# print(df['TRNorm_compare'].nunique())
m1, b1 = np.polyfit(x_num, df['AdjNorm_compare'], 1)
m2, b2 = np.polyfit(x_num, df['TRNorm_compare'], 1)

plt.plot(df['Date'], df['AdjNorm_compare'], label='Price', color='blue', alpha=1)
plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PriceTrend', color='blue', alpha=0.9)

plt.plot(df['Date'], df['TRNorm_compare'], label='Total Return', color='red', alpha=1)
plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='TotalReturnTrend', color='red', alpha=0.9)

plt.title('Relationships ' + etfs[1] + '/' + etfs[0])
plt.xlabel('Date')
plt.ylabel('Normalized Relation Ratios')
plt.legend()
# plt.ioff()
plt.grid(True)
plt.show()

# plt.savefig('justagraph3.png')