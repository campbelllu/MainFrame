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

#Mild Cheatsheet##################################

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
etfs = ['QQQ', "QQQI"] # # Example ETFs ; iwy==ymag ##First underlying, second the one to test against it
time_period = "1y" #mo, y

# Fetch historical price data for each ETF 
etf_data = {} 
for etf in etfs: 
    data = yf.Ticker(etf).history(period=time_period) # Fetch 1 year of data 
  
    etf_data[etf + '-Close'] = data["Close"] # Store only closing prices 
    etf_data[etf + '-Divs'] = data['Dividends']
    etf_data[etf + '-TRScuffed'] = round(data['Close'] + data['Dividends'].cumsum(), 5)
    TRAlist = []

    for i in range(len(etf_data[etf + '-Close'])):        
        #Finding Total Return at that time, similar to the equation below this: 
        TRA = etf_data[etf + '-TRScuffed'].iloc[i] - etf_data[etf + '-Close'].iloc[0]
        # ((end price - initial price) + distributions over that time) / initial price
        #((data["Close"].iloc[i] - data["Close"].iloc[0]) + data['Dividends'].iloc[0].cumsum()) / data["Close"].iloc[0]

        TRAlist.append(round(TRA,5))

    etf_data[etf + '-TRActual'] = TRAlist
    
    # etf_data[etf + '-AdjClose'] = data['Close'] * (1 - (data['Dividends'].cumsum() / data['Close'].iloc[0])) # adjusted closing prices approximation #LUKE CUMSUM DROP IT I THINK # data["Close"] - data["Dividends"]# 
    # etf_data[etf + '-PricePlusDivThatDate'] = data['Close'] + data["Dividends"]#.cumsum() #everything drip'd

#Fixing TR divide by zero error
etf_data[etfs[0]+ '-TRActual'][0] = 1.00000
etf_data[etfs[1] + '-TRActual'][0] = 0.00001
# df_etfD = pd.DataFrame(etf_data)
# print(df_etfD.to_string())

# Combine into a single DataFrame with dates aligned, drop nulls to avoid lack of data due to inception dates
df = pd.DataFrame(etf_data).dropna(how="any")
# Reset index to make Date a column 
df = df.reset_index() 
# Rename columns for clarity 
df.columns = ["Date"] + list(etf_data.keys())

#Create comparisons, normalize
df['CloseComparison'] = df[etfs[1] + '-Close'] / df[etfs[0] + '-Close']
df['CloseNorm_compare'] = df['CloseComparison'] / df['CloseComparison'].iloc[0]
# df['AdjComparison'] = df[etfs[1] + '-AdjClose'] / df[etfs[0] + '-AdjClose']
# df['AdjNorm_compare'] = df['AdjComparison'] / df['AdjComparison'].iloc[0]
df['TRComparison'] = df[etfs[1] + '-TRActual'] / df[etfs[0] + '-TRActual']

# df['TRComparison'] = df['TRComparison'].fillna(0)
# print(df['TRComparison'].to_string())

# guh = []
# for i in range(len(df['TRComparison'])):   
#     print(df['TRComparison'].iloc[i] / df['TRComparison'].iloc[0])
df['TRNorm_compare'] = (df['TRComparison'] / df['TRComparison'].iloc[1])
# print(df['TRNorm_compare'].to_string())
print(df[[etfs[1]+'-TRActual',etfs[0]+'-TRActual','TRComparison','TRNorm_compare']].to_string())
#LUKE
#run this to see what we were seeing mid 2025
#huge volatility, qqq goes negative, it screws up the ratio and forces it negative, even though it should be looking at absolute value changes, and that should boost rating. 
#find a way to express their relationship via absolute values and you got it. TR is different from price returns because of those negative values. you can do it!

#Get percentage of time that fund beat the underlying
# countOverOne = (df["AdjNorm_compare"] > 1).sum() 
# percentOverOne = (df["AdjNorm_compare"] > 1).mean() * 100
# percentOverOneLastTen = (df["AdjNorm_compare"].iloc[-10:] > 1).mean() * 100
percentOverOne = (df["CloseNorm_compare"] > 1).mean() * 100
# percentOverOneLastTen = (df["CloseNorm_compare"].iloc[-10:] > 1).mean() * 100
TRpercentOverOne = (df["TRNorm_compare"] > 1).mean() * 100
# TRpercentOverOneLastTen = (df["TRNorm_compare"].iloc[-10:] > 1).mean() * 100

#Was I going for total return comparisons? delete because redundant now?
# etf1gain = (df[etfs[1] + '-AdjClose'].iloc[-1] - df[etfs[1] + '-AdjClose'].iloc[0]) / df[etfs[1] + '-AdjClose'].iloc[0] * 100
# etf0gain = (df[etfs[0] + '-AdjClose'].iloc[-1] - df[etfs[0] + '-AdjClose'].iloc[0]) / df[etfs[0] + '-AdjClose'].iloc[0] * 100
# percentDifferent = (etf0gain - etf1gain) / etf1gain * 100

#growth rates
# df['PriceGrowthRate'] = df["AdjNorm_compare"].pct_change() * 100
df['PriceGrowthRate'] = df["CloseNorm_compare"].pct_change() * 100
df['TRGrowthRate'] = df["TRNorm_compare"].pct_change(fill_method=None) * 100

#Terminal Data
# print('Average compare: ' + str(df['AdjNorm_compare'].mean()))
# print('Average compare, last 10: ' + str(df['AdjNorm_compare'].iloc[-10:].mean()))
print('Average compare, Price: ' + str(df['CloseNorm_compare'].mean()))
print('Percentage of Price beating the underlying: ' + str(percentOverOne))
print('Price Ratio Change AVG: ' +  str(df['PriceGrowthRate'].mean() * 100))

print('...')

print('Average compare, Total Return: ' + str(df['TRNorm_compare'].mean()))
print('Percentage of TR beating the underlying: ' + str(TRpercentOverOne))
print('Total Return Ratio Change AVG: ' +  str(df['TRGrowthRate'].mean() * 100))
# print('Percentage TR beating the underlying: ' + str(TRpercentOverOne))
# print('Percentage TR beating the underlying, last 10: ' + str(TRpercentOverOneLastTen))
# print('TR Ratio Change AVG: ' +  str(df['TRGrowthRate'].mean() * 100))
# print('Total Dividends & price gain target: ' + str(df[etfs[0] + '-Divs'].sum()) + ', ' + str(etf0gain))
# print('Total Dividends & price gain test: ' + str(df[etfs[1] + '-Divs'].sum()) + ', ' + str(etf1gain))
# print('Percentage difference in price gains: ' + str(percentDifferent))

# firstPR = df[etfs[1] + '-AdjClose'].iloc[0] / df[etfs[0] + '-AdjClose'].iloc[0]
# lastPR = df[etfs[1] + '-AdjClose'].iloc[-1] / df[etfs[0] + '-AdjClose'].iloc[-1]
# print('1st price ratio: ' + str(firstPR))
# print('last price ratio: ' + str(lastPR))

# df[etfs[1] + '-AdjClose'].iloc[0] / df[etfs[0] + '-AdjClose'].iloc[0]
####
# print('Test Yield: ' + str(df[etfs[1] + '-Yield'].iloc[-1]))

# print('compare to check: ' + str(countOverOne / len(df["AdjNorm_compare"]) * 100))
# print(df.head(15))
# print(df.tail(15))
# print(df.to_string())

###FIGURE INFO
plt.figure(figsize=(10,5))

x_num = np.arange(len(df))
# m1, b1 = np.polyfit(x_num, df['AdjNorm_compare'], 1)
m1, b1 = np.polyfit(x_num, df['CloseNorm_compare'], 1)
m2, b2 = np.polyfit(x_num, df['TRNorm_compare'], 1)

#comparisons and trendlines
#price trends


# plt.plot(df['Date'], df['AdjNorm_compare'], label='Price', color='red', alpha=1)


plt.plot(df['Date'], df['CloseNorm_compare'], label='Price', color='blue', alpha=1)
plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PriceTrend', color='blue', alpha=0.9)

plt.plot(df['Date'], df['TRNorm_compare'], label='TR', color='red', alpha=1)
plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='TR_Trend', color='red', alpha=0.9)

print('...')
print('Price trendline: y= ' + str(m1) + ' * x + ' + str(b1))
print('...')
print('TR trendline: y= ' + str(m2) + ' * x + ' + str(b2))
#TR trends
# plt.plot(df['Date'], df['TRNorm_compare'], label='Total Return', color='red', alpha=1)
# plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='TotalReturnTrend', color='red', alpha=0.9)

# #prices
# plt.plot(df['Date'], df[etfs[1] + '-Close'] / 100, label='Test Price', color='green', alpha=0.9)
# plt.plot(df['Date'], df[etfs[0] + '-Close'] / 3000, label='Target Price', color='orange', alpha=0.9)

#Graph info
plt.title('Relationship of ' + etfs[1] + '/' + etfs[0])
plt.xlabel('Date')
plt.ylabel('Normalized Relation Ratios')
plt.legend()
# plt.ioff()
plt.grid(True)
plt.show()
# plt.savefig('justagraph3.png')


# Display DataFrame 
# print(etfs)
# print(etfs[1])
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn', 'TRNorm_compare']].tail(200).to_string())
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn',  'AdjNorm_compare', 'TRNorm_compare']].to_string()) #etfs[0] + '-Divs', etfs[1] + '-Divs',
# print(df.to_string())