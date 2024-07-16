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
#going to have to manually review all of these rankings, to verify the integrity of rankings is what our company stands by #luke
#




# print('divrates, literal, ttm')
# print(divrate)
# print('yields, literal, 5yr, ttm')
# print(divyield)
# print('price')
# print(price)
# print('valuation')
# print(price / divrate)
# print('yield valuation')
# print(1 / divyield) #less good

# testing = 'SELECT Ticker FROM Metadata WHERE aggDivsPSGrowthAVG IS null;'
# print_DB(testing, 'print')



# from metadata, get AveragedOverYears
# priceGrowthAVG
# 
def evaluate():
    try:
        toupload = pd.DataFrame()
        metafacts = 'SELECT Ticker, Sector, cast(AveragedOverYears as integer) as years, \
                        CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                        priceGrowthAVG as pgr \
                    FROM Metadata WHERE Ticker IN (\'MSFT\');'#, \'TXN\', \'O\', \'NEE\');'
        metadata = print_DB(metafacts, 'return')
        stock = yf.Ticker('MSFT')
        dict1 = stock.info
        price = dict1['previousClose']
        divrate = dict1['dividendRate']
        # divyield = dict1['dividendYield']
        toupload['Ticker'] = 'MSFT'
        toupload['Sector'] = metadata['Sector'][0]
        toupload['currentPrice'] = price
        # latestDiv = models.FloatField(blank=True, null=True)
        # currentValuation = models.FloatField(blank=True, null=True)

        # priceGR = tenYearDiv = models.FloatField(blank=True, null=True)
        # divGR = models.FloatField(blank=True, null=True)

        # tenYearPrice = models.FloatField(blank=True, null=True)
        # tenYearDiv = models.FloatField(blank=True, null=True)
        # tenYearValuation = models.FloatField(blank=True, null=True)

        # twentyYearPrice = models.FloatField(blank=True, null=True)
        # twentyYearDiv = models.FloatField(blank=True, null=True)
        # twentyYearValuation = models.FloatField(blank=True, null=True)

        #and don't forget to do migrations

    except Exception as err:
        print('evaulate err')
        print(err)
    finally:
        return toupload

#P/D, inverse yield, is a current valuation. <25 is great. <40 + gr>10% is still decent. >45 is no go. 40-45 debatable for enough quality, price history

#div cagr * yield == alternative valuation, giving an idea into future value as well

# priceGrowthAVG from metadata could also be useful in that:
# PGAVG / divgrAVG gives us some idea of how quickly price vs yield changes.
# the smaller the number, the more likely dividend grows while price stays sane

#also, you can predict the future price by pGR * years analyzed, divGR * years analyzed, recalculating the P/Div. obviously using a(1+-r)^t



