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

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}
#EDGAR API Endpoints
#companyconcept: returns all filing data from specific company, specific accounting item. timeseries for 'assets from apple'?
#company facts: all data from filings for specific company 
#frames: cross section of data from every company filed specific accnting item in specific period. quick company comparisons
ep = {"cc":"https://data.sec.gov/api/xbrl/companyconcept/" , "cf":"https://data.sec.gov/api/xbrl/companyfacts/" , "f":"https://data.sec.gov/api/xbrl/frames/"}

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

#Take full ticker, cik list and append sector, industry, upload to db
def uploadCIKs():
    try:
        tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
        time.sleep(0.1)
        tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
        tickers_cik['CIK'] = tickers_cik['cik_str'].astype(str).str.zfill(10)
        tickers_cik = tickers_cik.drop('cik_str',axis=1)
        tickers_cik = tickers_cik.drop('title',axis=1)
        tickers_cik = tickers_cik.drop_duplicates(subset='CIK', keep='first')

        df2save = pd.DataFrame(columns=['Ticker','CIK','Sector', 'Industry'])
        cikList = []
        tickerList = []
        sectorList = []
        industryList = []
        print_tracker = 0

        for x in tickers_cik['ticker']:
            print_tracker += 1
            try:
                stock = yf.Ticker(x)
                dict1 = stock.info
                sector = dict1['sector']
                industry = dict1['industry']

                cikList.append(tickers_cik.loc[tickers_cik['ticker'] == x, 'CIK'].iloc[0])
                tickerList.append(x)
                sectorList.append(sector)
                industryList.append(industry)

                time.sleep(0.1) #As a courtesy to yahoo finance, IDK if they have rate limits and will kick me, also.
            except Exception as err:
                print('try update tickers append lists error: ')
                print(err)
                continue

            print(print_tracker)

        df2save['Ticker'] = tickerList
        df2save['CIK'] = cikList
        df2save['Sector'] = sectorList
        df2save['Industry'] = industryList
        # csv.simple_saveDF_to_csv(fr_iC_toSEC, df3, 'badtickers',False)
        # csv.simple_saveDF_to_csv(fr_iC_toSEC, df2save, 'full_tickersCik_sectorsInd', False)
        uploadToDB(df2save,'stockList')
    except Exception as err:
        print('update tickerscikssectorsindustry error: ')
        print(err)
# uploadCIKs()

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
netIncomeNCI = ['ProfitLoss', 'ProfitLossAttributableToOwnersOfParent']

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
                deprecAndAmor3, shareHolderEquity, currentAssets, nonCurrentAssets, netAssetValue, dilutedSharesOutstanding, netIncomeNCI, 
                returnOfCapitalPerShare, totalReturnOfCapital ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'longTermDebt3', 'longTermDebt4',  'currentLiabilities','nonCurrentLiabilities',
                'deprecAndAmor2', 'deprecAndAmor3', 'shareHolderEquity', 'currentAssets','nonCurrentAssets', 'netAssetValue', 'dilutedSharesOutstanding', 
                'netIncomeNCI', 'returnOfCapitalPerShare', 'totalReturnOfCapital']
# removedFromUltList = [cashOnHand, altVariables, 'incomeTaxPaid',incomeTaxPaid,'exchangeRate',exchangeRate,]

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

# Returns organized data pertaining to the tag(s) provided in form of DF
def consolidateSingleAttribute(ticker, year, version, tagList, indexFlag):
    try:
        #get csv to df from params
        filtered_data = csv.simple_get_df_from_csv(stock_data, ticker + '_Master_' + year + '_V' + version, indexFlag)
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            held_data = filtered_data[filtered_data['Tag'].eq(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
        returned_data = get_Only_10k_info(returned_data)
        returned_data = dropAllExceptFYRecords(returned_data)
        returned_data = orderAttributeDF(returned_data) #moved from above fy records. so we gather 10k, all fy, then order then drop dupes
        returned_data = dropDuplicatesInDF(returned_data) #added after filtering for FY only
        returned_data = dropUselessColumns(returned_data)
        
        return returned_data

    except Exception as err:
        print("consolidate single attr error: ")
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
                conRev.append(curConvert.convert(origRev[i], 'USD', 'USD', date=date(int(datesFrom[i]),12,31))) #luke here added
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
        
        #Because Equity is important to calculations, we need to verify non-reported values as being a lower approximation of the mean 
        #of all liabilities over time.
        # LUKE RETHINK THIS...maybe
        assAndLies = pd.merge(assets, liabilities, on=['year','Ticker','CIK','Units'], how='outer')

        assAndLies['assets'] = assAndLies['val_x']
        assetsMean = assAndLies['assets'].mean() #/ ((len(assAndLies['assets'])/2)+1)
        assAndLies['assets'] = assAndLies['assets'].fillna(assetsMean)
        assAndLies['liabilities'] = assAndLies['val_y']
        liaMean = assAndLies['liabilities'].mean() #/ ((len(assAndLies['liabilities'])/2)+1)
        assAndLies['liabilities'] = assAndLies['liabilities'].fillna(liaMean)
        assAndLies = assAndLies.drop(['val_x','val_y'],axis=1)

        assAndLies = pd.merge(assAndLies, reportedEquity, on=['Units','year','Ticker','CIK'], how='outer')

        assAndLies['ReportedTotalEquity'] = assAndLies['val']
        assAndLies = assAndLies.drop(['val'],axis=1)

        assAndLies['TotalEquity'] = assAndLies['assets']-assAndLies['liabilities']

        return assAndLies

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

def cleanDividends(total, perShare, shares, dilutedShares, rocps, roctotal): 
    #luke here, units aren't consolidating properly for fdus
    try:
        shares = shares.rename(columns={'val':'shares'})
        shares = shares.drop(columns=['Units'])
        dilutedShares = dilutedShares.rename(columns={'val':'dilutedShares'})
        dilutedShares = dilutedShares.drop(columns=['Units'])

        total = cleanUnits(total)
        total = total.rename(columns={'val':'totalDivsPaid'})
        if total['Units'].isnull().all():
            total = total.drop(columns=['Units'])
        total['totalDivsPaid'] = (total['totalDivsPaid'] * (-1)).where(total['totalDivsPaid'] < 0, other=total['totalDivsPaid'])
        perShare = perShare.rename(columns={'val':'divsPaidPerShare'})
        perShare = perShare.drop(columns=['Units'])
        perShare['divsPaidPerShare'] = (perShare['divsPaidPerShare'] * (-1)).where(perShare['divsPaidPerShare'] < 0, other=perShare['divsPaidPerShare'])

        rocps = cleanUnits(rocps)
        rocps = rocps.rename(columns={'val':'ROCperShare'})
        if rocps['Units'].isnull().all():
            rocps = rocps.drop(columns=['Units'])
        roctotal = cleanUnits(roctotal)
        roctotal = roctotal.rename(columns={'val':'ROCTotal'})
        if roctotal['Units'].isnull().all():
            roctotal = roctotal.drop(columns=['Units'])
        #luke here
        df_col_added = pd.merge(total, perShare, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(shares, df_col_added, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(dilutedShares, df_col_added, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(roctotal, df_col_added, on=['year','Ticker','CIK'], how='outer')
        print('in clean divs')
        print(df_col_added)
        
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
        df_col_added['dilutedShares'] = df_col_added['dilutedShares'].ffill().bfill()
        growthCol = grManualCalc(df_col_added['shares'])
        df_col_added['sharesGrowthRate'] = growthCol

        growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
        df_col_added['divGrowthRateBOT'] = growthCol1 

        growthCol2 = grManualCalc(df_col_added['divsPaidPerShare'])
        df_col_added['divGrowthRateBORPS'] = growthCol2

        growthCol3 = grManualCalc(df_col_added['ROCperShare'])
        df_col_added['ROCperShareGrowthRate'] = growthCol3

        growthCol4 = grManualCalc(df_col_added['ROCTotal'])
        df_col_added['ROCTotalGrowthRate'] = growthCol4

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
        fixTracker = 0

        if df_filled['netCashFlow'].isnull().any():
            df_filled['netCashFlow'] = df_filled['netCashFlow'].fillna(df_filled['operatingCashFlow'] + df_filled['investingCashFlow'] + df_filled['financingCashFlow'])

        tarList = ['revenue','netIncome','netIncomeNCI','operatingCashFlow','investingCashFlow','financingCashFlow','netCashFlow', 'capEx', 'depreNAmor']
        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            savedCol = df_filled[x]
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol

            if savedCol.isnull().any():
                percentNull = savedCol.isnull().sum() / len(savedCol)
                if percentNull > 0.4:
                    fixTracker += 1

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

        #payout ratio related
        df_filled['payoutRatio'] = df_filled['totalDivsPaid'] / df_filled['netIncome']
        df_filled['fcfPayoutRatio'] = df_filled['totalDivsPaid'] / df_filled['fcf']
        df_filled['ffoPayoutRatio'] = df_filled['totalDivsPaid'] / df_filled['ffo']

        if fixTracker > 4:
            df_filled['INCintegrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['INCintegrityFlag'] = 'Good'
        else:
            df_filled['INCintegrityFlag'] = 'Acceptable'
        
    except Exception as err:
        print("fill empty inc GR error: ")
        print(err)
    finally:
        return df_filled

def fillEmptyDivsGrowthRates(df):
    try:
        df_filled = df
        fixTracker = 0

        if df_filled['interestPaid'].isnull().any():
            percentNull = df_filled['interestPaid'].isnull().sum() / len(df_filled['interestPaid'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['interestPaid'] = df_filled['interestPaid'].ffill().bfill()
        if df_filled['totalDivsPaid'].isnull().any():
            percentNull = df_filled['totalDivsPaid'].isnull().sum() / len(df_filled['totalDivsPaid'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['totalDivsPaid'] = df_filled['totalDivsPaid'].replace(np.nan, 0)
        if df_filled['divsPaidPerShare'].isnull().any():
            percentNull = df_filled['divsPaidPerShare'].isnull().sum() / len(df_filled['divsPaidPerShare'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['divsPaidPerShare'] = df_filled['divsPaidPerShare'].replace(np.nan, 0)
        if df_filled['shares'].isnull().all():
            fixTracker += 3
            df_filled['shares'] = df_filled['shares'].replace(np.nan, 0)
        elif df_filled['shares'].isnull().any():
            percentNull = df_filled['shares'].isnull().sum() / len(df_filled['shares'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['shares'] = df_filled['shares'].ffill().bfill() 

        df_filled['ROCperShare'] = df_filled['ROCperShare'].replace(np.nan, 0)
        df_filled['ROCTotal'] = df_filled['ROCTotal'].replace(np.nan, 0)

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

        if df_filled['ROCperShareGrowthRate'].isnull().any():
            growthCol = grManualCalc(df_filled['ROCperShare'])
            df_filled['temp5'] = growthCol
            df_filled['ROCperShareGrowthRate'] = df_filled['ROCperShareGrowthRate'].fillna(df_filled.pop('temp5'))
        
        if df_filled['ROCTotalGrowthRate'].isnull().any():
            growthCol = grManualCalc(df_filled['ROCTotal'])
            df_filled['temp6'] = growthCol
            df_filled['ROCTotalGrowthRate'] = df_filled['ROCTotalGrowthRate'].fillna(df_filled.pop('temp6'))

        if df_filled['dilutedShares'].isnull().all():
            df_filled['dilutedSharesGrowthRate'] = np.nan
        else:
            growthCol1 = grManualCalc(df_filled['dilutedShares'])
            df_filled['dilutedSharesGrowthRate'] = growthCol1

        if df_filled['Units'].isnull().all():
            df_filled = df_filled.drop('Units',axis=1)
        else:
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        if fixTracker >= 4:
            df_filled['DIVintegrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['DIVintegrityFlag'] = 'Good'
        else:
            df_filled['DIVintegrityFlag'] = 'Acceptable'
        
    except Exception as err:
        print("fill empty divs GR error: ")
        print(err)

    finally:
        return df_filled

def fillEmptyROICGrowthRates(df):
    try:
        df_filled = df
        fixTracker = 0
        tarList = ['operatingIncome']
        tDebt = 'TotalDebt'
        equityParts = ['assets','liabilities']

        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            savedCol = df_filled[x]
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol

            if savedCol.equals(df_filled[x]):
                continue
            else:
                fixTracker += 1

        if df_filled['TotalDebt'].isnull().any():
            percentNull = df_filled['TotalDebt'].isnull().sum() / len(df_filled['TotalDebt'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['TotalDebt'] = df_filled['TotalDebt'].replace(np.nan, 0)
        if df_filled['assets'].isnull().any():
            percentNull = df_filled['assets'].isnull().sum() / len(df_filled['assets'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['assets'] = df_filled['assets'].ffill().bfill()
        if df_filled['liabilities'].isnull().any():
            percentNull = df_filled['liabilities'].isnull().sum() / len(df_filled['liabilities'])
            if percentNull > 0.4:
                fixTracker += 1
            df_filled['liabilities'] = df_filled['liabilities'].ffill().bfill()
        df_filled['TotalEquity'] = df_filled['TotalEquity'].fillna(df_filled['assets'] - df_filled['liabilities'])

        if df_filled['Units'].isnull().all():
            df_filled = df_filled.drop('Units',axis=1)
        else:
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        df_filled['nopat'] = df_filled['operatingIncome'] * (1 - df_filled['taxRate'])
        df_filled['investedCapital'] = df_filled['TotalEquity'] + df_filled['TotalDebt']
        df_filled['roic'] = df_filled['nopat'] / df_filled['investedCapital'] * 100
        df_filled['adjRoic'] = df_filled['netIncome'] / df_filled['investedCapital'] * 100
        df_filled['reportedAdjRoic'] = df_filled['netIncome'] / (df_filled['ReportedTotalEquity'] + df_filled['TotalDebt']) * 100
        df_filled['calculatedRoce'] = df_filled['netIncome'] / df_filled['TotalEquity'] * 100
        df_filled['reportedRoce'] = df_filled['netIncome'] / df_filled['ReportedTotalEquity'] * 100
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

        if fixTracker > 4:
            df_filled['ROICintegrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['ROICintegrityFlag'] = 'Good'
        else:
            df_filled['ROICintegrityFlag'] = 'Acceptable'

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
        
#Making tables for DB insertion, left for notes, but deprecated and consolidated below
# def makeIncomeTableEntry(ticker, year, version, index_flag):
#     try:
#         rev_df = cleanRevenue(consolidateSingleAttribute(ticker, year, version, revenue, False))
#         netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
#         netIncNCI_df = cleanNetIncomeNCI(consolidateSingleAttribute(ticker, year, version, netIncomeNCI, False))
#         opcf_df = cleanOperatingCashFlow(consolidateSingleAttribute(ticker, year, version, operatingCashFlow, False))
#         invcf_df = cleanInvestingCashFlow(consolidateSingleAttribute(ticker, year, version, investingCashFlow, False))
#         fincf_df = cleanFinancingCashFlow(consolidateSingleAttribute(ticker, year, version, financingCashFlow, False))
#         netcf_df = cleanNetCashFlow(consolidateSingleAttribute(ticker, year, version, netCashFlow, False))
#         capex_df = cleanCapEx(consolidateSingleAttribute(ticker, year, version, capEx, False))
#         depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))
#         if depAmor_df.empty:
#             depAmor_df = cleanDeprNAmor2(consolidateSingleAttribute(ticker, year, version, deprecAndAmor2, False),
#                                             consolidateSingleAttribute(ticker, year, version, deprecAndAmor3, False))
#         gainSaleProp_df = cleanGainSaleProp(consolidateSingleAttribute(ticker, year, version, gainSaleProperty, False))
        
#         revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
#         revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusopcf = pd.merge(revNinc, opcf_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','Ticker','CIK','Units'], how='outer')
#         pluscapex = pd.merge(plusnetcf, capex_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusDepAmor = pd.merge(pluscapex, depAmor_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plusSaleProp = pd.merge(plusDepAmor, gainSaleProp_df, on=['year','Ticker','CIK','Units'], how='outer')
#         #CLEAN column empty values here before adding FFO calculations 
#         plusSaleProp = fillEmptyIncomeGrowthRates(plusSaleProp)
#         plusSaleProp = plusSaleProp.drop(columns=['depreNAmorGrowthRate'])
        
#         addfcf = cleanfcf(plusSaleProp)
#         addfcfMargin = cleanfcfMargin(addfcf)
#         #Clean sales of property
#         addfcfMargin['gainSaleProp'] = addfcfMargin['gainSaleProp'].replace(np.nan,0)
#         addfcfMargin['ffo'] = addfcfMargin['netIncome'] + addfcfMargin['depreNAmor'] - addfcfMargin['gainSaleProp']
#         growthCol = grManualCalc(addfcfMargin['ffo'])
#         addfcfMargin['ffoGrowthRate'] = growthCol

#         return addfcfMargin

#     except Exception as err:
#         print("makeIncomeTable error: ")
#         print(err)

# def makeROICtableEntry(ticker, year, version, index_flag):
#     try:
#         opIncome_df = cleanOperatingIncome(consolidateSingleAttribute(ticker, year, version, operatingIncome, False))
#         taxRate_df = cleanTaxRate(consolidateSingleAttribute(ticker, year, version, taxRate, False))
#         netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
#         totalDebt_df = cleanDebt(consolidateSingleAttribute(ticker, year, version, shortTermDebt, False), 
#                                     consolidateSingleAttribute(ticker, year, version, longTermDebt1, False), 
#                                     consolidateSingleAttribute(ticker, year, version, longTermDebt2, False),
#                                     consolidateSingleAttribute(ticker, year, version, longTermDebt3, False), 
#                                     consolidateSingleAttribute(ticker, year, version, longTermDebt4, False))
#         totalEquity_df = cleanTotalEquity(consolidateSingleAttribute(ticker, year, version, totalAssets, False), 
#                                     consolidateSingleAttribute(ticker, year, version, totalLiabilities, False), 
#                                     consolidateSingleAttribute(ticker, year, version, nonCurrentLiabilities, False),
#                                     consolidateSingleAttribute(ticker, year, version, currentLiabilities, False), 
#                                     consolidateSingleAttribute(ticker, year, version, nonCurrentAssets, False),
#                                     consolidateSingleAttribute(ticker, year, version, currentAssets, False), 
#                                     consolidateSingleAttribute(ticker, year, version, shareHolderEquity, False))
#         opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
#         if opIncNtax['Units'].isnull().any():
#             opIncNtax = opIncNtax.drop(columns=['Units'], axis=1)
#             opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK'], how='outer')
#         else:
#             opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
#             opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])
#         opIncNtaxNinc['Units'] = opIncNtaxNinc['Units'].ffill().bfill()
#         plustDebt = pd.merge(opIncNtaxNinc, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
#         plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
#         plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
     
#         plustEquity = fillEmptyROICGrowthRates(plustEquity)

#         plustEquity['nopat'] = plustEquity['operatingIncome'] * (1 - plustEquity['taxRate'])
#         plustEquity['investedCapital'] = plustEquity['TotalEquity'] + plustEquity['TotalDebt']
#         plustEquity['roic'] = plustEquity['nopat'] / plustEquity['investedCapital'] * 100
#         plustEquity['adjRoic'] = plustEquity['netIncome'] / plustEquity['investedCapital'] * 100
#         plustEquity['reportedAdjRoic'] = plustEquity['netIncome'] / (plustEquity['ReportedTotalEquity'] + plustEquity['TotalDebt']) * 100
#         plustEquity['calculatedRoce'] = plustEquity['netIncome'] / plustEquity['TotalEquity'] * 100
#         plustEquity['reportedRoce'] = plustEquity['netIncome'] / plustEquity['ReportedTotalEquity'] * 100

#         return plustEquity

#     except Exception as err:
#         print("makeROIC table error: ")
#         print(err)

# def makeDividendTableEntry(ticker, year, version, index_flag):
#     try:
#         intPaid_df = cleanInterestPaid(consolidateSingleAttribute(ticker, year, version, interestPaid, False))
#         divs_df = cleanDividends(consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, False), 
#                                     consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, False),
#                                     consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False),
#                                     consolidateSingleAttribute(ticker, year, version, dilutedSharesOutstanding, False),
#                                     consolidateSingleAttribute(ticker, year, version, returnOfCapitalPerShare, False),
#                                     consolidateSingleAttribute(ticker, year, version, totalReturnOfCapital, False))
#         if divs_df['year'][0] == -1:
#             df_dunce = pd.DataFrame(columns=['Ticker'])
#             df_dunce.loc[0, 'Ticker'] = ticker
#             csv.simple_appendTo_csv(fr_iC_toSEC, df_dunce,'z-divDataReallyNotFound', False)
#             return 'No Good Dividend Data'
#         else:
#             if divs_df['Units'].isnull().any():
#                 divs_df = divs_df.drop(columns=['Units'])
#                 intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')#Was nested in else on row 'start', 'end',
#             else:
#                 intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer') 

#             intNdivs = fillEmptyDivsGrowthRates(intNdivs)

#             return intNdivs
    
#     except Exception as err:
#         print("makeDividend table error: ")
#         print(err)

def makeConsolidatedTableEntry(ticker, year, version, index_flag):
    try:
        ### INCOME TABLE START
        rev_df = cleanRevenue(consolidateSingleAttribute(ticker, year, version, revenue, False))
        netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
        netIncNCI_df = cleanNetIncomeNCI(consolidateSingleAttribute(ticker, year, version, netIncomeNCI, False))
        eps_df = cleanEPS(consolidateSingleAttribute(ticker, year, version, eps, False))
        opcf_df = cleanOperatingCashFlow(consolidateSingleAttribute(ticker, year, version, operatingCashFlow, False))
        invcf_df = cleanInvestingCashFlow(consolidateSingleAttribute(ticker, year, version, investingCashFlow, False))
        fincf_df = cleanFinancingCashFlow(consolidateSingleAttribute(ticker, year, version, financingCashFlow, False))
        netcf_df = cleanNetCashFlow(consolidateSingleAttribute(ticker, year, version, netCashFlow, False))
        capex_df = cleanCapEx(consolidateSingleAttribute(ticker, year, version, capEx, False))
        depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))
        if depAmor_df.empty:
            depAmor_df = cleanDeprNAmor2(consolidateSingleAttribute(ticker, year, version, deprecAndAmor2, False),
                            consolidateSingleAttribute(ticker, year, version, deprecAndAmor3, False))
        gainSaleProp_df = cleanGainSaleProp(consolidateSingleAttribute(ticker, year, version, gainSaleProperty, False))
        
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer') 
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
        intPaid_df = cleanInterestPaid(consolidateSingleAttribute(ticker, year, version, interestPaid, False))
        divs_df = cleanDividends(consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, False), 
                                    consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, dilutedSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, returnOfCapitalPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, totalReturnOfCapital, False))
        if 'Units' not in divs_df:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        elif divs_df['Units'].isnull().any():
            divs_df = divs_df.drop(columns=['Units'])
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        else:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        
        intNdivs = fillUnits(intNdivs)
        ### DIVS TABLE END
        
        ### ROIC TABLE START
        opIncome_df = cleanOperatingIncome(consolidateSingleAttribute(ticker, year, version, operatingIncome, False))
        taxRate_df = cleanTaxRate(consolidateSingleAttribute(ticker, year, version, taxRate, False))
        totalDebt_df = cleanDebt(consolidateSingleAttribute(ticker, year, version, shortTermDebt, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt1, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt2, False),
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt3, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt4, False))
        totalEquity_df = cleanTotalEquity(consolidateSingleAttribute(ticker, year, version, totalAssets, False), 
                                    consolidateSingleAttribute(ticker, year, version, totalLiabilities, False), 
                                    consolidateSingleAttribute(ticker, year, version, nonCurrentLiabilities, False),
                                    consolidateSingleAttribute(ticker, year, version, currentLiabilities, False), 
                                    consolidateSingleAttribute(ticker, year, version, nonCurrentAssets, False),
                                    consolidateSingleAttribute(ticker, year, version, currentAssets, False), 
                                    consolidateSingleAttribute(ticker, year, version, shareHolderEquity, False))
                                    
        nav_df = cleanNAV(consolidateSingleAttribute(ticker, year, version, netAssetValue, False))

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        opIncNtax['Units'] = opIncNtax['Units'].ffill().bfill()
        if opIncNtax['Units'].isnull().all():
            opIncNtax['Units'] = 'USD'
        
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
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

        incDivsROIC = fillPrice(incDivsROIC)

        incDivsROIC = fillEmptyDivsGrowthRates(incDivsROIC) 
        
        #Finish the Income Table Entries
        incDivsROIC = fillEmptyIncomeGrowthRates(incDivsROIC)

        #Finish the ROIC Table Entries
        incDivsROIC = fillEmptyROICGrowthRates(incDivsROIC)

        incDivsROIC['Sector'] = nameSectorDict[ticker]
        incDivsROIC['Industry'] = nameIndustryDict[ticker]
    except Exception as err:
        print("make consolidated table error: ")
        print(err)
    finally:
        return incDivsROIC
   
# Returns organized data pertaining to the tag(s) provided in form of DF, but from API, for DB, instead of from CSV
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
def mCTEDB(df, ticker):
    try:
        ### INCOME TABLE START
        rev_df = cleanRevenue(cSADB(df, revenue))
        netInc_df = cleanNetIncome(cSADB(df, netIncome))
        netIncNCI_df = cleanNetIncomeNCI(cSADB(df, netIncomeNCI))
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
        revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer') 
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
                                    cSADB(df, basicSharesOutstanding),
                                    cSADB(df, dilutedSharesOutstanding),
                                    cSADB(df, returnOfCapitalPerShare),
                                    cSADB(df, totalReturnOfCapital))
        
        # intPaid_df = fillUnits(intPaid_df) #luke here remove these
        print('intpaid')
        for x in intPaid_df:
            print(x)
            print(intPaid_df[x])
        print(intPaid_df)
        # divs_df = fillUnits(divs_df)
        print('divs df')
        for y in divs_df:
            print(y)
            print(divs_df[y])

        if 'Units' not in divs_df:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        else: #luke you added this and commented that out
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        # elif divs_df['Units'].isnull().any():
        #     divs_df = divs_df.drop(columns=['Units'])
        #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        # else:
        #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        
        intNdivs = fillUnits(intNdivs)
        # for x in intNdivs:
        #     print(x)
        #     print(intNdivs[x])
        # print(plusSaleProp) #luke
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
        opIncNtax['Units'] = opIncNtax['Units'].ffill().bfill()

        if opIncNtax['Units'].isnull().all():
            opIncNtax['Units'] = 'USD'
        
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')

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

def write_full_EDGAR_to_Mega():
    try:
        errorTickers = []
        # getStocks = 'SELECT Ticker, CIK FROM stockList;'
        # gSdf = print_DB(getStocks, 'return')
        tickerlist = gSdf['Ticker'].tolist()
        # cik_dict = gSdf.set_index('Ticker')['CIK'].astype(str).str.zfill(10).to_dict()
        for i in tickerlist:
            print(i)
            try:
                company_data = EDGAR_query(i, cik_dict[i], header, ultimateTagsList)
                consol_table = mCTEDB(company_data, i)
                time.sleep(0.1)
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

def write_list_to_Mega(thelist):
    try:
        errorTickers = []
        # getStocks = 'SELECT Ticker, CIK FROM stockList;'
        # gSdf = print_DB(getStocks, 'return')
        # tickerlist = tuple(thelist)
        # cik_dict = gSdf.set_index('Ticker')['CIK'].astype(str).str.zfill(10).to_dict()
        for i in thelist:
            print(i)
            try:
                company_data = EDGAR_query(i, cik_dict[i], header, ultimateTagsList)
                consol_table = mCTEDB(company_data, i)
                uploadToDB(consol_table, 'Mega')
                print(i + ' uploaded to DB!')
                time.sleep(0.1)
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

#this gets all stocks and tickers available, then all tickers in Mega, checks latest year in Mega, 
# gathers new data where necessary and uploads only that to Mega
def update_Mega(latestyear):
    try:
        # getStocks = 'SELECT Ticker, CIK FROM stockList;'
        # gSdf = print_DB(getStocks, 'return')
        # cik_dict = gSdf.set_index('Ticker')['CIK'].astype(str).str.zfill(10).to_dict()
        #get list of tickers in mega
        gettickers = 'SELECT DISTINCT(Ticker) FROM Mega;'
        tickersinmega = print_DB(gettickers, 'return')['Ticker'].tolist()
        stillNotUpdated = []
        updated = []
        for x in tickersinmega:
            getyears = 'SELECT Ticker, year FROM Mega\
                        WHERE Ticker IN (\'' + x + '\');'
            yearsdf = print_DB(getyears, 'return')
            newdf = yearsdf.max()
            latestyearinDB = newdf['year']
            if latestyearinDB != latestyear:
                try:
                    company_data = EDGAR_query(x, cik_dict[x], header, ultimateTagsList)
                    consol_table = mCTEDB(company_data, x)
                    time.sleep(0.1)
                    #here we have to only upload the rows where year is greater than the latest year
                    consol_table = consol_table[consol_table['year'] > latestyearinDB]
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
                    continue

    except Exception as err:
        print("update mega DB error: ")
        print(err)
    finally:
        #luke this will eventually be saved in logs
        print('stocks still needing updates:')
        print(stillNotUpdated)
        print('those that just got updated:')
        print(updated)

# update_Mega('2023')

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
        print(consol_table)

# testEDGARdata('MSFT','0000789019')

#testing functionality while refactoring
# company_data = EDGAR_query('MSFT', '0000789019', header, ultimateTagsList)
# print(company_data)
#########################################################
#Not used
##DB EXAMPLES THAT WORK
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

# ohmylord = ['ARCC', 'BBDC', 'BCSF', 'BKCC', 'BXSL', 'CCAP', 'CGBD', 'FCRD', 'CSWC', 'GAIN', 
#             'GBDC', 'GECC', 'GLAD', 'GSBD', 'HRZN', 'ICMB', 'LRFC', 'MFIC', 'MAIN', 'MRCC', 
#             'MSDL', 'NCDL', 'NMFC', 'OBDC', 'OBDE', 'OCSL', 'OFS', 'OXSQ', 'PFLT', 'PFX', 
#             'PNNT', 'PSBD', 'PSEC', 'PTMN', 'RAND', 'RWAY', 'SAR', 'SCM', 'SLRC', 'SSSS', 
#             'TCPC', 'TPVG', 'TRIN', 'TSLX', 'WHF', 'HTGC', 'CION', 'FDUS', 'FSK']

ohmylord = ['FDUS']
# for i in ohmylord:
#     delete_ticker_DB(i)

# write_list_to_Mega(ohmylord)

company_data = EDGAR_query('FDUS', cik_dict['FDUS'], header, ultimateTagsList)
consol_table = mCTEDB(company_data, 'FDUS')
# print(consol_table)

# guh = 'SELECT * FROM Mega WHERE Ticker IN ' + str(tuple(ohmylord))+ ';'
# guh = 'SELECT * FROM Mega WHERE Ticker LIKE \'FDUS\';'
# print_DB(guh,'print')

def find_badUnitsDB():
    conn = sql.connect(db_path)
    query = conn.cursor()
    # del_query = 'SELECT DISTINCT Ticker FROM Mega;'
    # query.execute(del_query)
    # conn.commit()
    qentry = 'SELECT DISTINCT Ticker \
                FROM Mega \
                WHERE Units NOT LIKE \'USD\''
    df12 = pd.read_sql(qentry,conn)
    print(df12)

    query.close()
    conn.close()

# def delete_DB(table):
    #only use this while testing, or suffer the consequences
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
# dblist = print_DB()['ticker']
# print(datlist)
# sourcelist = materials['Ticker']
#############

### LUKE - To DO
### depreciation and amor with a handful of stocks
#notes from below for above
# missingDepreNAmor = ['MSFT', 'TSM', 'AVGO', 'ORCL', 'SAP', 'INTU', 'IBM', 'TXN']
#possible amoritization add: CapitalizedComputerSoftwareAmortization1 
#it looks like depre and amor isn't getting the full picture for the above stocks
####
#need to check differences between what is in stockList, from SEC filings, and what is in Mega,
#so when you updateMega, great, records are updated, but any newbies are then also added fresh

## clean units error usd/share not a supported currency for bbdc at least.
#need to run a full scan of the bdc's. catch those errors and fix them. delete and refresh db with them. they're generating an extra column for some reason

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
# ffo = netincomeloss + depr&amor - gainloss sale of property and it matches their reporting, albeit slightly lower due to minor costs not included/found on sec reportings.
# You almost end up with a bas****ized affo value because of the discrepancy tho!
#ffo/(dividend bulk payment + interest expense) gives idea of how much money remains after paying interest and dividends for reits. aim for ratio > 1
#---------------------------------------------------------------------

#---------------------------------------------------------------------
#The testing zone
#---------------------------------------------------------------------
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

# t235CON = makeConsolidatedTableEntry(ticker235, year235, version235, False)
# print(t235CON)
# print(t235CON['calculatedEPS'])
# print(t235CON['reportedEPS'] == t235CON['calculatedEPS'])
# print(t235CON['shares'])
# print(t235CON['calculatedEPSGrowthRate'])
# print(t235CON['fcfPayoutRatio'])
# print(t235CON['reitEPSGrowthRate'] - t235CON['calculatedEPSGrowthRate'])
# print(t235CON['year'])

# for x in t235CON:
#     print(x)
# print(t235CON)
# divTests = ['shares', 'totalDivsPaid', 'divsPaidPerShare','divGrowthRateBORPS']
# for x in divTests:
#     if t235CON[x].equals(t235DIVS[x]):
#         pass
#     else:
#         print(x + ' did not match.')
        # print('con:')
        # print(t235CON[x])
        # print('divs:')
        # print(t235DIVS[x])
# for x in t235CON:
#     print(x)

# print(set(techmissingincomeyears).difference(techmissingroicyears))

# print(set(wrong).difference(REincwrongendyear))
# print(len(techmissingincomecapEx))
# print(len(techmissingincomecapex2))

# checkYearsIntegritySector(util,0,10)

# ticker12 = 'O' #ABR
# print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker12]+'.json')
# write_Master_csv_from_EDGAR(ticker12,ultimateTagsList,'2024','2')
# year12 = '2024'
# version12 = '2'
# print(ticker12 + ' income:')
# print(makeIncomeTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs:')
# print(makeDividendTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs and roic table: ')
# print(makeConsolidatedTableEntry(ticker12, year12, version12, False).iloc[:, 0:12])
# print(ticker12 + ' roic: ')
# print(makeROICtableEntry(ticker12,'2024',version12,False)) #'ReportedTotalEquity'
# print(ticker12 + ' divs and roic table: ')
# table12 = makeConsolidatedTableEntry(ticker12, year12, version12, False)
# print(table12['ReportedTotalEquity'])

#################
# ticker13 = 'MSFT' 
# year13 = '2024'
# version13 = '2'
# print(ticker13 + ' income:')
# print(makeIncomeTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + ' divs:')
# print(makeDividendTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + '  roic: ')
# print(makeROICtableEntry(ticker13,'2024',version13,False))

# ticker12 = 'NEE' 
# year12 = '2024'
# version12 = '2'
# print(ticker12 + ' income:')
# print(makeIncomeTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs:')
# print(makeDividendTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' roic: ')
# print(makeROICtableEntry(ticker12,'2024',version12,False))

# ticker14 = 'O' #EGP
# year14 = '2024'
# version14 = '2'
# print(ticker14 + ' income:')
# print(makeIncomeTableEntry(ticker14,year14,version14,False))
# print(ticker14 + ' divs:')
# print(makeDividendTableEntry(ticker14,'2024',version14,False))
# print(ticker14 + '  roic: ')
# print(makeROICtableEntry(ticker14,'2024',version14,False))

# ticker234 = 'ARCC'
# year234 = '2024'
# version234 = '2'
# print(ticker234 + ' income:')
# print(makeIncomeTableEntry(ticker234,year234,version234,False))
# print(ticker234 + ' divs:')
# print(makeDividendTableEntry(ticker234,year234,version234,False))
# print(ticker234 + ' roic: ')
# print(makeROICtableEntry(ticker234,year234,version234,False))


# ticker123 = 'AMZN' #AMZN
# year123 = '2024'
# version123 = '2'
# print('AMZN income:')
# print(makeIncomeTableEntry(ticker123,'2024',version123,False))
# print('AMZN divs:')
# print(makeDividendTableEntry(ticker123,'2024',version123,False))
# print('AMZN roic: ')
# print(makeROICtableEntry(ticker123,'2024',version123,False))