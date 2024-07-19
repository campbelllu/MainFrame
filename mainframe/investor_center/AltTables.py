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
#going to have to manually review all of these rankings, to verify the integrity of rankings is what our company stands by #luke
#



#############################################################################
#luke here is where we start filling other tables 
#############################################################################
def rank_Growth(): 
    try:
        tickergrab = 'SELECT Ticker as ticker, Sector FROM Metadata'
        tickers = print_DB(tickergrab, 'return')
        tickersdict = tickers.set_index('ticker')['Sector'].to_dict()
        length1 = len(tickersdict)
        n = 1
        
        for x in tickers['ticker']:
            try:
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf = pd.DataFrame()
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = tickersdict[x]
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divgrowth_rating(x)
                divpay = uploaddf['divpay'] = divspaid_rating(x)
                shares = uploaddf['shares'] = shares_rating(x)
                cf = uploaddf['cf'] = cf_rating(x)
                bv = uploaddf['bv'] = bvnav_rating(x)
                equity = uploaddf['equity'] = equity_rating(x)
                debt = uploaddf['debt'] = debt_rating(x)
                fcfm = uploaddf['fcfm'] = fcfm_rating(x)
                fcf = uploaddf['fcf'] = fcf_rating(x)
                ffo = uploaddf['ffo'] = ffo_rating(x)
                ni = uploaddf['ni'] = ni_rating(x)
                rev = uploaddf['rev'] = growth_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 1
                roicv = 1
                rocv = 0
                ffopov = 0
                pov = 0
                divgrv = 0
                divpayv = 0
                sharesv = 0
                cfv = 1
                bvv = 0
                equityv = 1
                debtv = 0
                fcfmv = 1
                fcfv = 1
                ffov = 0
                niv = 1
                revv = 5
                yieldv = 0

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (equity) + (cf)  + (roic) + (roce))

                maxscore = 40
                uploaddf['maxplainscore'] = maxscore
                uploaddf['plainscore'] = justscore

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'Growth_Ranking')
                n += 1
            except Exception as err:
                print('rank growth error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank growth error: ')
        print(err)

def rank_QualNonDivPayers():
    try:
        tickergrab = 'SELECT Ticker as ticker, Sector FROM Sector_Rankings WHERE divpay = -1'
        tickers = print_DB(tickergrab, 'return')
        # tickergrab = 'SELECT Ticker as ticker, Sector FROM Metadata'
        # tickers = print_DB(tickergrab, 'return')
        tickersdict = tickers.set_index('ticker')['Sector'].to_dict()
        length1 = len(tickersdict)
        # time1 = time.time()
        n = 1
        
        for x in tickers['ticker']:
            try:
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf = pd.DataFrame()
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = tickersdict[x]
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divgrowth_rating(x)
                divpay = uploaddf['divpay'] = divspaid_rating(x)
                shares = uploaddf['shares'] = shares_rating(x)
                cf = uploaddf['cf'] = cf_rating(x)
                bv = uploaddf['bv'] = bvnav_rating(x)
                equity = uploaddf['equity'] = equity_rating(x)
                debt = uploaddf['debt'] = debt_rating(x)
                fcfm = uploaddf['fcfm'] = fcfm_rating(x)
                fcf = uploaddf['fcf'] = fcf_rating(x)
                ffo = uploaddf['ffo'] = ffo_rating(x)
                ni = uploaddf['ni'] = ni_rating(x)
                rev = uploaddf['rev'] = growth_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 5
                rocv = 0
                ffopov = 0
                pov = 0
                divgrv = 0
                divpayv = 0
                sharesv = 1
                cfv = 5
                bvv = 3
                equityv = 5
                debtv = 1
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (bv) + (debt) + (equity) + (cf) + (shares) + (roic) + (roce))

                maxscore = 55
                uploaddf['maxplainscore'] = maxscore
                uploaddf['plainscore'] = justscore

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'QualNonDivPayers_Ranking')
                n += 1
            except Exception as err:
                print('rank qual non div payers error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank qual non div payers error: ')
        print(err)

# rank_Growth()
# rank_QualNonDivPayers() 

#Get the mean of sector scores, return list of tickers above that value
def investableUniverse(sector):
    try:
        avgpull = 'SELECT avg(score) as avg, max(score), min(score) FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\''
        avgdf = print_DB(avgpull, 'return')
        avg = avgdf['avg'][0]
        invUni = 'SELECT * FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\' AND score >= ' + str(avg) + ' ORDER BY score DESC'
        invUnidf = print_DB(invUni, 'return')
    
    except Exception as err:
        print('investable uni error: ')
        print(err)
    finally:
        return invUnidf

# investableUniverse('E')

#############################################################################
#luke here we start filling investable universe from notes sheet
#############################################################################
def LSMats(): 
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, netCashFlowAVG, operatingCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equitygr, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG ELSE raroicAVG END roicavg, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roceavg \
                    FROM Metadata \
                    WHERE Sector LIKE \'Basic Materials\' \
                    AND years >= 1 \
                    AND revGrowthAVG >= 0 \
                    AND netIncomeGrowthAVG >= 3 \
                    AND equitygr >= 0 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowAVG > 0 \
                    AND divgr >= 6 \
                    AND payoutRatioAVG <= 0.5 \
                    AND roicavg > 5 \
                    AND roceavg > 5 \
                    ORDER BY divgr;'
                    
        sqldf = print_DB(matspull, 'return')
        print(sqldf)
        #screening targets
        # Ticker    years     revgr       nigr  payoutRatioAVG  netCashFlowAVG  operatingCashFlowAVG  equitygr      divgr   roicavg    roceavg
        # 0    NUE     18  2.625312  10.085268        0.433444    2.014189e+08          1.715804e+09  5.590830   0.950187  9.209051  12.263205
        # 1   STLD     18  4.563829   4.415330        0.207457    1.110677e+08          7.234860e+08  8.801051  11.681113  7.843229  14.992343
        # 2     RS     17  5.015402   3.829977        0.178590    1.103483e+07          6.411757e+08  9.418193  17.718853  9.121950  12.131660
        # 3    NEM     18  0.655908  13.195627        0.147077    1.930000e+08          2.648077e+09  0.112810  20.960141  3.464378   4.572959
        #results from above:
        #   Ticker  years      revgr       nigr  payoutRatioAVG  netCashFlowAVG  operatingCashFlowAVG   equitygr      divgr    roicavg    roceavg
        # 0   HWKN     15   7.921215   4.962971        0.350206    6.669091e+05          3.689775e+07   8.906628   6.526646  10.400827  12.637140
        # 3   STLD     18   4.563829   4.415330        0.207457    1.110677e+08          7.234860e+08   8.801051  11.681113   7.843229  14.992343
        # 4   UFPI     16  13.809333  25.466438        0.169407    6.471333e+06          1.308264e+08  11.629191  11.687335   9.462612  10.677567
        # 5     RS     17   5.015402   3.829977        0.178590    1.103483e+07          6.411757e+08   9.418193  17.718853   9.121950  12.131660
        

        # tickerslist = sqldf['Ticker'].tolist()
        # # checklist = invunidf['Ticker'].tolist()
        # # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in tickerslist: #qualifiedtickers
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)        
    except Exception as err:
        print('LSMats error: ')
        print(err)
    # finally:
        # csv.simple_saveDF_to_csv('',themats,'z-LSMats', False)
        # return themats
    
# LSMats()
        
def LSComms(): 
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, netCashFlowAVG, operatingCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Communication Services\' \
                    AND TICKER IN (\'GOOGL\', \'META\', \'NFLX\') \
                    ORDER BY divgr;'
                    
                    # AND years >= 5 \
                    # AND revGrowthAVG >= 0 \
                    # AND netIncomeGrowthAVG >= 0 \
                    # AND divgr >= 0 AND divgr < 60\
                    # AND payoutRatioAVG <= 0.9 \
                    # AND equity >= 0 \
                    # AND operatingCashFlowAVG > 0 \
                    # AND netCashFlowAVG > 0 \
                    # AND roic > 5 \
                    # AND roce > 5 \

                    #screening targets
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  netCashFlowAVG  operatingCashFlowAVG     equity       divgr       roic       roce
                    # 0   META     14  47.335342  37.976751        0.000000    1.533636e+08          1.840508e+10  24.041229         nan  17.842301  17.869286
                    # 1  GOOGL     12  16.515023  16.308754        0.000240    8.296250e+08          5.796967e+10  13.143930 -100.000000  19.730637  20.391842
                    # 2      T     18   1.231327   2.633111        0.702355    5.810769e+08          3.639192e+10   3.952106    2.157714   9.648406  10.361199
                    # 3     VZ     17   3.357788 -13.410203        0.657019   -5.953077e+08          3.384829e+10   9.666178    2.586280  13.408076  14.311030
                    #actual screen
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  netCashFlowAVG  operatingCashFlowAVG     equity      divgr       roic       roce
                    # 0   NTES     17  16.327206  22.105606        0.198972    1.573337e+07          1.214019e+09  26.167256   5.154560  22.976737  22.594944
                    # 1   CABO     12   6.224846   2.479315        0.228958    2.829000e+06          3.930389e+08   7.040326  11.081614  17.981284  18.949085
    
                    
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
    except Exception as err:
        print('LSComms error: ')
        print(err)          

# LSComms()

def LSEnergy(): 
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, \
                    repsAVG as repsAVG, repsGrowthAVG as repsGRAvg, cepsAVG as cepsAVG, cepsGrowthAVG as cepsGRAVG, \
                    payoutRatioAVG, operatingCashFlowAVG, netCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    debtGrowthAVG, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Ticker IN ( \'TXN\', \'ADI\',\'MCHP\') \
                    ORDER BY Ticker;'

                    # \'UFPI\', \'PH\', \'FAST\', \'AAON\', \'FIX\', \'WSO\', \'ETN\'
                    # Sector LIKE \'Energy\' \
                    # AND years >= 10 \
                    # AND divgr >= 4 \
                    # AND payoutRatioAVG <= 0.9 \
                    # AND operatingCashFlowAVG > 0 \
                    # AND equity >= 2 \
                    # AND roic > 15 \
                    # AND roce > 15 \

                    #unneeded screens
                    #  divgr <= 30 \
                    # AND netCashFlowAVG > 0 \
                    # AND revGrowthAVG >= 0 \
                    # AND netIncomeGrowthAVG >= 0 \
                    #initial
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG    equity      divgr       roic       roce
                    # 0    CVX     17  -4.591927 -15.175337        0.383902          2.960193e+10   -1.147769e+09  5.912741   6.242237  11.466649  12.525441
                    # 1    EOG     18  29.641039  -0.779903        0.099695          5.260627e+09    3.922576e+08       nan  14.501993  10.553666  14.424227
                    # 2    PSX     15  -2.271819 -15.748739        0.158731          4.845786e+09   -1.333333e+07  0.684323  12.609659  17.878898  17.992002
                    # 3    XOM     18   1.681971 -10.319898        0.377031          4.357575e+10   -1.946154e+08  2.361327   4.630759  17.360837  17.890969
                    #screen
                    #   Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity       divgr       roic       roce
                    # 0   ARLP     16   6.387910  13.179572        0.148237          5.926950e+08   -2.178444e+07   9.860818   17.060478  23.576827  36.690378 -mlp beware
                    # 1    NOG     15  26.058289  68.351471        0.133021          2.156712e+08    2.635051e+06  11.069820  239.722663  17.142036  18.888567
                    # 2    XOM     18   1.681971 -10.319898        0.377031          4.357575e+10   -1.946154e+08   2.361327    4.630759  17.360837  17.890969
       
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     # uploadToDB(sqldf2,'Investable_Universe')
        #     print(sqldf2)
    except Exception as err:
        print('LSEnergy error: ')
        print(err)       

# LSEnergy()

def LSFin():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, operatingCashFlowAVG, netCashFlowAVG, \
                    CASE WHEN repBookValueGrowthAVG > calcBookValueGrowthAVG THEN repBookValueGrowthAVG ELSE calcBookValueGrowthAVG END bv, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN calcDivsPerShareGrowthAVG IS NULL THEN repDivsPerShareGrowthAVG END divgr2, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Financial Services\';'
       
        sqldf = print_DB(matspull, 'return')
        # print(sqldf.to_string())
        # df = df[df.line_race != 0]
        sqldf2 = sqldf[sqldf.divgr2.notnull()]
        sqldf = sqldf[sqldf.divgr.notnull()] 
        sqldf2['divgr'] = sqldf2['divgr2']
        # df_filled = df_filled.drop('Units',axis=1)
        sqldf = sqldf.drop('divgr2', axis=1)
        sqldf2 = sqldf2.drop('divgr2', axis=1)
        # print(sqldf)
        # print(sqldf2)
        sqldf = pd.concat([sqldf, sqldf2], axis = 0)
        # print(sqldf.to_string())
        sqldf = sqldf[sqldf.roic.notnull()]
        
        #luke here gotta re filter it looks like. weird null value pulls. wierd finance. despise this secgtor lol

        # AND years >= 5 \
        sqldf = sqldf[sqldf.years >= 10]
        # AND netIncomeGrowthAVG >= 3 \
        sqldf = sqldf[sqldf.nigr >= 0]
        # AND (divgr >= 8 AND divgr <= 30) OR (divgr2 >= 8) \
        sqldf = sqldf[sqldf.divgr.between(8,20)]
        # AND payoutRatioAVG <= 0.5 \
        sqldf = sqldf[sqldf.payoutRatioAVG <= 0.5]
        # AND equity >= 3 \
        sqldf = sqldf[sqldf.equity >= 3.5]
        # AND operatingCashFlowAVG > 0 \
        sqldf = sqldf[sqldf.operatingCashFlowAVG >= 1000000000]
        # AND netCashFlowAVG > 0 \
        sqldf = sqldf[sqldf.netCashFlowAVG >= 100000000]
        # AND roic > 10 \
        sqldf = sqldf[sqldf.roic >= 10]
        # AND roce > 10 \
        sqldf = sqldf[sqldf.roce >= 10]
        # AND (revgr IS NULL OR revgr > 0) \
        todrop = ['ARCC', 'BBDC', 'BCSF', 'BKCC', 'BXSL', 'CCAP', 'CGBD', 'FCRD', 'CSWC', 'GAIN', 'GBDC', 
                                            'GECC', 'GLAD', 'GSBD', 'HRZN', 'ICMB', 'LRFC', 'MFIC', 'MAIN', 'MRCC', 'MSDL', 'NCDL', 
                                            'NMFC', 'OBDC', 'OBDE', 'OCSL', 'OFS', 'OXSQ', 'PFLT', 'PFX', 'PNNT', 'PSBD', 'PSEC', 
                                            'PTMN', 'RAND', 'RWAY', 'SAR', 'SCM', 'SLRC', 'SSSS', 'TCPC', 'TPVG', 'TRIN', 'TSLX', 
                                            'WHF', 'HTGC', 'CION', 'FDUS', 'FSK']
        sqldf = sqldf[~sqldf.Ticker.isin(todrop)]
        # sqldf = sqldf[sqldf.revgr >= 0 | sqldf.revgr.isnull()]
        # AND bv >= 3 OR bv IS NULL \
        # sqldf['bv'] = sqldf['bv'].fillna(10)
        
        sqldf = sqldf.sort_values(by=['divgr'], ascending=False)
        print(sqldf.to_string())
        print(sqldf.shape)
        #unused
        # AND (divgr >= 0 AND divgr <= 30) OR (divgr2 >= 0) \
        # AND revgr > 2 \
        # AND netIncomeGrowthAVG <= 35 \
        # AND equity <= 20 \
        # AND Ticker NOT IN (\'ARCC\', \'BBDC\', \'BCSF\', \'BKCC\', \'BXSL\', \'CCAP\', \'CGBD\', \'FCRD\', \'CSWC\', \'GAIN\', \'GBDC\', \
        # \'GECC\', \'GLAD\', \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \
        # \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \
        # \'SCM\', \'SLRC\', \'SSSS\', \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\') 

        #ini screen
                    #   Ticker    years     revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG         bv     equity      divgr       roic       roce
                    # 0       V     18  11.782065  13.951760        0.192225          6.205125e+09    1.566154e+08        nan   5.271089        nan  19.211963  19.534281
                    # 1      MS     18   0.000000  -0.148192        0.284637          5.225062e+09    2.008750e+09   3.473520   3.626883  17.606352   6.349572   7.802749
                    # 2      MA     18  12.455496   0.000000        0.220132          4.195150e+09    8.645765e+08   4.536454   5.868946  14.512999  29.242511  45.672711
                    # 3     BLK     18  -0.007121   7.135477        0.439311          3.104143e+09    5.544615e+08   5.248478   3.454758  12.865347  11.986603  11.986603
                    # 4     JPM     17   2.600539   9.381052        0.321679          3.194575e+10    2.878083e+09   6.084620   3.909434  11.572023  10.508470  10.508470
                    # 5      GS     17        nan -18.160193        0.205881          5.585571e+09    7.563500e+09   7.144024   5.992205  17.568776   4.195360   9.492229
                    # 6     AXP     18   0.897985   1.415459        0.199070          9.634600e+09    3.587000e+09   7.263925   3.431624  10.370913  27.296490  27.296490
                    # 7    TROW     18   0.345987  15.226549        0.439817          1.159050e+09    1.220083e+08  10.941966  11.569203  11.910636  23.768405  23.768405
                    # 8     DFS     18        nan   1.585452        0.154129          4.362713e+09    1.179338e+09  12.256109   3.520530  16.556411  21.258176  21.258176
                    # 9    SCHW     18   9.540676  12.822463        0.298110          1.630538e+09    3.536214e+09  13.980383  14.609661   8.050996  11.682316  11.682316
                    # 10   SPGI     18   6.269991   2.639047        0.289784          1.512441e+09    3.451868e+08  17.193617  14.629222  10.265943  36.527934  80.101654
                    # 11   MSCI     17   9.260249  16.239868        0.212577          3.845744e+08    3.945708e+07  23.110777  15.839196  26.991692  13.766375   5.756975
                    #used screen
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG         bv     equity      divgr       roic       roce
                    # 1       V     18  11.782065  13.951760        0.192225          6.205125e+09    1.566154e+08        nan   5.271089  17.626413  19.211963  19.534281
                    # 68    DFS     18        nan   1.585452        0.154129          4.362713e+09    1.179338e+09  12.256109   3.520530  16.556411  21.258176  21.258176
                    # 3      MA     18  12.455496   0.000000        0.220132          4.195150e+09    8.645765e+08   4.536454   5.868946  14.512999  29.242511  45.672711
                    # 71   TROW     18   0.345987  15.226549        0.439817          1.159050e+09    1.220083e+08  10.941966  11.569203  11.910636  23.768405  23.768405
                    # 2     JPM     17   2.600539   9.381052        0.321679          3.194575e+10    2.878083e+09   6.084620   3.909434  11.572023  10.508470  10.508470
                    # 10   SPGI     18   6.269991   2.639047        0.289784          1.512441e+09    3.451868e+08  17.193617  14.629222  10.265943  36.527934  80.101654
                    # 15   SCHW     18   9.540676  12.822463        0.298110          1.630538e+09    3.536214e+09  13.980383  14.609661   8.050996  11.682316  11.682316
        

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSFin error: ')
        print(err)    

# LSFin()

def LSBDC():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG as po, \
                        netCashFlowAVG as netcfAmount, netCashFlowGrowthAVG as netcfGRAVG, \
                        CASE WHEN repBookValueGrowthAVG > calcBookValueGrowthAVG THEN repBookValueGrowthAVG ELSE calcBookValueGrowthAVG END bv, \
                        CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                        CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                        CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                        CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                        FROM Metadata \
                        WHERE Ticker IN (\'ARCC\', \'BBDC\', \'BCSF\', \'BKCC\', \'BXSL\', \'CCAP\', \'CGBD\', \'FCRD\', \'CSWC\', \'GAIN\', \
                                         \'GBDC\', \'GECC\', \'GLAD\', \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \
                                         \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \
                                         \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \'SCM\', \'SLRC\', \'SSSS\', \
                                         \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\') \
                        AND years >= 1 \
                        AND nigr >= -1 \
                        AND divgr >= -10 AND divgr < 75 \
                        AND payoutRatioAVG <= 0.9 \
                        AND netcfGRAVG >= 0 \
                        AND equity >= 0 \
                        AND roic > 0 \
                        AND roce > 0 \
                        ORDER BY equity;'

                        # AND revgr >= -1 \
                        
                        # AND opcfAmount > 0 \
                        # AND opcfGRAVG >= 0 \
                        # AND netcfAmount > 0 \
                        # AND netcfGRAVG >= -25 \
                        # AND bv >= 0 \
                        # 
        
        sqldf = print_DB(matspull, 'return')
        print(sqldf)
        # csv.simple_saveDF_to_csv('',print_DB(bdcRanks, 'return'), 'z-BDClist', False)
    except Exception as err:
        print('LSBDC error: ')
        print(err)   
        # operatingCashFlowAVG as opcfAmount, operatingCashFlowGrowthAVG as opcfGRAVG, \
        #                 financingCashFlowAVG as fincfAmount, financingCashFlowGrowthAVG as fincfGRAVG, \
        #                 investingCashFlowAVG as invcfAmount, investingCashFlowGrowthAVG as invcfGRAVG, \

# LSBDC()

def LSInd():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, operatingCashFlowAVG, netCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Industrials\' \
                    AND years >= 5 \
                    AND revGrowthAVG >= 0 \
                    AND netIncomeGrowthAVG >= 0 \
                    AND divgr >= 10 AND divgr <= 20 \
                    AND payoutRatioAVG <= 0.75 \
                    AND equity >= 1 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowAVG > 0 \
                    AND roic > 10 \
                    AND roce > 10 \
                    ORDER BY Ticker;'
                
            #init
            # Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity      divgr       roic       roce
            # 0    CAT     18   1.641555 -15.957918        0.330153          6.583000e+09    5.275385e+08   5.994098   6.009861  11.471140  35.913091
            # 1     WM     18   2.951983  -0.890013        0.538505          2.768714e+09   -4.350000e+07   0.531524   6.784685  22.062362  22.530457
            # 2    RTX     18   4.441660   8.686486        0.349052          6.623875e+09    3.371333e+08   3.123065   7.483888  18.275310  18.326759
            # 3     GE     18  -4.254855  18.906530        0.312470          2.169244e+10    1.565727e+09   0.667138   7.704522   9.480665   9.572312
            # 4    RSG     18   3.193927  -0.021190        0.536223          1.807783e+09    8.092857e+06        nan   7.759505  10.563221  10.672990
            # 5    NOC     17   2.920955   1.109682        0.273852          2.833867e+09    1.491538e+08  10.567245   9.593496  16.809136  26.058515
            # 6     GD     18   1.869071   1.631721        0.287132          3.173385e+09    1.496923e+08   6.568281  10.146197  15.065814  19.992949
            # 7    LMT     18   1.926400   4.113817        0.441893          5.247824e+09    3.023529e+07  -7.412228  10.500326  33.664914  99.229021
            # 8     DE     18  10.104561   9.981592        0.248744          2.778964e+09   -4.218182e+06   5.977654  11.622701   8.459864  30.365365
            #run
            #   Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity      divgr       roic       roce
            # 0     AME     17  11.669495  13.566476        0.139801          7.321566e+08    2.792631e+07  13.274516  14.546022  11.520536  16.907232
            # 1     DLB     17   4.365741   3.925827        0.208562          3.502052e+08    4.820300e+07   6.161482  15.264467  12.114591  12.162470
            # 2    EXPO     16   4.756921   8.557933        0.282977          6.612708e+07    1.575367e+07   6.586006  18.589796  19.456993  19.837206
            # 3      GD     18   1.869071   1.631721        0.287132          3.173385e+09    1.496923e+08   6.568281  10.146197  15.065814  19.992949
            # 4     HRI     17   8.754766  16.105328        0.006222          1.265007e+09    2.454915e+07   8.619919  13.848510  11.920595  11.615864
            # 5     IEX     17   5.451147   8.377064        0.326201          3.883606e+08    8.426858e+07   9.380938  12.052875  11.513216  16.967746
            # 6    POOL     17   6.931234  15.144808        0.331950          1.503296e+08    3.123385e+06   1.637345  16.854136  23.521539  46.736407
            # 7     SNA     17   2.616076   9.863874        0.296946          6.264688e+08    9.288889e+06   9.099957  14.112095  15.113566  18.911209
            # 8     SXI     14   4.084016   1.698475        0.124665          6.938155e+07    1.726467e+07   5.592689  13.136054  11.052315  13.706980
            # 9     WAB     17   8.578566  16.696298        0.078748          5.533072e+08    3.746909e+07   8.352241  11.560519  10.697280  12.647773
            # 10   WERN     17   1.793273   1.359433        0.255121          3.310144e+08    7.178889e+05  26.836940  14.153429  12.719533  13.279837
            # 11    WWD     17   4.858690   4.155718        0.149933          2.794669e+08    1.531769e+06  10.975194  10.112709  10.076212  13.660002
        
        
                   
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSInd error: ')
        print(err)    

# LSInd()

def LSTech():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, operatingCashFlowAVG, netCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Technology\' \
                    AND years >= 5 \
                    AND netIncomeGrowthAVG > -5 \
                    AND equity >= 1.5 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowAVG > 10000000 \
                    AND divgr >= 8 AND divgr <= 40 \
                    AND payoutRatioAVG <= 0.75 AND payoutRatioAVG >= 0 \
                    AND roic > 12 \
                    AND roce > 10 \
                    ORDER BY divgr;'

                    

        #  AND revGrowthAVG >= 4 \
        
        # init
        #   Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity       divgr       roic       roce
        # 0    AAPL     18   8.816089   6.581789        0.161836          5.399888e+10    2.430786e+09  -0.684364    8.732056  29.872809  36.495287
        # 1     ACN     17   3.695180  13.231359        0.395505          4.800244e+09    5.457945e+08  15.989917   10.730739  41.955634  43.043044
        # 2     ADI     17   5.889502   5.084997        0.627590          1.079013e+09    1.221677e+08   5.522134    9.542130  12.019164  12.163146
        # 3    AMAT     18   7.088549  34.033102        0.230050          2.361674e+09    3.620124e+08   1.287084    8.403995  20.089036  24.192929
        # 4     AMD     17   3.207412  22.172897        0.000000          5.361538e+07    4.445455e+07        nan         nan  11.539060  22.497147
        # 5    ANET     13  41.593335  47.165121        0.000000          4.496792e+08    5.465564e+07  32.273795         nan  22.112241  22.168602
        # 6    ASML     16  12.660632  16.708757        0.229989          2.764633e+09    4.426604e+08  11.523360   11.290233  20.811058  23.503372
        # 7    AVGO      9  12.677225  51.377072        0.568398          1.298238e+10    1.400000e+09  -0.593911   29.146302  12.969006  28.923214
        # 8    CSCO     17   2.623500   3.267293        0.435724          1.283707e+10    6.404706e+08   7.603257    9.680117  15.763935  20.175566
        # 9     IBM     18  -2.096716   3.703036        0.337966          1.702527e+10   -6.636923e+08   7.344961    8.916288  20.417317  61.815304
        # 10   INTC     18   1.533952  -6.968304        0.379032          1.714146e+10   -8.600000e+08        nan    6.115508  14.990948  18.068437
        # 11   INTU     17  11.572977  10.392048        0.212399          1.477615e+09    1.769231e+07  10.066996   13.639516  20.362582  23.679682
        # 12   KLAC     16  10.900095  11.488950        0.375356          8.921842e+08    1.914440e+08  11.875910   15.159376  18.103193  55.915187
        # 13   LRCX     16  20.845737  20.066094        0.123370          1.564338e+09    2.616656e+08  12.589839   31.974256  17.759093  27.180024
        # 14   MCHP     17  11.447419   0.877442        0.861432          8.870314e+08   -4.712064e+07        nan    1.025195  11.350981  13.742577
        # 15   MPWR     16  15.999371  24.766335        0.360900          9.693315e+07    1.654992e+07  20.919293   27.307130  12.722596  12.726359
        # 16   MRVL      6   8.922568 -27.040050       -0.230760          1.133294e+09    6.142350e+07   0.000000    0.019605  -2.652105  -3.326828
        # 17   MSFT     16   9.450247  15.781682        0.315768          3.193717e+10    5.213333e+08  18.639394   11.512707  22.720834  35.433912
        # 18     MU     16   3.769690  32.952306       -0.000943          3.696917e+09    4.301000e+08  10.015289  163.449913  12.185228  14.495693
        # 19   NVDA     18   8.321348  30.286784        0.054497          2.164909e+09    3.136199e+08  18.872270    8.210057  15.739399  19.671156
        # 20   NXPI     14   4.552677  -9.697391        0.038412          2.491000e+09    1.750000e+08   3.099695   35.183781  19.265443  19.464295
        # 21     ON     17   5.650164   5.999278        0.000000          6.041692e+08    5.193846e+07  10.686487         nan   6.923268  11.472216
        # 22   PANW     14  31.211709  -8.947647        0.000000          5.714248e+08    1.102403e+08   8.237812         nan   1.121241   1.121241
        # 23   QCOM     18   4.648874   0.581958        0.372119          5.952125e+09    4.318462e+08  10.602295    9.709177  18.447238  18.161972
        # 24   SWKS     17   7.972981  -1.816635        0.150324          9.560881e+08    1.190425e+08  13.850989   13.331944  19.046871  19.220033
        # 25    TSM     10   5.539021        nan             nan          2.655144e+10    3.551650e+09  14.023235   10.430306        nan        nan
        # 26    TXN     17  -0.588669   5.793732        0.503148          4.605267e+09    7.542857e+07   1.667329   14.372670  24.365203  36.644384
        #refined
        #  Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity      divgr       roic       roce
        # 0    MPWR     16  15.999371  24.766335        0.360900          9.693315e+07    1.654992e+07  20.919293  27.307130  12.722596  12.726359
        # 1      UI     15  15.434508  28.126452        0.043073          1.458879e+08    7.025333e+07  27.252817  25.857526  42.165026  52.496036
        # 2    LOGI     16   0.332295  13.273062        0.266094          2.523964e+08    7.873727e+07   7.868332  12.467254  15.509158  15.569094
        # 3     CDW     16   8.181141  22.570100        0.139957          6.351286e+08    7.466154e+07  35.115608  33.095935  13.285208  57.986013
        # 4    KLAC     16  10.900095  11.488950        0.375356          8.921842e+08    1.914440e+08  11.875910  15.159376  18.103193  55.915187
        # 5     APH     18  -0.021315   7.721365        0.158075          9.177279e+08    1.265639e+08  19.699803  11.450744  20.627810  23.783900
        # 6    SWKS     17   7.972981  -1.816635        0.150324          9.560881e+08    1.190425e+08  13.850989  13.331944  19.046871  19.220033
        # 7     ADI     17   5.889502   5.084997        0.627590          1.079013e+09    1.221677e+08   5.522134   9.542130  12.019164  12.163146
        # 8    INTU     17  11.572977  10.392048        0.212399          1.477615e+09    1.769231e+07  10.066996  13.639516  20.362582  23.679682
        # 9    LRCX     16  20.845737  20.066094        0.123370          1.564338e+09    2.616656e+08  12.589839  31.974256  17.759093  27.180024
        # 10   CTSH     18   9.243775  12.248982        0.030952          1.573747e+09    1.592833e+08  14.957784   9.749579  17.294141  19.140751
        # 11    TEL     18  -0.535326   5.794455        0.270866          2.100714e+09    3.241429e+08   4.677149   9.559963  13.462648  16.990405
        # 12   NVDA     18   8.321348  30.286784        0.054497          2.164909e+09    3.136199e+08  18.872270   8.210057  15.739399  19.671156
        # 13   ASML     16  12.660632  16.708757        0.229989          2.764633e+09    4.426604e+08  11.523360  11.290233  20.811058  23.503372
        # 14    TXN     17  -0.588669   5.793732        0.503148          4.605267e+09    7.542857e+07   1.667329  14.372670  24.365203  36.644384
        # 15    ACN     17   3.695180  13.231359        0.395505          4.800244e+09    5.457945e+08  15.989917  10.730739  41.955634  43.043044
        # 16   QCOM     18   4.648874   0.581958        0.372119          5.952125e+09    4.318462e+08  10.602295   9.709177  18.447238  18.161972
        # 17   CSCO     17   2.623500   3.267293        0.435724          1.283707e+10    6.404706e+08   7.603257   9.680117  15.763935  20.175566
        # 18   ORCL     17   2.065553   3.861761        0.210639          1.459892e+10    4.100000e+08   7.861781  13.029764  24.643717  24.643717
        # 19   MSFT     16   9.450247  15.781682        0.315768          3.193717e+10    5.213333e+08  18.639394  11.512707  22.720834  35.433912
                        
        sqldf = print_DB(matspull, 'return')
        print(sqldf)
        

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSTech error: ')
        print(err)    

# LSTech()

def LSP():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, \
                    operatingCashFlowAVG as opcfAmount, operatingCashFlowGrowthAVG as opcfGRAVG, netCashFlowAVG as netcfAmount, netCashFlowGrowthAVG as netcfGRAVG, \
                    CASE WHEN repBookValueGrowthAVG > calcBookValueGrowthAVG THEN repBookValueGrowthAVG ELSE calcBookValueGrowthAVG END bv, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Consumer Defensive\' \
                    AND years >= 5 \
                    AND revgr >= -1 \
                    AND nigr >= -15 \
                    AND opcfAmount > 0 \
                    AND opcfGRAVG >= 0 \
                    AND netcfAmount > 0 \
                    AND netcfGRAVG >= -25 \
                    AND equity >= 10 \
                    AND divgr >= -20 AND divgr < 21 \
                    AND payoutRatioAVG <= 0.75 \
                    AND roic > 10 \
                    AND roce > 20 \
                    ORDER BY roce;'

                    #init ::: AND Ticker IN (\'KR\', \'COST\', \'WMT\', \'SFM\', \'PG\', \'PEP\', \'KO\', \'CL\', \'KMB\', \'SYY\', \'ADM\', \'HSY\', \'GIS\', \'CHD\', \'HRL\') \
                    #      Ticker  years   revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     bv        equity      divgr       roic        roce
                    # 0     SFM     14  0.672284  15.954637        0.000000          3.146795e+08    2.114025e+07  15.321938  11.491161        nan  12.317866   23.113926
                    # 1    COST     17  8.450071  15.874480        0.266252          4.198385e+09    3.809231e+08  11.478007  12.379436 -16.610309  13.603188   20.822293
                    # 2     WMT     18  3.018433  -0.995369        0.375721          2.589423e+10    5.933846e+08        nan        nan   3.141014  11.889157   18.408654
                    # 3      CL     17  1.610136  -0.405310        0.623488          3.145000e+09    3.942857e+07  -6.261083  -3.470780   3.606261  29.956134  150.025664
                    # 4     SYY     17  0.382352   7.034560        0.582480          1.684833e+09   -5.579820e+07   2.745845   1.995446   4.163013  28.913539   31.237070
                    # 5     KMB     17  1.069345   0.899082        0.645072          2.849333e+09   -7.800000e+07        nan        nan   4.648064  57.850925  131.275858
                    # 6     GIS     17  0.300916   6.694189        0.526021          2.707709e+09    3.026667e+07   5.931027   5.617303   5.418652  24.700704   25.127948
                    # 7      KO     18  0.775930  -1.115576        0.692794          1.021915e+10    6.320000e+08        nan        nan   6.002045  14.836955   29.932706
                    # 8     PEP     17  2.318789   4.633028        0.588480          9.979692e+09    1.358417e+09   5.593741   4.998578   6.774506  14.873945   44.854359
                    # 9     ADM     17 -1.829961  -3.508348        0.304042          2.523667e+09   -4.515385e+07   3.348879   2.524214   7.319883   7.477781   10.433476
                    # 10     PG     17  1.715124   1.022159        0.579380          1.514814e+10   -1.405333e+08  -0.602753  -2.286862   7.482243  15.182172   18.537180
                    # 11    CHD     17  1.224504   8.081264        0.355999          6.863774e+08    3.699154e+07   8.810537   9.744301   8.155390  13.527249   19.075527
                    # 12    HSY     18  3.521175  10.867016        0.532020          1.111915e+09    9.934692e+06  21.346222  17.535345   9.044399  28.392922   58.372306
                    # 13    HRL     17  2.901532   7.761210        0.352526          9.323203e+08    3.088111e+07        nan        nan  11.336586  15.441286   16.273557
                    # 14     KR     18 -0.066847   2.600030        0.216080          3.649500e+09    1.737143e+08   9.939171   6.484384  14.059554   8.916643   25.422762
                    #yes
                    #  Ticker  years     revgr       nigr  payoutRatioAVG    opcfAmount  opcfGRAVG   netcfAmount  netcfGRAVG         bv     equity      divgr       roic       roce
                    # 0   COST     17  8.450071  15.874480        0.266252  4.198385e+09   6.478864  3.809231e+08  -23.844195  11.478007  12.379436 -16.610309  13.603188  20.822293
                    # 1     EL     15  7.089827  14.380978        0.336390  1.630862e+09   7.266475  1.350400e+08   -1.270493  32.189791  27.581459  17.765229  30.191299  28.530883
                    # 2    HSY     18  3.521175  10.867016        0.532020  1.111915e+09   3.083043  9.934692e+06   42.534879  21.346222  17.535345   9.044399  28.392922  58.372306
                   
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSP error: ')
        print(err)    

# LSP()

def LSRE(): #revise a little but otherwise golden.
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, ffoGrowthAVG as ffogr, reitepsAVG as eps, reitepsGrowthAVG as epsGR, \
                    ffoPayoutRatioAVG as ffopo, operatingCashFlowAVG as opcfAmount, operatingCashFlowGrowthAVG as opcfGRAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    (calcDivYieldAVG + repDivYieldAVG) / 2 as yieldAVG, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Ticker IN ( \'NSA\', \'PLD\', \'REXR\', \'TRNO\', \'EGP\') \
                    ORDER BY divgr DESC, ffogr DESC;'
        
                    # \'O\', \'ADC\', \'NNN\',
                    # WHERE Sector LIKE \'Real Estate\' \
                    # AND years >= 5 \
                    # AND revgr >= 0 \
                    # AND ffogr >= 5 \
                    # AND eps >= 1 \
                    # AND epsGR >= 0 \
                    # AND opcfAmount > 0 \
                    # AND opcfGRAVG >= 6 \
                    # AND equity > 3 \
                    # AND divgr >= -3 AND divgr <= 50 \
                    # AND ffopo <= 0.9 AND ffopo > 0 \
                    # AND yieldAVG > 0 \
                    # AND roic > 0 \
                    # AND roce > 0 \

                    # AND revGrowthAVG >= 0 \
                    # AND ffoGrowthAVG >= 1 \
                    # AND equity >= 0 \
                    # AND operatingCashFlowAVG > 0 \
                    # AND netCashFlowAVG > 0 \
                    # AND ffoPayoutRatioAVG <= 90 \
                    #init AND Ticker IN (\'O\', \'PLD\', \'STAG\', \'EGP\', \'REXR\', \'TRNO\', \'LAND\', \'FPI\', \'WY\', \'RYN\', \'WPC\', \'AMT\', \'DLR\', \'PSA\', \'VICI\', \'IRM\', \'FRT\', \'FR\', \'NNN\', \'ADC\') \
                    # Ticker  years      revgr       nigr      ffogr  reitepsAVG        po     ffopo    opcfAmount  opcfGRAVG   netcfAmount  netcfGRAVG         bv     equity      divgr       roic       roce  cYieldavg  rYieldavg
                # 0    STAG     14  17.044633  -4.672891  18.942035    1.751875  0.775602  0.897646  2.335600e+08  18.830450 -1.249125e+06  -13.827527   5.322461  20.361738  -0.462147   4.181835   4.181835   6.034279   6.088664
                # 1    LAND     14  27.301310  36.200495  53.239336    0.435799  3.210411  0.547829  1.044982e+07  24.608051  1.499941e+05   65.708462  18.099068  29.977541   0.553977   0.568420   0.568420   4.156289   3.770156
                # 2       O     17  11.139858   1.977330   9.495216    2.761982  1.821735  0.789246  6.649373e+08  12.919603  1.142438e+07   67.947507   2.305357  13.203644   2.821127   4.725368   4.725368   4.712625   4.896805
                # 3     FRT     17   5.519050  10.199265   5.101680    5.250925  1.202913  0.657902  3.690873e+08   6.954425  1.147125e+07   28.134541   4.328848   6.505314   2.887301  11.338018  11.338018   3.316554   3.299779
                # 4     NNN     17   8.810333  13.817769  12.808287    2.412025  1.102692  0.728694  3.988139e+08  10.418153 -1.648500e+06  -42.177200   0.090047   5.448021   2.961793   6.199792   6.199792   4.525120   4.526938
                # 5     FPI     13   9.501433  22.939135   7.687959    0.512156  0.597814  0.357860  9.588507e+06 -20.109146 -4.469333e+06    3.207090  -3.653778  27.128694   3.609124   2.433009   2.433009   3.065304   2.311055
                # 6     IRM     17   0.462294  -1.179094   5.754689    2.805197  1.649241  0.725218  6.836071e+08   6.390874  3.122400e+07    8.384818        nan        nan   3.689258   4.004123  15.680956   7.610774   6.731443
                # 7     WPC     17   7.994711  16.287523  12.097651    4.618143  1.427300  0.883796  5.157438e+08   6.514407  1.109273e+07   21.738059   0.511662   0.294825   3.751152   7.034948   7.034948   5.613932   5.577569
                # 8     EGP     16   8.477091  12.457961  11.932193    3.991044  1.323689  0.639679  1.287662e+08   6.820333  8.890909e+04  207.514753  11.146744  15.826327   3.965242   8.307110   8.307110   3.201940   3.156567
                # 9     DLR     16  15.420055  39.319976  17.088927    2.359779  1.657873  1.338220  1.054417e+09   9.609409  5.111455e+06   -8.621045   3.528066   8.569163   4.057466   5.268870   5.268870   4.417618   4.417618
                # 10    ADC     15  27.142147  14.332015  21.348636    2.156212  1.175616  0.917818  5.938388e+07  23.538417 -4.118838e+06  -64.451676  10.948915  34.442844   4.587622   5.763665   5.763665   4.150675   4.228155
                # 11    RYN     16   4.580407 -24.207416   8.572854    2.012773  0.889151  0.493709  2.771987e+08   2.107633 -1.979855e+07  -14.460932   8.152251   3.817619   4.704516   5.577871   9.979560   3.681747   3.725719
                # 12     WY     17  -0.790696 -12.318917   3.315262    1.744263  0.823045  0.431293  1.010333e+09   9.716964 -2.505714e+08  -11.444395  -3.072850  -2.779203   6.681926   5.842523  10.260059   3.476230   3.268174
                # 13     FR     15   4.643413  43.666775  18.294981    1.262556  0.677611  0.545931  1.908325e+08   8.537965  5.387111e+06   33.626571   7.985713   9.332528   7.753480   9.817753   9.817753   3.261596   2.313134
                # 14    PSA     18   5.251905   5.670954   5.112214    9.138806  0.816193  0.638420  1.616263e+09   4.940741 -4.703321e+07   40.946823  -1.805098  -1.646658   9.451960  14.555860  14.555860   2.950686   2.941176
                # 15   VICI      8  28.491854  18.305407  18.182911    1.509511  0.779243  0.775557  1.221966e+09  13.087972  3.927385e+08   67.707812   6.431061  24.509181   9.576433   7.815374   7.815374   4.953887   4.542089
                # 16    PLD     16  16.753735  34.854055  13.820046    3.102574  0.842441  0.614340  1.277009e+09  18.867865 -4.834400e+07   44.570194   1.030452   3.005580  10.053445   5.646996   5.646996   3.422233   3.367302
                # 17   TRNO     15  15.578849  24.053417  21.604003    1.533246  0.989600  0.719757  6.368967e+07  20.425449  1.438100e+07    6.476443  10.702281  16.865568  12.273021   3.284133   3.284133   3.324632   1.274749
                # 18   REXR     14  22.094937  30.458015  25.170835    1.677598  1.262340  0.590894  2.371625e+08  26.152239 -3.464750e+06  -23.249410  15.594463  37.985240  13.726380   2.626129   2.626129   2.073204   1.536900
                # 19    AMT     18  13.858538  10.236767  14.961015    4.790007  0.650294  0.295138  2.169801e+09  16.154024  2.220908e+07   61.627673   1.432079   0.040212  19.562929   4.654488  14.343723   1.869859   1.307939
                #run
                # Ticker  years      revgr      ffogr        eps      epsGR     ffopo    opcfAmount  opcfGRAVG     equity      divgr   yieldAVG       roic       roce
                # 0     ABR     16   0.000000  21.142982   1.439661   2.686701  0.575582  7.186552e+07  61.744509  19.572096   9.409787  10.002282   9.848327   9.848327
                # 1     AHH     13  23.688315  10.429443   1.095079   3.123934  0.773961  5.898900e+07   5.784194  24.363130   6.172547   6.924290   4.431848   4.431848
                # 2     AKR     15  10.491896   8.535969   1.641150   9.464060  0.552573  1.071473e+08   8.465985   3.508083  -0.868627   4.210814   3.127630   3.127630
                # 3     AVB     18   7.019866   8.954259   8.091225   5.150866  0.689430  9.562168e+08   8.321641   3.803045   4.546365   3.200199   8.426437   8.426437
                # 4     CDP     17   1.647067   4.474543   1.811406   4.930338  0.594957  1.996096e+08   4.290395   3.210895  -0.048905   3.899390   5.045904   5.045904
                # 5    CIGI     16   8.177800  21.231661   2.895141   4.663452  0.020693  1.517538e+08  19.615105  12.725698  -4.761905   0.262234   6.870681  13.053546
                # 6     CIO     11  11.009753   4.569641   1.360295   7.694060  0.730049  4.937212e+07  22.411170   4.919162   5.235043   7.380378   0.586041   0.586041
                # 7    COLD      9   6.253111  19.146829   1.133202   4.051282  0.544308  2.733416e+08  19.397675  17.185404   2.499859   2.019978   0.721957   0.721957
                # 8     CPT     17   3.129320  10.894355   5.065133  10.680746  0.570628  3.934064e+08   5.341730   5.113566   6.949625   3.722503   7.189694   7.189694
                # 9     CTO     16  22.374887  36.389888   1.733638  33.372842  0.063641  1.025563e+07   4.834337   8.976871  28.476867   0.981469   2.578574   2.578574
                # 10   CUBE     16  12.612722  14.227782   1.327441  10.408008  0.614129  2.198135e+08  15.341324   3.273769  18.348083   2.972921   4.912779   4.912779
                # 11    EGP     16   8.477091  11.932193   3.991044   6.430346  0.639679  1.287662e+08   6.820333  15.826327   3.965242   3.179253   8.307110   8.307110
                # 12    ELS     17   5.923845   7.618466   2.566299   6.933987  0.513808  3.412785e+08   5.963395   3.554445  11.466968   4.148626  18.647693  18.647693
                # 13   EPRT      8  30.569500  44.475735   1.265956  13.658577  0.750845  1.429888e+08  25.468555  25.647553   6.826034   4.004894   4.296727   4.296727
                # 14   EQIX     17  13.088076  14.480996  13.136224   8.295151  0.295188  1.110584e+09  13.565764  13.037897  10.036534   2.541620   4.845284   5.128729
                # 15    EXR     17  15.480130   8.100785   2.849361   3.008004  0.636946  4.190264e+08  17.691361   9.250392  17.686457   3.337901   9.361796   9.361796
                # 16   FCPT     11   9.874911   9.664334   1.505815   2.958696  0.808960  8.912588e+07  16.344881  14.041612   4.441405   4.753576   9.949017   9.949017
                # 17     FR     15   4.643413  18.294981   1.262556  11.490054  0.545931  1.908325e+08   8.537965   9.332528   7.753480   2.787365   9.817753   9.817753
                # 18    FRT     17   5.519050   5.101680   5.250925   3.065942  0.657902  3.690873e+08   6.954425   6.505314   2.887301   3.308167  11.338018  11.338018
                # 19   GLPI     14   8.141309  12.320525   2.792851   4.364112  0.689353  5.853067e+08  10.309880   7.931058   5.278337   6.563871  14.695751  15.482438
                # 20    GTY     15   4.969280   9.437471   1.395861   4.444992  0.861596  5.852800e+07   9.582071   6.077485   7.637973   5.475293   8.613622   8.613622
                # 21   LAMR     17   0.600957   5.526489   5.647943   3.610795  0.360144  4.651098e+08   5.837324   3.242380   8.979439   4.865362   5.789386  23.689694
                # 22    MAA     15   4.392274   7.020637   6.935168   5.379529  0.565429  6.866522e+08   6.290177   4.928500   3.448423   3.771026   7.383438   7.383438
                # 23    NHI     17   8.478010   3.573156   4.890431   1.467391  0.708283  1.462412e+08   7.677964   3.856995   5.458102   5.644335  12.697365  12.697365
                # 24    NNN     17   8.810333  12.808287   2.412025   9.247136  0.728694  3.988139e+08  10.418153   5.448021   2.961793   4.526029   6.199792   6.199792
                # 25    NSA     12  21.481487  23.809821   3.280125   4.964097  0.533835  2.471858e+08  19.805404   4.572888  11.166826   3.441907   1.971008   1.971008
                # 26   NXRT     11  11.540939  30.621604   1.715203  39.945011  0.651851  4.268850e+07  12.103377   7.837619  11.207880   3.077816   3.282698   3.282698
                # 27      O     17  11.139858   9.495216   2.761982   1.319359  0.789246  6.649373e+08  12.919603  13.203644   2.821127   4.804715   4.725368   4.725368
                # 28    PLD     16  16.753735  13.820046   3.102574  12.732395  0.614340  1.277009e+09  18.867865   3.005580  10.053445   3.394767   5.646996   5.646996
                # 29   REXR     14  22.094937  25.170835   1.677598   9.636630  0.590894  2.371625e+08  26.152239  37.985240  13.726380   1.805052   2.626129   2.626129
                # 30    RMR     11  11.212166  11.250399   2.779824  10.919829  0.590540  9.821729e+07   1.869769  18.259547   0.110755   3.446795  12.717721  13.022789
                # 31   ROIC     16  11.019525   5.651260   1.047852   0.788237  0.657984  7.924953e+07  12.721737   5.134363  11.092232   4.342909   2.658438   2.658438
                # 32    RYN     16   4.580407   8.572854   2.012773   3.799954  0.493709  2.771987e+08   2.107633   3.817619   4.704516   3.703733   5.577871   9.979560
                # 33   STAG     14  17.044633  18.942035   1.751875   7.114952  0.897646  2.335600e+08  18.830450  20.361738  -0.462147   6.061471   4.181835   4.181835
                # 34    SUI     14  15.267966  19.937374   4.149191   4.134355  0.632165  2.301071e+08  25.134244  27.079961   7.487589   3.620356   3.282838   3.282838
                # 35   TRNO     15  15.578849  21.604003   1.533246  17.179825  0.719757  6.368967e+07  20.425449  16.865568  12.273021   2.299690   3.284133   3.284133
                # 36    UDR     17   6.329154   4.975899   1.999374   5.529338  0.665042  4.876632e+08   9.121222   3.567117   6.077770   3.475159   5.585314   5.585314
                # 37   VICI      8  28.491854  18.182911   1.509511   0.146807  0.775557  1.221966e+09  13.087972  24.509181   9.576433   4.747988   7.815374   7.815374

        sqldf = print_DB(matspull, 'return')
        print(sqldf)#.head(25))

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSRE error: ')
        print(err)    

# LSRE()

def LSU():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, \
                    payoutRatioAVG as po,  \
                    CASE WHEN repBookValueGrowthAVG > calcBookValueGrowthAVG THEN repBookValueGrowthAVG ELSE calcBookValueGrowthAVG END bv, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    (calcDivYieldAVG + repDivYieldAVG) / 2 as yieldAVG, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Utilities\' \
                    AND years >= 5 \
                    AND revgr >= -1 \
                    AND nigr >= 5 \
                    AND equity >= 5 \
                    AND divgr >= 3 \
                    AND payoutRatioAVG <= 0.9 \
                    AND yieldAVG >= 3 \
                    AND roic > 5 \
                    AND roce >= 10 \
                    ORDER BY roce DESC;'        
        
        # AND Ticker IN (\'SO\', \'NEE\', \'SRE\', \'AEP\', \'AWK\', \'CEG\', \'DUK\', \'XEL\', \'ED\') \
        # ' Ticker  years     revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  opcfGRAVG  netCashFlowAVG  netCashFlowGrowthAVG         bv     equity       divgr       roic       roce
            # 0     ED     16  0.011786   7.139141        0.664163          2.691571e+09   2.531526    1.326923e+08             -1.604445   2.822946   4.206808    2.554914   4.475670   8.774117
            # 2     SO     18  2.171045   8.943522        0.796197          6.014083e+09   1.860861    1.842667e+08            -23.119291   3.610923   5.672442    3.493040  10.581139  10.670477
            # 3    AEP     18 -0.093679   2.914157        0.636054          4.318267e+09   0.715478    1.438462e+07             57.999799   4.240100   4.951068    5.234602   4.350508  10.036047
            # 6    AWK     17  2.436247   9.859694        0.548786          1.169949e+09   4.421253    2.460727e+06            122.562528   6.778088   8.816126    9.868292   7.612115   9.098066
            # 7    NEE     18 -0.751340   8.041960        0.503835          5.715625e+09   2.289646    4.171429e+07            -42.261875  10.226074  11.739939   10.205066   5.205711  12.626598
            # 8    CEG      5  4.526276 -37.617845       -0.186148         -2.741800e+09 -67.048787   -7.400000e+07            -57.814592   0.780038  19.753014  100.900343   3.695757   6.809931
        #run
        #  Ticker  years     revgr       nigr        po         bv     equity      divgr  yieldAVG       roic       roce
        # 0    NEE     18 -0.751340   8.041960  0.503835  10.226074  11.739939  10.205066  7.115109   5.205711  12.626598
        # 3     SO     18  2.171045   8.943522  0.796197   3.610923   5.672442   3.493040  4.720481  10.581139  10.670477
        # 6    DTE     18 -0.068762  11.366474  0.604611   4.432862   5.981913   5.845635  4.103859   6.281121  10.162496

                   
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSU error: ')
        print(err)    

# LSU()

def LSV():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, \
                    operatingCashFlowAVG, operatingCashFlowGrowthAVG as opcfGRAVG, netCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Healthcare\' \
                    AND years >= 5 \
                    AND revGrowthAVG > 0 \
                    AND netIncomeGrowthAVG > 0 \
                    AND equity >= 2 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowAVG > 0 \
                    AND divgr >= 5 AND divgr <= 30 \
                    AND payoutRatioAVG <= 0.9 \
                    AND roic > 10 \
                    AND roce > 20 \
                    ORDER BY divgr;'
        
        # Ticker  years     revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  opcfGRAVG  netCashFlowAVG     equity      divgr       roic       roce
        # 0    JNJ     18  0.053266   0.639752        0.523625          1.944044e+10   1.723225    3.340200e+09   2.491466   6.354853  19.093455  25.802498
        # 1    CHE     17  5.487058   4.826768        0.112086          2.039388e+08   3.716200    6.639800e+06   9.167445   8.314974  17.416843  21.291781
        # 2    BAX     17  4.593906   5.192259        0.390515          2.328294e+09   4.786372    4.261538e+07   2.392073  13.569116  25.355061  25.760886
        # 3    ZTS     14  5.719685   9.974373        0.258936          1.394500e+09   2.899658    1.597778e+08  22.010731  19.351457  14.235721  48.630513
        # 4    UNH     18  8.932597  10.404949        0.247011          1.086680e+10  10.131522    2.234000e+08  10.609211  23.203761  12.924552  20.236874
        # 5    NRC     16  6.182689   2.572075        0.577848          2.927812e+07   4.124795    3.415000e+06   7.928680  25.073207  28.560532  29.375253
        
                   
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSV error: ')
        print(err)    

# LSV()

def LSY():
    try:
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, operatingCashFlowAVG, operatingCashFlowGrowthAVG as opcfGRAVG, \
                    netCashFlowAVG, netCashFlowGrowthAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    payoutRatioAVG, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Consumer Cyclical\' \
                    AND years >= 5 \
                    AND revGrowthAVG >= 3 \
                    AND netIncomeGrowthAVG >= 5 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowGrowthAVG > 0 \
                    AND equity >= 10 \
                    AND divgr >= 5 AND divgr <= 50 \
                    AND payoutRatioAVG <= 0.9 \
                    AND roic > 10 \
                    AND roce > 10 \
                    ORDER BY divgr;'

        # Ticker  years      revgr       nigr  operatingCashFlowAVG  opcfGRAVG  netCashFlowAVG  netCashFlowGrowthAVG     equity      divgr  payoutRatioAVG       roic       roce
        # 0   AMZN     18  25.158803   5.469834          1.602340e+10  27.755116    2.365615e+09             -6.442240  30.914254        nan        0.000000   8.738340  14.292071
        # 1   TSLA     16  55.815803  37.733530          8.608899e+08  14.331766    2.085190e+08             78.325071  20.272625        nan        0.000000 -11.012581  -3.796099
        # 2     HD     18   5.148000  14.820723          9.314800e+09   0.684573    4.073077e+08             92.754643 -16.044242  12.522931        0.433224  81.982101  52.936413
        #run
        # Ticker  years      revgr       nigr  operatingCashFlowAVG  opcfGRAVG  netCashFlowAVG  netCashFlowGrowthAVG     equity      divgr  payoutRatioAVG       roic       roce
        # 0    WGO     15  16.726710   8.757104          4.471791e+07  46.139882    6.520909e+06             35.849774  20.239517   7.664924        0.096590  15.287101  17.684549
        # 1     BC     16   5.970890   5.895730          3.849467e+08  19.785466    1.287500e+06             44.201273  10.669052  13.684247        0.137431  12.014558  21.620041
        # 2    LAD     16  18.041475  21.981927          1.752767e+07  34.831863    7.425667e+06             42.089850  18.127205  13.867439        0.097754  15.732312  20.225043
        # 3      F     18   3.000861  10.437957          1.472193e+10   2.463674   -1.775188e+09             12.915407  10.521648  14.315109        0.085081  16.966215  17.048993
        # 4    ASO      6   5.707345  62.716192          5.061795e+08  -5.388023    5.937725e+07             82.370468  14.415214  20.000000        0.000000  16.175759  30.965504
        # 5   MELI     17   8.313859  55.910868          1.728577e+08  21.381201    4.065116e+07             28.096461  12.101567  21.969248        0.016067  23.574243  26.162650
        # 6   SBUX     18  10.604473  13.154940          3.194706e+09   5.665425    2.814636e+08             35.666138  11.381260  25.161787        0.406358  27.201981  25.940525
        # 7    KRT      5   8.820896  16.214444          3.189160e+07  13.589056    7.035000e+06             10.659801  11.079528  49.520299        0.082270  20.522848  23.799595
                   
        sqldf = print_DB(matspull, 'return')
        print(sqldf)

        # tickerslist = sqldf['Ticker'].tolist()
        # checklist = invunidf['Ticker'].tolist()
        # qualifiedtickers = [x for x in tickerslist if x in checklist]
        # for x in qualifiedtickers:
        #     matspull2 = 'SELECT Ticker, Sector, roce, roic, roc, ffopo, po, divgr, divpay, divyield, shares, debt, rev, ni, ffo, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
        #             WHERE Ticker LIKE \'' + x + '\''
        #     sqldf2 = print_DB(matspull2, 'return')
        #     uploadToDB(sqldf2,'Investable_Universe')
            # print(sqldf2)
    except Exception as err:
        print('LSY error: ')
        print(err)    

# LSY()

def LSGrowth(): 
    try:
        matspull = 'SELECT Ticker, rev, ni, cf, bv, equity as eq, divgr as dg, po, roic, roce,  plainscore as pscore, score, maxplainscore as maxpscore, maxscore \
                    FROM Growth_Ranking \
                    WHERE rev > 2 \
                    AND ni > 2 \
                    AND cf > 2 \
                    AND eq > 2 \
                    AND roic > 3 \
                    AND roce > 3 \
                    AND pscore > 35 \
                    AND score > 55 \
                    ORDER BY score DESC, plainscore DESC;'
                   
        sqldf = print_DB(matspull, 'return')
        tickerlist = sqldf['Ticker'].tolist()
        yearlist = []

        for x in tickerlist:
            tickergrab = 'SELECT Ticker, Sector, AveragedOverYears as years FROM Metadata WHERE Ticker LIKE \'' + str(x) + '\''
            tickers = print_DB(tickergrab, 'return')
            try:
                yearlist.append(tickers['years'][0])
            except:
                print('nonetype dangit')
                yearlist.append('no year data')
                continue

        sqldf['years'] = yearlist
        print(sqldf)

    except Exception as err:
        print('LSGrowth error: ')
        print(err)  

# LSGrowth()

def LSQualNonDivPayers(): 
    try:
        matspull = 'SELECT Ticker, rev, ni, cf, bv, equity as eq, roic, roce,  plainscore as pscore, score, maxplainscore as maxpscore, maxscore \
                    FROM QualNonDivPayers_Ranking \
                    WHERE rev > 3 \
                    AND ni > 3 \
                    AND cf > 3 \
                    AND eq > 3 \
                    AND roic > 3 \
                    AND roce > 3 \
                    AND pscore > 45 \
                    AND score > 175 \
                    ORDER BY score DESC, plainscore DESC;'
                   
        sqldf = print_DB(matspull, 'return')
        tickerlist = sqldf['Ticker'].tolist()
        yearlist = []

        for x in tickerlist:
            tickergrab = 'SELECT Ticker, Sector, AveragedOverYears as years FROM Metadata WHERE Ticker LIKE \'' + str(x) + '\''
            tickers = print_DB(tickergrab, 'return')
            try:
                yearlist.append(tickers['years'][0])
            except:
                print('nonetype dangit')
                yearlist.append('no year data')
                continue

        sqldf['years'] = yearlist
        print(sqldf)

    except Exception as err:
        print('LSGrowth error: ')
        print(err)  

# LSQualNonDivPayers()

#this gauges a popular etf, but also gives ideas for later screenings, currently a play thing
def semiETFavg():
    try:
        tsla = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    payoutRatioAVG, \
                    repsAVG as repsAVG, repsGrowthAVG as repsGRAvg, cepsAVG as cepsAVG, cepsGrowthAVG as cepsGRAVG, \
                    operatingCashFlowAVG as opcfAmount, operatingCashFlowGrowthAVG as opcfGRAVG, netCashFlowAVG as netcfAmount, netCashFlowGrowthAVG as netcfGRAVG, \
                    CASE WHEN repBookValueGrowthAVG > calcBookValueGrowthAVG THEN repBookValueGrowthAVG ELSE calcBookValueGrowthAVG END bv, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    debtGrowthAVG, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Ticker IN ( \'NVDA\', \'AMD\', \'GFS\', \'TER\', \'ENTG\', \'QRVO\', \'AMKR\', \'LSCC\', \'RMBS\', \'ALGM\', \
                                        \'SWKS\', \'COHR\', \'INTC\', \'TXN\', \'ADI\', \'MCHP\', \'AVGO\', \'TSM\', \'LRCX\', \'AMAT\', \
                                        \'KLAC\', \'ASML\', \'MU\', \'MRVL\', \'QCOM\', \'ON\', \'NXPI\', \'MPWR\') \
                    ORDER BY years;'

        # print_DB(tsla, 'print')
        tslastore = print_DB(tsla, 'return')
        soxq = pd.DataFrame()
        soxq['revgr'] = [np.average(tslastore['revgr'].dropna())]
        soxq['nigr'] = np.average(tslastore['nigr'].dropna())
        soxq['repsAVG'] = np.average(tslastore['repsAVG'].dropna())
        soxq['repsGRAvg'] = np.average(tslastore['repsGRAvg'].dropna())
        soxq['cepsAVG'] = np.average(tslastore['cepsAVG'].dropna())
        soxq['cepsGRAVG'] = np.average(tslastore['cepsGRAVG'].dropna())
        soxq['divgr'] = np.average(tslastore['divgr'].dropna())
        soxq['payoutRatioAVG'] = np.average(tslastore['payoutRatioAVG'].dropna())
        soxq['opcfAmount'] = np.average(tslastore['opcfAmount'].dropna())
        soxq['opcfGRAVG'] = np.average(tslastore['opcfGRAVG'].dropna())
        soxq['netcfAmount'] = np.average(tslastore['netcfAmount'].dropna())
        soxq['netcfGRAVG'] = np.average(tslastore['netcfGRAVG'].dropna())
        soxq['equity'] = np.average(tslastore['equity'].dropna())
        soxq['roic'] = np.average(tslastore['roic'].dropna())
        soxq['roce'] = np.average(tslastore['roce'].dropna())
        
        print(soxq)
        eps = soxq['repsAVG'][0]
        filter = tslastore[tslastore['repsAVG'] >= eps]
        divgr = soxq['divgr'][0]
        filter = filter[filter['divgr'] >= divgr]
        roic = soxq['roic'][0]
        filter = filter[filter['roic'] >= roic]
        # roce = soxq['roce'][0]
        # filter = tslastore[tslastore['roce'] >= roce]
        print(filter.sort_values('divgr'))

    except Exception as err:
        print('soxq error')
        print(err)

# semiETFavg() #luke soxq for testing

#useful template
# AND Ticker IN (\'MSFT\', \'AAPL\', \'CSCO\', \'ACN\', \'INTU\', \'IBM\', \'PANW\', \'SWKS\', \'ANET\', \'NVDA\', \'AMD\', \
#                     \'INTC\', \'TXN\', \'ADI\', \'MCHP\', \'AVGO\', \'TSM\', \'LRCX\', \'AMAT\', \'KLAC\', \'ASML\', \'MU\', \'MRVL\', \'QCOM\', \
#                     \'ON\', \'NXPI\', \'MPWR\') \

#sql tests
# testinv = 'Select * From Investable_Universe ORDER BY Sector, score DESC'
# print_DB(testinv,'print')

# testh = 'Select * From Growth_Ranking ORDER BY score DESC '
# print_DB(testh, 'print')

# testq = 'Select * From QualNonDivPayers_Ranking ORDER BY score DESC '
# print_DB(testq, 'print')

# testsector = 'Select * From Sector_Rankings ORDER BY score DESC'
# print_DB(testsector, 'print')

# testb = 'Select * From Materials_Ranking ORDER BY score DESC'
# print_DB(testb,'print')

# testc = 'Select * From Communications_Ranking ORDER BY score DESC'
# print_DB(testc,'print')

# teste = 'Select * From Energy_Ranking ORDER BY score DESC'
# print_DB(teste,'print')

# testf = 'Select * From Financials_Ranking ORDER BY score DESC'
# print_DB(testf,'print')

# testi = 'Select * From Industrials_Ranking ORDER BY score DESC'
# print_DB(testi,'print')

# testk = 'Select * From Tech_Ranking ORDER BY score DESC'
# print_DB(testk,'print')

# testp = 'Select * From ConsumerDefensive_Ranking ORDER BY score DESC'
# print_DB(testp,'print')

# testr = 'Select * From RealEstate_Ranking ORDER BY score DESC'
# print_DB(testr,'print')

# testu = 'Select * From Utilities_Ranking ORDER BY score DESC'
# print_DB(testu,'print')

# testv = 'Select * From Healthcare_Ranking ORDER BY score DESC'
# print_DB(testv,'print')

# testy = 'Select * From ConsumerCyclical_Ranking ORDER BY score DESC'
# print_DB(testy,'print')

# testsectorTop = 'Select avg(roce), avg(roic), avg(ffopo), avg(divgr), avg(divpay), avg(shares), avg(cf), avg(bv), avg(equity), avg(debt), \
#                         avg(fcfm), avg(fcf), avg(ni), avg(ffo), avg(rev) From Sector_Rankings WHERE Sector LIKE \'RE\''
# print_DB(testsectorTop, 'print')

# ohohmagic = 'Select * From Sector_Rankings WHERE Sector LIKE \'I\' ORDER BY score DESC LIMIT 50 '
# print_DB(ohohmagic, 'print')

#check all tables in DB, nifty
# tman = 'SELECT name FROM sqlite_master WHERE type = \'table\''
# print_DB(tman, 'print')

###dangerous reset button
# testd = 'DELETE From Metadata_Backup'
# conn = sql.connect(db_path)
# query = conn.cursor()
# query.execute(testd)
# conn.commit()
# query.close()
# conn.close()
##dangerous delete button

# testindustries = 'SELECT DISTINCT(Industry), Sector FROM Mega WHERE Sector LIKE \'Utilities\''
# csv.simple_saveDF_to_csv('',print_DB(testindustries, 'return'), 'z-Industries-util', False)