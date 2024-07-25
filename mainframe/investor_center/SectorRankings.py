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

#going to have to manually review all of these rankings, to verify the integrity of rankings is what our company stands by #luke
# debate full clearing sector rankings, vs snapshots, vs just keeping them in for more metadata; note below


#rev: [15, 7, 3, 2, 0, -1, -2, -3, -4]
#roic: [20,15,7,5,1,0,-1,-5,-7]
#roce: [25,15,10,5,1,0,-1,-5,-10]

#ni: 2==2+, 3==4-7, same ffo
#fcf: [10, 7, 4, 2, 0, -1, -2, -3, -4]
#fcfm: 1== >0
#debt: 3 == 1-10+
#equity: [10,5,1,0,-1,-2,-3,-4,-5]
#bv/nav: ;[10,5,1,0,-1,-2,-3,-4,-5]
#cf: [7,4,2,0,-1,-5,-7,-10,-15] op/netcf
#shares: 2 lowest, <=10+
#divspaid
#divgrowth: 2== >=3
#po: 2 == <80, ffo same
#yield: 1 == 2-3%, 3+ ideal 3%+

#luke here edit this to reflect actuality
#individual stock reports: go thru each section below. RATING each section as 5=amazing, 4=good, 3=acceptable, 2=subpar, 1=bad
#sector rankings have to provide each of the following, then calculate a weighted score, grading each stock in each sector
##so out of 5: 5=amazing, 4=good, 3=acceptable, 2=subpar, 1=bad
##then that score is multiplied by a weighting factor based on the user's preferences, or preset screens. (grade)(weighting) = overall score

###
# Each security scores according to its own financial records. Then it also has a weighted score for the sector it is in.
# The first part is how we weight investment decisions as a whole, in a vacuum.
# The sector weightings is how we would analyze a stock in that sector.
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

def growth_rating(ticker):
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

# print(growth_rating('F'))

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
        elif avg > 1 and avg <= 10:
            finalrating = 3
        elif avg > 10 and avg <= 15:
            finalrating = 1
        elif avg > 15 and avg <= 18:
            finalrating = -1
        elif avg > 18 and avg <= 20:
            finalrating = -2
        elif avg > 20 and avg <= 25:
            finalrating = -3
        elif avg > 25 and avg <= 30:
            finalrating = -4
        elif avg > 30:
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

        finalrating = max(rfinalrating, cfinalrating)
    except Exception as err:
        print('equity rating error:')
        print(err)
    finally:
        return finalrating

# print(equity_rating('TXN'))

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
            reqavg = 1

        if pd.isnull(resultsdf['cgravg'][0]) == False and np.isinf(resultsdf['cgravg'][0]) == False and pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:      
            ceqavg = max(resultsdf['cgravg'][0], resultsdf['cgravgnz'][0])
        else:
            ceqavg = 1
        
        avg = max(reqavg, ceqavg)

        if pd.isnull(resultsdf['navgravg'][0]) == False and np.isinf(resultsdf['navgravg'][0]) == False:
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

# print(bvnav_rating('MSFT'))

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
        
        rcompare = [7,4,2,0,-1,-5,-7,-10,-15] 
        rrating = rating_assignment(reqavg,rcompare)
        ccompare = [7,4,2,0,-1,-2,-3,-4,-5] 
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
            reqavg = 12
       
        if reqavg <= 0:
            finalrating = 5
        elif reqavg > 0 and reqavg <= 5:
            finalrating = 4
        elif reqavg > 5 and reqavg <= 7:
            finalrating = 3
        elif reqavg > 7 and reqavg <= 10:
            finalrating = 2
        elif reqavg > 10 and reqavg <= 15:
            finalrating = 1
        elif reqavg > 15 and reqavg <= 20:
            finalrating = -1
        elif reqavg > 20 and reqavg <= 25:
            finalrating = -2
        elif reqavg > 25 and reqavg <= 30:
            finalrating = -3
        elif reqavg > 30 and reqavg <= 35:
            finalrating = -4
        elif reqavg > 35:
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

def divgrowth_rating(ticker):
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

# print(divgrowth_rating('PLD'))

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
        roiccompare = [25,15,10,5,1,0,-1,-2,-3]
        finalrating = rating_assignment(finalroic,roiccompare)
    except Exception as err:
        print('roce rating error:')
        print(err)
    finally:
        return finalrating

# print(roce_rating('O'))

def reitroce_rating(ticker):
    try:
        #luke here
        #add reitroce to all sector rankings
        #migrate models
        #you need ffo from mega, and TotalEquity, ReportedTotalEquity
        #calc ffo / TE,RTE, , return which is higher
        #then get average from that list
        #then grade and return it. that's your reit roce my dude
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
        roiccompare = [25,15,10,5,1,0,-1,-2,-3]
        finalrating = rating_assignment(finalroic,roiccompare)
    except Exception as err:
        print('roce rating error:')
        print(err)
    finally:
        return finalrating

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
        elif avgyield < 15 and avgyield >= 12:
            finalrating = 5
        elif avgyield < 12 and avgyield >= 8:
            finalrating = 4
        elif avgyield < 8 and avgyield >= 3:
            finalrating = 3
        elif avgyield < 3 and avgyield >= 2:
            finalrating = 1
        elif avgyield < 2 and avgyield >= 1:
            finalrating = -1
        elif avgyield < 1:
            finalrating = -5

    except Exception as err:
        print('yield rating error:')
        print(err)
    finally:
        return finalrating

#############################################################################
#luke here start filling sector rankings, also fill the individual sector tables with raw scores, not weighted scores like sector rankings
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'B'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 1
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 3
                yieldv = 1
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

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))
                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Materials_Ranking')

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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'C'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 1
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 3
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Communications_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank comms error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank comms error: ')
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'Y'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 1
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 4
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))
                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'ConsumerCyclical_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'P'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 1
                fcfmv = 2
                fcfv = 2
                ffov = 0
                niv = 2
                revv = 3
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'ConsumerDefensive_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank cons staples error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank Consumer Def error: ')
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'E'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 5
                fcfmv = 1
                fcfv = 1
                ffov = 0
                niv = 1
                revv = 1
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Energy_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
        tickergrab = 'SELECT Ticker as ticker FROM Metadata WHERE Sector Like \'Financial Services\''
        tickers = print_DB(tickergrab, 'return')
        length1 = len(tickers['ticker'])
        n = 1
        
        for x in tickers['ticker']:
            try:
                uploaddf = pd.DataFrame()
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'F'
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
                rocv = 1
                ffopov = 0
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 3
                cfv = 3
                bvv = 5
                equityv = 5
                debtv = 3
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 1
                yieldv = 3

                #these brought out the best
                sqldf = sqldf[sqldf.years >= 10]
                # # AND netIncomeGrowthAVG >= 3 \
                # sqldf = sqldf[sqldf.nigr >= 0]
                # # AND (divgr >= 8 AND divgr <= 30) OR (divgr2 >= 8) \
                # sqldf = sqldf[sqldf.divgr.between(8,20)]
                # # AND payoutRatioAVG <= 0.5 \
                # sqldf = sqldf[sqldf.payoutRatioAVG <= 0.5]
                # # AND equity >= 3 \
                # sqldf = sqldf[sqldf.equity >= 3.5]
                # # AND operatingCashFlowAVG > 0 \
                # sqldf = sqldf[sqldf.operatingCashFlowAVG >= 1000000000]
                # # AND netCashFlowAVG > 0 \
                # sqldf = sqldf[sqldf.netCashFlowAVG >= 100000000]
                # # AND roic > 10 \
                # sqldf = sqldf[sqldf.roic >= 10]
                # # AND roce > 10 \
                # sqldf = sqldf[sqldf.roce >= 10]

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (roc) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 80
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Financials_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank financials error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank financials error: ')
        print(err)

#This could be usefully added to sector rankings, but it may be tricky. Might need to add tickers there, 'not in' #luke
def selectingBDC():
    try:
        bdcRanks = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG as po, \
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

        print_DB(bdcRanks, 'print')
        # csv.simple_saveDF_to_csv('',print_DB(bdcRanks, 'return'), 'z-BDClist', False)
    except Exception as err:
        print('select bdc error:')
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'V'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 1
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 3
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Healthcare_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'I'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 1
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 3
                fcfmv = 3
                fcfv = 3
                ffov = 0
                niv = 3
                revv = 4
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Industrials_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'RE'
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
                rocv = 1
                ffopov = 5
                pov = 0
                divgrv = 5
                divpayv = 5
                sharesv = 2
                cfv = 3
                bvv = 5
                equityv = 5
                debtv = 2
                fcfmv = 1
                fcfv = 1
                ffov = 5
                niv = 1
                revv = 3
                yieldv = 1

                justscore = ((rev) + (ni) + (ffo) + (fcf) + (fcfm) + (roc) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (ffopo) + (roic) + (roce) + (divyield))

                maxscore = 85
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'RealEstate_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'K'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 3
                cfv = 5
                bvv = 0
                equityv = 5
                debtv = 3
                fcfmv = 5
                fcfv = 5
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 70
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Tech_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
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
                print(str(round(n/length1,4)*100) + '% complete!')
                uploaddf['Ticker'] = [x]
                uploaddf['Sector'] = 'U'
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
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 2
                cfv = 1
                bvv = 5
                equityv = 5
                debtv = 1
                fcfmv = 1
                fcfv = 1
                ffov = 0
                niv = 5
                revv = 5
                yieldv = 1

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 75
                uploaddf['maxscore'] = maxscore
                uploaddf['score'] = justscore
                uploadToDB(uploaddf,'Utilities_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'Sector_Rankings')
                n += 1
            except Exception as err:
                print('rank utilities error in loop for: ' + str(x))
                print(err)
                continue
    except Exception as err:
        print('rank utils error: ')
        print(err)

# rank_Materials()
# rank_Communications()
# rank_Energy()
# rank_Financials()
# rank_Industrials()
# rank_Technology()
# rank_ConsumerDefensive()
# rank_RealEstate()
# rank_Utilities()
# rank_Healthcare()
# rank_ConsumerCyclical() 