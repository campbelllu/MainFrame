import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# import seaborn as sns
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
from currency_converter import CurrencyConverter #https://pypi.org/project/CurrencyConverter/
converter_address = './currency-hist.csv'
curConvert = CurrencyConverter(converter_address, fallback_on_missing_rate=True)
### Documentation: https://pypi.org/project/CurrencyConverter/ 
import os
import django
import sys
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# from django.db import connection
# with connection.cursor() as cursor:
#     cursor.execute("VACUUM;")
#luke here this block after you migrate tables

from django.conf import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainframe.settings')
django.setup()
db_path = settings.DATABASES['default']['NAME']

#From fellow files
import csv_modules as csv

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}
#EDGAR API Endpoints
#companyconcept: returns all filing data from specific company, specific accounting item. timeseries for 'assets from apple'?
#company facts: all data from filings for specific company 
#frames: cross section of data from every company filed specific accnting item in specific period. quick company comparisons
ep = {"cc":"https://data.sec.gov/api/xbrl/companyconcept/" , "cf":"https://data.sec.gov/api/xbrl/companyfacts/" , "f":"https://data.sec.gov/api/xbrl/frames/"}

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

###
#EVERYTHING RELATED TO stockList TABLE
###
def getTickersCIKs():
    #Talk to EDGAR, upload tickers and ciks to stocklist; fully working 1/29/25
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()

        #Get our tickers+ciks DF
        tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
        time.sleep(0.1) #Respect the EDGAR
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik['CIK'] = tickers_cik['cik_str']#.astype(str).str.zfill(10) #redacted, done later, saves DB space
        tickers_cik = tickers_cik.drop('cik_str',axis=1)
        tickers_cik = tickers_cik.drop('title',axis=1)
        tickers_cik = tickers_cik.drop_duplicates(subset='CIK', keep='first')
        tickers_cik = tickers_cik.rename(columns={'ticker': 'Ticker'})
        #Only insert records that aren't already there
        insertquery = """
                        INSERT INTO stockList (Ticker, CIK)
                        SELECT ?, ?
                        WHERE NOT EXISTS (
                            SELECT 1 FROM stockList WHERE Ticker = ?
                        );
                    """
        #First save how many Rows we started with
        print('Starting upload process:')
        orig_count = print_DB('SELECT COUNT(*) FROM stockList;', 'return')
        #Now put them in the DB
        for row in tickers_cik[['Ticker', 'CIK']].values.tolist():
            query.execute(insertquery, (row[0], row[1], row[0]))
        # query.executemany(insertquery, tickers_cik[['Ticker', 'CIK']].values.tolist())
        conn.commit()

        #Finally tell us how many Rows we ended up with
        print('Starting and Final Row Count in stockList:')
        print('Starting: ' +  str(orig_count))
        print('Final: ')
        print_DB('SELECT COUNT(*) FROM stockList;', 'print')

    except Exception as err:
        print('getTickersCIKs error: ')
        print(err)
    finally:
        query.close()
        conn.close()

lock = threading.Lock()
counter = 0

#Fill Sectors and Industries
def scrapeSnI(ticker):
    global counter
    try:
        conn = sql.connect(db_path, check_same_thread=False) #Allows multithreading
        query = conn.cursor()
        stock = yf.Ticker(ticker)
        # dict1 = stock.info
        sector = stock.info.get("sector", "Unknown")#dict1['sector']
        industry = stock.info.get("industry", "Unknown")#dict1['industry']

        insertquery = """ 
                        INSERT INTO stockList (Ticker, Sector, Industry)
                        VALUES (?, ?, ?)
                        ON CONFLICT(Ticker) DO UPDATE
                        SET Sector = ?, Industry = ?;
        """
        query.execute(insertquery, (str(ticker), str(sector), str(industry), str(sector), str(industry)))
        conn.commit()
        
        with lock:
            counter += 1
            print(f"[{counter}] Updated {ticker}: {sector}, {industry}")

        time.sleep(random.uniform(5,10)) #Trying to repect rate limits here, kind of a black box as of 1/29/25.

    except Exception as err:
        print('scrape sni error: ')
        print(err)
    finally:
        query.close()
        conn.close()
#ties it all together. 
def threadSnI():
    try:
        needsData = print_DB('SELECT Ticker FROM stockList WHERE Sector IS NULL OR Industry IS NULL;', 'return')
        length1 = len(needsData['Ticker'])
        print(f"Starting Ticker, CIK, Sector, Industry Updates for {length1} tickers...")

        with ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(scrapeSnI, needsData['Ticker'])

        print(f"Update complete!")
    except Exception as err:
        print('threading scrape sni error: ')
        print(err)

def fillStockListTable():
    try:
        getTickersCIKs()
        #Checking for Duplicates, Test
        # print_DB('SELECT Ticker FROM stockList GROUP BY Ticker HAVING COUNT(*) > 1;', 'print')
        threadSnI()
    except Exception as err:
        print('filling stockList Wrapper error: ')
        print(err)
###
#EVERYTHING RELATED TO stockList TABLE ENDS HERE
###

#Referenced by later functions
nsd = 'SELECT Ticker, CIK, Sector, Industry FROM stockList;'
gSdf = print_DB(nsd, 'return')
nameSectorDict = gSdf.set_index('Ticker')['Sector'].to_dict()
#just for ciks #.astype(str).str.zfill(10).to_dict()
cik_dict = gSdf.set_index('Ticker')['CIK'].astype(str).str.zfill(10).to_dict()
nameIndustryDict = gSdf.set_index('Ticker')['Industry'].to_dict()

def EDGAR_query(ticker, cik, header, tag: list=None) -> pd.DataFrame:
    try:   
        url = ep["cf"] + 'CIK' + cik + '.json'
        response = requests.get(url, headers=header)
        filingList = ['us-gaap','ifrs-full']
        company_data = pd.DataFrame()
        held_data = pd.DataFrame()
        tags = tag
        if len(tags) == 0:
            tags = list(response.json()['facts']['us-gaap'].keys())

        for x in filingList:
            for i in range(len(tags)):
                try:
                    tag = tags[i] 
                    units = list(response.json()['facts'][x][tag]['units'].keys())#[0] 
                    for y in units:
                        data = pd.json_normalize(response.json()['facts'][x][tag]['units'][y])#[units])
                        data['Tag'] = tag
                        data['Units'] = y
                        data['Ticker'] = ticker
                        data['CIK'] = cik
                        held_data = pd.concat([held_data, data], ignore_index = True)
                    company_data = pd.concat([company_data, held_data], ignore_index = True)
                except Exception as err:
                    pass

        return company_data
    except Exception as err:
        print('edgar query super error')
        print(err)

### RESOURCES TO HELP WITH EDGAR JSON DECODING
### amazing resource to check what each element is: https://www.calcbench.com/element/WeightedAverageNumberOfSharesIssuedBasic 
### THIS WILL TEACH YOU MUCH I THINK: https://xbrl.us/guidance/specific-non-controlling-interest-elements/ 
# altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
# cashOnHand = ['CashCashEquivalentsAndShortTermInvestments', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 
#                 'CashAndCashEquivalentsAtCarryingValue', 'CashEquivalentsAtCarryingValue', 
#                 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations']
# incomeTaxPaid = ['IncomeTaxExpenseContinuingOperations'] #never used?
# exchangeRate = ['EffectOfExchangeRateChangesOnCashAndCashEquivalents'] #You'll want to know this is here eventually, unlikely with curr.converter

netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 
                'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect', 
                'IncreaseDecreaseInCashAndCashEquivalents', 'CashAndCashEquivalentsPeriodIncreaseDecrease',
                'IncreaseDecreaseInCashAndCashEquivalentsBeforeEffectOfExchangeRateChanges'] #operCF + InvestCF + FinancingCF
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities','CashFlowsFromUsedInOperatingActivities',
                        'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 'NetCashProvidedByUsedInContinuingOperations', 
                        'CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital','CashFlowsFromUsedInOperations',
                        'CashFlowsFromUsedInOperatingActivitiesContinuingOperations']
investingCashFlow = ['CashFlowsFromUsedInInvestingActivities','NetCashProvidedByUsedInInvestingActivities']
financingCashFlow = ['CashFlowsFromUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivities']

revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenueFromContractsWithCustomers', 'SalesRevenueNet', 'Revenues', 
            'RealEstateRevenueNet', 'Revenue','RevenueFromContractWithCustomerIncludingAssessedTax','GrossInvestmentIncomeOperating',
            'RevenueFromRenderingOfTelecommunicationServices'] #banks?! GrossInvestmentIncomeOperating #totally not revenue how?!?

netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic']
# netIncomeNCI = ['ProfitLoss', 'ProfitLossAttributableToOwnersOfParent']

operatingIncome = ['OperatingIncomeLoss','ProfitLossFromOperatingActivities']

taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense','FinanceCosts','InterestExpenseDebt','InterestAndDebtExpense','InterestIncomeExpenseNet',
                'InterestIncomeExpenseNonoperatingNet', 'FinancingInterestExpense','InterestPaidNet','InterestRevenueExpense']

shortTermDebt = ['LongTermDebtCurrent','ShorttermBorrowings']
longTermDebt1 = ['LongTermDebtNoncurrent','NoncurrentPortionOfNoncurrentBondsIssued']#,'LongTermDebt']
longTermDebt2 = ['OperatingLeaseLiabilityNoncurrent','NoncurrentPortionOfNoncurrentLoansReceived']
longTermDebt3 = ['NoncurrentLeaseLiabilities']
longTermDebt4 = ['LongtermBorrowings']

totalAssets = ['Assets','LiabilitiesAndStockholdersEquity']
currentAssets = ['CurrentAssets']
nonCurrentAssets = ['NoncurrentAssets']
totalLiabilities = ['Liabilities']
currentLiabilities = ['LiabilitiesCurrent','CurrentLiabilities']
nonCurrentLiabilities = ['LiabilitiesNoncurrent','NoncurrentLiabilities']
shareHolderEquity = ['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
                        'EquityAttributableToOwnersOfParent','PartnersCapital','Equity', 'MembersCapital']

capEx = ['PaymentsToAcquirePropertyPlantAndEquipment','PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities',
        'PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets',
        'PaymentsToAcquireProductiveAssets', 'PaymentsForCapitalImprovements','PaymentsToAcquireOtherPropertyPlantAndEquipment',
        'PaymentsForProceedsFromProductiveAssets','PaymentsToDevelopRealEstateAssets',
        'PurchaseOfAvailableforsaleFinancialAssets','PaymentsToAcquireAndDevelopRealEstate'] 

totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends','DividendsCommonStock','DividendsCommonStockCash',
                            'DividendsPaidClassifiedAsFinancingActivities','DividendsPaid',
                            'DividendsPaidToEquityHoldersOfParentClassifiedAsFinancingActivities','PartnersCapitalAccountDistributions',
                            'DividendsPaidOrdinaryShares','DividendsPaidClassifiedAsOperatingActivities','PaymentsOfOrdinaryDividends'] 
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid',
                                            'InvestmentCompanyDistributionToShareholdersPerShare',
                                            'DistributionMadeToLimitedPartnerDistributionsPaidPerUnit','DividendsPaidOrdinarySharesPerShare']
returnOfCapitalPerShare = ['InvestmentCompanyTaxReturnOfCapitalDistributionPerShare']
totalReturnOfCapital = ['InvestmentCompanyTaxReturnOfCapitalDistribution']

eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare','BasicEarningsLossPerShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic', 'EntityCommonStockSharesOutstanding','WeightedAverageShares', 
                            'CommonStockSharesOutstanding', 'NumberOfSharesIssued']
dilutedSharesOutstanding = ['WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted']

gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes',
                    'GainsLossesOnSalesOfInvestmentRealEstate']
deprecAndAmor = ['DepreciationDepletionAndAmortization','Depreciation','DepreciationAmortizationAndAccretionNet','AmortizationOfIntangibleAssets',
                    'AdjustmentsForDepreciationAndAmortisationExpense','DeferredTaxLiabilityAsset','AdjustmentsForDepreciationExpense']
deprecAndAmor2 = ['AmortizationOfMortgageServicingRightsMSRs']
deprecAndAmor3 = ['DepreciationAndAmortization']

netAssetValue = ['NetAssetValuePerShare'] 

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, longTermDebt3, longTermDebt4, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow, 
                investingCashFlow, financingCashFlow, currentLiabilities, nonCurrentLiabilities, deprecAndAmor2, 
                deprecAndAmor3, shareHolderEquity, currentAssets, nonCurrentAssets, netAssetValue, dilutedSharesOutstanding, 
                returnOfCapitalPerShare, totalReturnOfCapital ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'longTermDebt3', 'longTermDebt4',  'currentLiabilities','nonCurrentLiabilities',
                'deprecAndAmor2', 'deprecAndAmor3', 'shareHolderEquity', 'currentAssets','nonCurrentAssets', 'netAssetValue', 'dilutedSharesOutstanding', 
                'returnOfCapitalPerShare', 'totalReturnOfCapital']
# removedFromUltList = [cashOnHand, altVariables, 'incomeTaxPaid',incomeTaxPaid,'exchangeRate',exchangeRate,'netIncomeNCI', ]

ultimateTagsList = [item for sublist in ultimateList for item in sublist]

#Begin data cleaning process
def get_Only_10k_info(df):
    try:
        filtered_data = pd.DataFrame()
        formList = ['10-K','20-F','40-F','6-K']
        filtered_data = df[df['form'].isin(formList) == True] 
    except Exception as err:
        print("10k filter error")
        print(err)
    finally:
        return filtered_data

def dropAllExceptFYRecords(df):
    try:
        testdf = df
        returned_data = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-12-')==True)]
        oneEnds = ['-01-','-02-']#'-12',
        twoEnds = ['-01-','-02-','-03-']
        threeEnds = ['-02-','-03-','-04-']
        fourEnds = ['-03-','-04-','-05-']
        fiveEnds = ['-04-','-05-','-06-']
        sixEnds = ['-05-','-06-','-07-']
        sevenEnds = ['-06-','-07-','-08-']
        eightEnds = ['-07-','-08-','-09-']
        nineEnds = ['-08-','-09-','-10-']
        tenEnds = ['-09-','-10-','-11-']
        elevenEnds = ['-10-','-11-','-12-']
        twelveEnds = ['-11-','-12-','-01-']
        countdown = ['-01-','-02-','-03-','-04-','-05-','-06-','-07-','-08-','-09-','-10-','-11-']
        revCD = reversed(countdown)

        for x in oneEnds:
            # returned_data = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-12-')==True)]
            held_data = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True) 
       
        for x in twoEnds:
            held_data = df[(df['start'].str.contains('-02-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in threeEnds:
            held_data = df[(df['start'].str.contains('-03-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
       
        for x in fourEnds:
            held_data = df[(df['start'].str.contains('-04-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in fiveEnds:
            held_data = df[(df['start'].str.contains('-05-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in sixEnds:
            held_data = df[(df['start'].str.contains('-06-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
       
        for x in sevenEnds:
            held_data = df[(df['start'].str.contains('-07-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in eightEnds:
            held_data = df[(df['start'].str.contains('-08-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in nineEnds:
            held_data = df[(df['start'].str.contains('-09-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in tenEnds:
            held_data = df[(df['start'].str.contains('-10-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        
        for x in elevenEnds:
            held_data = df[(df['start'].str.contains('-11-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)

        for x in twelveEnds:
            held_data = df[(df['start'].str.contains('-12-')==True) & (df['end'].str.contains(x)==True) & (df.end.str[:4] != df.start.str[:4])]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        #Now checking for those halfies because some companies just file things weirdly. Still including start dates
        for x in revCD:
            held_data1 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains(x)==True)]
            if held_data1.empty:
                continue
            else:
                lastKnownLog = x
                held_data2 = df[(df['start'].str.contains(lastKnownLog)==True) & (df['end'].str.contains('-12-')==True)]
                held3 = pd.merge(held_data1, held_data2, on=['Ticker','CIK','Units','fp','fy','form','frame','filed','Tag','accn'], how='outer')
                held3['val'] = held3['val_x'] + held3['val_y']
                held3['start'] = held3['start_x']
                held3['end'] = held3['end_y']
                held3 = held3.drop(columns=['val_x','val_y','start_x','start_y','end_x','end_y'])
                held3 = held3.dropna(subset=['val'])#,'start'])
                returned_data = pd.concat([returned_data, held3], ignore_index = True)
        

        # No start dates and some monthly reporters make things weird, empty here.
        # So just pass the whole data set to the sorter and duplicate trimmer, let them deal with it
        if returned_data.empty:
            returned_data = df
           
        return returned_data
    except Exception as err:
        print("drop all except FY data rows error")
        print(err)

def orderAttributeDF(df):
    try:
        filtered_data = pd.DataFrame()
        filtered_data = df.sort_values(by=['end','val'], ascending=True)
    except Exception as err:
        print("order attribute error")
        print(err)
    finally:
        return filtered_data

def dropDuplicatesInDF(df):
    try:
        filtered_data = df
        endYear = []
        endMonth = []
        startYear = []
        
        for x in filtered_data['end']: #Prep endyear-related for year calc's
            #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
            endYear.append(int(x[:4]))
            endMonth.append(int(x[5:7]))
        filtered_data['endYear'] = endYear
        filtered_data['endMonth'] = endMonth
        yearMinusOne = list(filtered_data['endYear'] - 1)
        yearMinusOne = [str(x) for x in yearMinusOne]
        filtered_data['yearMinusOne'] = yearMinusOne
        if filtered_data['start'].isnull().all(): #Did we get a dataset that doesn't include starts?
            filtered_data['startYear'] = 0
            filtered_data['year7'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 5)
            filtered_data['year8'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 6)
            filtered_data['year9'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 7)
            filtered_data['year10'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 8)
            filtered_data['year11'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 9) 
            filtered_data['year12'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 10)
            filtered_data['year13'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 11)
            filtered_data['year14'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 12)


            filtered_data['year'] = filtered_data['year8'].fillna(filtered_data['year9'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year7'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year10'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year11'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year12'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year13'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year14'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['yearMinusOne'])
         
            filtered_data = filtered_data.drop('year7',axis=1)
            filtered_data = filtered_data.drop('year8',axis=1)
            filtered_data = filtered_data.drop('year9',axis=1)
            filtered_data = filtered_data.drop('year10',axis=1)
            filtered_data = filtered_data.drop('year11',axis=1)
            filtered_data = filtered_data.drop('year12',axis=1)
            filtered_data = filtered_data.drop('year13',axis=1)
            filtered_data = filtered_data.drop('year14',axis=1)

        else: #Otherwise fill necessary columns for year calc's
            for x in filtered_data['start']:
                #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
                if type(x) == float:
                    startYear.append(0)
                else:
                    startYear.append(int(x[:4]))
            filtered_data['startYear'] = startYear
            filtered_data['yearDiff'] = (filtered_data['endYear'] - filtered_data['startYear']).where((filtered_data['endYear'] > filtered_data['startYear']))
            filtered_data['yearDiff2'] = (filtered_data['endYear'] - filtered_data['startYear']).where((filtered_data['endYear'] == filtered_data['startYear']))
            filtered_data['yearDiff'] = filtered_data['yearDiff'].fillna(filtered_data['yearDiff2'])
            filtered_data['yearDiff'] = filtered_data['yearDiff'].fillna(3.0)
            filtered_data = filtered_data.drop('yearDiff2',axis=1)

            ###Case: yearDiff == 3: drop that row because report given to sec is just wrong
            filtered_data = filtered_data[filtered_data['yearDiff'] < 3]
            
            ###Case: yearDiff == 2: year = (end - 1)
            filtered_data['year1'] = filtered_data['yearMinusOne'].where(filtered_data['yearDiff'] == 2)
           
            ###Case: yearDiff == 0: start=year
            startYearStrings = list(filtered_data['startYear'])
            startYearStrings = [str(x) for x in startYearStrings]
            filtered_data['startYear'] = startYearStrings
            filtered_data['year2'] = filtered_data['startYear'].where(filtered_data['yearDiff'] == 0)

            ###Case: year diff == 1: if end month >= 6, year=end; else year = start
            endYearStrings = list(filtered_data['endYear'])
            endYearStrings = [str(x) for x in endYearStrings]
            filtered_data['endYear'] = endYearStrings
            filtered_data['year3'] = filtered_data['endYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] >= 5))
            filtered_data['year4'] = filtered_data['startYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] < 5))
          
            # filtered_data['year'] = filtered_data['year1'] + filtered_data['year2'] + filtered_data['year3']
            filtered_data['year'] = filtered_data['year1'].fillna(filtered_data['year2'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year3'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year4'])
            filtered_data = filtered_data.drop('yearDiff',axis=1)
            filtered_data = filtered_data.drop('year1',axis=1)
            filtered_data = filtered_data.drop('year2',axis=1)
            filtered_data = filtered_data.drop('year3',axis=1)
            filtered_data = filtered_data.drop('year4',axis=1)

        # filtered_data = filtered_data.drop(['endYear','startYear','yearDiff','endMonth','yearMinusOne'],axis=1)
        filtered_data = filtered_data.drop('endYear',axis=1)
        filtered_data = filtered_data.drop('startYear',axis=1)
        filtered_data = filtered_data.drop('yearMinusOne',axis=1)
        filtered_data = filtered_data.drop('endMonth',axis=1)
        filtered_data = filtered_data.drop_duplicates(subset=['year'],keep='last')
        
    except Exception as err:
        print("drop duplicates error")
        print(err)
    finally:
        return filtered_data

def dropUselessColumns(df):
    try:
        returned_data = df.drop(['start','end','accn','fy','fp','form','filed','frame','Tag'],axis=1)

        return returned_data
    except Exception as err:
        print("drop useless columns error")
        print(err)

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

#Changes Dollar Denomination to USD
def cleanUnits(df):
    #Add to EL below as conflicting currencies are found. Manually add them below in for loop. woof. 
    #You could just do an if in statement but the specificity must match the conversion rate
    # exclusionList = ['TWD']
    try:
        df_col_added = df
        origRev = df_col_added['val'].tolist()
        unitsFrom = df_col_added['Units'].tolist()
        datesFrom = df_col_added['year'].tolist()
        conRev = []
        for i in range(len(origRev)):
            if unitsFrom[i] == 'TWD':
                conRev.append(origRev[i] * 0.03)
            elif unitsFrom[i] == 'USD/shares':
                conRev.append(curConvert.convert(origRev[i], 'USD', 'USD', date=date(int(datesFrom[i]),12,31)))
            else:
                conRev.append(curConvert.convert(origRev[i], unitsFrom[i], 'USD', date=date(int(datesFrom[i]),12,31)))
        df_col_added['newVal'] = conRev
        df_col_added['Units'] = 'USD'
    
        df_col_added['val'] = df_col_added['newVal']
        df_col_added = df_col_added.drop('newVal',axis=1)
        
    except Exception as err:
        print("clean Units error: ")
        print(err)
    finally:
        return df_col_added

def cleanRevenue(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'revenue'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['revenue'])
            df_col_added['revenueGrowthRate'] = growthCol
            
    except Exception as err:
        print("cleanRevenue error: ")
        print(err)
    finally:
        return df_col_added

def cleanNetIncome(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netIncome'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netIncome'])
            df_col_added['netIncomeGrowthRate'] = growthCol

    except Exception as err:
        print("cleanNetIncome error: ")
        print(err)
    finally:
        return df_col_added

def cleanNetIncomeNCI(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netIncomeNCI'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netIncomeNCI'])
            df_col_added['netIncomeNCIGrowthRate'] = growthCol

    except Exception as err:
        print("cleanNetIncomeNCI error: ")
        print(err)
    finally:
        return df_col_added

def cleanOperatingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'operatingCashFlow'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['operatingCashFlow'])
            df_col_added['operatingCashFlowGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean oper cash flow error: ")
        print(err)

def cleanInvestingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'investingCashFlow'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['investingCashFlow'])
            df_col_added['investingCashFlowGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean investing cash flow error: ")
        print(err)

def cleanFinancingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'financingCashFlow'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['financingCashFlow'])
            df_col_added['financingCashFlowGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean financingCashFlow error: ")
        print(err)

def cleanNetCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netCashFlow'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netCashFlow'])
            df_col_added['netCashFlowGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean netCashFlow error: ")
        print(err)

def cleanCapEx(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'capEx'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['capEx'])
            df_col_added['capExGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean capEx error: ")
        print(err)

def cleanEPS(df):
    try:
        df_col_added = df.rename(columns={'val':'reportedEPS'})
        growthCol = grManualCalc(df_col_added['reportedEPS'])
        df_col_added['reportedEPSGrowthRate'] = growthCol
        df_col_added = df_col_added.drop('Units', axis=1)

    except Exception as err:
        print("clean eps error: ")
        print(err)
    finally:
        if df_col_added['Ticker'].isnull().any():
            return pd.DataFrame()
        else:
            return df_col_added

def cleanNAV(df):
    try:
        df_col_added = df.rename(columns={'val':'nav'})
        growthCol = grManualCalc(df_col_added['nav'])
        df_col_added['navGrowthRate'] = growthCol
        df_col_added = df_col_added.drop('Units', axis=1)

    except Exception as err:
        print("clean nav error: ")
        print(err)
    finally:
        if df_col_added['Ticker'].isnull().any(): #Ticker will never be null if NAV exists. 
            return pd.DataFrame()
        else:
            return df_col_added

def cleanfcf(df): #Requires a pre-built DF include OCF and CapEX!!!
    try:
        df_col_added = df
        df_col_added['fcf'] = df_col_added['operatingCashFlow'] - df_col_added['capEx']
        growthCol = grManualCalc(df_col_added['fcf'])
        df_col_added['fcfGrowthRate'] = growthCol

        return df_col_added

    except Exception as err:
        print("clean fcf error: ")
        print(err)

def cleanfcfMargin(df): #Requires a pre-built DF including fcf!!!
    try:
        df_col_added = df
        df_col_added['fcfMargin'] = df_col_added['fcf'] / df_col_added['revenue'] * 100
        growthCol = grManualCalc(df_col_added['fcfMargin'])
        df_col_added['fcfMarginGrowthRate'] = growthCol

        return df_col_added

    except Exception as err:
        print("clean fcfMargin error: ")
        print(err)

def cleanOperatingIncome(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'operatingIncome'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['operatingIncome'])
            df_col_added['operatingIncomeGrowthRate'] = growthCol

            return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanTaxRate(df):
    try:
        df_col_added = df.rename(columns={'val':'taxRate'})
        df_col_added = df_col_added.drop(columns=['Units'])
        return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanDebt(short, long1, long2, long3, long4):
    #This isn't filling in blanks, it's making sure columns are added together properly with zeroes instead of nulls. Fine 1/21/25. 
    try:
        short = cleanUnits(short)
        long1 = cleanUnits(long1)
        long2 = cleanUnits(long2)
        long3 = cleanUnits(long3)
        long4 = cleanUnits(long4)

        shortNlong1 = pd.merge(short, long1, on=['year','Ticker','CIK','Units'], how='outer')
        shortNlong1['val_x'] = shortNlong1['val_x'].fillna(0)
        shortNlong1['val_y'] = shortNlong1['val_y'].fillna(0)
        shortNlong1['subTotalDebt'] = shortNlong1['val_x'] + shortNlong1['val_y']
        shortNlong1 = shortNlong1.drop(['val_x','val_y'],axis=1)
        
        plusLong2 = pd.merge(shortNlong1, long2, on=['year','Ticker','CIK','Units'], how='outer')
        plusLong2['val'] = plusLong2['val'].fillna(0)
        plusLong2['subTotalDebt'] = plusLong2['subTotalDebt'].fillna(0) 
        plusLong2['TotalDebt'] = plusLong2['subTotalDebt'] + plusLong2['val']
        plusLong2 = plusLong2.drop(['subTotalDebt','val'],axis=1)

        plusLong3 = pd.merge(plusLong2, long3, on=['year','Ticker','CIK','Units'], how='outer')
        plusLong3['val'] = plusLong3['val'].fillna(0)
        plusLong3['TotalDebt'] = plusLong3['TotalDebt'].fillna(0)
        plusLong3['TotalDebt'] = plusLong3['TotalDebt'] + plusLong3['val']
        plusLong3 = plusLong3.drop(['val'],axis=1)

        plusLong4 = pd.merge(plusLong3, long4, on=['year','Ticker','CIK','Units'], how='outer')
        plusLong4['val'] = plusLong4['val'].fillna(0)
        plusLong4['TotalDebt'] = plusLong4['TotalDebt'].fillna(0)
        plusLong4['TotalDebt'] = plusLong4['TotalDebt'] + plusLong4['val']
        plusLong4 = plusLong4.drop(['val'],axis=1)

        # print('in cleandebt, debt DF: ')
        # print(plusLong4)

        return plusLong4

    except Exception as err:
        print("clean Debt error: ")
        print(err)

def cleanAssets(nonCurrent, current):
    try:
        nonCurrent = cleanUnits(nonCurrent)
        current = cleanUnits(current)

        anl = pd.merge(nonCurrent, current, on=['year','Ticker','CIK','Units'], how='outer')
        anl['val'] = anl['val_x'] + anl['val_y']
        anl = anl.drop(['val_x','val_y'],axis=1) 
        return anl

    except Exception as err:
        print("clean assets error: ")
        print(err)

def cleanLiabilities(nonCurrent, current):
    try:
        nonCurrent = cleanUnits(nonCurrent)
        current = cleanUnits(current)

        anl = pd.merge(nonCurrent, current, on=['year','Ticker','CIK','Units'], how='outer')
        anl['val'] = anl['val_x'] + anl['val_y']
        anl = anl.drop(['val_x','val_y'],axis=1) 
        return anl

    except Exception as err:
        print("clean Liabilities error: ")
        print(err)

def cleanTotalEquity(assets, liabilities, ncL, cuL, ncA, cuA, reportedEquity):
    try:
        if assets.empty:
            assets = cleanAssets(ncA, cuA)
        else:
            assets = cleanUnits(assets)

        if liabilities.empty:
            liabilities = cleanLiabilities(ncL, cuL)
        else:
            liabilities = cleanUnits(liabilities)

        reportedEquity = cleanUnits(reportedEquity)
        
        #Because Equity is important to calculations, we chose to not fill nulls at this time
        assetsAndLias = pd.merge(assets, liabilities, on=['year','Ticker','CIK','Units'], how='outer')

        assetsAndLias['assets'] = assetsAndLias['val_x']
        #removed
        # assetsMean = assetsAndLias['assets'].mean() #/ ((len(assetsAndLias['assets'])/2)+1)
        # assetsAndLias['assets'] = assetsAndLias['assets'].fillna(assetsMean)
        #
        assetsAndLias['liabilities'] = assetsAndLias['val_y']
        #removed
        # liaMean = assetsAndLias['liabilities'].mean() #/ ((len(assetsAndLias['liabilities'])/2)+1)
        # assetsAndLias['liabilities'] = assetsAndLias['liabilities'].fillna(liaMean)
        #
        assetsAndLias = assetsAndLias.drop(['val_x','val_y'],axis=1)

        assetsAndLias = pd.merge(assetsAndLias, reportedEquity, on=['Units','year','Ticker','CIK'], how='outer')
        assetsAndLias['ReportedTotalEquity'] = assetsAndLias['val']
        assetsAndLias = assetsAndLias.drop(['val'],axis=1)

        #changed to exclude null fillings
        assetsAndLias['TotalEquity'] = np.where(((assetsAndLias['assets'] == 0 | assetsAndLias['assets'].isnull()) | 
                                                    (assetsAndLias['liabilities'] == 0 | assetsAndLias['liabilities'].isnull())), 
                                                    None, assetsAndLias['assets']-assetsAndLias['liabilities'])
        #assetsAndLias['assets']-assetsAndLias['liabilities']

        #Suggested solution: Fill in values not via estimates, but from reported values if they exist
        assetsAndLias['TotalEquity'] = np.where(assetsAndLias['TotalEquity'].isnull(), assetsAndLias['ReportedTotalEquity'], assetsAndLias['TotalEquity'])

        return assetsAndLias

    except Exception as err:
        print("clean totalEquity error: ")
        print(err)

def cleanDeprNAmor(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'depreNAmor'})

        return df_col_added
    except Exception as err:
        print("clean deprNAmor error: ")
        print(err)

def cleanDeprNAmor2(df1,df2):
    try:
        df_col_added = cleanUnits(df1)
        df_col_added = df_col_added.rename(columns={'val':'depreNAmor1'})

        df2 = cleanUnits(df2)
        df2 = df2.rename(columns={'val':'depreNAmor2'})

        df_col_added2 = pd.merge(df_col_added, df2, on=['year','Ticker','CIK','Units'], how='outer')
        df_col_added2['depreNAmor'] = df_col_added2['depreNAmor1'].replace(np.nan, 0) + df_col_added2['depreNAmor2'].replace(np.nan, 0)
        df_col_added2 = df_col_added2.drop(columns=['depreNAmor1','depreNAmor2'])

        return df_col_added2 
    except Exception as err:
        print("clean deprNAmor2 error: ")
        print(err)

def cleanGainSaleProp(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'gainSaleProp'})

        return df_col_added
    except Exception as err:
        print("clean gainSaleProp error: ")
        print(err)

def cleanInterestPaid(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'interestPaid'})

        return df_col_added

    except Exception as err:
        print("clean interestPaid error: ")
        print(err)

def cleanDividends(total, perShare, shares): #, dilutedShares, rocps, roctotal): 
    #This function retains the ability to process ROC and diluted share values, otherwise commented out for deprecation
    try:
        # rocpsFlag = True
        totalflag = True
        # roctotalFlag = True
        shares = shares.rename(columns={'val':'shares'})
        shares = shares.drop(columns=['Units'])
        # dilutedShares = dilutedShares.rename(columns={'val':'dilutedShares'})
        # dilutedShares = dilutedShares.drop(columns=['Units'])

        total = cleanUnits(total)
        total = total.rename(columns={'val':'totalDivsPaid'})
        if total['Units'].isnull().all():
            total = total.drop(columns=['Units'])
            totalflag = False
        total['totalDivsPaid'] = (total['totalDivsPaid'] * (-1)).where(total['totalDivsPaid'] < 0, other=total['totalDivsPaid'])
        perShare = perShare.rename(columns={'val':'divsPaidPerShare'})
        perShare = perShare.drop(columns=['Units'])
        perShare['divsPaidPerShare'] = (perShare['divsPaidPerShare'] * (-1)).where(perShare['divsPaidPerShare'] < 0, other=perShare['divsPaidPerShare'])

        # rocps = cleanUnits(rocps)
        # rocps = rocps.rename(columns={'val':'ROCperShare'})
        # if rocps['Units'].isnull().all():
        #     rocps = rocps.drop(columns=['Units'])
        #     rocpsFlag = False
        # roctotal = cleanUnits(roctotal)
        # roctotal = roctotal.rename(columns={'val':'ROCTotal'})
        # if roctotal['Units'].isnull().all():
        #     roctotal = roctotal.drop(columns=['Units'])
        #     roctotalFlag = False
       
        df_col_added = pd.merge(total, perShare, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(shares, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # df_col_added = pd.merge(dilutedShares, df_col_added, on=['year','Ticker','CIK'], how='outer')

        # if rocpsFlag == False:
        #     df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # elif rocps.empty:
        #     df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # else:
        #     if 'Units' in df_col_added:
        #         df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK','Units'], how='outer')
        #     else:
        #         df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # if roctotalFlag == False:
        #     df_col_added = pd.merge(roctotal, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # elif roctotal.empty:
        #     df_col_added = pd.merge(roctotal, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # else:
        #     df_col_added = pd.merge(roctotal, df_col_added, on=['year','Ticker','CIK','Units'], how='outer')
        
        #first we check for nans, keep them in mind for later
        nanList = []
        for x in df_col_added:
            if df_col_added[x].isnull().any():
                # integrity_flag = 'Acceptable'
                nanList.append(x)
                # print('nans found: ' + x)
        #How to handle those empty values in each column
        df_col_added['calcDivsPerShare'] = df_col_added['totalDivsPaid'] / df_col_added['shares']
        df_col_added['tempTotalDivs'] = df_col_added['divsPaidPerShare'] * df_col_added['shares']
        df_col_added['tempShares'] = df_col_added['totalDivsPaid'] / df_col_added['divsPaidPerShare']

        for x in nanList: #Values in ex-US currencies seem weird versus common stock analysis sites. 
                            #Could be an exchange rate issue I haven't accounted for in the exchange to USD.
            if x == 'divsPaidPerShare':
                df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['calcDivsPerShare']) 
                # growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
                # df_col_added['divGrowthRate'] = growthCol1 
            elif x == 'totalDivsPaid':
                df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
                # growthCol1 = grManualCalc(df_col_added['divsPaidPerShare'])
                # df_col_added['divGrowthRate'] = growthCol1 
        df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempShares']) 
        
        df_col_added['shares'] = df_col_added['shares'].ffill().bfill() 
        # df_col_added['dilutedShares'] = df_col_added['dilutedShares'].ffill().bfill()
        growthCol = grManualCalc(df_col_added['shares'])
        df_col_added['sharesGrowthRate'] = growthCol

        growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
        df_col_added['divGrowthRateBOT'] = growthCol1 

        growthCol2 = grManualCalc(df_col_added['divsPaidPerShare'])
        df_col_added['divGrowthRateBORPS'] = growthCol2

        # growthCol3 = grManualCalc(df_col_added['ROCperShare'])
        # df_col_added['ROCperShareGrowthRate'] = growthCol3
        # growthCol4 = grManualCalc(df_col_added['ROCTotal'])
        # df_col_added['ROCTotalGrowthRate'] = growthCol4

        growthCol5 = grManualCalc(df_col_added['calcDivsPerShare'])
        df_col_added['divGrowthRateBOCPS'] = growthCol5

    except Exception as err:
        print("clean dividends error: ")
        print(err)
    finally:
        return df_col_added

def fillEmptyIncomeGrowthRates(df):
    try:
        df_filled = df
        # fixTracker = 0

        if df_filled['netCashFlow'].isnull().any():
            df_filled['netCashFlow'] = df_filled['netCashFlow'].fillna(df_filled['operatingCashFlow'] + df_filled['investingCashFlow'] + df_filled['financingCashFlow'])

        tarList = ['revenue','netIncome','operatingCashFlow','investingCashFlow','financingCashFlow','netCashFlow', 'capEx', 'depreNAmor'] #'netIncomeNCI',
        
        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            savedCol = df_filled[x]
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol

            # if savedCol.isnull().any():
            #     percentNull = savedCol.isnull().sum() / len(savedCol)
            #     if percentNull > 0.4:
            #         fixTracker += 1

        df_filled = df_filled.drop(columns=['depreNAmorGrowthRate'])

        if df_filled['Units'].isnull().all():
            df_filled = df_filled.drop('Units',axis=1)
        else:
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        df_filled = cleanfcf(df_filled)
        df_filled = cleanfcfMargin(df_filled)
        
        df_filled['gainSaleProp'] = df_filled['gainSaleProp'].replace(np.nan,0)
        df_filled['ffo'] = df_filled['netIncome'] + df_filled['depreNAmor'] - df_filled['gainSaleProp']
        growthCol1 = grManualCalc(df_filled['ffo'])
        df_filled['ffoGrowthRate'] = growthCol1

        #eps related values
        df_filled['calculatedEPS'] = round(df_filled['netIncome'] / df_filled['shares'], 2)
        growthCol2 = grManualCalc(df_filled['calculatedEPS'])
        df_filled['calculatedEPSGrowthRate'] = growthCol2
        #calculated reit eps from ffo 
        df_filled['reitEPS'] = df_filled['ffo'] / df_filled['shares']
        growthCol3 = grManualCalc(df_filled['reitEPS'])
        df_filled['reitEPSGrowthRate'] = growthCol3

        df_filled['profitMargin'] = round(df_filled['netIncome'] / df_filled['revenue'] * 100, 2)
        growthCol3 = grManualCalc(df_filled['profitMargin'])
        df_filled['profitMarginGrowthRate'] = growthCol3

        #payout ratio related
        df_filled['payoutRatio'] = df_filled['totalDivsPaid'] / df_filled['netIncome'] * 100
        df_filled['fcfPayoutRatio'] = df_filled['totalDivsPaid'] / df_filled['fcf'] * 100
        df_filled['ffoPayoutRatio'] = df_filled['totalDivsPaid'] / df_filled['ffo'] * 100

        # if fixTracker > 4:
        #     df_filled['INCintegrityFlag'] = 'NeedsWork'
        # elif fixTracker == 0: 
        #     df_filled['INCintegrityFlag'] = 'Good'
        # else:
        #     df_filled['INCintegrityFlag'] = 'Acceptable'
        
    except Exception as err:
        print("fill empty inc GR error: ")
        print(err)
    finally:
        return df_filled

def fillEmptyDivsGrowthRates(df):
    try:
        df_filled = df
        # fixTracker = 0

        if df_filled['interestPaid'].isnull().any():
            # percentNull = df_filled['interestPaid'].isnull().sum() / len(df_filled['interestPaid'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['interestPaid'] = df_filled['interestPaid'].ffill().bfill()
        if df_filled['totalDivsPaid'].isnull().any():
            # percentNull = df_filled['totalDivsPaid'].isnull().sum() / len(df_filled['totalDivsPaid'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['totalDivsPaid'] = df_filled['totalDivsPaid'].replace(np.nan, 0)
        if df_filled['divsPaidPerShare'].isnull().any():
            # percentNull = df_filled['divsPaidPerShare'].isnull().sum() / len(df_filled['divsPaidPerShare'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['divsPaidPerShare'] = df_filled['divsPaidPerShare'].replace(np.nan, 0)
        if df_filled['shares'].isnull().all():
            # fixTracker += 3
            df_filled['shares'] = df_filled['shares'].replace(np.nan, 1)
        elif df_filled['shares'].isnull().any():
            # percentNull = df_filled['shares'].isnull().sum() / len(df_filled['shares'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['shares'] = df_filled['shares'].ffill().bfill() 

        # df_filled['ROCperShare'] = df_filled['ROCperShare'].replace(np.nan, 0)
        # df_filled['ROCTotal'] = df_filled['ROCTotal'].replace(np.nan, 0)

        if df_filled['sharesGrowthRate'].isnull().any(): 
            growthCol = grManualCalc(df_filled['shares'])
            df_filled['temp1'] = growthCol
            df_filled['sharesGrowthRate'] = df_filled['sharesGrowthRate'].fillna(df_filled.pop('temp1'))
            
        if df_filled['divGrowthRateBOT'].isnull().any():
            growthCol = grManualCalc(df_filled['totalDivsPaid'])
            df_filled['temp2'] = growthCol
            df_filled['divGrowthRateBOT'] = df_filled['divGrowthRateBOT'].fillna(df_filled.pop('temp2'))

        if df_filled['divGrowthRateBORPS'].isnull().any():
            growthCol = grManualCalc(df_filled['divsPaidPerShare'])
            df_filled['temp3'] = growthCol
            df_filled['divGrowthRateBORPS'] = df_filled['divGrowthRateBORPS'].fillna(df_filled.pop('temp3'))

        if df_filled['divGrowthRateBOCPS'].isnull().any():
            growthCol = grManualCalc(df_filled['calcDivsPerShare'])
            df_filled['temp4'] = growthCol
            df_filled['divGrowthRateBOCPS'] = df_filled['divGrowthRateBOCPS'].fillna(df_filled.pop('temp4'))

        # if df_filled['ROCperShareGrowthRate'].isnull().any():
        #     growthCol = grManualCalc(df_filled['ROCperShare'])
        #     df_filled['temp5'] = growthCol
        #     df_filled['ROCperShareGrowthRate'] = df_filled['ROCperShareGrowthRate'].fillna(df_filled.pop('temp5'))
        
        # if df_filled['ROCTotalGrowthRate'].isnull().any():
        #     growthCol = grManualCalc(df_filled['ROCTotal'])
        #     df_filled['temp6'] = growthCol
        #     df_filled['ROCTotalGrowthRate'] = df_filled['ROCTotalGrowthRate'].fillna(df_filled.pop('temp6'))

        # if df_filled['dilutedShares'].isnull().all():
        #     print('if diluted shares is all null triggered')
        #     df_filled['dilutedSharesGrowthRate'] = np.nan
        # else:
        #     print('if diluted shares is all null else statement hit')
        #     growthCol1 = grManualCalc(df_filled['dilutedShares'])
        #     df_filled['dilutedSharesGrowthRate'] = growthCol1

        if df_filled['Units'].isnull().all():
            df_filled = df_filled.drop('Units',axis=1)
        else:
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        # if fixTracker >= 4:
        #     df_filled['DIVintegrityFlag'] = 'NeedsWork'
        # elif fixTracker == 0: 
        #     df_filled['DIVintegrityFlag'] = 'Good'
        # else:
        #     df_filled['DIVintegrityFlag'] = 'Acceptable'
        
    except Exception as err:
        print("fill empty divs GR error: ")
        print(err)

    finally:
        return df_filled

def fillEmptyROICGrowthRates(df):
    try:
        df_filled = df
        # fixTracker = 0
        tarList = ['operatingIncome']
        tDebt = 'TotalDebt'
        equityParts = ['assets','liabilities']

        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            savedCol = df_filled[x]
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol

            # if savedCol.equals(df_filled[x]):
            #     continue
            # else:
            #     fixTracker += 1

        if df_filled['TotalDebt'].isnull().any():
            # percentNull = df_filled['TotalDebt'].isnull().sum() / len(df_filled['TotalDebt'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['TotalDebt'] = df_filled['TotalDebt'].replace(np.nan, 0)
        if df_filled['assets'].isnull().any():
            # percentNull = df_filled['assets'].isnull().sum() / len(df_filled['assets'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['assets'] = df_filled['assets'].ffill().bfill()
        if df_filled['liabilities'].isnull().any():
            # percentNull = df_filled['liabilities'].isnull().sum() / len(df_filled['liabilities'])
            # if percentNull > 0.4:
            #     fixTracker += 1
            df_filled['liabilities'] = df_filled['liabilities'].ffill().bfill()
        
        #This is unlikely to be needed, cleanTotalEquity already does something similar
        df_filled['TotalEquity'] = df_filled['TotalEquity'].fillna(df_filled['assets'] - df_filled['liabilities'])

        if df_filled['Units'].isnull().all():
            df_filled = df_filled.drop('Units',axis=1)
        else:
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        #We only ended up using adjusted ROIC values anyway.
        # df_filled['nopat'] = df_filled['operatingIncome'] * (1 - df_filled['taxRate'])
        df_filled['investedCapital'] = df_filled['TotalEquity'] + df_filled['TotalDebt']
        # df_filled['roic'] = df_filled['nopat'] / df_filled['investedCapital'] * 100
        df_filled['adjRoic'] = df_filled['netIncome'] / df_filled['investedCapital'] * 100
        df_filled['reportedAdjRoic'] = df_filled['netIncome'] / (df_filled['ReportedTotalEquity'] + df_filled['TotalDebt']) * 100
        df_filled['calculatedRoce'] = df_filled['netIncome'] / df_filled['TotalEquity'] * 100
        df_filled['reportedRoce'] = df_filled['netIncome'] / df_filled['ReportedTotalEquity'] * 100

        df_filled['cReitROE'] = df_filled['ffo'] / df_filled['TotalEquity'] * 100
        # growthColcr = grManualCalc(df_filled['cReitROE'])
        # df_filled['cReitROEGrowthRate'] = growthColcr

        df_filled['rReitROE'] = df_filled['ffo'] / df_filled['ReportedTotalEquity'] * 100
        # growthColrr = grManualCalc(df_filled['rReitROE'])
        # df_filled['rReitROEGrowthRate'] = growthColrr

        df_filled['calcBookValue'] = df_filled['TotalEquity'] / df_filled['shares']
        growthCol1 = grManualCalc(df_filled['calcBookValue'])
        df_filled['calcBookValueGrowthRate'] = growthCol1
        df_filled['reportedBookValue'] = df_filled['ReportedTotalEquity'] / df_filled['shares']
        growthCol2 = grManualCalc(df_filled['reportedBookValue'])
        df_filled['reportedBookValueGrowthRate'] = growthCol2

        growthCol3 = grManualCalc(df_filled['TotalDebt'])
        df_filled['TotalDebtGrowthRate'] = growthCol3

        growthCol4 = grManualCalc(df_filled['TotalEquity'])
        df_filled['TotalEquityGrowthRate'] = growthCol4

        growthCol5 = grManualCalc(df_filled['ReportedTotalEquity'])
        df_filled['ReportedTotalEquityGrowthRate'] = growthCol5

        # if fixTracker > 4:
        #     df_filled['ROICintegrityFlag'] = 'NeedsWork'
        # elif fixTracker == 0: 
        #     df_filled['ROICintegrityFlag'] = 'Good'
        # else:
        #     df_filled['ROICintegrityFlag'] = 'Acceptable'

    except Exception as err:
        print("fill empty ROIC GR error: ")
        print(err)

    finally:
        return df_filled

def fillUnits(df):
    try:
        df_filled = pd.DataFrame()
        if df['Units'].isnull().all():
            df_filled = df.drop('Units',axis=1)
        else:
            df_filled = df
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        return df_filled
    except Exception as err:
        print("fill Units error: ")
        print(err)

def fillPrice(df):
    try:
        ticker = df['Ticker'].loc[0]
        df_filled = df
        yearList = df_filled['year'].tolist()
        priceList = []
        for x in yearList:
            # df_filled['price'] = yf.download(ticker, str(x) + '-12-20', str(x) + '-12-31')['Close'][-1]
            priceData = yf.download(ticker, str(x) + '-12-20', str(x) + '-12-31')['Close']
            try:
                priceList.append(priceData[-1])
            except:
                priceList.append(np.nan)
                continue
          
        df_filled['price'] = priceList
        growthCol = grManualCalc(df_filled['price'])
        df_filled['priceGrowthRate'] = growthCol
        
    except Exception as err:
        print("fill price error: ")
        print(err)
    finally:
        return df_filled
        
# Returns organized data pertaining to the tag(s) provided in form of DF, but from API, for DB, instead of from CSV
#consolidateSingleAttributeforDataBase
def cSADB(df, tagList):
    try:
        filtered_data = df
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            held_data = filtered_data[filtered_data['Tag'].eq(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        returned_data = get_Only_10k_info(returned_data)
        returned_data = dropAllExceptFYRecords(returned_data) 
        returned_data = orderAttributeDF(returned_data)
        returned_data = dropDuplicatesInDF(returned_data) 
        returned_data = dropUselessColumns(returned_data)

    except Exception as err:
        print("consolidate single attr error: ")
        print(err)
    finally:
        return returned_data

# Returns full table for Mega DB table, using above cSADB function per section analyzed
#makeConsolidatedTableEntryforDataBase
def mCTEDB(df, ticker):
    try:
        ### INCOME TABLE START
        rev_df = cleanRevenue(cSADB(df, revenue))
        netInc_df = cleanNetIncome(cSADB(df, netIncome))
        # netIncNCI_df = cleanNetIncomeNCI(cSADB(df, netIncomeNCI))
        eps_df = cleanEPS(cSADB(df, eps))
        opcf_df = cleanOperatingCashFlow(cSADB(df, operatingCashFlow))
        invcf_df = cleanInvestingCashFlow(cSADB(df, investingCashFlow))
        fincf_df = cleanFinancingCashFlow(cSADB(df, financingCashFlow))
        netcf_df = cleanNetCashFlow(cSADB(df, netCashFlow))
        capex_df = cleanCapEx(cSADB(df, capEx))
        depAmor_df = cleanDeprNAmor(cSADB(df, deprecAndAmor))
        if depAmor_df.empty:
            depAmor_df = cleanDeprNAmor2(cSADB(df, deprecAndAmor2),cSADB(df, deprecAndAmor3))
        gainSaleProp_df = cleanGainSaleProp(cSADB(df, gainSaleProperty))
        
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        # revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer')

        if eps_df.empty:
            revNinc['reportedEPS'] = np.nan
            revNinc['reportedEPSGrowthRate'] = np.nan
        else:
            revNinc = pd.merge(revNinc, eps_df, on=['year','Ticker','CIK'], how='outer')

        plusopcf = pd.merge(revNinc, opcf_df, on=['year','Ticker','CIK','Units'], how='outer')
        plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','Ticker','CIK','Units'], how='outer')
        plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','Ticker','CIK','Units'], how='outer')
        plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','Ticker','CIK','Units'], how='outer')
        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','Ticker','CIK','Units'], how='outer')
        plusDepAmor = pd.merge(pluscapex, depAmor_df, on=['year','Ticker','CIK','Units'], how='outer')
        plusSaleProp = pd.merge(plusDepAmor, gainSaleProp_df, on=['year','Ticker','CIK','Units'], how='outer')

        plusSaleProp = fillUnits(plusSaleProp)
        ### INCOME TABLE END

        ### DIVS TABLE START
        intPaid_df = cleanInterestPaid(cSADB(df, interestPaid))
        divs_df = cleanDividends(cSADB(df, totalCommonStockDivsPaid), 
                                    cSADB(df, declaredORPaidCommonStockDivsPerShare),
                                    cSADB(df, basicSharesOutstanding))#,
                                    # cSADB(df, dilutedSharesOutstanding),
                                    # cSADB(df, returnOfCapitalPerShare), #Saved in case later versions want to reference these.
                                    # cSADB(df, totalReturnOfCapital))

        if 'Units' not in divs_df:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        else: 
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        #Added else above, commented below out, due to Units errors. 7/2024
        # elif divs_df['Units'].isnull().any():
        #     divs_df = divs_df.drop(columns=['Units'])
        #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        # else:
        #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        
        intNdivs = fillUnits(intNdivs)
        ### DIVS TABLE END
        
        ### ROIC TABLE START
        opIncome_df = cleanOperatingIncome(cSADB(df, operatingIncome))
        taxRate_df = cleanTaxRate(cSADB(df, taxRate))
        totalDebt_df = cleanDebt(cSADB(df, shortTermDebt), 
                                    cSADB(df, longTermDebt1), cSADB(df, longTermDebt2),
                                    cSADB(df, longTermDebt3), cSADB(df, longTermDebt4))
        totalEquity_df = cleanTotalEquity(cSADB(df, totalAssets), 
                                    cSADB(df, totalLiabilities), cSADB(df, nonCurrentLiabilities),
                                    cSADB(df, currentLiabilities), cSADB(df, nonCurrentAssets),
                                    cSADB(df, currentAssets), cSADB(df, shareHolderEquity))
        nav_df = cleanNAV(cSADB(df, netAssetValue))

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        #I believe in the following block (u-fill), we did this manually instead of using fillUnits() due to debt merging reasons
        opIncNtax['Units'] = opIncNtax['Units'].ffill().bfill()

        if opIncNtax['Units'].isnull().all():
            opIncNtax['Units'] = 'USD'
        
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
        #u-fill end

        if nav_df.empty:
            plustEquity['nav'] = np.nan
            plustEquity['navGrowthRate'] = np.nan
        else:
            plustEquity = pd.merge(plustEquity, nav_df, on=['year','Ticker','CIK'], how='outer')
        
        plustEquity = fillUnits(plustEquity)
        ### ROIC TABLE END
        
        ###INCOME TABLE IS plusSaleProp
        ###Dividends table is intNdivs
        ###ROIC TABLE is plustEquity
        if 'Units' not in intNdivs:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK'], how='outer')
        else:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK','Units'], how='outer')
        incDivsROIC = pd.merge(divsPlusROIC, plusSaleProp, on=['year','Ticker','CIK','Units'], how='outer')
        
        #Make sure before we fill things up that the df is sorted properly for bfill/ffill
        incDivsROIC = incDivsROIC.sort_values(by='year')

        #While currently not presented on the site, this could be a wonderful feature to add, average price growth per year. More data to store, anyway.
        incDivsROIC = fillPrice(incDivsROIC)

        incDivsROIC = fillEmptyDivsGrowthRates(incDivsROIC) 
        
        #Finish the Income Table Entries
        incDivsROIC = fillEmptyIncomeGrowthRates(incDivsROIC)

        #Finish the ROIC Table Entries
        incDivsROIC = fillEmptyROICGrowthRates(incDivsROIC)

        incDivsROIC['Sector'] = nameSectorDict[ticker]
        incDivsROIC['Industry'] = nameIndustryDict[ticker]
    
    except Exception as err:
        print("mCTEDB error: ")
        print(err)
    finally:
        return incDivsROIC

def write_full_EDGAR_to_Mega(): #luke, add a print tracker for % complete from below-updatemega function
    try:
        errorTickers = []
        tickerlist = gSdf['Ticker'].tolist()
        for i in tickerlist:
            print(i)
            try:
                company_data = EDGAR_query(i, cik_dict[i], header, ultimateTagsList)
                time.sleep(0.1)
                consol_table = mCTEDB(company_data, i)
                uploadToDB(consol_table, 'Mega')
                print(i + ' uploaded to DB!')
            except Exception as err1:
                errorTickers.append(str(i))
                print('write list to DB in for loop error for: ' + i)
                print(err1)
                continue
    except Exception as err:
        print("write List to DB error: ")
        print(err)
    finally:
        print(errorTickers)

def write_list_to_Mega(thelist): #luke, add a print tracker for % complete from below-updatemega function
    try:
        errorTickers = []
        length1 = len(thelist)
        n = 0
        time0 = time.time()
        for i in thelist:
            print(str(round(n/length1,4)*100) + '% Complete!')
            n += 1
            try:
                time1 = time.time()

                company_data = EDGAR_query(i, cik_dict[i], header, ultimateTagsList)
                consol_table = mCTEDB(company_data, i)
                uploadToDB(consol_table, 'Mega')
                print(i + ' uploaded to DB!')
                
                time2 = time.time()
                print('Time to upload: ' + str(time2-time1))
                # print('time to complete')
                # print(time2-time1)
                time.sleep(0.1)
            except Exception as err1:
                errorTickers.append(str(i))
                print('write list to DB in for loop error for: ' + i)
                print(err1)
                continue
        time4  = time.time()
    except Exception as err:
        print("write List to DB error: ")
        print(err)
    finally:
        print('Total Time to completion: ' + str(time4-time0))
        print(errorTickers)

# megalist = print_DB('SELECT Ticker FROM stockList WHERE Sector LIKE \'Basic Materials\';', 'return')
# write_list_to_Mega(megalist['Ticker'])

# megalist = print_DB('SELECT COUNT(DISTINCT Ticker) FROM Mega;', 'print')# WHERE Sector LIKE \'Utilities\';', 'return')
# stockList = print_DB('SELECT DISTINCT Ticker FROM stockList WHERE Sector LIKE \'Utilities\';', 'return')
# print(len(megalist)-len(stockList))
#unlogged, stockList to Mega
#B: 77
#C: 29
#E: 38
#F: 505
#I: 77
#K: 59
#P: 29
#RE: 14
#U: 16
#V: 77
#Y: 51
# print(megalist)
# unstockList = print_DB('SELECT DISTINCT Ticker FROM stockList WHERE Sector LIKE \'Unknown\';', 'return')
# print(len(unstockList))
# guh = print_DB('DELETE FROM Mega;', 'return')
# conn = sql.connect(db_path)
# query = conn.cursor()
# del_query = 'DELETE FROM Mega;'
# query.execute(del_query)
# conn.commit()
# query.close()
# conn.close()
# print_DB('SELECT * FROM Mega ;', 'print') #LIKE \'Unknown\' ###RE:4077 rows, Y, V, U, P, K, I, F, E, C, B
# print_DB('SELECT DISTINCT Sector FROM stockList;','print')
# Sector
# 0               Technology
# 1   Communication Services
# 2        Consumer Cyclical
# 3       Financial Services
# 4       Consumer Defensive
# 5               Healthcare
# 6                   Energy
# 7              Industrials
# 8          Basic Materials
# 9                Utilities
# 10             Real Estate

# gotta test errors for: tech, bmrn, they had weird errors.

#gets new tickers from stocklist, adds them to mega, embedded in updateMega()
def addNewToMega():
    try:
        tickerlist = gSdf['Ticker'].tolist() #stocklist
        gettickers = 'SELECT DISTINCT(Ticker) as ticker FROM Mega;' #mega
        megatickers = print_DB(gettickers,'return')['ticker'].tolist()
        tickerstoadd = list(set(tickerlist).difference(megatickers))
        write_list_to_Mega(tickerstoadd)
    except Exception as err:
        print('add new to mega err')
        print(err)

#this gets all stocks and tickers available, then all tickers in Mega, checks latest year in Mega, 
# gathers new data where necessary and uploads only that to Mega
def update_Mega(latestyear):
    try:
        #get list of tickers in mega
        gettickers = 'SELECT DISTINCT(Ticker) FROM Mega;'
        tickersinmega = print_DB(gettickers, 'return')['Ticker'].tolist()
        stillNotUpdated = []
        updated = []
        length1 = len(tickersinmega)
        n = 1
        for x in tickersinmega:
            getyears = 'SELECT Ticker, year FROM Mega\
                        WHERE Ticker IN (\'' + x + '\');'
            yearsdf = print_DB(getyears, 'return')
            newdf = yearsdf.max()
            latestyearinDB = newdf['year']
            print(str(round(n/length1,4)*100) + '% complete!')

            if latestyearinDB != latestyear:
                try:
                    company_data = EDGAR_query(x, cik_dict[x], header, ultimateTagsList)
                    consol_table = mCTEDB(company_data, x)
                    time.sleep(0.1)
                    #here we have to only upload the rows where year is greater than the latest year
                    consol_table = consol_table[consol_table['year'] > latestyearinDB]
                    n += 1
                    if consol_table.empty:
                        print('SEC records not updated yet for: ' + x)
                        stillNotUpdated.append(x)
                        continue
                    else:
                        uploadToDB(consol_table, 'Mega')
                        updated.append(x)
                    print(i + ' updated in DB!')
                except Exception as err1:
                    print('update  DB in for loop error for: ' + x)
                    print(err1)
                    n += 1
                    continue
            else:
                n += 1
    except Exception as err:
        print("update mega DB error: ")
        print(err)
        n += 1
    finally:
        addNewToMega()
        #luke below will eventually be saved in logs
        print('stocks still needing updates:')
        print(stillNotUpdated)
        print('those that just got updated:')
        print(updated)

# update_Mega('2023')
#ran 7/29/24
#still needing update
# needup = ['RNW', 'AZREF', 'ADN', 'ARAO', 'MMMW', 'GSFI', 'VENG', 'PPWLM', 'HUNGF', 'PWCO', 'CTA-PA', 'SIM', 'DRD', 'MULG', 'RMRI', 'EVA', 'GRFX', 'ZKIN', 'RETO', 'GURE', 'TLRS', 'GRMC', 'COWI', 'SRGZ', 'MNGG', 'ETCK', 'GPLDF', 'VYST', 'GYST', 'MKDTY', 'SGMD', 'NSRCF', 'AVLNF', 'ALMMF', 'ERLFF', 'SILEF', 'GIGGF', 'EXNRF', 'CGSI', 'SHVLF', 'SINC', 'SMTSF', 'JSHG', 'MXSG', 'STCC', 'HGLD', 'MPVDF', 'IIJIY', 'LDSN', 'DRCT', 'SKLZ', 'BBUZ', 'EGLXF', 'SALM', 'SPTY', 'SNPW', 'NUGL', 'COMS', 'SLDC', 'GFMH', 'SRAX', 'MDEX', 'SNWR', 'WINR', 'MLFB', 'CLIS', 'XFCI', 'FRFR', 'YVRLF', 'NTTYY', 'QBCRF', 'ILLMF', 'IDWM', 'EMWPF', 'BYOC', 'GZIC', 'PTNRF', 'PSNY', 'NWTN', 'YTRA', 'TUP', 'INTG', 'SLNA', 'SOND', 'UXIN', 'PDRO', 'PRSI', 'LTRY', 'CMOT', 'ELYS', 'EVVL', 'LQLY', 'SHMY', 'BQ', 'DREM', 'SCRH', 'FLES', 'BBIG', 'REII', 'THBD', 'BTDG', 'SFTGQ', 'CGAC', 'UFABQ', 'WESC', 'ASCK', 'TKAYF', 'ALTB', 'WCRS', 'DSHK', 'LMPX', 'FTCHF', 'FXLV', 'AMTY', 'ELRA', 'SSUNF', 'ATEYY', 'CAJPY', 'DDD', 'SPWR', 'TGAN', 'LUNA', 'WRAP', 'LTCH', 'FEIM', 'SOL', 'MOBX', 'EBIXQ', 'RAASY', 'DZSI', 'EGIO', 'DGHI', 'RCAT', 'DSWL', 'SGMA', 'SPI', 'GOLQ', 'MVLA', 'HUBC', 'VSMR', 'AIAD', 'LKCO', 'WRNT', 'NXTP', 'IMTE', 'MICS', 'WDLF', 'SRCO', 'RKFL', 'DUSYF', 'ZRFY', 'WOWI', 'XNDA', 'ONCI', 'ODII', 'TTCM', 'IGEN', 'MAPT', 'AGILQ', 'IINX', 'RDAR', 'KBNT', 'TMPOQ', 'ALFIQ', 'TMNA', 'ISGN', 'IMCI', 'DSGT', 'OGBLY', 'NIPNF', 'AUOTY', 'LCHD', 'AATC', 'CATG', 'SEAC', 'BNSOF', 'EVOL', 'FALC', 'HPTO', 'VQSSF', 'RBCN', 'TKOI', 'BDRL', 'GSPT', 'DROP', 'SPYR', 'TCCO', 'EHVVF', 'ABCE', 'BTZI', 'SMIT', 'XDSL', 'TRIRF', 'SANP', 'MAXD', 'SDVI', 'DIGAF', 'NTPIF', 'HWTR', 'MHPC', 'CRDV', 'PDNLA', 'DPWW', 'CNI', 'RYAAY', 'FLCX', 'HRBR', 'PYRGF', 'RSKIA', 'NSGP', 'TPCS', 'CACO', 'PGTK', 'GTMAY', 'AUSI', 'ALPP', 'OCLN', 'CAMG', 'GPOX', 'TBLT', 'MACE', 'TLSS', 'PTNYF', 'AETHF', 'WARM', 'NVGT', 'DRFS', 'BLIS', 'DLYT', 'BRDSQ', 'FIFG', 'COUV', 'ZEVY', 'DTII', 'GDSI', 'BBRW', 'JPEX', 'WOEN', 'PHOT', 'AFIIQ', 'MJHI', 'WLMSQ', 'RNWR', 'YAYO', 'CHEAF', 'CHKIF', 'GNGYF', 'YELLQ', 'ACMB', 'UCIX', 'PRPI', 'AMMX', 'TMRR', 'ECOX', 'RENO', 'EVO', 'TARO', 'SUPN', 'MDRX', 'CORBF', 'BLUE', 'CELU', 'TIHE', 'EGRX', 'VICP', 'PNPL', 'OKYO', 'ESLA', 'DXR', 'BIMI', 'MDNAF', 'HSTI', 'PMCB', 'CLRD', 'COSM', 'BTTX', 'EDXC', 'RADCQ', 'ACBM', 'HENC', 'ALZN', 'XTLB', 'VFRM', 'RNVA', 'REPCF', 'ARDS', 'CWBR', 'ELOX', 'NMRD', 'INQD', 'GBLX', 'AGTX', 'VRAX', 'WORX', 'DVLP', 'CMRA', 'ATHXQ', 'MJNE', 'NTRR', 'PKBO', 'BLPH', 'INQR', 'RSPI', 'SDCCQ', 'GMVDF', 'QTXB', 'SGBI', 'CSTF', 'BLMS', 'BBBT', 'VNTH', 'GLSHQ', 'RGMP', 'QBIO', 'ATRX', 'RGTPQ', 'ACUR', 'INLB', 'STAB', 'HDVY', 'RVLPQ', 'IVRN', 'RBSH', 'INFIQ', 'BIOCQ', 'ABMC', 'HTGMQ', 'USRM', 'ONCSQ', 'VRAYQ', 'HGENQ', 'PHASQ', 'BBLNF', 'NMTRQ', 'SWGHF', 'BFFTF', 'SKYI', 'FZMD', 'PMEDF', 'TMDIF', 'INND', 'UTRS', 'IGEX', 'NAVB', 'CANQF', 'MCOA', 'GPFT', 'GRNF', 'IGPK', 'IMUC', 'SQZB', 'SNNC', 'TOMDF', 'KGKG', 'WCUI', 'ENDV', 'VIVE', 'PHBI', 'CBGL', 'SCPS', 'PHCG', 'EWLL', 'NPHC', 'NBRVF', 'CLSK', 'FIHL', 'ABIT', 'FRST', 'EVE', 'CFNB', 'ATEK', 'APXI', 'NPFC', 'PSBQ', 'IMAQ', 'VHAQ', 'SWSS', 'MSSA', 'MATH', 'OWVI', 'WTMA', 'MCAG', 'GNRV', 'ARGC', 'TNBI', 'TGGI', 'SLTN', 'SIVBQ', 'FDCT', 'OOGI', 'SITS', 'ADAD', 'FRBK', 'GLAE', 'EEGI', 'VCOR', 'BFYW', 'RAHGF', 'CONC', 'BZRD', 'WWSG', 'UNAM', 'SDON', 'MMMM', 'AFHIF', 'PLYN', 'EQOSQ', 'PMPG', 'SYSX', 'LFAP', 'CILJF', 'CIXXF', 'GAMI', 'BKSC', 'ODTC', 'GWIN', 'OFED', 'UBOH', 'FFBW', 'MSVB', 'OSBK', 'FIGI', 'BQST', 'TBBA', 'WVFC', 'ERKH', 'SICP', 'FGCO', 'BOPO', 'HALL', 'IMPM', 'MGHL', 'PUGE', 'PLPL', 'APSI', 'BABL', 'CSAN', 'UNTC', 'BROG', 'WTRV', 'SMGI', 'OILY', 'GRVE', 'GSPE', 'AMNI', 'QREE', 'DBRM', 'PCCYF', 'SNPMF', 'ATGFF', 'SPTJF', 'VTDRF', 'BRLL', 'MRGE', 'NOMD', 'AQPW', 'DOLE', 'ZHYBF', 'NXMH', 'RGF', 'MALG', 'MSS', 'CTGL', 'BRSH', 'GV', 'HPCO', 'WAFU', 'MNKA', 'FAMI', 'LEAI', 'RMHB', 'WTER', 'VGFCQ', 'SMFL', 'RTON', 'MFLTY', 'NUVI', 'OGAA', 'TTCFQ', 'TDNT', 'PCNT', 'TUEMQ', 'PACV', 'UPDC', 'ICNB', 'RAYT', 'BRCNF', 'QOEG', 'ASPU', 'GLUC', 'LMDCF', 'FKST', 'SGLA', 'HVCW', 'DTEAF', 'CELJF']
# just updated
# wasup = ['VZLA', 'ACRG', 'USAU', 'NRHI', 'ELRE', 'BOTY', 'CRMT', 'BGI', 'MOGU', 'KITL', 'EVTK', 'LSEB', 'HKD', 'DPLS', 'VEII', 'SING', 'PTOS', 'AXR', 'BUKS', 'PPSI', 'OPTT', 'HIHO', 'ATXG', 'YJGJ', 'KRFG', 'CSBR', 'CXXIF', 'HSCS', 'ABTI', 'ECIA', 'ADMT', 'EMCG', 'HUDA', 'CARV', 'TIRX', 'UROY', 'GWTI', 'OILCF', 'MMEX', 'SHMP', 'GNLN', 'ASII']

def testEDGARdata(ticker,cik):
    try:
        company_data = EDGAR_query(ticker, cik, header, ultimateTagsList)
        consol_table = mCTEDB(company_data, ticker)
    except Exception as err:
        print("test indies error: ")
        print(err)
    finally:
        # for x in consol_table:
        #     print(x)
        print(consol_table[['Ticker','year','rReitROE', 'rReitROEGrowthRate', 'cReitROE', 'cReitROEGrowthRate']])
        # print()

# print_DB('SELECT Ticker, payoutRatioAVGnz as por, fcfPayoutRatioAVGnz as fcfpor, ffoPayoutRatioAVGnz as ffopor FROM Metadata WHERE Ticker LIKE \'ADC\';', 'print')
# print_DB('SELECT * FROM Metadata;', 'print')

# time1 = time.time()
# tester = 'TSLA'
# testEDGARdata(tester, cik_dict[tester])
# time2 = time.time()
# print('time to complete')
# print((time2-time1)*1000)

# print_DB('SELECT Ticker, priceGrowthAVG FROM Metadata WHERE Ticker LIKE \'PG\';', 'print')
# print_DB('SELECT Ticker, year, price, priceGrowthRate as PGR FROM Mega_Backup WHERE Ticker LIKE \'TSLA\';', 'print')


#check size of all tables
# print_DB('SELECT name AS tableName, SUM(pgsize) AS bytesize FROM dbstat GROUP BY name ORDER BY bytesize DESC;', 'print')

#########################################################
##DB EXAMPLES THAT WORK
def copyMega():
    try:
        copyit = 'INSERT INTO Mega_Backup SELECT * FROM Mega;'
        conn = sql.connect(db_path)
        query = conn.cursor()
        query.execute(copyit)
        conn.commit()
        query.close()
        conn.close()
    except Exception as err:
        print('copy MD erro')
        print(err)
# copyMega()

def fillMega_Backup(): #Thank you ChatGPT, let's see if this can help me fix my DB copy failure. ugh.
    # Connect to the SQLite database
    conn = sql.connect(db_path)
    cursor = conn.cursor()
    # Replace with your table names
    old_table = "Mega"
    new_table = "Mega_Backup"

    # Get column names from oldtable
    cursor.execute(f"PRAGMA table_info({old_table})")
    columns = [row[1] for row in cursor.fetchall()]  # Column names are in the second field

    # Generate and execute update statements for each column
    for column in columns:
        if column != "id":  # Skip the ID column
            update_query = f"""
            UPDATE {new_table}
            SET {column} = (SELECT {column} FROM {old_table} WHERE {old_table}.id = {new_table}.id);
            """
            cursor.execute(update_query)
            print(f"Updated column: {column}")
    #for notes
    # 'UPDATE Mega_Backup SET Ticker = (SELECT Ticker FROM Mega WHERE Mega.id = Mega_Backup.id);'
    #
    # Commit and close
    conn.commit()
    cursor.close()
    conn.close()
# fillMega_Backup()

# print_DB('SELECT Ticker, revenue, CIK, Sector, divsPaidPerShare FROM Mega_Backup ;', 'print')
# print_DB('SELECT Ticker, revenue, CIK, Sector, divsPaidPerShare FROM Mega ;', 'print')
#Test differences between tables
# print_DB('SELECT * FROM Mega EXCEPT SELECT * FROM Mega_Backup;', 'print')

# print_DB(
#     'Drop Table Metadata;', 'print'
# )

def delete_ticker_DB(ticker):
    conn = sql.connect(db_path)
    query = conn.cursor()

    del_query = 'DELETE FROM Mega WHERE Ticker LIKE \''+ticker+'\';'
    query.execute(del_query)
    conn.commit()

    df12 = pd.read_sql('SELECT * FROM Mega WHERE Ticker LIKE \''+ticker+'\';', conn)
    print(df12)

    query.close()
    conn.close()

def find_badUnitsDB():
    # conn = sql.connect(db_path)
    # query = conn.cursor()
    # #del_query = 'SELECT DISTINCT Ticker FROM Mega;'
    # # query.execute(del_query)
    # # conn.commit()
    qentry = 'SELECT DISTINCT Ticker \
                FROM Mega \
                WHERE Units NOT LIKE \'USD\''
    badunits = print_DB(qentry, 'return')
    return badunits
    # df12 = pd.read_sql(qentry,conn)
    # print(df12)
    # query.close()
    # conn.close()

###LUKE mega function needs to be made ####
def megaDoAll():
    try:
        #Deal with stockList
        fillStockListTable()
        #Deal with Mega
        #Deal with Metadata
    except Exception as err:
        print('Mega Do All Error: ')
        print(err)

# guh = 'SELECT Ticker, year FROM Mega '
# mega = 'SELECT * FROM Mega;'
# megasaver = print_DB(mega, 'return')
# csv.simple_saveDF_to_csv('./', megasaver, 'Mega_csv', False)

# meta = 'SELECT * FROM Metadata;'
# metasaver = print_DB(meta, 'return')
# csv.simple_saveDF_to_csv('./', metasaver, 'Metadata_csv', False)

#################################################
# 
#         
# def delete_DB(table):
    #only use this while testing, or suffer the consequences
    # conn = sql.connect(db_path)
    # query = conn.cursor()
    # del_query = 'DELETE FROM Mega;'
    # query.execute(del_query)
    # conn.commit()
    # query.close()
    # conn.close()
    ####YOU HAVE BEEN WARNED

    # conn = sql.connect(db_path)
    # query = conn.cursor()

    # q = 'SELECT * FROM Mega ;'
    # query.execute(q)

    # table12.to_sql('Mega', conn, if_exists='append', index=False) # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html 

    # thequery = 'INSERT INTO Revenue (start,end,val,ticker,cik) VALUES ('+str(df13['start'])+',' +str(df13['end'])+',' +df13['val']+',' +df13['ticker']+',' +df13['cik']+');'
    # query.execute(thequery)
    # conn.commit()

    # del_query = 'DELETE FROM \'' + table + '\';'
    # query.execute(del_query)
    # conn.commit()

    # df12 = pd.DataFrame(query.execute('SELECT * FROM Revenue;'))

    # df12 = pd.read_sql('SELECT * FROM Mega;', conn)
    # print(df12)

    # query.close()
    # conn.close()
#----------------------------------------------------------------------------------------------
#############

### LUKE - To DO
### depreciation and amor with a handful of stocks
#notes from below for above
# missingDepreNAmor = ['MSFT', 'TSM', 'AVGO', 'ORCL', 'SAP', 'INTU', 'IBM', 'TXN']
#possible amoritization add: CapitalizedComputerSoftwareAmortization1 
#it looks like depre and amor isn't getting the full picture for the above stocks

#Revise code and models as needed. Create a function that can be called via script that:
## updates the stock ticker list table
## backs up mega to mega backup
## wipes mega
## refills mega
####

#---------------------------------------------------------------------
#What each value is
#---------------------------------------------------------------------
#roic = nopat / invested capital
#nopat = operating income * (1-tax rate)
#invested capital = total equity + total debt + non operating cash
#tequity = t assets - t liabilities
#ocf - capex = free cash flow
#fcf margin = fcf / revenue
#payout ratio = divs paid / net income
# modded payout ratio = divs paid / fcf
# ffo = netincomeloss + depr&amor - gainloss sale of property and it matches their reporting, 
# albeit slightly lower due to minor costs not included/found on sec reportings.
# You almost end up with a bas****ized affo value because of the discrepancy tho!
#---------------------------------------------------------------------
#---------------------------------------------------------------------
#The testing zone
#---------------------------------------------------------------------

# conn = sql.connect(db_path)
# query = conn.cursor()
# del_query = 'PRAGMA table_info(\'stockList\')'
# print(query.execute(del_query))
# conn.commit()
# query.close()
# conn.close()

# save = print_DB('PRAGMA table_info(\'stockList\')', 'return')
# print(save)


# ohmylord = ['ARCC', 'BBDC', 'BCSF', 'BKCC', 'BXSL', 'CCAP', 'CGBD', 'FCRD', 'CSWC', 'GAIN', 
#             'GBDC', 'GECC', 'GLAD', 'GSBD', 'HRZN', 'ICMB', 'LRFC', 'MFIC', 'MAIN', 'MRCC', 
#             'MSDL', 'NCDL', 'NMFC', 'OBDC', 'OBDE', 'OCSL', 'OFS', 'OXSQ', 'PFLT', 'PFX', 
#             'PNNT', 'PSBD', 'PSEC', 'PTMN', 'RAND', 'RWAY', 'SAR', 'SCM', 'SLRC', 'SSSS', 
#             'TCPC', 'TPVG', 'TRIN', 'TSLX', 'WHF', 'HTGC', 'CION', 'FDUS', 'FSK']

# ohmylord = ['BKCC','FCRD','NCDL','MSDL','PSBD','OBDE']
# for i in ohmylord:
#     delete_ticker_DB(i)

# write_list_to_Mega(ohmylord)

# bdcproblem = 'SLRC'
# company_data = EDGAR_query(bdcproblem, cik_dict[bdcproblem], header, ultimateTagsList)
# consol_table = mCTEDB(company_data, bdcproblem)
# print(consol_table)

# guh = 'SELECT DISTINCT Ticker FROM Mega WHERE Ticker IN ' + str(tuple(ohmylord))+ ';'
# guh = 'SELECT * FROM Mega WHERE Ticker LIKE \'NCDL\';'
# print_DB(guh, 'print')
# tickers = print_DB(guh,'return')
# print(len(ohmylord) - len(tickers['Ticker']))
# print(set(ohmylord).difference(tickers['Ticker']))

# likeit = [] 
# for x in likeit:
#     write_Master_csv_from_EDGAR(x,ultimateTagsList,'2024','2')
# checkYearsIntegrityList(likeit)

# ticker235 = 'NEE'  #agnc, wmb, 
# print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker235]+'.json')
# write_Master_csv_from_EDGAR(ticker235,ultimateTagsList,'2024','2')
# year235 = '2024'
# version235 = '2'
# print(ticker235 + ' income:')
# t235INC = makeIncomeTableEntry(ticker235,year235,version235,False)
# print(ticker235 + ' divs:')
# t235DIVS = makeDividendTableEntry(ticker235,year235,version235,False)
# print(ticker235 + '  roic: ')
# t235ROIC = makeROICtableEntry(ticker235,yea
# r235,version235,False) #['ReportedTotalEquity']
# print(ticker235 + ' divs and roic table: ')
# t235CON = fillPrice(makeConsolidatedTableEntry(ticker235, year235, version235, False))

#################