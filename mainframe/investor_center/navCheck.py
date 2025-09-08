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

#used to test .pct_change function
def grManualCalc(df_col):
    try:
        origList = df_col.tolist()
        growthList = []
        growthList.append(np.nan)
        for x in range(len(origList)-1):
            diff = abs((origList[x+1])-origList[x])
            if origList[x] > origList[x+1]:
                diff = diff * -1
            if abs(origList[x]) == 0:
                change = np.nan
            else:
                change = diff / abs(origList[x]) * 100
            growthList.append(change)
         
        return growthList

    except Exception as err:
        print("grManualCalc error: ")
        print(err)


# Define ETFs to compare 
etfs = ['QQQI', "GPIQ"] # # Example ETFs ; iwy==ymag ##First underlying, second the one to test against it
time_period = "1y" #mo, y
start_date = "2024-02-01"
end_date = "2025-12-31"

# Fetch historical price data for each ETF 
etf_data = {} 
for etf in etfs: 
    # data = yf.Ticker(etf).history(period=time_period, auto_adjust=False) # Fetch data from time_period
    data = yf.Ticker(etf).history(start=start_date, end=end_date, auto_adjust=False) # Fetch data from start to end date
  
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
        TRA_pct_change = (TRA / first_close_price) * 100
        TRA_pct_change_list.append(round(TRA_pct_change,5))

        #Finding price change data
        priceReturn = etf_data[etf + '-Close'].iloc[i] - first_close_price
        price_return.append(round(priceReturn,5))
        PR_pct_change = (priceReturn / first_close_price) * 100
        price_return_pct_change.append(round(PR_pct_change,5))

    etf_data[etf + '-PriceReturn'] = price_return
    etf_data[etf + '-PR_pct_change'] = price_return_pct_change
    etf_data[etf + '-TRActual'] = TRAlist
    etf_data[etf + '-TR_pct_change'] = TRA_pct_change_list

#Fixing TR and PR divide by zero error; replaced fix with min values as we're now just graphing total returns directly
etf_data[etfs[0]+ '-TR_pct_change'][0] = 0.00001 #1.00000
etf_data[etfs[1] + '-TR_pct_change'][0] = 0.00001
etf_data[etfs[0]+ '-PR_pct_change'][0] = 0.00001 #1.00000
etf_data[etfs[1] + '-PR_pct_change'][0] = 0.00001

#LUKE
#also, add CAGR to TR calcs, and price action of both underlying and target
#cagr = (v_final/v_initial)^(1/t) - 1, t is  years
#add correlations to final prints

# Combine into a single DataFrame with dates aligned, drop nulls to avoid lack of data due to inception dates
df = pd.DataFrame(etf_data).dropna(how="any")
# Reset index to make Date a column 
df = df.reset_index() 
# Rename columns for clarity 
df.columns = ["Date"] + list(etf_data.keys())

#correlation between prices, then total returns
Price_Correlation = round(df[etfs[1] + '-PR_pct_change'].corr(df[etfs[0] + '-PR_pct_change']), 5)
TR_Correlation = round(df[etfs[1] + '-TR_pct_change'].corr(df[etfs[0] + '-TR_pct_change']), 5)
#Create comparisons, normalize
df['CloseComparison'] = df[etfs[1] + '-Close'] / df[etfs[0] + '-Close']
df['CloseNorm_compare'] = df['CloseComparison'] / df['CloseComparison'].iloc[0]

#TR compare
#working on a fix. turns out unused altogether. abs vs no abs produces same shaped of graph, just different y-values. 
df['NoAbs'] = (df[etfs[1] + '-TR_pct_change'] - df[etfs[0] + '-TR_pct_change'])
# df['NoAbs_gr'] = grManualCalc(df['NoAbs'])
# df['TRNorm_compare'] = (df[etfs[1] + '-TR_pct_change'] - df[etfs[0] + '-TR_pct_change']).abs()

##Classic total return compare
# df['TRComparison'] = df[etfs[1] + '-TR_pct_change'] / df[etfs[0] + '-TR_pct_change']
# df['TRNorm_compare'] = (df['TRComparison'] / df['TRComparison'].iloc[1])

#Get percentage of time that fund beat the underlying; only used for price now
percentOverOne = (df["CloseNorm_compare"] > 1).mean() * 100
# percentOverOneLastTen = (df["CloseNorm_compare"].iloc[-10:] > 1).mean() * 100
TRpercentOverOne = (df["NoAbs"] > 1).mean() * 100 #(df["TRNorm_compare"] > 1).mean() * 100
# TRpercentOverOneLastTen = (df["TRNorm_compare"].iloc[-10:] > 1).mean() * 100

#Get Mean and Median from difference in total return percentages; over time this might tend to infinity anyway
#However, in comparing time frames for different funds, similar underlying different strategy, this might be useful!
medianTRdiff = round(df['NoAbs'].median(), 4)
averageTRdiff = round(df['NoAbs'].mean(), 4)
#luke, price means and medians?

#growth rates
df['PriceGrowthRate'] = grManualCalc(df["CloseNorm_compare"])#.pct_change() * 100
#TR growth rates become meaningless while measuring difference in growth rates. essentially how fast they are moving apart. 
#it sounds useful, until looking at 2024-9/2025. 9522% returned QQQI/QQQ. essentially saying QQQI standing still in some cases. really only pointing out
#the volatility of the underlying. not helpful here.
# df['TRGrowthRate'] = df["TRNorm_compare"].pct_change(fill_method=None) * 100
# df['TRGrowthRate'] = grManualCalc(df["NoAbs"])#.pct_change(fill_method=None) * 100 #TRNorm_compare

###FIGURE INFO

def priceGraph():
    # plt.figure(figsize=(10,5))
    plt.subplot(2,2,1)

    x_num = np.arange(len(df))
    m2, b2 = np.polyfit(x_num, df[etfs[0] + '-PR_pct_change'], 1) #price of underlying
    m3, b3 = np.polyfit(x_num, df[etfs[1] + '-PR_pct_change'], 1) #price of target

    #comparisons and trendlines
    # plt.plot(df['Date'], df['CloseNorm_compare'], label='Price Ratio', color='green', alpha=1)
    # plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PR-Trend', color='green', alpha=0.9)

    plt.plot(df['Date'], df[etfs[0] + '-PR_pct_change'], label=etfs[0] +' Price', color='blue', alpha=1)
    plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label=etfs[0] + ' Price Trend', color='blue', alpha=0.9)

    plt.plot(df['Date'], df[etfs[1] + '-PR_pct_change'], label=etfs[1] + ' Price', color='red', alpha=1)
    plt.plot(df['Date'], m3 * x_num + b3, linestyle="dashed", label=etfs[1] + ' Price Trend', color='red', alpha=0.9)

    # df['Price_Correlation'] = df[etfs[1] + '-PR_pct_change'].corr(df[etfs[0] + '-PR_pct_change'])
    print('...')    
    print('Price Return Stats: ')
    print('Percentage of Target Price beating the Underlying: ' + str(percentOverOne) + '%')
    print('')
    print('Price Return Correlation: ' + str(Price_Correlation))
    print('')
    print('Underlying Price trendline: y=mx+b: m = ' + str(round(m2, 5)) + '.')
    print('Target Price trendline: y=mx+b: m = ' + str(round(m3, 5)) + '.')
    print('')

    print('Initial Closes first, then final, then price return, then in %-terms: ')
    print(df[[etfs[1]+'-Close', 
              etfs[0]+'-Close']].iloc[0])
    print(df[[etfs[1]+'-Close', 
              etfs[0]+'-Close', 
              etfs[1]+'-PriceReturn', 
              etfs[0]+'-PriceReturn', 
              etfs[1]+'-PR_pct_change', 
              etfs[0]+'-PR_pct_change']].iloc[-1])    
    print('...')

    #Graph info
    plt.title('Price % Return Comparison of ' + etfs[1] + ' against ' + etfs[0])
    plt.xlabel('Date')
    plt.ylabel('Percentage Gains in Price')
    plt.legend()
    # plt.ioff()
    plt.grid(True)
    # plt.show()

def TRGraph():
    # plt.figure(figsize=(10,5))
    plt.subplot(2,2,2)

    x_num = np.arange(len(df))
    m1, b1 = np.polyfit(x_num, df[etfs[0] + '-TR_pct_change'], 1)
    m2, b2 = np.polyfit(x_num, df[etfs[1] + '-TR_pct_change'], 1) 

    #comparisons and trendlines
    plt.plot(df['Date'], df[etfs[0] + '-TR_pct_change'], label=etfs[0] + ' TR', color='blue', alpha=1)
    plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label=etfs[0] + ' TR Trend', color='blue', alpha=0.9)

    plt.plot(df['Date'], df[etfs[1] + '-TR_pct_change'], label=etfs[1] + ' TR', color='red', alpha=1)
    plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label=etfs[1] + ' TR Trend', color='red', alpha=0.9)
    #orig
    # plt.plot(df['Date'], df['TRNorm_compare'], label='TR', color='red', alpha=1)
    # plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='TR_Trend', color='red', alpha=0.9)

    print('...')
    print('Total Return Stats: ')
    print('Percentage of T-TR beating the Underlying: ' + str(TRpercentOverOne) + '%')
    print('')
    print('Total Return Correlation: ' + str(TR_Correlation))
    print('')
    print('Underlying TR trendline: y=mx+b: m = ' + str(round(m1, 5)) + '.')
    print('Target TR trendline: y=mx+b: m = ' + str(round(m2, 5)) + '.')
    print('')
    print('Measuring Target TR - Underlying TR, the percentage difference between them: ')
    print('Mean difference in TR\'s: ' + str(averageTRdiff) + '%')
    print('Median difference in TR\'s: ' + str(medianTRdiff) + '%')
    print('')
    print(df[[  etfs[1]+'-TRActual', 
                etfs[0]+'-TRActual',
                etfs[1]+'-TR_pct_change', 
                etfs[0]+'-TR_pct_change'
                ]].iloc[-1])   #'TRNorm_compare'  'Date', etfs[1]+'-Close', etfs[1] + '-TRScuffed', etfs[0]+'-Close', etfs[0] + '-TRScuffed',
    print('...')

    #Graph info
    plt.title('Total Return Comparison of ' + etfs[1] + ' against ' + etfs[0])
    plt.xlabel('Date')
    plt.ylabel('Total Return %')
    plt.legend()
    # plt.ioff()
    plt.grid(True)
    # plt.show()

def priceRelationshipGraph():
    # plt.figure(figsize=(10,5))
    plt.subplot(2,2,3)

    x_num = np.arange(len(df))
    m1, b1 = np.polyfit(x_num, df['CloseNorm_compare'], 1)

    #comparisons and trendlines
    plt.plot(df['Date'], df['CloseNorm_compare'], label='Price Ratio', color='green', alpha=1)
    plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PR-Trend', color='green', alpha=0.9)

    print('...')
    print('Price Ratio Stats: ')
    print('Average Price Ratio: ' + str(round(df['CloseNorm_compare'].mean(), 5)))
    print('Percentage of Target Price beating the Underlying: ' + str(percentOverOne) + '%')
    print('Price Ratio %-Change, AVG: ' +  str(df['PriceGrowthRate'].mean() * 100))
    print('')
    print('Price Correlation: ' + str(Price_Correlation))
    print('')
    print('Price trendline, y=mx+b: m = ' + str(round(m1,5)) + '.')
    print('...')

    #Graph info
    plt.title('Price Action, Normalized, for ' + etfs[1] + ' / ' + etfs[0])
    plt.xlabel('Date')
    plt.ylabel('Normalized Price Relation Ratio')
    plt.legend()
    # plt.ioff()
    plt.grid(True)
    # plt.show()

def dividendsGraph():
    # plt.figure(figsize=(10,5))
    plt.subplot(2,2,4)
    underlying_divs =  round(df[etfs[0] + '-DivsSummed'].iloc[-1], 2)
    target_divs =  round(df[etfs[1] + '-DivsSummed'].iloc[-1], 2)
    labels = [str(etfs[0]), str(etfs[1])]
    values = [underlying_divs, target_divs]
    # plt.bar(labels, values, color=['blue','red'])

    plt.bar(labels[0], values[0], label=str(etfs[0]) + ' Total: ' + '$' + str(values[0]), color='blue')
    plt.bar(labels[1], values[1], label=str(etfs[1]) + ' Total: ' + '$' + str(values[1]), color='red')

    # x_num = np.arange(len(df))
    # m1, b1 = np.polyfit(x_num, df['AdjNorm_compare'], 1)
    # m1, b1 = np.polyfit(x_num, df['CloseNorm_compare'], 1)
    # m2, b2 = np.polyfit(x_num, df[etfs[0] + '-PR_pct_change'], 1) #price of underlying
    # m3, b3 = np.polyfit(x_num, df[etfs[1] + '-PR_pct_change'], 1) #price of target

    #comparisons and trendlines
    # plt.plot(df['Date'], df['CloseNorm_compare'], label='Price Ratio', color='green', alpha=1)
    # plt.plot(df['Date'], m1 * x_num + b1, linestyle="dashed", label='PR-Trend', color='green', alpha=0.9)

    # plt.plot(df['Date'], df[etfs[0] + '-PR_pct_change'], label='Underlying Price', color='blue', alpha=1)
    # plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='U-Price Trend', color='blue', alpha=0.9)

    # plt.plot(df['Date'], df[etfs[1] + '-PR_pct_change'], label='Target Price', color='red', alpha=1)
    # plt.plot(df['Date'], m3 * x_num + b3, linestyle="dashed", label='T-Price Trend', color='red', alpha=0.9)

    # plt.plot(df['Date'], df['TRNorm_compare'], label='TR', color='red', alpha=1)
    # plt.plot(df['Date'], m2 * x_num + b2, linestyle="dashed", label='TR_Trend', color='red', alpha=0.9)


    # print('...')
    # print('Price Ratio Stats: ')
    # print('Average Price Ratio: ' + str(round(df['CloseNorm_compare'].mean(), 5)))
    # print('Percentage of Target Price beating the Underlying: ' + str(percentOverOne) + '%')
    # print('Price Ratio %-Change, AVG: ' +  str(df['PriceGrowthRate'].mean() * 100))
    # print('')
    # print('Price Return Correlation: ' + str(Price_Correlation))
    # print('')
    # print('Price trendline: y= ' + str(m1) + ' * x + ' + str(b1))
    # print('...')


    # print('Average compare, Price: ' + str(df['CloseNorm_compare'].mean()))
    # print('Percentage of Price beating the underlying: ' + str(percentOverOne) + '%')
    # print('Price Ratio Change AVG: ' +  str(df['PriceGrowthRate'].mean() * 100))
    # print('My Price Ratio Change AVG: ' +  str(df['MYPriceGrowthRate'].mean() * 100))


    # df['Price_Correlation'] = df[etfs[1] + '-PR_pct_change'].corr(df[etfs[0] + '-PR_pct_change'])



    # print(df[[etfs[1]+'-Close', 
    #             etfs[0]+'-Close']].iloc[0] )
    # print(df[[etfs[1]+'-Close', 
    #             etfs[0]+'-Close', 
    # etfs[1]+'-PriceReturn', 
    #         etfs[0]+'-PriceReturn', 
    #         etfs[1]+'-PR_pct_change', 
    #         etfs[0]+'-PR_pct_change']].iloc[-1])

    # print('...')
    # print('Price trendline: y= ' + str(m1) + ' * x + ' + str(b1))
    # print('...')
    # print('TR trendline: y= ' + str(m2) + ' * x + ' + str(b2))

    # print(df[[  etfs[1]+'-Close', 
    #             etfs[0]+'-Close',
    #             etfs[1]+'-TRActual', 
    #             etfs[0]+'-TRActual'
    #             ]].iloc[2]) 


    # #prices
    # plt.plot(df['Date'], df[etfs[1] + '-Close'] / 100, label='Test Price', color='green', alpha=0.9)
    # plt.plot(df['Date'], df[etfs[0] + '-Close'] / 3000, label='Target Price', color='orange', alpha=0.9)

    #Graph info
    plt.title('Total Distributions for both ' + etfs[1] + ' vs ' + etfs[0])
    plt.xlabel('Two Funds Being Compared')
    plt.ylabel('Total Distributions in $')
    plt.legend()
    # plt.ioff()
    plt.grid(True)
    # plt.show()

    #Alternate labels on top of bars
    # for i, value in enumerate(values):
    #     plt.text(i, value - 2, '$' + str(round(value,2)), ha='center', va='bottom', fontsize=12, color='black')


plt.figure(figsize=(18,9))

priceGraph()
TRGraph()
priceRelationshipGraph()
dividendsGraph()

plt.tight_layout()
plt.show()


# plt.savefig('justagraph3.png')
# Display DataFrame 
# print(etfs)
# print(etfs[1])
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn', 'TRNorm_compare']].tail(200).to_string())
# print(df[['Date', etfs[0] + '-TotalReturn', etfs[1] + '-TotalReturn',  'AdjNorm_compare', 'TRNorm_compare']].to_string()) #etfs[0] + '-Divs', etfs[1] + '-Divs',
# print(df.to_string())