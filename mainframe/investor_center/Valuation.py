import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
# import datetime as dt #leaving only because I'm not sure which I used.
from datetime import date 
import time
import json
import requests
import math
import yfinance as yf
import statistics as stats
from collections import Counter as counter
import sqlite3 as sql
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) #infer_objects(copy=False) works nonreliably. SO WE JUST SQUELCH IT ALTOGETHER!
from currency_converter import CurrencyConverter #https://pypi.org/project/CurrencyConverter/
converter_address = '/home/family/Documents/repos/MainFrame/mainframe/investor_center/currency-hist.csv' 
curConvert = CurrencyConverter(converter_address, fallback_on_missing_rate=True)
### Documentation: https://pypi.org/project/CurrencyConverter/ 

#From fellow files
import csv_modules as csv
import Mega as mega
import Metadata as metadata
# import SectorRankings as sr #luke clean up imports
# import AltTables as at

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}

db_path = '/home/family/Documents/repos/MainFrame/mainframe/stock_data.sqlite3'

def print_DB(thequery, superflag):
    conn = sql.connect(db_path)
    query = conn.cursor()
    # del_query = 'SELECT DISTINCT Ticker FROM Mega;'
    # query.execute(del_query)
    # conn.commit()
    
    df12 = pd.read_sql(thequery,conn)
    query.close()
    conn.close()

    if superflag == 'print':
        print(df12)
    elif superflag == 'return':
        return df12

def uploadToDB(upload,table):
    #https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html 
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        upload.to_sql(table, conn, if_exists='append', index=False)
    except Exception as err:
        print("upload to DB error: ")
        print(err)
    finally:
        query.close()
        conn.close()

#luke to do
# Clean code: below
# test pd, test growth valuation, add features you want
# see about flow of all this. maybe adding some of these things all the way back in mega?
#you can use stocks in the etf ones, but the numbers are then wrong.

def PD(listofstocktickers):
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        tupleforsql = tuple(listofstocktickers)
        metafacts = 'SELECT Ticker, Sector, cast(AveragedOverYears as integer) as years, \
                        CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                        priceGrowthAVG as pgr \
                    FROM Metadata \
                    WHERE Ticker IN ' + str(tupleforsql) + ';'
        metadata = print_DB(metafacts, 'return')
        for x in metadata['Ticker']:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                sector = metadata.loc[metadata['Ticker'] == x, 'Sector'].iloc[0]
                price = dict1['previousClose']
                pricegr = metadata.loc[metadata['Ticker'] == x, 'pgr'].iloc[0]
                divrate = dict1['dividendRate']
                divgr = metadata.loc[metadata['Ticker'] == x, 'divgr'].iloc[0]
                tenYearPrice = price * ((1 + (pricegr/100)) ** 10)
                tenYearDiv = divrate * ((1 + (divgr/100)) ** 10)
                twentyYearPrice = price * ((1 + (pricegr/100)) ** 20)
                twentyYearDiv = divrate * ((1 + (divgr/100)) ** 20)
                toupload['Ticker'] = [x]
                toupload['Sector'] = sector
                toupload['currentPrice'] = price
                toupload['currentDiv'] = divrate
                toupload['currentYield'] = divrate / price
                toupload['currentValuation'] = price / divrate
                toupload['idealPriceCeiling'] = 25 * divrate
                toupload['priceGR'] = pricegr
                toupload['divGR'] = divgr
                toupload['tenYearPrice'] = tenYearPrice
                toupload['tenYearDiv'] = tenYearDiv
                toupload['tenYearValuation'] = tenYearPrice / tenYearDiv
                toupload['tenYearFlatValuation'] = price / tenYearDiv
                toupload['twentyYearPrice'] = twentyYearPrice
                toupload['twentyYearDiv'] = twentyYearDiv
                toupload['twentyYearValuation'] = twentyYearPrice / twentyYearDiv
                toupload['twentyYearFlatValuation'] = price / twentyYearDiv

                toreturn = pd.concat([toreturn, toupload], ignore_index = True)

            except Exception as err:
                print('PD evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('evaulate err')
        print(err)
    finally:
        return toreturn.sort_values("currentValuation")

def DDM(listofstocktickers):
    #Takes tickers to analyze, returns a 5%-50% price target, return rate fair value
    #if numbers are negative or higher than current price, buy for that return percentage
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        tupleforsql = tuple(listofstocktickers)
        metafacts = 'SELECT Ticker, Sector, \
                        CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                        totalDivsPaidGrowthAVG as totaldivgr \
                    FROM Metadata \
                    WHERE Ticker IN ' + str(tupleforsql) + ';'
        metadata = print_DB(metafacts, 'return')
        for x in metadata['Ticker']:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                sector = metadata.loc[metadata['Ticker'] == x, 'Sector'].iloc[0]
                divrate = dict1['dividendRate']
                lowerTracker = 0

                divgr1 = metadata.loc[metadata['Ticker'] == x, 'divgr'].iloc[0]
                divgr2 = metadata.loc[metadata['Ticker'] == x, 'totaldivgr'].iloc[0]
                divgr = max(divgr1, divgr2) / 100
                
                divp1 = divrate * ((1 + (divgr)) ** 2)
                divp2 = divrate * ((1 + (divgr)) ** 3)
                divp3 = divrate * ((1 + (divgr)) ** 4)
                divp4 = divrate * ((1 + (divgr)) ** 5)
                divp5 = divrate * ((1 + (divgr)) ** 6)

                ror = 0.05
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['Ticker'] = [x]
                toupload['CurrentPrice'] = dict1['previousClose']
                toupload['5%TargetPrice'] = fairvalue
                
                #Also return fair price for 10% returns
                ror = 0.1
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['10%TargetPrice'] = fairvalue

                #Also return fair price for 15% returns
                ror = 0.15
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['15%TargetPrice'] = fairvalue

                #Also return fair price for 20% returns
                ror = 0.2
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['20%TargetPrice'] = fairvalue

                #Also return fair price for 30% returns
                ror = 0.3
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['30%TargetPrice'] = fairvalue

                #Also return fair price for 40% returns
                ror = 0.4
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['40%TargetPrice'] = fairvalue

                #Also return fair price for 50% returns
                ror = 0.5
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['50%TargetPrice'] = fairvalue

                if toupload['5%TargetPrice'][0] < 0:
                    lowerTracker = 5
                elif toupload['5%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 5
                    
                if toupload['10%TargetPrice'][0] < 0:
                    lowerTracker = 10
                elif toupload['10%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 10

                if toupload['15%TargetPrice'][0] < 0:
                    lowerTracker = 15
                elif toupload['15%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 15

                if toupload['20%TargetPrice'][0] < 0:
                    lowerTracker = 20
                elif toupload['20%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 20

                if toupload['30%TargetPrice'][0] < 0:
                    lowerTracker = 30
                elif toupload['30%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 30

                if toupload['40%TargetPrice'][0] < 0:
                    lowerTracker = 40
                elif toupload['40%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 40

                if toupload['50%TargetPrice'][0] < 0:
                    lowerTracker = 50
                elif toupload['50%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 50
                
                toupload['ExpectedMinReturnAtThisPrice'] = lowerTracker

                toreturn = pd.concat([toreturn, toupload], ignore_index = True)
            except Exception as err:
                print('DDM evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('DDM evaulate err')
        print(err)
    finally:
        return toreturn.sort_values("ExpectedMinReturnAtThisPrice")

def ETFPD(listofstocktickers):
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        for x in listofstocktickers:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                divs = stock.dividends
                growthList = []

                toupload['Ticker'] = [x]

                for i in range(len(divs) - 1):
                    diff = abs((divs[i+1])-divs[i])
                    if divs[i] > divs[i+1]:
                        diff = diff * -1
                    if abs(divs[i]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[i])
                    growthList.append(change)
                try:
                    divrate =  dict1['navPrice'] * dict1['yield']
                except:
                    divrate = divs[-1] * 12

                price = dict1['previousClose']
                
                time1 = (len(divs)/4)
                cagr = ((divs[-1]/divs[0]) ** (1/time1)) - 1
                iqrMean = metadata.IQR_Mean(growthList)
                divgr = (cagr + iqrMean) / 2

                tenYearDiv = divrate * ((1 + (divgr)) ** 10)
                twentyYearDiv = divrate * ((1 + (divgr)) ** 20)
                toupload['currentPrice'] = price
                toupload['currentDiv'] = divrate
                toupload['currentYield'] = divrate / price
                toupload['currentValuation'] = price / divrate
                toupload['idealPriceCeiling'] = 25 * divrate
                toupload['divGR'] = divgr * 100
                toupload['tenYearDiv'] = tenYearDiv
                toupload['tenYearFlatValuation'] = price / tenYearDiv
                toupload['twentyYearDiv'] = twentyYearDiv
                toupload['twentyYearFlatValuation'] = price / twentyYearDiv
                
                toreturn = pd.concat([toreturn, toupload], ignore_index = True)

            except Exception as err:
                print('PD evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('etf pd err')
        print(err)
    finally:
        return toreturn.sort_values("currentValuation")

def ETFDDM(listofstocktickers):
    #Takes tickers to analyze, returns a 5%-50% price target, return rate fair value
    #if numbers are negative or higher than current price, buy for that return percentage
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        
        for x in listofstocktickers:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                divs = stock.dividends
                growthList = []
                lowerTracker = 0
                toupload['Ticker'] = [x]
                
                for i in range(len(divs) - 1):
                    diff = abs((divs[i+1])-divs[i])
                    if divs[i] > divs[i+1]:
                        diff = diff * -1
                    if abs(divs[i]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[i])
                    growthList.append(change)
                try:
                    divrate =  dict1['navPrice'] * dict1['yield']
                except:
                    divrate = divs[-1] * 12
                
                time1 = (len(divs)/4)
                cagr = ((divs[-1]/divs[0]) ** (1/time1)) - 1
                iqrMean = metadata.IQR_Mean(growthList)
                divgr = (cagr + iqrMean) / 2
                
                divp1 = divrate * ((1 + (divgr)) ** 2)
                divp2 = divrate * ((1 + (divgr)) ** 3)
                divp3 = divrate * ((1 + (divgr)) ** 4)
                divp4 = divrate * ((1 + (divgr)) ** 5)
                divp5 = divrate * ((1 + (divgr)) ** 6)

                ror = 0.05
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['CurrentPrice'] = dict1['previousClose']
                toupload['5%TargetPrice'] = fairvalue
                
                #Also return fair price for 10% returns
                ror = 0.1
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['10%TargetPrice'] = fairvalue

                #Also return fair price for 15% returns
                ror = 0.15
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['15%TargetPrice'] = fairvalue

                #Also return fair price for 20% returns
                ror = 0.2
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['20%TargetPrice'] = fairvalue

                #Also return fair price for 30% returns
                ror = 0.3
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['30%TargetPrice'] = fairvalue

                #Also return fair price for 40% returns
                ror = 0.4
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['40%TargetPrice'] = fairvalue

                #Also return fair price for 50% returns
                ror = 0.5
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['50%TargetPrice'] = fairvalue

                if toupload['5%TargetPrice'][0] < 0:
                    lowerTracker = 5
                elif toupload['5%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 5
                    
                if toupload['10%TargetPrice'][0] < 0:
                    lowerTracker = 10
                elif toupload['10%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 10

                if toupload['15%TargetPrice'][0] < 0:
                    lowerTracker = 15
                elif toupload['15%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 15

                if toupload['20%TargetPrice'][0] < 0:
                    lowerTracker = 20
                elif toupload['20%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 20

                if toupload['30%TargetPrice'][0] < 0:
                    lowerTracker = 30
                elif toupload['30%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 30

                if toupload['40%TargetPrice'][0] < 0:
                    lowerTracker = 40
                elif toupload['40%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 40

                if toupload['50%TargetPrice'][0] < 0:
                    lowerTracker = 50
                elif toupload['50%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 50
                
                toupload['ExpectedMinReturnAtThisPrice'] = lowerTracker
                toreturn = pd.concat([toreturn, toupload], ignore_index = True)
            except Exception as err:
                print('DDM etf evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('DDM etf evaulate err')
        print(err)
    finally:
        return toreturn.sort_values("ExpectedMinReturnAtThisPrice")

# print(ETFDDM(['SCHD','DGRO','SOXQ','VIG','AMZY']))
# print(ETFPD(['SCHD','DGRO','SOXQ','VIG','AMZY']))

def weeklyETFPD(listofstocktickers):
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        for x in listofstocktickers:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                divs = stock.dividends
                growthList = []

                # print(divs)

                toupload['Ticker'] = [x]

                for i in range(len(divs) - 1):
                    diff = abs((divs[i+1])-divs[i])
                    if divs[i] > divs[i+1]:
                        diff = diff * -1
                    if abs(divs[i]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[i])
                    growthList.append(change)
                try:
                    divrate =  dict1['navPrice'] * dict1['yield']
                except:
                    divrate = divs[-1] * 52

                price = dict1['previousClose']
                
                time1 = (len(divs)/4)
                cagr = ((divs[-1]/divs[0]) ** (1/time1)) - 1
                iqrMean = metadata.IQR_Mean(growthList)
                divgr = (cagr + iqrMean) / 2

                tenYearDiv = divrate * ((1 + (divgr)) ** 10)
                twentyYearDiv = divrate * ((1 + (divgr)) ** 20)
                toupload['currentPrice'] = price
                toupload['currentDiv'] = divrate
                toupload['currentYield'] = divrate / price * 100
                toupload['currentValuation'] = price / divrate
                toupload['idealPriceCeiling'] = 25 * divrate
                toupload['divGR'] = divgr * 100
                toupload['tenYearDiv'] = tenYearDiv
                toupload['tenYearFlatValuation'] = price / tenYearDiv
                toupload['twentyYearDiv'] = twentyYearDiv
                toupload['twentyYearFlatValuation'] = price / twentyYearDiv
                
                toreturn = pd.concat([toreturn, toupload], ignore_index = True)

            except Exception as err:
                print('PD evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('etf pd err')
        print(err)
    finally:
        return toreturn.sort_values("currentValuation")

def weeklyETFDDM(listofstocktickers):
    #Takes tickers to analyze, returns a 5%-50% price target, return rate fair value
    #if numbers are negative or higher than current price, buy for that return percentage
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        
        for x in listofstocktickers:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                divs = stock.dividends
                growthList = []
                lowerTracker = 0
                toupload['Ticker'] = [x]
                
                for x in range(len(divs) - 1):
                    diff = abs((divs[x+1])-divs[x])
                    if divs[x] > divs[x+1]:
                        diff = diff * -1
                    if abs(divs[x]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[x])
                    growthList.append(change)
                try:
                    divrate =  dict1['navPrice'] * dict1['yield']
                except:
                    divrate = divs[-1] * 52
                
                time1 = (len(divs)/4)
                cagr = ((divs[-1]/divs[0]) ** (1/time1)) - 1
                iqrMean = metadata.IQR_Mean(growthList)
                divgr = (cagr + iqrMean) / 2
                
                divp1 = divrate * ((1 + (divgr)) ** 2)
                divp2 = divrate * ((1 + (divgr)) ** 3)
                divp3 = divrate * ((1 + (divgr)) ** 4)
                divp4 = divrate * ((1 + (divgr)) ** 5)
                divp5 = divrate * ((1 + (divgr)) ** 6)

                ror = 0.05
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                # toupload['Ticker'] = [x]
                toupload['CurrentPrice'] = dict1['previousClose']
                toupload['5%TargetPrice'] = fairvalue
                
                #Also return fair price for 10% returns
                ror = 0.1
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['10%TargetPrice'] = fairvalue

                #Also return fair price for 15% returns
                ror = 0.15
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['15%TargetPrice'] = fairvalue

                #Also return fair price for 20% returns
                ror = 0.2
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['20%TargetPrice'] = fairvalue

                #Also return fair price for 30% returns
                ror = 0.3
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['30%TargetPrice'] = fairvalue

                #Also return fair price for 40% returns
                ror = 0.4
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['40%TargetPrice'] = fairvalue

                #Also return fair price for 50% returns
                ror = 0.5
                pvd1 = divp1 / ((1 + ror) ** 1)
                pvd2 = divp2 / ((1 + ror) ** 2)
                pvd3 = divp3 / ((1 + ror) ** 3)
                pvd4 = divp4 / ((1 + ror) ** 4)
                pvd5 = divp5 / ((1 + ror) ** 5)
                tvd5 = divp5 * ((1 + divgr) / (ror - divgr))
                updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5
                toupload['50%TargetPrice'] = fairvalue

                if toupload['5%TargetPrice'][0] < 0:
                    lowerTracker = 5
                elif toupload['5%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 5
                    
                if toupload['10%TargetPrice'][0] < 0:
                    lowerTracker = 10
                elif toupload['10%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 10

                if toupload['15%TargetPrice'][0] < 0:
                    lowerTracker = 15
                elif toupload['15%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 15

                if toupload['20%TargetPrice'][0] < 0:
                    lowerTracker = 20
                elif toupload['20%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 20

                if toupload['30%TargetPrice'][0] < 0:
                    lowerTracker = 30
                elif toupload['30%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 30

                if toupload['40%TargetPrice'][0] < 0:
                    lowerTracker = 40
                elif toupload['40%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 40

                if toupload['50%TargetPrice'][0] < 0:
                    lowerTracker = 50
                elif toupload['50%TargetPrice'][0] > dict1['previousClose']:
                    lowerTracker = 50
                
                toupload['ExpectedMinReturnAtThisPrice'] = lowerTracker

                toreturn = pd.concat([toreturn, toupload], ignore_index = True)
            except Exception as err:
                print('DDM etf evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('DDM etf evaulate err')
        print(err)
    finally:
        return toreturn.sort_values("ExpectedMinReturnAtThisPrice")

# print(weeklyETFDDM(['XDTE','QDTE']))

def growthValuation(listofstocktickers):
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        tupleforsql = tuple(listofstocktickers)
        metafacts = 'SELECT Ticker, Sector, year, revenue \
                    FROM Mega \
                    WHERE Ticker IN ' + str(tupleforsql) + ' ORDER BY year;'
        metadata = print_DB(metafacts, 'return')
        for x in listofstocktickers:
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                sector = metadata.loc[metadata['Ticker'] == x, 'Sector'].iloc[0]
                # price = dict1['previousClose']
                # pricegr = metadata.loc[metadata['Ticker'] == x, 'pgr'].iloc[0]
                marketcap = dict1['marketCap']
                revenue = metadata.loc[metadata['Ticker'] == x, 'revenue'].iloc[-1]
                valuationratio = marketcap / revenue
                # divrate = dict1['dividendRate']
                # divgr = metadata.loc[metadata['Ticker'] == x, 'divgr'].iloc[0]
                # tenYearPrice = price * ((1 + (pricegr/100)) ** 10)
                # tenYearDiv = divrate * ((1 + (divgr/100)) ** 10)
                # twentyYearPrice = price * ((1 + (pricegr/100)) ** 20)
                # twentyYearDiv = divrate * ((1 + (divgr/100)) ** 20)
                toupload['Ticker'] = [x]
                toupload['Sector'] = sector
                toupload['lastRevenue'] = revenue
                toupload['marketCap'] = marketcap
                toupload['valuation'] = valuationratio
                

                # toupload['currentValuation'] = price / divrate
                # toupload['idealPriceCeiling'] = 25 * divrate
                # toupload['priceGR'] = pricegr
                # toupload['divGR'] = divgr
                # toupload['tenYearPrice'] = tenYearPrice
                # toupload['tenYearDiv'] = tenYearDiv
                # toupload['tenYearValuation'] = tenYearPrice / tenYearDiv
                # toupload['tenYearFlatValuation'] = price / tenYearDiv
                # toupload['twentyYearPrice'] = twentyYearPrice
                # toupload['twentyYearDiv'] = twentyYearDiv
                # toupload['twentyYearValuation'] = twentyYearPrice / twentyYearDiv
                # toupload['twentyYearFlatValuation'] = price / twentyYearDiv

                toreturn = pd.concat([toreturn, toupload], ignore_index = True)

            except Exception as err:
                print('growth evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('growth evaulate err')
        print(err)
    finally:
        return toreturn.sort_values(["Sector","valuation"])


divetfs = ['SPYD', 'SMDV', 'SDY', 'HDV', 'GCOW', 'DVY', 'DTD', 'DON', 'DLN', 'DIVB', 
            'DHS', 'DGRW', 'DGRS', 'DEW', 'DES', 'DGRO', 'DIVO', 'SCHD', 'VIG' ]
hyetfs = [ 'MSFO', 'AMZY', 'CONY', 'APLY', 'GOOY', 'FBY', 'NVDY', 'TSLY', 'FEPI', 'YMAX', 
            'YMAG', 'MSTY', 'YBIT', 'SVOL', 'QQQI', 'IWMI', 'SPYI', 'JEPI', 'JEPQ', 'GPIQ', 
            'GPIX',  'CRSH', 'FIAT', 'DIPS']
weeklyetfs = ['XDTE', 'QDTE',]
stocks = ['UFPI', 'RS', 'STLD', 'NUE', 'VZ', 'T', 'CVX', 'XOM', 'ARCC', 'MAIN', 
            'HTGC', 'TSLX', 'CSWC', 'JPM', 'GS', 'MS', 'V', 'MA', 'DFS', 'FAST', 
            'PH', 'ETN', 'RSG', 'WM', 'CAT', 'GD', 'WSO', 'FIX', 'CTAS', 'LMT', 
            'TXN', 'ADI', 'MCHP', 'MSFT', 'AAPL', 'CSCO', 'IBM', 'NVDA', 'PLTR', 
            'SMCI', 'COST', 'WMT', 'PG', 'KR', 'KVUE', 'O', 'NNN', 'ADC', 'PLD', 
            'STAG', 'REXR', 'TRNO', 'FR', 'AMT', 'SBAC', 'CCI', 'DLR', 'EQIX', 
            'WY', 'NSA', 'NEE', 'CEG', 'SO', 'AWK', 'CPK', 'ATO', 'UNH', 'MCK', 
            'JNJ', 'ABBV', 'HD', 'TSCO', 'MCD', 'F', 'YUM']
sectoretfs = ['XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'SCHH', 'XLU', 
                'XLV', 'XLY', 'PBDC', 'SOXQ']

# print(growthValuation(stocks).to_string())

# print(ETFPD(divetfs))
#     Ticker  currentPrice  currentDiv  currentYield  currentValuation  idealPriceCeiling      divGR  tenYearDiv  tenYearFlatValuation  twentyYearDiv  twentyYearFlatValuation
# 4    GCOW       35.1500    2.224250      0.063279         15.803083          55.606238   8.493262    5.025869              6.993816      11.356351                 3.095184
# 16   DIVO       39.5200    1.813421      0.045886         21.793062          45.335530   0.905686    1.984518             19.914153       2.171758                18.197237
# 0    SPYD       43.1300    1.966642      0.045598         21.930781          49.166057   1.764241    2.342488             18.412049       2.790161                15.457887
# 13    DEW       52.7186    2.305435      0.043731         22.867099          57.635864  -5.996531    1.242200             42.439695       0.669315                78.765031
# 10    DHS       91.1900    3.692505      0.040492         24.695973          92.312622  -2.341135    2.913653             31.297482       2.299082                39.663649
# 5     DVY      130.1000    4.930176      0.037895         26.388512         123.254391   3.712068    7.098316             18.328291      10.219938                12.730018
# 17   SCHD       82.5800    3.007732      0.036422         27.455904          75.193300  10.346286    8.050379             10.257902      21.547332                 3.832493
# 3     HDV      114.8300    4.029442      0.035090         28.497743         100.736047   4.991795    6.558409             17.508820      10.674611                10.757300
# 1    SMDV       70.9300    2.173640      0.030645         32.631901          54.340995  14.239105    8.228781              8.619746      31.151817                 2.276914
# 14    DES       34.9200    1.007090      0.028840         34.674164          25.177247  -6.566167    0.510634             68.385553       0.258912               134.872289
# 9    DIVB       46.7000    1.330566      0.028492         35.097838          33.264157   8.715010    3.068539             15.218971       7.076633                 6.599183
# 2     SDY      134.8300    3.547705      0.026312         38.004850          88.692628   6.778793    6.835930             19.723725      13.171877                10.236202
# 7     DON       50.1100    1.228123      0.024509         40.802108          30.703071  -1.765181    1.027771             48.756005       0.860104                58.260421
# 15   DGRO       60.3000    1.422637      0.023593         42.386077          35.565924   1.410456    1.636521             36.846468       1.882560                32.030852
# 12   DGRS       52.3800    1.198415      0.022879         43.707741          29.960368  -1.732838    1.006216             52.056413       0.844842                61.999775
# 6     DTD       73.7445    1.658617      0.022491         44.461453          41.465413  -1.496916    1.426410             51.699385       1.226712                60.115589
# 8     DLN       75.2200    1.647091      0.021897         45.668390          41.177278  -1.724653    1.384087             54.346283       1.163079                64.673146
# 18    VIG      189.7900    3.493056      0.018405         54.333512          87.326400   8.004499    7.544388             25.156449      16.294553                11.647451
# 11   DGRW       79.7500    1.283860      0.016099         62.117347          32.096509   2.359795    1.621108             49.194757       2.046944                38.960519

# print(ETFPD(hyetfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]
# print(weeklyETFPD(weeklyetfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]

#     Ticker  currentPrice  currentDiv  currentYield  currentValuation  idealPriceCeiling      divGR  tenYearDiv  tenYearFlatValuation  twentyYearDiv  twentyYearFlatValuation
# 2    CONY       18.4500   18.876000      1.023089          0.977432         471.900000   1.392943   21.676406              0.851156      24.892274                 0.741194
# 13   MSTY       29.4800   27.984000      0.949254          1.053459         699.600000 -37.237642    0.265401            111.077265       0.002517             11712.043358
# 14   YBIT       16.2800   14.592000      0.896314          1.115680         364.800000 -16.319340    2.456777              6.626567       0.413635                39.358416
# 7    TSLY       15.8500   12.992831      0.819737          1.219903         324.820780  -8.719049    5.218015              3.037553       2.095593                 7.563492
# 23   CRSH       14.8300    9.780000      0.659474          1.516360         244.500000 -20.793888    0.950442             15.603259       0.092366               160.556675
# 6    NVDY       26.6500   14.100172      0.529087          1.890048         352.504307  23.020175  111.940652              0.238073     888.691947                 0.029988
# 5     FBY       17.7200    8.436000      0.476072          2.100522         210.900000  23.918433   72.027063              0.246019     614.971283                 0.028814
# 1    AMZY       20.9800    9.180000      0.437560          2.285403         229.500000   7.502074   18.923920              1.108650      39.010322                 0.537806
# 0    QDTE       43.2414      18.408      0.425703          2.349055              460.2  4.570562   28.780678              1.502445      44.998232                 0.960958
# 11   YMAX       18.8200    7.824000      0.415728          2.405419         195.600000  11.266189   22.754168              0.827101      66.174869                 0.284398
# 12   YMAG       19.6900    7.644000      0.388217          2.575877         191.100000  17.168963   37.277479              0.528201     181.791005                 0.108311
# 4    GOOY       16.6600    5.616000      0.337095          2.966524         140.400000   5.960318   10.019813              1.662706      17.876898                 0.931929
# 3    APLY       18.0400    4.811831      0.266731          3.749092         120.295780   2.881494    6.392681              2.821977       8.492892                 2.124129
# 10   FEPI       51.8700   13.068000      0.251938          3.969238         326.700000  -0.953580   11.873997              4.368369      10.789088                 4.807635
# 1    XDTE       51.8289      12.532      0.241796          4.135725              313.3  0.878369   13.677317              3.789406      14.927305                 3.472087
# 0    MSFO       20.3500    4.620000      0.227027          4.404762         115.500000   5.761147    8.089161              2.515712      14.163319                 1.436810
# 15   SVOL       22.3200    3.576485      0.160237          6.240763          89.412137   1.363475    4.095165              5.450330       4.689066                 4.760010
# 16   QQQI       50.4700    7.428000      0.147177          6.794561         185.700000   1.866777    8.937119              5.647234      10.752840                 4.693644
# 17   IWMI       52.1398    7.224000      0.138551          7.217580         180.600000  16.234997   32.519722              1.603329     146.391519                 0.356167
# 18   SPYI       50.2200    5.897619      0.117436          8.515301         147.440469   1.204566    6.647797              7.554382       7.493398                 6.701899
# 21   GPIQ       46.8800    5.040000      0.107509          9.301587         126.000000   4.280728    7.664275              6.116691      11.654983                 4.022314
# 20   JEPQ       53.2932    4.709569      0.088371         11.315940         117.739223   1.716930    5.583591              9.544610       6.619818                 8.050553
# 22   GPIX       47.7200    4.032000      0.084493         11.835317         100.800000   3.915873    5.920242              8.060482       8.692773                 5.489617
# 19   JEPI       57.1905    4.217351      0.073742         13.560763         105.433779   0.594500    4.474887             12.780322       4.748150                12.044796

# print(PD(stocks)[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']].to_string())

# print(ETFDDM(sectoretfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]
# print(ETFDDM(divetfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]
# print(ETFDDM(hyetfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]
# print(weeklyETFDDM(weeklyetfs))[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]
# print(DDM(stocks).to_string())[['Ticker','currentPrice','currentValuation', 'idealPriceCeiling','tenYearFlatValuation']]

## ETF NOTES FROM YAHOO
# {'phone': '1-800-435-4000', 
# 'longBusinessSummary': 'To pursue its goal, the fund generally invests in stocks that are included in the index. \
# The index is designed to measure the performance of high dividend yielding stocks issued by U.S. companies that have a record of \
# consistently paying dividends, selected for fundamental strength relative to their peers, based on financial ratios. \
# The fund will invest at least 90% of its net assets in these stocks.', 
# 'maxAge': 86400, 'priceHint': 2, 
# 'previousClose': 81.61, 
# 'open': 81.64, 'dayLow': 80.85, 
# 'dayHigh': 81.8599, 'regularMarketPreviousClose': 81.61, 'regularMarketOpen': 81.64, 'regularMarketDayLow': 80.85, 'regularMarketDayHigh': 81.8599, 
# 'trailingPE': 15.385382, 'volume': 2232073, 'regularMarketVolume': 2232073, 
# 'averageVolume': 2826832, 'averageVolume10days': 3089350, 'averageDailyVolume10Day': 3089350, 
# 'bid': 81.06, 'ask': 81.2, 'bidSize': 1100, 'askSize': 1100, 
# 'yield': 0.0364, 
# 'totalAssets': 54676262912, 'fiftyTwoWeekLow': 66.67, 'fiftyTwoWeekHigh': 82.94, 'fiftyDayAverage': 78.4938, 'twoHundredDayAverage': 75.93525, 
# 'navPrice': 81.57, 'currency': 'USD', 'category': 'Large Value', 
# 'ytdReturn': 0.101243295, 'beta3Year': 0.76, 
# 'fundFamily': 'Schwab ETFs', 'fundInceptionDate': 1319068800, 'legalType': 'Exchange Traded Fund', 
# 'threeYearAverageReturn': 0.066436, 'fiveYearAverageReturn': 0.1281362, 'exchange': 'PCX', 
# 'quoteType': 'ETF', 'symbol': 'SCHD', 'underlyingSymbol': 'SCHD', 'shortName': 'Schwab US Dividend Equity ETF', 
# 'longName': 'Schwab U.S. Dividend Equity ETF', 'firstTradeDateEpochUtc': 1319031000, 'timeZoneFullName': 'America/New_York', 
# 'timeZoneShortName': 'EDT', 'uuid': '51763995-7570-386d-806d-a25eca52c2b1', 'messageBoardId': 'finmb_141947998', 'gmtOffSetMilliseconds': -14400000, 
# 'trailingPegRatio': None}

#probably will never be used, db deprecated, might be re-added if it streamlines front end loading later
#needs massive refactoring first, though
def evaluateAndUploadPD():
    try:
        toupload = pd.DataFrame()
        metafacts = 'SELECT Ticker, Sector, cast(AveragedOverYears as integer) as years, \
                        CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                        priceGrowthAVG as pgr \
                    FROM Metadata;'
        metadata = print_DB(metafacts, 'return')
        length1 = len(metadata['Ticker'])
        n = 1
        time1 = time.time()
        for x in metadata['Ticker']:
            try:
                print(str(round(n/length1,4)*100) + '% complete!')
                stock = yf.Ticker(x)
                dict1 = stock.info
                sector = metadata.loc[metadata['Ticker'] == x, 'Sector'].iloc[0]
                price = dict1['previousClose']
                pricegr = metadata.loc[metadata['Ticker'] == x, 'pgr'].iloc[0]
                divrate = dict1['dividendRate']
                divgr = metadata.loc[metadata['Ticker'] == x, 'divgr'].iloc[0]
                tenYearPrice = price * ((1 + (pricegr/100)) ** 10)
                tenYearDiv = divrate * ((1 + (divgr/100)) ** 10)
                twentyYearPrice = price * ((1 + (pricegr/100)) ** 20)
                twentyYearDiv = divrate * ((1 + (divgr/100)) ** 20)
                toupload['Ticker'] = [x]
                toupload['Sector'] = sector
                toupload['currentPrice'] = price
                toupload['currentDiv'] = divrate
                toupload['currentValuation'] = price / divrate
                toupload['priceGR'] = pricegr
                toupload['divGR'] = divgr
                toupload['tenYearPrice'] = tenYearPrice
                toupload['tenYearDiv'] = tenYearDiv
                toupload['tenYearValuation'] = tenYearPrice / tenYearDiv
                toupload['twentyYearPrice'] = twentyYearPrice
                toupload['twentyYearDiv'] = twentyYearDiv
                toupload['twentyYearValuation'] = twentyYearPrice / twentyYearDiv
                uploadToDB(toupload,'PDValuation')

                n += 1
            except Exception as err:
                print('PD evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                n += 1
                continue
    except Exception as err:
        print('evaulate err')
        print(err)
    finally:
        time2 = time.time()
        print('time to complete:')
        print((time2-time1)/60)

# evaluateAndUploadPD()

def evaluateDCF(listofstocktickers, ror): #tricky, i'm not getting the hang of it, yet. msft fair value fcf/shares == 23. wut.
    try:
        toupload = pd.DataFrame()
        toreturn = pd.DataFrame()
        tupleforsql = tuple(listofstocktickers)
        metafacts = 'SELECT Ticker, Sector, cast(AveragedOverYears as integer) as years, \
                        fcfGrowthAVG as fcfgr, \
                        priceGrowthAVG as pgr \
                    FROM Metadata \
                    WHERE Ticker IN ' + str(tupleforsql) + ';'
        metadata = print_DB(metafacts, 'return')
        # length1 = len(metadata['Ticker'])
        for x in metadata['Ticker']:
            try:
                # Get latest FCF from the ticker, also FCF_1
                getfcf = 'Select year, fcf FROM Mega WHERE Ticker LIKE \'' + x + '\' ORDER BY year'
                fcf = print_DB(getfcf,'return')['fcf'].iloc[-1]
                # print(fcf)
                # print(str(round(n/length1,4)*100) + '% complete!')
                stock = yf.Ticker(x)
                dict1 = stock.info



                sector = metadata.loc[metadata['Ticker'] == x, 'Sector'].iloc[0]

                price = dict1['previousClose']
                
                pricegr = metadata.loc[metadata['Ticker'] == x, 'pgr'].iloc[0] / 100
                # print(pricegr)
                # divrate = dict1['dividendRate']
                fcfgr = metadata.loc[metadata['Ticker'] == x, 'fcfgr'].iloc[0] / 100
                # print(fcfgr)
                fiveYearPriceComparison = price * ((1 + (pricegr/100)) ** 5)
                fcfp1 = fcf * ((1 + (fcfgr/100)) ** 1)
                fcfp2 = fcf * ((1 + (fcfgr/100)) ** 2)
                fcfp3 = fcf * ((1 + (fcfgr/100)) ** 3)
                fcfp4 = fcf * ((1 + (fcfgr/100)) ** 4)
                fcfp5 = fcf * ((1 + (fcfgr/100)) ** 5)
                denom1 = (1 + ror) ** 1
                denom2 = (1 + ror) ** 2
                denom3 = (1 + ror) ** 3
                denom4 = (1 + ror) ** 4
                denom5 = (1 + ror) ** 5
                dcf = (fcfp1 / denom1) + (fcfp2 / denom2) + (fcfp3 / denom3) + (fcfp4 / denom4) + (fcfp5 / denom5)
                pvfcf1 = fcfp1 / ((1 + ror) ** 1)
                pvfcf2 = fcfp2 / ((1 + ror) ** 2)
                pvfcf3 = fcfp3 / ((1 + ror) ** 3)
                pvfcf4 = fcfp4 / ((1 + ror) ** 4)
                pvfcf5 = fcfp5 / ((1 + ror) ** 5)
                tvpvfcf5 = pvfcf5 * (1 + fcfgr) / (1 - fcfgr)
                pvpvfcf5 = (tvpvfcf5 + pvfcf5) / ((1 + ror) ** 5)
                # print(pvpvfcf5)
                fairvalue = pvfcf1+pvfcf2+pvfcf3+pvfcf4+pvpvfcf5
                sharecount = 'Select shares FROM Mega WHERE Ticker LIKE \'' + x + '\' ORDER BY year;'
                finalshares = print_DB(sharecount, 'return')['shares'].iloc[-1]
                print(fairvalue)
                print(fairvalue / finalshares)

                # tvd5 = pvd5 * (1 + divgrafterfiveyears) / (1 - divgrafterfiveyears)
                # updatedpvd5 = (divp5 + tvd5) / ((1 + ror) ** 5)
                # fairvalue = pvd1 + pvd2 + pvd3 + pvd4 + updatedpvd5

                # print('sum of fcfs')
                # print(fcfp1 + fcfp2+fcfp3+fcfp4+fcfp5)
                # tv = fcfp5 * (1 + fcfgr) / (ror - fcfgr)
                # pv = (tv)
                # print(tv)
                # tenYearPrice = price * ((1 + (pricegr/100)) ** 10)
                # tenYearDiv = divrate * ((1 + (divgr/100)) ** 10)
                # twentyYearPrice = price * ((1 + (pricegr/100)) ** 20)
                # twentyYearDiv = divrate * ((1 + (divgr/100)) ** 20)
                # toupload['Ticker'] = [x]
                # toupload['Sector'] = sector
                # toupload['currentPrice'] = price
                # toupload['currentDiv'] = divrate
                # toupload['currentValuation'] = price / divrate
                # toupload['priceGR'] = pricegr
                # toupload['divGR'] = divgr
                # toupload['tenYearPrice'] = tenYearPrice
                # toupload['tenYearDiv'] = tenYearDiv
                # toupload['tenYearValuation'] = tenYearPrice / tenYearDiv
                # toupload['tenYearFlatValuation'] = price / tenYearDiv
                # toupload['twentyYearPrice'] = twentyYearPrice
                # toupload['twentyYearDiv'] = twentyYearDiv
                # toupload['twentyYearValuation'] = twentyYearPrice / twentyYearDiv
                # toupload['twentyYearFlatValuation'] = price / twentyYearDiv
                # # uploadToDB(toupload,'PDValuation')
                # toreturn = pd.concat([toreturn, toupload], ignore_index = True)

            except Exception as err:
                print('DCF evaulate for inner err')
                print(str(x) + ' does not pay a dividend, most likely.')
                print(err)
                continue
    except Exception as err:
        print('DCF evaulate err')
        print(err)
    # finally:
    #     return toreturn

# evaluateDCF(['MSFT','AAPL'],0.2)

