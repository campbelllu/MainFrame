import numpy as np
import pandas as pd
# import pandas_datareader.data as web
#docu: https://pandas-datareader.readthedocs.io/en/latest/ 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import datetime as dt
# import mplfinance as mpf
# import datetime as dt
import time
import yfinance as yf
import json
# import pyarrow
import requests
import math
# from itertools import chain
from collections import Counter as counter
import sqlite3 as sql
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning) #infer_objects(copy=False) works nonreliably. SO WE JUST SQUELCH IT ALTOGETHER!
# import gc
from currency_converter import CurrencyConverter #https://pypi.org/project/CurrencyConverter/
converter_address = '/home/family/Documents/repos/MainFrame/mainframe/investor_center/currency-hist.csv' 
curConvert = CurrencyConverter(converter_address, fallback_on_missing_rate=True)
### Documentation: https://pypi.org/project/CurrencyConverter/ 
from datetime import date
import time
import statistics as stats
# from forex_python.converter import CurrencyRates

import csv_modules as csv

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}

### The initial fetching of CIKS and Tickers needs to have an automated function eventually. This part was skipped, having been harvested manually and data massaging and program setup began instead. 
### A fun project for later once all this gets plugged into API calls on a website! :)
# #Automated pulling of tickers and cik's
# tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
# tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
# tickers_cik['cik_str'] = tickers_cik['cik_str'].astype(str).str.zfill(10)
#Then you have to save said df to csv, done below manually.

#We have to parse full SEC CIK list into a df
def convert_CIKdict_to_df(dictionary):
    df = pd.DataFrame()
    cik = "cik_str"
    ticker = "ticker"
    name = "title"
    try:
        #make dict into lists, easier to add to df
        tlist = []
        nlist = []
        clist = []
        for x in dictionary:
            tlist.append(dictionary[x][ticker])
            nlist.append(dictionary[x][name])
            clist.append(dictionary[x][cik])
        #append lists into appropriate columns of df1
        df['Ticker'] = tlist
        df['Company Name'] = nlist
        df['CIK'] = clist
        df['CIK'] = df['CIK'].astype(str).str.zfill(10) #check indentation upon copy
    except Exception as err:
        print(err)
    else:
        print("DF made! Here it is!")
        # print(df)
        return df
# # Manual processing of data to generate ticker repo's
# #Manually saved json of tickers and cik's from SEC. Methods for automating download to be added later(later added, above.).
# json_path = './sec_related/full_cik_list.json'
# #turn it into a dict to feed into above function
# with open(json_path, 'r') as j:
#     fcl_dict = json.loads(j.read())
# #print(fcl_dict)
# #Turn that dict into a df, check how it looks
# df2 = convert_CIKdict_to_df(fcl_dict)
# print(df2)
# #Make the CSV, check name and save-location before executing!
# csv.simple_saveDF_to_csv('./sec_related/', df2, 'full_tickers_and_ciks2', False)

#Take full cik list and append sector, industry, marketcap info onto it
def updateTickersCiksSectors():
    #'quoteType' might be useful later to verify equity=stock vs etf=etf, uncertain, currently not included
    try:
        df2save = pd.DataFrame(columns=['Ticker','Company Name','CIK','Sector', 'Industry'])
        cikList = []
        tickerList = []
        titleList = []
        sectorList = []
        industryList = []
        marketCapList = []
        print_tracker = 0
        errorTracker = []
        for i in range(math.floor(len(full_cik_list))):
            print_tracker += 1
            cik = full_cik_list['CIK'][i] 
            ticker = full_cik_list['Ticker'][i]
            title = full_cik_list['Company Name'][i]
            try:

                stock = yf.Ticker(ticker)
                dict1 = stock.info

                sector = dict1['sector']
                industry = dict1['industry']
                # marketCap = dict1['marketCap']

                cikList.append(cik)
                tickerList.append(ticker)
                titleList.append(title)
                sectorList.append(sector)
                industryList.append(industry)
                # marketCapList.append(marketCap)

                time.sleep(0.1) #As a courtesy to yahoo finance, IDK if they have rate limits and will kick me, also.
            except Exception as err:
                print('try update tickers append lists error: ')
                print('ticker, sector: ',ticker,sector)
                errorTracker.append(ticker)
                print(err)

            if print_tracker % 10 == 0:
                print("Finished data pull for(ticker): " + ticker)# + ', ' + str(marketCap))
            
        df2save['Ticker'] = tickerList
        df2save['Company Name'] = titleList
        df2save['CIK'] = cikList
        df2save['Sector'] = sectorList
        df2save['Industry'] = industryList
        # df2save['Market Cap'] = marketCapList
        # print(df2save)
        df3 = pd.DataFrame(errorTracker)
        csv.simple_saveDF_to_csv(fr_iC_toSEC, df3, 'badtickers',False)
        csv.simple_saveDF_to_csv(fr_iC_toSEC, df2save, 'full_tickersCik_sectorsInd', False)
    except Exception as err:
        print('update tickerscikssectorsindustry error: ')
        print(err)
# updateTickersCiksSectors()

# ------------------------------------------
# The above represents organizing ticker data, with the exception of sector csv's and duplicate cleanup, below is getting company data from API calls to SEC EDGAR.
# ------------------------------------------

#EDGAR API Endpoints
#companyconcept: returns all filing data from specific company, specific accounting item. timeseries for 'assets from apple'?
#company facts: all data from filings for specific company 
#frames: cross section of data from every company filed specific accnting item in specific period. quick company comparisons
ep = {"cc":"https://data.sec.gov/api/xbrl/companyconcept/" , "cf":"https://data.sec.gov/api/xbrl/companyfacts/" , "f":"https://data.sec.gov/api/xbrl/frames/"}

fr_iC_toSEC = '/home/family/Documents/repos/MainFrame/mainframe/sec_related/' #..
fr_iC_toSEC_stocks = '/home/family/Documents/repos/MainFrame/mainframe/sec_related/stocks/' 
stock_data = './stockData/'

db_path = '/home/family/Documents/repos/MainFrame/mainframe/stock_data.sqlite3'

#Set types for each column in df, to retain leading zeroes upon csv -> df loading.
type_converter = {'Ticker': str, 'Company Name': str, 'CIK': str}
type_converter_full = {'Ticker': str, 'Company Name': str, 'CIK': str, 'Sector': str, 'Industry': str, 'Market Cap': str}
type_converter_full2 = {'Ticker': str, 'Company Name': str, 'CIK': str, 'Sector': str, 'Industry': str}#, 'Market Cap': str}

# full_cik_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickers_and_ciks', type_converter)
# full_cik_sectInd_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickersCik_sectorsInd', type_converter_full)
clean_stockList = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_stockList_clean', type_converter_full2)
#/home/family/Documents/repos/MainFrame/mainframe/investor_center/workbook1.py
#/home/family/Documents/repos/MainFrame/mainframe/sec_related/full_stockList_clean.csv
# sec_related/full_stockList_clean.csv

nameCikDict = clean_stockList.set_index('Ticker')['CIK'].to_dict()
nameSectorDict = clean_stockList.set_index('Ticker')['Sector'].to_dict()
nameIndustryDict = clean_stockList.set_index('Ticker')['Industry'].to_dict()

materials = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Basic Materials_Sector_clean', type_converter_full2)
comms = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Communication Services_Sector_clean', type_converter_full2)
consCyclical = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Cyclical_Sector_clean', type_converter_full2)
consStaples = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Defensive_Sector_clean', type_converter_full2)
energy = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Energy_Sector_clean', type_converter_full2)
finance = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Financial Services_Sector_clean', type_converter_full2)
health = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Healthcare_Sector_clean', type_converter_full2)
ind = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Industrials_Sector_clean', type_converter_full2)
realEstate = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Real Estate_Sector_clean', type_converter_full2)
tech = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Technology_Sector_clean', type_converter_full2)
util = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Utilities_Sector_clean', type_converter_full2)

def cleanFCLduplicates(df):
    try:
        df_clean = df.drop_duplicates(subset='CIK', keep='first')
        if 'Market Cap' in df_clean.columns:
            df_clean = df_clean.drop(columns=['Market Cap']) #Removed after Market Cap tracked elsewhere.
        csv.simple_saveDF_to_csv(fr_iC_toSEC, df_clean, 'full_stockList_clean2', False)
    except Exception as err:
        print("cleanFCLdupes error")
        print(err)
# cleanFCLduplicates(full_cik_sectInd_list)

def makeSectorCSVs():
    try:
        full_list = clean_stockList
        allSectors = clean_stockList['Sector'].unique()
        for x in allSectors:
            mask = full_list['Sector'].isin([x])
            csv.simple_saveDF_to_csv(fr_iC_toSEC, full_list[mask], str(x) + '_Sector_clean', False)
    except Exception as err:
        print("make Sector CSV's error")
        print(err)
# makeSectorCSVs()

def EDGAR_query(ticker, header, tag: list=None) -> pd.DataFrame: #cik,
    try:
        cik = nameCikDict[ticker]
        url = ep["cf"] + 'CIK' + cik + '.json'
        response = requests.get(url, headers=header)
        print('EDGAR response: ')
        print(response)
        filingList = ['us-gaap','ifrs-full']
        company_data = pd.DataFrame()
        held_data = pd.DataFrame()
        tags = tag
        if len(tags) == 0:
            print('change it to len()')
            tags = list(response.json()['facts']['us-gaap'].keys())

        for x in filingList:
            # if tag == None:
            #     tags = list(response.json()['facts'][x].keys())
            #     # print('in query tags: ')
            #     # print(tags)
            #     # if tags.empty or (len(tags) <= 0):
            #     #     tags = list(response.json()['facts']['ifrs-full'].keys())
            # else:
            #     tags = tag

            for i in range(len(tags)):
                try:
                    tag = tags[i] 
                    units = list(response.json()['facts'][x][tag]['units'].keys())#[0] 
                    # print('units?')
                    # print(units)
                    # print('tags[i]')
                    # print(tag)
                    for y in units:
                        # print('y') #this is just money units, no worries
                        # print(y)
                        data = pd.json_normalize(response.json()['facts'][x][tag]['units'][y])#[units])
                        # print('data post json normal')
                        # print(data)
                        data['Tag'] = tag
                        # print('data post tag')
                        # print(data)
                        data['Units'] = y
                        # print('data post units')
                        # print(data)
                        data['Ticker'] = ticker
                        data['CIK'] = cik
                        # print('data at end before concat')
                        # print(data)
                        held_data = pd.concat([held_data, data], ignore_index = True)
                    company_data = pd.concat([company_data, held_data], ignore_index = True)
                    # print('company data')
                    # print(company_data)
                except Exception as err:
                    # print(str(tags[i]) + ' not found for ' + ticker + ' in ' + x)
                    # print('was it units,?')
                    # print(y)
                    pass
                    # print("Edgar query error: ")
                    # print(err)
                # finally:
                #     time.sleep(0.1)

            # if company_data.empty or str(type(company_data)) == "<class 'NoneType'>":
            #     for i in range(len(tags)):
            #         try:
            #             tag = tags[i] 
            #             units = list(response.json()['facts']['ifrs-full'][tag]['units'].keys())[0]
            #             data = pd.json_normalize(response.json()['facts']['ifrs-full'][tag]['units'][units])
            #             data['Tag'] = tag
            #             data['Units'] = units
            #             data['Ticker'] = ticker
            #             data['CIK'] = cik
            #             company_data = pd.concat([company_data, data], ignore_index = True)
            #         except Exception as err:
            #             print(str(tags[i]) + ' not found for ' + ticker + ' in ifrs-full.')
            #             # print("Edgar query error: ")
            #             # print(err)
            #         finally:
            #             time.sleep(0.1)

        return company_data
        # time.sleep(0.1)
    except Exception as err:
        print('edgar query super error')
        print(err)

        ### DONT BREAK IT
        # units = list(response.json()['facts'][x][tag]['units'].keys())[0] #
        #             # print('units?')
        #             # print(units)
        #             # print('tags[i]')
        #             # print(tag)
        #             # for y in units:
        #                 # print('y')
        #                 # print(y)
        #                 data = pd.json_normalize(response.json()['facts'][x][tag]['units'][units])
        #                 # print('data post json normal')
        #                 # print(data)
        #                 data['Tag'] = tag
        #                 # print('data post tag')
        #                 # print(data)
        #                 data['Units'] = units
        #                 # print('data post units')
        #                 # print(data)
        #                 data['Ticker'] = ticker
        #                 data['CIK'] = cik
        #                 # print('data at end before concat')
        #                 # print(data)
        #                 company_data = pd.concat([company_data, data], ignore_index = True)


### amazing resource to check what each element is: https://www.calcbench.com/element/WeightedAverageNumberOfSharesIssuedBasic 
### LUKE THIS WILL TEACH YOU MUCH I THINK: https://xbrl.us/guidance/specific-non-controlling-interest-elements/ 
#organizing data titles into variable lists
# altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
# cashOnHand = ['CashCashEquivalentsAndShortTermInvestments', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 
#                 'CashAndCashEquivalentsAtCarryingValue', 'CashEquivalentsAtCarryingValue', 
#                 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations']
netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 
                'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect', 'IncreaseDecreaseInCashAndCashEquivalents',
                'CashAndCashEquivalentsPeriodIncreaseDecrease','IncreaseDecreaseInCashAndCashEquivalentsBeforeEffectOfExchangeRateChanges'] #operCF + InvestCF + FinancingCF
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities','CashFlowsFromUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 
                    'NetCashProvidedByUsedInContinuingOperations', 'CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital','CashFlowsFromUsedInOperations','CashFlowsFromUsedInOperatingActivitiesContinuingOperations']
investingCashFlow = ['CashFlowsFromUsedInInvestingActivities','NetCashProvidedByUsedInInvestingActivities']
financingCashFlow = ['CashFlowsFromUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivities']

revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenueFromContractsWithCustomers', 'SalesRevenueNet', 'Revenues', 'RealEstateRevenueNet', 
            'Revenue','RevenueFromContractWithCustomerIncludingAssessedTax','GrossInvestmentIncomeOperating','RevenueFromRenderingOfTelecommunicationServices'] #banks?! GrossInvestmentIncomeOperating #totally not revenue how?!? 'RetainedEarnings',

netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic']
netIncomeNCI = ['ProfitLoss', 'ProfitLossAttributableToOwnersOfParent']

operatingIncome = ['OperatingIncomeLoss','ProfitLossFromOperatingActivities'] #IDK if REITS even have this filed with SEC. Finding it from SEC is hard right now.

taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense','FinanceCosts','InterestExpenseDebt','InterestAndDebtExpense','InterestIncomeExpenseNet','InterestIncomeExpenseNonoperatingNet',
                'FinancingInterestExpense','InterestPaidNet','InterestRevenueExpense']

incomeTaxPaid = ['IncomeTaxExpenseContinuingOperations'] #LUKE never used?

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
shareHolderEquity = ['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest','EquityAttributableToOwnersOfParent','PartnersCapital','Equity',
                        'MembersCapital']

exchangeRate = ['EffectOfExchangeRateChangesOnCashAndCashEquivalents'] #LUKE You'll want to know this is here eventually

capEx = ['PaymentsToAcquirePropertyPlantAndEquipment','PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities',
        'PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets','PaymentsToAcquireProductiveAssets',
        'PaymentsForCapitalImprovements','PaymentsToAcquireOtherPropertyPlantAndEquipment','PaymentsForProceedsFromProductiveAssets','PaymentsToDevelopRealEstateAssets',
        'PurchaseOfAvailableforsaleFinancialAssets','PaymentsToAcquireAndDevelopRealEstate'] 

totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends','DividendsCommonStock','DividendsCommonStockCash',
                            'DividendsPaidClassifiedAsFinancingActivities','DividendsPaid','DividendsPaidToEquityHoldersOfParentClassifiedAsFinancingActivities',
                            'PartnersCapitalAccountDistributions','DividendsPaidOrdinaryShares','DividendsPaidClassifiedAsOperatingActivities','PaymentsOfOrdinaryDividends'] 
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid','InvestmentCompanyDistributionToShareholdersPerShare',
                                        'DistributionMadeToLimitedPartnerDistributionsPaidPerUnit','DividendsPaidOrdinarySharesPerShare']
returnOfCapitalPerShare = ['InvestmentCompanyTaxReturnOfCapitalDistributionPerShare']
totalReturnOfCapital = [' InvestmentCompanyTaxReturnOfCapitalDistribution']

eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare','BasicEarningsLossPerShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic', 'EntityCommonStockSharesOutstanding','WeightedAverageShares', 'CommonStockSharesOutstanding',
                            'NumberOfSharesIssued']
dilutedSharesOutstanding = ['WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted']

gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes',
                    'GainsLossesOnSalesOfInvestmentRealEstate']
deprecAndAmor = ['DepreciationDepletionAndAmortization','Depreciation','DepreciationAmortizationAndAccretionNet','AmortizationOfIntangibleAssets',
                    'AdjustmentsForDepreciationAndAmortisationExpense','DeferredTaxLiabilityAsset','AdjustmentsForDepreciationExpense']
deprecAndAmor2 = ['AmortizationOfMortgageServicingRightsMSRs']
deprecAndAmor3 = ['DepreciationAndAmortization']
#notes from below for above
# missingDepreNAmor = ['MSFT', 'TSM', 'AVGO', 'ORCL', 'SAP', 'INTU', 'IBM', 'TXN']
#LUKE possible amoritization add: CapitalizedComputerSoftwareAmortization1 
#it looks like depre and amor isn't getting the full picture for the above stocks
#realty income is good tho. interesting.

netAssetValue = ['NetAssetValuePerShare'] 

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, longTermDebt3, longTermDebt4, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow, 
                investingCashFlow, financingCashFlow, exchangeRate, incomeTaxPaid, currentLiabilities, nonCurrentLiabilities, deprecAndAmor2, 
                deprecAndAmor3, shareHolderEquity, currentAssets, nonCurrentAssets, netAssetValue, dilutedSharesOutstanding, netIncomeNCI, 
                returnOfCapitalPerShare, totalReturnOfCapital ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'exchangeRate', 'longTermDebt3', 'longTermDebt4', 'incomeTaxPaid', 'currentLiabilities','nonCurrentLiabilities',
                'deprecAndAmor2', 'deprecAndAmor3', 'shareHolderEquity', 'currentAssets','nonCurrentAssets', 'netAssetValue', 'dilutedSharesOutstanding', 'netIncomeNCI', 
                'returnOfCapitalPerShare', 'totalReturnOfCapital']
# removedFromUltList = [netCashFlow, cashOnHand, altVariables]

ultimateTagsList = [item for sublist in ultimateList for item in sublist]

#Saves MASTER CSV containing data most pertinent to calculations.
def write_Master_csv_from_EDGAR(ticker, tagList, year, version): # cik,
    try:
        company_data = EDGAR_query(ticker, header, tagList)#cik,
        time.sleep(0.1)
    except Exception as err:
        print('write to csv from edgar error:')
        print(err)                
    finally:
        csv.simple_saveDF_to_csv(stock_data, company_data, ticker + '_Master_' + year + '_V' + version, False)

def harvestMasterCSVs(sectorTarget): #edit version as necessary!
    try:
        df_full = sectorTarget
        tickerList = df_full['Ticker']
        # cikList = df_full['CIK']
    
        for i in range(len(tickerList)):
            write_Master_csv_from_EDGAR(tickerList[i], ultimateTagsList, '2024', '2')
        
        #full_cik_sectInd_list
        # return null

    except Exception as err:
        print("harvestMasters error: ")
        print(err)

#Begin data cleaning process
def get_Only_10k_info(df):
    try:
        filtered_data = pd.DataFrame()
        # returned_data = pd.concat([returned_data, held_data], ignore_index = True) #loop thru the options and just add it all together!
        formList = ['10-K','20-F','40-F','6-K'] #

        # filtered_data = df[df['form'].str.contains('10-K') == True]
        filtered_data = df[df['form'].isin(formList) == True] #.str.contains
        # filtered_data = pd.concat([filtered_data, filtered_data1], ignore_index = True)

        # for x in formList:
        #     filtered_data1 = df[df['form'].isin(formList) == True] #.str.contains
        #     filtered_data = pd.concat([filtered_data, filtered_data1], ignore_index = True)
            # print('filtered data')
            # print(filtered_data)
        # filtered_data1 = df[df['form'].str.contains('20-F') == True] #ADDED FOR ex-US stocks
        # # print(filtered_data1)
        # filtered_data2 = df[df['form'].str.contains('6-K') == True] #ADDED FOR ex-US stocks
    except Exception as err:
        print("10k filter error")
        print(err)
    finally:
        # if str(type(filtered_data)) == "<class 'NoneType'>" or filtered_data.empty:
        #     if str(type(filtered_data1)) == "<class 'NoneType'>" or filtered_data1.empty:
        #         return filtered_data2
        #     else:
        #         return filtered_data1
        # else:
        #     return filtered_data
        return filtered_data

def dropAllExceptFYRecords(df):
    try:
        testdf = df
        # print('testdf')
        # print(testdf)
        # print('tag then df')
        # print(df['Tag'])
        # print(df)
        # returned_data = pd.DataFrame()
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
        # print('reversed')
        # for x in revCD:
        #     print(x)
        # print('forward')
        # for x in countdown:
        #     print(x)
        # print(revCD)
        # halfStarts = ['-01-','-06-','-07-']
        # halfEnds = ['-06-','-07-','-12-']
        #First we check for the full year reportings, includes start dates
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
            # print('x')
            # print(x)
            # print('df within the damn for????')
            # print(df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-11-')==True)])
            held_data1 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains(x)==True)]
            # print('held at beg of for')
            # print(held_data1)
            if held_data1.empty:
                # print('held empty')
                continue
            else:
                lastKnownLog = x
                held_data2 = df[(df['start'].str.contains(lastKnownLog)==True) & (df['end'].str.contains('-12-')==True)]
                
                # print('held2 in else')
                # print(held_data2)
        # print('pine be empty')
                held3 = pd.merge(held_data1, held_data2, on=['Ticker','CIK','Units','fp','fy','form','frame','filed','Tag','accn'], how='outer')
                held3['val'] = held3['val_x'] + held3['val_y']
                held3['start'] = held3['start_x']
                held3['end'] = held3['end_y']
                held3 = held3.drop(columns=['val_x','val_y','start_x','start_y','end_x','end_y'])
                held3 = held3.dropna(subset=['val'])#,'start'])
                # print('held3')
                # print(held3)
                returned_data = pd.concat([returned_data, held3], ignore_index = True)

        #So you've gone x-y all numbers, and 1-x, x-12 and still nervous?
        #1-2, 2-3, 3-4...
        #for x in 1-11, mask for x-(x+1)
        # held_data123 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-02-')==True)]
        #dummy df['columnONE'] = that
        #dumm df['columnTWO'] = mask for (x+1)-(x+2)
        #held4['val'] = dummy1 + dumm2
        #concat to returned data

        
        # print('pre check if empty')
        # print(returned_data)
        

        # No start dates and some monthly reporters make things weird, empty here.
        # So just pass the whole data set to the sorter and duplicate trimmer, let them deal with it
        if returned_data.empty:
            #if said month string is 12, year is end.str.year, if it's 01, it's year -1 ok ok
            # listMax = df.end.str[5:7]
            # # print('all the end months')
            # # print(listMax.unique())
            # tarMax = str(listMax.max())
            # held_data = df[df['end'].str.contains(tarMax)==True] #held_data
            # held_data2 = df[df['end'].str.contains('-01-')==True]
            # returned_data = pd.concat([returned_data, held_data], ignore_index = True)
            # returned_data = pd.concat([returned_data, held_data2], ignore_index = True)

            # yeartest = df.end.str[:4]
            # print(yeartest)
            # held_data = df[df['end'].str.contains('2014')==True]
            # print(held_data)
            returned_data = df
           
        # print('post check if empty')
        # print(returned_data)
        # print(returned_data)
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
        # filtered_data = pd.DataFrame()
        # print('pre drop dupes')
        # print(df)
        filtered_data = df
        endYear = []
        endMonth = []
        startYear = []
        
        for x in filtered_data['end']: #Prep endyear-related for year calc's
            # print(type(x))
            #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
            # print('in end processor')
            endYear.append(int(x[:4]))
            endMonth.append(int(x[5:7]))
            # print(filtered_data)
        filtered_data['endYear'] = endYear
        filtered_data['endMonth'] = endMonth
        # print('end month col')
        # print(filtered_data['endMonth'])
        # print(type(filtered_data['endMonth'].loc[0]))
        yearMinusOne = list(filtered_data['endYear'] - 1)
        yearMinusOne = [str(x) for x in yearMinusOne]
        filtered_data['yearMinusOne'] = yearMinusOne
        # print('end problem?')
        # print(endYear)
        # print(endMonth)
        # print('pre start processing')
        # print(filtered_data)
        if filtered_data['start'].isnull().all(): #Did we get a dataset that doesn't include starts?
            # print(type(filtered_data['start'].loc[0]))
            # print(filtered_data['start'].loc[0])
            # filtered_data['start'] = filtered_data['start'].infer_objects(copy=False).fillna(0) #.replace(np.NaN,0) #this one
            # print('start is bad')
            # print(filtered_data['endMonth'])
            
            filtered_data['startYear'] = 0#filtered_data['start']#'0000-00-00' #this one
            # endMonthCheck = [9,10,11,12]
            filtered_data['year7'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 5)
            filtered_data['year8'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 6)
            filtered_data['year9'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 7)
            filtered_data['year10'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 8)
            filtered_data['year11'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 9)  #, other=filtered_data['yearMinusOne'])
            filtered_data['year12'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 10)
            filtered_data['year13'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 11)
            filtered_data['year14'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 12)


            filtered_data['year'] = filtered_data['year8'].fillna(filtered_data['year9'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year7'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year10'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year11'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year12'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year13'])#.infer_objects(copy=False)
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
            # print('start null')
            # print(filtered_data)

        else: #Otherwise fill necessary columns for year calc's
            # print('start filled')
            # print('we hit else anyway?')
            for x in filtered_data['start']:
                # print('start?!?')
                # print(filtered_data.where(filtered_data.isnull()))
                # print(x)
                # print(type(x))
                #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
                if type(x) == float:
                    startYear.append(0)
                else:
                    startYear.append(int(x[:4]))
                # print(filtered_data)
            filtered_data['startYear'] = startYear
            # print('start problem?')
            # print(startYear)
            # print(filtered_data['startYear'])
            ### TRY LEAVING START EMPTY. EASIER TO CHEKC. LESS ERRORS. MUCH CODE. WOW
        # if filtered_data['start'].loc[0] == 0: #In the case of those null start datasets this one
            # filtered_data['year'] = filtered_data.end.str[:4] #this one
            # print('wtf start is zero')
            # print(filtered_data['year'])
        # else: #otherwise proceed as normal
            # print('mean was not zero tyvm')
            filtered_data['yearDiff'] = (filtered_data['endYear'] - filtered_data['startYear']).where((filtered_data['endYear'] > filtered_data['startYear']))
            filtered_data['yearDiff2'] = (filtered_data['endYear'] - filtered_data['startYear']).where((filtered_data['endYear'] == filtered_data['startYear']))
            # wrongOrder = pd.Series([3.0])
            # filtered_data['yearDiff3'] = (wrongOrder).where((filtered_data['endYear'] < filtered_data['startYear']))
            filtered_data['yearDiff'] = filtered_data['yearDiff'].fillna(filtered_data['yearDiff2'])
            # filtered_data['yearDiff'] = filtered_data['yearDiff'].fillna(filtered_data['yearDiff3'])
            filtered_data['yearDiff'] = filtered_data['yearDiff'].fillna(3.0)
            filtered_data = filtered_data.drop('yearDiff2',axis=1)
            # filtered_data = filtered_data.drop('yearDiff3',axis=1)
            # print(filtered_data)
            # filtered_data['endMonth'] = endMonth
            # print('pre fitler')
            # print(filtered_data)
            # print(filtered_data.shape)

            
            # print('post fitler')
            # print(filtered_data)
            # print(filtered_data.shape)

            ###Case: yearDiff == 3: drop that row because report given to sec is just wrong
            filtered_data = filtered_data[filtered_data['yearDiff'] < 3]
            
            ###Case: yearDiff == 2: year = (end - 1)
            # yearMinusOne = list(filtered_data['endYear'] - 1)
            # yearMinusOne = [str(x) for x in yearMinusOne]
            # filtered_data['yearMinusOne'] = yearMinusOne
            filtered_data['year1'] = filtered_data['yearMinusOne'].where(filtered_data['yearDiff'] == 2)
            # print('just 2s')
            # print(filtered_data)

            ###Case: yearDiff == 0: start=year
            startYearStrings = list(filtered_data['startYear'])
            startYearStrings = [str(x) for x in startYearStrings]
            filtered_data['startYear'] = startYearStrings
            filtered_data['year2'] = filtered_data['startYear'].where(filtered_data['yearDiff'] == 0)
            # print('just 2s and 0s')
            # print(filtered_data)

            ###Case: year diff == 1: if end month >= 6, year=end; else year = start
            endYearStrings = list(filtered_data['endYear'])
            endYearStrings = [str(x) for x in endYearStrings]
            filtered_data['endYear'] = endYearStrings
            filtered_data['year3'] = filtered_data['endYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] >= 5)) #changed here from 6
            filtered_data['year4'] = filtered_data['startYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] < 5))
            # print('all three applied')
            # print(filtered_data)
            # filtered_data['year'] = filtered_data['year1'] + filtered_data['year2'] + filtered_data['year3']
            filtered_data['year'] = filtered_data['year1'].fillna(filtered_data['year2'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year3'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year4'])#.infer_objects(copy=False)
            #.replace(np.NaN,filtered_data['year4'])
            filtered_data = filtered_data.drop('yearDiff',axis=1)
            # print('post yeardiff drops')
            # print(filtered_data)
            # filtered_data = filtered_data.drop('endMonth',axis=1)
            # print('post endmonth drops')
            # print(filtered_data)
            # filtered_data = filtered_data.drop('yearMinusOne',axis=1)
            filtered_data = filtered_data.drop('year1',axis=1)
            filtered_data = filtered_data.drop('year2',axis=1)
            filtered_data = filtered_data.drop('year3',axis=1)
            filtered_data = filtered_data.drop('year4',axis=1)

        # filtered_data = filtered_data.drop(['endYear','startYear','yearDiff','endMonth','yearMinusOne'],axis=1)
        # print('pre pops')
        # print(filtered_data)
        filtered_data = filtered_data.drop('endYear',axis=1)
        # print('post end drops')
        # print(filtered_data)
        filtered_data = filtered_data.drop('startYear',axis=1)
        filtered_data = filtered_data.drop('yearMinusOne',axis=1)
        filtered_data = filtered_data.drop('endMonth',axis=1)
        # print('post start drops')
        # print(filtered_data)
        
            
        

        
        # filtered_data['year3']
        # print('post year minus one drops')
        # print('good results?')
        # print(filtered_data)

        filtered_data = filtered_data.drop_duplicates(subset=['year'],keep='last')#val #end
        # print('seper')
        # print(filtered_data)
        
    except Exception as err:
        print("drop duplicates error")
        print(err)
    finally:
        return filtered_data
        # #####
        # if filtered_data.start.str[5:7].eq('02').all() & filtered_data.end.str[5:7].eq('01').all(): #starts feb, ends jan, hopefully one year later
        #     filtered_data['year'] = filtered_data.start.str[:4]
        # else:
        #     filtered_data['compare'] = (filtered_data.end.str[5:7] == filtered_data.start.str[5:7]) #Where the months are the same
        #     # print(filtered_data['compare'])

        #     #2022-07 -> 2023-06 == end is year
        #     #2022-01 -> 2022-12 == start or end is year
        #     #2022-01 -> 2023-01 == start year is year
        #     filtered_data['year'] = filtered_data.start.str[:4].where(filtered_data['compare'] == True, other=filtered_data.end.str[:4])



        #     # filtered_data['intstart'] = filtered_data.start.str[5:7].astype(int)
        #     # filtered_data['intend'] = filtered_data.end.str[5:7].astype(int)
        #     # print(filtered_data['intstart'])


        #     # if abs(filtered_data.start.str[5:7].astype(int)-filtered_data.end.str[5:7].astype(int)) == 1:
        #     #     if abs(filtered_data.start.str[:4].astype(int)-filtered_data.end.str[:4].astype(int)) == 1:
        #     #         if filtered_data.start.str[5:7].astype(int) < 3:
        #     #             filtered_data['year'] = filtered_data.start.str[:4]

        #     # filtered_data = filtered_data.drop(columns=['compare']) ##WHY DIDN'T DROP WORK?! guh
        #     filtered_data = filtered_data.pop('compare')
        #     #####

def dropUselessColumns(df):
    try:
        returned_data = df.drop(['start','end','accn','fy','fp','form','filed','frame','Tag'],axis=1) #start, end added  ,'compare'

        return returned_data
    except Exception as err:
        print("drop useless columns error")
        print(err)

# Returns organized data pertaining to the tag(s) provided in form of DF
def consolidateSingleAttribute(ticker, year, version, tagList, indexFlag):
    try:
        # print('taglist')
        # print(tagList)
        #get csv to df from params
        filtered_data = csv.simple_get_df_from_csv(stock_data, ticker + '_Master_' + year + '_V' + version, indexFlag)
        # print(filtered_data)
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            
            held_data = filtered_data[filtered_data['Tag'].eq(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
            # print(x)
            # if 'PerShare' in x:
            #     print('in consolidate')
            #     print(returned_data)
        # print(returned_data['Tag'].unique())
        # print(returned_data)
        returned_data = get_Only_10k_info(returned_data)
        # print('10k data')
        # print(returned_data)
        # print(returned_data.shape)
        
        # print('pre drop fy records')
        # print(returned_data)#.to_string())
        # print(returned_data.shape)
        # print(returned_data['Tag'].unique())
        # print(returned_data['start'].min())
        # print(returned_data['end'].min())
        
        returned_data = dropAllExceptFYRecords(returned_data) #was held data
        # print('post drop fy records pre order')
        # print(returned_data)#.to_string())
        # print(returned_data.shape)
        returned_data = orderAttributeDF(returned_data) #moved from above fy records. so we gather 10k, all fy, then order then drop dupes
        # print('post order pre drop  dupes')
        # print(returned_data.to_string())
        # print(returned_data.shape)

        returned_data = dropDuplicatesInDF(returned_data) #added after filtering for FY only
        # print('post drop  dupes')
        # print(returned_data)
        # print(returned_data.shape)


        returned_data = dropUselessColumns(returned_data)
        
        # print('consolidate all drops done')
        # print(returned_data)

        # csv.simple_saveDF_to_csv('./sec_related/stocks/',held_data, ticker+'_'+'dataFilter'+'_V'+outputVersion,False)
        # csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_' + year + '_' + outputName,False)
        return returned_data

    except Exception as err:
        print("consolidate single attr error: ")
        print(err)

def grManualCalc(df_col):
    try:
        # origList = []
        origList = df_col.tolist()
        # print(origList)
        # print(len(origList))
        growthList = []
        growthList.append(np.NaN)
        for x in range(len(origList)-1):
            diff = abs((origList[x+1])-origList[x])
            if origList[x] > origList[x+1]:
                diff = diff * -1
            # print('x+1')
            # print(origList[x+1])
            # print('x')
            # print(origList[x])
            if abs(origList[x]) == 0:# and abs(origList[x+1]) == 0:
                change = np.NaN
            # elif abs(origList[x]) == 0 and abs(origList[x+1]) != 0:
            #     placeHolder = 0.001
            #     diff = abs((origList[x+1])-placeHolder)
            #     change = diff / abs(placeHolder) * 100
            else:
                change = diff / abs(origList[x]) * 100
            # if change == 'inf':
            #     print('inf tripped')
            #     change = np.NaN
            # print(change)
            # print(type(change))
            growthList.append(change)
            # print(change)
            # print('x')
            # print(origList[x])
            # print('x-1')
            # print(origList[x-1])

        # print(growthList)
        # print(len(growthList))
        # print(growthList)
        return growthList

    except Exception as err:
        print("grManualCalc error: ")
        print(err)

def cleanUnits(df): 
    #Add to EL below as conflicting currencies are found. Manually add them below in for loop. woof. You could just do an if in statement but the specificity must match the conversion rate
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
        # print('df')
        # print(df)

        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'revenue'})
        # df_col_added = df.rename(columns={'val':'revenue'})
        if df_col_added.empty:
            return df_col_added
        else:
            # if df_col_added['revenue'].empty:
            #     df_col_added['revenueGrowthRate'] = np.NaN
            # else:
            # origRev = df_col_added['revenue'].tolist()
            # unitsFrom = df_col_added['Units'].tolist()
            # datesFrom = df_col_added['year'].tolist()
            # # unitsTo
            # conRev = []
            # # print(len(origRev))
            # # print(len(unitsFrom))
            # for i in range(len(origRev)):
            #     conRev.append(curConvert.convert(origRev[i], unitsFrom[i], 'USD', date=date(int(datesFrom[i]),12,31)))
            # df_col_added['newRev'] = conRev
            #     print(x + ', ' + y)
            # df_col_added['convRev'] = curConvert.convert(df_col_added['revenue'], df_col_added['Units'], 'USD')
            # print('did it convert?')
            # print(df_col_added)

            growthCol = grManualCalc(df_col_added['revenue'])
            df_col_added['revenueGrowthRate'] = growthCol#df_col_added['revenue'].pct_change()*100
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])
        # print('df col added')
        # print(df_col_added)
    # try:#I like coding this part. It felt clean. Leaving it for future reference, but it's best handled elsewhere/in other ways.
    #     df_col_added = pd.DataFrame()
    #     if df.empty:
    #         df_col_added['revenue'] = np.NaN
    #         df_col_added['revenueGrowthRate'] = np.NaN
    #         df_col_added['year'] = np.NaN
    #         df_col_added['start'] = np.NaN # df_col_added['year'].replace(np.NaN, np.NaN)
    #         df_col_added['end'] = np.NaN # df_col_added['year'].replace(np.NaN, np.NaN)
    #         df_col_added['Ticker'] = np.NaN # df_col_added['year'].replace(np.NaN, np.NaN)
    #         df_col_added['CIK'] = np.NaN # df_col_added['year'].replace(np.NaN, np.NaN)
    #         df_col_added['Units'] = np.NaN # df_col_added['year'].replace(np.NaN, np.NaN)
    #     else:
    #         df_col_added = df.rename(columns={'val':'revenue'})
    #         df_col_added['revenueGrowthRate'] = df_col_added['revenue'].pct_change()*100
    #         df_col_added['year'] = df_col_added.end.str[:4]
       
            

    except Exception as err:
        print("cleanRevenue error: ")
        print(err)
        # print(df_col_added)
    finally:
        return df_col_added

def cleanNetIncome(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netIncome'})
        # df_col_added = df.rename(columns={'val':'netIncome'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netIncome'])
            df_col_added['netIncomeGrowthRate'] = growthCol#df_col_added['netIncome'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            

    except Exception as err:
        print("cleanNetIncome error: ")
        print(err)
    finally:
        return df_col_added

def cleanNetIncomeNCI(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netIncomeNCI'})
        # df_col_added = df.rename(columns={'val':'netIncome'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netIncomeNCI'])
            df_col_added['netIncomeNCIGrowthRate'] = growthCol#df_col_added['netIncome'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            

    except Exception as err:
        print("cleanNetIncomeNCI error: ")
        print(err)
    finally:
        return df_col_added

def cleanOperatingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'operatingCashFlow'})
        # df_col_added = df.rename(columns={'val':'operatingCashFlow'})
        # if df_col_added['operatingCashFlow'].isnull().any():
        #     df_col_added['operatingCashFlow'] = df_col_added['operatingCashFlow'].ffill()
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['operatingCashFlow'])
            df_col_added['operatingCashFlowGrowthRate'] = growthCol#df_col_added['operatingCashFlow'].pct_change()*100
            # df_col_added['operatingCashFlowGrowthRate'] = df_col_added['operatingCashFlowGrowthRate'].replace(np.nan,0) #Replace NaN with zero? Uncertain.
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean oper cash flow error: ")
        print(err)

def cleanInvestingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'investingCashFlow'})
        # df_col_added = df.rename(columns={'val':'investingCashFlow'})
        # if df_col_added['investingCashFlow'].isnull().any():
        #     df_col_added['investingCashFlow'] = df_col_added['investingCashFlow'].ffill()
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['investingCashFlow'])
            df_col_added['investingCashFlowGrowthRate'] = growthCol#df_col_added['investingCashFlow'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean investing cash flow error: ")
        print(err)

def cleanFinancingCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'financingCashFlow'})
        # df_col_added = df.rename(columns={'val':'financingCashFlow'})
        # if df_col_added['financingCashFlow'].isnull().any():
        #     df_col_added['financingCashFlow'] = df_col_added['financingCashFlow'].ffill()
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['financingCashFlow'])
            df_col_added['financingCashFlowGrowthRate'] = growthCol#df_col_added['financingCashFlow'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean financingCashFlow error: ")
        print(err)

def cleanNetCashFlow(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'netCashFlow'})
        # df_col_added = df.rename(columns={'val':'netCashFlow'})
        # if df_col_added['netCashFlowe'].empty:
        #     df_col_added['netCashFlowGrowthRate'] = np.NaN
        # else:
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netCashFlow'])
            df_col_added['netCashFlowGrowthRate'] = growthCol#df_col_added['netCashFlow'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean netCashFlow error: ")
        print(err)

def cleanCapEx(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'capEx'})
        # df_col_added = df.rename(columns={'val':'capEx'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['capEx'])
            df_col_added['capExGrowthRate'] = growthCol #df_col_added['operatingIncome'].pct_change()*100
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end']) 

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
        # returned_data = targetdf

        # if df_col_added.empty:
        #     return df_col_added
        # else:
        #     growthCol = grManualCalc(df_col_added['eps'])
        #     df_col_added['epsGrowthRate'] = growthCol#df_col_added['eps'].pct_change()*100
        #     # df_col_added['year'] = df_col_added.end.str[:4]

        #     # df_col_added = df_col_added.drop(columns=['start','end']) 

        #     return df_col_added

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
        # print(df_col_added)

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
        df_col_added['fcfGrowthRate'] = growthCol#df_col_added['fcf'].pct_change(fill_method=None)*100

        return df_col_added

        # ERROR DETAILS
        ### When empty we get this error. see: O ;; 413, 431
        #         /home/user1/masterSword/MainFrame/mainframe/investor_center/workbook1.py:414: FutureWarning: The default fill_method='pad' in Series.pct_change is deprecated and will be removed in a future version. Either fill in any non-leading NA values prior to calling pct_change or specify 'fill_method=None' to not fill NA values.
        #   df_col_added['fcfGrowthRate'] = df_col_added['fcf'].pct_change()*100
        # /home/user1/masterSword/MainFrame/mainframe/investor_center/workbook1.py:427: FutureWarning: The default fill_method='pad' in Series.pct_change is deprecated and will be removed in a future version. Either fill in any non-leading NA values prior to calling pct_change or specify 'fill_method=None' to not fill NA values.
        #   df_col_added['fcfMarginGrowthRate'] = df_col_added['fcfMargin'].pct_change()*100

    except Exception as err:
        print("clean fcf error: ")
        print(err)

def cleanfcfMargin(df): #Requires a pre-built DF including fcf!!!
    try:
        df_col_added = df
        df_col_added['fcfMargin'] = df_col_added['fcf'] / df_col_added['revenue'] * 100
        growthCol = grManualCalc(df_col_added['fcfMargin'])
        df_col_added['fcfMarginGrowthRate'] = growthCol#df_col_added['fcfMargin'].pct_change(fill_method=None)*100

        return df_col_added

    except Exception as err:
        print("clean fcfMargin error: ")
        print(err)

def cleanOperatingIncome(df):
    try:
        # print('df')
        # print(df)
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'operatingIncome'})
        # df_col_added = df.rename(columns={'val':'operatingIncome'})
        # print('renamed df')
        # print(df_col_added)
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['operatingIncome'])
            df_col_added['operatingIncomeGrowthRate'] = growthCol #df_col_added['operatingIncome'].pct_change()*100
            # print('growth col added df')
            # print(df_col_added)

        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanTaxRate(df):
    try:
        # df_col_added = cleanUnits(df)
        # df_col_added = df_col_added.rename(columns={'val':'taxRate'})
        df_col_added = df.rename(columns={'val':'taxRate'})
        # df_col_added['taxRateGrowthRate'] = df_col_added['operatingIncome'].pct_change(periods=1)*100
        # df_col_added['year'] = df_col_added.end.str[:4]

        df_col_added = df_col_added.drop(columns=['Units']) #'start','end',

        return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanDebt(short, long1, long2, long3, long4): 
    try:
        #take short, long1, long2 debt, create year column, reproduce df with just year and debt column 
        # short['year'] = short.end.str[:4]
        # long1['year'] = long1.end.str[:4]
        # long2['year'] = long2.end.str[:4]
        # long3['year'] = long3.end.str[:4]
        # long4['year'] = long4.end.str[:4]

        # short = short.drop(columns=['start','end']) 
        # long1 = long1.drop(columns=['start','end']) 
        # long2 = long2.drop(columns=['start','end']) 
        # long3 = long3.drop(columns=['start','end']) 
        # long4 = long4.drop(columns=['start','end']) 
        # print('printing short')
        # print(short)
        # print('printing long1')
        # print(long1)
        # print('printing long2')
        # print(long2)
        # print('printing long3')
        # print(long3)
        # print('printing long4')
        # print(long4)
        short = cleanUnits(short)
        long1 = cleanUnits(long1)
        long2 = cleanUnits(long2)
        long3 = cleanUnits(long3)
        long4 = cleanUnits(long4)
        # df_col_added = df_col_added.rename(columns={'val':'operatingIncome'})

        shortNlong1 = pd.merge(short, long1, on=['year','Ticker','CIK','Units'], how='outer')
        shortNlong1['val_x'] = shortNlong1['val_x'].fillna(0)
        shortNlong1['val_y'] = shortNlong1['val_y'].fillna(0)
        shortNlong1['subTotalDebt'] = shortNlong1['val_x'] + shortNlong1['val_y']
        shortNlong1 = shortNlong1.drop(['val_x','val_y'],axis=1)

        # print('shortnlong1')
        # print(shortNlong1)
        
        plusLong2 = pd.merge(shortNlong1, long2, on=['year','Ticker','CIK','Units'], how='outer')
        # print('pluslong2')
        # print(plusLong2)
        plusLong2['val'] = plusLong2['val'].fillna(0)
        plusLong2['subTotalDebt'] = plusLong2['subTotalDebt'].fillna(0) 
        # print('post fill na pluslong2')
        # print(plusLong2)
        plusLong2['TotalDebt'] = plusLong2['subTotalDebt'] + plusLong2['val']
        # print('total debt pluslong2')
        # print(plusLong2)
        plusLong2 = plusLong2.drop(['subTotalDebt','val'],axis=1)

        # print('pluslong2 dropped columns')
        # print(plusLong2)

        plusLong3 = pd.merge(plusLong2, long3, on=['year','Ticker','CIK','Units'], how='outer')
        plusLong3['val'] = plusLong3['val'].fillna(0)
        plusLong3['TotalDebt'] = plusLong3['TotalDebt'].fillna(0)
        plusLong3['TotalDebt'] = plusLong3['TotalDebt'] + plusLong3['val']
        plusLong3 = plusLong3.drop(['val'],axis=1)

        # print('pluslong3')
        # print(plusLong3)

        plusLong4 = pd.merge(plusLong3, long4, on=['year','Ticker','CIK','Units'], how='outer')
        plusLong4['val'] = plusLong4['val'].fillna(0)
        plusLong4['TotalDebt'] = plusLong4['TotalDebt'].fillna(0)
        plusLong4['TotalDebt'] = plusLong4['TotalDebt'] + plusLong4['val']
        plusLong4 = plusLong4.drop(['val'],axis=1)

        # print('pluslong4')
        # print(plusLong4)

        return plusLong4

    except Exception as err:
        print("clean Debt error: ")
        print(err)

def cleanAssets(nonCurrent, current):
    try:
        # nonCurrent['year'] = nonCurrent.end.str[:4]
        # current['year'] = current.end.str[:4]

        # nonCurrent = nonCurrent.drop(columns=['start','end'])
        # current = current.drop(columns=['start','end'])

        nonCurrent = cleanUnits(nonCurrent)
        current = cleanUnits(current)
        # df_col_added = df_col_added.rename(columns={'val':'operatingIncome'})

        anl = pd.merge(nonCurrent, current, on=['year','Ticker','CIK','Units'], how='outer')
        anl['val'] = anl['val_x'] + anl['val_y']
        anl = anl.drop(['val_x','val_y'],axis=1) 
        return anl

    except Exception as err:
        print("clean assets error: ")
        print(err)

def cleanLiabilities(nonCurrent, current):
    try:
        # nonCurrent['year'] = nonCurrent.end.str[:4]
        # current['year'] = current.end.str[:4]

        # nonCurrent = nonCurrent.drop(columns=['start','end'])
        # current = current.drop(columns=['start','end'])

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
        #take assets and liabilities and get total equity from them
        # assets['year'] = assets.end.str[:4]
        # liabilities['year'] = liabilities.end.str[:4]

        # assets = assets.drop(columns=['start','end'])
        # liabilities = liabilities.drop(columns=['start','end'])

        # print('weird reqport??E?')
        # print(reportedEquity)
        if assets.empty:
            assets = cleanAssets(ncA, cuA)
        else:
            # print('clean equity assets not empty else')
            # print(assets)
            assets = cleanUnits(assets)

        # print('clean equity assets not empty else post clean')
        # print(assets)
        

        if liabilities.empty:
            liabilities = cleanLiabilities(ncL, cuL)
        else:
            # print('clean equity lias not empty else pre clean')
            # print(liabilities)
            liabilities = cleanUnits(liabilities)

        reportedEquity = cleanUnits(reportedEquity)
        
        # print('clean equity lias not empty else post clean')
        # print(liabilities)
        # print('liabilities?!?')
        # print(liabilities)
        # print('assets?')
        # print(assets)
        #Because Equity is important to calculations, we need to verify non-reported values as being a lower approximation of the mean of all liabilities over time.
        # LUKE RETHINK THIS...maybe
        assAndLies = pd.merge(assets, liabilities, on=['year','Ticker','CIK','Units'], how='outer')
        
        # print('post merge ass and lias')
        # print(assAndLies)

        assAndLies['assets'] = assAndLies['val_x']
        assetsMean = assAndLies['assets'].mean() #/ ((len(assAndLies['assets'])/2)+1)
        assAndLies['assets'] = assAndLies['assets'].fillna(assetsMean)
        assAndLies['liabilities'] = assAndLies['val_y']
        liaMean = assAndLies['liabilities'].mean() #/ ((len(assAndLies['liabilities'])/2)+1)
        assAndLies['liabilities'] = assAndLies['liabilities'].fillna(liaMean)
        assAndLies = assAndLies.drop(['val_x','val_y'],axis=1)

        # print('post fill and drop ass and lias')
        # print(assAndLies)

        assAndLies = pd.merge(assAndLies, reportedEquity, on=['Units','year','Ticker','CIK'], how='outer')
        # print('post merge ass and lias and total equity')
        # print(assAndLies)

        assAndLies['ReportedTotalEquity'] = assAndLies['val']
        assAndLies = assAndLies.drop(['val'],axis=1)

        assAndLies['TotalEquity'] = assAndLies['assets']-assAndLies['liabilities']
        # assAndLies['ReportedTotalEquity'] = reportedEquity
        # print('TEquity checker')
        # print(assAndLies)

        return assAndLies

    except Exception as err:
        print("clean totalEquity error: ")
        print(err)

def cleanDeprNAmor(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'depreNAmor'})
        # df_col_added = df.rename(columns={'val':'depreNAmor'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added
    except Exception as err:
        print("clean deprNAmor error: ")
        print(err)

def cleanDeprNAmor2(df1,df2):
    try:
        df_col_added = cleanUnits(df1)
        df_col_added = df_col_added.rename(columns={'val':'depreNAmor1'})
        # df_col_added = df1.rename(columns={'val':'depreNAmor1'})
        # df_col_added['year'] = df_col_added.end.str[:4]
        # df_col_added = df_col_added.drop(columns=['start','end'])

        df2 = cleanUnits(df2)
        df2 = df2.rename(columns={'val':'depreNAmor2'})
        # df2 = df2.rename(columns={'val':'depreNAmor2'})
        # df2['year'] = df2.end.str[:4]
        # df2 = df2.drop(columns=['start','end'])


        df_col_added2 = pd.merge(df_col_added, df2, on=['year','Ticker','CIK','Units'], how='outer')
        df_col_added2['depreNAmor'] = df_col_added2['depreNAmor1'].replace(np.NaN, 0) + df_col_added2['depreNAmor2'].replace(np.NaN, 0)
        df_col_added2 = df_col_added2.drop(columns=['depreNAmor1','depreNAmor2'])
        # print(df_col_added2)

        return df_col_added2 
    except Exception as err:
        print("clean deprNAmor2 error: ")
        print(err)

def cleanGainSaleProp(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'gainSaleProp'})
        # df_col_added = df.rename(columns={'val':'gainSaleProp'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added
    except Exception as err:
        print("clean gainSaleProp error: ")
        print(err)

def cleanInterestPaid(df):
    try:
        df_col_added = cleanUnits(df)
        df_col_added = df_col_added.rename(columns={'val':'interestPaid'})
        # df_col_added = df.rename(columns={'val':'interestPaid'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added

    except Exception as err:
        print("clean interestPaid error: ")
        print(err)

#ASML case study: shares are working. per share works, but throws off data as nulls are filled because total paid loads fine, but then we try to fill nulls both ways and make a bunch of nulls.
def cleanDividends(total, perShare, shares, dilutedShares, rocps, roctotal): 

    try:
        # shares['year'] = shares.end.str[:4]
        shares = shares.rename(columns={'val':'shares'})
        shares = shares.drop(columns=['Units'])
        # print('what about shares?')
        # print(shares)
        # print('before dilutedShares is scrubbed')
        # print(dilutedShares)
        dilutedShares = dilutedShares.rename(columns={'val':'dilutedShares'})
        dilutedShares = dilutedShares.drop(columns=['Units'])
        # print('what about diluted shares?')
        # print(dilutedShares)

        # while shares['shares'].min() < 1000000:
        #     print('shares less than mil')
        #     # print(shares['shares']/1000000)
        #     shares['shares'] = (shares['shares'] * 1000).where(shares['shares'] < 1000000)
        # while dilutedShares['dilutedShares'].min() < 1000000:
        #     print('diluted shares less than mil')
        #     dilutedShares['dilutedShares'] = (dilutedShares['dilutedShares'] * 1000).where(dilutedShares['dilutedShares'] < 1000000)
        # print('do we have any diluted share?')
        # print(dilutedShares)
        # total['year'] = total.end.str[:4]
        # print('pre clean units total')
        # print(total)
        total = cleanUnits(total)
        # print('mid block post cleanunits total')
        # print(total)
        #  = df_col_added.rename(columns={'val':'interestPaid'})
        total = total.rename(columns={'val':'totalDivsPaid'})
        if total['Units'].isnull().all():
            total = total.drop(columns=['Units'])
        # print(total)
        total['totalDivsPaid'] = (total['totalDivsPaid'] * (-1)).where(total['totalDivsPaid'] < 0, other=total['totalDivsPaid'])
        # print(total)
        # perShare['year'] = perShare.end.str[:4]
        perShare = perShare.rename(columns={'val':'divsPaidPerShare'})
        perShare = perShare.drop(columns=['Units'])
        perShare['divsPaidPerShare'] = (perShare['divsPaidPerShare'] * (-1)).where(perShare['divsPaidPerShare'] < 0, other=perShare['divsPaidPerShare'])
        # shares = shares.drop(columns=['start','end'])
        # total = total.drop(columns=['start','end'])
        # perShare = perShare.drop(columns=['start','end'])
        # print('total, per share')
        # print(total)
        # print(perShare)

        
        rocps = cleanUnits(rocps)
        rocps = rocps.rename(columns={'val':'ROCperShare'})
        if rocps['Units'].isnull().all():
            rocps = rocps.drop(columns=['Units'])
        roctotal = cleanUnits(roctotal)
        roctotal = roctotal.rename(columns={'val':'ROCTotal'})
        if roctotal['Units'].isnull().all():
            roctotal = roctotal.drop(columns=['Units'])
        

        # print('shares, total, pershare: ')
        # print(shares)
        # print(total)
        # print(perShare)
        df_col_added = pd.merge(total, perShare, on=['year','Ticker','CIK'], how='outer')
        # print('1')
        # print(df_col_added)
        df_col_added = pd.merge(shares, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # print('2')
        # print(df_col_added)
        df_col_added = pd.merge(dilutedShares, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # print('3')
        # print(df_col_added)
        df_col_added = pd.merge(rocps, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # print('4')
        # print(df_col_added)
        df_col_added = pd.merge(roctotal, df_col_added, on=['year','Ticker','CIK'], how='outer')
        # print('5')
        # print(df_col_added)

        # print('tot and pshare pre temps')
        # print(df_col_added)
        
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
        # print('tot and pshare post temps')
        # print(df_col_added)

        for x in nanList: #Values in ex-US currencies seem weird versus common stock analysis sites. Could be an exchange rate issue I haven't accounted for in the exchange to USD.
            if x == 'divsPaidPerShare':
                df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['calcDivsPerShare']) #'tempPerShare',
                # growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
                # df_col_added['divGrowthRate'] = growthCol1 
            elif x == 'totalDivsPaid':
                df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
                # growthCol1 = grManualCalc(df_col_added['divsPaidPerShare'])
                # df_col_added['divGrowthRate'] = growthCol1 
        df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempShares']) #'tempPerShare',
        # print('tot and pshare post fills and drops')
        # print(df_col_added)
        
        df_col_added['shares'] = df_col_added['shares'].ffill().bfill() #.replace("", None) pre ffillbfill
        df_col_added['dilutedShares'] = df_col_added['dilutedShares'].ffill().bfill()
        # if df_col_added['shares'].empty:
        #     df_col_added['sharesGrowthRate'] = np.NaN
        # else:
        growthCol = grManualCalc(df_col_added['shares'])
        df_col_added['sharesGrowthRate'] = growthCol #df_col_added['shares'].pct_change()*100 #now we can add the growth rate once nulls filled
        # growthCol1 = grManualCalc(df_col_added['dilutedShares'])
        # df_col_added['dilutedSharesGrowthRate'] = growthCol1
        # df_col_added['sharesGrowthRate'] = df_col_added['sharesGrowthRate'].replace(np.nan,0) #fill in null values so later filter doesn't break dataset

        


        # df42 = pd.DataFrame()
        # df42['temp'] = df_col_added['tempPerShare']
        # df42['actual'] = df_col_added['divsPaidPerShare']
        # print(df42)

        

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
        
        # if df_col_added['divsPaidPerShares'].empty:
        #     df_col_added['divGrowthRate'] = np.NaN
        # else:
        
        # print('average growth rate: ')
        # print(df_col_added['divGrowthRate'].mean())
        # print('whats it look like end of clean divs')
        # print(df_col_added)

        # return df_col_added
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
            # meanReplacement = df_filled[x].mean()
            savedCol = df_filled[x]
            # df_filled[x] = df_filled[x].replace(np.NaN, meanReplacement)#.ffill()  we trying backfilling instead
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol#df_filled[x].pct_change(fill_method=None)*100

            if savedCol.isnull().any():
                percentNull = savedCol.isnull().sum() / len(savedCol)
                if percentNull > 0.4:
                    fixTracker += 1
            # if savedCol.equals(df_filled[x]):
            #     continue
            # else:
            #     fixTracker += 1

        df_filled = df_filled.drop(columns=['depreNAmorGrowthRate'])

        if df_filled['Units'].isnull().all():
            # print('they all empty')
            df_filled = df_filled.drop('Units',axis=1)
        else:
            # print('filling empties')
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
            # print('int paid percent')
            # print(percentNull)
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['interestPaid'] = df_filled['interestPaid'].ffill().bfill()
        if df_filled['totalDivsPaid'].isnull().any():
            percentNull = df_filled['totalDivsPaid'].isnull().sum() / len(df_filled['totalDivsPaid'])
            if percentNull > 0.4:
                fixTracker += 1
            # fixTracker += 1    
            # print('it was total divs paid')
            df_filled['totalDivsPaid'] = df_filled['totalDivsPaid'].replace(np.NaN, 0)#.ffill()
        if df_filled['divsPaidPerShare'].isnull().any():
            percentNull = df_filled['divsPaidPerShare'].isnull().sum() / len(df_filled['divsPaidPerShare'])
            if percentNull > 0.4:
                fixTracker += 1
            # fixTracker += 1   
            # print('it was per share divs paid')
            df_filled['divsPaidPerShare'] = df_filled['divsPaidPerShare'].replace(np.NaN, 0)#.ffill()
        if df_filled['shares'].isnull().all():
            # print('all shares null')
            fixTracker += 3
            df_filled['shares'] = df_filled['shares'].replace(np.NaN, 0)
        elif df_filled['shares'].isnull().any():
            percentNull = df_filled['shares'].isnull().sum() / len(df_filled['shares'])
            if percentNull > 0.4:
                fixTracker += 1
            # fixTracker += 1  
            # print('it was shares')
            df_filled['shares'] = df_filled['shares'].ffill().bfill() 

        df_filled['ROCperShare'] = df_filled['ROCperShare'].replace(np.NaN, 0)
        df_filled['ROCTotal'] = df_filled['ROCTotal'].replace(np.NaN, 0)

        # print('pre shares and div GR')
        # print(df_filled)
        if df_filled['sharesGrowthRate'].isnull().any():
            # fixTracker += 1  
            growthCol = grManualCalc(df_filled['shares'])
            df_filled['temp1'] = growthCol
            df_filled['sharesGrowthRate'] = df_filled['sharesGrowthRate'].fillna(df_filled.pop('temp1'))
            # df_filled = df_filled.drop(columns=['temp1'])
            # print('shares  GR')
            # print(df_filled)
            
        if df_filled['divGrowthRateBOT'].isnull().any():
            growthCol = grManualCalc(df_filled['totalDivsPaid'])
            df_filled['temp2'] = growthCol
            df_filled['divGrowthRateBOT'] = df_filled['divGrowthRateBOT'].fillna(df_filled.pop('temp2'))#['temp2'])
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)

        if df_filled['divGrowthRateBORPS'].isnull().any():
            growthCol = grManualCalc(df_filled['divsPaidPerShare'])
            df_filled['temp3'] = growthCol
            df_filled['divGrowthRateBORPS'] = df_filled['divGrowthRateBORPS'].fillna(df_filled.pop('temp3'))#['temp2'])

        if df_filled['divGrowthRateBOCPS'].isnull().any():
            growthCol = grManualCalc(df_filled['calcDivsPerShare'])
            df_filled['temp4'] = growthCol
            df_filled['divGrowthRateBOCPS'] = df_filled['divGrowthRateBOCPS'].fillna(df_filled.pop('temp4'))#['temp2'])

        if df_filled['ROCperShareGrowthRate'].isnull().any():
            growthCol = grManualCalc(df_filled['ROCperShare'])
            df_filled['temp5'] = growthCol
            df_filled['ROCperShareGrowthRate'] = df_filled['ROCperShareGrowthRate'].fillna(df_filled.pop('temp5'))#['temp2'])
        
        if df_filled['ROCTotalGrowthRate'].isnull().any():
            growthCol = grManualCalc(df_filled['ROCTotal'])
            df_filled['temp6'] = growthCol
            df_filled['ROCTotalGrowthRate'] = df_filled['ROCTotalGrowthRate'].fillna(df_filled.pop('temp6'))#['temp2'])

        if df_filled['dilutedShares'].isnull().all():
            # print('dil shares all null')
            df_filled['dilutedSharesGrowthRate'] = np.NaN
        else:
            # print('dil shares else')
            # print(df_filled['dilutedShares'])
            growthCol1 = grManualCalc(df_filled['dilutedShares'])
            # print(growthCol1)
            df_filled['dilutedSharesGrowthRate'] = growthCol1#['temp10'] = growthCol1
            
            # df_filled['dilutedSharesGrowthRate'] = df_filled['dilutedSharesGrowthRate'].fillna(df_filled.pop('temp10'))
            # print('temp10, dilutedsharesGR')
            # print(df_filled['temp10'])
            # print(df_filled[['dilutedShares','dilutedSharesGrowthRate','year']])
        # df_filled = df_filled.drop(columns=['temp10'],axis=1)
        # for x in df_filled:
        #     print(x)
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)

        # df_filled = df_filled.drop(columns=['temp1'])

        # print('about to fill units column')
        # print(df_filled)

        if df_filled['Units'].isnull().all():
            # print('they all empty')
            df_filled = df_filled.drop('Units',axis=1)
        else:
            # print('filling empties')
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        # print('filled units column')
        # print(df_filled)

        # print('ppost drop shares and div GR')
        # print(df_filled)
        # print('fixTracker')
        # print(fixTracker)
        if fixTracker >= 4:
            df_filled['DIVintegrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['DIVintegrityFlag'] = 'Good'
        else:
            df_filled['DIVintegrityFlag'] = 'Acceptable'
        # print('ppost int flag added')
        # print(df_filled)
        # df_filled2 = df_filled
        
    except Exception as err:
        print("fill empty divs GR error: ")
        print(err)

    finally:
        # print('in finally df filled')
        # print(df_filled)
        return df_filled

def fillEmptyROICGrowthRates(df):
    try:
        df_filled = df
        fixTracker = 0
        tarList = ['operatingIncome']#,'netIncome']
        tDebt = 'TotalDebt'
        equityParts = ['assets','liabilities']
        # equityFlag = 0

        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            # meanReplacement = df_filled[x].mean()
            savedCol = df_filled[x]
            df_filled[x] = df_filled[x].ffill().bfill()

            growthCol = grManualCalc(df_filled[x])
            df_filled[tarGrowthRate] = growthCol

            if savedCol.equals(df_filled[x]):
                continue
            else:
                fixTracker += 1
        # df_filled = df_filled.drop(columns=['netIncomeGrowthRate'])

        if df_filled['TotalDebt'].isnull().any():
            percentNull = df_filled['TotalDebt'].isnull().sum() / len(df_filled['TotalDebt'])
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['TotalDebt'] = df_filled['TotalDebt'].replace(np.NaN, 0)
        if df_filled['assets'].isnull().any():
            percentNull = df_filled['assets'].isnull().sum() / len(df_filled['assets'])
            # if df_filled['assets'].isnull().sum() > 1:
            #     equityFlag = 1
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['assets'] = df_filled['assets'].ffill().bfill()
        if df_filled['liabilities'].isnull().any():
            percentNull = df_filled['liabilities'].isnull().sum() / len(df_filled['liabilities'])
            # if df_filled['liabilities'].isnull().sum() > 1:
            #     equityFlag = 1
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['liabilities'] = df_filled['liabilities'].ffill().bfill()
        # if equityFlag == 1:
        df_filled['TotalEquity'] = df_filled['TotalEquity'].fillna(df_filled['assets'] - df_filled['liabilities'])

        if df_filled['Units'].isnull().all():
            # print('they all empty')
            df_filled = df_filled.drop('Units',axis=1)
        else:
            # print('filling empties')
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

        # print('ppost int flag added')
        # print(df_filled)

    except Exception as err:
        print("fill empty ROIC GR error: ")
        print(err)

    finally:
        # print('in finally df filled')
        # print(df_filled)
        return df_filled

def fillUnits(df):
    try:
        df_filled = pd.DataFrame()
        if df['Units'].isnull().all():
            # print('they all empty')
            df_filled = df.drop('Units',axis=1)
        else:
            # print('filling empties')
            df_filled = df
            df_filled['Units'] = df_filled['Units'].ffill().bfill()

        return df_filled
    except Exception as err:
        print("fill Units error: ")
        print(err)

def fillPrice(df):
    try:
        # data1 = yf.download(ticker235, '2020-12-30','2020-12-31')
        # print(df['Ticker'].loc[0])
        ticker = df['Ticker'].loc[0]
        df_filled = df
        yearList = df_filled['year'].tolist()
        priceList = []
        # print(yearList)
        # df_filled['price'] = 0 #maybe not needed
        # print('yearlist')
        # print(yearList)
        for x in yearList:
            # print(type(x))
            # print(x)
            # if int(x) <= 2012:
            #     pass
            # else:
            # df_filled['price'] = yf.download(ticker, str(x) + '-12-20', str(x) + '-12-31')['Close'][-1]
            priceData = yf.download(ticker, str(x) + '-12-20', str(x) + '-12-31')['Close']
            try:
                priceList.append(priceData[-1])
            except:
                priceList.append(np.NaN)
                continue
            # print('priceData')
            # print(priceData)
            
        # print(priceList)
        # print('priceList')
        # print(priceList)
        df_filled['price'] = priceList
        growthCol = grManualCalc(df_filled['price'])
        df_filled['priceGrowthRate'] = growthCol
        # print(df_filled['price'])
        # df_filled['price'] = yf.download(ticker, df['year'] + '-12-30', df['year'] + '-12-31')['Close'][0]
        
    except Exception as err:
        print("fill price error: ")
        print(err)
    finally:
        return df_filled
        # print(df_filled['price'])
        # print(df_filled['year'])
        # print(priceList)
        
#Making tables for DB insertion
def makeIncomeTableEntry(ticker, year, version, index_flag): 
    try:
        # integrity_flag = 'Good'
        rev_df = cleanRevenue(consolidateSingleAttribute(ticker, year, version, revenue, False))
        # print('rev df: ')
        # print(rev_df)
        netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
        # print('netInc_df df: ')
        # print(netInc_df)
        netIncNCI_df = cleanNetIncomeNCI(consolidateSingleAttribute(ticker, year, version, netIncomeNCI, False))
        # print('netIncNCI_df df: ')
        # print(netIncNCI_df)
        opcf_df = cleanOperatingCashFlow(consolidateSingleAttribute(ticker, year, version, operatingCashFlow, False))
        # print('opcf_df df: ')
        # print(opcf_df)
        invcf_df = cleanInvestingCashFlow(consolidateSingleAttribute(ticker, year, version, investingCashFlow, False))
        # print('invcf_dff df: ')
        # print(invcf_df)
        fincf_df = cleanFinancingCashFlow(consolidateSingleAttribute(ticker, year, version, financingCashFlow, False))
        # print('fincf_df df: ')
        # print(fincf_df)
        netcf_df = cleanNetCashFlow(consolidateSingleAttribute(ticker, year, version, netCashFlow, False))
        # print('netcf_df df: ')
        # print(netcf_df)
        capex_df = cleanCapEx(consolidateSingleAttribute(ticker, year, version, capEx, False))
        # print('capex_df df: ')
        # print(capex_df)
        depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))
        if depAmor_df.empty:
            depAmor_df = cleanDeprNAmor2(consolidateSingleAttribute(ticker, year, version, deprecAndAmor2, False),consolidateSingleAttribute(ticker, year, version, deprecAndAmor3, False))
        # print('depAmor_df df: ')
        # print(depAmor_df)
        gainSaleProp_df = cleanGainSaleProp(consolidateSingleAttribute(ticker, year, version, gainSaleProperty, False))
        # print('gainSaleProp_df: ')
        # print(gainSaleProp_df)
        #Merge all these DF's!
        # if rev_df['start'].isnull().any():
        #     print('in the if')
        #     rev_df = rev_df.drop(columns=['start'])
        #     revNinc = pd.merge(rev_df, netInc_df, on=['year','end','Ticker','CIK','Units'], how='outer')
        # else:
        #     print('in the else')
        #     # rev_df = rev_df.drop(columns=['start','end']) 
        #     # netInc_df = netInc_df.drop(columns=['start','end']) 

        ## this nested in else
        # print(len(rev_df['Units'].unique()))
        # print(len(netInc_df['Units'].unique()))
        #
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer')
        # revNinc['units'] = revNinc['Units_x']
        # revNinc = revNinc.drop(columns=['Units_x', 'Units_y'])
        # print('revNinc: ')
        # print(revNinc)
        plusopcf = pd.merge(revNinc, opcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusopcf = plusopcf.drop(columns=['units'])
        # print('plusopcf: ')
        # print(plusopcf)
        plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusinvcf['units'] = plusinvcf['Units_x']
        # plusinvcf = plusinvcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusinvcf: ')
        # print(plusinvcf)
        plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusfincf = plusfincf.drop(columns=['units'])
        # print('plusfincf: ')
        # print(plusfincf)

        plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusnetcf['units'] = plusnetcf['Units_x']
        # plusnetcf = plusnetcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusnetcf: ')
        # print(plusnetcf)

        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # pluscapex = pluscapex.drop(columns=['units'])
        # print('pluscapex: ')
        # print(pluscapex)

        plusDepAmor = pd.merge(pluscapex, depAmor_df, on=['year','Ticker','CIK','Units'], how='outer') #Testing joining on Units 'start','end',
        # print('plusDepAmor: ')
        # print(plusDepAmor)
        # plusDepAmor = pluseps.drop(columns=['Units_x', 'Units_y'])
        
        plusSaleProp = pd.merge(plusDepAmor, gainSaleProp_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # print('plusSaleProp: ')
        # print(plusSaleProp['investingCashFlow'])
        # print(plusSaleProp['investingCashFlowGrowthRate'])

        #CLEAN column empty values here before adding FFO calculations 
        plusSaleProp = fillEmptyIncomeGrowthRates(plusSaleProp)
        plusSaleProp = plusSaleProp.drop(columns=['depreNAmorGrowthRate'])
        
        addfcf = cleanfcf(plusSaleProp)
        # print('addfcf: ')
        # print(addfcf)
        
        addfcfMargin = cleanfcfMargin(addfcf)
        #Clean sales of property
        addfcfMargin['gainSaleProp'] = addfcfMargin['gainSaleProp'].replace(np.nan,0)
        # print('addfcfMargin: ')
        # print(addfcfMargin)

        addfcfMargin['ffo'] = addfcfMargin['netIncome'] + addfcfMargin['depreNAmor'] - addfcfMargin['gainSaleProp']
        growthCol = grManualCalc(addfcfMargin['ffo'])
        addfcfMargin['ffoGrowthRate'] = growthCol

        # for x in addfcfMargin:
        #     print(x)
        #     print(addfcfMargin[x])

        return addfcfMargin

    except Exception as err:
        print("makeIncomeTable error: ")
        print(err)

def makeROICtableEntry(ticker, year, version, index_flag):
    try:
        opIncome_df = cleanOperatingIncome(consolidateSingleAttribute(ticker, year, version, operatingIncome, False))
        # print('opinc df')
        # print(opIncome_df)
        taxRate_df = cleanTaxRate(consolidateSingleAttribute(ticker, year, version, taxRate, False))
        # print('taxrate df')
        # print(taxRate_df)
        netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
        # print('netincome df')
        # print(netInc_df)
        totalDebt_df = cleanDebt(consolidateSingleAttribute(ticker, year, version, shortTermDebt, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt1, False), consolidateSingleAttribute(ticker, year, version, longTermDebt2, False),
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt3, False), consolidateSingleAttribute(ticker, year, version, longTermDebt4, False))
        # print('TDebt df')
        # print(totalDebt_df)
        totalEquity_df = cleanTotalEquity(consolidateSingleAttribute(ticker, year, version, totalAssets, False), 
                                    consolidateSingleAttribute(ticker, year, version, totalLiabilities, False), consolidateSingleAttribute(ticker, year, version, nonCurrentLiabilities, False),
                                    consolidateSingleAttribute(ticker, year, version, currentLiabilities, False), consolidateSingleAttribute(ticker, year, version, nonCurrentAssets, False),
                                    consolidateSingleAttribute(ticker, year, version, currentAssets, False), consolidateSingleAttribute(ticker, year, version, shareHolderEquity, False))
                                    
        # print('TEquity df')
        # print(totalEquity_df)

    

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        # print('opIncNtax pre if statement')
        # print(opIncNtax)
        if opIncNtax['Units'].isnull().any():
            opIncNtax = opIncNtax.drop(columns=['Units'], axis=1)
            # print('opincntax df in empty if')
            # print(opIncNtaxNinc)
            # print(opIncNtax)
            opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK'], how='outer')
            # print('still in iff post merge')
            # print(opIncNtaxNinc)
        else:
            # print('in else')

            opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
            opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])
        # print('opincntax df after if')
        # print(opIncNtaxNinc)
        # print(opIncNtax)
        opIncNtaxNinc['Units'] = opIncNtaxNinc['Units'].ffill().bfill()
        
        plustDebt = pd.merge(opIncNtaxNinc, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        # print('plusdebt df')
        # print(plustDebt)
        # plustDebt = plustDebt.rename(columns={'start_x': 'start'})
        # plustDebt = plustDebt.drop(['start_y'],axis=1)
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
        # plustEquity = plustEquity.rename(columns={'start_x': 'start'})
        # plustEquity = plustEquity.drop(['start_y'],axis=1)

        # print('plustequity prefill gr')
        # print(plustEquity)

        plustEquity = fillEmptyROICGrowthRates(plustEquity)


        plustEquity['nopat'] = plustEquity['operatingIncome'] * (1 - plustEquity['taxRate'])
        plustEquity['investedCapital'] = plustEquity['TotalEquity'] + plustEquity['TotalDebt']
        plustEquity['roic'] = plustEquity['nopat'] / plustEquity['investedCapital'] * 100
        plustEquity['adjRoic'] = plustEquity['netIncome'] / plustEquity['investedCapital'] * 100
        plustEquity['reportedAdjRoic'] = plustEquity['netIncome'] / (plustEquity['ReportedTotalEquity'] + plustEquity['TotalDebt']) * 100
        plustEquity['calculatedRoce'] = plustEquity['netIncome'] / plustEquity['TotalEquity'] * 100
        plustEquity['reportedRoce'] = plustEquity['netIncome'] / plustEquity['ReportedTotalEquity'] * 100

        # print('ass')
        # print(plustEquity['assets'])
        # print('lia')
        # print(plustEquity['liabilities'])
        # print('eq')
        # print(plustEquity['TotalEquity'])
        # print('rep eq')
        # print(plustEquity['ReportedTotalEquity'])



        return plustEquity

    except Exception as err:
        print("makeROIC table error: ")
        print(err)

def makeDividendTableEntry(ticker, year, version, index_flag): 
    try:
        intPaid_df = cleanInterestPaid(consolidateSingleAttribute(ticker, year, version, interestPaid, False))
        # print('intpaid: ')
        # print(intPaid_df)
        divs_df = cleanDividends(consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, False), 
                                    consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, dilutedSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, returnOfCapitalPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, totalReturnOfCapital, False))
                                    
        # print('divsdf: ')
        # print(divs_df)
        if divs_df['year'][0] == -1:
            df_dunce = pd.DataFrame(columns=['Ticker'])
            df_dunce.loc[0, 'Ticker'] = ticker
            csv.simple_appendTo_csv(fr_iC_toSEC, df_dunce,'z-divDataReallyNotFound', False)
            return 'No Good Dividend Data'
        else:
            # intNshares = pd.merge(intPaid_df, shares_df, on=['year','start','end','Ticker','CIK'], how='outer')
            if divs_df['Units'].isnull().any():
                divs_df = divs_df.drop(columns=['Units'])
                # print('did divsdf drop units?!?!: ')
                # print(divs_df)
                # if divs_df['start'].isnull().any():
                #     divs_df = divs_df.drop(columns=['start'])
                #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year', 'end','Ticker','CIK'], how='outer')
                # else:
                intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')#Was nested in else on row 'start', 'end',
                # print('if intNdivs: ')
                # print(intNdivs)
            else:
                intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer') #'start', 'end',
            #     print('else intNdivs: ')
            #     print(intNdivs)
            # print('post ifelse merge intdivs')
            # print(intNdivs)
            # print('pre fill intndivs: ')
            # print(intNdivs)

            intNdivs = fillEmptyDivsGrowthRates(intNdivs)

            # print('post fill intndivs: ')
            # print(intNdivs)

            return intNdivs
    
    except Exception as err:
        print("makeDividend table error: ")
        print(err)

def makeConsolidatedTableEntry(ticker, year, version, index_flag):
    try:
        ### INCOME TABLE START
        rev_df = cleanRevenue(consolidateSingleAttribute(ticker, year, version, revenue, False))
        # print('rev df: ')
        # print(rev_df)
        netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
        # print('netInc_df df: ')
        # print(netInc_df)
        netIncNCI_df = cleanNetIncomeNCI(consolidateSingleAttribute(ticker, year, version, netIncomeNCI, False))
        # print('netIncNCI_df df: ')
        # print(netIncNCI_df)
        eps_df = cleanEPS(consolidateSingleAttribute(ticker, year, version, eps, False))
        # print('eps df')
        # print(eps_df)
        # print(eps_df['Ticker'].isnull().any())
        opcf_df = cleanOperatingCashFlow(consolidateSingleAttribute(ticker, year, version, operatingCashFlow, False))
        # print('opcf_df df: ')
        # print(opcf_df)
        invcf_df = cleanInvestingCashFlow(consolidateSingleAttribute(ticker, year, version, investingCashFlow, False))
        # print('invcf_dff df: ')
        # print(invcf_df)
        fincf_df = cleanFinancingCashFlow(consolidateSingleAttribute(ticker, year, version, financingCashFlow, False))
        # print('fincf_df df: ')
        # print(fincf_df)
        netcf_df = cleanNetCashFlow(consolidateSingleAttribute(ticker, year, version, netCashFlow, False))
        # print('netcf_df df: ')
        # print(netcf_df)
        capex_df = cleanCapEx(consolidateSingleAttribute(ticker, year, version, capEx, False))
        # print('capex_df df: ')
        # print(capex_df)
        depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))
        if depAmor_df.empty:
            depAmor_df = cleanDeprNAmor2(consolidateSingleAttribute(ticker, year, version, deprecAndAmor2, False),consolidateSingleAttribute(ticker, year, version, deprecAndAmor3, False))
        # print('depAmor_df df: ')
        # print(depAmor_df)
        gainSaleProp_df = cleanGainSaleProp(consolidateSingleAttribute(ticker, year, version, gainSaleProperty, False))
        # print('gainSaleProp_df: ')
        # print(gainSaleProp_df)
        
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        # print('revNinc: ')
        # print(revNinc)
        revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer') 
        # print('revNinc: ')
        # print(revNinc)
        if eps_df.empty:
            revNinc['reportedEPS'] = np.NaN
            revNinc['reportedEPSGrowthRate'] = np.NaN
        else:
            revNinc = pd.merge(revNinc, eps_df, on=['year','Ticker','CIK'], how='outer')
        # revNinc['units'] = revNinc['Units_x']
        # revNinc = revNinc.drop(columns=['Units_x', 'Units_y'])
        # print('revNinc: ')
        # print(revNinc)
        plusopcf = pd.merge(revNinc, opcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusopcf = plusopcf.drop(columns=['units'])
        # print('plusopcf: ')
        # print(plusopcf)
        plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusinvcf['units'] = plusinvcf['Units_x']
        # plusinvcf = plusinvcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusinvcf: ')
        # print(plusinvcf)
        plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusfincf = plusfincf.drop(columns=['units'])
        # print('plusfincf: ')
        # print(plusfincf)

        plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusnetcf['units'] = plusnetcf['Units_x']
        # plusnetcf = plusnetcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusnetcf: ')
        # print(plusnetcf)

        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # pluscapex = pluscapex.drop(columns=['units'])
        # print('pluscapex: ')
        # print(pluscapex)

        plusDepAmor = pd.merge(pluscapex, depAmor_df, on=['year','Ticker','CIK','Units'], how='outer') #Testing joining on Units 'start','end',
        # print('plusDepAmor: ')
        # print(plusDepAmor)
        # plusDepAmor = pluseps.drop(columns=['Units_x', 'Units_y'])
        
        plusSaleProp = pd.merge(plusDepAmor, gainSaleProp_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # print('plusSaleProp: ')
        # print(plusSaleProp['investingCashFlow'])
        # print(plusSaleProp['investingCashFlowGrowthRate'])

        plusSaleProp = fillUnits(plusSaleProp)
        # print('income done')
        # print(plusSaleProp['Units'])
        ### INCOME TABLE END

        ### DIVS TABLE START
        intPaid_df = cleanInterestPaid(consolidateSingleAttribute(ticker, year, version, interestPaid, False))
        # print('intpaid: ')
        # print(intPaid_df)
        divs_df = cleanDividends(consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, False), 
                                    consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, dilutedSharesOutstanding, False),
                                    consolidateSingleAttribute(ticker, year, version, returnOfCapitalPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, totalReturnOfCapital, False))
        # print('divsdf con: ')
        # print(divs_df['Units'])
        # if divs_df['year'][0] == -1:
        #     df_dunce = pd.DataFrame(columns=['Ticker'])
        #     df_dunce.loc[0, 'Ticker'] = ticker
        #     csv.simple_appendTo_csv(fr_iC_toSEC, df_dunce,'z-divDataReallyNotFound', False)
        #     return 'No Good Dividend Data'
        # else:
            # intNshares = pd.merge(intPaid_df, shares_df, on=['year','start','end','Ticker','CIK'], how='outer')
        if 'Units' not in divs_df:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        elif divs_df['Units'].isnull().any():
            # print('divs df had empty units')
            divs_df = divs_df.drop(columns=['Units'])
            # print('did divsdf drop units?!?!: ')
            # print(divs_df)
            # if divs_df['start'].isnull().any():
            #     divs_df = divs_df.drop(columns=['start'])
            #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year', 'end','Ticker','CIK'], how='outer')
            # else:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')#Was nested in else on row 'start', 'end',
            # print('if intNdivs: ')
            # print(intNdivs)
        else:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        

        #     print('else intNdivs: ')
        # print(intNdivs)
        # print('post ifelse merge intdivs')
        # print(intNdivs)
        # print('pre fill intndivs con: ')
        # print(intNdivs)
        intNdivs = fillUnits(intNdivs)
        # print('post fill intndivs con: ')
        # print(intNdivs['Units'])
        ### DIVS TABLE END
        
        ### ROIC TABLE START
        opIncome_df = cleanOperatingIncome(consolidateSingleAttribute(ticker, year, version, operatingIncome, False))
        # print('opinc df')
        # print(opIncome_df)
        taxRate_df = cleanTaxRate(consolidateSingleAttribute(ticker, year, version, taxRate, False))
        # print('taxrate df')
        # print(taxRate_df)
        totalDebt_df = cleanDebt(consolidateSingleAttribute(ticker, year, version, shortTermDebt, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt1, False), consolidateSingleAttribute(ticker, year, version, longTermDebt2, False),
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt3, False), consolidateSingleAttribute(ticker, year, version, longTermDebt4, False))
        # print('TDebt df')
        # print(totalDebt_df)
        totalEquity_df = cleanTotalEquity(consolidateSingleAttribute(ticker, year, version, totalAssets, False), 
                                    consolidateSingleAttribute(ticker, year, version, totalLiabilities, False), consolidateSingleAttribute(ticker, year, version, nonCurrentLiabilities, False),
                                    consolidateSingleAttribute(ticker, year, version, currentLiabilities, False), consolidateSingleAttribute(ticker, year, version, nonCurrentAssets, False),
                                    consolidateSingleAttribute(ticker, year, version, currentAssets, False), consolidateSingleAttribute(ticker, year, version, shareHolderEquity, False))
                                    
        # print('TEquity df')
        # print(totalEquity_df)
        nav_df = cleanNAV(consolidateSingleAttribute(ticker, year, version, netAssetValue, False))
        # print('nav df')
        # print(nav_df)
        # print(nav_df.empty)
        # print(nav_df.isnull().any())

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        opIncNtax['Units'] = opIncNtax['Units'].ffill().bfill()
        # print('opIncNtax')
        # print(opIncNtax)
        if opIncNtax['Units'].isnull().all():
            opIncNtax['Units'] = 'USD'
        # print('opIncNtax')
        # print(opIncNtax)
        
        # if opIncNtax['Units'].isnull().all():
        #     opIncNtax = opIncNtax.drop(columns=['Units'], axis=1)
        #     # print('opincntax df in empty if')
        #     # print(opIncNtaxNinc)
        #     # print(opIncNtax)
        #     opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK'], how='outer')
        #     # print('still in iff post merge')
        #     # print(opIncNtaxNinc)
        # else:

        #     opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        #     opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])

        # print('opincntax df after if')
        # print(opIncNtaxNinc)
        # print(opIncNtax)
        
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        # print('plusdebt df')
        # print(plustDebt)
        # plustDebt = plustDebt.rename(columns={'start_x': 'start'})
        # plustDebt = plustDebt.drop(['start_y'],axis=1)
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
        # print('plustequity pre first merge')
        # print(plustEquity)
        if nav_df.empty:
            plustEquity['nav'] = np.NaN
            plustEquity['navGrowthRate'] = np.NaN
        else:
            plustEquity = pd.merge(plustEquity, nav_df, on=['year','Ticker','CIK'], how='outer')
        

        # print('plustequity post merge')
        # print(plustEquity)
        # plustEquity = plustEquity.rename(columns={'start_x': 'start'})
        # plustEquity = plustEquity.drop(['start_y'],axis=1)

        # print('plustequity pre fill')
        # print(plustEquity)
        plustEquity = fillUnits(plustEquity)
        # print('plustequity at end')
        # print(plustEquity)
        ### ROIC TABLE END
        
        ###INCOME TABLE IS plusSaleProp
        ###Dividends table is intNdivs
        ###ROIC TABLE is plustEquity
        # print('intNdivs')
        # print(intNdivs)
        # print('plustequity after fill')
        # print(plustEquity)
        if 'Units' not in intNdivs:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK'], how='outer')
        else:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK','Units'], how='outer')
        # print('pre final merge')
        # print(divsPlusROIC)
        # print('divs n roic con')
        # print(divsPlusROIC)
        # print('pre final merge second df')
        # print(plusSaleProp)
        incDivsROIC = pd.merge(divsPlusROIC, plusSaleProp, on=['year','Ticker','CIK','Units'], how='outer')
        # print('all con')
        # print(incDivsROIC)
        # print('after final merge')
        # print(incDivsROIC)

        incDivsROIC = fillPrice(incDivsROIC)

        incDivsROIC = fillEmptyDivsGrowthRates(incDivsROIC) 
        
        #Finish the Income Table Entries
        incDivsROIC = fillEmptyIncomeGrowthRates(incDivsROIC)

        #moved into above function. fingers crossed!
        # incDivsROIC = incDivsROIC.drop(columns=['depreNAmorGrowthRate'])
        # incDivsROIC = cleanfcf(incDivsROIC)
        # incDivsROIC = cleanfcfMargin(incDivsROIC)
        # # #Clean sales of property
        # incDivsROIC['gainSaleProp'] = incDivsROIC['gainSaleProp'].replace(np.nan,0)
        # incDivsROIC['ffo'] = incDivsROIC['netIncome'] + incDivsROIC['depreNAmor'] - incDivsROIC['gainSaleProp']
        # growthCol = grManualCalc(incDivsROIC['ffo'])
        # incDivsROIC['ffoGrowthRate'] = growthCol

        #Finish the ROIC Table Entries
        incDivsROIC = fillEmptyROICGrowthRates(incDivsROIC)

        incDivsROIC['Sector'] = nameSectorDict[ticker]
        incDivsROIC['Industry'] = nameIndustryDict[ticker]
        #cik = nameCikDict[ticker]

        #moved into above function. fingers crossed!
        # incDivsROIC['nopat'] = incDivsROIC['operatingIncome'] * (1 - incDivsROIC['taxRate'])
        # incDivsROIC['investedCapital'] = incDivsROIC['TotalEquity'] + incDivsROIC['TotalDebt']
        # incDivsROIC['roic'] = incDivsROIC['nopat'] / incDivsROIC['investedCapital'] * 100
        # incDivsROIC['adjRoic'] = incDivsROIC['netIncome'] / incDivsROIC['investedCapital'] * 100
        # incDivsROIC['reportedAdjRoic'] = incDivsROIC['netIncome'] / (incDivsROIC['ReportedTotalEquity'] + incDivsROIC['TotalDebt']) * 100
        # incDivsROIC['calculatedRoce'] = incDivsROIC['netIncome'] / incDivsROIC['TotalEquity'] * 100
        # incDivsROIC['reportedRoce'] = incDivsROIC['netIncome'] / incDivsROIC['ReportedTotalEquity'] * 100

        # return incDivsROIC
    
    except Exception as err:
        print("make consolidated table error: ")
        print(err)
    finally:
        return incDivsROIC

def checkYearsIntegritySector(sector,begNum,endNum):
    try:
        nameCheckList = sector['Ticker'][begNum:endNum]
        # nameCikDict = sector.set_index('Ticker')['CIK'].to_dict()
        MissingYearTracker = []
        EndYearTracker = []
        # dMissingYearTracker = []
        # dEndYearTracker = []
        # rMissingYearTracker = []
        # rEndYearTracker = []
        #NEW
        incRev = []
        incNetInc = []
        incOpCF = []
        incCapEx = []
        incNetCF = []
        incDepnAmor = []
        incGainProp = []

        # divYearTracker = []
        # divomeNullTracker = []
        #NEW
        dIntPaid = []
        dTotalPaid = []
        dSharesPaid = []
        dShares = []

        # roicYearTracker = []
        # roicNullTracker = []
        #new
        rTotalEq = []

        toRecapture = []
        yearsList = ['2023'] #2022
        version123 = '2'
        # numTracker = tracker

        # while endNum > numTracker:
        for x in nameCheckList:# in range(len(nameCheckList)/10):
            print(x)# + ', ' + str(numTracker) + ' out of ' + str(endNum))
            # gc.collect() #not helping memory issue
            # numTracker += 1
            try:
                theTable = makeConsolidatedTableEntry(x, '2024', version123, False)
                # divsTable = makeDividendTableEntry(x,'2024',version123,False)
                # roicTable = makeROICtableEntry(x,'2024', version123, False)
                #make lists of years columns, use to track years
                iyears = list(theTable['year'])
                iyearsint = []
                for y in iyears:
                    iyearsint.append(int(y))
                istart, iend = iyearsint[0], iyearsint[-1]
                iMissingYears = sorted(set(range(istart,iend)) - set(iyearsint))
                if len(iMissingYears) > 0:
                    MissingYearTracker.append(x)
                if iend != 2023:
                    EndYearTracker.append(x)
                if theTable['revenue'].isnull().any():
                    incRev.append(x)
                if theTable['netIncome'].isnull().any():
                    incNetInc.append(x)
                if theTable['operatingCashFlow'].isnull().any():
                    incOpCF.append(x)
                if theTable['capEx'].isnull().any():
                    incCapEx.append(x)
                if theTable['netCashFlow'].isnull().any():
                    incNetCF.append(x)
                if theTable['depreNAmor'].isnull().any():
                    incDepnAmor.append(x)
                if theTable['gainSaleProp'].isnull().any():
                    incGainProp.append(x)

                #make lists of years columns, use to track years
                # dyears = list(theTable['year'])
                # dyearsint = []
                # for z in dyears:
                #     dyearsint.append(int(z))
                # dstart, dend = dyearsint[0], dyearsint[-1]
                # # dMissingYears = sorted(set(range(dstart,dend)) - set(dyearsint))
                # # if len(dMissingYears) > 0:
                # #     dMissingYearTracker.append(x)
                # if dend != 2023:
                #     dEndYearTracker.append(x)
                if theTable['interestPaid'].isnull().any():
                    dIntPaid.append(x)
                if theTable['totalDivsPaid'].isnull().any():
                    dTotalPaid.append(x)
                if theTable['divsPaidPerShare'].isnull().any():
                    dSharesPaid.append(x)
                if theTable['shares'].isnull().any():
                    dShares.append(x)
                


                # #make lists of years columns, use to track years
                # ryears = list(roicTable['year'])
                # ryearsint = []
                # for a in ryears:
                #     ryearsint.append(int(a))
                # rstart, rend = ryearsint[0], ryearsint[-1]
                # # rMissingYears = sorted(set(range(rstart,rend)) - set(ryearsint))
                # # if len(rMissingYears) > 0:
                # #     rMissingYearTracker.append(x)
                # if rend != 2023:
                #     rEndYearTracker.append(x)
                if theTable['TotalEquity'].isnull().any():
                    if theTable['ReportedTotalEquity'].isnull().any():
                        rTotalEq.append(x)
                
                # if numTracker == endNum:
                #     break
                
            except Exception as err:
                print("nested check years integrity error: ")
                print(err)
                toRecapture.append(x)
                continue             


    except Exception as err:
        print("check years integrity error: ")
        print(err)

    finally:
        print('recapList = ')
        print(toRecapture)
        
        print('missingRevenue = ')
        print(incRev)
        print('missingNetIncome = ')
        print(incNetInc)
        print('missingOpCF = ')
        print(incOpCF)
        print('missingCapEx = ')
        print(incCapEx)
        print('missingNetCF = ')
        print(incNetCF)
        print('missingDepreNAmor = ')
        print(incDepnAmor)
        print('missing income prop sales')
        print(incGainProp)
        
        
        print('missingIntPaid = ')
        print(dIntPaid)
        print('missingDivTotalPaid = ')
        print(dTotalPaid)
        print('missingDivSharesPaid = ')
        print(dSharesPaid)
        print('missingSshares = ')
        print(dShares)
        
        
        print('missingTotalEquity = ')
        print(rTotalEq)

        print('missing years = ')
        print(MissingYearTracker)
        # print('missingdivyears = ')
        # print(dMissingYearTracker)
        # print('missingroicyears =')
        # print(rMissingYearTracker)

        print('wrong end year = ')
        print(EndYearTracker)
        # print('wrongdivendyear = ')
        # print(dEndYearTracker)
        # print('wrongroicendyear = ')
        # print(rEndYearTracker)
        
def checkYearsIntegritySectorBACKUP(sector,begNum,endNum):
    try:
        nameCheckList = sector['Ticker'][begNum:endNum]
        # nameCikDict = sector.set_index('Ticker')['CIK'].to_dict()
        incMissingYearTracker = []
        incomeEndYearTracker = []
        dMissingYearTracker = []
        dEndYearTracker = []
        rMissingYearTracker = []
        rEndYearTracker = []
        #NEW
        incRev = []
        incNetInc = []
        incOpCF = []
        incCapEx = []
        incNetCF = []
        incDepnAmor = []
        incGainProp = []

        # divYearTracker = []
        # divomeNullTracker = []
        #NEW
        dIntPaid = []
        dTotalPaid = []
        dSharesPaid = []
        dShares = []

        # roicYearTracker = []
        # roicNullTracker = []
        #new
        rTotalEq = []

        toRecapture = []
        yearsList = ['2023'] #2022
        version123 = '2'
        # numTracker = tracker

        # while endNum > numTracker:
        for x in nameCheckList:# in range(len(nameCheckList)/10):
            print(x)# + ', ' + str(numTracker) + ' out of ' + str(endNum))
            # numTracker += 1
            try:
                incTable = makeIncomeTableEntry(x, '2024', version123, False)
                divsTable = makeDividendTableEntry(x,'2024',version123,False)
                roicTable = makeROICtableEntry(x,'2024', version123, False)
                #make lists of years columns, use to track years
                iyears = list(incTable['year'])
                iyearsint = []
                for y in iyears:
                    iyearsint.append(int(y))
                istart, iend = iyearsint[0], iyearsint[-1]
                # iMissingYears = sorted(set(range(istart,iend)) - set(iyearsint))
                # if len(iMissingYears) > 0:
                #     incMissingYearTracker.append(x)
                if iend != 2023:
                    incomeEndYearTracker.append(x)
                if incTable['revenue'].isnull().any():
                    incRev.append(x)
                if incTable['netIncome'].isnull().any():
                    incNetInc.append(x)
                if incTable['operatingCashFlow'].isnull().any():
                    incOpCF.append(x)
                if incTable['capEx'].isnull().any():
                    incCapEx.append(x)
                if incTable['netCashFlow'].isnull().any():
                    incNetCF.append(x)
                if incTable['depreNAmor'].isnull().any():
                    incDepnAmor.append(x)
                if incTable['gainSaleProp'].isnull().any():
                    incGainProp.append(x)

                #make lists of years columns, use to track years
                dyears = list(divsTable['year'])
                dyearsint = []
                for z in dyears:
                    dyearsint.append(int(z))
                dstart, dend = dyearsint[0], dyearsint[-1]
                # dMissingYears = sorted(set(range(dstart,dend)) - set(dyearsint))
                # if len(dMissingYears) > 0:
                #     dMissingYearTracker.append(x)
                if dend != 2023:
                    dEndYearTracker.append(x)
                if divsTable['interestPaid'].isnull().any():
                    dIntPaid.append(x)
                if divsTable['totalDivsPaid'].isnull().any():
                    dTotalPaid.append(x)
                if divsTable['divsPaidPerShare'].isnull().any():
                    dSharesPaid.append(x)
                if divsTable['shares'].isnull().any():
                    dShares.append(x)
                


                # #make lists of years columns, use to track years
                ryears = list(roicTable['year'])
                ryearsint = []
                for a in ryears:
                    ryearsint.append(int(a))
                rstart, rend = ryearsint[0], ryearsint[-1]
                # rMissingYears = sorted(set(range(rstart,rend)) - set(ryearsint))
                # if len(rMissingYears) > 0:
                #     rMissingYearTracker.append(x)
                if rend != 2023:
                    rEndYearTracker.append(x)
                if roicTable['TotalEquity'].isnull().any():
                    if roicTable['ReportedTotalEquity'].isnull().any():
                        rTotalEq.append(x)
                
                # if numTracker == endNum:
                #     break
                
            except Exception as err:
                print("nested check years integrity error: ")
                print(err)
                toRecapture.append(x)
                continue             


    except Exception as err:
        print("check years integrity error: ")
        print(err)

    finally:
        print('recapList = ')
        print(toRecapture)
        
        print('missingRevenue = ')
        print(incRev)
        print('missingNetIncome = ')
        print(incNetInc)
        print('missingOpCF = ')
        print(incOpCF)
        print('missingCapEx = ')
        print(incCapEx)
        print('missingNetCF = ')
        print(incNetCF)
        print('missingDepreNAmor = ')
        print(incDepnAmor)
        print('missing income prop sales')
        print(incGainProp)
        
        
        print('missingIntPaid = ')
        print(dIntPaid)
        print('missingDivTotalPaid = ')
        print(dTotalPaid)
        print('missingDivSharesPaid = ')
        print(dSharesPaid)
        print('missingSshares = ')
        print(dShares)
        
        
        print('missingTotalEquity = ')
        print(rTotalEq)

        # print('missingincomeyears = ')
        # print(incMissingYearTracker)
        # print('missingdivyears = ')
        # print(dMissingYearTracker)
        # print('missingroicyears =')
        # print(rMissingYearTracker)

        print('wrongincomeendyear = ')
        print(incomeEndYearTracker)
        print('wrongdivendyear = ')
        print(dEndYearTracker)
        print('wrongroicendyear = ')
        print(rEndYearTracker)
        
def checkYearsIntegrityList(sectorList):
    try:
        nameCheckList = sectorList
        # nameCikDict = sector.set_index('Ticker')['CIK'].to_dict()
        MissingYearTracker = []
        EndYearTracker = []
        # dMissingYearTracker = []
        # dEndYearTracker = []
        # rMissingYearTracker = []
        # rEndYearTracker = []
        #NEW
        incRev = []
        incNetInc = []
        incOpCF = []
        incCapEx = []
        incNetCF = []
        incDepnAmor = []
        incGainProp = []

        # divYearTracker = []
        # divomeNullTracker = []
        #NEW
        dIntPaid = []
        dTotalPaid = []
        dSharesPaid = []
        dShares = []

        # roicYearTracker = []
        # roicNullTracker = []
        #new
        rTotalEq = []

        toRecapture = []
        yearsList = ['2023'] #2022
        version123 = '2'
        # numTracker = tracker

        # while endNum > numTracker:
        for x in nameCheckList:# in range(len(nameCheckList)/10):
            print(x)# + ', ' + str(numTracker) + ' out of ' + str(endNum))
            # gc.collect() #not helping memory issue
            # numTracker += 1
            try:
                theTable = makeConsolidatedTableEntry(x, '2024', version123, False)
                # divsTable = makeDividendTableEntry(x,'2024',version123,False)
                # roicTable = makeROICtableEntry(x,'2024', version123, False)
                #make lists of years columns, use to track years
                iyears = list(theTable['year'])
                iyearsint = []
                for y in iyears:
                    iyearsint.append(int(y))
                istart, iend = iyearsint[0], iyearsint[-1]
                iMissingYears = sorted(set(range(istart,iend)) - set(iyearsint))
                if len(iMissingYears) > 0:
                    MissingYearTracker.append(x)
                if iend != 2023:
                    EndYearTracker.append(x)
                if theTable['revenue'].isnull().any():
                    incRev.append(x)
                if theTable['netIncome'].isnull().any():
                    incNetInc.append(x)
                if theTable['operatingCashFlow'].isnull().any():
                    incOpCF.append(x)
                if theTable['capEx'].isnull().any():
                    incCapEx.append(x)
                if theTable['netCashFlow'].isnull().any():
                    incNetCF.append(x)
                if theTable['depreNAmor'].isnull().any():
                    incDepnAmor.append(x)
                if theTable['gainSaleProp'].isnull().any():
                    incGainProp.append(x)

                #make lists of years columns, use to track years
                # dyears = list(theTable['year'])
                # dyearsint = []
                # for z in dyears:
                #     dyearsint.append(int(z))
                # dstart, dend = dyearsint[0], dyearsint[-1]
                # # dMissingYears = sorted(set(range(dstart,dend)) - set(dyearsint))
                # # if len(dMissingYears) > 0:
                # #     dMissingYearTracker.append(x)
                # if dend != 2023:
                #     dEndYearTracker.append(x)
                if theTable['interestPaid'].isnull().any():
                    dIntPaid.append(x)
                if theTable['totalDivsPaid'].isnull().any():
                    dTotalPaid.append(x)
                if theTable['divsPaidPerShare'].isnull().any():
                    dSharesPaid.append(x)
                if theTable['shares'].isnull().any():
                    dShares.append(x)
                


                # #make lists of years columns, use to track years
                # ryears = list(roicTable['year'])
                # ryearsint = []
                # for a in ryears:
                #     ryearsint.append(int(a))
                # rstart, rend = ryearsint[0], ryearsint[-1]
                # # rMissingYears = sorted(set(range(rstart,rend)) - set(ryearsint))
                # # if len(rMissingYears) > 0:
                # #     rMissingYearTracker.append(x)
                # if rend != 2023:
                #     rEndYearTracker.append(x)
                if theTable['TotalEquity'].isnull().any():
                    if theTable['ReportedTotalEquity'].isnull().any():
                        rTotalEq.append(x)
                
                # if numTracker == endNum:
                #     break
                
            except Exception as err:
                print("nested check years integrity error: ")
                print(err)
                toRecapture.append(x)
                continue             


    except Exception as err:
        print("check years integrity error: ")
        print(err)

    finally:
        print('recapList = ')
        print(toRecapture)
        
        print('missingRevenue = ')
        print(incRev)
        print('missingNetIncome = ')
        print(incNetInc)
        print('missingOpCF = ')
        print(incOpCF)
        print('missingCapEx = ')
        print(incCapEx)
        print('missingNetCF = ')
        print(incNetCF)
        print('missingDepreNAmor = ')
        print(incDepnAmor)
        print('missing income prop sales')
        print(incGainProp)
        
        
        print('missingIntPaid = ')
        print(dIntPaid)
        print('missingDivTotalPaid = ')
        print(dTotalPaid)
        print('missingDivSharesPaid = ')
        print(dSharesPaid)
        print('missingSshares = ')
        print(dShares)
        
        
        print('missingTotalEquity = ')
        print(rTotalEq)

        print('missing years = ')
        print(MissingYearTracker)
        # print('missingdivyears = ')
        # print(dMissingYearTracker)
        # print('missingroicyears =')
        # print(rMissingYearTracker)

        print('wrong end year = ')
        print(EndYearTracker)
        # print('wrongdivendyear = ')
        # print(dEndYearTracker)
        # print('wrongroicendyear = ')
        # print(rEndYearTracker)
    
    # try:
    #     nameCheckList = sectorList
    #     # nameCikDict = sector.set_index('Ticker')['CIK'].to_dict()
    #     incMissingYearTracker = []
    #     incomeEndYearTracker = []
    #     dMissingYearTracker = []
    #     dEndYearTracker = []
    #     rMissingYearTracker = []
    #     rEndYearTracker = []
    #     #NEW
    #     incRev = []
    #     incNetInc = []
    #     incOpCF = []
    #     incCapEx = []
    #     incNetCF = []
    #     incDepnAmor = []
    #     incGainProp = []

    #     # divYearTracker = []
    #     # divomeNullTracker = []
    #     #NEW
    #     dIntPaid = []
    #     dTotalPaid = []
    #     dSharesPaid = []
    #     dShares = []

    #     # roicYearTracker = []
    #     # roicNullTracker = []
    #     #new
    #     rTotalEq = []

    #     toRecapture = []
    #     yearsList = ['2023','2024'] #2022
    #     version123 = '2'

    #     for x in nameCheckList:
    #         print(x)
    #         try:
    #             incTable = makeIncomeTableEntry(x, '2024', version123, False)
    #             divsTable = makeDividendTableEntry(x,'2024',version123,False)
    #             roicTable = makeROICtableEntry(x,'2024', version123, False)
    #             #make lists of years columns, use to track years
    #             iyears = list(incTable['year'])
    #             iyearsint = []
    #             for y in iyears:
    #                 iyearsint.append(int(y))
    #             istart, iend = iyearsint[0], iyearsint[-1]
    #             # iMissingYears = sorted(set(range(istart,iend)) - set(iyearsint))
    #             # if len(iMissingYears) > 0:
    #             #     incMissingYearTracker.append(x)
    #             if iend != 2023:
    #                 incomeEndYearTracker.append(x)
    #             if incTable['revenue'].isnull().any():
    #                 incRev.append(x)
    #             if incTable['netIncome'].isnull().any():
    #                 incNetInc.append(x)
    #             if incTable['operatingCashFlow'].isnull().any():
    #                 incOpCF.append(x)
    #             if incTable['capEx'].isnull().any():
    #                 incCapEx.append(x)
    #             if incTable['netCashFlow'].isnull().any():
    #                 incNetCF.append(x)
    #             if incTable['depreNAmor'].isnull().any():
    #                 incDepnAmor.append(x)
    #             if incTable['gainSaleProp'].isnull().any():
    #                 incGainProp.append(x)

    #             #make lists of years columns, use to track years
    #             dyears = list(divsTable['year'])
    #             dyearsint = []
    #             for z in dyears:
    #                 dyearsint.append(int(z))
    #             dstart, dend = dyearsint[0], dyearsint[-1]
    #             # dMissingYears = sorted(set(range(dstart,dend)) - set(dyearsint))
    #             # if len(dMissingYears) > 0:
    #             #     dMissingYearTracker.append(x)
    #             if dend != 2023:
    #                 dEndYearTracker.append(x)
    #             if divsTable['interestPaid'].isnull().any():
    #                 dIntPaid.append(x)
    #             if divsTable['totalDivsPaid'].isnull().any():
    #                 dTotalPaid.append(x)
    #             if divsTable['divsPaidPerShare'].isnull().any():
    #                 dSharesPaid.append(x)
    #             if divsTable['shares'].isnull().any():
    #                 dShares.append(x)
                 


    #             # #make lists of years columns, use to track years
    #             ryears = list(roicTable['year'])
    #             ryearsint = []
    #             for a in ryears:
    #                 ryearsint.append(int(a))
    #             rstart, rend = ryearsint[0], ryearsint[-1]
    #             # rMissingYears = sorted(set(range(rstart,rend)) - set(ryearsint))
    #             # if len(rMissingYears) > 0:
    #             #     rMissingYearTracker.append(x)
    #             if rend != 2023:
    #                 rEndYearTracker.append(x)
    #             # if roicTable['TotalEquity'].isnull().any():
    #             #     rTotalEq.append(x)
    #             if roicTable['TotalEquity'].isnull().any():
    #                 if roicTable['ReportedTotalEquity'].isnull().any():
    #                     rTotalEq.append(x)
                
                 
    #         except Exception as err:
    #             print("nested check years integrity error: ")
    #             print(err)
    #             toRecapture.append(x)
    #             continue             


    # except Exception as err:
    #     print("check years integrity error: ")
    #     print(err)

    # finally:
    #     print('recap list: ')
    #     print(toRecapture)
    #     # print('missing income years:')
    #     # print(incMissingYearTracker)
    #     print('wrong income end year')
    #     print(incomeEndYearTracker)
    #     print('missing income revenue')
    #     print(incRev)
    #     print('missing income netIncome')
    #     print(incNetInc)
    #     print('missing income opCF')
    #     print(incOpCF)
    #     print('missing income capEx')
    #     print(incCapEx)
    #     print('missing income netCF')
    #     print(incNetCF)
    #     print('missing income depreNAmor')
    #     print(incDepnAmor)
    #     print('missing income prop sales')
    #     print(incGainProp)
    #     # print('missing div years:')
    #     # print(dMissingYearTracker)
    #     print('wrong div end year')
    #     print(dEndYearTracker)
    #     print('missing div intPaid')
    #     print(dIntPaid)
    #     print('missing div totalPaid')
    #     print(dTotalPaid)
    #     print('missingDivSharesPaid = ')
    #     print(dSharesPaid)
    #     print('missing div shares')
    #     print(dShares)
    #     # print('missing roic years:')
    #     # print(rMissingYearTracker)
    #     print('wrong roic end year')
    #     print(rEndYearTracker)
    #     print('missing roic total equity')
    #     print(rTotalEq)
        
# Returns organized data pertaining to the tag(s) provided in form of DF, but from API, for DB, instead of from CSV
def cSADB(df, tagList):
    try:
        # print('taglist')
        # print(tagList)
        #get csv to df from params
        filtered_data = df#csv.simple_get_df_from_csv(stock_data, ticker + '_Master_' + year + '_V' + version, indexFlag)
        # print(filtered_data)
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            
            held_data = filtered_data[filtered_data['Tag'].eq(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
            # print(x)
            # if 'PerShare' in x:
            #     print('in consolidate')
            #     print(returned_data)
        # print(returned_data['Tag'].unique())
        # print(returned_data)
        returned_data = get_Only_10k_info(returned_data)
        # print('10k data')
        # print(returned_data)
        # print(returned_data.shape)
        
        # print('pre drop fy records')
        # print(returned_data)#.to_string())
        # print(returned_data.shape)
        # print(returned_data['Tag'].unique())
        # print(returned_data['start'].min())
        # print(returned_data['end'].min())
        
        returned_data = dropAllExceptFYRecords(returned_data) #was held data
        # print('post drop fy records pre order')
        # print(returned_data)#.to_string())
        # print(returned_data.shape)
        returned_data = orderAttributeDF(returned_data) #moved from above fy records. so we gather 10k, all fy, then order then drop dupes
        # print('post order pre drop  dupes')
        # print(returned_data.to_string())
        # print(returned_data.shape)

        returned_data = dropDuplicatesInDF(returned_data) #added after filtering for FY only
        # print('post drop  dupes')
        # print(returned_data)
        # print(returned_data.shape)


        returned_data = dropUselessColumns(returned_data)
        
        # print('consolidate all drops done')
        # print(returned_data)

        # csv.simple_saveDF_to_csv('./sec_related/stocks/',held_data, ticker+'_'+'dataFilter'+'_V'+outputVersion,False)
        # csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_' + year + '_' + outputName,False)
        # return returned_data

    except Exception as err:
        print("consolidate single attr error: ")
        print(err)
    finally:
        return returned_data

def mCTEDB(df, ticker):
    try:
        ### INCOME TABLE START
        rev_df = cleanRevenue(cSADB(df, revenue))
        # print('rev')
        # print(rev_df)
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
        # print('gainSaleProp_df: ')
        # print(gainSaleProp_df)
        
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        # print('revNinc: ')
        # print(revNinc)
        revNinc = pd.merge(revNinc, netIncNCI_df, on=['year','Ticker','CIK','Units'], how='outer') 
        # print('revNinc: ')
        # print(revNinc)
        if eps_df.empty:
            revNinc['reportedEPS'] = np.NaN
            revNinc['reportedEPSGrowthRate'] = np.NaN
        else:
            revNinc = pd.merge(revNinc, eps_df, on=['year','Ticker','CIK'], how='outer')
        # revNinc['units'] = revNinc['Units_x']
        # revNinc = revNinc.drop(columns=['Units_x', 'Units_y'])
        # print('revNinc: ')
        # print(revNinc)
        plusopcf = pd.merge(revNinc, opcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusopcf = plusopcf.drop(columns=['units'])
        # print('plusopcf: ')
        # print(plusopcf)
        plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusinvcf['units'] = plusinvcf['Units_x']
        # plusinvcf = plusinvcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusinvcf: ')
        # print(plusinvcf)
        plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusfincf = plusfincf.drop(columns=['units'])
        # print('plusfincf: ')
        # print(plusfincf)

        plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # plusnetcf['units'] = plusnetcf['Units_x']
        # plusnetcf = plusnetcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusnetcf: ')
        # print(plusnetcf)

        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # pluscapex = pluscapex.drop(columns=['units'])
        # print('pluscapex: ')
        # print(pluscapex)

        plusDepAmor = pd.merge(pluscapex, depAmor_df, on=['year','Ticker','CIK','Units'], how='outer') #Testing joining on Units 'start','end',
        # print('plusDepAmor: ')
        # print(plusDepAmor)
        # plusDepAmor = pluseps.drop(columns=['Units_x', 'Units_y'])
        
        plusSaleProp = pd.merge(plusDepAmor, gainSaleProp_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
        # print('plusSaleProp: ')
        # print(plusSaleProp['investingCashFlow'])
        # print(plusSaleProp['investingCashFlowGrowthRate'])

        plusSaleProp = fillUnits(plusSaleProp)
        # print('income table')
        # print(plusSaleProp)
        ### INCOME TABLE END

        ### DIVS TABLE START
        intPaid_df = cleanInterestPaid(cSADB(df, interestPaid))
        # print('intpaid: ')
        # print(intPaid_df)
        divs_df = cleanDividends(cSADB(df, totalCommonStockDivsPaid), 
                                    cSADB(df, declaredORPaidCommonStockDivsPerShare),
                                    cSADB(df, basicSharesOutstanding),
                                    cSADB(df, dilutedSharesOutstanding),
                                    cSADB(df, returnOfCapitalPerShare),
                                    cSADB(df, totalReturnOfCapital))
        # print('divsdf con: ')
        # print(divs_df)
        # if divs_df['year'][0] == -1:
        #     df_dunce = pd.DataFrame(columns=['Ticker'])
        #     df_dunce.loc[0, 'Ticker'] = ticker
        #     csv.simple_appendTo_csv(fr_iC_toSEC, df_dunce,'z-divDataReallyNotFound', False)
        #     return 'No Good Dividend Data'
        # else:
            # intNshares = pd.merge(intPaid_df, shares_df, on=['year','start','end','Ticker','CIK'], how='outer')
        if 'Units' not in divs_df:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')
        elif divs_df['Units'].isnull().any():
            # print('divs df had empty units')
            divs_df = divs_df.drop(columns=['Units'])
            # print('did divsdf drop units?!?!: ')
            # print(divs_df)
            # if divs_df['start'].isnull().any():
            #     divs_df = divs_df.drop(columns=['start'])
            #     intNdivs = pd.merge(intPaid_df, divs_df, on=['year', 'end','Ticker','CIK'], how='outer')
            # else:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK'], how='outer')#Was nested in else on row 'start', 'end',
            # print('if intNdivs: ')
            # print(intNdivs)
        else:
            intNdivs = pd.merge(intPaid_df, divs_df, on=['year','Ticker','CIK','Units'], how='outer')
        

        #     print('else intNdivs: ')
        # print(intNdivs)
        # print('post ifelse merge intdivs')
        # print(intNdivs)
        # print('pre fill intndivs con: ')
        # print(intNdivs)
        intNdivs = fillUnits(intNdivs)
        # print('divs table: ')
        # print(intNdivs)
        ### DIVS TABLE END
        
        ### ROIC TABLE START
        opIncome_df = cleanOperatingIncome(cSADB(df, operatingIncome))
        # print('opinc df')
        # print(opIncome_df)
        taxRate_df = cleanTaxRate(cSADB(df, taxRate))
        # print('taxrate df')
        # print(taxRate_df)
        totalDebt_df = cleanDebt(cSADB(df, shortTermDebt), 
                                    cSADB(df, longTermDebt1), cSADB(df, longTermDebt2),
                                    cSADB(df, longTermDebt3), cSADB(df, longTermDebt4))
        # print('TDebt df')
        # print(totalDebt_df)
        totalEquity_df = cleanTotalEquity(cSADB(df, totalAssets), 
                                    cSADB(df, totalLiabilities), cSADB(df, nonCurrentLiabilities),
                                    cSADB(df, currentLiabilities), cSADB(df, nonCurrentAssets),
                                    cSADB(df, currentAssets), cSADB(df, shareHolderEquity))
                                    
        # print('TEquity df')
        # print(totalEquity_df)
        nav_df = cleanNAV(cSADB(df, netAssetValue))
        # print('nav df')
        # print(nav_df)
        # print(nav_df.empty)
        # print(nav_df.isnull().any())

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        opIncNtax['Units'] = opIncNtax['Units'].ffill().bfill()
        # print('opIncNtax')
        # print(opIncNtax)
        if opIncNtax['Units'].isnull().all():
            opIncNtax['Units'] = 'USD'
        # print('opIncNtax')
        # print(opIncNtax)
        
        # if opIncNtax['Units'].isnull().all():
        #     opIncNtax = opIncNtax.drop(columns=['Units'], axis=1)
        #     # print('opincntax df in empty if')
        #     # print(opIncNtaxNinc)
        #     # print(opIncNtax)
        #     opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK'], how='outer')
        #     # print('still in iff post merge')
        #     # print(opIncNtaxNinc)
        # else:

        #     opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        #     opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])

        # print('opincntax df after if')
        # print(opIncNtaxNinc)
        # print(opIncNtax)
        
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        plustDebt['Units'] = plustDebt['Units'].ffill().bfill()
        # print('plusdebt df')
        # print(plustDebt)
        # plustDebt = plustDebt.rename(columns={'start_x': 'start'})
        # plustDebt = plustDebt.drop(['start_y'],axis=1)
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
        # print('plustequity pre first merge')
        # print(plustEquity)
        if nav_df.empty:
            plustEquity['nav'] = np.NaN
            plustEquity['navGrowthRate'] = np.NaN
        else:
            plustEquity = pd.merge(plustEquity, nav_df, on=['year','Ticker','CIK'], how='outer')
        

        # print('plustequity post merge')
        # print(plustEquity)
        # plustEquity = plustEquity.rename(columns={'start_x': 'start'})
        # plustEquity = plustEquity.drop(['start_y'],axis=1)

        # print('plustequity pre fill')
        # print(plustEquity)
        plustEquity = fillUnits(plustEquity)
        # print('plustequity at end')
        # print(plustEquity)
        ### ROIC TABLE END
        
        ###INCOME TABLE IS plusSaleProp
        ###Dividends table is intNdivs
        ###ROIC TABLE is plustEquity
        # print('intNdivs')
        # print(intNdivs)
        # print('plustequity after fill')
        # print(plustEquity)
        if 'Units' not in intNdivs:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK'], how='outer')
        else:
            divsPlusROIC = pd.merge(intNdivs, plustEquity, on=['year','Ticker','CIK','Units'], how='outer')
        # print('pre final merge')
        # print(divsPlusROIC)
        # print('divs n roic con')
        # print(divsPlusROIC)
        # print('pre final merge second df')
        # print(plusSaleProp)
        incDivsROIC = pd.merge(divsPlusROIC, plusSaleProp, on=['year','Ticker','CIK','Units'], how='outer')
        # print('all con')
        # print(incDivsROIC)
        # print('after final merge')
        # print(incDivsROIC)

        incDivsROIC = fillPrice(incDivsROIC)

        incDivsROIC = fillEmptyDivsGrowthRates(incDivsROIC) 
        
        #Finish the Income Table Entries
        incDivsROIC = fillEmptyIncomeGrowthRates(incDivsROIC)

        #moved into above function. fingers crossed!
        # incDivsROIC = incDivsROIC.drop(columns=['depreNAmorGrowthRate'])
        # incDivsROIC = cleanfcf(incDivsROIC)
        # incDivsROIC = cleanfcfMargin(incDivsROIC)
        # # #Clean sales of property
        # incDivsROIC['gainSaleProp'] = incDivsROIC['gainSaleProp'].replace(np.nan,0)
        # incDivsROIC['ffo'] = incDivsROIC['netIncome'] + incDivsROIC['depreNAmor'] - incDivsROIC['gainSaleProp']
        # growthCol = grManualCalc(incDivsROIC['ffo'])
        # incDivsROIC['ffoGrowthRate'] = growthCol

        #Finish the ROIC Table Entries
        incDivsROIC = fillEmptyROICGrowthRates(incDivsROIC)

        incDivsROIC['Sector'] = nameSectorDict[ticker]
        incDivsROIC['Industry'] = nameIndustryDict[ticker]
        #cik = nameCikDict[ticker]

        #moved into above function. fingers crossed!
        # incDivsROIC['nopat'] = incDivsROIC['operatingIncome'] * (1 - incDivsROIC['taxRate'])
        # incDivsROIC['investedCapital'] = incDivsROIC['TotalEquity'] + incDivsROIC['TotalDebt']
        # incDivsROIC['roic'] = incDivsROIC['nopat'] / incDivsROIC['investedCapital'] * 100
        # incDivsROIC['adjRoic'] = incDivsROIC['netIncome'] / incDivsROIC['investedCapital'] * 100
        # incDivsROIC['reportedAdjRoic'] = incDivsROIC['netIncome'] / (incDivsROIC['ReportedTotalEquity'] + incDivsROIC['TotalDebt']) * 100
        # incDivsROIC['calculatedRoce'] = incDivsROIC['netIncome'] / incDivsROIC['TotalEquity'] * 100
        # incDivsROIC['reportedRoce'] = incDivsROIC['netIncome'] / incDivsROIC['ReportedTotalEquity'] * 100

        # return incDivsROIC
    
    except Exception as err:
        print("mCTEDB error: ")
        print(err)
    finally:
        return incDivsROIC


def testIndies(ticker):
    try:
        company_data = EDGAR_query(ticker, header, ultimateTagsList)
        consol_table = mCTEDB(company_data, ticker)
    except Exception as err:
        print("test indies error: ")
        print(err)
    finally:
        for x in consol_table:
            print(x)
        # print(consol_table['Units'])

# testIndies('MSFT')



#########################################################

### LUKE - ToDO
# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm
# Clean code: this includes packages up top, turns out.
# Automate setup of initial ciks, tickers, up top

#---------------------------------------------------------------------
#DB interaction notes
#---------------------------------------------------------------------
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

def write_csvList_to_DB(df):
    try:
        # trackerNum = 0
        errorTickers = []
        for i in df['Ticker']:
            print(i)
            try:
                company_data = EDGAR_query(i, header, ultimateTagsList)
                # print('making big boi table now')
                # revDF = cSADB(company_data, revenue)
                consol_table = mCTEDB(company_data, i)
                # print(consol_table)
                time.sleep(0.1)
                uploadToDB(consol_table)
                print(i + ' uploaded to DB!')
                # trackerNum += 1
                # if trackerNum == 1:
                #     break
            except Exception as err1:
                errorTickers.append(str(i))
                print('write to DB in for loop error for: ' + i)
                print(err1)
                continue
    except Exception as err:
        print("write csvList to DB error: ")
        print(err)
        # continue
    finally:
        print(errorTickers)
    
    # pass

def write_list_to_DB(thelist):
    try:
        errorTickers = []
        for i in thelist:
            print(i)
            try:
                company_data = EDGAR_query(i, header, ultimateTagsList)
                # print('making big boi table now')
                # revDF = cSADB(company_data, revenue)
                consol_table = mCTEDB(company_data, i)
                # print(consol_table)
                time.sleep(0.1)
                uploadToDB(consol_table,'Mega')
                print(i + ' uploaded to DB!')
                # trackerNum += 1
                # if trackerNum == 1:
                #     break
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


# materials = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Basic Materials_Sector_clean', type_converter_full2)
# comms = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Communication Services_Sector_clean', type_converter_full2)
# consCyclical = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Cyclical_Sector_clean', type_converter_full2)
# consStaples = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Defensive_Sector_clean', type_converter_full2)
# energy = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Energy_Sector_clean', type_converter_full2)
# finance = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Financial Services_Sector_clean', type_converter_full2)
# health = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Healthcare_Sector_clean', type_converter_full2)
# ind = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Industrials_Sector_clean', type_converter_full2)
# realEstate = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Real Estate_Sector_clean', type_converter_full2)
# tech = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Technology_Sector_clean', type_converter_full2)
# util = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Utilities_Sector_clean', type_converter_full2)

# utillist = ['CEG', 'OPAL']

# write_list_to_DB(utillist)

# write_csvList_to_DB(consStaples) 

##Tickers mixed Currencies
# stockstorecap = ['ENIC','PAM','CEPU'] #need to manually convert these currencies, unsupported! :)

# for x in stockstorecap:
#     delete_ticker_DB(x)

# write_list_to_DB(stockstorecap)


##DB EXAMPLES THAT WORK

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
    # else:


def checkUnits_DB(ticker):
    conn = sql.connect(db_path)
    query = conn.cursor()
    # del_query = 'SELECT DISTINCT Ticker FROM Mega;'
    # query.execute(del_query)
    # conn.commit()
    df12 = pd.read_sql('SELECT Ticker, Units FROM Mega WHERE Ticker Like \''+ticker+'\';',conn)# WHERE count(DISTINCT Units) > 1 GROUP BY Ticker;', conn)
    print(df12)

    query.close()
    conn.close()

def print_ticker_DB(ticker):
    conn = sql.connect(db_path)
    query = conn.cursor()

    # del_query = 'SELECT * FROM Mega WHERE Ticker = ' + ticker + ';'
    # query.execute(del_query)
    # conn.commit()

    df12 = pd.read_sql('SELECT * FROM Mega WHERE Ticker LIKE \''+ticker+'\';',conn)# WHERE Ticker = ' + ticker + ';', conn)
    print(df12)

    query.close()
    conn.close()

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



# thequery = 'SELECT DISTINCT Ticker as ticker, Year, shares, sharesGrowthRate \
#             FROM Mega \
#             WHERE sharesGrowthRate > 50.0 \
#             AND Sector LIKE \'%Real%\' \
#             ;'
growthratequery = 'SELECT DISTINCT Ticker \
            FROM Mega \
            WHERE sharesGrowthRate > 50.0 \
            AND Sector LIKE \'%Real%\' \
            ;'
# print_DB(thequery,'print')

# (((divsPaidPerShare-calcDivsPerShare)/divsPaidPerShare)*100) as repMinusCalc_diff \

divquery = 'SELECT Ticker, Year, shares, sharesGrowthRate, totalDivsPaid, revenue, netIncome, divsPaidPerShare as divPS, divGrowthRateBORPS as divPSrate, calcDivsPerShare as calcdivPS, divGrowthRateBOCPS as calcdivPSrate, payoutRatio, ffoPayoutRatio \
            FROM Mega \
            WHERE Ticker LIKE \'NEE\' \
            AND Year > \'2006\' \
            ORDER BY Year  \
            ;'
incomequery = 'SELECT Ticker, Year, shares, sharesGrowthRate, revenue, revenueGrowthRate, netIncome, netIncomeGrowthRate, reportedEPS,  calculatedEPS, reportedEPSGrowthRate, calculatedEPSGrowthRate, capEx, capExGrowthRate  \
            FROM Mega \
            WHERE Ticker LIKE \'AMZN\' \
            AND Year > \'2006\'  \
            ORDER BY Year  \
            ;'

# print_DB(divquery,'print')
# print_DB(incomequery, 'print')

sharesquery = 'SELECT sharesGrowthRate \
                FROM Mega \
                WHERE Ticker LIKE \'NEE\' \
                ;'

testlistquery = 'SELECT Year \
                FROM Mega \
                WHERE Ticker LIKE \'NEE\' \
                ;'

def IQR_Mean(list):
    try:
        # cleaned_list = []
        nonechecker = 0
        infchecker = 0
        for x in list:
            if x is None:
                nonechecker += 1
            if x == np.inf:
                infchecker += 1

        if nonechecker == len(list):
            ar_Mean = np.NaN
            return ar_Mean
        if infchecker == len(list):
            ar_Mean = np.NaN
            return ar_Mean
        # if list[0] is None:
        #     # print('nonetype detected, returning something')
        #     # print(list[0])
        #     ar_Mean = np.NaN
        #     return ar_Mean

        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list if not np.isnan(x)]
            cleaned_list = [x for x in cleaned_list if not np.isinf(x)]
            # print('nums cleaning nans')
            # print(cleaned_list)
            # badNumbersMan = [0, 0.0]
            # cleaned_list = [x for x in cleaned_list if x != 0]
            # print(cleaned_list)
            # cleaned_list = [x for x in cleaned_list if x != 0.0]
            # print(cleaned_list)
        elif isinstance(list[0],str):
            cleaned_list = [eval(i) for i in list]
            # print('strings cleaning nans')
            # print(cleaned_list)
        else:
            print('IQR_Mean type was not string or float')

        q1 = np.percentile(cleaned_list, 25)
        q3 = np.percentile(cleaned_list, 75)
        iqr = q3 - q1
        median = np.median(cleaned_list)
        ar_top = median + iqr
        ar_bottom = median - iqr

        # print('q1 q3 iqr artop arbot')
        # print(q1)
        # print(q3)
        # print(iqr)
        # print(ar_top)
        # print(ar_bottom)

        ar_list = []
        for x in cleaned_list:
            if x < ar_top and x > ar_bottom:
                ar_list.append(x)

        # print('final ar list')
        # print(ar_list)
        #When q1=q3, it leaves no mean found, the fix:
        if len(ar_list) == 0:
            ar_Mean = np.mean(cleaned_list)
        else:
            ar_Mean = np.mean(ar_list)
        return ar_Mean
    except Exception as err:
        print("IQR Mean error: ")
        print(err)
    # finally:
    #     return ar_Mean

def IQR_MeanNZ(list):
    try:
        nonechecker = 0
        infchecker = 0
        for x in list:
            if x is None:
                nonechecker += 1
            if x == np.inf:
                infchecker += 1
        # print('none checker then inf checker')
        # print(nonechecker)
        # print(infchecker)        
        if nonechecker == len(list):
            ar_Mean = np.NaN
            return ar_Mean
        if infchecker == len(list):
            ar_Mean = np.NaN
            return ar_Mean
        # print(list)
        
        # if list[0] is None:
        #     # print('nonetype detected, returning something')
        #     # print(list[0])
        #     ar_Mean = np.NaN
        #     return ar_Mean
        if isinstance(list[0], float) or isinstance(list[0], int):
            cleaned_list = [x for x in list if not np.isnan(x)]
            # print('clean list no nans')
            # print(cleaned_list)
            cleaned_list = [x for x in cleaned_list if not np.isinf(x)]
            # print('nums cleaning infs')
            # print(cleaned_list)
            # badNumbersMan = [0, 0.0]
            cleaned_list = [x for x in cleaned_list if x != 0]
            # print('final cleaned list no zeroes')

            # print(cleaned_list)
            if len(cleaned_list) == 0:
                return np.NaN
            # print(cleaned_list)
            # cleaned_list = [x for x in cleaned_list if x != 0.0]
            # print(cleaned_list)
        elif isinstance(list[0], str):
            cleaned_list = [eval(i) for i in list]
            # print('strings cleaning nans')
            # print(cleaned_list)
        else:
            print('IQR_Mean nz type was not string or float')

        # print('final cleaned list')
        # print(cleaned_list)
        q1 = np.percentile(cleaned_list, 25)
        q3 = np.percentile(cleaned_list, 75)
        iqr = q3 - q1
        median = np.median(cleaned_list)
        ar_top = median + iqr
        ar_bottom = median - iqr

        # print('q1 q3 iqr artop arbot')
        # print(q1)
        # print(q3)
        # print(iqr)
        # print(ar_top)
        # print(ar_bottom)

        ar_list = []
        for x in cleaned_list:
            if x < ar_top and x > ar_bottom:
                ar_list.append(x)

        # print('final ar list')
        # print(ar_list)
        #When q1=q3, it leaves no mean found, the fix:
        if len(ar_list) == 0:
            # print('did filter it all to zero?')
            ar_Mean = np.mean(cleaned_list)
        else:
            ar_Mean = np.mean(ar_list)
        return ar_Mean
    except Exception as err:
        print("IQR Mean nz error: ")
        print(err)

def nan_strip_min(list):
    try:
        cleaned_list = []
        # print('strip min test length')
        # print(len(list))
        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list if not np.isnan(x)]
            ar_Min = np.min(cleaned_list)
        elif isinstance(list[0], str):# == <class 'str'>:
            cleaned_list = [eval(i) for i in list]
            ar_Min = np.min(cleaned_list)
        elif list[0] is None:
            # print('nonetype detected, returning something')
            # print(list[0])
            ar_Min = np.NaN
            # for x in range(len(list)):
                # cleaned_list[x] = np.NaN
            # cleaned_list = -1
            # print(list)
            # print(cleaned_list)
        else:
            print('strip Min type was not int, float or none')
            # print(type(list[0]))
            # print(list)

        # print('pre ar min')

        # ar_Min = np.min(cleaned_list)
        # print(ar_Min)
        # print('post ar min')
    except Exception as err:
        print("strip Min error: ")
        print(err)
    finally:
        return ar_Min

def nan_strip_max(list):
    try:
        cleaned_list = []
        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list if not np.isnan(x)]
            ar_Max = np.max(cleaned_list)
        elif isinstance(list[0],str):# == <class 'str'>:
            cleaned_list = [eval(i) for i in list]
            ar_Max = np.max(cleaned_list)
        elif list[0] is None:
            # print('nonetype detected, returning something')
            # print(list[0])
            ar_Max = np.NaN
        else:
            print('strip Max type was not int or float')

        
        # ar_Max = np.max(cleaned_list)
    except Exception as err:
        print("strip Max error: ")
        print(err)
    finally:
        return ar_Max

def nan_strip_count(list):
    try:
        cleaned_list = []
        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list if not np.isnan(x)]
        elif isinstance(list[0],str):# == <class 'str'>:
            cleaned_list = [eval(i) for i in list]
        else:
            print('strip count type was not int or float')

        # print(cleaned_list)
        ar_count = len(cleaned_list)
    except Exception as err:
        print("strip count error: ")
        print(err)
    finally:
        return ar_count

def nan_strip_list(list):
    try:
        cleaned_list = []
        if isinstance(list[0],float) or isinstance(list[0],int):
            cleaned_list = [x for x in list if not np.isnan(x)]
        elif isinstance(list[0],str):# == <class 'str'>:
            cleaned_list = [eval(i) for i in list]
        else:
            print('strip count type was not int or float')

        # print(cleaned_list)
        # ar_count = len(cleaned_list)
    except Exception as err:
        print("strip list error: ")
        print(err)
    finally:
        return cleaned_list

def count_nonzeroes(list):
    try:
        cleaned_list = [n for n in list if n != 0]
        # if isinstance(list[0],float) or isinstance(list[0],int):
        #     cleaned_list = [x for x in list if not np.isnan(x)]
        # elif isinstance(list[0],str):# == <class 'str'>:
        #     cleaned_list = [eval(i) for i in list]
        # else:
        #     print('strip count type was not int or float')
        # for x in cleaned_list:
        #     print(cleaned_list)
        #     # if x in (0, 0.0, '0', '0.0'):
        #     #     cleaned_list.remove(x)
        #     #     print(cleaned_list)
        #     if x == 0:
        #         cleaned_list.remove(x)
        #     if x == 0.0:
        #         cleaned_list.remove(x)
        #     if x == '0':
        #         cleaned_list.remove(x)
        #     if x == '0.0':
        #         cleaned_list.remove(x)
        #     print(cleaned_list)
        # for x in cleaned_list:
        #     print(type(x))
        # print(list)
        
        ar_count = len(cleaned_list)
    except Exception as err:
        print("nonzero count error: ")
        print(err)
    finally:
        return ar_count

def zeroIntegrity(list1):
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

        #now solve empty/nan list returning 'good'
        newlistdf = pd.DataFrame()
        newlistdf['test'] = list1
        newlistdf = newlistdf.replace([np.inf, -np.inf], np.NaN)
        newlist = newlistdf['test'].dropna()#.tolist()
        if len(newlist) == 0:
            integrityFlag = 'emptyAVG'

        # if numnans == len(list1):
        #     integrityFlag = 'emptyAVG'
        
        # checknan = numnans / len(list1)
        # if numnans > 0:
        #     print('we counting nans bro')
        # if numzeroes > 0:
        #     print('we counting zeroes')
        # print('len list, numnans:')
        # print(len(list1))
        # print(numnans)
        # for x in list1:
        #     if np.isinf(x):
        #         print('found an inf!')

        # if checknan == 1:
        #     integrityFlag = 'all NaNs'
    except Exception as err:
        print('zero integrity error: ')
        print(err)
    finally:
        return integrityFlag


def income_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, revenue, revenueGrowthRate, netIncome, netIncomeGrowthRate, netIncomeNCI, netIncomeNCIGrowthRate, ffo, ffoGrowthRate, \
                        reportedEPS, reportedEPSGrowthRate, calculatedEPS, calculatedEPSGrowthRate, reitEPS, reitEPSGrowthRate, \
                        fcf, fcfGrowthRate, fcfMargin, fcfMarginGrowthRate, \
                        price, priceGrowthRAte \
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
        thequery = 'SELECT Ticker, Sector, Industry, Year, shares, sharesGrowthRate, dilutedShares, dilutedSharesGrowthRate, totalDivsPaid, \
                        divsPaidPerShare, calcDivsPerShare, divGrowthRateBOT, divGrowthRateBORPS, divGrowthRateBOCPS, payoutRatio, \
                        fcfPayoutRatio, ffoPayoutRatio, ROCTotal, ROCperShare, ROCperShareGrowthRate, ROCTotalGrowthRate \
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

def efficiency_reading(ticker):
    try:
        conn = sql.connect(db_path)
        query = conn.cursor()
        thequery = 'SELECT Ticker, Sector, Industry, Year, operatingIncome, operatingIncomeGrowthRate, taxRate, nopat, investedCapital, \
                        roic, adjRoic, reportedAdjRoic, calculatedRoce, reportedRoce, calcBookValue, calcBookValueGrowthRate, \
                        reportedBookValue, reportedBookValueGrowthRate, nav, navGrowthRate \
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
        revavg = IQR_Mean(revlist)
        revavgnz = IQR_MeanNZ(revlist)
        revavginteg = zeroIntegrity(revlist)

        metadata['revGrowthAVG'] = revavg
        metadata['revGrowthAVGintegrity'] = revavginteg
        metadata['revGrowthAVGnz'] = revavgnz

        #netincome x2, gr's min, max, avg
        netinclist = incomedf['netIncome'].tolist()
        # print('pre min net income')
        nimin = nan_strip_min(netinclist)
        # nimax = nan_strip_max(netinclist)
        # niavg = IQR_Mean(netinclist)

        netincgrlist = incomedf['netIncomeGrowthRate'].tolist()
        # nigrmin = nan_strip_min(netincgrlist)
        # nigrmax = nan_strip_max(netincgrlist)
        nigravg = IQR_Mean(netincgrlist)
        nigravgnz = IQR_MeanNZ(netincgrlist)
        nigravgint = zeroIntegrity(netincgrlist)

        netincNCIlist = incomedf['netIncomeNCI'].tolist()
        # print('pre min net income NCI')
        # print(netincNCIlist)
        # print(netincNCIlist[0])
        # print(type(netincNCIlist[0]))
        # print(type(netincNCIlist[0]) is None)
        nincimin = nan_strip_min(netincNCIlist)
        # nincimax = nan_strip_max(netincNCIlist)
        # ninciavg = IQR_Mean(netincNCIlist)

        netincNCIgrlist = incomedf['netIncomeNCIGrowthRate'].tolist()
        # nincigrmin = nan_strip_min(netincNCIgrlist)
        # nincigrmax = nan_strip_max(netincNCIgrlist)
        nincigravg = IQR_Mean(netincNCIgrlist)
        nincigravgnz = IQR_MeanNZ(netincNCIgrlist)
        nincigrint = zeroIntegrity(netincNCIgrlist)

        metadata['netIncomeLow'] = nimin
        metadata['netIncomeGrowthAVG'] = nigravg
        metadata['netIncomeGrowthAVGintegrity'] = nigravgint
        metadata['netIncomeGrowthAVGnz'] = nigravgnz

        metadata['netIncomeNCILow'] = nincimin
        metadata['netIncomeNCIGrowthAVG'] = nincigravg
        metadata['netIncomeNCIGrowthAVGintegrity'] = nincigrint
        metadata['netIncomeNCIGrowthAVGnz'] = nincigravgnz

        # print(metadata['netIncomeNCILow'])
        # print( metadata['netIncomeNCIGrowthAVG'] )

        #ffo gr's min, max, avg
        ffolist = incomedf['ffo'].tolist()
        ffomin = nan_strip_min(ffolist)
        # ffomax = nan_strip_max(ffolist)
        # ffoavg = IQR_Mean(ffolist)

        ffogrlist = incomedf['ffoGrowthRate'].tolist()
        # ffogrmin = nan_strip_min(ffogrlist)
        # ffogrmax = nan_strip_max(ffogrlist)
        ffogravg = IQR_Mean(ffogrlist)
        ffogravgnz = IQR_MeanNZ(ffogrlist)
        ffogravgint = zeroIntegrity(ffogrlist)

        metadata['ffoLow'] = ffomin
        metadata['ffoGrowthAVG'] = ffogravg
        metadata['ffoGrowthAVGintegrity'] = ffogravgint
        metadata['ffoGrowthAVGnz'] = ffogravgnz

        # reportedEPS, 
        repslist = incomedf['reportedEPS'].tolist()
        repsmin = nan_strip_min(repslist)
        repsavg = IQR_Mean(repslist)
        repsavgint = zeroIntegrity(repslist)
        repsavgnz = IQR_MeanNZ(repslist)

        metadata['repsLow'] = repsmin
        metadata['repsAVG'] = repsavg
        metadata['repsAVGintegrity'] = repsavgint
        metadata['repsAVGnz'] = repsavgnz
        
        #reportedEPSGrowthRate, 
        repsgrlist = incomedf['reportedEPSGrowthRate'].tolist()
        # repsgrmin = nan_strip_min(repsgrlist)
        repsgravg = IQR_Mean(repsgrlist)
        repsgrint = zeroIntegrity(repsgrlist)
        repsgravgnz = IQR_MeanNZ(repsgrlist)

        metadata['repsGrowthAVG'] = repsgravg
        metadata['repsGrowthAVGintegrity'] = repsgrint
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
        dshareslist = divdf['dilutedSharesGrowthRate'].tolist()
        # dsharesmin = nan_strip_min(dshareslist)
        # dsharesmax = nan_strip_max(dshareslist)
        dsharesavg = IQR_Mean(dshareslist)

        metadata['dilutedSharesGrowthAVG'] = dsharesavg

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

        # print('type of none isn an?')
        # print(pd.isnull(cdpslatest))
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

def fillMetadata(sector):

    tickerq = 'SELECT DISTINCT Ticker \
                FROM Mega \
                WHERE Sector LIKE \'' + sector + '\''
    # print(print_DB(tickerq, 'return')['Ticker'])
    tickerfetch = print_DB(tickerq, 'return')['Ticker']
    for x in tickerfetch:
        print('Working on ' + x)
        faTable = full_analysis(income_reading(x), balanceSheet_reading(x), cashFlow_reading(x), dividend_reading(x), efficiency_reading(x))
        print('Table made for: ' + x)
        # print(faTable)
        uploadToDB(faTable,'Metadata')


# time1 = time.time()
# time2 = time.time()
# print('time to complete')
# print((time2-time1)*1000)

# fillMetadata('Utilities')

# 0                Utilities
# 1          Basic Materials
# 2   Communication Services
# 3        Consumer Cyclical
# 4               Technology
# 5              Real Estate
# 6              Industrials
# 7               Healthcare
# 8       Financial Services
# 9                   Energy
# 10      Consumer Defensive




#luke here  Ticker, Sector, Industry, Year,
#two sets of filters: sector leaders, and individual stock reports. 
#individual stock reports: go thru each section below. RATING each section as 5=amazing, 4=good, 3=acceptable, 2=subpar, 1=bad

#sector rankings have to provide each of the following, then calculate a weighted score, grading each stock in each sector
##so out of 5: 5=amazing, 4=good, 3=acceptable, 2=subpar, 1=bad
##then that score is multiplied by a weighting factor based on the user's preferences, or preset screens. (grade)(weighting) = overall score

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
        elif avg > 0 and avg <= 2:
            finalrating = 1
        elif avg > 2 and avg <= 4:
            finalrating = 2
        elif avg > 4 and avg <= 7:
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
        elif avg > 0 and avg <= 2:
            finalrating = 1
        elif avg > 2 and avg <= 4:
            finalrating = 2
        elif avg > 4 and avg <= 7:
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
        
        rulecompare = [10, 7, 4, 2, 0, -1, -2, -3, -4]
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
        #sort avg
        if resultsdf['fcfmint'][0] in ('good','decent'):
            netincomeavg = resultsdf['fcfmgravg'][0]
        else:
            netincomeavg = resultsdf['fcfmgravgnz'][0]
        
        if pd.isnull(resultsdf['fcfmavg'][0]) == False and np.isinf(resultsdf['fcfmavg'][0]) == False:      
            fcfmaverage = resultsdf['fcfmavg'][0]
        else:
            fcfmaverage = 1

        fcfmrulecompare = [20, 10, 5, 2, 0, -1, -2, -3, -4]
        fcfmfinalrating = rating_assignment(fcfmaverage,fcfmrulecompare)

        #determine avg
        if pd.isnull(netincomeavg) == False and np.isinf(netincomeavg) == False:      
            avg = netincomeavg
        else:
            avg = 1
        
        rulecompare = [10, 7, 4, 2, 0, -1, -2, -3, -4]
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
        #sort avg
        # if resultsdf['fcfmint'][0] in ('good','decent'):
        #     netincomeavg = resultsdf['fcfmgravg'][0]
        # else:
        #     netincomeavg = resultsdf['fcfmgravgnz'][0]
        
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
        
        if pd.isnull(resultsdf['rgravg'][0]) == False and np.isinf(resultsdf['rgravg'][0]) == False and pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:      
            reqavg = max(resultsdf['rgravg'][0], resultsdf['rgravgnz'][0])
        elif pd.isnull(resultsdf['rgravg'][0]) == True or np.isinf(resultsdf['rgravg'][0]) == True:
            if pd.isnull(resultsdf['rgravgnz'][0]) == False and np.isinf(resultsdf['rgravgnz'][0]) == False:
                reqavg = resultsdf['rgravgnz'][0]
            else:
                reqavg = 0
        
        rrulecompare = [10,5,1,0,-1,-2,-3,-4,-5]
        rfinalrating = rating_assignment(reqavg,rrulecompare)

        if pd.isnull(resultsdf['cgravg'][0]) == False and np.isinf(resultsdf['cgravg'][0]) == False and pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:      
            ceqavg = max(resultsdf['cgravg'][0], resultsdf['cgravgnz'][0])
        elif pd.isnull(resultsdf['cgravg'][0]) == True or np.isinf(resultsdf['cgravg'][0]) == True:
            if pd.isnull(resultsdf['cgravgnz'][0]) == False and np.isinf(resultsdf['cgravgnz'][0]) == False:
                ceqavg = resultsdf['cgravgnz'][0]
            else:
                ceqavg = 0
        
        rulecompare = [10,5,1,0,-1,-2,-3,-4,-5]
        cfinalrating = rating_assignment(ceqavg, rulecompare)

        finalrating = math.floor((rfinalrating + cfinalrating) / 2)
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
            navcompare = [10,5,1,0,-1,-2,-3,-4,-5]
            navrating = rating_assignment(resultsdf['navgravg'][0], navcompare)
            rulecompare = [10,5,1,0,-1,-2,-3,-4,-5]
            cfinalrating = rating_assignment(avg, rulecompare)
            finalrating = math.floor((navrating + cfinalrating) / 2)
        else:
            rulecompare = [10,5,1,0,-1,-2,-3,-4,-5]
            cfinalrating = rating_assignment(avg, rulecompare)
            finalrating = cfinalrating
    except Exception as err:
        print('book value rating error:')
        print(err)
    finally:
        return finalrating

# print(bvnav_rating('PLTR'))

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

# print(cf_rating('BUD'))

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

# print(divspaid_rating('MSFT'))

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
            elif calcdivs < 15 and calcdivs >= 12:
                cdivsrating = 4
            elif calcdivs < 12 and calcdivs >= 7:
                cdivsrating = 3
            elif calcdivs < 7 and calcdivs >= 3:
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
            elif repdivs < 15 and repdivs >= 12:
                rdivsrating = 4
            elif repdivs < 12 and repdivs >= 7:
                rdivsrating = 3
            elif repdivs < 7 and repdivs >= 3:
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

# print(divgrowth_rating('HD'))

def payout_rating(ticker): 
    try:
        sqlq = 'SELECT payoutRatioAVG as pra, payoutRatioAVGintegrity as praint, payoutRatioAVGnz as pranz, \
                    fcfPayoutRatioAVG as fcfa, fcfPayoutRatioAVGintegrity as fcfaint, fcfPayoutRatioAVGnz as fcfanz \
                    FROM Metadata \
                    WHERE Ticker LIKE \'' + ticker + '\';'
        resultsdf = print_DB(sqlq, 'return')
        # print(resultsdf)
       
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

        finalrating = math.floor((fdivsrating + cdivsrating) / 2)
    except Exception as err:
        print('payout rating error:')
        print(err)
    finally:
        return finalrating

# print(payout_rating('O'))

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
        roiccompare = [20,15,7,5,1,0,-1,-5,-7]
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
        roiccompare = [25,15,10,5,1,0,-1,-5,-10]
        finalrating = rating_assignment(finalroic,roiccompare)
    except Exception as err:
        print('roce rating error:')
        print(err)
    finally:
        return finalrating

# print(roce_rating('O'))

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
# rank_ConsumerCyclical() #luke do this, check 3 custom tables, update models, fill 3 tables, 

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
                # uploadToDB(uploaddf,'Growth_Ranking')

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
        #avg(ffopo),
        # avgpull = 'SELECT avg(roce), avg(roic), avg(po), avg(divgr), avg(divpay), avg(shares), avg(cf), avg(bv), avg(equity), avg(debt), \
        #                 avg(fcfm), avg(fcf), avg(ffo), avg(ni), avg(rev), avg(divyield), avg(score) FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\''
        avgpull = 'SELECT avg(score) as avg, max(score), min(score) FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\''
        avgdf = print_DB(avgpull, 'return')
        # print(avgdf)
        avg = avgdf['avg'][0]
        invUni = 'SELECT * FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\' AND score >= ' + str(avg) + ' ORDER BY score DESC'
        invUnidf = print_DB(invUni, 'return')
        # print(invUnidf['Ticker'])

        # invUni2 = 'SELECT * FROM Sector_Rankings WHERE Sector LIKE \'' + sector + '\' AND score < ' + str(avg) + ' ORDER BY score DESC'
        # invUnidf2 = print_DB(invUni2, 'print')
                    
        
    except Exception as err:
        print('investable uni error: ')
        print(err)
    finally:
        # name = 'z-InvUni-' + sector
        # csv.simple_saveDF_to_csv('', invUnidf, name, False)
        return invUnidf

# investableUniverse('E')

#############################################################################
#luke here we start filling investable universe from notes sheet
#############################################################################
#luke here editing these don't forget to add the column/type: Type , indicating 'divs' or 'growth'
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
        # 1    ECL     18   4.490953   9.545361        0.337469    2.669091e+07          1.723550e+09   6.456562   9.394432  16.869523  16.797879
        # 2   BCPC     16   7.303757   8.769953        0.188848    1.968275e+07          1.068192e+08  12.840403  11.620022  10.711269  12.414149
        # 3   STLD     18   4.563829   4.415330        0.207457    1.110677e+08          7.234860e+08   8.801051  11.681113   7.843229  14.992343
        # 4   UFPI     16  13.809333  25.466438        0.169407    6.471333e+06          1.308264e+08  11.629191  11.687335   9.462612  10.677567
        # 5     RS     17   5.015402   3.829977        0.178590    1.103483e+07          6.411757e+08   9.418193  17.718853   9.121950  12.131660
        # 6   TGLS     13  14.174309   3.522493        0.066999    1.095124e+07          1.121103e+07  20.649606  35.979257   8.178108  22.319511
        

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
                    AND years >= 5 \
                    AND revGrowthAVG >= 5 \
                    AND netIncomeGrowthAVG >= 1 \
                    AND divgr >= 5 \
                    AND payoutRatioAVG <= 0.7 \
                    AND equity >= 5 \
                    AND operatingCashFlowAVG > 0 \
                    AND netCashFlowAVG > 0 \
                    AND roic > 10 \
                    AND roce > 10 \
                    ORDER BY divgr;'

                    #screening targets
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  netCashFlowAVG  operatingCashFlowAVG     equity       divgr       roic       roce
                    # 0   META     14  47.335342  37.976751        0.000000    1.533636e+08          1.840508e+10  24.041229         NaN  17.842301  17.869286
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
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, operatingCashFlowAVG, netCashFlowAVG, \
                    CASE WHEN reportedEquityGrowthAVG > calculatedEquityGrowthAVG THEN reportedEquityGrowthAVG ELSE calculatedEquityGrowthAVG END equity, \
                    CASE WHEN repDivsPerShareGrowthAVG > calcDivsPerShareGrowthAVG THEN repDivsPerShareGrowthAVG ELSE calcDivsPerShareGrowthAVG END divgr, \
                    CASE WHEN aroicAVG > raroicAVG THEN aroicAVG  ELSE raroicAVG END roic, \
                    CASE WHEN croceAVG > rroceAVG THEN croceAVG ELSE rroceAVG END roce \
                    FROM Metadata \
                    WHERE Sector LIKE \'Energy\' \
                    AND years >= 10 \
                    AND divgr >= 4 \
                    AND payoutRatioAVG <= 0.9 \
                    AND operatingCashFlowAVG > 0 \
                    AND equity >= 2 \
                    AND roic > 15 \
                    AND roce > 15 \
                    ORDER BY Ticker;'

                    #unneeded screens
                    #  divgr <= 30 \
                    # AND netCashFlowAVG > 0 \
                    # AND revGrowthAVG >= 0 \
                    # AND netIncomeGrowthAVG >= 0 \
                    #initial
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG    equity      divgr       roic       roce
                    # 0    CVX     17  -4.591927 -15.175337        0.383902          2.960193e+10   -1.147769e+09  5.912741   6.242237  11.466649  12.525441
                    # 1    EOG     18  29.641039  -0.779903        0.099695          5.260627e+09    3.922576e+08       NaN  14.501993  10.553666  14.424227
                    # 2    PSX     15  -2.271819 -15.748739        0.158731          4.845786e+09   -1.333333e+07  0.684323  12.609659  17.878898  17.992002
                    # 3    XOM     18   1.681971 -10.319898        0.377031          4.357575e+10   -1.946154e+08  2.361327   4.630759  17.360837  17.890969
                    #screen
                    #   Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity       divgr       roic       roce
                    # 0   ARLP     16   6.387910  13.179572        0.148237          5.926950e+08   -2.178444e+07   9.860818   17.060478  23.576827  36.690378
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
                    # 0       V     18  11.782065  13.951760        0.192225          6.205125e+09    1.566154e+08        NaN   5.271089        NaN  19.211963  19.534281
                    # 1      MS     18   0.000000  -0.148192        0.284637          5.225062e+09    2.008750e+09   3.473520   3.626883  17.606352   6.349572   7.802749
                    # 2      MA     18  12.455496   0.000000        0.220132          4.195150e+09    8.645765e+08   4.536454   5.868946  14.512999  29.242511  45.672711
                    # 3     BLK     18  -0.007121   7.135477        0.439311          3.104143e+09    5.544615e+08   5.248478   3.454758  12.865347  11.986603  11.986603
                    # 4     JPM     17   2.600539   9.381052        0.321679          3.194575e+10    2.878083e+09   6.084620   3.909434  11.572023  10.508470  10.508470
                    # 5      GS     17        NaN -18.160193        0.205881          5.585571e+09    7.563500e+09   7.144024   5.992205  17.568776   4.195360   9.492229
                    # 6     AXP     18   0.897985   1.415459        0.199070          9.634600e+09    3.587000e+09   7.263925   3.431624  10.370913  27.296490  27.296490
                    # 7    TROW     18   0.345987  15.226549        0.439817          1.159050e+09    1.220083e+08  10.941966  11.569203  11.910636  23.768405  23.768405
                    # 8     DFS     18        NaN   1.585452        0.154129          4.362713e+09    1.179338e+09  12.256109   3.520530  16.556411  21.258176  21.258176
                    # 9    SCHW     18   9.540676  12.822463        0.298110          1.630538e+09    3.536214e+09  13.980383  14.609661   8.050996  11.682316  11.682316
                    # 10   SPGI     18   6.269991   2.639047        0.289784          1.512441e+09    3.451868e+08  17.193617  14.629222  10.265943  36.527934  80.101654
                    # 11   MSCI     17   9.260249  16.239868        0.212577          3.845744e+08    3.945708e+07  23.110777  15.839196  26.991692  13.766375   5.756975
                    #used screen
                    #  Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG         bv     equity      divgr       roic       roce
                    # 1       V     18  11.782065  13.951760        0.192225          6.205125e+09    1.566154e+08        NaN   5.271089  17.626413  19.211963  19.534281
                    # 68    DFS     18        NaN   1.585452        0.154129          4.362713e+09    1.179338e+09  12.256109   3.520530  16.556411  21.258176  21.258176
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
# jpm = 'SELECT calcBookValueAVG, calcBookValueGrowthAVG, repBookValueAVG, repBookValueGrowthAVG FROM Metadata WHERE Ticker LIKE \'V\''
# jpmdf = print_DB(jpm, 'print')
# for x in jpmdf:
#     print(x)
#     print(jpmdf[x])

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
            # 4    RSG     18   3.193927  -0.021190        0.536223          1.807783e+09    8.092857e+06        NaN   7.759505  10.563221  10.672990
            # 5    NOC     17   2.920955   1.109682        0.273852          2.833867e+09    1.491538e+08  10.567245   9.593496  16.809136  26.058515
            # 6     GD     18   1.869071   1.631721        0.287132          3.173385e+09    1.496923e+08   6.568281  10.146197  15.065814  19.992949
            # 7    LMT     18   1.926400   4.113817        0.441893          5.247824e+09    3.023529e+07  -7.412228  10.500326  33.664914  99.229021
            # 8     DE     18  10.104561   9.981592        0.248744          2.778964e+09   -4.218182e+06   5.977654  11.622701   8.459864  30.365365
            #run
            # Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity      divgr       roic       roce
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
                    ORDER BY operatingCashFlowAVG;'

        #  AND revGrowthAVG >= 4 \
        
        # init
        #   Ticker  years      revgr       nigr  payoutRatioAVG  operatingCashFlowAVG  netCashFlowAVG     equity       divgr       roic       roce
        # 0    AAPL     18   8.816089   6.581789        0.161836          5.399888e+10    2.430786e+09  -0.684364    8.732056  29.872809  36.495287
        # 1     ACN     17   3.695180  13.231359        0.395505          4.800244e+09    5.457945e+08  15.989917   10.730739  41.955634  43.043044
        # 2     ADI     17   5.889502   5.084997        0.627590          1.079013e+09    1.221677e+08   5.522134    9.542130  12.019164  12.163146
        # 3    AMAT     18   7.088549  34.033102        0.230050          2.361674e+09    3.620124e+08   1.287084    8.403995  20.089036  24.192929
        # 4     AMD     17   3.207412  22.172897        0.000000          5.361538e+07    4.445455e+07        NaN         NaN  11.539060  22.497147
        # 5    ANET     13  41.593335  47.165121        0.000000          4.496792e+08    5.465564e+07  32.273795         NaN  22.112241  22.168602
        # 6    ASML     16  12.660632  16.708757        0.229989          2.764633e+09    4.426604e+08  11.523360   11.290233  20.811058  23.503372
        # 7    AVGO      9  12.677225  51.377072        0.568398          1.298238e+10    1.400000e+09  -0.593911   29.146302  12.969006  28.923214
        # 8    CSCO     17   2.623500   3.267293        0.435724          1.283707e+10    6.404706e+08   7.603257    9.680117  15.763935  20.175566
        # 9     IBM     18  -2.096716   3.703036        0.337966          1.702527e+10   -6.636923e+08   7.344961    8.916288  20.417317  61.815304
        # 10   INTC     18   1.533952  -6.968304        0.379032          1.714146e+10   -8.600000e+08        NaN    6.115508  14.990948  18.068437
        # 11   INTU     17  11.572977  10.392048        0.212399          1.477615e+09    1.769231e+07  10.066996   13.639516  20.362582  23.679682
        # 12   KLAC     16  10.900095  11.488950        0.375356          8.921842e+08    1.914440e+08  11.875910   15.159376  18.103193  55.915187
        # 13   LRCX     16  20.845737  20.066094        0.123370          1.564338e+09    2.616656e+08  12.589839   31.974256  17.759093  27.180024
        # 14   MCHP     17  11.447419   0.877442        0.861432          8.870314e+08   -4.712064e+07        NaN    1.025195  11.350981  13.742577
        # 15   MPWR     16  15.999371  24.766335        0.360900          9.693315e+07    1.654992e+07  20.919293   27.307130  12.722596  12.726359
        # 16   MRVL      6   8.922568 -27.040050       -0.230760          1.133294e+09    6.142350e+07   0.000000    0.019605  -2.652105  -3.326828
        # 17   MSFT     16   9.450247  15.781682        0.315768          3.193717e+10    5.213333e+08  18.639394   11.512707  22.720834  35.433912
        # 18     MU     16   3.769690  32.952306       -0.000943          3.696917e+09    4.301000e+08  10.015289  163.449913  12.185228  14.495693
        # 19   NVDA     18   8.321348  30.286784        0.054497          2.164909e+09    3.136199e+08  18.872270    8.210057  15.739399  19.671156
        # 20   NXPI     14   4.552677  -9.697391        0.038412          2.491000e+09    1.750000e+08   3.099695   35.183781  19.265443  19.464295
        # 21     ON     17   5.650164   5.999278        0.000000          6.041692e+08    5.193846e+07  10.686487         NaN   6.923268  11.472216
        # 22   PANW     14  31.211709  -8.947647        0.000000          5.714248e+08    1.102403e+08   8.237812         NaN   1.121241   1.121241
        # 23   QCOM     18   4.648874   0.581958        0.372119          5.952125e+09    4.318462e+08  10.602295    9.709177  18.447238  18.161972
        # 24   SWKS     17   7.972981  -1.816635        0.150324          9.560881e+08    1.190425e+08  13.850989   13.331944  19.046871  19.220033
        # 25    TSM     10   5.539021        NaN             NaN          2.655144e+10    3.551650e+09  14.023235   10.430306        NaN        NaN
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
        matspull = 'SELECT Ticker, cast(AveragedOverYears as integer) as years, revGrowthAVG as revgr, netIncomeGrowthAVG as nigr, payoutRatioAVG, operatingCashFlowAVG as opcfAmount, operatingCashFlowGrowthAVG as opcfGRAVG, netCashFlowAVG as netcfAmount, netCashFlowGrowthAVG as netcfGRAVG, \
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
                    # 0     SFM     14  0.672284  15.954637        0.000000          3.146795e+08    2.114025e+07  15.321938  11.491161        NaN  12.317866   23.113926
                    # 1    COST     17  8.450071  15.874480        0.266252          4.198385e+09    3.809231e+08  11.478007  12.379436 -16.610309  13.603188   20.822293
                    # 2     WMT     18  3.018433  -0.995369        0.375721          2.589423e+10    5.933846e+08        NaN        NaN   3.141014  11.889157   18.408654
                    # 3      CL     17  1.610136  -0.405310        0.623488          3.145000e+09    3.942857e+07  -6.261083  -3.470780   3.606261  29.956134  150.025664
                    # 4     SYY     17  0.382352   7.034560        0.582480          1.684833e+09   -5.579820e+07   2.745845   1.995446   4.163013  28.913539   31.237070
                    # 5     KMB     17  1.069345   0.899082        0.645072          2.849333e+09   -7.800000e+07        NaN        NaN   4.648064  57.850925  131.275858
                    # 6     GIS     17  0.300916   6.694189        0.526021          2.707709e+09    3.026667e+07   5.931027   5.617303   5.418652  24.700704   25.127948
                    # 7      KO     18  0.775930  -1.115576        0.692794          1.021915e+10    6.320000e+08        NaN        NaN   6.002045  14.836955   29.932706
                    # 8     PEP     17  2.318789   4.633028        0.588480          9.979692e+09    1.358417e+09   5.593741   4.998578   6.774506  14.873945   44.854359
                    # 9     ADM     17 -1.829961  -3.508348        0.304042          2.523667e+09   -4.515385e+07   3.348879   2.524214   7.319883   7.477781   10.433476
                    # 10     PG     17  1.715124   1.022159        0.579380          1.514814e+10   -1.405333e+08  -0.602753  -2.286862   7.482243  15.182172   18.537180
                    # 11    CHD     17  1.224504   8.081264        0.355999          6.863774e+08    3.699154e+07   8.810537   9.744301   8.155390  13.527249   19.075527
                    # 12    HSY     18  3.521175  10.867016        0.532020          1.111915e+09    9.934692e+06  21.346222  17.535345   9.044399  28.392922   58.372306
                    # 13    HRL     17  2.901532   7.761210        0.352526          9.323203e+08    3.088111e+07        NaN        NaN  11.336586  15.441286   16.273557
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
                    WHERE Sector LIKE \'Real Estate\' \
                    AND years >= 5 \
                    AND revgr >= 0 \
                    AND ffogr >= 3 \
                    AND eps >= 1 \
                    AND epsGR >= 0 \
                    AND opcfAmount > 0 \
                    AND opcfGRAVG >= 0 \
                    AND equity > 3 \
                    AND divgr >= -10 AND divgr <= 50 \
                    AND ffopo <= 0.9 AND ffopo > 0 \
                    AND yieldAVG > 0 \
                    AND roic > 0 \
                    AND roce > 0 \
                    ORDER BY Ticker;'
        
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
                # 6     IRM     17   0.462294  -1.179094   5.754689    2.805197  1.649241  0.725218  6.836071e+08   6.390874  3.122400e+07    8.384818        NaN        NaN   3.689258   4.004123  15.680956   7.610774   6.731443
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
            # 1    DUK     18  0.221211   7.954555        0.913625          6.323071e+09   3.260719    2.490000e+07             23.105484        NaN        NaN    3.193720   3.056168   6.177616
            # 2     SO     18  2.171045   8.943522        0.796197          6.014083e+09   1.860861    1.842667e+08            -23.119291   3.610923   5.672442    3.493040  10.581139  10.670477
            # 3    AEP     18 -0.093679   2.914157        0.636054          4.318267e+09   0.715478    1.438462e+07             57.999799   4.240100   4.951068    5.234602   4.350508  10.036047
            # 4    XEL     17  0.880361   8.630919        0.621380          2.494910e+09   2.754592    9.907583e+06            -20.853668        NaN        NaN    5.649633   9.761526  10.143703
            # 5    SRE     17  5.062096  20.892003        0.495156          2.475267e+09   3.474076   -9.766667e+07             31.294351        NaN        NaN    6.689960   9.487637   9.531081
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
        # 0   AMZN     18  25.158803   5.469834          1.602340e+10  27.755116    2.365615e+09             -6.442240  30.914254        NaN        0.000000   8.738340  14.292071
        # 1   TSLA     16  55.815803  37.733530          8.608899e+08  14.331766    2.085190e+08             78.325071  20.272625        NaN        0.000000 -11.012581  -3.796099
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

# AND Ticker IN (\'MSFT\', \'AAPL\', \'CSCO\', \'ACN\', \'INTU\', \'IBM\', \'PANW\', \'SWKS\', \'ANET\', \'NVDA\', \'AMD\', \
#                     \'INTC\', \'TXN\', \'ADI\', \'MCHP\', \'AVGO\', \'TSM\', \'LRCX\', \'AMAT\', \'KLAC\', \'ASML\', \'MU\', \'MRVL\', \'QCOM\', \
#                     \'ON\', \'NXPI\', \'MPWR\') \

#roic: [20,15,7,5,1,0,-1,-5,-7]
#roce: [25,15,10,5,1,0,-1,-5,-10]
#rev: [15, 7, 3, 2, 0, -1, -2, -3, -4]
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

def selectingBDC():
    try:
        bdcRanks = 'Select * From Sector_Rankings \
                    WHERE Ticker IN (\'ARCC\', \'BBDC\', \'BCSF\', \'BKCC\', \'BXSL\', \'CCAP\', \'CGBD\', \'FCRD\', \'CSWC\', \'GAIN\', \'GBDC\', \
                    \'GECC\', \'GLAD\', \'GSBD\', \'HRZN\', \'ICMB\', \'LRFC\', \'MFIC\', \'MAIN\', \'MRCC\', \'MSDL\', \'NCDL\', \'NMFC\', \'OBDC\', \
                    \'OBDE\', \'OCSL\', \'OFS\', \'OXSQ\', \'PFLT\', \'PFX\', \'PNNT\', \'PSBD\', \'PSEC\', \'PTMN\', \'RAND\', \'RWAY\', \'SAR\', \
                    \'SCM\', \'SLRC\', \'SSSS\', \'TCPC\', \'TPVG\', \'TRIN\', \'TSLX\', \'WHF\', \'HTGC\', \'CION\', \'FDUS\', \'FSK\') \
                    AND roce >= 2 \
                    AND roic >= 2 \
                    AND shares >= 2 \
                    AND cf >= 0 \
                    AND bv >= 2 \
                    AND equity >= 0 \
                    ORDER BY bv DESC'

        print_DB(bdcRanks, 'print')
        csv.simple_saveDF_to_csv('',print_DB(bdcRanks, 'return'), 'z-BDClist', False)
    except Exception as err:
        print('select bdc error:')
        print(err)

def LSUlti():
    try:
        #sql pull, save as csv for now
        matspull = 'SELECT Ticker, Sector, roce, roic, po, divgr, divyield, shares, debt, rev, ni, fcf, fcfm, cf, bv, equity, score FROM Sector_Rankings \
                    WHERE roce >= 3 \
                    AND roic >= 3 \
                    AND equity >= 2 \
                    AND po >= 1 \
                    AND divgr >= 2 \
                    AND shares >= 2 \
                    AND ni >= 2 \
                    AND rev >= 1 \
                    AND fcf >= 2 \
                    AND fcfm >= 2 \
                    AND cf >= 2 \
                    AND divpay > 0 \
                    AND debt >= 3 \
                    AND bv >= 2 \
                    ORDER BY Sector, score DESC'
        themats = print_DB(matspull, 'return')
    except Exception as err:
        print('LSulti error: ')
        print(err)
    finally:
        csv.simple_saveDF_to_csv('',themats,'z-UltiInvUniverse', False)

# LSUlti()

def rank_DivGrowth(): #not necessary, already baked into sector rankings, and each sector's stock analyses
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
                rocev = 5
                roicv = 5
                rocv = 0
                ffopov = 5
                pov = 5
                divgrv = 5
                divpayv = 5
                sharesv = 3
                cfv = 5
                bvv = 3
                equityv = 4
                debtv = 3
                fcfmv = 3
                fcfv = 3
                ffov = 3
                niv = 3
                revv = 3
                yieldv = 5

                justscore = ((rev) + (ni) + (fcf) + (fcfm) + (bv) + (debt) + (equity) + (cf) + (shares) + (divpay) + 
                                (divgr) + (po) + (roic) + (roce) + (divyield))

                maxscore = 40
                uploaddf['maxplainscore'] = maxscore
                uploaddf['plainscore'] = justscore
                # uploadToDB(uploaddf,'Growth_Ranking')

                srmaxscore = 5*((revv) + (niv) + (ffov) + (fcfv) + (fcfmv) + (debtv) + (equityv) + (bvv) + (cfv) + (sharesv) + (divpayv) + 
                                (divgrv) + (pov) + (ffopov) + (rocv) + (roicv) + (rocev) + (yieldv))
                finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
                                (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
                                (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

                uploaddf['maxscore'] = srmaxscore
                uploaddf['score'] = finalscore
                uploadToDB(uploaddf,'DivGrowth_Ranking')
                n += 1
            except Exception as err:
                print('rank div growth error in loop for: ' + str(x))
                print(err)
                continue
        time2 = time.time()
        print('time to completion:')
        print(time2-time1)
    except Exception as err:
        print('rank div growth error: ')
        print(err)

# testg = 'Select * From DivGrowth_Ranking ORDER BY score DESC'
# print_DB(testg, 'print')

##oh god new delete button no touchie
# hehe = 'DELETE FROM '
# hehe = 'Select Count(distinct Ticker) From Metadata'
# gege = 'Select Count(distinct Ticker) From Metadata_Backup'
# conn = sql.connect(db_path)
# query = conn.cursor()
# query.execute(hehe)
# conn.commit()
# query.close()
# conn.close()


# print_DB(hehe, 'print')
# print_DB(gege, 'print')
#########


###### NO#######
# delete_DB()
########NO###########

#---------------------------------------------------------------------
#The testing zone - includes yahoo finance examples
#---------------------------------------------------------------------

# lickit = [] 
# for x in lickit:
#     write_Master_csv_from_EDGAR(x,ultimateTagsList,'2024','2')
# checkYearsIntegrityList(lickit)


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

# print((consolidateSingleAttribute(ticker235, year235, version235, revenue, False)))
# print(consolidateSingleAttribute(ticker235, year235, version235, totalCommonStockDivsPaid, False)) #netIncome 
# print(consolidateSingleAttribute(ticker235, year235, version235, declaredORPaidCommonStockDivsPerShare, False))
# print(consolidateSingleAttribute(ticker235, year235, version235, basicSharesOutstanding, False))
# totalCommonStockDivsPaid, declaredORPaidCommonStockDivsPerShare, basicSharesOutstanding

# print(cleanTotalEquity(consolidateSingleAttribute(ticker235, year235, version235, totalAssets, False), 
#                                     consolidateSingleAttribute(ticker235, year235, version235, totalLiabilities, False), consolidateSingleAttribute(ticker235, year235, version235, nonCurrentLiabilities, False),
#                                     consolidateSingleAttribute(ticker235, year235, version235, currentLiabilities, False), consolidateSingleAttribute(ticker235, year235, version235, nonCurrentAssets, False),
#                                     consolidateSingleAttribute(ticker235, year235, version235, currentAssets, False), consolidateSingleAttribute(ticker235, year235, version235, shareHolderEquity, False)))


# print(cleanDebt(consolidateSingleAttribute(ticker235, year235, version235, shortTermDebt, False), 
#                                     consolidateSingleAttribute(ticker235, year235, version235, longTermDebt1, False), consolidateSingleAttribute(ticker235, year235, version235, longTermDebt2, False),
#                                     consolidateSingleAttribute(ticker235, year235, version235, longTermDebt3, False), consolidateSingleAttribute(ticker235, year235, version235, longTermDebt4, False)))

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


# ticker100 = 'ARCC' #ABR
# year100 = '2024'
# version100 = '2'
# print(consolidateSingleAttribute(ticker100, year100, version100, totalCommonStockDivsPaid, False))
# print(cleanDividends(consolidateSingleAttribute(ticker100, year100, version100, totalCommonStockDivsPaid, False), 
#                                     consolidateSingleAttribute(ticker100, year100, version100, declaredORPaidCommonStockDivsPerShare, False),
#                                     consolidateSingleAttribute(ticker100, year100, version100, basicSharesOutstanding, False),
#                                       consolidateSingleAttribute(ticker100, year100, version100, dilutedSharesOutstanding, False)))

# print(cleanDebt(consolidateSingleAttribute(ticker100, year100, version100, shortTermDebt, False), 
#                                     consolidateSingleAttribute(ticker100, year100, version100, longTermDebt1, False), consolidateSingleAttribute(ticker100, year100, version100, longTermDebt2, False),
#                                     consolidateSingleAttribute(ticker100, year100, version100, longTermDebt3, False), consolidateSingleAttribute(ticker100, year100, version100, longTermDebt4, False)))
        
# print(cleanTotalEquity(consolidateSingleAttribute(ticker100, year100, version100, totalAssets, False), 
#                                     consolidateSingleAttribute(ticker100, year100, version100, totalLiabilities, False), 
#                                       consolidateSingleAttribute(ticker100, year100, version100, nonCurrentLiabilities, False),
#                                     consolidateSingleAttribute(ticker100, year100, version100, currentLiabilities, False)))



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






#---------------------------------------------------------------------
#What each value is
#---------------------------------------------------------------------
#roic = nopat / invested capital
#nopat = operating income * (1-tax rate)
# invested capital = total equity + total debt + non operating cash
#tequity = t assets - t liabilities
#ocf - capex = free cash flow
#fcf margin = fcf / revenue
#payout ratio = divs paid / net income
# modded payout ratio = divs paid / fcf
# ffo = netincomeloss + depr&amor - gainloss sale of property and it matches their reporting, albeit slightly lower due to minor costs not included/found on sec reportings.
# You almost end up with a bas****ized affo value because of the discrepancy tho!
#ffo/(dividend bulk payment + interest expense) gives idea of how much money remains after paying interest and dividends for reits. aim for ratio > 1
#---------------------------------------------------------------------






# -----------------------------------------------------------------SAVED until prod, or for notes, or or or---------------------
#nifty loop checking
# print(len(revenue))
# tar = eps
# def loopCheck(target):
#     if len(target) > 1:
#         for y in target:
#             if len(y) > 1:
#                 for z in y:
#                     print(z)
#             else:
#                 print(y[0])
#     else:
#         print(target[0])

# loopCheck(eps)
# loopCheck(revenue)
# loopCheck(ultimateList)
###
#time tests
# time1 = time.time()
# time2 = time.time()
# print('time to complete')
# print((time2-time1)*1000)
###
#yahoo stuff
# ticker = 'MSFT'
# stock = yf.Ticker(ticker)
# dict1 = stock.info
# marketCap = dict1['marketCap']

# # pe = dict1['pe']
# # for x in dict1:
# #     print(x)
# print(marketCap)
###

#set checks
# print(set(fullNulls).difference(yearsOff))
# print(set(fullNulls).difference(fullNulls))

# print(set(divsYearsOff).intersection(incYearsOff))
# fullNullOverlap = set(incFullNulls).intersection(divsFullNulls)
# yearsOffOverlap = set(divsYearsOff).intersection(incYearsOff)
# print(fullNullOverlap)
# print(yearsOffOverlap)
# print(set(fullNullOverlap).intersection(yearsOffOverlap))
###
# def rank_FullWeight(): #luke: why even use this?
#     try:
#         tickergrab = 'SELECT Ticker as ticker, Sector FROM Metadata'
#         tickers = print_DB(tickergrab, 'return')
#         tickersdict = tickers.set_index('ticker')['Sector'].to_dict()
#         print('ranking full weight now')
#         n = 1
#         for x in tickers['ticker']:
#             ###
#             uploaddf = pd.DataFrame()
#             print(x)
#             uploaddf['Ticker'] = [x]
#             uploaddf['Sector'] = tickersdict[x]
#             roce = uploaddf['roce'] = roce_rating(x)
#             roic = uploaddf['roic'] = roic_rating(x)
#             roc = uploaddf['roc'] = roc_rating(x)
#             ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
#             po = uploaddf['po'] = payout_rating(x)
#             divgr = uploaddf['divgr'] = divgrowth_rating(x)
#             divpay = uploaddf['divpay'] = divspaid_rating(x)
#             shares = uploaddf['shares'] = shares_rating(x)
#             cf = uploaddf['cf'] = cf_rating(x)
#             bv = uploaddf['bv'] = bvnav_rating(x)
#             equity = uploaddf['equity'] = equity_rating(x)
#             debt = uploaddf['debt'] = debt_rating(x)
#             fcfm = uploaddf['fcfm'] = fcfm_rating(x)
#             fcf = uploaddf['fcf'] = fcf_rating(x)
#             ffo = uploaddf['ffo'] = ffo_rating(x)
#             ni = uploaddf['ni'] = ni_rating(x)
#             rev = uploaddf['rev'] = growth_rating(x)
#             divyield = uploaddf['divyield'] = yield_rating(x)
#             #v = value to be VALUED at lol
#             rocev = 5
#             roicv = 5
#             rocv = 5
#             ffopov = 0
#             pov = 5
#             divgrv = 5
#             divpayv = 5
#             sharesv = 5
#             cfv = 5
#             bvv = 5
#             equityv = 5
#             debtv = 5
#             fcfmv = 5
#             fcfv = 5
#             ffov = 0
#             niv = 5
#             revv = 5
#             yieldv = 5

#             finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
#                             (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
#                             (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

#             uploaddf['score'] = finalscore
#             ###
#             # n+=1
#             # print(n)
#             uploadToDB(uploaddf,'FullWeight_Ranking')
#         # print('final n')
#         # print(n)
#     except Exception as err:
#         print('rank full weighting error: ')
#         print(err)

# def rank_REITFullWeight():
#     try:
#         tickergrab = 'SELECT Ticker as ticker, Sector FROM Metadata WHERE Sector LIKE \'Real Estate\''
#         tickers = print_DB(tickergrab, 'return')
#         tickersdict = tickers.set_index('ticker')['Sector'].to_dict()
#         n = 0
#         for x in tickers['ticker']:
#             print(n)
#             uploaddf = pd.DataFrame()
#             uploaddf['Ticker'] = [x]
#             uploaddf['Sector'] = tickersdict[x]
#             roce = uploaddf['roce'] = roce_rating(x)
#             roic = uploaddf['roic'] = roic_rating(x)
#             roc = uploaddf['roc'] = roc_rating(x)
#             ffopo = uploaddf['ffopo'] = ffopayout_rating(x)
#             po = uploaddf['po'] = payout_rating(x)
#             divgr = uploaddf['divgr'] = divgrowth_rating(x)
#             divpay = uploaddf['divpay'] = divspaid_rating(x)
#             shares = uploaddf['shares'] = shares_rating(x)
#             cf = uploaddf['cf'] = cf_rating(x)
#             bv = uploaddf['bv'] = bvnav_rating(x)
#             equity = uploaddf['equity'] = equity_rating(x)
#             debt = uploaddf['debt'] = debt_rating(x)
#             fcfm = uploaddf['fcfm'] = fcfm_rating(x)
#             fcf = uploaddf['fcf'] = fcf_rating(x)
#             ffo = uploaddf['ffo'] = ffo_rating(x)
#             ni = uploaddf['ni'] = ni_rating(x)
#             rev = uploaddf['rev'] = growth_rating(x)
#             divyield = uploaddf['divyield'] = yield_rating(x)
#             #v = value to be VALUED at lol
#             rocev = 5
#             roicv = 5
#             rocv = 5
#             ffopov = 5
#             pov = 0
#             divgrv = 5
#             divpayv = 5
#             sharesv = 5
#             cfv = 5
#             bvv = 5
#             equityv = 5
#             debtv = 5
#             fcfmv = 5
#             fcfv = 5
#             ffov = 5
#             niv = 5
#             revv = 5
#             yieldv = 5

#             finalscore = ((rev * revv) + (niv * ni) + (ffov * ffo) + (fcfv * fcf) + (fcfmv * fcfm) + (debtv * debt) + 
#                             (equityv * equity) + (bvv * bv) + (cfv * cf) + (sharesv * shares) + (divpayv * divpay) + 
#                             (divgrv * divgr) + (pov * po) + (ffopov * ffopo) + (rocv * roc) + (roicv * roic) + (rocev * roce) + (yieldv * divyield))

#             uploaddf['score'] = finalscore
#             # print(uploaddf)
#             n += 1
#             uploadToDB(uploaddf,'REITFullWeight_Ranking')
#         # print(n)
#     except Exception as err:
#         print('rank reit full weighting error: ')
#         print(err)
###############


# Let’s quickly visualize some of the data we just downloaded. 
# As an example we’ll look at quarterly revenues for one of the largest 
# US-based global logistics companies, Expeditors International of Washington Inc. 
# We’ll also clean up the data a bit to make a more readable figure.

# EDGAR_data2 = pd.read_csv('./sec_related/' + 'EDGAR1' + '.csv')
# EXPD_data = EDGAR_data2[EDGAR_data2['ticker'] == 'EXPD'].copy()
# EXPD_data['frame'] = EXPD_data['frame'].str.replace('CY',"")
# EXPD_data['val_billions'] = EXPD_data['val'] / 1000000000

# sns.set_theme(style='darkgrid')
# fig = sns.lineplot(data=EXPD_data, x='frame', y='val_billions')
# fig.set(xlabel='Quarter', ylabel='Revenue(billions USD)', title='EXPD')
# plt.show()

# f = open('./demoData.txt', 'a')
    # f.write(company_data)
    # f.close()

# f = open('./demoData.txt', 'r')
# print(f.read())

#neato percentile manual function
# time1 = time.time()
# isitalist = print_DB(testlistquery, 'return')['sharesGrowthRate'].tolist()
# # print(isitalist)
# #numbers
# isitalist = [x for x in isitalist if not np.isnan(x)]

# q12 = np.percentile(isitalist, 25)
# q32 = np.percentile(isitalist, 75)
# iqr2 = q32-q12

# # print(isitalist)
# #strings
# # isitalist = [eval(i) for i in isitalist]
# # for x in isitalist:
# #     print(type(x))
# median = np.median(isitalist)
# print('median')
# print(median)
# q1list = []
# q2list = []
# i = 0
# j = 0
# length = len(isitalist)
# while i < length:
#     x = isitalist[i]
#     if x < median:
#         q1list.append(x)
#     i += 1
# # print(q1list)
# q1 = np.median(q1list)
# while j < length:
#     x = isitalist[j]
#     if x > median:
#         q2list.append(x)
#     j += 1
# # print(q2list)
# q3 = np.median(q2list)
# iqr_test = q3-q1
# ar_top = median + iqr_test
# ar_bottom = median - iqr_test
# ar_top2 = median + iqr2
# ar_bottom2 = median - iqr2
# # print(ar_top, ar_bottom)

# finalyearlist = []
# finalyearlist2 = []
# for x in isitalist:
#     if x < ar_top and x > ar_bottom:
#         finalyearlist.append(x)

# for x in isitalist:
#     if x < ar_top2 and x > ar_bottom2:
#         finalyearlist2.append(x)

# print('personal list')
# print(isitalist)
# print('filtered list')
# print(finalyearlist)
# print('average?')
# print(np.average(finalyearlist))
# print('average2?')
# print(np.average(finalyearlist2))
# time2 = time.time()
# print('time to complete')
# print((time2-time1)*1000)

#saved for example, but decided to go another direction
# def OverAVGMats():
#     try:
#         # avg(roce)  avg(roic)   avg(po)  avg(divgr)  avg(divpay)  avg(shares)   avg(cf)  avg(equity)  avg(debt)  avg(fcfm)  avg(fcf)   avg(ni)  avg(rev)
#         #  0.143251   0.84573   1.146006  -0.112948    -0.272727    2.493113    1.815427     0.903581    3.07438   0.066116  0.176309  0.198347  0.501377
#         matspull = 'SELECT Ticker, roce, roic, po, divgr, shares, debt, rev, ni, fcf, fcfm, cf, equity, score FROM Sector_Rankings \
#                     WHERE Sector LIKE \'B\' \
#                     AND roce >= 1 \
#                     AND roic >= 1 \
#                     AND po >= 2 \
#                     AND divpay > 0 \
#                     AND divgr > 0 \
#                     AND shares >= 3 \
#                     AND rev >= 1 \
#                     AND ni >= 1 \
#                     AND fcf >= 1 \
#                     AND fcfm >= 1 \
#                     AND cf >= 2 \
#                     AND equity >= 1 \
#                     AND debt >= 4 \
#                     ORDER BY score DESC'
                    
#         themats = print_DB(matspull, 'return')
#     except Exception as err:
#         print('LSMats error: ')
#         print(err)
#     finally:
#         csv.simple_saveDF_to_csv('',themats,'z-OverAVGMats', False)

#unused idea
# def fillAllEmptyGrowthRates(df):
#     try:
#         tarList = ['revenue','netIncome','operatingCashFlow','investingCashFlow','financingCashFlow','netCashFlow', 'capEx','depreNAmor']
#         df_filled = df
#         fixTracker = 0
#         for x in tarList:
#             tarGrowthRate = x + 'GrowthRate'
#             # meanReplacement = df_filled[x].mean()
#             savedCol = df_filled[x]
#             # df_filled[x] = df_filled[x].replace(np.NaN, meanReplacement)#.ffill()  we trying backfilling instead
#             df_filled[x] = df_filled[x].ffill().bfill()

#             growthCol = grManualCalc(df_filled[x])
#             df_filled[tarGrowthRate] = growthCol#df_filled[x].pct_change(fill_method=None)*100

#             if savedCol.isnull().any():
#                 percentNull = savedCol.isnull().sum() / len(savedCol)
#                 if percentNull > 0.4:
#                     fixTracker += 1
#             # if savedCol.equals(df_filled[x]):
#             #     continue
#             # else:
#             #     fixTracker += 1

        
#         # if df_filled['depreNAmor'].isnull().any():
#         #     percentNull = df_filled['depreNAmor'].isnull().sum() / len(df_filled['depreNAmor'])
#         #     if percentNull > 0.4:
#         #         fixTracker += 1
#         #     # fixTracker += 1  
#         #     # print('it was shares')
#         #     df_filled['depreNAmor'] = df_filled['depreNAmor'].ffill().bfill() 

#         # if df_filled['Units'].isnull().all():
#         #     # print('they all empty')
#         #     df_filled = df_filled.drop('Units',axis=1)
#         # else:
#         #     # print('filling empties')
#         #     df_filled['Units'] = df_filled['Units'].ffill().bfill()

#         if fixTracker > 4:
#             df_filled['INCintegrityFlag'] = 'NeedsWork'
#         elif fixTracker == 0: 
#             df_filled['INCintegrityFlag'] = 'Good'
#         else:
#             df_filled['INCintegrityFlag'] = 'Acceptable'
#         return df_filled
#     except Exception as err:
#         print("fill empty inc GR error: ")
#         print(err)

##drop all except fy records notes
### this worked, trying to automate above
        # held_data126 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-06-')==True)]
        # held_data127 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-07-')==True)]
        # held_data1211 = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-11-')==True)]
        # print('held1211')
        # print(held_data1211)

        # held_data6212 = df[(df['start'].str.contains('-06-')==True) & (df['end'].str.contains('-12-')==True)]
        # held_data7212 = df[(df['start'].str.contains('-07-')==True) & (df['end'].str.contains('-12-')==True)]
        # held_data11212 = df[(df['start'].str.contains('-11-')==True) & (df['end'].str.contains('-12-')==True)]

        # # if held_data126.empty:
        # held7 = pd.merge(held_data127, held_data7212, on=['Ticker','CIK','Units','fp','fy','form','frame','filed','Tag','accn'], how='outer')
        # held7['val'] = held7['val_x'] + held7['val_y']
        # held7['start'] = held7['start_x']
        # held7['end'] = held7['end_y']
        # held7 = held7.drop(columns=['val_x','val_y','start_x','start_y','end_x','end_y'])
        # held7 = held7.dropna(subset=['val'])#,'start'])
        # returned_data = pd.concat([returned_data, held7], ignore_index = True)
        # # else:
        # held6 = pd.merge(held_data126, held_data6212, on=['Ticker','CIK','Units','fp','fy','form','frame','filed','Tag','accn'], how='outer')
        # held6['val'] = held6['val_x'] + held6['val_y']
        # held6['start'] = held6['start_x']
        # held6['end'] = held6['end_y']
        # held6 = held6.drop(columns=['val_x','val_y','start_x','start_y','end_x','end_y'])
        # held6 = held6.dropna(subset=['val'])#,'start'])
        # returned_data = pd.concat([returned_data, held6], ignore_index = True)

        # held11 = pd.merge(held_data1211, held_data11212, on=['Ticker','CIK','Units','fp','fy','form','frame','filed','Tag','accn'], how='outer')
        # held11['val'] = held11['val_x'] + held11['val_y']
        # held11['start'] = held11['start_x']
        # held11['end'] = held11['end_y']
        # held11 = held11.drop(columns=['val_x','val_y','start_x','start_y','end_x','end_y'])
        # held11 = held11.dropna(subset=['val'])#,'start'])
        # returned_data = pd.concat([returned_data, held11], ignore_index = True)

# def cleanDividends(total, perShare, shares):  #backup

#     try:
#         # shares['year'] = shares.end.str[:4]
#         shares = shares.rename(columns={'val':'shares'})
#         shares = shares.drop(columns=['Units'])
#         # total['year'] = total.end.str[:4]
#         total = total.rename(columns={'val':'totalDivsPaid'})
#         # perShare['year'] = perShare.end.str[:4]
#         perShare = perShare.rename(columns={'val':'divsPaidPerShare'})
#         perShare = perShare.drop(columns=['Units'])

#         # shares = shares.drop(columns=['start','end'])
#         # total = total.drop(columns=['start','end'])
#         # perShare = perShare.drop(columns=['start','end'])

#         print('shares, total, pershare: ')
#         print(shares)
#         print(total)
#         print(perShare)
        
#         if shares.empty:# and total.empty and perShare.empty: #maybe think about how to fill the shares dataframe. could be a useful tactic. maybe yahoo has a way?
#             cols = {'Units': -1, 'Ticker': -1, 'CIK': -1, 'year': -1, 'totalDivsPaid': -1, 'shares': -1,
#                      'divsPaidPerShare': -1, 'sharesGrowthRate': -1, 'divGrowthRate': -1, 'integrityFlag': -1}#, 'Ticker': total['Ticker'] #'interestPaid': -1, 'start': -1, 'end': -1,
#             # vals = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
#             df_col_added = pd.DataFrame(cols, index=[0])
#             return df_col_added
#             # shares['val'] = 1
#         else:
#             sharesNperShare = pd.merge(shares, perShare, on=['year','Ticker','CIK'], how='outer')#'start','end',
#             # print('sharesNperShare: ')
#             # print(sharesNperShare)
#             df_col_added = pd.merge(total, sharesNperShare, on=['year','Ticker','CIK'], how='outer')#'start','end',
#             # print('total + shares + per share: ')
#             # print(df_col_added)
#             df_col_added['shares'] = df_col_added['shares'].ffill().bfill() #.replace("", None) pre ffillbfill
#             # if df_col_added['shares'].empty:
#             #     df_col_added['sharesGrowthRate'] = np.NaN
#             # else:
#             growthCol = grManualCalc(df_col_added['shares'])
#             df_col_added['sharesGrowthRate'] = growthCol #df_col_added['shares'].pct_change()*100 #now we can add the growth rate once nulls filled
#             # df_col_added['sharesGrowthRate'] = df_col_added['sharesGrowthRate'].replace(np.nan,0) #fill in null values so later filter doesn't break dataset

#             #first we check for nans, keep them in mind for later
#             nanList = []
#             for x in df_col_added:
#                 if df_col_added[x].isnull().any():
#                     # integrity_flag = 'Acceptable'
#                     nanList.append(x)
#                     # print('nans found: ' + x)
#             #How to handle those empty values in each column
#             df_col_added['tempPerShare'] = df_col_added['totalDivsPaid'] / df_col_added['shares']
#             df_col_added['tempTotalDivs'] = df_col_added['divsPaidPerShare'] * df_col_added['shares']

#             # df42 = pd.DataFrame()
#             # df42['temp'] = df_col_added['tempPerShare']
#             # df42['actual'] = df_col_added['divsPaidPerShare']
#             # print(df42)

#             for x in nanList: #Values in ex-US currencies seem weird versus common stock analysis sites. Could be an exchange rate issue I haven't accounted for in the exchange to USD.
#                 if x == 'divsPaidPerShare':
#                     df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['tempPerShare'])
#                     # growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
#                     # df_col_added['divGrowthRate'] = growthCol1 
#                 elif x == 'totalDivsPaid':
#                     df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
#                     # growthCol1 = grManualCalc(df_col_added['divsPaidPerShare'])
#                     # df_col_added['divGrowthRate'] = growthCol1 
#             df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempPerShare'])

#             growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
#             df_col_added['divGrowthRateBOT'] = growthCol1 
#             growthCol2 = grManualCalc(df_col_added['divsPaidPerShare'])
#             df_col_added['divGrowthRateBOPS'] = growthCol2
            
#             # if df_col_added['divsPaidPerShares'].empty:
#             #     df_col_added['divGrowthRate'] = np.NaN
#             # else:
            
#             # print('average growth rate: ')
#             # print(df_col_added['divGrowthRate'].mean())

#             return df_col_added
#     except Exception as err:
#         print("clean dividends error: ")
#         print(err)

# def checkTechIncYears():
#     try:
#         # incomeBadYears = pd.DataFrame(columns=['Ticker', 'Column'])
#         # noIncData = pd.DataFrame(columns=['Ticker', 'Column'])
#         nameCheckList = tech['Ticker']
#         nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
#         incYearTracker = []
#         incomeNullTracker = []
#         toRecapture = []
#         yearsList = ['2023','2024'] #2022
#         version123 = '2'
#         for x in nameCheckList:
#             print(x)
#             try:
#                 incTable = makeIncomeTableEntry(x, '2024', version123, False)
#                 #Checking if returned tables are just empty
#                 if str(type(incTable)) == "<class 'NoneType'>" or incTable.empty:
#                     incomeNullTracker.append(x)
#                     continue
#                 #checking latest data from the pull             
#                 if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
#                     # print(str(x) + ' incYears are good!')
#                     incYearTracker.append(x)     
#             except Exception as err:
#                 print("nested check tech years error: ")
#                 print(err)
#                 toRecapture.append(x)
#                 continue                

#     except Exception as err:
#         print("check tech years error: ")
#         print(err)
#         # toRecapture.append(x)
#         # continue
#     finally:
#         print('recap list: ')
#         print(toRecapture)
#         print('full nulls:')
#         print(incomeNullTracker)
#         print('years off')
#         print(incYearTracker)
    # finally:
    #     if len(incYearTracker) > 0:
    #         incomeBadYears['Ticker'] = incYearTracker
    #         csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

    #     if len(divTracker) > 0:
    #         divsBadYears['Ticker']=divTracker
    #         csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

    #     if len(incomeNullTracker) > 0:
    #         noIncData['Ticker']=incomeNullTracker
    #         csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

    #     if len(DivNullTracker) > 0:
    #         noDivData['Ticker']=DivNullTracker
    #         csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

    #     # for x in toRecapture:
    #     #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
    #     print(toRecapture) 

# def checkTechDivYears():
#     try:
#         nameCheckList = tech['Ticker']
#         nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
    
#         divYearTracker = []
#         divNullTracker = []
#         toRecapture = []
#         yearsList = ['2023','2024'] #2022
#         version123 = '2'

#         for x in nameCheckList:
#             print(x)
#             try:
              
#                 divsTable = makeDividendTableEntry(x, '2024', version123, False)
                
#                 #Checking if returned tables are just empty
#                 # if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
#                 #     incomeNullTracker.append(x)
#                 if str(type(divsTable)) == "<class 'NoneType'>" or divsTable.empty:#.empty:
#                     divNullTracker.append(x)
#                     continue
#                 #checking latest data from the pull
#                 if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
#                     # print(str(x) + ' divYears are good!')
#                     divYearTracker.append(x)                

#                 # if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
#                 #     # print(str(x) + ' incYears are good!')
#                 #     incYearTracker.append(x)     
#             except Exception as err:
#                 print("nested check tech div years error: ")
#                 print(err)
#                 toRecapture.append(x)
#                 continue                

       
#     except Exception as err:
#         print("check tech years error: ")
#         print(err)
#         # toRecapture.append(x)
#         # continue
#     finally:
#         # if len(incYearTracker) > 0:
#         #     incomeBadYears['Ticker'] = incYearTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

#         # if len(divTracker) > 0:
#         #     divsBadYears['Ticker']=divTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

#         # if len(incomeNullTracker) > 0:
#         #     noIncData['Ticker']=incomeNullTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

#         # if len(DivNullTracker) > 0:
#         #     noDivData['Ticker']=DivNullTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

#         # for x in toRecapture:
#         #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
#         print('recap list: ')
#         print(toRecapture)
#         print('full nulls:')
#         print(divNullTracker)
#         print('years off')
#         print(divYearTracker)

# def checkREIncYears():
#     try:
#         # incomeBadYears = pd.DataFrame(columns=['Ticker', 'Column'])
#         # noIncData = pd.DataFrame(columns=['Ticker', 'Column'])
#         nameCheckList = realEstate['Ticker']
#         nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
#         incYearTracker = []
#         incomeNullTracker = []
#         toRecapture = []
#         yearsList = ['2023','2024'] #2022
#         version123 = '2'
#         for x in nameCheckList:
#             print(x)
#             try:
               
#                 incTable = makeIncomeTableEntry(x, '2024', version123, False)
#                 #Checking if returned tables are just empty
#                 if str(type(incTable)) == "<class 'NoneType'>" or incTable.empty:
#                     incomeNullTracker.append(x)
#                     continue
#                 #checking latest data from the pull             
#                 if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
#                     # print(str(x) + ' incYears are good!')
#                     incYearTracker.append(x)     
#             except Exception as err:
#                 print("nested check realEstate years error: ")
#                 print(err)
#                 toRecapture.append(x)
#                 continue                

#     except Exception as err:
#         print("check realEstate years error: ")
#         print(err)
#         # toRecapture.append(x)
#         # continue
#     finally:
#         print('recap list: ')
#         print(toRecapture)
#         print('full nulls:')
#         print(incomeNullTracker)
#         print('years off')
#         print(incYearTracker)
#     # finally:
#     #     if len(incYearTracker) > 0:
#     #         incomeBadYears['Ticker'] = incYearTracker
#     #         csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

#     #     if len(divTracker) > 0:
#     #         divsBadYears['Ticker']=divTracker
#     #         csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

#     #     if len(incomeNullTracker) > 0:
#     #         noIncData['Ticker']=incomeNullTracker
#     #         csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

#     #     if len(DivNullTracker) > 0:
#     #         noDivData['Ticker']=DivNullTracker
#     #         csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

#     #     # for x in toRecapture:
#     #     #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
#     #     print(toRecapture) 

# def checkREDivYears():
#     try:
#         nameCheckList = realEstate['Ticker']
#         nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
    
#         divYearTracker = []
#         divNullTracker = []
#         toRecapture = []
#         yearsList = ['2023','2024'] #2022
#         version123 = '2'

#         for x in nameCheckList:
#             print(x)
#             try:
               
#                 divsTable = makeDividendTableEntry(x, '2024', version123, False)
                
#                 #Checking if returned tables are just empty
#                 # if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
#                 #     incomeNullTracker.append(x)
#                 if str(type(divsTable)) == "<class 'NoneType'>" or divsTable.empty:#.empty:
#                     divNullTracker.append(x)
#                     continue
#                 #checking latest data from the pull
#                 if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
#                     # print(str(x) + ' divYears are good!')
#                     divYearTracker.append(x)                

#                 # if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
#                 #     # print(str(x) + ' incYears are good!')
#                 #     incYearTracker.append(x)     
#             except Exception as err:
#                 print("nested check realEstate div years error: ")
#                 print(err)
#                 toRecapture.append(x)
#                 continue                

       
#     except Exception as err:
#         print("check realEstate years error: ")
#         print(err)
#         # toRecapture.append(x)
#         # continue
#     finally:
#         # if len(incYearTracker) > 0:
#         #     incomeBadYears['Ticker'] = incYearTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

#         # if len(divTracker) > 0:
#         #     divsBadYears['Ticker']=divTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

#         # if len(incomeNullTracker) > 0:
#         #     noIncData['Ticker']=incomeNullTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

#         # if len(DivNullTracker) > 0:
#         #     noDivData['Ticker']=DivNullTracker
#         #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

#         # for x in toRecapture:
#         #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
#         print('recap list: ')
#         print(toRecapture)
#         print('full nulls:')
#         print(divNullTracker)
#         print('years off')
#         print(divYearTracker)

# def dropDuplicatesInDF(df):
#  
#     ### look at onto and compare against working ones below: nvda, crm, msft, o
#     ### let's make cases of sorts. if statements. whatever. but sort it as such:
#     ### years: same year? diff years by 1? dif years by 2?
#     ### months: 1-12, maybe multiple cases, but depends on the years
#     ### days? useless?
#     ### determine year label via those 'cases'
#     try:
#         # filtered_data = pd.DataFrame()
#         # print('pre drop dupes')
#         # print(df)
#         filtered_data = df
#         # filtered_data2 = df.drop_duplicates(subset=['val'])#,keep='last')#val #end) #This just does not work because of weird dupe numbers. gotta use full data!
#         # print('filtered_data2')
#         # print(filtered_data2)

#         if filtered_data.start.str[5:7].eq('02').all() & filtered_data.end.str[5:7].eq('01').all(): #starts feb, ends jan, hopefully one year later
#             filtered_data['year'] = filtered_data.start.str[:4]
#         else:


#             filtered_data['compare'] = (filtered_data.end.str[5:7] == filtered_data.start.str[5:7]) #Where the months are the same
#             # print(filtered_data['compare'])

#             #2022-07 -> 2023-06 == end is year
#             #2022-01 -> 2022-12 == start or end is year
#             #2022-01 -> 2023-01 == start year is year
#             filtered_data['year'] = filtered_data.start.str[:4].where(filtered_data['compare'] == True, other=filtered_data.end.str[:4])



#             # filtered_data['intstart'] = filtered_data.start.str[5:7].astype(int)
#             # filtered_data['intend'] = filtered_data.end.str[5:7].astype(int)
#             # print(filtered_data['intstart'])


#             # if abs(filtered_data.start.str[5:7].astype(int)-filtered_data.end.str[5:7].astype(int)) == 1:
#             #     if abs(filtered_data.start.str[:4].astype(int)-filtered_data.end.str[:4].astype(int)) == 1:
#             #         if filtered_data.start.str[5:7].astype(int) < 3:
#             #             filtered_data['year'] = filtered_data.start.str[:4]

#             # filtered_data = filtered_data.drop(columns=['compare']) ##WHY DIDN'T DROP WORK?! guh
#             filtered_data = filtered_data.pop('compare')
            
#             # print(filtered_data)
#         filtered_data = df.drop_duplicates(subset=['year'],keep='last')#val #end
        

#     except Exception as err:
#         print("drop duplicates error")
#         print(err)
#     finally:
#         return filtered_data



#gives tags to get from SEC. returns dataframe filled with info!
# def EDGAR_query(ticker, cik, header, tag: list=None) -> pd.DataFrame:
#     url = ep["cf"] + 'CIK' + cik + '.json'
#     response = requests.get(url, headers=header)

#     if tag == None:
#         tags = list(response.json()['facts']['us-gaap'].keys())
#         # print('in query tags: ')
#         # print(tags)
#         if tags.empty or (len(tags) <= 0):
#             tags = list(response.json()['facts']['ifrs-full'].keys())
#     else:
#         tags = tag

#     company_data = pd.DataFrame()

#     for i in range(len(tags)):
#         try:
#             tag = tags[i] 
#             units = list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
#             data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units])
#             data['Tag'] = tag
#             data['Units'] = units
#             data['Ticker'] = ticker
#             data['CIK'] = cik
#             company_data = pd.concat([company_data, data], ignore_index = True)
#         except Exception as err:
#             print(str(tags[i]) + ' not found for ' + ticker + ' in US-Gaap.')
#             # print("Edgar query error: ")
#             # print(err)
#         finally:
#             time.sleep(0.1)

#     if company_data.empty or str(type(company_data)) == "<class 'NoneType'>":
#         for i in range(len(tags)):
#             try:
#                 tag = tags[i] 
#                 units = list(response.json()['facts']['ifrs-full'][tag]['units'].keys())[0]
#                 data = pd.json_normalize(response.json()['facts']['ifrs-full'][tag]['units'][units])
#                 data['Tag'] = tag
#                 data['Units'] = units
#                 data['Ticker'] = ticker
#                 data['CIK'] = cik
#                 company_data = pd.concat([company_data, data], ignore_index = True)
#             except Exception as err:
#                 print(str(tags[i]) + ' not found for ' + ticker + ' in ifrs-full.')
#                 # print("Edgar query error: ")
#                 # print(err)
#             finally:
#                 time.sleep(0.1)

#     return company_data

##remove fy records notes
 #V1
        # returned_data2 = df[(df['start'].str.contains('-07-')==True) & (df['end'].str.contains('-06-')==True)]
        # returned_data3 = df[(df['start'].str.contains('-06-')==True) & (df['end'].str.contains('-06-')==True)]
        # returned_data4 = df[(df['start'].str.contains('-04-')==True) & (df['end'].str.contains('-03-')==True)]
        # returned_data5 = df[(df['start'].str.contains('-09-')==True) & (df['end'].str.contains('-09-')==True)]

        #V2
        # oneEnds = ['-12-','-01-','-02-']
        # twoEnds = ['-01-','-02-','-03-']
        # threeEnds = ['-02-','-03-','-04-']
        # fourEnds = ['-03-','-04-','-05-']
        # fiveEnds = ['-04-','-05-','-06-']
        # sixEnds = ['-05-','-06-','-07-']
        # sevenEnds = ['-06-','-07-','-08-']
        # eightEnds = ['-07-','-08-','-09-']
        # nineEnds = ['-08-','-09-','-10-']
        # tenEnds = ['-09-','-10-','-11-']
        # elevenEnds = ['-10-','-11-','-12-']
        # twelveEnds = ['-11-','-12-','-01-']
        # returned_data = df[(df['start'].str.contains('-01-')==True) & (df['end'].isin(oneEnds) == True)]#df['end'].str.contains('-12-')==True)]
        # print('returned data in fy recs 01')
        # print(returned_data)
        # returned_data1 = df[(df['start'].str.contains('-02-')==True) & (df['end'].isin(twoEnds) == True)]
        # print('returned data in fy recs 02')
        # print(returned_data)
        # returned_data2 = df[(df['start'].str.contains('-03-')==True) & (df['end'].isin(threeEnds) == True)]
        # print('returned data in fy recs 03')
        # print(returned_data)
        # returned_data3 = df[(df['start'].str.contains('-04-')==True) & (df['end'].isin(fourEnds) == True)]
        # print('returned data in fy recs 04')
        # print(returned_data)
        # returned_data4 = df[(df['start'].str.contains('-05-')==True) & (df['end'].isin(fiveEnds) == True)]
        # print('returned data in fy recs 05')
        # print(returned_data)
        # returned_data5 = df[(df['start'].str.contains('-06-')==True) & (df['end'].isin(sixEnds) == True)]
        # print('returned data in fy recs 06')
        # print(returned_data)
        # returned_data6 = df[(df['start'].str.contains('-07-')==True) & (df['end'].isin(sevenEnds) == True)]
        # print('returned data in fy recs 07')
        # print(returned_data)
        # returned_data7 = df[(df['start'].str.contains('-08-')==True) & (df['end'].isin(eightEnds) == True)]
        # print('returned data in fy recs 08')
        # print(returned_data)
        # returned_data8 = df[(df['start'].str.contains('-09-')==True) & (df['end'].isin(nineEnds) == True)]
        # print('returned data in fy recs 09')
        # print(returned_data)
        # returned_data9 = df[(df['start'].str.contains('-10-')==True) & (df['end'].isin(tenEnds) == True)]
        # print('returned data in fy recs 10')
        # print(returned_data)
        # returned_data10 = df[(df['start'].str.contains('-11-')==True) & (df['end'].isin(elevenEnds) == True)]
        # print('returned data in fy recs 11')
        # print(returned_data)
        # returned_data11 = df[(df['start'].str.contains('-12-')==True) & (df['end'].isin(twelveEnds) == True)]
        # print('returned data in fy recs 12')
        # print(returned_data)

        #V2
        # returned_data = pd.concat([returned_data, returned_data1], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data2], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data3], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data4], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data5], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data6], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data7], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data8], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data9], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data10], ignore_index = True) 
        # returned_data = pd.concat([returned_data, returned_data11], ignore_index = True) 

#Just saved while editing
# def fillEmptyDivsGrowthRates(df):
#     try:
#         # print('we gr now')
#         # print(df)
#         df_filled = df
#         fixTracker = 0
#         if df_filled['interestPaid'].isnull().any():
#             fixTracker += 1
#             # print('it was int paid')
#             df_filled['interestPaid'] = df_filled['interestPaid'].ffill()#replace(np.NaN, None).ffill() 
#         if df_filled['totalDivsPaid'].isnull().any():
#             fixTracker += 1    
#             # print('it was total divs paid')
#             df_filled['totalDivsPaid'] = df_filled['totalDivsPaid'].replace(np.NaN, 0)#.ffill()
#         if df_filled['divsPaidPerShare'].isnull().any():
#             fixTracker += 1   
#             # print('it was per share divs paid')
#             df_filled['divsPaidPerShare'] = df_filled['divsPaidPerShare'].replace(np.NaN, 0)#.ffill()
#         if df_filled['shares'].isnull().all():
#             print('all shares null')
#         elif df_filled['shares'].isnull().any():
#             fixTracker += 1  
#             # print('it was shares')
#             # df_filled['shares'] = df_filled['shares'].replace(np.NaN, None).ffill() 
#             # df_filled['shares'] = df_filled['shares'].replace(np.NaN, None).bfill() 
#             # df_filled['shares'] = df_filled['shares'].ffill().bfill() 
#             # df_filled['shares'] = df_filled['shares'].bfill() 
#         if df_filled['sharesGrowthRate'].isnull().any():
#             # fixTracker += 1  
#             df_filled['sharesGrowthRate'] = df_filled['sharesGrowthRate'].fillna(df_filled['shares'].pct_change()*100)
#         if df_filled['divGrowthRate'].isnull().any():
#             df_filled['divGrowthRate'] = df_filled['divGrowthRate'].fillna(df_filled['divsPaidPerShare'].pct_change()*100)
#         # df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
#         # for x in tarList:
#         #     tarGrowthRate = x + 'GrowthRate'
#         #     meanReplacement = df_filled[x].mean()
#         #     savedCol = df_filled[x]
#         #     df_filled[x] = df_filled[x].replace(np.NaN, meanReplacement)#.ffill()
#         #     df_filled[tarGrowthRate] = df_filled[x].pct_change()*100
#             # if savedCol.equals(df_filled[x]):
#             #     continue
#             # else:
#             #     fixTracker += 1
#         if fixTracker == 4:
#             df_filled['integrityFlag'] = 'NeedsWork'
#         elif fixTracker == 0: 
#             df_filled['integrityFlag'] = 'Good'
#         else:
#             df_filled['integrityFlag'] = 'Acceptable'
#         return df_filled
#     except Exception as err:
#         print("fill empty divs GR error: ")
#         print(err)


### replaced above with better code
# def checkTechDivYears():
#     try:
#         incomeBadYears = pd.DataFrame(columns=['Ticker'])
#         divsBadYears = pd.DataFrame(columns=['Ticker'])
#         noIncData = pd.DataFrame(columns=['Ticker'])
#         noDivData = pd.DataFrame(columns=['Ticker'])

#         nameCheckList = tech['Ticker']
#         nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
#         incYearTracker = []
#         divTracker = []
#         toRecapture = []
#         incomeNullTracker = []
#         DivNullTracker = []
#         yearsList = ['2022','2023','2024']
#         version123 = '2'
#         for x in nameCheckList:
#             try:
#                
#                 incTable = makeIncomeTableEntry(x, '2024', version123, False)
#                 divsTable = makeDividendTableEntry(x, '2024', version123, False)
                
#                 #Checking if returned tables are just empty
#                 if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
#                     incomeNullTracker.append(x)
#                     if str(type(divsTable)) == "<class 'NoneType'>":#.empty:
#                         DivNullTracker.append(x)
#                         continue
#                 #checking latest data from the pull
#                 if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
#                     # print(str(x) + ' divYears are good!')
#                     divTracker.append(x)                

#                 if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
#                     # print(str(x) + ' incYears are good!')
#                     incYearTracker.append(x)     
#             except Exception as err:
#                 print("nested check tech years error: ")
#                 print(err)
#                 toRecapture.append(x)
#                 continue                

       
#     except Exception as err:
#         print("check tech years error: ")
#         print(err)
#         # toRecapture.append(x)
#         # continue
#     finally:
#         if len(incYearTracker) > 0:
#             incomeBadYears['Ticker'] = incYearTracker
#             csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

#         if len(divTracker) > 0:
#             divsBadYears['Ticker']=divTracker
#             csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

#         if len(incomeNullTracker) > 0:
#             noIncData['Ticker']=incomeNullTracker
#             csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

#         if len(DivNullTracker) > 0:
#             noDivData['Ticker']=DivNullTracker
#             csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

#         # for x in toRecapture:
#         #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
#         print(toRecapture) 

#might get deprecated!
# def dropDuplicatesInDF_property(df):
#     try:
#         filtered_data = pd.DataFrame()
#         filtered_data = df.drop_duplicates(subset=['val'])
#         filtered_data = df.drop_duplicates(subset=['end'], keep='last')
#     except Exception as err:
#         print("drop duplicates property error")
#         print(err)
#     finally:
#         return filtered_data

#deprecated
# def cleanShares(df):
#     try:
#         df_col_added = df.rename(columns={'val':'shares'})
#         df_col_added['year'] = df_col_added.end.str[:4]

#         return df_col_added

#     except Exception as err:
#         print("clean shares error: ")
#         print(err)

### Deprecated, being done elsewhere
# # Consolidate debt into TotalDebt csv
# def consolidateDebt(ticker, year): 
#     #in DB we use 'year', 'val', ticker, cik, still grabbing that end date
#     try:
#         dfShortDebt = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_shortTermDebt')
#         dfLongDebt1 = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_longTermDebt1')
#         dfLongDebt2 = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_longTermDebt2')
#         shortDict = {}
#         longDict1 = {}
#         longDict2 = {}
#         for x in range(len(dfShortDebt['end'])):
#             shortDict[dfShortDebt['end'][x][:4]] = dfShortDebt['val'][x]
#         for y in range(len(dfLongDebt1['end'])):
#             longDict1[dfLongDebt1['end'][y][:4]] = dfLongDebt1['val'][y]
#         for z in range(len(dfLongDebt2['end'])):
#             longDict2[dfLongDebt2['end'][z][:4]] = dfLongDebt2['val'][z]

#         totalDebtdict = dict(counter(shortDict) + counter(longDict1) + counter(longDict2))
#         tdebtholder = list(totalDebtdict.keys())
#         tdebtholder.sort() #make sure the keys(years) are in proper order for easier iteration later
#         sortedTotalDebt = {i: totalDebtdict[i] for i in tdebtholder}

#         returned_data = pd.DataFrame(sortedTotalDebt.items(), columns=['Year', 'Val'])

#         csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_TotalDebt', False)

#     except Exception as err:
#         print("consolidate debt error: ")
#         print(err)

###SAME, DEPRECATED, SEE ABOVE
#Consolidate TotalEquity csv
# def consolidateEquity(ticker, year):
#     #
#     try:
#         dfAssets = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_totalAssets')
#         dfLiabilities = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_totalLiabilities')
#         assetsDict = {}
#         liaDict = {}
#         for x in range(len(dfAssets['end'])):
#             assetsDict[dfAssets['end'][x][:4]] = dfAssets['val'][x]
#         for y in range(len(dfLiabilities['end'])):
#             liaDict[dfLiabilities['end'][y][:4]] = dfLiabilities['val'][y]

#         #If either assets or liabilities are missing each other's matching years, it'll throw off calculations later. Pop them outta' there!
#         noMatchingYear1 = []
#         noMatchingYear2 = []
#         for key in assetsDict:
#             if key not in liaDict:
#                 noMatchingYear1.append(key)
#         for key2 in liaDict:
#             if key not in assetsDict:
#                 noMatchingYear2.append(key2)
#         for x in noMatchingYear1:
#             assetsDict.pop(x,None)
#         for y in noMatchingYear2:
#             liaDict.pop(y,None)

#         totalEquitydict = dict(counter(assetsDict) - counter(liaDict))
#         teqholder = list(totalEquitydict.keys())
#         teqholder.sort() #make sure the keys(years) are in proper order for easier iteration later
#         sortedTotaEquity = {i: totalEquitydict[i] for i in teqholder}

#         returned_data = pd.DataFrame(sortedTotaEquity.items(), columns=['Year', 'Val'])

#         csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_TotalEquity', False)

#     except Exception as err:
#         print("consolidate debt error: ")
#         print(err)