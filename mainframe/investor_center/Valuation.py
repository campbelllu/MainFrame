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
import SectorRankings as sr
import AltTables as at

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

# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm
# Clean code: below
#pd analysis of a list of stocks, or etf's, returns something to put on webpage eventually, but first saves it in csv or prints it
#


#this turned out well.
#we will add more valuations, and different price changes thru the years
#make it callable via a list input of tickers. that invalidates the table, removes need of updates, and works better for report generation

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
        # length1 = len(metadata['Ticker'])
        for x in metadata['Ticker']:
            try:
                # print(str(round(n/length1,4)*100) + '% complete!')
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
        return toreturn

# print(PD(['MSFT','AAPL'])[['Ticker','currentValuation', 'idealPriceCeiling', 'tenYearValuation', 'twentyYearValuation', 'tenYearFlatValuation','twentyYearFlatValuation']])

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
        return toreturn

# print(DDM(['ARCC', 'TXN', 'STAG','PLD','O']))

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

                for x in range(len(divs) - 1):
                    diff = abs((divs[x+1])-divs[x])
                    if divs[x] > divs[x+1]:
                        diff = diff * -1
                    if abs(divs[x]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[x]) * 4
                    growthList.append(change)
                divrate =  dict1['navPrice'] * dict1['yield']
                price = dict1['previousClose']
                
                time1 = (len(divs)/4)
                cagr = ((divs[-1]/divs[0]) ** (1/time1)) - 1
                iqrMean = metadata.IQR_Mean(growthList)
                divgr = (cagr + iqrMean) / 2

                tenYearDiv = divrate * ((1 + (divgr)) ** 10)
                twentyYearDiv = divrate * ((1 + (divgr)) ** 20)
                toupload['currentPrice'] = price
                toupload['currentDiv'] = divrate
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
        return toreturn

# print(ETFPD(['SCHD','DGRO','VIG','SOXX','SPY','QQQ','SCHG','JEPI','BITO']))

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
                toupload['Ticker'] = [x]
                
                for x in range(len(divs) - 1):
                    diff = abs((divs[x+1])-divs[x])
                    if divs[x] > divs[x+1]:
                        diff = diff * -1
                    if abs(divs[x]) == 0:
                        change = np.nan
                    else:
                        change = diff / abs(divs[x]) * 4
                    growthList.append(change)
                divrate =  dict1['navPrice'] * dict1['yield']
                
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
        return toreturn


# ETFDDM(['DGRO','SCHD','VIG','SOXX','SPY','QQQ','SCHG','JEPI','BITO','IWM']) #

stockmats = ['UFPI']
stockenergy = ['CVX','XOM']
stockfinance = ['ARCC','MAIN','HTGC','TSLX','CSWC','JPM']
stockinds = ['FAST','PH','ETN','RSG','WM','CAT','WSO','FIX','CTAS','LMT']
stocktech = ['TXN','ADI','MCHP','MSFT','AAPL','IBM']
stockstaples = ['COST','WMT','PG','KR']
stockre = ['O','NNN','ADC','PLD','STAG','REXR','TRNO','FR','AMT','SBAC','CCI','DLR','EQIX']
stockutil = ['NEE','SO','AWK','CPK','ATO']
stockhealth = ['UNH','MCK','JNJ','ABBV']
stockdisc = ['HD','TSCO','MCD','F','YUM']
etflist = ['XLB','XLC','XLE','XLF','XLI','XLK','XLP','XLRE','SCHH','XLU','XLV','XLY']
print(ETFPD(etflist))
print(ETFDDM(etflist))



# getpd = 'SELECT * FROM PDValuation \
#             WHERE Ticker IN (\'ARCC\', \'HD\', \'O\', \'PLD\', \'STAG\', \'NNN\', \'ADC\', \'TSCO\', \'NUE\', \'COST\', \
#                                 \'TXN\', \'ADI\', \'MCHP\') \
#             ORDER BY currentValuation;'
# print(print_DB(getpd, 'return').head(50))

# eq = 'Select Ticker, Sector, calcBookValueAVG as cbv, repBookValueAVG as rbv, calculatedEquityGrowthAVG as ceq, reportedEquityGrowthAVG as req \
#         FROM Metadata \
#         WHERE cbv IS NULL \
#         AND rbv IS NULL \
#         AND ceq IS NULL \
#         AND req IS NULL'
# print_DB(eq, 'print')

# AND currentValuation >= 25 \
#             AND tenYearValuation < 45 \
#             AND twentyYearValuation < 35 \
#             AND divGR < 50 \

# , \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \
#                                 \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \
#                                 \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \'SCM\', \'SLRC\', \'SSSS\', \
#                                 \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\'



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

#probably will never be used, db deprecated
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