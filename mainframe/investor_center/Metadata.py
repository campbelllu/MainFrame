import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
# import datetime as dt #leaving only because I'm not sure which I used.
from datetime import date 
import time
import os
from pathlib import Path
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
# from currency_converter import CurrencyConverter #https://pypi.org/project/CurrencyConverter/
# converter_address = 'investor_center/currency-hist.csv'
# curConvert = CurrencyConverter(converter_address, fallback_on_missing_rate=True)
### Documentation: https://pypi.org/project/CurrencyConverter/ 
import os
import django
import sys
from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainframe.settings')
django.setup()

db_path = settings.DATABASES['default']['NAME']

#From fellow files
import csv_modules as csv
# import Mega as mega

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}

# db_path = os.path.join(Path(__file__).resolve().parent.parent, 'stock_data.sqlite3') #'/home/family/Documents/repos/MainFrame/mainframe/stock_data.sqlite3'

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

def IQR_Mean(list1):
    try:
        nonechecker = 0
        infchecker = 0
        for x in list1:
            if x is None:
                nonechecker += 1
            if x == np.inf:
                infchecker += 1

        if nonechecker == len(list1):
            ar_Mean = np.nan
            return ar_Mean
        if infchecker == len(list1):
            ar_Mean = np.nan
            return ar_Mean

        if isinstance(list1[0],float) or isinstance(list1[0],int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
            cleaned_list = [x for x in cleaned_list if not np.isinf(x)]
        elif isinstance(list1[0],str):
            cleaned_list = [eval(i) for i in list1]
        else:
            print('IQR_Mean type was not string or float')

        q1 = np.percentile(cleaned_list, 25)
        q3 = np.percentile(cleaned_list, 75)
        iqr = q3 - q1
        median = np.median(cleaned_list)
        ar_top = median + iqr
        ar_bottom = median - iqr

        ar_list = []
        for x in cleaned_list:
            if x < ar_top and x > ar_bottom:
                ar_list.append(x)

        #When q1=q3, it leaves no mean found, the fix:
        if len(ar_list) == 0:
            ar_Mean = np.mean(cleaned_list)
        else:
            ar_Mean = np.mean(ar_list)
        return ar_Mean
    except Exception as err:
        print("IQR Mean error: ")
        print(err)

def IQR_MeanNZ(list1):
    try:
        nonechecker = 0
        infchecker = 0
        for x in list1:
            if x is None:
                nonechecker += 1
            if x == np.inf:
                infchecker += 1      
        if nonechecker == len(list1):
            ar_Mean = np.nan
            return ar_Mean
        if infchecker == len(list1):
            ar_Mean = np.nan
            return ar_Mean
       
        if isinstance(list1[0], float) or isinstance(list1[0], int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
            cleaned_list = [x for x in cleaned_list if not np.isinf(x)]
            cleaned_list = [x for x in cleaned_list if x != 0]

            if len(cleaned_list) == 0:
                return np.nan
          
        elif isinstance(list1[0], str):
            cleaned_list = [eval(i) for i in list1]
        else:
            print('IQR_Mean nz type was not string or float')

        q1 = np.percentile(cleaned_list, 25)
        q3 = np.percentile(cleaned_list, 75)
        iqr = q3 - q1
        median = np.median(cleaned_list)
        ar_top = median + iqr
        ar_bottom = median - iqr

        ar_list = []
        for x in cleaned_list:
            if x < ar_top and x > ar_bottom:
                ar_list.append(x)

        #When q1=q3, it leaves no mean found, the fix:
        if len(ar_list) == 0:
            ar_Mean = np.mean(cleaned_list)
        else:
            ar_Mean = np.mean(ar_list)
        return ar_Mean
    except Exception as err:
        print("IQR Mean nz error: ")
        print(err)

def nan_strip_min(list1):
    try:
        cleaned_list = []
        if isinstance(list1[0],float) or isinstance(list1[0],int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
            ar_Min = np.min(cleaned_list)
        elif isinstance(list1[0], str):
            cleaned_list = [eval(i) for i in list1]
            ar_Min = np.min(cleaned_list)
        elif list1[0] is None:
            ar_Min = np.nan
        else:
            print('strip Min type was not int, float or none')

    except Exception as err:
        print("strip Min error: ")
        print(err)
    finally:
        return ar_Min

def nan_strip_max(list1):
    try:
        cleaned_list = []
        if isinstance(list1[0],float) or isinstance(list1[0],int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
            ar_Max = np.max(cleaned_list)
        elif isinstance(list1[0],str):
            cleaned_list = [eval(i) for i in list1]
            ar_Max = np.max(cleaned_list)
        elif list1[0] is None:
            ar_Max = np.nan
        else:
            print('strip Max type was not int or float')

    except Exception as err:
        print("strip Max error: ")
        print(err)
    finally:
        return ar_Max

def nan_strip_count(list1):
    try:
        cleaned_list = []
        if isinstance(list1[0],float) or isinstance(list1[0],int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
        elif isinstance(list1[0],str):
            cleaned_list = [eval(i) for i in list1]
        else:
            print('strip count type was not int or float')

        ar_count = len(cleaned_list)
    except Exception as err:
        print("strip count error: ")
        print(err)
    finally:
        return ar_count

def nan_strip_list(list1):
    try:
        cleaned_list = []
        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list1 if not np.isnan(x)]
        elif isinstance(list1[0],str):
            cleaned_list = [eval(i) for i in list1]
        else:
            print('strip count type was not int or float')

    except Exception as err:
        print("strip list1 error: ")
        print(err)
    finally:
        return cleaned_list

def count_nonzeroes(list1):
    try:
        cleaned_list = [n for n in list1 if n != 0]
        ar_count = len(cleaned_list)
    except Exception as err:
        print("nonzero count error: ")
        print(err)
    finally:
        return ar_count

def zeroIntegrity(list1):
    #deprecated, ended up not being used
    try:
        #first check zeroes
        numzeroes = list1.count(0)
        check = numzeroes / len(list1)

        if check == 1:
            integrityFlag = 'allZeroes'
        elif check > 0.5 and check < 1:
            integrityFlag = 'bad'
        elif check < 0.5 and check >= 0.2:
            integrityFlag = 'unreliable'
        elif check < 0.2 and check >= 0.05:
            integrityFlag = 'decent'
        elif check < 0.05:
            integrityFlag = 'good'

        #now solve empty/nan list1 returning 'good'
        newlistdf = pd.DataFrame()
        newlistdf['test'] = list1
        newlistdf = newlistdf.replace([np.inf, -np.inf], np.nan)
        newlist = newlistdf['test'].dropna()
        if len(newlist) == 0:
            integrityFlag = 'emptyAVG'

    except Exception as err:
        print('zero integrity error: ')
        print(err)
    finally:
        return integrityFlag

def income_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, revenue, revenueGrowthRate, netIncome, netIncomeGrowthRate, \
                        ffo, ffoGrowthRate, \
                        reportedEPS, reportedEPSGrowthRate, calculatedEPS, calculatedEPSGrowthRate, reitEPS, reitEPSGrowthRate, \
                        fcf, fcfGrowthRate, fcfMargin, fcfMarginGrowthRate, profitMargin, profitMarginGrowthRate, \
                        price, priceGrowthRate \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' \
                    ORDER BY Year  \
                    ;'
                    # netIncomeNCI, netIncomeNCIGrowthRate,
        df1 = pd.read_sql(thequery,conn)
        query.close()
        conn.close()
    except Exception as Err:
        print('income reading error: ')
        print(Err)
    finally:
        return df1

def balanceSheet_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, TotalDebt, TotalDebtGrowthRate, assets, liabilities, \
                        ReportedTotalEquity, ReportedTotalEquityGrowthRate, TotalEquity, TotalEquityGrowthRate \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' \
                    ORDER BY Year  \
                    ;'

        df1 = pd.read_sql(thequery,conn)
        query.close()
        conn.close()
    except Exception as Err:
        print('income reading error: ')
        print(Err)
    finally:
        return df1

def cashFlow_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, operatingCashflow, operatingCashflowGrowthRate, \
                        investingCashFlow, investingCashFlowGrowthRate, \
                        financingCashFlow, financingCashFlowGrowthRate, \
                        netCashFlow, netCashFlowGrowthRate, interestPaid, \
                        capEx, capExGrowthRate, depreNAmor, gainSaleProp \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' \
                    ORDER BY Year  \
                    ;'
        df1 = pd.read_sql(thequery,conn)
        query.close()
        conn.close()
    except Exception as Err:
        print('income reading error: ')
        print(Err)
    finally:
        return df1

def dividend_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, shares, sharesGrowthRate, totalDivsPaid, \
                        divsPaidPerShare, calcDivsPerShare, divGrowthRateBOT, divGrowthRateBORPS, divGrowthRateBOCPS, payoutRatio, \
                        fcfPayoutRatio, ffoPayoutRatio \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' \
                    ORDER BY Year  \
                    ;'
                    # dilutedShares, dilutedSharesGrowthRate, ROCTotal, ROCperShare, ROCperShareGrowthRate, ROCTotalGrowthRate
        df1 = pd.read_sql(thequery,conn)
        query.close()
        conn.close()
    except Exception as Err:
        print('income reading error: ')
        print(Err)
    finally:
        return df1

def efficiency_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, operatingIncome, operatingIncomeGrowthRate, taxRate, nopat, investedCapital, \
                        roic, adjRoic, reportedAdjRoic, calculatedRoce, reportedRoce, rReitROE, rReitROEGrowthRate, cReitROE, cReitROEGrowthRate, \
                        calcBookValue, calcBookValueGrowthRate, reportedBookValue, reportedBookValueGrowthRate, nav, navGrowthRate \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' \
                    ORDER BY Year  \
                    ;'
        df1 = pd.read_sql(thequery,conn)
        query.close()
        conn.close()
    except Exception as Err:
        print('income reading error: ')
        print(Err)
    finally:
        return df1

#luke gotta add this in somewhere, edit models and templates, win. and views!
# @property  #LUKE this isn't actually used, but is calculated in views, line 84 roughly. gotta just do it in mega-no-metadata. <3
    # def profit_margin_avg(self):
    #     if self.revenue is None or self.revenue == 0:
    #         return None
    #     elif self.netIncome is None:
    #         return None
    #     else:
    #         return self.netIncome / self.revenue * 100

    # @property
    # def poravg100(self):
    #     if self.payoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.payoutRatioAVG * 100

    # @property
    # def fcfporavg100(self):
    #     if self.fcfPayoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.fcfPayoutRatioAVG * 100
        
    # @property
    # def ffoporavg100(self):
    #     if self.ffoPayoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.ffoPayoutRatioAVG * 100

def full_analysis(incomedf, balancedf, cfdf, divdf, effdf):
    try:
        ticker = incomedf['Ticker'].iloc[:1]
        latest_year = nan_strip_max(incomedf['year'])
        first_year = nan_strip_min(incomedf['year'])
        numYearsAnalyzed = count_nonzeroes(nan_strip_list(incomedf['year']))
        sector = incomedf['Sector']
        industry = incomedf['Industry']

        metadata = pd.DataFrame()
        metadata['Ticker'] = ticker
        metadata['FirstYear'] = first_year
        metadata['LatestYear'] = latest_year
        metadata['AveragedOverYears'] = numYearsAnalyzed
        metadata['Sector'] = sector
        metadata['Industry'] = industry

        #Revenue, GR min, max, avg
        revlist = incomedf['revenueGrowthRate'].tolist()
        # revmin = nan_strip_min(revlist)
        # revmax = nan_strip_max(revlist)
        # revavg = IQR_Mean(revlist)
        revavgnz = IQR_MeanNZ(revlist)
        # revavginteg = zeroIntegrity(revlist)

        # metadata['revGrowthAVG'] = revavg
        # metadata['revGrowthAVGintegrity'] = revavginteg
        metadata['revGrowthAVGnz'] = revavgnz

        #netincome x2, gr's min, max, avg
        netinclist = incomedf['netIncome'].tolist()
        nimin = nan_strip_min(netinclist)
        # nimax = nan_strip_max(netinclist)
        # niavg = IQR_Mean(netinclist)

        netincgrlist = incomedf['netIncomeGrowthRate'].tolist()
        # nigrmin = nan_strip_min(netincgrlist)
        # nigrmax = nan_strip_max(netincgrlist)
        # nigravg = IQR_Mean(netincgrlist)
        nigravgnz = IQR_MeanNZ(netincgrlist)
        # nigravgint = zeroIntegrity(netincgrlist)

        # netincNCIlist = incomedf['netIncomeNCI'].tolist()
        # nincimin = nan_strip_min(netincNCIlist)

        # netincNCIgrlist = incomedf['netIncomeNCIGrowthRate'].tolist()
        # nincigrmin = nan_strip_min(netincNCIgrlist)
        # nincigrmax = nan_strip_max(netincNCIgrlist)
        # nincigravg = IQR_Mean(netincNCIgrlist)
        # nincigravgnz = IQR_MeanNZ(netincNCIgrlist)
        # nincigrint = zeroIntegrity(netincNCIgrlist)

        metadata['netIncomeLow'] = nimin
        # metadata['netIncomeGrowthAVG'] = nigravg
        # metadata['netIncomeGrowthAVGintegrity'] = nigravgint
        metadata['netIncomeGrowthAVGnz'] = nigravgnz

        # metadata['netIncomeNCILow'] = nincimin
        # metadata['netIncomeNCIGrowthAVG'] = nincigravg
        # metadata['netIncomeNCIGrowthAVGintegrity'] = nincigrint
        # metadata['netIncomeNCIGrowthAVGnz'] = nincigravgnz

        #ffo gr's min, max, avg
        ffolist = incomedf['ffo'].tolist()
        ffomin = nan_strip_min(ffolist)
        # ffomax = nan_strip_max(ffolist)
        # ffoavg = IQR_Mean(ffolist)

        ffogrlist = incomedf['ffoGrowthRate'].tolist()
        # ffogrmin = nan_strip_min(ffogrlist)
        # ffogrmax = nan_strip_max(ffogrlist)
        # ffogravg = IQR_Mean(ffogrlist)
        ffogravgnz = IQR_MeanNZ(ffogrlist)
        # ffogravgint = zeroIntegrity(ffogrlist)

        metadata['ffoLow'] = ffomin
        # metadata['ffoGrowthAVG'] = ffogravg
        # metadata['ffoGrowthAVGintegrity'] = ffogravgint
        metadata['ffoGrowthAVGnz'] = ffogravgnz

        # reportedEPS, 
        repslist = incomedf['reportedEPS'].tolist()
        repsmin = nan_strip_min(repslist)
        # repsavg = IQR_Mean(repslist)
        # repsavgint = zeroIntegrity(repslist)
        repsavgnz = IQR_MeanNZ(repslist)

        metadata['repsLow'] = repsmin
        # metadata['repsAVG'] = repsavg
        # metadata['repsAVGintegrity'] = repsavgint
        metadata['repsAVGnz'] = repsavgnz
        
        #reportedEPSGrowthRate, 
        repsgrlist = incomedf['reportedEPSGrowthRate'].tolist()
        # repsgrmin = nan_strip_min(repsgrlist)
        # repsgravg = IQR_Mean(repsgrlist)
        # repsgrint = zeroIntegrity(repsgrlist)
        repsgravgnz = IQR_MeanNZ(repsgrlist)

        # metadata['repsGrowthAVG'] = repsgravg
        # metadata['repsGrowthAVGintegrity'] = repsgrint
        metadata['repsGrowthAVGnz'] = repsgravgnz

        #calculatedEPS, 
        cepslist = incomedf['calculatedEPS'].tolist()
        cepsmin = nan_strip_min(cepslist)
        cepsavg = IQR_Mean(cepslist)
        cepsavgint = zeroIntegrity(cepslist)
        cepsavgnz = IQR_MeanNZ(cepslist)

        metadata['cepsLow'] = cepsmin
        metadata['cepsAVG'] = cepsavg
        metadata['cepsAVGintegrity'] = cepsavgint
        metadata['cepsAVGnz'] = cepsavgnz
        
        #calculatedEPSGrowthRate, 
        cepsgrlist = incomedf['calculatedEPSGrowthRate'].tolist()
        # repsgrmin = nan_strip_min(repsgrlist)
        cepsgravg = IQR_Mean(cepsgrlist)
        cepsgrint = zeroIntegrity(cepsgrlist)
        cepsgravgnz = IQR_MeanNZ(cepsgrlist)

        metadata['cepsGrowthAVG'] = cepsgravg
        metadata['cepsGrowthAVGintegrity'] = cepsgrint
        metadata['cepsGrowthAVGnz'] = cepsgravgnz
        
        #reitEPS, 
        reitepslist = incomedf['reitEPS'].tolist()
        reitepsmin = nan_strip_min(reitepslist)
        reitepsavg = IQR_Mean(reitepslist)
        reitepsavgint = zeroIntegrity(reitepslist)
        reitepsavgnz = IQR_MeanNZ(reitepslist)

        metadata['reitepsLow'] = reitepsmin
        metadata['reitepsAVG'] = reitepsavg
        metadata['reitepsAVGintegrity'] = reitepsavgint
        metadata['reitepsAVGnz'] = reitepsavgnz
        
        #reitEPSGrowthRate,
        reitepsgrlist = incomedf['reitEPSGrowthRate'].tolist()
        # repsgrmin = nan_strip_min(repsgrlist)
        reitepsgravg = IQR_Mean(reitepsgrlist)
        reitepsgrint = zeroIntegrity(reitepsgrlist)
        reitepsgravgnz = IQR_MeanNZ(reitepsgrlist)

        metadata['reitepsGrowthAVG'] = reitepsgravg
        metadata['reitepsGrowthAVGintegrity'] = reitepsgrint
        metadata['reitepsGrowthAVGnz'] = reitepsgravgnz
        

        #fcf: gr min max avg
        fcflist = incomedf['fcf'].tolist()
        fcfmin = nan_strip_min(fcflist)
        # fcfmax = nan_strip_max(fcflist)
        # fcfavg = IQR_Mean(fcflist)

        fcfgrlist = incomedf['fcfGrowthRate'].tolist()
        # fcfgrmin = nan_strip_min(fcfgrlist)
        # fcfgrmax = nan_strip_max(fcfgrlist)
        fcfgravg = IQR_Mean(fcfgrlist)
        fcfgravgint = zeroIntegrity(fcfgrlist)
        fcfgravgnz = IQR_MeanNZ(fcfgrlist)

        metadata['fcfLow'] = fcfmin
        metadata['fcfGrowthAVG'] = fcfgravg
        metadata['fcfGrowthAVGintegrity'] = fcfgravgint
        metadata['fcfGrowthAVGnz'] = fcfgravgnz

        #fcfmargin: min max avg
        fcfmarginlist = incomedf['fcfMargin'].tolist()
        fcfmarginmin = nan_strip_min(fcfmarginlist)
        fcfmarginmax = nan_strip_max(fcfmarginlist)
        fcfmarginavg = IQR_Mean(fcfmarginlist)
        # fcfmarginavgint = zeroIntegrity(fcfmarginlist)
        # fcfmarginavgnz = IQR_MeanNZ(fcfmarginlist)

        metadata['fcfMarginLow'] = fcfmarginmin
        metadata['fcfMarginHigh'] = fcfmarginmax
        metadata['fcfMarginAVG'] = fcfmarginavg
        # metadata['fcfMarginAVGintegrity'] = fcfmarginavgint
        # metadata['fcfMarginAVGnz'] = fcfmarginavgnz

        #fcfmargin gr min max avg
        fcfmargingrlist = incomedf['fcfMarginGrowthRate'].tolist()
        # fcfmargingrmin = nan_strip_min(fcfmargingrlist)
        # fcfmargingrmax = nan_strip_max(fcfmargingrlist)
        fcfmargingravg = IQR_Mean(fcfmargingrlist)
        fcfmargingravgint = zeroIntegrity(fcfmargingrlist)
        fcfmargingravgnz = IQR_MeanNZ(fcfmargingrlist)

        metadata['fcfMarginGrowthAVG'] = fcfmargingravg
        metadata['fcfMarginGrowthAVGintegrity'] = fcfmargingravgint
        metadata['fcfMarginGrowthAVGnz'] = fcfmargingravgnz

        #price min max avg, gr min max avg
        pricelist = incomedf['price'].tolist()
        pricemin = nan_strip_min(pricelist)
        pricemax = nan_strip_max(pricelist)
        pricelatest = pricelist[-1]
        priceavg = IQR_Mean(pricelist)
        pricegrlist = incomedf['priceGrowthRate'].tolist()
        # pricegrmin = nan_strip_min(pricegrlist)
        # pricegrmax = nan_strip_max(pricegrlist)
        pricegravg = IQR_Mean(pricegrlist)

        metadata['priceLow'] = pricemin
        metadata['priceHigh'] = pricemax
        metadata['priceLatest'] = pricelatest
        metadata['priceAVG'] = priceavg
        metadata['priceGrowthAVG'] = pricegravg

        #debt gr min max avg
        debtlist = balancedf['TotalDebtGrowthRate'].tolist()
        # debtmin = nan_strip_min(debtlist)
        # debtmax = nan_strip_max(debtlist)
        debtavg = IQR_Mean(debtlist)

        metadata['debtGrowthAVG'] = debtavg

        #rep equity gr min max avg
        repeqlist = balancedf['ReportedTotalEquity'].tolist()
        repeqmin = nan_strip_min(repeqlist)
        # repeqmax = nan_strip_max(repeqlist)
        # repeqavg = IQR_Mean(repeqlist)
        repeqgrlist = balancedf['ReportedTotalEquityGrowthRate'].tolist()
        # repeqgrmin = nan_strip_min(repeqgrlist)
        # repeqgrmax = nan_strip_max(repeqgrlist)
        repeqgravg = IQR_Mean(repeqgrlist)
        repeqgravgint = zeroIntegrity(repeqgrlist)
        repeqgravgnz = IQR_MeanNZ(repeqgrlist)

        metadata['reportedEquityLow'] = repeqmin
        metadata['reportedEquityGrowthAVG'] = repeqgravg
        metadata['reportedEquityGrowthAVGintegrity'] = repeqgravgint
        metadata['reportedEquityGrowthAVGnz'] = repeqgravgnz

        #calcd equity gr min max avg
        calceqlist = balancedf['TotalEquity'].tolist()
        calceqmin = nan_strip_min(calceqlist)
        # calceqmax = nan_strip_max(calceqlist)
        # calceqavg = IQR_Mean(calceqlist)
        calceqgrlist = balancedf['TotalEquityGrowthRate'].tolist()
        # calceqgrmin = nan_strip_min(calceqgrlist)
        # calceqgrmax = nan_strip_max(calceqgrlist)
        calceqgravg = IQR_Mean(calceqgrlist)
        calceqgravgint = zeroIntegrity(calceqgrlist)
        calceqgravgnz = IQR_MeanNZ(calceqgrlist)

        metadata['calculatedEquityLow'] = calceqmin
        metadata['calculatedEquityGrowthAVG'] = calceqgravg
        metadata['calculatedEquityGrowthAVGintegrity'] = calceqgravgint
        metadata['calculatedEquityGrowthAVGnz'] = calceqgravgnz

        #equity avg... avg'd
        # aggeqmin = (repeqgrmin + calceqgrmin) / 2
        # aggeqmax = (repeqgrmax + calceqgrmax) / 2
        aggeqavg = (repeqgravg + calceqgravg) / 2

        metadata['aggEquityGrowthAVG'] = aggeqavg

        #op cf min max avg
        opcflist = cfdf['operatingCashFlow'].tolist()
        opcfmin = nan_strip_min(opcflist)
        # opcfmax = nan_strip_max(opcflist)
        opcfavg = IQR_Mean(opcflist)
        opcfavgint = zeroIntegrity(opcflist)
        opcfavgnz = IQR_MeanNZ(opcflist)

        metadata['operatingCashFlowLow'] = opcfmin
        metadata['operatingCashFlowAVG'] = opcfavg
        metadata['operatingCashFlowAVGintegrity'] = opcfavgint
        metadata['operatingCashFlowAVGnz'] = opcfavgnz

        #op cf gr min max avg
        opcfgrlist = cfdf['operatingCashFlowGrowthRate'].tolist()
        # opcfgrmin = nan_strip_min(opcfgrlist)
        # opcfgrmax = nan_strip_max(opcfgrlist)
        opcfgravg = IQR_Mean(opcfgrlist)
        opcfgravgint = zeroIntegrity(opcfgrlist)
        opcfgravgnz = IQR_MeanNZ(opcfgrlist)

        metadata['operatingCashFlowGrowthAVG'] = opcfgravg
        metadata['operatingCashFlowGrowthAVGintegrity'] = opcfgravgint
        metadata['operatingCashFlowGrowthAVGnz'] = opcfgravgnz

        #inv cf min max avg
        invcflist = cfdf['investingCashFlow'].tolist()
        invcfmin = nan_strip_min(invcflist)
        # invcfmax = nan_strip_max(invcflist)
        invcfavg = IQR_Mean(invcflist)
        invcfavgint = zeroIntegrity(invcflist)
        invcfavgnz = IQR_MeanNZ(invcflist)

        metadata['investingCashFlowLow'] = invcfmin
        metadata['investingCashFlowAVG'] = invcfavg
        metadata['investingCashFlowAVGintegrity'] = invcfavgint
        metadata['investingCashFlowAVGnz'] = invcfavgnz

        #inv cf gr min max avg
        invcfgrlist = cfdf['investingCashFlowGrowthRate'].tolist()
        # invcfgrmin = nan_strip_min(invcfgrlist)
        # invcfgrmax = nan_strip_max(invcfgrlist)
        invcfgravg = IQR_Mean(invcfgrlist)
        invcfgravgint = zeroIntegrity(invcfgrlist)
        invcfgravgnz = IQR_MeanNZ(invcfgrlist)

        metadata['investingCashFlowGrowthAVG'] = invcfgravg
        metadata['investingCashFlowGrowthAVGintegrity'] = invcfgravgint
        metadata['investingCashFlowGrowthAVGnz'] = invcfgravgnz

        #fin cf min max avg
        fincflist = cfdf['financingCashFlow'].tolist()
        fincfmin = nan_strip_min(fincflist)
        # fincfmax = nan_strip_max(fincflist)
        fincfavg = IQR_Mean(fincflist)
        fincfavgint = zeroIntegrity(fincflist)
        fincfavgnz = IQR_MeanNZ(fincflist)

        metadata['financingCashFlowLow'] = fincfmin
        metadata['financingCashFlowAVG'] = fincfavg
        metadata['financingCashFlowAVGintegrity'] = fincfavgint
        metadata['financingCashFlowAVGnz'] = fincfavgnz

        #fin cf gr min max avg
        fincfgrlist = cfdf['financingCashFlowGrowthRate'].tolist()
        # fincfgrmin = nan_strip_min(fincfgrlist)
        # fincfgrmax = nan_strip_max(fincfgrlist)
        fincfgravg = IQR_Mean(fincfgrlist)
        fincfgravgint = zeroIntegrity(fincfgrlist) 
        fincfgravgnz = IQR_MeanNZ(fincfgrlist)

        metadata['financingCashFlowGrowthAVG'] = fincfgravg
        metadata['financingCashFlowGrowthAVGintegrity'] = fincfgravgint
        metadata['financingCashFlowGrowthAVGnz'] = fincfgravgnz

        #net cf min max avg
        netcflist = cfdf['netCashFlow'].tolist()
        netcfmin = nan_strip_min(netcflist)
        # netcfmax = nan_strip_max(netcflist)
        netcfavg = IQR_Mean(netcflist)
        netcfavgint = zeroIntegrity(netcflist)
        netcfavgnz = IQR_MeanNZ(netcflist)

        metadata['netCashFlowLow'] = netcfmin
        metadata['netCashFlowAVG'] = netcfavg
        metadata['netCashFlowAVGintegrity'] = netcfavgint
        metadata['netCashFlowAVGnz'] = netcfavgnz

        #net cf gr min max avg
        netcfgrlist = cfdf['netCashFlowGrowthRate'].tolist()
        # netcfgrmin = nan_strip_min(netcfgrlist)
        # netcfgrmax = nan_strip_max(netcfgrlist)
        netcfgravg = IQR_Mean(netcfgrlist)
        netcfgravgint = zeroIntegrity(netcfgrlist)
        netcfgravgnz = IQR_MeanNZ(netcfgrlist)

        metadata['netCashFlowGrowthAVG'] = netcfgravg
        metadata['netCashFlowGrowthAVGintegrity'] = netcfgravgint
        metadata['netCashFlowGrowthAVGnz'] = netcfgravgnz

        #capex gr min max avg
        capexlist = cfdf['capExGrowthRate'].tolist()
        # capexmin = nan_strip_min(capexlist)
        # capexmax = nan_strip_max(capexlist)
        capexavg = IQR_Mean(capexlist)
        capexavgint = zeroIntegrity(capexlist)
        capexavgnz = IQR_MeanNZ(capexlist)

        metadata['capexGrowthAVG'] = capexavg
        metadata['capexGrowthAVGintegrity'] = capexavgint
        metadata['capexGrowthAVGnz'] = capexavgnz

        #shares gr min max avg
        shareslist = divdf['sharesGrowthRate'].tolist()
        # sharesmin = nan_strip_min(shareslist)
        # sharesmax = nan_strip_max(shareslist)
        sharesavg = IQR_Mean(shareslist)

        metadata['sharesGrowthAVG'] = sharesavg

        #dil shares same as above
        # dshareslist = divdf['dilutedSharesGrowthRate'].tolist()
        # dsharesmin = nan_strip_min(dshareslist)
        # dsharesmax = nan_strip_max(dshareslist)
        # dsharesavg = IQR_Mean(dshareslist)

        # metadata['dilutedSharesGrowthAVG'] = dsharesavg

        #total divs
        # tdivslist = divdf['totalDivsPaid'].tolist()
        # tdivsmin = nan_strip_min(tdivslist)
        # tdivsmax = nan_strip_max(tdivslist)
        # tdivsavg = IQR_Mean(tdivslist)

        #total divs gr divGrowthRateBOT
        tdivsgrlist = divdf['divGrowthRateBOT'].tolist()
        tdivsgrmin = nan_strip_min(tdivsgrlist)
        tdivsgrmax = nan_strip_max(tdivsgrlist)
        tdivsgravg = IQR_Mean(tdivsgrlist)
        tdivsgravgint = zeroIntegrity(tdivsgrlist)
        tdivsgravgnz = IQR_MeanNZ(tdivsgrlist)

        metadata['totalDivsPaidGrowthAVG'] = tdivsgravg
        metadata['totalDivsPaidGrowthAVGintegrity'] = tdivsgravgint
        metadata['totalDivsPaidGrowthAVGnz'] = tdivsgravgnz

        #calc dps
        cdpslist = divdf['calcDivsPerShare'].tolist()
        cdpsmin = nan_strip_min(cdpslist)
        cdpsmax = nan_strip_max(cdpslist)
        cdpslatest = cdpslist[-1]
        cdpsavg = IQR_Mean(cdpslist)

        metadata['calcDivsPerShareLow'] = cdpsmin
        metadata['calcDivsPerShareHigh'] = cdpsmax
        metadata['calcDivsPerShareLatest'] = cdpslatest
        metadata['calcDivsPerShareAVG'] = cdpsavg

        #calc dps gr divGrowthRateBOCPS
        cdpsgrlist = divdf['divGrowthRateBOCPS'].tolist()
        cdpsgrmin = nan_strip_min(cdpsgrlist)
        cdpsgrmax = nan_strip_max(cdpsgrlist)
        cdpsgravg = IQR_Mean(cdpsgrlist)
        cdpsgravgint = zeroIntegrity(cdpsgrlist)
        cdpsgravgnz = IQR_MeanNZ(cdpsgrlist)

        metadata['calcDivsPerShareGrowthLow'] = cdpsgrmin
        metadata['calcDivsPerShareGrowthHigh'] = cdpsgrmax
        metadata['calcDivsPerShareGrowthAVG'] = cdpsgravg
        metadata['calcDivsPerShareGrowthAVGintegrity'] = cdpsgravgint
        metadata['calcDivsPerShareGrowthAVGnz'] = cdpsgravgnz

        #dps
        dpslist = divdf['divsPaidPerShare'].tolist()
        dpsmin = nan_strip_min(dpslist)
        dpsmax = nan_strip_max(dpslist)
        dpslatest = dpslist[-1]
        dpsavg = IQR_Mean(dpslist)

        metadata['repDivsPerShareLow'] = dpsmin
        metadata['repDivsPerShareHigh'] = dpsmax
        metadata['repDivsPerShareLatest'] = dpslatest
        metadata['repDivsPerShareAVG'] = dpsavg

        #dps gr divGrowthRateBORPS
        dpsgrlist = divdf['divGrowthRateBORPS'].tolist()
        dpsgrmin = nan_strip_min(dpsgrlist)
        dpsgrmax = nan_strip_max(dpsgrlist)
        dpsgravg = IQR_Mean(dpsgrlist)
        dpsgravgint = zeroIntegrity(dpsgrlist)
        dpsgravgnz = IQR_MeanNZ(dpsgrlist)

        metadata['repDivsPerShareGrowthLow'] = dpsgrmin
        metadata['repDivsPerShareGrowthHigh'] = dpsgrmax
        metadata['repDivsPerShareGrowthAVG'] = dpsgravg
        metadata['repDivsPerShareGrowthAVGintegrity'] = dpsgravgint
        metadata['repDivsPerShareGrowthAVGnz'] = dpsgravgnz

        #agg ps
        aggpsdivmin = (dpsmin + cdpsmin) / 2
        aggpsdivmax = (dpsmax + cdpsmax) / 2
        aggpsdivavg = (dpsavg + cdpsavg) / 2

        metadata['aggDivsPSLow'] = aggpsdivmin
        metadata['aggDivsPSHigh'] = aggpsdivmax
        metadata['aggDivsPSAVG'] = aggpsdivavg

        aggpsdivgrmin = (dpsgrmin + cdpsgrmin) / 2
        aggpsdivgrmax = (dpsgrmax + cdpsgrmax) / 2
        aggpsdivgravg = (dpsgravg + cdpsgravg) / 2

        metadata['aggDivsPSGrowthLow'] = aggpsdivgrmin
        metadata['aggDivsPSGrowthHigh'] = aggpsdivgrmax
        metadata['aggDivsPSGrowthAVG'] = aggpsdivgravg

        #agg ps + total avg
        # aggbotnpsdivsmin = (tdivsmin + aggpsdivmin) / 2
        # aggbotnpsdivsmax = (tdivsmax + aggpsdivmax) / 2
        # aggbotnpsdivsavg = (tdivsavg + aggpsdivavg) / 2

        aggbotnpsdivsgrmin = (tdivsgrmin + aggpsdivgrmin) / 2
        aggbotnpsdivsgrmax = (tdivsgrmax + aggpsdivgrmax) / 2
        aggbotnpsdivsgravg = (tdivsgravg + aggpsdivgravg) / 2

        metadata['aggDivsGrowthLow'] = aggbotnpsdivsgrmin
        metadata['aggDivsGrowthHigh'] = aggbotnpsdivsgrmax
        metadata['aggDivsGrowthAVG'] = aggbotnpsdivsgravg

        #payout ratio min max avg
        prlist = divdf['payoutRatio'].tolist()
        prmin = nan_strip_min(prlist)
        prmax = nan_strip_max(prlist)
        pravg = IQR_Mean(prlist)
        pravgint = zeroIntegrity(prlist)
        pravgnz = IQR_MeanNZ(prlist)

        metadata['payoutRatioLow'] = prmin
        metadata['payoutRatioHigh'] = prmax
        metadata['payoutRatioAVG'] = pravg
        metadata['payoutRatioAVGintegrity'] = pravgint
        metadata['payoutRatioAVGnz'] = pravgnz

        #fcfpayratio  min max avg
        fcfprlist = divdf['fcfPayoutRatio'].tolist()
        fcfprmin = nan_strip_min(fcfprlist)
        fcfprmax = nan_strip_max(fcfprlist)
        fcfpravg = IQR_Mean(fcfprlist)
        fcfpravgint = zeroIntegrity(fcfprlist)
        fcfpravgnz = IQR_MeanNZ(fcfprlist)

        metadata['fcfPayoutRatioLow'] = fcfprmin
        metadata['fcfPayoutRatioHigh'] = fcfprmax
        metadata['fcfPayoutRatioAVG'] = fcfpravg
        metadata['fcfPayoutRatioAVGintegrity'] = fcfpravgint
        metadata['fcfPayoutRatioAVGnz'] = fcfpravgnz

        #ffo payratio  min max avg
        ffoprlist = divdf['ffoPayoutRatio'].tolist()
        ffoprmin = nan_strip_min(ffoprlist)
        ffoprmax = nan_strip_max(ffoprlist)
        ffopravg = IQR_Mean(ffoprlist)
        ffopravgint = zeroIntegrity(ffoprlist)
        ffopravgnz = IQR_MeanNZ(ffoprlist)

        metadata['ffoPayoutRatioLow'] = ffoprmin
        metadata['ffoPayoutRatioHigh'] = ffoprmax
        metadata['ffoPayoutRatioAVG'] = ffopravg
        metadata['ffoPayoutRatioAVGintegrity'] = ffopravgint
        metadata['ffoPayoutRatioAVGnz'] = ffopravgnz

        #roc any payments
        rocpscountlist = divdf['ROCperShare'].tolist()
        rocpshowmanyyears = count_nonzeroes(rocpscountlist)
        # rocpsmin = nan_strip_min(ffoprlist)
        # ffoprmax = nan_strip_max(ffoprlist)
        rocpsavg = IQR_Mean(rocpscountlist)

        metadata['ROCpsAVG'] = rocpsavg
        metadata['numYearsROCpaid'] = rocpshowmanyyears

        #roic min max avg
        roiclist = effdf['roic'].tolist()
        roicmin = nan_strip_min(roiclist)
        roicmax = nan_strip_max(roiclist)
        roicavg = IQR_Mean(roiclist)
        
        metadata['roicLow'] = roicmin
        metadata['roicHigh'] = roicmax
        metadata['roicAVG'] = roicavg

        #adjroic min max avg
        aroiclist = effdf['adjRoic'].tolist()
        aroicmin = nan_strip_min(aroiclist)
        aroicmax = nan_strip_max(aroiclist)
        aroicavg = IQR_Mean(aroiclist)

        metadata['aroicLow'] = aroicmin
        metadata['aroicHigh'] = aroicmax
        metadata['aroicAVG'] = aroicavg

        #rep adj roic min max avg
        raroiclist = effdf['reportedAdjRoic'].tolist()
        raroicmin = nan_strip_min(raroiclist)
        raroicmax = nan_strip_max(raroiclist)
        raroicavg = IQR_Mean(raroiclist)

        metadata['raroicLow'] = raroicmin
        metadata['raroicHigh'] = raroicmax
        metadata['raroicAVG'] = raroicavg

        #agg adj roic
        aggadjroicmin = (aroicmin + raroicmin) / 2
        aggadjroicmax = (aroicmax + raroicmax) / 2
        aggadjroicavg = (aroicavg + raroicavg) / 2

        metadata['aggaroicLow'] = aggadjroicmin
        metadata['aggaroicHigh'] = aggadjroicmax
        metadata['aggaroicAVG'] = aggadjroicavg

        #calc roce min max avg
        crocelist = effdf['calculatedRoce'].tolist()
        crocemin = nan_strip_min(crocelist)
        crocemax = nan_strip_max(crocelist)
        croceavg = IQR_Mean(crocelist)

        metadata['croceLow'] = crocemin
        metadata['croceHigh'] = crocemax
        metadata['croceAVG'] = croceavg

        #rep roce min max avg
        rrocelist = effdf['reportedRoce'].tolist()
        rrocemin = nan_strip_min(rrocelist)
        rrocemax = nan_strip_max(rrocelist)
        rroceavg = IQR_Mean(rrocelist)

        metadata['rroceLow'] = rrocemin
        metadata['rroceHigh'] = rrocemax
        metadata['rroceAVG'] = rroceavg

        #agg calc rep roce
        aggrocemin = (crocemin + rrocemin) / 2
        aggrocemax = (crocemax + rrocemax) / 2
        aggroceavg = (croceavg + rroceavg) / 2

        metadata['aggroceLow'] = aggrocemin
        metadata['aggroceHigh'] = aggrocemax
        metadata['aggroceAVG'] = aggroceavg

        #calc book value min max avg
        cbvlist = effdf['calcBookValue'].tolist()
        cbvmin = nan_strip_min(cbvlist)
        # cbvmax = nan_strip_max(cbvlist)
        cbvavg = IQR_Mean(cbvlist)

        metadata['calcBookValueLow'] = cbvmin
        metadata['calcBookValueAVG'] = cbvavg

        #calc book gr min max avg
        cbvgrlist = effdf['calcBookValueGrowthRate'].tolist()
        # cbvgrmin = nan_strip_min(cbvgrlist)
        # cbvgrmax = nan_strip_max(cbvgrlist)
        cbvgravg = IQR_Mean(cbvgrlist)
        cbvgravgint = zeroIntegrity(cbvgrlist)
        cbvgravgnz = IQR_MeanNZ(cbvgrlist)

        metadata['calcBookValueGrowthAVG'] = cbvgravg
        metadata['calcBookValueGrowthAVGintegrity'] = cbvgravgint
        metadata['calcBookValueGrowthAVGnz'] = cbvgravgnz

        #rep bv min max avg
        rbvlist = effdf['reportedBookValue'].tolist()
        rbvmin = nan_strip_min(rbvlist)
        # rbvmax = nan_strip_max(rbvlist)
        rbvavg = IQR_Mean(rbvlist)

        metadata['repBookValueLow'] = rbvmin
        metadata['repBookValueAVG'] = rbvavg

        #rep bv gr min max avg
        rbvgrlist = effdf['reportedBookValueGrowthRate'].tolist()
        # rbvgrmin = nan_strip_min(rbvgrlist)
        # rbvgrmax = nan_strip_max(rbvgrlist)
        rbvgravg = IQR_Mean(rbvgrlist)
        rbvgravgint = zeroIntegrity(rbvgrlist)
        rbvgravgnz = IQR_MeanNZ(rbvgrlist)

        metadata['repBookValueGrowthAVG'] = rbvgravg
        metadata['repBookValueGrowthAVGintegrity'] = rbvgravgint
        metadata['repBookValueGrowthAVGnz'] = rbvgravgnz

        aggbvmin = (cbvmin + rbvmin) / 2
        aggbvavg = (cbvavg + rbvavg) / 2
        aggbvgravg = (cbvgravg + rbvgravg) / 2

        metadata['aggBookValueLow'] = aggbvmin
        metadata['aggBookValueAVG'] = aggbvavg
        metadata['aggBookValueGrowthAVG'] = aggbvgravg

        #nav min max avg
        navlist = effdf['nav'].tolist()
        # navmin = nan_strip_min(navlist)
        # navmax = nan_strip_max(navlist)
        navavg = IQR_Mean(navlist)

        metadata['navAVG'] = navavg
        
        #nav gr min max avg
        navgrlist = effdf['navGrowthRate'].tolist()
        # navgrmin = nan_strip_min(navgrlist)
        # navgrmax = nan_strip_max(navgrlist)
        navgravg = IQR_Mean(navgrlist)

        metadata['navGrowthAVG'] = navgravg

        if pd.isnull(cdpslatest):
            metadata['calcDivYieldLatest'] = 0
        else:
            metadata['calcDivYieldLatest'] = cdpslatest / pricelatest * 100

        if pd.isnull(cdpsavg):
            metadata['calcDivYieldAVG'] = 0
        else:
            metadata['calcDivYieldAVG'] = cdpsavg / priceavg * 100
        
        if pd.isnull(dpslatest):
            metadata['repDivYieldLatest'] = 0
        else:
            metadata['repDivYieldLatest'] = dpslatest / pricelatest * 100
        
        if pd.isnull(dpsavg):
            metadata['repDivYieldAVG'] = 0
        else:
            metadata['repDivYieldAVG'] = dpsavg / priceavg * 100
        
    except Exception as err:
        print('full analysis error: ')
        print(err)
    finally:
        return metadata

def sectorFillMetadata(sector):
    #Need to decide if we remove old records, or just add new records, latestyear and any stat changes will be only distinguishing between different
    #rows of data
    #i believe we should save a snapshot, wipe, fill again: keep one for current records, one for trend data analysis later
    tickerq = 'SELECT DISTINCT Ticker \
                FROM Mega \
                WHERE Sector LIKE \'' + sector + '\''
    tickerfetch = print_DB(tickerq, 'return')['Ticker']
    length1 = len(tickerfetch)
    n = 1

    for x in tickerfetch:
        # print('Working on ' + x)
        try:
            print(str(round(n/length1,4)*100) + '% complete!')
            faTable = full_analysis(income_reading(x), balanceSheet_reading(x), cashFlow_reading(x), dividend_reading(x), efficiency_reading(x))
            print('Table made for: ' + x)
            uploadToDB(faTable,'Metadata')
            n += 1
        except Exception as err:
            print('sector fill metadata err')
            print(err)
            continue

def fullFillMetadata():
    try:
        getsectors = 'SELECT DISTINCT Sector FROM Mega;'
        sectors = print_DB(getsectors, 'return')
        for x in sectors['Sector']:
            sectorFillMetadata(x)
    except Exception as err:
        print('full fill metadata')
        print(err)

# fullFillMetadata()

#luke to do
# updateOrFillMetadata fills metadata now. we need a function to backup metadata, then just rewrite it from scratch
# after this first backup is done
#Luke Need to update this to compare each row, probably based on ticker, and only insert if the row contains differences along any column
#instead of a delete function, luke, try to combine the above copy description with a copy and replace function. could cut run time down?
#either you copy what you can, delete, refill totally.
#or, get all tickers, then iterate thru each ticker row, compare to backup, if same, next, if diff, add row to backup, 
#then clear from metadata, then fill metadata with it 
#i'm learning towards first one. beacuse metadata fills from mega. mega gets updated. now you check backup, copy, delete, refill metadata with new mega data
#streamlines it
# we also need a function that checks differences between what is in metadata and what is just generated from mega
# if different, original is snapshotted to backup DB
# if same, new one is dropped and loop continues. I think that's how to do it.
def copyMD():
    try:
        copyit = 'INSERT INTO Metadata_Backup SELECT * FROM Metadata;'
        conn = sql.connect(db_path)
        query = conn.cursor()
        query.execute(copyit)
        conn.commit()
        query.close()
        conn.close()
    except Exception as err:
        print('copy MD erro')
        print(err)

# copyMD()

print_DB('SELECT * FROM Metadata_Backup;', 'print')