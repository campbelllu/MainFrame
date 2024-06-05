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
        # LUKE RETHINK THIS
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

### LUKE
# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm
# Clean code: this includes packages up top, turns out.
# Automate setup of initial ciks, tickers, up top
#check below and keep your ear to the grindstone.


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
    

    df12 = pd.read_sql(thequery,conn)# WHERE Sector LIKE \'Basic Mat%\'  ;', conn)
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


# def delete_DB():
    #only use this while testing, or suffer the consequences
    conn = sql.connect(db_path)
    query = conn.cursor()

    # q = 'SELECT * FROM Mega ;'
    # query.execute(q)

    # table12.to_sql('Mega', conn, if_exists='append', index=False) # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html 

    # thequery = 'INSERT INTO Revenue (start,end,val,ticker,cik) VALUES ('+str(df13['start'])+',' +str(df13['end'])+',' +df13['val']+',' +df13['ticker']+',' +df13['cik']+');'
    # query.execute(thequery)
    # conn.commit()

    del_query = 'DELETE FROM Mega;'
    query.execute(del_query)
    conn.commit()

    # df12 = pd.DataFrame(query.execute('SELECT * FROM Revenue;'))

    df12 = pd.read_sql('SELECT * FROM Mega;', conn)
    print(df12)

    query.close()
    conn.close()
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
        # cleaned_list = [] #hey luke you commented this out in testing
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
            cleaned_list = [x for x in cleaned_list if not np.isinf(x)]
            # print('nums cleaning nans')
            # print(cleaned_list)
            # badNumbersMan = [0, 0.0]
            cleaned_list = [x for x in cleaned_list if x != 0]
            # print('final cleaned list')
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
        cleaned_list = list
        # if isinstance(list[0],float) or isinstance(list[0],int):
        #     cleaned_list = [x for x in list if not np.isnan(x)]
        # elif isinstance(list[0],str):# == <class 'str'>:
        #     cleaned_list = [eval(i) for i in list]
        # else:
        #     print('strip count type was not int or float')
        for x in cleaned_list:
            print(cleaned_list)
            # if x in (0, 0.0, '0', '0.0'):
            #     cleaned_list.remove(x)
            #     print(cleaned_list)
            if x == 0:
                cleaned_list.remove(x)
            if x == 0.0:
                cleaned_list.remove(x)
            if x == '0':
                cleaned_list.remove(x)
            if x == '0.0':
                cleaned_list.remove(x)
            print(cleaned_list)
        for x in cleaned_list:
            print(type(x))
        # print(list)
        #luke here. count non zeroes isn't removing some zeros. trippy
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

        if check > 0.5:
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

# isitalist = print_DB(testlistquery, 'return')['year'].tolist()
# print(isitalist)
# shareslist = print_DB(sharesquery, 'return')['sharesGrowthRate'].tolist()
# print(shareslist)

# print(nan_strip_min(shareslist))
# print(nan_strip_max(shareslist))
# print(nan_strip_count(shareslist))
# print(nan_strip_list(shareslist))

# print(nan_strip_min(isitalist))
# print(nan_strip_max(isitalist))
# print(len(shareslist))
# print(nan_strip_count(shareslist))
# print(count_nonzeroes(nan_strip_list(shareslist)))

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
        thequery = 'SELECT Ticker, Sector, Industry, Year, operatingCashflow, operatingCashflowGrowthRate, investingCashFlow, investingCashFlowGrowthRate, \
                        financingCashFlow, financingCashFlowGrowthRate, netCashFlow, netCashFlowGrowthRate, interestPaid, \
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
        repeqgravgint = zeroIntegrity(repeqlist)
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
        calceqgravgint = zeroIntegrity(calceqlist)
        calceqgravgnz = IQR_MeanNZ(calceqlist)

        metadata['calculatedEquityLow'] = calceqmin
        metadata['calculatedEquityGrowthAVG'] = calceqgravg
        metadata['calculatedEquityGrowthAVGintegrity'] = calceqgravgint
        metadata['calculatedEquityGrowthAVGnz'] = calceqgravgnz

        #equity avg... avg'd
        # aggeqmin = (repeqgrmin + calceqgrmin) / 2
        # aggeqmax = (repeqgrmax + calceqgrmax) / 2
        aggeqavg = (repeqgravg + calceqgravg) / 2

        metadata['mixedEquityGrowthAVG'] = aggeqavg

        #op cf min max avg
        opcflist = cfdf['operatingCashFlow'].tolist()
        opcfmin = nan_strip_min(opcflist)
        # opcfmax = nan_strip_max(opcflist)
        # opcfavg = IQR_Mean(opcflist)

        metadata['operatingCashFlowLow'] = opcfmin

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
        # invcfavg = IQR_Mean(invcflist)

        metadata['investingCashFlowLow'] = invcfmin

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
        # fincfavg = IQR_Mean(fincflist)

        metadata['financingCashFlowLow'] = fincfmin

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
        # netcfavg = IQR_Mean(netcflist)

        metadata['netCashFlowLow'] = netcfmin

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

        metadata['calcDivYieldLatest'] = cdpslatest / pricelatest * 100
        metadata['calcDivYieldAVG'] = cdpsavg / priceavg * 100
        metadata['repDivYieldLatest'] = dpslatest / pricelatest * 100
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
        print(faTable)
# fillMetadata('Utilities')
# uploadToDB(table,'Metadata')
#luke here
#then test NEE, AMZN, O, ARCC, MSFT, for any anomalies and call it good!
#MSFT: checking roc
# ROCpsAVG
# 0    0.0

# numYearsROCpaid
# 0    8

testticker11 = 'MSFT'
thedfofdfs = full_analysis(income_reading(testticker11), balanceSheet_reading(testticker11), cashFlow_reading(testticker11), dividend_reading(testticker11), efficiency_reading(testticker11))
# for col in thedfofdfs:
#     print(col)
#     print(thedfofdfs[col])
# print(thedfofdfs)
#luke i think your average isn't dropping nans before returning averages
print('roc big table')
print(thedfofdfs['numYearsROCpaid'])

# metadata['revGrowthAVG'] = revavg
        # metadata['revGrowthAVGintegrity'] = revavginteg
        # metadata['revGrowthAVGnz'] = revavgnz

        # metadata['netIncomeLow'] = nimin
        # metadata['netIncomeGrowthAVG'] = nigravg
        # metadata['netIncomeGrowthAVGintegrity'] = nigravgint
        # metadata['netIncomeGrowthAVGnz'] = nigravgnz


# print(thedfofdfs['repBookValueGrowthAVGintegrity'])
# print(thedfofdfs['revGrowthAVGnz'])

# print('orig poratio list')
# print(IQR_Mean(income_reading(testticker11)['netIncome']))


# print(income_reading(testticker11)['netIncome'])
#luke here
# print(efficiency_reading(testticker11))
divtable = dividend_reading(testticker11)
# efftable = efficiency_reading(testticker11)
# incometable = income_reading(testticker11)
# balancetable = balanceSheet_reading(testticker11)
# cftable = cashFlow_reading(testticker11)
# for x in efftable:
#     print(x)
#     print(efftable[x])

# print('roc lil table')
# print(divtable[['year','ROCperShareGrowthRate']])

# ROCTotal
# ROCperShare
# ROCperShareGrowthRate
# ROCTotalGrowthRate


# print('NI IQR ')
# print((IQR_MeanNZ(incometable['netIncomeGrowthRate'])))

# print('integrity:')
# print((zeroIntegrity(efftable['reportedBookValue'].tolist())))
# print('rep BV IQRnz ')
# print((IQR_MeanNZ(efftable['reportedBookValue'])))

# print('calc ROCE')
# print(efftable['calculatedRoce'])
# print('rep BV gr avg')
# print(thedfofdfs['repBookValueGrowthAVG'])
# print('above integrity')
# print(thedfofdfs['repBookValueGrowthAVGintegrity'])

# divsPaidPerShare
# calcDivsPerShare

# print(divtable['calcDivsPerShare'].iloc[-1])

# print(efftable['nav'])
# print('avg')
# print(IQR_Mean(efftable['nav']))
# print('no z')
# print(IQR_MeanNZ(efftable['nav']))

#BEP
#None test: reportedRoce
#Nan test: 
#inf test: reportedBookValue
#SO
#None: nav
# testluke = 'Select reportedBookValue from Mega Where Ticker LIKE \'BEP\''
# print(print_DB(testluke, 'return'))
# for x in efftable:
#     print(efftable[x])
# print(efftable)
# ['reportedBookValue'])

# for x in cftable:
#     if (cftable[x]==0).any():
#         print(x)
#         print(cftable[x])
        #luke remove zeroes from IQR mean so as to get better readings
        
# ughlist = [13.588072493527365, 13.588072493527365, 13.588072493527365, 13.588072493527365, 13.588072493527365, 13.588072493527365, 13.588072493527365, 13.588072493527365, 5.457825890843482, 17.6702751465945, 6.279434850863424, 13.588072493527365]
# print(IQR_Mean(ughlist))

# print('roce rep then calc min:')
# print(nan_strip_min(efficiency_reading('AMZN')['reportedRoce'].tolist()))
# print(nan_strip_min(efficiency_reading('AMZN')['calculatedRoce'].tolist()))

# print('roce rep then calc max:')
# print(nan_strip_max(efficiency_reading('AMZN')['reportedRoce'].tolist()))
# print(nan_strip_max(efficiency_reading('AMZN')['calculatedRoce'].tolist()))

# print('roce rep then calc avg:')
# print(IQR_Mean(efficiency_reading('AMZN')['reportedRoce'].tolist()))
# print(IQR_Mean(efficiency_reading('AMZN')['calculatedRoce'].tolist()))

# print(IQR_Mean(isitalist))

# time1 = time.time()
# time2 = time.time()
# print('time to complete')
# print((time2-time1)*1000)

# print(set(sourcelist).difference(dblist))

# print_ticker_DB('PAM')

# find_badUnitsDB()
# checkUnits_DB('HTOO') #again to see if it works. win! 

###### NO#######
# delete_DB()
########NO###########

#---------------------------------------------------------------------
#The testing zone - includes yahoo finance examples
#---------------------------------------------------------------------

lickit = [] 
# for x in lickit:
#     write_Master_csv_from_EDGAR(x,ultimateTagsList,'2024','2')
# checkYearsIntegrityList(lickit)

#weird clean units error : hdb
missingDepreNAmor = ['MSFT', 'TSM', 'AVGO', 'ORCL', 'SAP', 'INTU', 'IBM', 'TXN']
#LUKE possible amoritization add: CapitalizedComputerSoftwareAmortization1 
#it looks like depre and amor isn't getting the full picture for the above stocks
#realty income is good tho. interesting.


ticker235 = 'NEE'  #agnc, wmb, 
# print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker235]+'.json')
# write_Master_csv_from_EDGAR(ticker235,ultimateTagsList,'2024','2')
year235 = '2024'
version235 = '2'
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


ticker12 = 'O' #ABR
# print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker12]+'.json')
# write_Master_csv_from_EDGAR(ticker12,ultimateTagsList,'2024','2')
year12 = '2024'
version12 = '2'
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
# print(table12['TotalEquity'])
# print(table12[['year','depreNAmor']])
# print(table12['netIncomeNCI'])
# print(table12['Units'])
# print(table12)
# print(curConvert.currencies)

# print(table12['netIncomeNCIGrowthRate'])
# print(table12.loc[table12['Units']=='TWD']['netIncome'])
# print(table12.loc[table12['Units']=='USD']['netIncome'])

#################


ticker100 = 'ARCC' #ABR
year100 = '2024'
version100 = '2'
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



ticker13 = 'MSFT' 
year13 = '2024'
version13 = '2'
# print(ticker13 + ' income:')
# print(makeIncomeTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + ' divs:')
# print(makeDividendTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + '  roic: ')
# print(makeROICtableEntry(ticker13,'2024',version13,False))

ticker12 = 'NEE' 
year12 = '2024'
version12 = '2'
# print(ticker12 + ' income:')
# print(makeIncomeTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs:')
# print(makeDividendTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' roic: ')
# print(makeROICtableEntry(ticker12,'2024',version12,False))

ticker14 = 'O' #EGP
year14 = '2024'
version14 = '2'
# print(ticker14 + ' income:')
# print(makeIncomeTableEntry(ticker14,year14,version14,False))
# print(ticker14 + ' divs:')
# print(makeDividendTableEntry(ticker14,'2024',version14,False))
# print(ticker14 + '  roic: ')
# print(makeROICtableEntry(ticker14,'2024',version14,False))

ticker234 = 'ARCC'
year234 = '2024'
version234 = '2'
# print(ticker234 + ' income:')
# print(makeIncomeTableEntry(ticker234,year234,version234,False))
# print(ticker234 + ' divs:')
# print(makeDividendTableEntry(ticker234,year234,version234,False))
# print(ticker234 + ' roic: ')
# print(makeROICtableEntry(ticker234,year234,version234,False))


ticker123 = 'AMZN' #AMZN
year123 = '2024'
version123 = '2'
# print('AMZN income:')
# print(makeIncomeTableEntry(ticker123,'2024',version123,False))
# print('AMZN divs:')
# print(makeDividendTableEntry(ticker123,'2024',version123,False))
# print('AMZN roic: ')
# print(makeROICtableEntry(ticker123,'2024',version123,False))

# ticker = 'MSFT'
# stock = yf.Ticker(ticker)
# dict1 = stock.info
# marketCap = dict1['marketCap']

# # pe = dict1['pe']
# # for x in dict1:
# #     print(x)
# print(marketCap)

# print(set(fullNulls).difference(yearsOff))
# print(set(fullNulls).difference(fullNulls))

# print(set(divsYearsOff).intersection(incYearsOff))
# fullNullOverlap = set(incFullNulls).intersection(divsFullNulls)
# yearsOffOverlap = set(divsYearsOff).intersection(incYearsOff)
# print(fullNullOverlap)
# print(yearsOffOverlap)
# print(set(fullNullOverlap).intersection(yearsOffOverlap))


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