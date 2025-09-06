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
etfs = ['SPY', "SPYI"] # # Example ETFs ; iwy==ymag ##First underlying, second the one to test against it
time_period = "3y" #mo, y
start_date = "2023-01-01"
end_date = "2024-12-31"

# Fetch historical price data for each ETF 
etf_data = {} 
for etf in etfs: 
    # data = yf.Ticker(etf).history(period=time_period) # Fetch data from time_period
    data = yf.Ticker(etf).history(start=start_date, end=end_date) # Fetch data from start to end date

  
    etf_data[etf + '-Close'] = data["Close"] # Store only closing prices 
    etf_data[etf + '-Divs'] = data['Dividends']
    etf_data[etf + '-DivsSummed'] = data['Dividends'].cumsum()
    etf_data[etf + '-TRScuffed'] = round(data['Close'] + data['Dividends'].cumsum(), 5)
    TRAlist = []
    TRA_pct_change_list = []
    price_return = []
    price_return_pct_change = []
    first_close_price = etf_data[etf + '-Close'].iloc[0]

    for i in range(len(etf_data[etf + '-Close'])):        
        #Finding Total Return at that time, similar to the equation below this: 
        TRA = etf_data[etf + '-TRScuffed'].iloc[i] - first_close_price
        # ((end price - initial price) + distributions over that time) / initial price
        #((data["Close"].iloc[i] - data["Close"].iloc[0]) + data['Dividends'].iloc[0].cumsum()) / data["Close"].iloc[0]
        TRAlist.append(round(TRA,5))
        TRA_pct_change = TRA / first_close_price * 100
        TRA_pct_change_list.append(round(TRA_pct_change,5))

        #Finding price change data
        priceReturn = etf_data[etf + '-Close'].iloc[i] - first_close_price
        price_return.append(round(priceReturn,5))
        PR_pct_change = priceReturn / first_close_price * 100
        price_return_pct_change.append(round(PR_pct_change,5))

    etf_data[etf + '-PriceReturn'] = price_return
    etf_data[etf + '-PR_pct_change'] = price_return_pct_change
    etf_data[etf + '-TRActual'] = TRAlist
    etf_data[etf + '-TR_pct_change'] = TRA_pct_change_list

#Fixing TR and PR divide by zero error
etf_data[etfs[0]+ '-TR_pct_change'][0] = 1.00000
etf_data[etfs[1] + '-TR_pct_change'][0] = 0.00001
etf_data[etfs[0]+ '-PR_pct_change'][0] = 1.00000
etf_data[etfs[1] + '-PR_pct_change'][0] = 0.00001
# df_etfD = pd.DataFrame(etf_data)
# print(df_etfD.to_string())

# Combine into a single DataFrame with dates aligned, drop nulls to avoid lack of data due to inception dates
df = pd.DataFrame(etf_data).dropna(how="any")
# Reset index to make Date a column 
df = df.reset_index() 
# Rename columns for clarity 
df.columns = ["Date"] + list(etf_data.keys())

#correlation between prices, then total returns
df['Price_Correlation'] = df[etfs[1] + '-PR_pct_change'].corr(df[etfs[0] + '-PR_pct_change'])
df['TR_Correlation'] = df[etfs[1] + '-TR_pct_change'].corr(df[etfs[0] + '-TR_pct_change'])
#Create comparisons, normalize
df['CloseComparison'] = df[etfs[1] + '-Close'] / df[etfs[0] + '-Close']
df['CloseNorm_compare'] = df['CloseComparison'] / df['CloseComparison'].iloc[0]
#alt price comparison, redundant
# df['CloseComparison_pct'] = df[etfs[1] + '-PR_pct_change'] / df[etfs[0] + '-PR_pct_change']
# df['CloseNorm_compare_pct'] = df['CloseComparison_pct'] / df['CloseComparison_pct'].iloc[1]
#TR compare
df['TRComparison'] = df[etfs[1] + '-TR_pct_change'] / df[etfs[0] + '-TR_pct_change']
df['TRNorm_compare'] = (df['TRComparison'] / df['TRComparison'].iloc[1])

# print(df[['TRComparison', 'TRNorm_compare']].to_string())
# print(df['TRNorm_compare'].to_string())

# print(df[['Date', etfs[1]+'-TRActual',etfs[0]+'-TRActual','TRComparison','TRNorm_compare',]].to_string()) #etfs[1]+'-DivsSummed',etfs[0]+'-DivsSummed'
# print(df[['Date', etfs[1]+'-PriceReturn', etfs[1]+'-PR_pct_change' ,etfs[0]+'-PriceReturn', etfs[0]+'-PR_pct_change']].to_string())
# print(df[['Date', etfs[1]+'-TRActual', etfs[1]+'-TR_pct_change', etfs[0]+'-TRActual', etfs[0]+'-TR_pct_change']].to_string())
# print(df[['Date', etfs[1]+'-PriceReturn', etfs[1]+'-PR_pct_change', etfs[1]+'-TRActual', etfs[1]+'-TR_pct_change']].to_string())
# print(df[['Date', etfs[1] + '-PR_pct_change', etfs[0] + '-PR_pct_change', 'CloseComparison_pct', 'CloseNorm_compare_pct']].to_string())

#LUKE
#TR is wrong somehow. total return isn't calculated correctly because the tested's are beating the underlying by way too much. inaccurate twice.

#Get percentage of time that fund beat the underlying
percentOverOne = (df["CloseNorm_compare"] > 1).mean() * 100
# percentOverOne_pct = (df["CloseNorm_compare_pct"] > 1).mean() * 100
# percentOverOneLastTen = (df["CloseNorm_compare"].iloc[-10:] > 1).mean() * 100
TRpercentOverOne = (df["TRNorm_compare"] > 1).mean() * 100
# TRpercentOverOneLastTen = (df["TRNorm_compare"].iloc[-10:] > 1).mean() * 100

#growth rates
# df['PriceGrowthRate'] = df["AdjNorm_compare"].pct_change() * 100
df['PriceGrowthRate'] = df["CloseNorm_compare"].pct_change() * 100
# df['PriceGrowthRate_pct'] = df["CloseNorm_compare_pct"].pct_change() * 100
df['TRGrowthRate'] = df["TRNorm_compare"].pct_change(fill_method=None) * 100

#Terminal Data
# print('Average compare: ' + str(df['AdjNorm_compare'].mean()))
# print('Average compare, last 10: ' + str(df['AdjNorm_compare'].iloc[-10:].mean()))
print('Average compare, Price: ' + str(df['CloseNorm_compare'].mean()))
print('Percentage of Price beating the underlying: ' + str(percentOverOne))
print('Price Ratio Change AVG: ' +  str(df['PriceGrowthRate'].mean() * 100))
print(df[[etfs[1]+'-PriceReturn', 
            etfs[0]+'-PriceReturn', 
            etfs[1]+'-PR_pct_change', 
            etfs[0]+'-PR_pct_change']].iloc[-1])

print('...')

# print('Average compare, Price_pct: ' + str(df['CloseNorm_compare_pct'].mean()))
# print('Percentage of Price beating the underlying: ' + str(percentOverOne_pct))
# print('Price Ratio Change AVG: ' +  str(df['PriceGrowthRate_pct'].mean() * 100))
# print(df[[etfs[1]+'-PriceReturn', 
#             etfs[0]+'-PriceReturn', 
#             etfs[1]+'-PR_pct_change', 
#             etfs[0]+'-PR_pct_change']].iloc[-1])

# print('...')

print('Average compare, Total Return: ' + str(df['TRNorm_compare'].mean()))
print('Percentage of TR beating the underlying: ' + str(TRpercentOverOne))
print('Total Return Ratio Change AVG: ' +  str(df['TRGrowthRate'].mean() * 100))
print(df[[etfs[1]+'-TRActual', 
            etfs[0]+'-TRActual',
            etfs[1]+'-TR_pct_change', 
            etfs[0]+'-TR_pct_change']].iloc[-1])
# print('Percentage TR beating the underlying: ' + str(TRpercentOverOne))
# print('Percentage TR beating the underlying, last 10: ' + str(TRpercentOverOneLastTen))
# print('TR Ratio Change AVG: ' +  str(df['TRGrowthRate'].mean() * 100))
# print('Total Dividends & price gain target: ' + str(df[etfs[0] + '-Divs'].sum()) + ', ' + str(etf0gain))
# print('Total Dividends & price gain test: ' + str(df[etfs[1] + '-Divs'].sum()) + ', ' + str(etf1gain))
# print('Percentage difference in price gains: ' + str(percentDifferent))

###FIGURE INFO
plt.figure(figsize=(10,5))

x_num = np.arange(len(df))
# m1, b1 = np.polyfit(x_num, df['AdjNorm_compare'], 1)
m1, b1 = np.polyfit(x_num, df['CloseNorm_compare'], 1)
m2, b2 = np.polyfit(x_num, df['TRNorm_compare'], 1) 

#comparisons and trendlines
plt.plot(df['Date'], df['CloseNorm_compare'], label='Price', color='blue', alpha=1)
plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PriceTrend', color='blue', alpha=0.9)

plt.plot(df['Date'], df['TRNorm_compare'], label='TR', color='red', alpha=1)
plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='TR_Trend', color='red', alpha=0.9)

print('...')
print('Price trendline: y= ' + str(m1) + ' * x + ' + str(b1))
print('...')
print('TR trendline: y= ' + str(m2) + ' * x + ' + str(b2))

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