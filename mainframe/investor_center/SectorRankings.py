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
# import Valuation as value

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

###LUKE TO DO
# 1:
# debate full clearing sector rankings, vs snapshots, vs just keeping them in for more metadata; note below
# i'm thinking copy it to a new table: sector rankings: 2023-month upon which it was updated, wipe, refill
# NEED A FUNCTION TO COPY DB TO NEW TABLE AFTER MODEL IS MADE
# 2 
# MAKE SECTOR RANKING RETURN FUNCTIONS BELOW

###
# Each security scores according to its own financial records, weighted by what's important to each sector. 
# This gives us an overall picture of the quality of each company.
# Then the user can filter what other ranking scores they want to, to choose securities for viewing on the front end.
# The sector weightings are how we would analyze a stock in that sector, creating an investable universe.
# Thus is Sector Rankings.

def rating_assignment(number, listcompare):
    try:
        if pd.isnull(number) or np.isinf(number) or number is None:
            rating = 0
        else:
            if number >= listcompare[0]:
                rating = 5
            elif number < listcompare[0] and number >= listcompare[1]:
                rating = 4
            elif number < listcompare[1] and number >= listcompare[2]:
                rating = 3
            elif number < listcompare[2] and number >= listcompare[3]:
                rating = 2
            elif number < listcompare[3] and number >= listcompare[4]:
                rating = 1
            elif number < listcompare[4] and number >= listcompare[5]:
                rating = -1
            elif number < listcompare[5] and number >= listcompare[6]:
                rating = -2
            elif number < listcompare[6] and number >= listcompare[7]:
                rating = -3
            elif number < listcompare[7] and number >= listcompare[8]:
                rating = -4
            else:
                rating = -5
        
    except Exception as err:
        print('rating assignment error:')
        print(err)
    finally:
        return rating

def rev_rating(ticker):
    try:
        sqlq = 'SELECT revGrowthAVG as revavg, revGrowthAVGintegrity as integ, revGrowthAVGnz as revavgnz \
                        FROM Metadata \
                        WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        if resultsdf['integ'][0] in ('good','decent'):
            avg = resultsdf['revavg'][0]
        else:
            avg = resultsdf['revavgnz'][0]
        rulecompare = [15, 7, 3, 2, 0, -1, -2, -3, -4]
        finalrating = rating_assignment(avg, rulecompare)
    except Exception as err:
        print('growth analysis error:')
        print(err)
    finally:
        return finalrating

# print(rev_rating('F'))

def ni_rating(ticker):
    try:
        sqlq = 'SELECT netIncomeGrowthAVG as niavg, netIncomeGrowthAVGintegrity as niint, netIncomeGrowthAVGnz as niavgnz, \
                        netIncomeNCIGrowthAVG as ninciavg, netIncomeNCIGrowthAVGintegrity as ninciint, netIncomeNCIGrowthAVGnz as ninciavgnz \
                        FROM Metadata \
                        WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #sort ni avg
        if resultsdf['niint'][0] in ('good','decent'):
            netincomeavg = resultsdf['niavg'][0]
        else:
            netincomeavg = resultsdf['niavgnz'][0]
        #sort ninci avg
        if resultsdf['ninciint'][0] in ('good','decent'):
            nciavg = resultsdf['ninciavg'][0]
        else:
            nciavg = resultsdf['ninciavgnz'][0]
        #determine NI avg
        if pd.isnull(netincomeavg) == False and np.isinf(netincomeavg) == False and pd.isnull(nciavg) == False and np.isinf(nciavg) == False:
            avg = max(netincomeavg, nciavg)
        elif pd.isnull(nciavg) == True or np.isinf(nciavg) == True:
            if pd.isnull(netincomeavg) == False and np.isinf(netincomeavg) == False:
                avg = netincomeavg
            else:
                avg = 0 #arbitrary number, based below inflation due to lack of reporting
        elif pd.isnull(netincomeavg) == True or np.isinf(netincomeavg) == True:
            if pd.isnull(nciavg) == False and np.isinf(nciavg) == False:
                avg = nciavg
            else:
                avg = 0 #arbitrary number, based below inflation due to lack of reporting
        else:
            avg = 0 #arbitrary number, based below inflation due to lack of reporting
        #hardcode finalrating because some negative NI's have huge growth into positive numbers, skewing avg results
        if avg == 0:
            finalrating = -1
        elif avg > 0 and avg <= 1:
            finalrating = 1
        elif avg > 1 and avg <= 3:
            finalrating = 2
        elif avg > 3 and avg <= 7:
            finalrating = 3
        elif avg > 7 and avg < 10:
            finalrating = 4
        elif avg >= 10 and avg <= 35:
            finalrating = 5
        elif avg > 35:
            finalrating = 3
        elif avg < 0 and avg >= -1:
            finalrating = -2
        elif avg < -1 and avg >= -3:
            finalrating = -3
        elif avg < -3 and avg >= -5:
            finalrating = -4
        elif avg < -5:
            finalrating = -5
    except Exception as err:
        print('ni rating error:')
        print(err)
    finally:
        return finalrating

# print(ni_rating('SNAP'))
                
def ffo_rating(ticker):
    try:
        sqlq = 'SELECT ffoGrowthAVG as ffoavg, ffoGrowthAVGintegrity as ffoint, ffoGrowthAVGnz as ffoavgnz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #sort ni avg
        if resultsdf['ffoint'][0] in ('good','decent'):
            ffoavg = resultsdf['ffoavg'][0]
        else:
            ffoavg = resultsdf['ffoavgnz'][0]
        #determine avg
        if pd.isnull(ffoavg) == False and np.isinf(ffoavg) == False:      
            avg = ffoavg
        else:
            avg = 1 #arbitrary number, based below inflation due to lack of reporting
        #hardcode finalrating because some negative NI's have huge growth into positive numbers, skewing avg results
        if avg == 0:
            finalrating = -1
        elif avg > 0 and avg <= 1:
            finalrating = 1
        elif avg > 1 and avg <= 3:
            finalrating = 2
        elif avg > 3 and avg <= 7:
            finalrating = 3
        elif avg > 7 and avg < 10:
            finalrating = 4
        elif avg >= 10 and avg <= 35:
            finalrating = 5
        elif avg > 35:
            finalrating = 3
        elif avg < 0 and avg >= -1:
            finalrating = -2
        elif avg < -1 and avg >= -3:
            finalrating = -3
        elif avg < -3 and avg >= -5:
            finalrating = -4
        elif avg < -5:
            finalrating = -5

    except Exception as err:
        print('ffo rating error:')
        print(err)
    finally:
        return finalrating

# print(ffo_rating('WPC'))

def fcf_rating(ticker):  
    try:
        sqlq = 'SELECT fcfGrowthAVG as ffoavg, fcfGrowthAVGintegrity as ffoint, fcfGrowthAVGnz as ffoavgnz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #sort ni avg
        if resultsdf['ffoint'][0] in ('good','decent'):
            ffoavg = resultsdf['ffoavg'][0]
        else:
            ffoavg = resultsdf['ffoavgnz'][0]
        #determine avg
        if pd.isnull(ffoavg) == False and np.isinf(ffoavg) == False:      
            avg = ffoavg
        else:
            avg = 0 #arbitrary number, based below inflation due to lack of reporting
        
        rulecompare = [10, 7, 3, 1, 0, -1, -2, -3, -4]
        finalrating = rating_assignment(avg, rulecompare)
    except Exception as err:
        print('fcf rating error:')
        print(err)
    finally:
        return finalrating
                   
# print(fcf_rating('F'))

def fcfm_rating(ticker):
    try:
        sqlq = 'SELECT fcfMarginAVG as fcfmavg, fcfMarginGrowthAVG as fcfmgravg, fcfMarginGrowthAVGintegrity as fcfmint, fcfMarginGrowthAVGnz as fcfmgravgnz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        
        #determine fcfm avg
        if pd.isnull(resultsdf['fcfmavg'][0]) == False and np.isinf(resultsdf['fcfmavg'][0]) == False:      
            fcfmaverage = resultsdf['fcfmavg'][0]
        else:
            fcfmaverage = 1
        #grade fcfm avg
        fcfmrulecompare = [20, 10, 5, 2, 0, -1, -2, -3, -4]
        fcfmfinalrating = rating_assignment(fcfmaverage,fcfmrulecompare)

        #set fcfmGRavg
        if resultsdf['fcfmint'][0] in ('good','decent'):
            netincomeavg = resultsdf['fcfmgravg'][0]
        else:
            netincomeavg = resultsdf['fcfmgravgnz'][0]
        if pd.isnull(netincomeavg) == False and np.isinf(netincomeavg) == False:      
            avg = netincomeavg
        else:
            avg = 1
        #determine fcfm gr
        rulecompare = [10, 7, 3, 1, 0, -1, -2, -3, -4]
        fcfmgrfinalrating = rating_assignment(avg, rulecompare)

        finalrating = math.floor((fcfmfinalrating + fcfmgrfinalrating) / 2)
    except Exception as err:
        print('fcfm rating error:')
        print(err)
    finally:
        return finalrating

# print(fcfm_rating('F'))

#EPS averages are insane. excluded from weighting because they're mostly a valuation metric, and we can weight net income and shares growth instead for a more accurate picture of security.
# def reiteps_rating(ticker):
#     try:
#         sqlq = 'SELECT reitepsAVG as fcfmavg, reitepsAVGintegrity as repsavgint, reitepsAVGnz as repsavgnz fcfMarginGrowthAVG as fcfmgravg, fcfMarginGrowthAVGintegrity as fcfmint, fcfMarginGrowthAVGnz as fcfmgravgnz \
#                     FROM Metadata \
#                     WHERE Ticker LIKE \'' + ticker + '\';'
#         resultsdf = print_DB(sqlq, 'return')
#         #sort avg
#         if resultsdf['fcfmint'][0] in ('good','decent'):
#             netincomeavg = resultsdf['fcfmgravg'][0]
#         else:
#             netincomeavg = resultsdf['fcfmgravgnz'][0]
        
#         if pd.isnull(resultsdf['fcfmavg'][0]) == False and np.isinf(resultsdf['fcfmavg'][0]) == False:      
#             fcfmaverage = resultsdf['fcfmavg'][0]
#         else:
#             fcfmaverage = 1

#         fcfmrulecompare = [20,10,5,1]
#         fcfmfinalrating = rating_assignment(fcfmaverage,fcfmrulecompare)

#         #determine avg
#         if pd.isnull(netincomeavg) == False and np.isinf(netincomeavg) == False:      
#             avg = netincomeavg
#         else:
#             avg = 1
        
#         rulecompare = [10, 7, 3, 0]
#         fcfmgrfinalrating = rating_assignment(avg, rulecompare)

#         finalrating = math.floor((fcfmfinalrating + fcfmgrfinalrating) / 2)
#     except Exception as err:
#         print('reit eps rating error:')
#         print(err)
#     finally:
#         return finalrating

def debt_rating(ticker):
    try:
        sqlq = 'SELECT debtGrowthAVG as debtgravg \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        
        if pd.isnull(resultsdf['debtgravg'][0]) == False and np.isinf(resultsdf['debtgravg'][0]) == False:      
            avg = resultsdf['debtgravg'][0]
        else:
            avg = 'None' #arbitraily chosen to give a middling score due to non-reporting
        
        #best to manually calculate a value here, rating function only counts higher as better
        if avg == 'None':
            finalrating = 0
        elif avg <= 0:
            finalrating = 5
        elif avg > 0 and avg <= 1:
            finalrating = 4
        elif avg > 1 and avg <= 3:
            finalrating = 3
        elif avg > 3 and avg <= 5:
            finalrating = 1
        elif avg > 5 and avg <= 7:
            finalrating = -1
        elif avg > 7 and avg <= 10:
            finalrating = -2
        elif avg > 10 and avg <= 12:
            finalrating = -3
        elif avg > 12 and avg <= 15:
            finalrating = -4
        elif avg > 15:
            finalrating = -5
        # elif avg == 'None':
        #     finalrating = 0
     
    except Exception as err:
        print('debt rating error:')
        print(err)
    finally:
        return finalrating

# print(debt_rating('NLY'))

def equity_rating(ticker):
    try:
        sqlq = 'SELECT reportedEquityGrowthAVG as rgravg, reportedEquityGrowthAVGnz as rgravgnz,\
                 calculatedEquityGrowthAVG as cgravg, calculatedEquityGrowthAVGnz as cgravgnz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #assign reported equity gr
        if pd.isnull(resultsdf['rgravg'][0]) == False and np.isinf(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:      
            reqavg = max(resultsdf['rgravg'][0], resultsdf['rgravgnz'][0])
        elif pd.isnull(resultsdf['rgravg'][0]) == True or np.isinf(resultsdf['rgravg'][0]) == True:
            if pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:
                reqavg = resultsdf['rgravgnz'][0]
            else:
                reqavg = 0
        
        rrulecompare = [10,5,3,1,0,-1,-2,-3,-4]
        rfinalrating = rating_assignment(reqavg,rrulecompare)

        if pd.isnull(resultsdf['cgravg'][0]) == False and np.isinf(resultsdf['cgravg'][0]) == False and pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:      
            ceqavg = max(resultsdf['cgravg'][0], resultsdf['cgravgnz'][0])
        elif pd.isnull(resultsdf['cgravg'][0]) == True or np.isinf(resultsdf['cgravg'][0]) == True:
            if pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:
                ceqavg = resultsdf['cgravgnz'][0]
            else:
                ceqavg = 0
        
        rulecompare = [10,5,3,1,0,-1,-2,-3,-4]
        cfinalrating = rating_assignment(ceqavg, rulecompare)

        if reqavg + ceqavg == 0:
            finalrating = 0
        else:
            finalrating = max(rfinalrating, cfinalrating)
    except Exception as err:
        print('equity rating error:')
        print(err)
    finally:
        return finalrating

# print(equity_rating('CELH'))

def bvnav_rating(ticker):
    try:
        sqlq = 'SELECT repBookValueGrowthAVG as rgravg, repBookValueGrowthAVGnz as rgravgnz,\
                 calcBookValueGrowthAVG as cgravg, calcBookValueGrowthAVGnz as cgravgnz, \
                 navGrowthAVG as navgravg \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        
        if pd.isnull(resultsdf['rgravg'][0]) == False and np.isinf(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:
            reqavg = max(resultsdf['rgravg'][0], resultsdf['rgravgnz'][0])
        else:
            reqavg = 0

        if pd.isnull(resultsdf['cgravg'][0]) == False and np.isinf(resultsdf['cgravg'][0]) == False and pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:      
            ceqavg = max(resultsdf['cgravg'][0], resultsdf['cgravgnz'][0])
        else:
            ceqavg = 0
        
        avg = max(reqavg, ceqavg)

        if avg == 0: #this is here to catch companies who don't have the above information from SEC scrapings.
            finalrating = 0
        elif pd.isnull(resultsdf['navgravg'][0]) == False and np.isinf(resultsdf['navgravg'][0]) == False:
            navcompare = [10,5,3,1,0,-1,-2,-3,-4]
            navrating = rating_assignment(resultsdf['navgravg'][0], navcompare)
            rulecompare = [10,5,3,1,0,-1,-2,-3,-4]
            cfinalrating = rating_assignment(avg, rulecompare)
            finalrating = math.floor((navrating + cfinalrating) / 2)
        else:
            rulecompare = [10,5,3,1,0,-1,-2,-3,-4]
            cfinalrating = rating_assignment(avg, rulecompare)
            finalrating = cfinalrating
        
    except Exception as err:
        print('book value rating error:')
        print(err)
    finally:
        return finalrating

# print(bvnav_rating('MAIN'))

def cf_rating(ticker):
    try:
        sqlq = 'SELECT netCashFlowGrowthAVG as rgravg, netCashFlowGrowthAVGnz as rgravgnz,\
                 operatingCashFlowGrowthAVG as cgravg, operatingCashFlowGrowthAVGnz as cgravgnz, \
                 netCashFlowAVG as navgravg \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #repping net cf
        if pd.isnull(resultsdf['rgravg'][0]) == False and np.isinf(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:
            reqavg = max(resultsdf['rgravg'][0], resultsdf['rgravgnz'][0])
        else:
            reqavg = 0
        #repping op cf
        if pd.isnull(resultsdf['cgravg'][0]) == False and np.isinf(resultsdf['cgravg'][0]) == False and pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:      
            ceqavg = max(resultsdf['cgravg'][0], resultsdf['cgravgnz'][0])
        else:
            ceqavg = 0
        
        rcompare = [7,4,2,1,0,-1,-5,-7,-10] 
        rrating = rating_assignment(reqavg,rcompare)
        ccompare = [7,4,2,1,0,-1,-2,-3,-4] 
        crating = rating_assignment(ceqavg,ccompare)

        if pd.isnull(resultsdf['navgravg'][0]) == False and np.isinf(resultsdf['navgravg'][0]) == False:
            if resultsdf['navgravg'][0] > 0:
                flatrating = 5
            elif resultsdf['navgravg'][0] == 0:
                flatrating = 3
            else:
                flatrating = -1
        else:
            flatrating = 0
        finalrating = math.ceil((rrating + crating + flatrating) / 3)
    except Exception as err:
        print('cash flow rating error:')
        print(err)
    finally:
        return finalrating

# print(cf_rating('NUE'))

def shares_rating(ticker):
    try:
        sqlq = 'SELECT sharesGrowthAVG as rgravg, dilutedSharesGrowthAVG as cgravg \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        
        if pd.isnull(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['cgravg'][0]) == False:
            reqavg = max(resultsdf['rgravg'][0], resultsdf['cgravg'][0])
        elif pd.isnull(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['cgravg'][0]) == True:
            reqavg = resultsdf['rgravg'][0]
        elif pd.isnull(resultsdf['rgravg'][0]) == True and pd.isnull(resultsdf['cgravg'][0]) == False:
            reqavg = resultsdf['cgravg'][0]
        else:
            reqavg = 'None'

        if reqavg == 'None':
            finalrating = 0
        elif reqavg <= 0:
            finalrating = 5
        elif reqavg > 0 and reqavg <= 3:
            finalrating = 4
        elif reqavg > 3 and reqavg <= 5:
            finalrating = 3
        elif reqavg > 5 and reqavg <= 7:
            finalrating = 2
        elif reqavg > 7 and reqavg <= 10:
            finalrating = 1
        elif reqavg > 10 and reqavg <= 12:
            finalrating = -1
        elif reqavg > 12 and reqavg <= 15:
            finalrating = -2
        elif reqavg > 15 and reqavg <= 18:
            finalrating = -3
        elif reqavg > 18 and reqavg <= 20:
            finalrating = -4
        elif reqavg > 20:
            finalrating = -5

    except Exception as err:
        print('shares rating error:')
        print(err)
    finally:
        return finalrating

# print(shares_rating('PLD'))

def divspaid_rating(ticker):
    try:
        sqlq = 'SELECT calcDivsPerShareLow as rgravg, repDivsPerShareLow as cgravg, calcDivsPerShareLatest clat, repDivsPerShareLatest rlat \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
       
        if pd.isnull(resultsdf['rgravg'][0]) == False and resultsdf['rgravg'][0] > 0:
            cdivsrating = 1
        else:
            cdivsrating = -1
        if (resultsdf['rgravg'][0] is None) == True:
            cdivsrating = -1

        if pd.isnull(resultsdf['cgravg'][0]) == False and resultsdf['cgravg'][0] > 0:
            rdivsrating = 1
        else:
            rdivsrating = -1
        if (resultsdf['cgravg'][0] is None) == False:
            rdivsrating = -1

        if pd.isnull(resultsdf['clat'][0]) == False and resultsdf['clat'][0] > 0:
            cdivsrating = 1
        else:
            cdivsrating = -1
        if pd.isnull(resultsdf['rlat'][0]) == False and resultsdf['rlat'][0] > 0:
            rdivsrating = 1
        else:
            rdivsrating = -1
        
      
        finalrating = max(rdivsrating,cdivsrating)
    except Exception as err:
        print('divs paid rating error:')
        print(err)
    finally:
        return finalrating

# print(divspaid_rating('AMZN'))

def divrev_rating(ticker):
    try:
        sqlq = 'SELECT calcDivsPerShareGrowthAVG as cavg, repDivsPerShareGrowthAVG as ravg \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
                    #totalDivsPaidGrowthAVG as totavg,
        resultsdf = print_DB(sqlq, 'return')
        
        calcdivs = resultsdf['cavg'][0]
        if calcdivs is None:
            calcdivs = 0
        repdivs = resultsdf['ravg'][0]
        if repdivs is None:
            repdivs = 0
        
        if pd.isnull(calcdivs) == False:# and calcdivs is not None:
            if calcdivs == 0:
                cdivsrating = -1
            elif calcdivs >= 15:
                cdivsrating = 5
            elif calcdivs < 15 and calcdivs >= 10:
                cdivsrating = 4
            elif calcdivs < 10 and calcdivs >= 5:
                cdivsrating = 3
            elif calcdivs < 5 and calcdivs >= 3:
                cdivsrating = 2
            elif calcdivs < 3 and calcdivs > 0:
                cdivsrating = 1
            elif calcdivs < 0 and calcdivs >= -3:
                cdivsrating = -2
            elif calcdivs < -3 and calcdivs >= -5:
                cdivsrating = -3
            elif calcdivs < -5 and calcdivs >= -7:
                cdivsrating = -4
            elif calcdivs < -7:
                cdivsrating = -5
        elif calcdivs > 0: #this should never be tripped, but it catches any weird anomalies
            cdivsrating = 1
        else:
            cdivsrating = -1

        if pd.isnull(repdivs) == False:# and repdivs is not None:
            if repdivs == 0:
                rdivsrating = -1
            elif repdivs >= 15:
                rdivsrating = 5
            elif repdivs < 15 and repdivs >= 10:
                rdivsrating = 4
            elif repdivs < 10 and repdivs >= 5:
                rdivsrating = 3
            elif repdivs < 5 and repdivs >= 3:
                rdivsrating = 2
            elif repdivs < 3 and repdivs > 0:
                rdivsrating = 1
            elif repdivs < 0 and repdivs >= -3:
                rdivsrating = -2
            elif repdivs < -3 and repdivs >= -5:
                rdivsrating = -3
            elif repdivs < -5 and repdivs >= -7:
                rdivsrating = -4
            elif repdivs < -7:
                rdivsrating = -5
        elif repdivs > 0: #this should never be tripped, but it catches any weird anomalies
            rdivsrating = 1
        else:
            rdivsrating = -1
      
        finalrating = max(cdivsrating, rdivsrating)#, totdivsrating)
        #saved in case ever relevant
        # totedivs = resultsdf['totavg'][0]
        # if totedivs is None:
        #     totedivs = 0

        # if pd.isnull(totedivs) == False:# and totedivs is not None:
        #     if totedivs >= 15:
        #         totdivsrating = 5
        #     elif totedivs < 15 and totedivs >= 10:
        #         totdivsrating = 4
        #     elif totedivs < 10 and totedivs >= 3:
        #         totdivsrating = 3
        #     elif totedivs < 3 and totedivs >= 0.1:
        #         totdivsrating = 2
        #     else:
        #         totdivsrating = 1
        # elif totedivs > 0: #this should never be tripped, but it catches any weird anomalies
        #     totdivsrating = 3
        # else:
        #     totdivsrating = 1
    except Exception as err:
        print('divs growth rating error:')
        print(err)
    finally:
        return finalrating

# print(divrev_rating('PLD'))

def payout_rating(ticker): 
    try:
        sqlq = 'SELECT payoutRatioAVG as pra, payoutRatioAVGintegrity as praint, payoutRatioAVGnz as pranz, \
                    fcfPayoutRatioAVG as fcfa, fcfPayoutRatioAVGintegrity as fcfaint, fcfPayoutRatioAVGnz as fcfanz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
       
        if pd.isnull(resultsdf['pra'][0]) == False and np.isinf(resultsdf['pra'][0]) == False and resultsdf['pra'][0] is not None:     
            if resultsdf['praint'][0] in ('good','decent'):
                poravg = round(resultsdf['pra'][0] * 100, 2)
            else:
                if pd.isnull(resultsdf['pranz'][0]) == False and np.isinf(resultsdf['pranz'][0]) == False and resultsdf['pranz'][0] is not None:   
                    poravg = round(resultsdf['pranz'][0] * 100, 2)
                else:
                    poravg = 0
        else:
            poravg = 0

        if poravg < 1:
            poravg = 0

        if poravg == 0:
            cdivsrating = 0
        elif poravg <= 30 and poravg > 0:
            cdivsrating = 5
        elif poravg > 30 and poravg <= 45:
            cdivsrating = 4
        elif poravg > 45 and poravg <= 75:
            cdivsrating = 3
        elif poravg > 75 and poravg <= 80:
            cdivsrating = 2
        elif poravg > 80 and poravg <= 90:
            cdivsrating = 1
        elif poravg > 90 and poravg <= 100:
            cdivsrating = -1
        elif poravg > 100:
            cdivsrating = -5

        if pd.isnull(resultsdf['fcfa'][0]) == False and np.isinf(resultsdf['fcfa'][0]) == False and resultsdf['fcfa'][0] is not None:     
            if resultsdf['fcfaint'][0] in ('good','decent'):
                fcfavg = round(resultsdf['fcfa'][0] * 100, 2)
            else:
                if pd.isnull(resultsdf['fcfanz'][0]) == False and np.isinf(resultsdf['fcfanz'][0]) == False and resultsdf['fcfanz'][0] is not None:   
                    fcfavg = round(resultsdf['fcfanz'][0] * 100, 2)
                else:
                    fcfavg = 0
        else:
            fcfavg = 0

        if fcfavg < 1:
            fcfavg = 0

        if fcfavg == 0:
            fdivsrating = 0
        elif fcfavg <= 30 and fcfavg > 0:
            fdivsrating = 5
        elif fcfavg > 30 and fcfavg <= 45:
            fdivsrating = 4
        elif fcfavg > 45 and fcfavg <= 80:
            fdivsrating = 3
        elif fcfavg > 80 and fcfavg <= 90:
            fdivsrating = 1
        elif fcfavg > 90 and fcfavg <= 100:
            fdivsrating = -1
        elif fcfavg > 100:
            fdivsrating = -5

        #if fcf po rating is higher than ni po, they deserve a better score
        if fdivsrating > cdivsrating:
            finalrating = math.ceil((fdivsrating + cdivsrating) / 2)
        else:
            finalrating = math.floor((fdivsrating + cdivsrating) / 2)
    except Exception as err:
        print('payout rating error:')
        print(err)
    finally:
        return finalrating

# print(payout_rating('TXN'))

def ffopayout_rating(ticker):
    try:
        sqlq = 'SELECT ffoPayoutRatioAVG as pra, ffoPayoutRatioAVGintegrity as praint, ffoPayoutRatioAVGnz as pranz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
       
        if pd.isnull(resultsdf['pra'][0]) == False and np.isinf(resultsdf['pra'][0]) == False and resultsdf['pra'][0] is not None:     
            if resultsdf['praint'][0] in ('good','decent'):
                poravg = round(resultsdf['pra'][0] * 100, 2)
            else:
                if pd.isnull(resultsdf['pranz'][0]) == False and np.isinf(resultsdf['pranz'][0]) == False and resultsdf['pranz'][0] is not None:   
                    poravg = round(resultsdf['pranz'][0] * 100, 2)
                else:
                    poravg = 0
        else:
            poravg = 0

        if poravg < 1:
            poravg = 0

        if poravg == 0:
            cdivsrating = -1
        if poravg <= 45 and poravg > 0:
            cdivsrating = 5
        elif poravg > 45 and poravg <= 60:
            cdivsrating = 4
        elif poravg > 60 and poravg <= 80:
            cdivsrating = 3
        elif poravg > 80 and poravg <= 90:
            cdivsrating = 1
        elif poravg > 90 and poravg <= 100:
            cdivsrating = -1
        elif poravg > 100:
            cdivsrating = -5

        finalrating = cdivsrating
    except Exception as err:
        print('ffo payout rating error:')
        print(err)
    finally:
        return finalrating

# print(ffopayout_rating('LAND'))

def roc_rating(ticker):
    try:
        sqlq = 'SELECT AveragedOverYears as years, numYearsROCpaid as numyearsroc \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        #rocyears/years gives an idea for how often the security COULD BE eroding NAV
        if pd.isnull(resultsdf['numyearsroc'][0]) == False and np.isinf(resultsdf['numyearsroc'][0]) == False and resultsdf['numyearsroc'][0] is not None: 
            rocavg = int(resultsdf['numyearsroc'][0]) / int(resultsdf['years'][0]) * 100
        else:
            rocavg = 0
        
        if rocavg == 0:
            finalrating = 5
        elif rocavg > 0 and rocavg <= 20:
            finalrating = 3
        elif rocavg > 20 and rocavg <= 30:
            finalrating = 2
        elif rocavg > 30 and rocavg <= 50:
            finalrating = 1
        elif rocavg > 50 and rocavg <= 60:
            finalrating = -1
        elif rocavg > 60 and rocavg <= 70:
            finalrating = -3
        elif rocavg > 70:
            finalrating = -5
        
    except Exception as err:
        print('roc rating error:')
        print(err)
    finally:
        return finalrating

# print(roc_rating('ARCC'))#SLRC, TRIN

def roic_rating(ticker):
    try:
        sqlq = 'SELECT roicAVG as roic, aroicAVG as ar, raroicAVG as rar \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        
        if pd.isnull(resultsdf['roic'][0]) == False and np.isinf(resultsdf['roic'][0]) == False and resultsdf['roic'][0] is not None:
            roic = resultsdf['roic'][0]
        else:
            roic = 0

        if pd.isnull(resultsdf['ar'][0]) == False and np.isinf(resultsdf['ar'][0]) == False and resultsdf['ar'][0] is not None:
            aroic = resultsdf['ar'][0]
        else:
            aroic = 0

        if pd.isnull(resultsdf['rar'][0]) == False and np.isinf(resultsdf['rar'][0]) == False and resultsdf['rar'][0] is not None:
            raroic = resultsdf['rar'][0]
        else:
            raroic = 0

        finalroic = max(roic, aroic, raroic)
        roiccompare = [20,15,10,5,1,0,-1,-2,-3]
        finalrating = rating_assignment(finalroic,roiccompare)
    except Exception as err:
        print('roic rating error:')
        print(err)
    finally:
        return finalrating

# print(roic_rating('MSTR'))

def roce_rating(ticker):
    try:
        sqlq = 'SELECT croceAVG as roic, rroceAVG as ar \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
       
        if pd.isnull(resultsdf['roic'][0]) == False and np.isinf(resultsdf['roic'][0]) == False and resultsdf['roic'][0] is not None:
            roic = resultsdf['roic'][0]
        else:
            roic = 0

        if pd.isnull(resultsdf['ar'][0]) == False and np.isinf(resultsdf['ar'][0]) == False and resultsdf['ar'][0] is not None:
            aroic = resultsdf['ar'][0]
        else:
            aroic = 0

        if aroic != 0:
            finalroic = aroic
        else:
            finalroic = max(roic, aroic)
        roiccompare = [25,10,5,3,0,-1,-2,-3,-4]
        finalrating = rating_assignment(finalroic,roiccompare)
    except Exception as err:
        print('roce rating error:')
        print(err)
    finally:
        return finalrating

# print(roce_rating('O'))

def reitroce_rating(ticker):
    try:
        sqlq = 'SELECT year, ffo, TotalEquity, ReportedTotalEquity \
                    FROM Mega \
                    WHERE Ticker LIKE \'' + ticker + '\' ORDER BY year;'
        resultsdf = print_DB(sqlq, 'return')
        
        rroce = (resultsdf['ffo'] / resultsdf['ReportedTotalEquity']).tolist()
        croce = (resultsdf['ffo'] / resultsdf['TotalEquity']).tolist()
        rroceavg = metadata.IQR_Mean(rroce)
        croceavg = metadata.IQR_Mean(croce)
        
        if rroceavg is None and croceavg is None:
            reitroce = 0
        elif rroceavg is None and croceavg is not None:
            reitroce = croceavg
        elif rroceavg is not None and croceavg is None:
            reitroce = rroceavg
        else:
            reitroce = max(rroceavg,croceavg) * 100

        roiccompare = [20,10,7,3,0,-1,-2,-3,-4]
        finalrating = rating_assignment(reitroce,roiccompare)
    except Exception as err:
        print('reit roce rating error:')
        print(err)
    finally:
        return finalrating

# print(reitroce_rating('NNN'))

def yield_rating(ticker):
    try:
        sqlq = 'SELECT repDivYieldAVG as roic, calcDivYieldAVG as ar \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
       
        if pd.isnull(resultsdf['roic'][0]) == False and np.isinf(resultsdf['roic'][0]) == False and resultsdf['roic'][0] is not None:
            roic = resultsdf['roic'][0]
        else:
            roic = 0

        if pd.isnull(resultsdf['ar'][0]) == False and np.isinf(resultsdf['ar'][0]) == False and resultsdf['ar'][0] is not None:
            aroic = resultsdf['ar'][0]
        else:
            aroic = 0

        avgyield = round((roic + aroic) / 2, 2)

        if avgyield == 0:
            finalrating = 0
        elif avgyield >= 15:
            finalrating = 1
        elif avgyield < 15 and avgyield >= 10:
            finalrating = 5
        elif avgyield < 10 and avgyield >= 6:
            finalrating = 4
        elif avgyield < 6 and avgyield >= 3:
            finalrating = 3
        elif avgyield < 3 and avgyield >= 2:
            finalrating = 2
        elif avgyield < 2 and avgyield >= 0:
            finalrating = 1
        elif avgyield < 0:
            finalrating = -5

    except Exception as err:
        print('yield rating error:')
        print(err)
    finally:
        return finalrating

#############################################################################
#sector rankings
#############################################################################
def rank_Materials():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Basic Materials\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Materials ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'B'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))
                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Materials_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank mats error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank mats error: ')
        print(err)

def rank_Communications(): 
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Communication Services\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Comms ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'C'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Communications_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank comms error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank comms error: ')
        print(err)

def rank_Energy():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Energy\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Energy ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'E'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Energy_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank energy error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank energy error: ')
        print(err)

def rank_Financials():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Financial Services\' \
                        AND Ticker NOT IN (\'ARCC\', \'BBDC\', \'BCSF\', \'BKCC\', \'BXSL\', \'CCAP\', \'CGBD\', \'FCRD\', \'CSWC\', \'GAIN\', \
                                    \'GBDC\', \'GECC\', \'GLAD\', \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \
                                    \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \
                                    \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \'SCM\', \'SLRC\', \'SSSS\', \
                                    \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\');'
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Fins ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'F'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 1
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 1
                bvv = 5
                equityv = 5
                debtv = 0
                fcfmv = 1
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 0
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (roc) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 80
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Financials_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank financials error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank financials error: ')
        print(err)

def rank_BDC():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Financial Services\' \
                        AND Ticker IN (\'ARCC\', \'BBDC\', \'BCSF\', \'BKCC\', \'BXSL\', \'CCAP\', \'CGBD\', \'FCRD\', \'CSWC\', \'GAIN\', \
                                    \'GBDC\', \'GECC\', \'GLAD\', \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \
                                    \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \
                                    \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \'SCM\', \'SLRC\', \'SSSS\', \
                                    \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\');'
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('BDCs ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'BDC'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 5
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 5
                equityv = 5
                debtv = 0
                fcfmv = 1
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 0
                yieldv = 0

                # justscore = ((ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (roc) + (po) + (bv) + (roic) + (roce) + (divyield))

                # maxscore = 75
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'BDC_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank bdc error in loop for: ' + str(x))
                print(err)
                continue

    except Exception as err:
        print('rank bdc error:')
        print(err)

def rank_ConsumerCyclical():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Consumer Cyclical\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('XLY ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'Y'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))
                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'ConsumerCyclical_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank cons cyclic error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank Consumer Cyclical error: ')
        print(err)

def rank_ConsumerDefensive():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Consumer Defensive\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('XLP ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'P'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 3
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'ConsumerDefensive_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank cons staples error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank Consumer Def error: ')
        print(err)

def rank_Healthcare():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Healthcare\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('XLV ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'V'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Healthcare_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank healthcare error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank healthcare error: ')
        print(err)

def rank_Industrials():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Industrials\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Inds ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'I'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 3
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Industrials_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank inds error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank Industrials error: ')
        print(err)

def rank_RealEstate():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Real Estate\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('RE ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'RE'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                reitroce = uploaddf['reitroce'] = reitroce_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 0
                roicv = 0
                reitrocev = 5
                rocv = 1
                ffopov = 5
                pov = 0
                divgrv = 5
                divpayv = 5
                sharesv = 0
                cfv = 0
                bvv = 5
                equityv = 5
                debtv = 0
                fcfmv = 0
                fcfv = 0
                ffov = 5
                niv = 0
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ffo) + (roc) + (bv) + (debt) + (equity) + (shares) + (divpay) + 
                #                 (divgr) + (ffopo) + (roc) + (reitroce) + (divyield))

                # maxscore = 65
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'RealEstate_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (reitroce) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + 
                                (reitroce * reitrocev) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank RE error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank real estate error: ')
        print(err)

def rank_Technology():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Technology\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('tech ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'K'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 5
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 5
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 70
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Tech_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank tech error in loop for: ' + str(x))
                print(err)
                continue
        
    except Exception as err:
        print('rank Tech error: ')
        print(err)

def rank_Utilities():
    try:
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Utilities\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print('Utils ' + str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'U'
                roce = uploaddf['roce'] = roce_rating(x)
                roic = uploaddf['roic'] = roic_rating(x)
                roc = uploaddf['roc'] = roc_rating(x)
                ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
                po = uploaddf['po'] = payout_rating(x)
                divgr = uploaddf['divgr'] = divrev_rating(x)
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
                rev = uploaddf['rev'] = rev_rating(x)
                divyield = uploaddf['divyield'] = yield_rating(x)
                #v = value to be VALUED at lol
                rocev = 5
                roicv = 0
                rocv = 0
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 0
                fcfmv = 0
                fcfv = 0
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 0

                # justscore = ((rev) + (ni) + (fcf) + (fcfm) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                #                 (divgr) + (po) + (roic) + (roce) + (divyield))

                # maxscore = 75
                # uploaddf['maxscore'] = maxscore
                # uploaddf['score'] = justscore
                # uploaddf['scorerank'] = justscore / maxscore
                # uploadToDB(uploaddf,'Utilities_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploaddf['scorerank'] = finalscore / srmaxscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank utilities error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank utils error: ')
        print(err)

#luke here a copy rankings function

def clear_rankings():
    conn = sql.connect(db_path)
    query = conn.cursor()
    sector = 'DELETE FROM Sector_Rankings'
    query.execute(sector)
    conn.commit()
    query.close()
    conn.close()

    print_DB('SELECT * FROM Sector_Rankings','print')

def fillSectorRankings():
    try:
        rank_Materials()
        rank_Communications()
        rank_Energy()
        rank_Financials()
        rank_BDC()
        rank_Industrials()
        rank_Technology()
        rank_ConsumerDefensive()
        rank_RealEstate()
        rank_Utilities()
        rank_Healthcare()
        rank_ConsumerCyclical() 
    except Exception as err:
        print('fill fulls sector rankings error: ')
        print(err)

# clear_rankings()
# fillSectorRankings()

#####################################################################################
# return sector rankings
#####################################################################################
#luke here, make functions for each sector
def getUtilityRankings():
    try:
        sr = 'Select * \
                From Sector_Rankings \
                WHERE Sector LIKE \'U\' \
                ORDER BY scorerank DESC;'
        retdf = print_DB(sr,'return')
    except Exception as err:
        print('check sr err:')
        print(err)
    finally:
        return retdf

# print(checkUtilityRankings())

def getHealthcareRankings():
    try:
        sr = 'Select * \
                From Sector_Rankings \
                WHERE Sector LIKE \'V\' \
                ORDER BY scorerank DESC;'
        retdf = print_DB(sr,'return')
    except Exception as err:
        print('check sr err:')
        print(err)
    finally:
        return retdf

# print(checkHealthcareRankings())

##############
#deprecated
##############
#used to help define function, deprecate later
def checkreitroce():
    try:
        getit = 'SELECT DISTINCT(Ticker) as ticker FROM Mega WHERE Sector LIKE \'%Real Est%\''
        df = print_DB(getit, 'return')
        gathered = []
        n = 1
        for x in df['ticker']:
            val = reitroce_rating(x)
            gathered.append(val)
            print(str(round(n/len(df['ticker']),4)*100) + '% complete!')
            n += 1

        # print(min(gathered))
        # print(max(gathered))
        # print(sum(gathered)/len(gathered))
    except Exception as err:
        print(str(x) + ' failed for some reason:')
        print(err)
    finally:
        print(min(gathered))
        print(max(gathered))
        print(sum(gathered)/len(gathered))

# checkreitroce()

def checkUtilitiesRankings():
    try:
        sr = 'Select * From Utilities_Ranking \
                Where scorerank > 0.5 \
                ORDER BY scorerank DESC;'
        retdf = print_DB(sr,'return')
    except Exception as err:
        print('check util ranks err:')
        print(err)
    finally:
        return retdf

# print(checkUtilitiesRankings())

def compareRankers(sectorletter, sector):

    yes = 'select * From Sector_Rankings Where Sector LIKE \'' + sectorletter + '\' AND Ticker IN (\'O\') ORDER BY scorerank DESC;' #ticker, bv, equity, shares, debt 
    sr = print_DB(yes, 'return')

    no = 'select * From ' + sector + '_Ranking Where Ticker IN (\'O\') ORDER BY scorerank DESC ;' #Where Ticker IN (\'O\',\'ADC\',\'PLD\',\'STAG\') 
    spr = print_DB(no, 'return')
    combineddf = pd.DataFrame()

    for x in sr:
        print(x)
        combineddf['sr'] = sr[x]
        combineddf['spr'] = spr[x]
        print(combineddf)

# compareRankers('RE','RealEstate')

### deprecated, later added to front end for user to decide hwo to filter it down
def getInvestableHealthcare():
    try:
        sr = 'Select * \
                From Sector_Rankings \
                WHERE Sector LIKE \'V\' \
                AND scorerank > 0 \
                AND divpay == 1 \
                AND rev > 2 \
                AND ni > 2 \
                AND roce > 3 \
                AND po >= 4 \
                AND divgr > 3 \
                AND cf > 0 \
                AND equity >= 4 \
                AND fcfm > 1 \
                AND divgr > 1 \
                ORDER BY scorerank DESC;'
        retdf = print_DB(sr,'return')
    except Exception as err:
        print('check sr err:')
        print(err)
    finally:
        return retdf

# print(getInvestableHealthcare())

def getInvestableUtilities():
    try:
        sr = 'Select * \
                From Sector_Rankings \
                WHERE Sector LIKE \'U\' \
                AND scorerank > 0 \
                AND divpay == 1 \
                AND rev >= 2 \
                AND ni > 3 \
                AND roce > 3 \
                AND po > 0 \
                AND divgr > 0 \
                AND cf > 0 \
                AND equity >= 4 \
                AND divgr > 1 \
                ORDER BY scorerank DESC;'
        retdf = print_DB(sr,'return')
    except Exception as err:
        print('check sr err:')
        print(err)
    finally:
        return retdf

#deprecated, unused tables going forward
def clear_rankings2():
    conn = sql.connect(db_path)
    query = conn.cursor()
    mats = 'DELETE FROM Materials_Ranking'
    query.execute(mats)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    coms = 'DELETE FROM Communications_Ranking'
    query.execute(coms)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    en = 'DELETE FROM Energy_Ranking'
    query.execute(en)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    fin = 'DELETE FROM Financials_Ranking'
    query.execute(fin)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    fin2 = 'DELETE FROM BDC_Ranking'
    query.execute(fin2)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    ind = 'DELETE FROM Industrials_Ranking'
    query.execute(ind)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    tech = 'DELETE FROM Tech_Ranking'
    query.execute(tech)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    stap = 'DELETE FROM ConsumerDefensive_Ranking'
    query.execute(stap)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    re = 'DELETE FROM RealEstate_Ranking'
    query.execute(re)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    util = 'DELETE FROM Utilities_Ranking'
    query.execute(util)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    hc = 'DELETE FROM Healthcare_Ranking'
    query.execute(hc)
    conn.commit()
    query.close()
    conn.close()

    conn = sql.connect(db_path)
    query = conn.cursor()
    cd = 'DELETE FROM ConsumerCyclical_Ranking'
    query.execute(cd)
    conn.commit()
    query.close()
    conn.close()

    # print_DB('SELECT * FROM Sector_Rankings','print')
    print_DB('SELECT * FROM Materials_Ranking','print')
    print_DB('SELECT * FROM Communications_Ranking','print')
    print_DB('SELECT * FROM Energy_Ranking','print')
    print_DB('SELECT * FROM Financials_Ranking','print')
    print_DB('SELECT * FROM BDC_Ranking','print')
    print_DB('SELECT * FROM Industrials_Ranking','print')
    print_DB('SELECT * FROM Tech_Ranking','print')
    print_DB('SELECT * FROM ConsumerDefensive_Ranking','print')
    print_DB('SELECT * FROM RealEstate_Ranking','print')
    print_DB('SELECT * FROM Utilities_Ranking','print')
    print_DB('SELECT * FROM Healthcare_Ranking','print')
    print_DB('SELECT * FROM ConsumerCyclical_Ranking','print')

# clear_rankings2()