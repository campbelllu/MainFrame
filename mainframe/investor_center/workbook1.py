import numpy as np
import pandas as pd
# import pandas_datareader.data as web
#docu: https://pandas-datareader.readthedocs.io/en/latest/ 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import datetime as dt
import mplfinance as mpf
import datetime as dt
import time
import yfinance as yf
import json
import pyarrow
import requests
import math
# from itertools import chain
from collections import Counter as counter
import sqlite3 as sql
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning) #infer_objects(copy=False) works nonreliably. SO WE JUST SQUELCH IT ALTOGETHER!

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

fr_iC_toSEC = '../sec_related/'
fr_iC_toSEC_stocks = '../sec_related/stocks/' 
stock_data = './stockData/'

db_path = '../stock_data.sqlite3'

#Set types for each column in df, to retain leading zeroes upon csv -> df loading.
type_converter = {'Ticker': str, 'Company Name': str, 'CIK': str}
type_converter_full = {'Ticker': str, 'Company Name': str, 'CIK': str, 'Sector': str, 'Industry': str, 'Market Cap': str}
type_converter_full2 = {'Ticker': str, 'Company Name': str, 'CIK': str, 'Sector': str, 'Industry': str}#, 'Market Cap': str}

full_cik_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickers_and_ciks', type_converter)
full_cik_sectInd_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickersCik_sectorsInd', type_converter_full)
clean_stockList = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_stockList_clean', type_converter_full2)
nameCikDict = clean_stockList.set_index('Ticker')['CIK'].to_dict()

materials = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Basic Materials_Sector_clean', type_converter_full2)
comms = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Communication Services_Sector_clean', type_converter_full2)
consCyclical = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Cyclical_Sector_clean', type_converter_full2)
consStaples = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Consumer Defensive_Sector_clean', type_converter_full2)
energy = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Energy_Sector_clean', type_converter_full2)
financial = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'Financial Services_Sector_clean', type_converter_full2)
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

#organizing data titles into variable lists
# altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
# cashOnHand = ['CashCashEquivalentsAndShortTermInvestments', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 
#                 'CashAndCashEquivalentsAtCarryingValue', 'CashEquivalentsAtCarryingValue', 
#                 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations']
netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 
                'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect', 'IncreaseDecreaseInCashAndCashEquivalents',
                'CashAndCashEquivalentsPeriodIncreaseDecrease','IncreaseDecreaseInCashAndCashEquivalentsBeforeEffectOfExchangeRateChanges'] #operCF + InvestCF + FinancingCF
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities','CashFlowsFromUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 
                    'NetCashProvidedByUsedInContinuingOperations', 'CashFlowsFromUsedInOperationsBeforeChangesInWorkingCapital']
investingCashFlow = ['CashFlowsFromUsedInInvestingActivities','NetCashProvidedByUsedInInvestingActivities']
financingCashFlow = ['CashFlowsFromUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivities']
revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenueFromContractsWithCustomers', 'SalesRevenueNet', 'Revenues', 'RealEstateRevenueNet', 
            'Revenue','RevenueFromContractWithCustomerIncludingAssessedTax','RetainedEarnings','GrossInvestmentIncomeOperating'] #banks?! GrossInvestmentIncomeOperating
netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 
                'ProfitLossAttributableToOwnersOfParent','ProfitLoss']
operatingIncome = ['OperatingIncomeLoss','ProfitLossFromOperatingActivities'] #IDK if REITS even have this filed with SEC. Finding it from SEC is hard right now.
taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense','FinanceCosts','InterestExpenseDebt','InterestAndDebtExpense','InterestIncomeExpenseNet','InterestIncomeExpenseNonoperatingNet',
                'FinancingInterestExpense','InterestPaidNet','InterestRevenueExpense']
incomeTaxPaid = ['IncomeTaxExpenseContinuingOperations']
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
shareHolderEquity = ['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest']

exchangeRate = ['EffectOfExchangeRateChangesOnCashAndCashEquivalents'] #LUKE You'll want to know this is here eventually

capEx = ['PaymentsToAcquirePropertyPlantAndEquipment','PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities',
        'PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets','PaymentsToAcquireProductiveAssets',
        'PaymentsForCapitalImprovements','PaymentsToAcquireOtherPropertyPlantAndEquipment','PaymentsForProceedsFromProductiveAssets'] #NetCashProvidedByUsedInInvestingActivities # possible addition, questionable
totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends','DividendsCommonStock','DividendsCommonStockCash',
                            'DividendsPaidClassifiedAsFinancingActivities','DividendsPaid','DividendsPaidToEquityHoldersOfParentClassifiedAsFinancingActivities',
                            'PartnersCapitalAccountDistributions','DividendsPaidOrdinaryShares'] #DividendsPaid could be useful later
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid','InvestmentCompanyDistributionToShareholdersPerShare',
                                        'DistributionMadeToLimitedPartnerDistributionsPaidPerUnit']
eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare','BasicEarningsLossPerShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic', 'EntityCommonStockSharesOutstanding','WeightedAverageShares', 'CommonStockSharesOutstanding',
                           'WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted', 'NumberOfSharesIssued']
gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes',
                    'GainsLossesOnSalesOfInvestmentRealEstate']
deprecAndAmor = ['DepreciationDepletionAndAmortization','Depreciation','DepreciationAmortizationAndAccretionNet','AmortizationOfIntangibleAssets',
                    'AdjustmentsForDepreciationAndAmortisationExpense','DeferredTaxLiabilityAsset','AdjustmentsForDepreciationExpense']
deprecAndAmor2 = ['AmortizationOfMortgageServicingRightsMSRs']
deprecAndAmor3 = ['DepreciationAndAmortization']

netAssetValue = ['NetAssetValuePerShare'] #Luke don't forget to add this into a table somewhere

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, longTermDebt3, longTermDebt4, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow, 
                investingCashFlow, financingCashFlow, exchangeRate, incomeTaxPaid, currentLiabilities, nonCurrentLiabilities, deprecAndAmor2, 
                deprecAndAmor3, shareHolderEquity, currentAssets, nonCurrentAssets, netAssetValue ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'exchangeRate', 'longTermDebt3', 'longTermDebt4', 'incomeTaxPaid', 'currentLiabilities','nonCurrentLiabilities',
                'deprecAndAmor2', 'deprecAndAmor3', 'shareHolderEquity', 'currentAssets','nonCurrentAssets', 'netAssetValue']
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
        #First we check for the full year reportings
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
        #Now checking for those halfies because some companies just file things weirdly.
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

        

        

        #Monthly reporting sometimes also throws things off. 
        if returned_data.empty:
            listMax = df.end.str[5:7]
            tarMax = str(listMax.max())
            held_data = df[df['end'].str.contains(tarMax)==True] #held_data
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
           
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
            filtered_data['year8'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 6)
            filtered_data['year9'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 7)
            filtered_data['year10'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 8)
            filtered_data['year11'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 9)  #, other=filtered_data['yearMinusOne'])
            filtered_data['year12'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 10)
            filtered_data['year13'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 11)
            filtered_data['year14'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 12)


            filtered_data['year'] = filtered_data['year8'].fillna(filtered_data['year9'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year10'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year11'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year12'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year13'])#.infer_objects(copy=False)
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['year14'])
            filtered_data['year'] = filtered_data['year'].fillna(filtered_data['yearMinusOne'])
         
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
            filtered_data['year3'] = filtered_data['endYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] >= 5)) #changed here from 6; Luke wtf records wtf
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
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            
            held_data = filtered_data[filtered_data['Tag'].eq(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
            # print(x)
            # if 'PerShare' in x:
            #     print('in consolidate')
            #     print(returned_data)
        returned_data = get_Only_10k_info(returned_data)
        # print('10k data')
        # print(returned_data)
        # print(returned_data.shape)
        
        # print('pre drop fy records')
        # print(returned_data.to_string())
        
        returned_data = dropAllExceptFYRecords(returned_data) #was held data
        # print('post drop fy records pre order')
        # print(returned_data)
        # print(returned_data.shape)
        returned_data = orderAttributeDF(returned_data) #moved from above fy records. so we gather 10k, all fy, then order then drop dupes
        # print('post order pre drop  dupes')
        # print(returned_data)
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

def cleanRevenue(df):
    try:
        # print('df')
        # print(df)
        df_col_added = df.rename(columns={'val':'revenue'})
        if df_col_added.empty:
            return df_col_added
        else:
            # if df_col_added['revenue'].empty:
            #     df_col_added['revenueGrowthRate'] = np.NaN
            # else:
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
       
            return df_col_added

    except Exception as err:
        print("cleanRevenue error: ")
        print(err)
        # print(df_col_added)

def cleanNetIncome(df):
    try:
        df_col_added = df.rename(columns={'val':'netIncome'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['netIncome'])
            df_col_added['netIncomeGrowthRate'] = growthCol#df_col_added['netIncome'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("cleanNetIncome error: ")
        print(err)

def cleanOperatingCashFlow(df):
    try:
        df_col_added = df.rename(columns={'val':'operatingCashFlow'})
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
        df_col_added = df.rename(columns={'val':'investingCashFlow'})
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
        df_col_added = df.rename(columns={'val':'financingCashFlow'})
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
        df_col_added = df.rename(columns={'val':'netCashFlow'})
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
        df_col_added = df.rename(columns={'val':'capEx'})
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
        df_col_added = df.rename(columns={'val':'eps'})
        if df_col_added.empty:
            return df_col_added
        else:
            growthCol = grManualCalc(df_col_added['eps'])
            df_col_added['epsGrowthRate'] = growthCol#df_col_added['eps'].pct_change()*100
            # df_col_added['year'] = df_col_added.end.str[:4]

            # df_col_added = df_col_added.drop(columns=['start','end']) 

            return df_col_added

    except Exception as err:
        print("clean eps error: ")
        print(err)

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
        df_col_added = df.rename(columns={'val':'operatingIncome'})
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

        if liabilities.empty:
            liabilities = cleanLiabilities(ncL, cuL)
        # print('liabilities?!?')
        # print(liabilities)
        # print('assets?')
        # print(assets)
        #Because Equity is important to calculations, we need to verify non-reported values as being a lower approximation of the mean of all liabilities over time. LUKE RETHINK THIS
        assAndLies = pd.merge(assets, liabilities, on=['year','Ticker','CIK','Units'], how='outer')
        
        # print('post merge')
        # print(assAndLies)
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
        # assAndLies['ReportedTotalEquity'] = reportedEquity
        # print('TEquity checker')
        # print(assAndLies)

        return assAndLies

    except Exception as err:
        print("clean totalEquity error: ")
        print(err)

def cleanDeprNAmor(df):
    try:
        df_col_added = df.rename(columns={'val':'depreNAmor'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added
    except Exception as err:
        print("clean deprNAmor error: ")
        print(err)

def cleanDeprNAmor2(df1,df2):
    try:
        df_col_added = df1.rename(columns={'val':'depreNAmor1'})
        # df_col_added['year'] = df_col_added.end.str[:4]
        # df_col_added = df_col_added.drop(columns=['start','end'])

        df2 = df2.rename(columns={'val':'depreNAmor2'})
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
        df_col_added = df.rename(columns={'val':'gainSaleProp'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added
    except Exception as err:
        print("clean gainSaleProp error: ")
        print(err)

def cleanInterestPaid(df):
    try:
        df_col_added = df.rename(columns={'val':'interestPaid'})
        # df_col_added['year'] = df_col_added.end.str[:4]

        # df_col_added = df_col_added.drop(columns=['start','end'])

        return df_col_added

    except Exception as err:
        print("clean interestPaid error: ")
        print(err)

#ASML case study: shares are working. per share works, but throws off data as nulls are filled because total paid loads fine, but then we try to fill nulls both ways and make a bunch of nulls.
def cleanDividends(total, perShare, shares): 

    try:
        # shares['year'] = shares.end.str[:4]
        shares = shares.rename(columns={'val':'shares'})
        shares = shares.drop(columns=['Units'])
        # total['year'] = total.end.str[:4]
        total = total.rename(columns={'val':'totalDivsPaid'})
        # perShare['year'] = perShare.end.str[:4]
        perShare = perShare.rename(columns={'val':'divsPaidPerShare'})
        perShare = perShare.drop(columns=['Units'])

        # shares = shares.drop(columns=['start','end'])
        # total = total.drop(columns=['start','end'])
        # perShare = perShare.drop(columns=['start','end'])

        # print('shares, total, pershare: ')
        # print(shares)
        # print(total)
        # print(perShare)
        df_col_added = pd.merge(total, perShare, on=['year','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(shares, df_col_added, on=['year','Ticker','CIK'], how='outer')
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
        df_col_added['tempPerShare'] = df_col_added['totalDivsPaid'] / df_col_added['shares']
        df_col_added['tempTotalDivs'] = df_col_added['divsPaidPerShare'] * df_col_added['shares']
        df_col_added['tempShares'] = df_col_added['totalDivsPaid'] / df_col_added['divsPaidPerShare']
        # print('tot and pshare post temps')
        # print(df_col_added)

        for x in nanList: #Values in ex-US currencies seem weird versus common stock analysis sites. Could be an exchange rate issue I haven't accounted for in the exchange to USD.
            if x == 'divsPaidPerShare':
                df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['tempPerShare'])
                # growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
                # df_col_added['divGrowthRate'] = growthCol1 
            elif x == 'totalDivsPaid':
                df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
                # growthCol1 = grManualCalc(df_col_added['divsPaidPerShare'])
                # df_col_added['divGrowthRate'] = growthCol1 
        df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempPerShare','tempShares'])
        # print('tot and pshare post fills and drops')
        # print(df_col_added)
        
        # if shares.empty:# and total.empty and perShare.empty: #LUKE maybe double check everything's working via checks, but this work around is deprecated
        #     cols = {'Units': -1, 'Ticker': -1, 'CIK': -1, 'year': -1, 'totalDivsPaid': -1, 'shares': -1,
        #              'divsPaidPerShare': -1, 'sharesGrowthRate': -1, 'divGrowthRate': -1, 'integrityFlag': -1}#, 'Ticker': total['Ticker'] #'interestPaid': -1, 'start': -1, 'end': -1,
        #     # vals = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        #     df_col_added = pd.DataFrame(cols, index=[0])
        #     return df_col_added
        #     # shares['val'] = 1
        # else:
            # sharesNperShare = pd.merge(shares, perShare, on=['year','Ticker','CIK'], how='outer')#'start','end',
            # print('sharesNperShare: ')
            # print(sharesNperShare)
            # df_col_added = pd.merge(total, sharesNperShare, on=['year','Ticker','CIK'], how='outer')
            # print('total + shares + per share: ')
            # print(df_col_added)
        df_col_added['shares'] = df_col_added['shares'].ffill().bfill() #.replace("", None) pre ffillbfill
        # if df_col_added['shares'].empty:
        #     df_col_added['sharesGrowthRate'] = np.NaN
        # else:
        growthCol = grManualCalc(df_col_added['shares'])
        df_col_added['sharesGrowthRate'] = growthCol #df_col_added['shares'].pct_change()*100 #now we can add the growth rate once nulls filled
        # df_col_added['sharesGrowthRate'] = df_col_added['sharesGrowthRate'].replace(np.nan,0) #fill in null values so later filter doesn't break dataset

        


        # df42 = pd.DataFrame()
        # df42['temp'] = df_col_added['tempPerShare']
        # df42['actual'] = df_col_added['divsPaidPerShare']
        # print(df42)

        

        growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
        df_col_added['divGrowthRateBOT'] = growthCol1 
        growthCol2 = grManualCalc(df_col_added['divsPaidPerShare'])
        df_col_added['divGrowthRateBOPS'] = growthCol2
        
        # if df_col_added['divsPaidPerShares'].empty:
        #     df_col_added['divGrowthRate'] = np.NaN
        # else:
        
        # print('average growth rate: ')
        # print(df_col_added['divGrowthRate'].mean())

        # return df_col_added
    except Exception as err:
        print("clean dividends error: ")
        print(err)
    finally:
        return df_col_added



def fillEmptyIncomeGrowthRates(df):
    try:
        tarList = ['revenue','netIncome','operatingCashFlow','investingCashFlow','financingCashFlow','netCashFlow', 'capEx','depreNAmor']
        df_filled = df
        fixTracker = 0
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

        
        # if df_filled['depreNAmor'].isnull().any():
        #     percentNull = df_filled['depreNAmor'].isnull().sum() / len(df_filled['depreNAmor'])
        #     if percentNull > 0.4:
        #         fixTracker += 1
        #     # fixTracker += 1  
        #     # print('it was shares')
        #     df_filled['depreNAmor'] = df_filled['depreNAmor'].ffill().bfill() 


        if fixTracker > 4:
            df_filled['integrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['integrityFlag'] = 'Good'
        else:
            df_filled['integrityFlag'] = 'Acceptable'
        return df_filled
    except Exception as err:
        print("fill empty inc GR error: ")
        print(err)

def fillEmptyDivsGrowthRates(df):
    try:
        df_filled = df
        fixTracker = 0

        if df_filled['interestPaid'].isnull().any():
            percentNull = df_filled['interestPaid'].isnull().sum() / len(df_filled['interestPaid'])
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



        # print('pre shares and div GR')
        # print(df_filled)
        if df_filled['sharesGrowthRate'].isnull().any():
            # fixTracker += 1  
            growthCol = grManualCalc(df_filled['shares'])
            df_filled['temp1'] = growthCol
            df_filled['sharesGrowthRate'] = df_filled['sharesGrowthRate'].fillna(df_filled.pop('temp1'))#['temp1'])
            # df_filled = df_filled.drop(columns=['temp1'])
            # print('shares  GR')
            # print(df_filled)
            
        if df_filled['divGrowthRateBOT'].isnull().any():
            growthCol = grManualCalc(df_filled['totalDivsPaid'])
            df_filled['temp2'] = growthCol
        #     
            df_filled['divGrowthRateBOT'] = df_filled['divGrowthRateBOT'].fillna(df_filled.pop('temp2'))#['temp2'])
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)

        if df_filled['divGrowthRateBOPS'].isnull().any():
            growthCol = grManualCalc(df_filled['divsPaidPerShare'])
            df_filled['temp3'] = growthCol
        #     
            df_filled['divGrowthRateBOPS'] = df_filled['divGrowthRateBOPS'].fillna(df_filled.pop('temp3'))#['temp2'])
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)


        # df_filled = df_filled.drop(columns=['temp1'])
        
        # print('ppost drop shares and div GR')
        # print(df_filled)
        # print('fixTracker')
        # print(fixTracker)
        if fixTracker >= 4:
            df_filled['integrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['integrityFlag'] = 'Good'
        else:
            df_filled['integrityFlag'] = 'Acceptable'
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
        tarList = ['operatingIncome','netIncome']
        tDebt = 'TotalDebt'
        equityParts = ['assets','liabilities']
        equityFlag = 0

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
        df_filled = df_filled.drop(columns=['netIncomeGrowthRate'])

        if df_filled['TotalDebt'].isnull().any():
            percentNull = df_filled['TotalDebt'].isnull().sum() / len(df_filled['TotalDebt'])
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['TotalDebt'] = df_filled['TotalDebt'].replace(np.NaN, 0)
        if df_filled['assets'].isnull().any():
            percentNull = df_filled['assets'].isnull().sum() / len(df_filled['assets'])
            if df_filled['assets'].isnull().sum() > 1:
                equityFlag = 1
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['assets'] = df_filled['assets'].ffill().bfill()
        if df_filled['liabilities'].isnull().any():
            percentNull = df_filled['liabilities'].isnull().sum() / len(df_filled['liabilities'])
            if df_filled['liabilities'].isnull().sum() > 1:
                equityFlag = 1
            if percentNull > 0.4:
                fixTracker += 1
            # print('it was int paid')
            df_filled['liabilities'] = df_filled['liabilities'].ffill().bfill()
        # if equityFlag == 1:
        df_filled['TotalEquity'] = df_filled['TotalEquity'].fillna(df_filled['assets'] - df_filled['liabilities'])

        
        if fixTracker > 4:
            df_filled['integrityFlag'] = 'NeedsWork'
        elif fixTracker == 0: 
            df_filled['integrityFlag'] = 'Good'
        else:
            df_filled['integrityFlag'] = 'Acceptable'

        # print('ppost int flag added')
        # print(df_filled)

    except Exception as err:
        print("fill empty ROIC GR error: ")
        print(err)

    finally:
        # print('in finally df filled')
        # print(df_filled)
        return df_filled

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
        revNinc = pd.merge(rev_df, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')#'start','end',
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
        addfcfMargin['gainSaleProp']=addfcfMargin['gainSaleProp'].replace(np.nan,0)
        # print('addfcfMargin: ')
        # print(addfcfMargin)

        addfcfMargin['ffo'] = addfcfMargin['netIncome'] + addfcfMargin['depreNAmor'] - addfcfMargin['gainSaleProp']
        growthCol = grManualCalc(addfcfMargin['ffo'])
        addfcfMargin['ffoGrowthRate'] = growthCol#addfcfMargin['ffo'].pct_change(fill_method=None)*100

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
        # print('opIncNtax')
        # print(opIncNtax)
        if opIncNtax['Units'].isnull().all():
            opIncNtax = opIncNtax.drop(columns=['Units'], axis=1)
            # print('opincntax df in empty if')
            # print(opIncNtaxNinc)
            # print(opIncNtax)
            opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK'], how='outer')
            # print('still in iff post merge')
            # print(opIncNtaxNinc)
        else:


            opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
            opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])
        # print('opincntax df after if')
        # print(opIncNtaxNinc)
        # print(opIncNtax)

        
        plustDebt = pd.merge(opIncNtaxNinc, totalDebt_df, on=['year','Ticker','CIK','Units'], how='outer')
        # print('plusdebt df')
        # print(plustDebt)
        # plustDebt = plustDebt.rename(columns={'start_x': 'start'})
        # plustDebt = plustDebt.drop(['start_y'],axis=1)
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year','Ticker','CIK','Units'], how='outer')
        # plustEquity = plustEquity.rename(columns={'start_x': 'start'})
        # plustEquity = plustEquity.drop(['start_y'],axis=1)
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
                                    consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False))
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

            inNdivs = fillEmptyDivsGrowthRates(intNdivs)

            # print('post fill intndivs: ')
            # print(intNdivs)

            return intNdivs
    
    except Exception as err:
        print("makeDividend table error: ")
        print(err)
    
    # print('you got this!')

def checkYearsIntegritySector(sector,begNum,endNum):
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
        yearsList = ['2023','2024'] #2022
        version123 = '2'

        for x in nameCheckList:
            print(x)
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
                # if roicTable['TotalEquity'].isnull().any():
                #     rTotalEq.append(x)
                if roicTable['TotalEquity'].isnull().any():
                    if roicTable['ReportedTotalEquity'].isnull().any():
                        rTotalEq.append(x)
                
                 
            except Exception as err:
                print("nested check years integrity error: ")
                print(err)
                toRecapture.append(x)
                continue             


    except Exception as err:
        print("check years integrity error: ")
        print(err)

    finally:
        print('recap list: ')
        print(toRecapture)
        # print('missing income years:')
        # print(incMissingYearTracker)
        print('wrong income end year')
        print(incomeEndYearTracker)
        print('missing income revenue')
        print(incRev)
        print('missing income netIncome')
        print(incNetInc)
        print('missing income opCF')
        print(incOpCF)
        print('missing income capEx')
        print(incCapEx)
        print('missing income netCF')
        print(incNetCF)
        print('missing income depreNAmor')
        print(incDepnAmor)
        print('missing income prop sales')
        print(incGainProp)
        # print('missing div years:')
        # print(dMissingYearTracker)
        print('wrong div end year')
        print(dEndYearTracker)
        print('missing div intPaid')
        print(dIntPaid)
        print('missing div totalPaid')
        print(dTotalPaid)
        print('missingDivSharesPaid = ')
        print(dSharesPaid)
        print('missing div shares')
        print(dShares)
        # print('missing roic years:')
        # print(rMissingYearTracker)
        print('wrong roic end year')
        print(rEndYearTracker)
        print('missing roic total equity')
        print(rTotalEq)
        
lickit = [ ] #equity
#

# for x in lickit:
#     write_Master_csv_from_EDGAR(x,ultimateTagsList,'2024','2')
# checkYearsIntegrityList(lickit)
checkYearsIntegritySector(realEstate,9,10)

# print(len(lickit))

ticker12 = 'SJW' #ABR
print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker12]+'.json')
# write_Master_csv_from_EDGAR(ticker12,ultimateTagsList,'2024','2')
year12 = '2024'
version12 = '2'
# print(ticker12 + ' income:')
# print(makeIncomeTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs:')
# print(makeDividendTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' roic: ')
# print(makeROICtableEntry(ticker12,'2024',version12,False))


ticker235 = 'NWN' 
print('https://data.sec.gov/api/xbrl/companyfacts/CIK'+nameCikDict[ticker235]+'.json')
# write_Master_csv_from_EDGAR(ticker235,ultimateTagsList,'2024','2')
year235 = '2024'
version235 = '2'
# print(ticker235 + ' income:')
# print(makeIncomeTableEntry(ticker235,year235,version235,False))
# print(ticker235 + ' divs:')
# print(makeDividendTableEntry(ticker235,year235,version235,False))
# print(ticker235 + '  roic: ')
# print(makeROICtableEntry(ticker235,year235,version235,False))



# print(consolidateSingleAttribute(ticker235, year235, version235, totalAssets, False))
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

#refined screener results:
###NEW Materials
# recapList =
# ['RTNTF', 'SHECY', 'GLNCY', 'PTCAY', 'HDELY', 'MTLHY', 'AU', 'BDNNY', 'BZZUY', 'FUPBY', 'JSCPY', 'PUTKY', 'SHWDY', 'BBMPY', 'KOZAY', 'SLVYY', 'OUTKY', 'WS', 'PDO', 'CARCY', 'WTTR', 'LAC', 'RUPRF', 'AMLI', 'NWGL', 'LOMLF', 'FFMGF', 'ERDCF', 'ORRCF', 'WMLLF', 'SPAZF', 'GSVRF', 'AIRRF', 'UURAF', 'SVRSF', 'SMDRF', 'EQTRF', 'LISMF', 'AGXPF', 'LILIF', 'PAANF', 'AAU', 'TETOF', 'TRBMF', 'GSHRF', 'HGAS', 'GFGSF', 'JGLDF', 'AUCUF', 'HANNF', 'RSMXF', 'MXROF', 'GXSFF', 'FEMFF', 'EQMEF', 'SRLZF', 'VAUCF', 'TIGCF', 'GESI', 'NMREF', 'EVGDF', 'PBMLF', 'GARWF', 'CXXMF', 'NULGF', 'SILS', 'CGOLF', 'NVSGF', 'BMXI', 'BATXF', 'BKTPF', 'FMNJ', 'PMCOF', 'BGAVF', 'KNGRF', 'ZPHYF', 'ABCFF', 'NVDEF', 'ORMNF', 'EGMCF', 'BITTF', 'MEXGF', 'ABNAF', 'INUMF', 'SMREF', 'AVPMF', 'SIXWF', 'LNZNF', 'UBEOF', 'SGTM', 'OCGSF', 'RYTTF', 'MLLOF', 'DMXCF']
# missingRevenue =
# ['GATO', 'TMC', 'GDRZF', 'IPI', 'DC', 'PPTA', 'CTGO', 'ASPI', 'THM', 'NB', 'FEAM', 'TMQ', 'USGO', 'AUGG', 'XTGRF', 'TMRC', 'HGAS', 'RYES', 'SVBL', 'SCYYF', 'AHNR', 'TARSF', 'GNTOF', 'ATAO', 'SRGZ', 'MNGG', 'GKIN', 'MLYF']    
# missingNetIncome =
# ['AAU']
# missingOpCF =
# ['SLI', 'GLDG']
# missingCapEx =
# ['WPM', 'RGLD', 'ICL', 'BTG', 'TFPM', 'SAND', 'FSM', 'NGD', 'LZM', 'TMC', 'ANVI', 'MSB', 'MTA', 'RBTK', 'WRN', 'YCQH', 'NGLD', 'VOXR', 'XPL', 'CRCUF', 'PZG', 'LCGMF', 'AXREF', 'HGAS', 'FMST', 'NRHI', 'NMEX', 'AHNR', 'GRMC', 'THMG', 'ATAO', 'SRGZ', 'MNGG', 'AMRSQ', 'CGSI', 'SMTSF', 'JSHG', 'RLEA', 'GNVR']
# missingNetCF =
# ['VZLA']
# missingDepreNAmor =
# ['BHP', 'RIO', 'SHW', 'NUE', 'PKX', 'NTR', 'MT', 'FNV', 'WPM', 'TECK', 'SUZ', 'SQM', 'CX', 'GGB', 'TX', 'UFPI', 'KGC', 'WFG', 'ICL', 'SSL', 'SIM', 'PAAS', 'AGI', 'BVN', 'HMY', 'BTG', 'SBSW', 'MEOH', 'BAK', 'CSTM', 'OR', 'TFPM', 'EGO', 'HBM', 'ERO', 'SGML', 'EQX', 'AG', 'SAND', 'IAG', 'LOMA', 'ORLA', 'CGAU', 'GSM', 'LVRO', 'NEXA', 'FSM', 'MAG', 'NGD', 'SA', 'ASTL', 'SILV', 'NG', 'BIOX', 'ASIX', 'LAC', 'LAAC', 'DRD', 'MTAL', 'NFGC', 'ODC', 'LZM', 'GATO', 'CPAC', 'ARMN', 'SVM', 'TMC', 'IAUX', 'TGB', 'SKE', 'GDRZF', 'EXK', 'ANVI', 'VZLA', 'IPX', 'SLI', 'MSB', 'MTA', 'ODV', 'NEWP', 'GAU', 'CMCL', 'GROY', 'PNRLF', 'DC', 'PPTA', 'WRN', 'IONR', 'EMX', 'GLDG', 'CTGO', 'ASPI', 'VRDR', 'NAK', 'NMG', 'NTIC', 'LGO', 'FRD', 'ABAT', 'PLG', 'YCQH', 'NB', 'TRX', 'NGLD', 'VOXR', 'FFMGF', 'USGO', 'STCB', 'ASM', 'ITRG', 'FURY', 'USAS', 'AUGG', 'LONCF', 'RNGE', 'ELBM', 'LBSR', 'INHD', 'CRCUF', 'ZKIN', 'PZG', 'AAU', 'LCGMF', 'AXREF', 'LITM', 'HGAS', 'FMST', 'NRHI', 'AUST', 'ARRKF', 'NMEX', 'FUST', 'QZMRF', 'PBMLF', 'PGOL', 'AHNR', 'TARSF', 'ENRT', 'ATAO', 'WOLV', 'HHHEF', 'AVPMF', 'GKIN', 'GPLDF', 'RMESF', 'MKDTY', 'AMNL', 'ALMMF', 'ERLFF', 'NSRCF', 'MPVDF', 'SMTSF', 'AVLNF', 'SHVLF', 'SILEF', 'JSHG', 'EXNRF', 'GIGGF']
# missing income prop sales
# []
# missingIntPaid =
# ['CX', 'RGLD', 'ALTM', 'HCC', 'MAG', 'WLKP', 'SKE', 'ANVI', 'VZLA', 'NEWP', 'DC', 'PPTA', 'WRN', 'THM', 'YCQH', 'VOXR', 'USGO', 'ITRG', 'BHIL', 'ELBM', 'COPR', 'CRCUF', 'AAU', 'AUST', 'ARRKF', 'BGLC', 'PGOL', 'JUPGF', 'TARSF', 'YTEN', 'HHHEF', 'SMTSF', 'GIGGF']
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# []
# missingincomeyears =
# ['VALE', 'GOLD', 'AEM', 'MOS', 'SID', 'ARCH', 'BIOX', 'MTA', 'DC', 'ABAT', 'THM', 'AREC', 'NNUP', 'RNGE', 'BIOF', 'CRKN', 'COWI', 'GKIN', 'VYST', 'AMRSQ', 'MXSG', 'ERLFF', 'NSRCF', 'GNVR']
# missingdivyears =
# ['VALE', 'GOLD', 'AEM', 'MOS', 'SID', 'ARCH', 'BIOX', 'MTA', 'DC', 'LOOP', 'ABAT', 'THM', 'AREC', 'RNGE', 'BIOF', 'CRKN', 'THMG', 'COWI', 'GKIN', 'VYST', 'AMRSQ', 'MXSG', 'CGSI', 'NSRCF', 'GNVR']
# missingroicyears =
# ['VALE', 'GOLD', 'AEM', 'SID', 'BIOX', 'VRDR', 'ABAT', 'THM', 'AREC', 'NNUP', 'BIOF', 'COWI', 'VYST', 'AMRSQ', 'MXSG', 'ERLFF', 'NSRCF', 'GNVR']
# wrongincomeendyear =
# ['VALE', 'CTA-PA', 'PKX', 'JHX', 'SUZ', 'RPM', 'SQM', 'CX', 'EXP', 'SIM', 'SID', 'BVN', 'SBSW', 'BAK', 'SGML', 'HWKN', 'LOMA', 'GSM', 'ASTL', 'DRD', 'CPAC', 'SVM', 'GDRZF', 'ANVI', 'VZLA', 'MSB', 'SMID', 'RBTK', 'CMCL', 'PNRLF', 'LOOP', 'ASPI', 'FRD', 'AREC', 'YCQH', 'ACRG', 'GEVI', 'FURY', 'MULG', 'RMRI', 'EVA', 'DYNR', 'LONCF', 'XTGRF', 'GLGI', 'USAU', 'ELBM', 'LBSR', 'COPR', 'UAMY', 'GRFX', 'CRCUF', 'HLP', 'ZKIN', 'AAU', 'HGAS', 'RETO', 'GURE', 'NRHI', 'TLRS', 'BGLC', 'PBMLF', 'BASA', 'GRMC', 'MAGE', 'IMII', 'GNTOF', 'COWI', 'ATAO', 'WOLV', 'SRGZ', 'MNGG', 'HHHEF', 'ETCK', 'AVPMF', 'PVNNF', 'GPLDF', 'VYST', 'RMESF', 'MLYF', 'AMRSQ', 'GYST', 'MXSG', 'MKDTY', 'AMNL', 'STCC', 'CGSI', 'ALMMF', 'ERLFF', 'NSRCF', 'MPVDF', 'SMTSF', 'AVLNF', 'SHVLF', 'HGLD', 'SILEF', 'JSHG', 'EXNRF', 'SGMD', 'SINC', 'GIGGF', 'VNTRD']
# wrongdivendyear =
# ['VALE', 'CTA-PA', 'PKX', 'JHX', 'SUZ', 'RPM', 'SQM', 'CX', 'EXP', 'SIM', 'SID', 'BVN', 'SBSW', 'BAK', 'SGML', 'HWKN', 'LOMA', 'GSM', 'ASTL', 'WLKP', 'DRD', 'CPAC', 'SVM', 'GDRZF', 'ANVI', 'VZLA', 'MSB', 'SMID', 'RBTK', 'CMCL', 'PNRLF', 'LOOP', 'ASPI', 'FRD', 'AREC', 'YCQH', 'TRX', 'ACRG', 'GEVI', 'FURY', 'MULG', 'XPL', 'RMRI', 'EVA', 'DYNR', 'LONCF', 'XTGRF', 'GLGI', 'USAU', 'ELBM', 'LBSR', 'COPR', 'UAMY', 'GRFX', 'CRCUF', 'HLP', 'ZKIN', 'AAU', 'RETO', 'GURE', 'NRHI', 'TLRS', 'BGLC', 'LTUM', 'BASA', 'GRMC', 'MAGE', 'IMII', 'GNTOF', 'COWI', 'ATAO', 'WOLV', 'SRGZ', 'MNGG', 'HHHEF', 'ETCK', 'AVPMF', 'PVNNF', 'GPLDF', 'VYST', 'RMESF', 'MLYF', 'AMRSQ', 'GYST', 'MXSG', 'MKDTY', 'AMNL', 'STCC', 'CGSI', 'ALMMF', 'ERLFF', 'NSRCF', 'MPVDF', 'SMTSF', 'AVLNF', 'SHVLF', 'HGLD', 'SILEF', 'JSHG', 'EXNRF', 'SGMD', 'SINC', 'GIGGF', 'VNTRD']
# wrongroicendyear =
# ['VALE', 'CTA-PA', 'PKX', 'JHX', 'SUZ', 'RPM', 'SQM', 'CX', 'EXP', 'SIM', 'SID', 'BVN', 'SBSW', 'BAK', 'SGML', 'HWKN', 'LOMA', 'GSM', 'ASTL', 'DRD', 'CPAC', 'SVM', 'GDRZF', 'ANVI', 'VZLA', 'MSB', 'SMID', 'RBTK', 'CMCL', 'LOOP', 'ASPI', 'FRD', 'AREC', 'YCQH', 'ACRG', 'GEVI', 'FURY', 'MULG', 'RMRI', 'EVA', 'DYNR', 'LONCF', 'XTGRF', 'GLGI', 'USAU', 'ELBM', 'LBSR', 'COPR', 'UAMY', 'GRFX', 'CRCUF', 'HLP', 'ZKIN', 'RETO', 'GURE', 'NRHI', 'TLRS', 'BGLC', 'BASA', 'GRMC', 'MAGE', 'IMII', 'GNTOF', 'COWI', 'ATAO', 'WOLV', 'SRGZ', 'MNGG', 'HHHEF', 'ETCK', 'PVNNF', 'GPLDF', 'VYST', 'RMESF', 'MLYF', 'AMRSQ', 'GYST', 'MXSG', 'MKDTY', 'AMNL', 'STCC', 'CGSI', 'ALMMF', 'ERLFF', 'NSRCF', 'MPVDF', 'SMTSF', 'AVLNF', 'SHVLF', 'HGLD', 'SILEF', 'JSHG', 'EXNRF', 'SGMD', 'SINC', 'GIGGF', 'VNTRD']
###

###NEW Cons Cyclical
# recapList =
# ['NKE', 'CFRUY', 'MBGYY', 'RACE', 'OLCLY', 'DNZOY', 'YAHOY', 'CUK', 'VFS', 'ONON', 'RKUNY', 'BKGFY', 'PLNT', 'LNNGY', 'DUFRY', 'NGKSY', 'KBH', 'IHCPF', 'GEF', 'ZKH', 'MBUMY', 'FUN', 'EXTO', 'RICK', 'HVT', 'BH-A', 'IOCJY', 'MCFT', 'GHG', 'CDRO', 'PNST', 'BSET', 'MHGU', 'CJET', 'LGCB', 'FCCI', 'CREV', 'EGOX', 'HWH', 'ELMSQ', 'NCL', 'RWGI', 'JEWL', 'FFIE', 'HCNWF', 'JPOTF', 'MI', 'IVP', 'VEST', 'VMHG', 'MASN', 'GEGI', 'LFEV', 'FBCD', 'YUKA', 'PMNT', 'YAMHF', 'GFASY', 'GVSI', 'NEXCF', 'ELIO', 'ODDAF', 'ARVL', 'SPQS', 'SPBV', 'RECX', 'WNRS']
# missingRevenue =
# ['QS', 'NWTN', 'SES', 'RERE', 'PNST', 'ECDA', 'NCNC', 'HWH', 'ELMSQ', 'FFIE', 'PFSF', 'LSEB']
# missingNetIncome =
# []
# missingOpCF =
# []
# missingCapEx =
# ['BABA', 'LGIH', 'MSGE', 'MSC', 'PNST', 'EM', 'VNJA', 'PTZH', 'RENT', 'ECDA', 'CTNT', 'KEYR', 'HWH', 'SCTH', 'ELMSQ', 'SRM', 'KENS', 'PDRO', 'EBET', 'GHST', 'SPEV', 'OCTO', 'AUVI', 'SKFG', 'SCRH', 'MCOM', 'WESC', 'ALTB', 'MVXM', 'EVTK', 'ELRA', 'LCLP', 'FJHL']
# missingNetCF =
# ['ELRA']
# missingDepreNAmor =
# ['NKE', 'STLA', 'RACE', 'TCOM', 'DKNG', 'BALL', 'IHG', 'PAG', 'CVNA', 'BIRK', 'ONON', 'VIPS', 'CCK', 'LCID', 'XPEV', 'AS', 'MMYT', 'GIL', 'ALSN', 'DOOO', 'MNSO', 'PSNY', 'ZGN', 'ADNT', 'BOOT', 'AMBP', 'DAN', 'BKE', 'MBC', 'SGHC', 'OLPX', 'XPEL', 'GES', 'GOOS', 'MNRO', 'NGMS', 'BZH', 'EVGO', 'HLLY', 'GGR', 'BWMX', 'HEPS', 'PBPB', 'CYD', 'GAMB', 'UHG', 'JMIA', 'WEYS', 'BRLT', 'ALLG', 'LANV', 'MYTE', 'CBD', 'CDRO', 'RCKY', 'GOEV', 'FLXS', 'SPWH', 'PNST', 'NOBH', 'YTRA', 'VNJA', 'KEQU', 'TOUR', 'NTZ', 'CULP', 'SLNA', 'FTEL', 'RENT', 'VEV', 'KIRK', 'ECDA', 'CTNT', 'WBUY', 'CZOO', 'RIDEQ', 'NCNC', 'HWH', 'SCTH', 'FRSX', 'ELMSQ', 'LNBY', 'SRM', 'ZAPP', 'KENS', 'SPGC', 'TRNR', 'PDRO', 'VMAR', 'JXJT', 'USLG', 'REBN', 'SEVCQ', 'CMOT', 'EFOI', 'GHST', 'LQLY', 'SPEV', 'JZXN', 'SKFG', 'SCRH', 'THBD', 'CGAC', 'TKAYF', 'ALTB', 'MVXM', 'EVTK', 'FTCHF', 'ARVL', 'FXLV', 'LCLP', 'SSUNF']
# missing income prop sales
# []
# missingIntPaid =
# ['NKE', 'ABNB', 'CMG', 'LULU', 'QSR', 'DECK', 'WSM', 'BURL', 'WING', 'CART', 'SN', 'GLBE', 'W', 'GIL', 'BROS', 'COLM', 'AEO', 'AMBP', 'BKE', 'NWTN', 'GOOS', 'RVLV', 'CWH', 'FLWS', 'HSAI', 'SES', 'FNKO', 'SFIX', 'MPX', 'UHG', 'FINR', 'INVZ', 'NATH', 'DTC', 'EM', 'AOUT', 'NOBH', 'WISH', 'LUXH', 'VNJA', 'PTZH', 'BGI', 'LL', 'VIOT', 'REE', 'ECDA', 'BIMT', 'SOND', 'WBUY', 'NCNC', 'TBTC', 'KENS', 'VMAR', 'OCG', 'WNW', 'LQLY', 'SKFG', 'REII', 'SFTGQ', 'ALTB', 'MVXM', 'EVTK', 'ARMV', 'AMHG', 'FJHL', 'LSEB']
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# []
# missingincomeyears =
# ['HMC', 'HRB', 'VC', 'MLKN', 'WPRT', 'BIMT', 'VIVC', 'CTHR', 'AYRO', 'SNTW', 'BRVO', 'JXJT', 'REBN', 'AREB', 'AHRO', 'FLES', 'ALTB', 'MVXM']
# missingdivyears =
# ['HMC', 'VC', 'MLKN', 'WPRT', 'HFUS', 'BIMT', 'VIVC', 'CTHR', 'AYRO', 'SNTW', 'BRVO', 'JXJT', 'REBN', 'AREB', 'AHRO', 'DREM', 'FLES', 'ALTB', 'MVXM']
# missingroicyears =
# ['HMC', 'PRKA', 'BIMT', 'KENS', 'AYRO', 'SNTW', 'BRVO', 'JXJT', 'REBN', 'AREB', 'AHRO', 'FLES', 'ALTB', 'MVXM']
# wrongincomeendyear =
# ['TM', 'BABA', 'PDD', 'NKE', 'HMC', 'JD', 'LI', 'TCOM', 'SE', 'DECK', 'DRI', 'NIO', 'KMX', 'RL', 'CASY', 'HTHT', 'VIPS', 'XPEV', 'MMYT', 'LKNCY', 'VFC', 'CPRI', 'SKY', 'MOD', 'PSNY', 'UAA', 'CVCO', 'BOOT', 'ARCO', 'ATAT', 'NWTN', 'VSTO', 'SGHC', 'LZB', 'AMWD', 'GOOS', 'MNRO', 'NGMS', 'DESP', 'BWMX', 'HSAI', 'HEPS', 'NAAS', 'DADA', 'FSR', 'CRMT', 'LOVE', 'CYD', 'BBW', 'NEGG', 'GHG', 'ALLG', 'LANV', 'NATH', 'HOFT', 'CTRN', 'RERE', 'PLCE', 'INSE', 'CBD', 'TLYS', 'THCH', 'CDRO', 'MPAA', 'VIRC', 'BARK', 'CANG', 'BZUN', 'PNST', 'EM', 'NIU', 'CONN', 'AOUT', 'NOBH', 'YTRA', 'LUXH', 'KEQU', 'TOUR', 'BGI', 'NTZ', 'ZKGCF', 'TUP', 'TCS', 'VIOT', 'CULP', 'CRWS', 'INTG', 'VNCE', 'BNED', 'SLNA', 'PEV', 'RENT', 'JRSH', 'ECDA', 'MRM', 'SOND', 'FGH', 'CZOO', 'JOAN', 'CHSN', 'XELB', 'VIVC', 'SCTH', 'BFX', 'ELMSQ', 'MOGU', 'LNBY', 'BFI', 'EXPR', 'YJ', 'UXIN', 'FFIE', 'PDRO', 'TKLF', 'POL', 'JXJT', 'USLG', 'BWMG', 'PRSI', 'NROM', 'KXIN', 'UCAR', 'SEVCQ', 'LTRY', 'CMOT', 'ELYS', 'OCG', 'FUV', 'EVVL', 'WNW', 'JWEL', 'LQLY', 'SPEV', 'SECO', 'SHMY', 'PIK', 'JZXN', 'SBET', 'NVFY', 'DBGI', 'AUVI', 'KITL', 'BQ', 'AREB', 'ASAP', 'AHRO', 'CNXA', 'DREM', 'OMTK', 'MSSV', 'SKFG', 'SCRH', 'MCOM', 'NNAX', 'FLES', 'BBIG', 'IDICQ', 'REII', 'THBD', 'BTDG', 'IMBIQ', 'SFTGQ', 'CGAC', 'UFABQ', 'WESC', 'ASCK', 'TKAYF', 'ALTB', 'WCRS', 'DSHK', 'LMPX', 'EVTK', 'FTCHF', 'ARVL', 'FXLV', 'AMTY', 'PFSF', 'ARMV', 'ELRA', 'LCLP', 'AMHG', 'FJHL', 'SSUNF', 'LSEB']
# wrongdivendyear =
# ['TM', 'BABA', 'PDD', 'NKE', 'HMC', 'JD', 'LI', 'TCOM', 'SE', 'DECK', 'DRI', 'NIO', 'KMX', 'RL', 'CASY', 'HTHT', 'VIPS', 'XPEV', 'MMYT', 'LKNCY', 'VFC', 'CPRI', 'SKY', 'MOD', 'PSNY', 'UAA', 'CVCO', 'BOOT', 'ARCO', 'NWTN', 'VSTO', 'SGHC', 'LZB', 'AMWD', 'GOOS', 'MNRO', 'NGMS', 'DESP', 'BWMX', 'HSAI', 'HEPS', 'NAAS', 'DADA', 'FSR', 'CRMT', 'LOVE', 'CYD', 'FINR', 'BBW', 'NEGG', 'ALLG', 'LANV', 'NATH', 'HOFT', 'CTRN', 'RERE', 'PLCE', 'INSE', 'CBD', 'TLYS', 'THCH', 'MPAA', 'VIRC', 'BARK', 'CANG', 'BZUN', 'EM', 'LAKE', 'NIU', 'CONN', 'AOUT', 'NOBH', 'YTRA', 'LUXH', 'VNJA', 'KEQU', 'TOUR', 'BGI', 'NTZ', 'ZKGCF', 'TUP', 'TCS', 'VIOT', 'CULP', 'CRWS', 'INTG', 'VNCE', 'BNED', 'SLNA', 'PEV', 'RENT', 'JRSH', 'ECDA', 'MRM', 'SOND', 'FGH', 'WBUY', 'CZOO', 'JOAN', 'CHSN', 'XELB', 'VIVC', 'SCTH', 'BFX', 'MOGU', 'LNBY', 'BFI', 'EXPR', 'YJ', 'UXIN', 'PDRO', 'TKLF', 'POL', 'JXJT', 'USLG', 'BWMG', 'PRSI', 'NROM', 'KXIN', 'UCAR', 'SEVCQ', 'LTRY', 'CMOT', 'ELYS', 'OCG', 'FFLO', 'FUV', 'EVVL', 'WNW', 'JWEL', 'LQLY', 'SPEV', 'SECO', 'SHMY', 'PIK', 'JZXN', 'SBET', 'NVFY', 'DBGI', 'AUVI', 'KITL', 'BQ', 'AREB', 'ASAP', 'AHRO', 'CNXA', 'DREM', 'OMTK', 'MSSV', 'SKFG', 'SCRH', 'MCOM', 'NNAX', 'FLES', 'BBIG', 'IDICQ', 'REII', 'THBD', 'BTDG', 'IMBIQ', 'SFTGQ', 'CGAC', 'UFABQ', 'WESC', 'ASCK', 'TKAYF', 'ALTB', 'MVXM', 'WCRS', 'DSHK', 'LMPX', 'EVTK', 'FTCHF', 'FXLV', 'AMTY', 'PFSF', 'ARMV', 'ELRA', 'LCLP', 'AMHG', 'FJHL', 'SSUNF', 'LSEB']
# wrongroicendyear =
# ['TM', 'BABA', 'PDD', 'HMC', 'JD', 'LI', 'TCOM', 'SE', 'DECK', 'DRI', 'NIO', 'KMX', 'RL', 'CASY', 'HTHT', 'VIPS', 'XPEV', 'MMYT', 'LKNCY', 'VFC', 'CPRI', 'SKY', 'MOD', 'PSNY', 'UAA', 'CVCO', 'BOOT', 'ARCO', 'NWTN', 'VSTO', 'SGHC', 'LZB', 'AMWD', 'GOOS', 'MNRO', 'NGMS', 'DESP', 'BWMX', 'HSAI', 'HEPS', 'NAAS', 'DADA', 'FSR', 'CRMT', 'LOVE', 'CYD', 'BBW', 'NEGG', 'ALLG', 'LANV', 'NATH', 'HOFT', 'CTRN', 'RERE', 'PLCE', 'INSE', 'CBD', 'TLYS', 'THCH', 'MPAA', 'VIRC', 'BARK', 'CANG', 'BZUN', 'EM', 'LAKE', 'NIU', 'CONN', 'AOUT', 'NOBH', 'YTRA', 'LUXH', 'KEQU', 'TOUR', 'BGI', 'NTZ', 'ZKGCF', 'TUP', 'TCS', 'VIOT', 'CULP', 'CRWS', 'INTG', 'VNCE', 'BNED', 'SLNA', 'PEV', 'RENT', 'JRSH', 'ECDA', 'MRM', 'SOND', 'FGH', 'JOAN', 'CHSN', 'XELB', 'VIVC', 'SCTH', 'BFX', 'MOGU', 'LNBY', 'BFI', 'EXPR', 'YJ', 'UXIN', 'PDRO', 'TKLF', 'POL', 'JXJT', 'USLG', 'BWMG', 'PRSI', 'NROM', 'KXIN', 'UCAR', 'SEVCQ', 'LTRY', 'CMOT', 'ELYS', 'OCG', 'FUV', 'EVVL', 'WNW', 'JWEL', 'LQLY', 'SPEV', 'SECO', 'SHMY', 'PIK', 'JZXN', 'SBET', 'NVFY', 'DBGI', 'AUVI', 'KITL', 'BQ', 'AREB', 'ASAP', 'AHRO', 'CNXA', 'DREM', 'OMTK', 'MSSV', 'SKFG', 'SCRH', 'MCOM', 'NNAX', 'FLES', 'BBIG', 'IDICQ', 'REII', 'THBD', 'BTDG', 'IMBIQ', 'SFTGQ', 'CGAC', 'UFABQ', 'WESC', 'ASCK', 'TKAYF', 'ALTB', 'WCRS', 'DSHK', 'LMPX', 'EVTK', 'FTCHF', 'FXLV', 'AMTY', 'PFSF', 'ARMV', 'ELRA', 'LCLP', 'AMHG', 'FJHL', 'SSUNF', 'LSEB']
###

###NEW Cons Staples
# recapList = 
# ['FMX', 'BUD', 'BTI', 'STZ', 'SVNDY', 'JRONY', 'SMKUY', 'MEJHY', 'CUYTY', 'LCCTF', 'FIZZ', 'DFIHY', 'MRRTY', 'IMKTA', 'NISUY', 'KLG', 'EWCZ', 'GGROU', 'RFLFY', 'AAGR', 'YERBF', 'DDC', 'DTCK', 'YGF', 'NASO', 'PCST', 'VPRB', 'INKW', 'HIRU', 'GRLF', 'LBWR', 'PDPG', 'EARI', 'BMXC', 'TBBB', 'BRLS', 'BLEG', 'WNBD']
# missingRevenue =
# ['EWCZ', 'AAGR', 'NUVI', 'PCNT', 'BRLS', 'GLUC', 'SGLA']
# missingNetIncome =
# []
# missingOpCF =
# []
# missingCapEx =
# ['HIMS', 'AQPW', 'HAIN', 'YUMM', 'HIGR', 'NXMH', 'BFNH', 'AAGR', 'PGID', 'NPLS', 'EOSS', 'VINE', 'RMHB', 'SNAX', 'CBDW', 'YCRM', 'NGTF', 'SRSG', 'AGRI', 'NAFS', 'ARRT', 'SKVI', 'NUVI', 'PCNT', 'BRLS', 'NTCO', 'GWLL', 'MCLE', 'GLUC', 'FKST', 'SGLA', 'HVCW', 'ITOR']
# missingNetCF =
# ['NXMH', 'SGLA']
# missingDepreNAmor =
# ['FMX', 'BUD', 'UL', 'DEO', 'BTI', 'ABEV', 'CCEP', 'KOF', 'SJM', 'JBSAY', 'TAL', 'BRFS', 'ASAI', 'GHC', 'NOMD', 'RLX', 'CCU', 'AKO-A', 'ATGE', 'AFYA', 'GOTU', 'AGRO', 'OTLY', 'VTRU', 'YUMM', 'LND', 'ISPR', 'SNDL', 'SKIN', 'YSG', 'VSTA', 'AFRI', 'QSG', 'FREE', 'WILC', 'HIGR', 'AIU', 'BFNH', 'AAGR', 'CFOO', 'GNS', 'LXEH', 'NPLS', 'YQ', 'EOSS', 'STKH', 'FEDU', 'EDTK', 'NCRA', 'LQR', 'VINE', 'BRSH', 'KAVL', 'SNBH', 'TOFB', 'WTER', 'CBDW', 'NGTF', 'SRSG', 'NBND', 'VGFCQ', 'NAFS', 'BDPT', 'MFLTY', 'NUVI', 'TDNT', 'BRLS', 'NTCO', 'GWLL', 'BRCNF', 'MCLE', 'GLUC', 'LMDCF', 'SGLA', 'SUWN', 'DTEAF', 'BRWC', 'ITOR']
# missing income prop sales
# []
# missingIntPaid =
# ['MNST', 'LW', 'INGR', 'LANC', 'SAM', 'GO', 'DNUT', 'GOTU', 'HNST', 'QSG', 'MAMA', 'IH', 'ZVIA', 'BFNH', 'UG', 'MALG', 'AACG', 'ATPC', 'FEDU', 'EXDW', 'DQWS', 'MNKA', 'CBDW', 'AGRI', 'MFLTY', 'NUVI', 'OGAA', 'MCLE', 'SGLA', 'BRWC', 'ITOR']
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# ['RMHB', 'SGLA']
# missingincomeyears =
# ['SMPL', 'NOMD', 'CALM', 'AQPW', 'UTZ', 'SPTN', 'KUBR', 'SNDL', 'BIG', 'SKIL', 'GCEH', 'PYYX', 'EXDW', 'BRSH', 'YCRM', 'NAFS', 'BDPT', 'ASII', 'PCNT', 'ICNB', 'QOEG', 'FKST']
# missingdivyears =
# ['BTI', 'NOMD', 'CALM', 'AQPW', 'SPTN', 'KUBR', 'SNDL', 'WILC', 'SKIL', 'GCEH', 'PYYX', 'AACG', 'EXDW', 'BRSH', 'YCRM', 'BDPT', 'ASII', 'ICNB', 'RAYT']
# missingroicyears =
# ['NOMD', 'AQPW', 'UTZ', 'KUBR', 'SKIL', 'GCEH', 'PYYX', 'EXDW', 'YCRM', 'NAFS', 'BDPT', 'ASII', 'PCNT', 'ICNB', 'QOEG', 'FKST']
# wrongincomeendyear =
# ['FMX', 'STZ', 'GIS', 'BF-B', 'KOF', 'LW', 'EDU', 'SJM', 'CAG', 'ACI', 'ELF', 'TAL', 'BRFS', 'FIZZ', 'ASAI', 'RLX', 'HELE', 'CCU', 'AQPW', 'AFYA', 'UVV', 'GOTU', 'AGRO', 'KUBR', 'VTRU', 'DAO', 'SENEA', 'YSG', 'VSTA', 'AFRI', 'DDL', 'BIG', 'MAMA', 'IH', 'STG', 'SKIL', 'HIGR', 'FVTI', 'ZHYBF', 'NXMH', 'AAGR', 'CFOO', 'GCEH', 'CHUC', 'PYYX', 'JZ', 'RGF', 'COE', 'GNS', 'MALG', 'AACG', 'LXEH', 'RMCF', 'NPLS', 'PCSV', 'YQ', 'EOSS', 'MSS', 'STKH', 'CTGL', 'FEDU', 'PAVS', 'VPRB', 'EDTK', 'AIXN', 'TCTM', 'PETZ', 'BRSH', 'SHMP', 'GV', 'HPCO', 'CLEU', 'WAFU', 'MNKA', 'LEAI', 'BTCT', 'BTTR', 'SNBH', 'RMHB', 'CYAN', 'AMBO', 'WTER', 'CBDW', 'RVIV', 'TANH', 'SRSG', 'GNLN', 'FHSEY', 'NBND', 'SHRG', 'VGFCQ', 'SMFL', 'NAFS', 'RTON', 'BDPT', 'SKVI', 'MFLTY', 'ASII', 'NUVI', 'OGAA', 'IFMK', 'TTCFQ', 'TDNT', 'PCNT', 'TUEMQ', 'PACV', 'UPDC', 'ICNB', 'RAYT', 'BRLS', 'NTCO', 'GWLL', 'BRCNF', 'QOEG', 'ASPU', 'GLUC', 'LMDCF', 'FKST', 'SGLA', 'ZVOI', 'SUWN', 'HVCW', 'DTEAF', 'ITOR']
# wrongdivendyear =
# ['GIS', 'BF-B', 'KOF', 'LW', 'EDU', 'SJM', 'CAG', 'ACI', 'ELF', 'TAL', 'BRFS', 'ASAI', 'RLX', 'HELE', 'CCU', 'AQPW', 'AFYA', 'UVV', 'GOTU', 'AGRO', 'KUBR', 'VTRU', 'DAO', 'SENEA', 'YSG', 'VSTA', 'AFRI', 'DDL', 'BIG', 'MAMA', 'IH', 'STG', 'SKIL', 'HIGR', 'FVTI', 'ZHYBF', 'NXMH', 'UMEWF', 'CFOO', 'GCEH', 'CHUC', 'PYYX', 'JZ', 'RGF', 'COE', 'GNS', 'MALG', 'AACG', 'LXEH', 'PGID', 'RMCF', 'NPLS', 'PCSV', 'YQ', 'EOSS', 'MSS', 'STKH', 'CTGL', 'FEDU', 'PAVS', 'VPRB', 'EDTK', 'AIXN', 'TCTM', 'PETZ', 'BRSH', 'SHMP', 'GV', 'HPCO', 'CLEU', 'WAFU', 'MNKA', 'LEAI', 'BTCT', 'BTTR', 'SNBH', 'RMHB', 'CYAN', 'AMBO', 'WTER', 'CBDW', 'RVIV', 'TANH', 'SRSG', 'GNLN', 'FHSEY', 'NBND', 'SHRG', 'VGFCQ', 'SMFL', 'NAFS', 'RTON', 'BDPT', 'ARRT', 'SKVI', 'MFLTY', 'ASII', 'NUVI', 'OGAA', 'IFMK', 'TTCFQ', 'TDNT', 'PCNT', 'TUEMQ', 'PACV', 'UPDC', 'ICNB', 'RAYT', 'NTCO', 'GWLL', 'BRCNF', 'QOEG', 'ASPU', 'GLUC', 'LMDCF', 'FKST', 'SGLA', 'ZVOI', 'SUWN', 'HVCW', 'DTEAF', 'ITOR']
# wrongroicendyear =
# ['GIS', 'BF-B', 'KOF', 'LW', 'EDU', 'SJM', 'CAG', 'ACI', 'ELF', 'TAL', 'BRFS', 'ASAI', 'RLX', 'HELE', 'CCU', 'AQPW', 'AFYA', 'UVV', 'GOTU', 'AGRO', 'KUBR', 'VTRU', 'DAO', 'SENEA', 'YSG', 'VSTA', 'AFRI', 'DDL', 'BIG', 'MAMA', 'IH', 'STG', 'SKIL', 'HIGR', 'FVTI', 'ZHYBF', 'NXMH', 'CFOO', 'GCEH', 'CHUC', 'PYYX', 'JZ', 'RGF', 'COE', 'GNS', 'MALG', 'AACG', 'LXEH', 'RMCF', 'NPLS', 'PCSV', 'YQ', 'EOSS', 'MSS', 'STKH', 'CTGL', 'FEDU', 'PAVS', 'EDTK', 'AIXN', 'TCTM', 'PETZ', 'BRSH', 'SHMP', 'GV', 'HPCO', 'CLEU', 'WAFU', 'MNKA', 'LEAI', 'BTCT', 'BTTR', 'SNBH', 'RMHB', 'CYAN', 'AMBO', 'WTER', 'CBDW', 'RVIV', 'TANH', 'SRSG', 'GNLN', 'FHSEY', 'NBND', 'SHRG', 'VGFCQ', 'SMFL', 'NAFS', 'RTON', 'BDPT', 'SKVI', 'MFLTY', 'ASII', 'NUVI', 'OGAA', 'IFMK', 'TTCFQ', 'TDNT', 'PCNT', 'TUEMQ', 'PACV', 'UPDC', 'ICNB', 'RAYT', 'NTCO', 'GWLL', 'BRCNF', 'QOEG', 'ASPU', 'GLUC', 'LMDCF', 'FKST', 'SGLA', 'ZVOI', 'SUWN', 'HVCW', 'DTEAF', 'ITOR']
###

###NEW Comms
# recapList = 
# ['TLGPY', 'PUBGY', 'VOD', 'KKPNY', 'VIVHY', 'VDMCY', 'CSXXY', 'IIJIY', 'HMNTY', 'TV', 'SEAT', 'CCG', 'SGA', 'GOAI', 'HAO', 'MCHX', 'KUKE', 'ABLV', 'PODC', 'TRFE', 'MNY', 'SNAL', 'MMV', 'QYOUF', 'HRYU', 'EGLXF', 'TRUG', 'FENG', 'LEBGF', 'MIMO', 'HHSE', 'VSME', 'GTRL', 'SONG', 'CBIA', 'TAMG', 'MRNJ', 'UVSS', 'SNMN', 'EMDF', 'WTKN', 'GTOR', 'QBCRF', 'CAPV', 'MIKP', 'MOCI', 'PSRU', 'MACT', 'MEDE']
# missingRevenue =
# ['VIV', 'VPLM', 'MMV', 'TRUG', 'MGAM', 'SNWR', 'CLIS']
# missingNetIncome =
# []
# missingOpCF =
# []
# missingCapEx =
# ['EA', 'TKO', 'CRTO', 'DRCT', 'MVNC', 'RSTN', 'MMV', 'NCTY', 'CRGE', 'EGLXF', 'ELRE', 'TRUG', 'FHLD', 'XESP', 'FDIT', 'DROR', 'HHSE', 'CNNN', 'ONFO', 'FMHS', 'NUGL', 'CMGO', 'SLDC', 'HMLA', 'TMGI', 'SNWR', 'CLIS', 'FRFR', 'AFOM', 'IDWM', 'BTIM', 'BRQL']
# missingNetCF =
# ['BCE', 'ANGH', 'QBCRF']
# missingDepreNAmor =
# ['GOOGL', 'AMX', 'SPOT', 'CHTR', 'EA', 'BCE', 'ORAN', 'CHT', 'TLK', 'TU', 'RCI', 'VOD', 'TEF', 'VIV', 'TME', 'WPP', 'MTCH', 'TIMB', 'PSO', 'SKM', 'KT', 'PHI', 'TKC', 'IAC', 'BILI', 'MANU', 'TEO', 'IQ', 'ATHM', 'GSAT', 'TGNA', 'TIGO', 'PLTK', 'YY', 'GETY', 'CRTO', 'TV', 'VEON', 'ANGI', 'MOMO', 'IHS', 'OPRA', 'HUYA', 'RBBN', 'PGRU', 'GDEV', 'NEXN', 'SOHU', 'LDSN', 'MYPS', 'SIFY', 'ADTH', 'DOYU', 'OB', 'KNIT', 'TRVG', 'BRAG', 'XNET', 'SCOR', 'CMCM', 'BHAT', 'KUKE', 'STCN', 'UCL', 'RSTN', 'ICLK', 'SJ', 'AAQL', 'MMV', 'ANGH', 'CURI', 'EGLXF', 'ELRE', 'GAME', 'KRKR', 'BMTM', 'TRUG', 'GIGM', 'FHLD', 'BREA', 'XESP', 'FDIT', 'SPTY', 'DROR', 'LCFY', 'HHSE', 'ADD', 'MGOL', 'VYBE', 'MMND', 'VRVR', 'ONFO', 'DBMM', 'NUGL', 'SLDC', 'GFMH', 'SRAX', 'HMLA', 'TMGI', 'SNWR', 'WINR', 'MLFB', 'CLIS', 'FRFR', 'AFOM', 'QBCRF', 'CELJF', 'ILLMF', 'GZIC', 'TOWTF', 'PTNRF']
# missing income prop sales
# []
# missingIntPaid =
# ['NTES', 'PINS', 'TWLO', 'YELP', 'SSTK', 'HUYA', 'KIND', 'RBBN', 'CNSL', 'ZH', 'JFIN', 'DOYU', 'KNIT', 'SCOR', 'GAIA', 'CMCM', 'VPLM', 'RSTN', 'AAQL', 'CURI', 'KRKR', 'FDIT', 'ASST', 'TC', 'CCCP', 'CLIS', 'NTTYY', 'TOWTF']   
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# ['WPP']
# missingincomeyears =
# ['WMG', 'FYBR', 'THRY', 'MVNC', 'IQST', 'KTEL', 'AREN', 'HMMR', 'TRKAQ', 'CMGO', 'ROI', 'HMLA', 'TMGI', 'CLIS']
# missingdivyears =
# ['FYBR', 'THRY', 'MVNC', 'GMGI', 'IQST', 'KTEL', 'AREN', 'HMMR', 'VNUE', 'TRKAQ', 'CMGO', 'HMLA', 'TMGI', 'CLIS']
# missingroicyears =
# ['THRY', 'MVNC', 'IQST', 'KTEL', 'HMMR', 'TRKAQ', 'CMGO', 'ROI', 'HMLA', 'TMGI', 'CLIS']
# wrongincomeendyear =
# ['NTES', 'AMX', 'EA', 'CHT', 'TTWO', 'VOD', 'TME', 'TIMB', 'SKM', 'KT', 'YNDX', 'TKC', 'IIJIY', 'ATHM', 'LGF-A', 'WB', 'YY', 'ROVR', 'WLY', 'TV', 'VEON', 'PERI', 'SCHL', 'MOMO', 'OPRA', 'HUYA', 'ATEX', 'GRVY', 'GDEV', 'ZH', 'RSVR', 'LDSN', 'JFIN', 'SIFY', 'DOYU', 'DRCT', 'UONE', 'LVO', 'SKLZ', 'MVNC', 'FNGR', 'XNET', 'WIMI', 'BBUZ', 'EZOO', 'KORE', 'SCGY', 'CMCM', 'BHAT', 'KUKE', 'STCN', 'TOON', 'RSTN', 'ICLK', 'SJ', 'AAQL', 'MMV', 'NCTY', 'ANGH', 'CRGE', 'EGLXF', 'ELRE', 'GAME', 'KRKR', 'CNVS', 'TRUG', 'FENG', 'GIGM', 'EDUC', 'FAZE', 'BREA', 'FDIT', 'MIMO', 'DMSL', 'SALM', 'CNFN', 'KDOZF', 'SPTY', 'SLE', 'HHSE', 'BAOS', 'CNET', 'CSSE', 'TLLYF', 'MGAM', 'SNPW', 'VYBE', 'ANTE', 'VRVR', 'VNUE', 'TRKAQ', 'FMHS', 'NUGL', 'MOBQ', 'GROM', 'COMS', 'CMGO', 'QTTOY', 'NWCN', 'SLDC', 'BOTY', 'GFMH', 'ROI', 'SRAX', 'TMGI', 'CCCP', 'MDEX', 'SNWR', 'WINR', 'VOCL', 'MLFB', 'CLIS', 'XFCI', 'FRFR', 'YVRLF', 'AFOM', 'NTTYY', 'QBCRF', 'CELJF', 'OIBRQ', 'ILLMF', 'IDWM', 'EMWPF', 'LTES', 'BYOC', 'GZIC', 'TOWTF', 'BTIM', 'PTNRF', 'LOVLQ']
# wrongdivendyear =
# ['NTES', 'AMX', 'EA', 'CHT', 'TTWO', 'VOD', 'TME', 'TIMB', 'SKM', 'KT', 'YNDX', 'TKC', 'ATHM', 'LGF-A', 'YY', 'ROVR', 'WLY', 'VEON', 'PERI', 'SCHL', 'MOMO', 'OPRA', 'HUYA', 'ATEX', 'GRVY', 'GDEV', 'ZH', 'RSVR', 'LDSN', 'JFIN', 'SIFY', 'DOYU', 'DRCT', 'KNIT', 'UONE', 'LVO', 'SKLZ', 'MVNC', 'FNGR', 'XNET', 'WIMI', 'BBUZ', 'EZOO', 'KORE', 'SCGY', 'CMCM', 'BHAT', 'IQST', 'TOON', 'RSTN', 'ICLK', 'SJ', 'AAQL', 'NCTY', 'ANGH', 'CRGE', 'ELRE', 'GAME', 'KRKR', 'CNVS', 'GIGM', 'EDUC', 'FAZE', 'BREA', 'FDIT', 'DMSL', 'SALM', 'CNFN', 'KDOZF', 'SPTY', 'SLE', 'BAOS', 'CNET', 'CSSE', 'TLLYF', 'MGAM', 'SNPW', 'VYBE', 'ANTE', 'VRVR', 'VNUE', 'TRKAQ', 'FMHS', 'NUGL', 'MOBQ', 'GROM', 'COMS', 'CMGO', 'QTTOY', 'NWCN', 'SLDC', 'BOTY', 'GFMH', 'ROI', 'SRAX', 'TMGI', 'CCCP', 'MDEX', 'SNWR', 'WINR', 'VOCL', 'MLFB', 'CLIS', 'XFCI', 'FRFR', 'YVRLF', 'AFOM', 'NTTYY', 'CELJF', 'OIBRQ', 'ILLMF', 'IDWM', 'EMWPF', 'LTES', 'BYOC', 'GZIC', 'TOWTF', 'BTIM', 'PTNRF', 'LOVLQ']
# wrongroicendyear =
# ['NTES', 'AMX', 'EA', 'CHT', 'TTWO', 'TME', 'TIMB', 'SKM', 'KT', 'YNDX', 'TKC', 'ATHM', 'LGF-A', 'WB', 'YY', 'ROVR', 'WLY', 'VEON', 'PERI', 'SCHL', 'MOMO', 'OPRA', 'HUYA', 'ATEX', 'GRVY', 'GDEV', 'ZH', 'RSVR', 'LDSN', 'JFIN', 'SIFY', 'DOYU', 'DRCT', 'UONE', 'LVO', 'SKLZ', 'MVNC', 'FNGR', 'XNET', 'WIMI', 'BBUZ', 'EZOO', 'KORE', 'SCGY', 'CMCM', 'BHAT', 'STCN', 'TOON', 'RSTN', 'ICLK', 'SJ', 'AAQL', 'NCTY', 'ANGH', 'CRGE', 'ELRE', 'GAME', 'KRKR', 'CNVS', 'GIGM', 'EDUC', 'FAZE', 'BREA', 'FDIT', 'DMSL', 'SALM', 'CNFN', 'KDOZF', 'SPTY', 'SLE', 'BAOS', 'CNET', 'CSSE', 'TLLYF', 'MGAM', 'SNPW', 'VYBE', 'ANTE', 'VRVR', 'VNUE', 'TRKAQ', 'FMHS', 'NUGL', 'MOBQ', 'GROM', 'COMS', 'CMGO', 'QTTOY', 'NWCN', 'SLDC', 'BOTY', 'GFMH', 'ROI', 'SRAX', 'TMGI', 'CCCP', 'MDEX', 'SNWR', 'WINR', 'VOCL', 'MLFB', 'CLIS', 'XFCI', 'FRFR', 'YVRLF', 'AFOM', 'NTTYY', 'CELJF', 'OIBRQ', 'ILLMF', 'IDWM', 'EMWPF', 'LTES', 'BYOC', 'GZIC', 'TOWTF', 'BTIM', 'PTNRF', 'LOVLQ']
###

###NEW ind
# recapList = 
# ['EADSY', 'ATLKY', 'PCAR', 'BAESY', 'DKILY', 'CODYY', 'WTKWY', 'FANUY', 'CJPRY', 'SGSOY', 'BOUYY', 'TKHVY', 'RBA', 'ASR', 'OUKPY', 'EBCOY', 'SMBMY', 'ALSMY', 'VIAAY', 'MSSMY', 'ATS', 'AFLYY', 'ROYMY', 'IHICY', 'VSTS', 'OSTIY', 'SHZNY', 'GBX', 'ECO', 'AZUL', 'SPLP', 'GSL', 'FLYX', 'MIESY', 'KNOP', 'TUSK', 'FBYD', 'STI', 'PMEC', 'CCTG', 'AERT', 'EESH', 'PNYG', 'ROMA', 'MMTRS', 'CBMJ', 'MSNVF', 'ESGL', 'BURU', 'GPAK', 'CISS', 'IAALF', 'GOGR', 'SSHT', 'UMAV', 'MHHC', 'RCIT', 'DPUI', 'EENEF', 'GOL', 'GNGYF', 'EXROF', 'BCCEF', 'USDP', 'JETR', 'FTRS', 'LEAS', 'KNOS', 'WTII']
# missingRevenue =
# ['EVEX', 'ACHR', 'PCT', 'FLYX', 'SB', 'FREY', 'ZCAR', 'STI', 'AERT', 'HOVR', 'SPEC', 'GRHI', 'MMTRS', 'BURU', 'SSET', 'HLLK', 'JPEX']
# missingNetIncome =
# ['MMTRS']
# missingOpCF =
# ['MMTRS']
# missingCapEx =
# ['ADP', 'PAC', 'CAR', 'HTZ', 'CTOS', 'SFL', 'MRTN', 'CMRE', 'NAT', 'CRESY', 'FLYX', 'EGLE', 'SB', 'PANL', 'HSHP', 'WSCO', 'HQI', 'ELVA', 'CRAWA', 'ZCAR', 'RR', 'STI', 'BEEP', 'NEOV', 'NSGP', 'AERT', 'HOVR', 'UNXP', 'CLEV', 'QIND', 'EAWD', 'PNYG', 'WLGS', 'GRHI', 'MMTRS', 'BURU', 'NORD', 'YJGJ', 'GTLL', 'JKSM', 'NVGT', 'QPRC', 'DRFS', 'RAKR', 'ATVK', 'HLLK', 'JFIL', 'KDCE', 'DTII', 'JPEX', 'MSYN', 'MJHI', 'ACMB', 'ARMC', 'PRPI', 'IWAL', 'ECOX', 'CDXQ']
# missingNetCF =
# ['HLLK', 'PRPI']
# missingDepreNAmor =
# ['LTMAY', 'UNP', 'RELX', 'ITW', 'TRI', 'PH', 'FAST', 'OTIS', 'RYAAY', 'PWR', 'POOL', 'GFL', 'RTO', 'PNR', 'TFII', 'UHAL', 'NVT', 'FBIN', 'STN', 'AGCO', 'APG', 'RHI', 'PAC', 'SITE', 'AIT', 'CAE', 'CAR', 'R', 'AL', 'HRI', 'CAAP', 'CPA', 'OMAB', 'SPR', 'ERJ', 'HAYW', 'WERN', 'ALG', 'BE', 'PGTI', 'JBI', 'GOGL', 'SBLK', 'UPWK', 'TNC', 'BBU', 'SFL', 'ACHR', 'MRTN', 'ZIM', 'PRG', 'CDLR', 'VVX', 'BLDP', 'TDCX', 'VLRS', 'AZUL', 'NAT', 'PCT', 'BV', 'CRESY', 'EUBG', 'ASC', 'LNZA', 'FLYX', 'MTW', 'ACCO', 'EBF', 'LILM', 'SB', 'FORR', 'ADSE', 'LEV', 'PTSI', 'AMBI', 'MVST', 'QUAD', 'ESEA', 'MEC', 'GASS', 'GHM', 'SMR', 'NVX', 'WSCO', 'GRIN', 'FLCX', 'EVTL', 'SHIP', 'CRGO', 'ELVA', 'ESOA', 'SATL', 'ARC', 'ZCAR', 'RR', 'OMEX', 'STI', 'PYRGF', 'FLUX', 'GP', 'AQMS', 'EDRY', 'ESP', 'NEOV', 'NSGP', 'AZ', 'XOS', 'ASTR', 'GLBS', 'AERT', 'FTEK', 'VCIG', 'LICN', 'HOVR', 'GFAI', 'SPEC', 'UNXP', 'USEA', 'GTMAY', 'LWLW', 'DCFC', 'AIRI', 'QIND', 'SNRG', 'EAWD', 'YGMZ', 'PNYG', 'WLGS', 'MWG', 'GRHI', 'MMTRS', 'KIQ', 'KWE', 'MNTS', 'CHNR', 'PRZO', 'CAMG', 'OZSC', 'GPOX', 'BURU', 'NORD', 'BWVI', 'SMX', 'TBLT', 'YJGJ', 'AEHL', 'GTLL', 'KRFG', 'PTNYF', 'AETHF', 'WARM', 'IMHC', 'DRFS', 'BLIS', 'RAKR', 'HLLK', 'BLPG', 'COUV', 'JFIL', 'HWKE', 'KDCE', 'BBRW', 'JPEX', 'MSYN', 'PHOT', 'CHEAF', 'CHKIF', 'GOL', 'GNGYF', 'ACMB', 'DPRO', 'PRPI', 'TMRR', 'ECOX']
# missing income prop sales
# []
# missingIntPaid =
# ['CAT', 'ABBNY', 'TRI', 'URI', 'SYM', 'AXON', 'WMS', 'CLH', 'CHRW', 'BZ', 'ATKR', 'ESAB', 'EXPO', 'AVAV', 'CSWI', 'STRL', 'RXO', 'MIR', 'RKLB', 'SFL', 'ULCC', 'VVX', 'TGI', 'DNOW', 'PRLB', 'KRNT', 'NKLA', 'LNZA', 'AGX', 'NPK', 'BWMN', 'AMPX', 'DSKE', 'FREY', 'GENC', 'NVX', 'FLCX', 'SHIM', 'VTSI', 'ZCAR', 'RR', 'LUNR', 'BGSF', 'IVAC', 'ASFH', 'RVSN', 'SOAR', 'APT', 'ESP', 'BWEN', 'XOS', 'KSCP', 'HSON', 'SUGP', 'LICN', 'HOVR', 'SNT', 'UNXP', 'OP', 'CVR', 'CLWT', 'GRHI', 'KIQ', 'QWTR', 'YJGJ', 'JCSE', 'MACE', 'KRFG', 'TLSS', 'DRFS', 'BRDSQ', 'HLLK', 'MKULQ', 'TSP', 'ACMB', 'PWDY', 'TMRR']
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# ['RTO', 'HLLK']
# missingincomeyears =
# ['CWST', 'FA', 'BV', 'GNK', 'EGLE', 'BBCP', 'KODK', 'POWW', 'SKYX', 'HRBR', 'CODA', 'AGSS', 'CLIR', 'APWC', 'LWLW', 'OP', 'ALPP', 'AIRI', 'IVDA', 'KWE', 'SGBX', 'QWTR', 'TLSS', 'STAF', 'NVGT', 'CIRX', 'BRBL', 'RNWR', 'PWDY', 'IWAL', 'CDXQ']
# missingdivyears =
# ['GPN', 'CWST', 'FA', 'BV', 'GNK', 'EGLE', 'LMB', 'BBCP', 'KODK', 'POWW', 'SKYX', 'HRBR', 'CODA', 'AGSS', 'APWC', 'LWLW', 'ALPP', 'AIRI', 'IVDA', 'KWE', 'CAMG', 'QWTR', 'TLSS', 'STAF', 'NVGT', 'CIRX', 'BRBL', 'RNWR', 'PWDY', 'PCTL', 'IWAL', 'CDXQ']
# missingroicyears =
# ['EGLE', 'POWW', 'SKYX', 'HRBR', 'CODA', 'AGSS', 'CLIR', 'APWC', 'LWLW', 'ALPP', 'AIRI', 'IVDA', 'KWE', 'QWTR', 'NVGT', 'CIRX', 'BRBL', 'RNWR', 'PWDY', 'IWAL', 'CDXQ']
# wrongincomeendyear =
# ['CNI', 'CTAS', 'FDX', 'PAYX', 'RYAAY', 'BAH', 'ZTO', 'WMS', 'UHAL', 'PAC', 'RBC', 'CAE', 'BZ', 'CPA', 'OMAB', 'ENS', 'AVAV', 'CSWI', 'GMS', 'KFY', 'WOR', 'AIR', 'TGH', 'AZZ', 'SCS', 'APOG', 'CMCO', 'TGI', 'CPLP', 'TRNS', 'THR', 'TDCX', 'VLRS', 'AZUL', 'NAT', 'EH', 'FLYX', 'SWBI', 'AGX', 'EBF', 'ADSE', 'RGP', 'AMSC', 'AMBI', 'PKE', 'ESEA', 'POWW', 'GASS', 'GHM', 'FLCX', 'ICTSF', 'SATL', 'ZCAR', 'TAYD', 'HRBR', 'OMEX', 'STI', 'MEEC', 'PYRGF', 'GTII', 'GP', 'PPIH', 'RSKIA', 'EDRY', 'BUKS', 'NSGP', 'PPSI', 'AIRT', 'BEST', 'ASTR', 'GTEC', 'AERT', 'CVU', 'OESX', 'VCIG', 'TPCS', 'DFLI', 'CACO', 'FATH', 'SNT', 'PGTK', 'APWC', 'JYD', 'GFAI', 'EPOW', 'GTMAY', 'CETY', 'OPTT', 'KITT', 'AUSI', 'ALPP', 'GWAV', 'AIRI', 'QIND', 'SNRG', 'EAWD', 'OCLN', 'YGMZ', 'IDEX', 'CLWT', 'WLGS', 'MWG', 'HIHO', 'LASE', 'ILAG', 'MNTS', 'CHNR', 'CRWE', 'TIKK', 'RAYA', 'CAMG', 'OZSC', 'GPOX', 'BURU', 'BLNC', 'NORD', 'VIEW', 'SGBX', 'ATXG', 'UNQL', 'AGFY', 'QWTR', 'PTRAQ', 'BWVI', 'SENR', 'SMX', 'TBLT', 'YJGJ', 'AEHL', 'JCSE', 'BKYI', 'UUU', 'JAN', 'MACE', 'AMMJ', 'KRFG', 'TLSS', 'STAF', 'PTNYF', 'AETHF', 'RCRT', 'WARM', 'IMHC', 'JKSM', 'NVGT', 'DRFS', 'SPCB', 'EFSH', 'AULT', 'BLIS', 'DLYT', 'SSET', 'BRDSQ', 'FIFG', 'COUV', 'JFIL', 'GXXM', 'ZEVY', 'KDCE', 'DTII', 'DGWR', 'GDSI', 'BBRW', 'JPEX', 'CIRX', 'WOEN', 'PHOT', 'AFIIQ', 'MJHI', 'MKULQ', 'WLMSQ', 'RNWR', 'YAYO', 'CHEAF', 'CHKIF', 'GOL', 'GNGYF', 'YELLQ', 'NM-PH', 'TSP', 'ACMB', 'ADMQ', 'USDP', 'UCIX', 'PRPI', 'AMMX', 'PWDY', 'RELT', 'TMRR', 'PCTL', 'ECOX', 'RENO', 'CDXQ', 'HYREQ']
# wrongdivendyear =
# ['CNI', 'CTAS', 'FDX', 'PAYX', 'RYAAY', 'BAH', 'ZTO', 'WMS', 'UHAL', 'PAC', 'RBC', 'CAE', 'BZ', 'CPA', 'OMAB', 'ENS', 'AVAV', 'CSWI', 'GMS', 'KFY', 'WOR', 'AIR', 'TGH', 'BBU', 'AZZ', 'SCS', 'APOG', 'CMCO', 'TGI', 'CPLP', 'TRNS', 'THR', 'TDCX', 'VLRS', 'NAT', 'EH', 'SWBI', 'AGX', 'EBF', 'ADSE', 'RGP', 'AMSC', 'AMBI', 'PKE', 'ESEA', 'POWW', 'GASS', 'GHM', 'FLCX', 'SCWO', 'SATL', 'ZCAR', 'TAYD', 'HRBR', 'OMEX', 'MEEC', 'PYRGF', 'GTII', 'GP', 'PPIH', 'RSKIA', 'EDRY', 'BUKS', 'NSGP', 'PPSI', 'AIRT', 'BEST', 'ASTR', 'GTEC', 'LTBR', 'CVU', 'OESX', 'VCIG', 'TPCS', 'DFLI', 'HOVR', 'CACO', 'FATH', 'SNT', 'PGTK', 'APWC', 'JYD', 'GFAI', 'UNXP', 'EPOW', 'GTMAY', 'CETY', 'OPTT', 'KITT', 'AUSI', 'OP', 'ALPP', 'GWAV', 'AIRI', 'QIND', 'SNRG', 'EAWD', 'OCLN', 'YGMZ', 'IDEX', 'CLWT', 'WLGS', 'MWG', 'HIHO', 'LASE', 'ILAG', 'MNTS', 'CHNR', 'CRWE', 'TIKK', 'RAYA', 'CAMG', 'OZSC', 'ENG', 'GPOX', 'BLNC', 'NORD', 'VIEW', 'SGBX', 'ATXG', 'UNQL', 'AGFY', 'QWTR', 'PTRAQ', 'BWVI', 'SENR', 'TBLT', 'YJGJ', 'AEHL', 'JCSE', 'BKYI', 'UUU', 'JAN', 'MACE', 'AMMJ', 'KRFG', 'TLSS', 'STAF', 'PTNYF', 'AETHF', 'RCRT', 'WARM', 'IMHC', 'JKSM', 'NVGT', 'DRFS', 'SPCB', 'EFSH', 'AULT', 'BLIS', 'DLYT', 'SSET', 'BRDSQ', 'FIFG', 'COUV', 'JFIL', 'GXXM', 'HWKE', 'ZEVY', 'KDCE', 'DTII', 'DGWR', 'GDSI', 'BBRW', 'JPEX', 'CIRX', 'WOEN', 'PHOT', 'AFIIQ', 'MJHI', 'MKULQ', 'WLMSQ', 'RNWR', 'YAYO', 'CHEAF', 'CHKIF', 'YELLQ', 'NM-PH', 'TSP', 'ACMB', 'ADMQ', 'UCIX', 'PRPI', 'AMMX', 'PWDY', 'RELT', 'TMRR', 'PCTL', 'ECOX', 'RENO', 'CDXQ', 'HYREQ']
# wrongroicendyear =
# ['CNI', 'CTAS', 'FDX', 'PAYX', 'RYAAY', 'BAH', 'ZTO', 'WMS', 'UHAL', 'PAC', 'RBC', 'CAE', 'BZ', 'CPA', 'OMAB', 'ENS', 'AVAV', 'CSWI', 'GMS', 'KFY', 'WOR', 'AIR', 'TGH', 'AZZ', 'SCS', 'APOG', 'CMCO', 'TGI', 'CPLP', 'TRNS', 'THR', 'TDCX', 'VLRS', 'NAT', 'EH', 'SWBI', 'AGX', 'EBF', 'ADSE', 'RGP', 'AMSC', 'AMBI', 'PKE', 'ESEA', 'POWW', 'GASS', 'GHM', 'FLCX', 'ICTSF', 'ZCAR', 'TAYD', 'HRBR', 'OMEX', 'MEEC', 'PYRGF', 'GTII', 'GP', 'PPIH', 'RSKIA', 'EDRY', 'BUKS', 'NSGP', 'PPSI', 'AIRT', 'BEST', 'ASTR', 'GTEC', 'CVU', 'OESX', 'VCIG', 'TPCS', 'DFLI', 'CACO', 'FATH', 'SNT', 'PGTK', 'APWC', 'JYD', 'GFAI', 'EPOW', 'GTMAY', 'CETY', 'OPTT', 'KITT', 'AUSI', 'OP', 'ALPP', 'GWAV', 'AIRI', 'QIND', 'SNRG', 'EAWD', 'OCLN', 'YGMZ', 'IDEX', 'CLWT', 'WLGS', 'MWG', 'HIHO', 'LASE', 'ILAG', 'MNTS', 'CHNR', 'CRWE', 'TIKK', 'RAYA', 'CAMG', 'OZSC', 'GPOX', 'BLNC', 'NORD', 'VIEW', 'SGBX', 'ATXG', 'UNQL', 'AGFY', 'QWTR', 'PTRAQ', 'BWVI', 'SENR', 'SMX', 'TBLT', 'YJGJ', 'AEHL', 'JCSE', 'BKYI', 'UUU', 'JAN', 'MACE', 'AMMJ', 'KRFG', 'TLSS', 'STAF', 'PTNYF', 'AETHF', 'RCRT', 'WARM', 'IMHC', 'JKSM', 'NVGT', 'DRFS', 'SPCB', 'EFSH', 'AULT', 'BLIS', 'DLYT', 'SSET', 'BRDSQ', 'FIFG', 'COUV', 'JFIL', 'GXXM', 'ZEVY', 'KDCE', 'DTII', 'DGWR', 'GDSI', 'BBRW', 'JPEX', 'CIRX', 'WOEN', 'PHOT', 'AFIIQ', 'MJHI', 'MKULQ', 'WLMSQ', 'RNWR', 'YAYO', 'CHEAF', 'CHKIF', 'YELLQ', 'NM-PH', 'TSP', 'ACMB', 'ADMQ', 'UCIX', 'PRPI', 'AMMX', 'PWDY', 'RELT', 'TMRR', 'PCTL', 'ECOX', 'RENO', 'CDXQ', 'HYREQ']
###

###NEW Energy
# recapList = 
# ['TTE', 'PBR', 'BP', 'ET', 'MPLX', 'BKR', 'EC', 'CCJ', 'OMVKY', 'GLPEY', 'PAA', 'WES', 'HESM', 'IDKOY', 'SUN', 'ADOOY', 'BSM', 'NS', 'USAC', 'CRGY', 'GLP', 'NRP', 'SBR', 'NGL', 'PBT', 'WTI', 'SJT', 'MVO', 'GVXXF', 'KGEI', 'VOC', 'CRT', 'MMLP', 'ANLDF', 'MPIR', 'BPT', 'PRT', 'PVL', 'NRT', 'CHKR', 'CWPE', 'HGTXU', 'MTR', 'BKUCF', 'EGYF', 'MARPS', 'ECTM', 'GULTU', 'SSOF', 'FECOF', 'REOS', 'NXMR', 'AURI', 'SAPMF', 'CRNZF', 'SDTTU']
# missingRevenue =
# ['APA', 'OILY', 'SRNW', 'TPET', 'GRVE', 'GSPE', 'BRLL', 'MSCH']
# missingNetIncome =
# []
# missingOpCF =
# ['CPG']
# missingCapEx =
# ['SHEL', 'TTE', 'EOG', 'PSX', 'SU', 'WDS', 'FANG', 'PR', 'APA', 'CHRD', 'SM', 'MGY', 'CPG', 'BSM', 'STR', 'WHD', 'BTE', 'GPOR', 'TALO', 'CRGY', 'HPK', 'VET', 'MNR', 'BORR', 'EE', 'GRNT', 'NESR', 'VTS', 'DEC', 'TXO', 'BRY', 'UROY', 'AMPY', 'EPM', 'GTE', 'PNRG', 'TRLM', 'PHX', 'EPSN', 'MXC', 'VYEY', 'OILY', 'SRNW', 'TPET', 'PTCO', 'ROYL', 'ALTX', 'CRCE', 'FECOF', 'GRVE', 'AMNI', 'QREE', 'DBRM', 'ALPSQ', 'CJAX', 'BRLL', 'MRGE', 'MSCH', 'OKMN']      
# missingNetCF =
# []
# missingDepreNAmor =
# ['SHEL', 'TTE', 'BP', 'EQNR', 'CNQ', 'EPD', 'E', 'SU', 'WDS', 'MPLX', 'CVE', 'EC', 'CCJ', 'TS', 'PBA', 'PR', 'YPF', 'HESM', 'CSAN', 'UGP', 'NE', 'VNOM', 'VVV', 'SUN', 'VAL', 'PTEN', 'SM', 'NXE', 'CPG', 'EURN', 'STNG', 'ERF', 'TGS', 'TRMD', 'VIST', 'BTE', 'DNN', 'DHT', 'VET', 'BORR', 'FLNG', 'NEXT', 'DO', 'PDS', 'EU', 'GRNT', 'EFXT', 'VTS', 'DEC', 'OBE', 'GPRK', 'GFR', 'UROY', 'BROG', 'TRLM', 'DLNG', 'EPSN', 'NINE', 'IMPP', 'WSTRF', 'PXS', 'ZNOG', 'LRDC', 'TRLEF', 'SRNW', 'TPET', 'PTCO', 'CRCE', 'FECOF', 'GSPE', 'QREE', 'PCCYF', 'SNPMF', 'THNPF', 'SPTJF', 'GLOG-PA', 'VTDRF', 'BRLL', 'MRGE', 'MSCH']
# missing income prop sales
# []
# missingIntPaid =
# ['EQNR', 'TPL', 'WFRD', 'XPRO', 'EE', 'DMLP', 'CLNE', 'SND', 'NCSM', 'CKX', 'VIVK', 'SPND', 'SRNW', 'ALTX', 'CRCE', 'ALPSQ', 'PQEFF', 'OKMN']
# missingDivTotalPaid =
# []
# missingSshares =
# []
# missingTotalEquity =
# []
# missingincomeyears =
# ['PBR', 'SUN', 'VAL', 'CRC', 'TDW', 'BTU', 'PARR', 'SBOW', 'SD', 'UNTC', 'AMPY', 'KLXE', 'BATL', 'PFIE', 'CEI', 'OILY', 'GWTI', 'VTDRF']
# missingdivyears =
# ['NXE', 'CRC', 'TDW', 'BTU', 'PARR', 'LEU', 'SBOW', 'NESR', 'SD', 'UNTC', 'AMPY', 'KLXE', 'BATL', 'PFIE', 'CEI', 'OILY', 'GWTI', 'VTDRF']
# missingroicyears =
# ['SBOW', 'SD', 'CEI', 'OILY', 'GWTI']
# wrongincomeendyear =
# ['PBR', 'EC', 'YPF', 'CSAN', 'UGP', 'FRO', 'EURN', 'TGS', 'VIST', 'LPG', 'NGL', 'NESR', 'UNTC', 'UROY', 'BROG', 'PNRG', 'DLNG', 'IMPP', 'WSTRF', 'WTRV', 'PXS', 'SMGI', 'BANL', 'QSEP', 'INDO', 'VIVK', 'MXC', 'SPND', 'LRDC', 'TRLEF', 'VYEY', 'OILY', 'SNMP', 'NSFDF', 'GWTI', 'PTCO', 'NRIS', 'ROYL', 'OILCF', 'GRVE', 'GSPE', 'VBHI', 'AMNI', 'QREE', 'DBRM', 'MMEX', 'PCCYF', 'SNPMF', 'ATGFF', 'THNPF', 'SPTJF', 'VTDRF', 'ALPSQ', 'PQEFF', 'BRLL', 'MRGE', 'MSCH', 'FTXP', 'BBLS']
# wrongdivendyear =
# ['YPF', 'CSAN', 'UGP', 'FRO', 'EURN', 'TGS', 'VIST', 'LPG', 'TNP', 'NESR', 'UNTC', 'UROY', 'BROG', 'PNRG', 'IMPP', 'WSTRF', 'WTRV', 'PXS', 'SMGI', 'BANL', 'QSEP', 'INDO', 'VIVK', 'MXC', 'SPND', 'LRDC', 'TRLEF', 'VYEY', 'OILY', 'SNMP', 'NSFDF', 'GWTI', 'PTCO', 'NRIS', 'ROYL', 'ALTX', 'OILCF', 'GRVE', 'GSPE', 'VBHI', 'AMNI', 'QREE', 'DBRM', 'MMEX', 'PCCYF', 'SNPMF', 'ATGFF', 'THNPF', 'SPTJF', 'VTDRF', 'ALPSQ', 'PQEFF', 'BRLL', 'MRGE', 'MSCH', 'FTXP', 'BBLS']
# wrongroicendyear =
# ['YPF', 'CSAN', 'UGP', 'FRO', 'EURN', 'TGS', 'VIST', 'LPG', 'TNP', 'NESR', 'UNTC', 'UROY', 'BROG', 'PNRG', 'DLNG', 'IMPP', 'WSTRF', 'WTRV', 'PXS', 'SMGI', 'BANL', 'QSEP', 'VIVK', 'MXC', 'SPND', 'LRDC', 'TRLEF', 'VYEY', 'OILY', 'SNMP', 'NSFDF', 'GWTI', 'PTCO', 'NRIS', 'ROYL', 'OILCF', 'GRVE', 'GSPE', 'VBHI', 'AMNI', 'QREE', 'DBRM', 'MMEX', 'PCCYF', 'SNPMF', 'ATGFF', 'THNPF', 'SPTJF', 'VTDRF', 'ALPSQ', 'PQEFF', 'BRLL', 'MRGE', 'MSCH', 'FTXP', 'BBLS']
###

###NEW HEALTH
# recap list: 
# ['CSLLY', 'IQV', 'SAUHY', 'SGIOY', 'RYZB', 'GNNDY', 'NHNKY', 'BTSG', 'AMAM', 'PHVS', 'LTGHY', 'BIOGY', 'ABVX', 'AVBP', 'PRTC', 'GUTS', 'ANRO', 'NBTX', 'ANL', 'TLSI', 'IPHA', 'GNFT', 'MESO', 'CYBN', 'BSEM', 'AMIX', 'GALT', 'MLEC', 'GRUSF', 'LUDG', 'MSCLF', 'ONMD', 'GDTC', 'SLDX', 'VTVT', 'OCEA', 'GXXY', 'NRXS', 'IMRN', 'MSTH', 'LVRLF', 'CBIH', 'GSAC', 'XTLB', 'GRPS', 'BPTS', 'XRTX', 'SZLSF', 'REPCF', 'JUVAF', 'SFWJ', 'RSHN', 'ICCO', 'EBYH', 'ECGI', 'XCRT', 'TEVNF', 'NXGB', 'BLFE', 'CBDL', 'MGX', 'CHRO', 'RSCI', 'CUBT', 'CSSI', 'HALB', 'WSRC', 'AGNPF', 'SLHGF', 'NBCO', 'EMGE', 'FZRO', 'CNNA', 'DHAI']
# missing income revenue
# ['NVS', 'SNY', 'PCVX', 'IMVT', 'NUVL', 'BHVN', 'MLTX', 'AMED', 'NMRA', 'GPCR', 'VERA', 'APGE', 'PROK', 'EWTX', 'DYN', 'IRON', 'KURA', 'DAWN', 'BLTE', 'SANA', 'CABA', 'AKRO', 'GRCL', 'CRGX', 'TYRA', 'TRML', 'VERV', 'SSII', 'OLMA', 'ZNTL', 'ORIC', 'ETNB', 'SLRN', 'ABVX', 'HLVX', 'IGMS', 'CMPS', 'LBPH', 'BMEA', 'ELVN', 'MLYS', 'ANTX', 'AVTE', 'IVVD', 'AVXL', 'REPL', 'LIAN', 'ANNX', 'AURA', 'THRD', 'NUVB', 'CELC', 'TNYA', 'PEPG', 'NAUT', 'RPTX', 'INZY', 'HUMA', 'AEON', 'ACET', 'KOD', 'ERAS', 'TLSI', 'HOWL', 'GLUE', 'DRTS', 'CDT', 'GOSS', 'JSPR', 'ALDX', 'CMPX', 'THRX', 'ENGN', 'MNMD', 'ABOS', 'GRPH', 'PDSB', 'ZURA', 'PYXS', 'VOR', 'PRLD', 'ARMP', 'VTYX', 'ELEV', 'ATHA', 'NVCT', 'RVPH', 'IOBT', 'ALLK', 'CYT', 'KNTE', 'IMUX', 'GLSI', 'LIFW', 'VIGL', 'RGC', 'GALT', 'IRME', 'CRVS', 'TRVI', 'PMVP', 'CTCX', 'ACRV', 'ELYM', 'CGTX', 'MURA', 'RBOT', 'RLYB', 'SKYE', 'ANEB', 'VICP', 'GNTA', 'CDTX', 'AVRO', 'RTGN', 'RPHM', 'PASG', 'QNCX', 'CALC', 'MIST', 'ICU', 'INAB', 'ENLV', 'BIVI', 'SSIC', 'INTS', 'BEAT', 'LTRN', 'ESLA', 'CLRB', 'ACXP', 'RZLT', 'NRXP', 'ACHL', 'PMN', 'NKGN', 'ONMD', 'MOVE', 'PYPD', 'INKT', 'VINC', 'RNXT', 'APRE', 'NRBO', 'SNSE', 'BCLI', 'OCEA', 'XLO', 'NLSP', 'GLTO', 'CNTX', 'MIRA', 'INDP', 'ICCT', 'AKTX', 'CHEK', 'CVKD', 'BCEL', 'PHGE', 'GRTX', 'VIRI', 'APM', 'CMMB', 'QLIS', 'ALZN', 'HOTH', 'SHPH', 'ATXI', 'BPTS', 'VRPX', 'ARTL', 'CPMV', 'STSS', 'PRFX', 'SNPX', 'ONCO', 'CING', 'CWBR', 'NBSE', 'ALLR', 'CNSP', 'ADIL', 'KRBP', 'ATNF', 'IONM', 'NVIV', 'DRMA', 'REVB', 'THAR', 'ZVSA', 'BLPH', 'RNAZ', 'KTRA', 'PPCB', 'RBSH', 'GNRS', 'NMTRQ', 'TELO', 'FBLG', 'RAIN', 'SIOX', 'RAPH', 'SKYI', 'CANQF', 'EVLO', 'PHBI', 'CLCS', 'CNNA', 'DHAI']
# missing income netIncome
# []
# missing income opCF
# ['PHG', 'ONCY']
# missing income capEx
# ['LLY', 'WAT', 'RPRX', 'NUVL', 'VKTX', 'PRTA', 'ALHC', 'MD', 'MLYS', 'ANTX', 'ZIMV', 'NUVB', 'TLSI', 'INMB', 'CDT', 'APLT', 'SGMT', 'JSPR', 'IVA', 'MNMD', 'ZURA', 'BCAB', 'NVCT', 'RVPH', 'NGM', 'ANVS', 'GLSI', 'MGRM', 'COYA', 'ELYM', 'TIHE', 'ANEB', 'VICP', 'BCTX', 'RTGN', 'PASG', 'PHCI', 'ICU', 'INAB', 'BIVI', 'SSIC', 'CKPT', 'INTS', 'ESLA', 'ACXP', 'DYAI', 'RMTI', 'NKGN', 'ONMD', 'MDAI', 'BKUH', 'RNXT', 'ETAO', 'MAIA', 'MDNAF', 'CLDI', 'OHCS', 'PMCB', 'OCEA', 'COEP', 'NBIO', 'BIXT', 'MIRA', 'ICCT', 'ALRTF', 'ELAB', 'MCUJF', 'DRUG', 'INTI', 'EDXC', 'VIRI', 'ALID', 'SNGX', 'PKTX', 'RSCF', 'ACBM', 'ADTX', 'ALZN', 'CELZ', 'ATXI', 'BPTS', 'XRTX', 'MNPR', 'LIXT', 'VRPX', 'ARTL', 'LSDI', 'SILO', 'BZYR', 'ACON', 'ENSC', 'RGBP', 'IPIX', 'QRON', 'HSTC', 'INQD', 'NXL', 'EVOK', 'INBS', 'VRAX', 'ATNF', 'PXMD', 'DRMA', 'CSUI', 'PAXH', 'ATHXQ', 'HADV', 'NXEN', 'USAQ', 'THAR', 'ZVSA', 'INQR', 'GCAN', 'ENMI', 'VYND', 'KTRA', 'QTXB', 'CNBX', 'EMED', 'BLMS', 'BBBT', 'VNTH', 'RGMP', 'QBIO', 'GNRS', 'TELO', 'BFFTF', 'SIOX', 'SKYI', 'IGEX', 'REMI', 'GRNF', 'IGPK', 'SNNC', 'THCT', 'CNNA', 'SYBE', 'SSTC', 'DHAI']
# missing income netCF
# ['HLN', 'ARGX', 'MDXH', 'CSTF', 'IGPK', 'CNNA']
# missing income depreNAmor
# ['NVO', 'ABBV', 'NVS', 'AZN', 'ABT', 'ISRG', 'ELV', 'SNY', 'GILD', 'GSK', 'TAK', 'HLN', 'ALC', 'GEHC', 'MTD', 'ARGX', 'BNTX', 'WAT', 'PHG', 'GMAB', 'HOLX', 'RPRX', 'RDY', 'SNN', 'LEGN', 'MEDP', 'STVN', 'APLS', 'ASND', 'IONS', 'ITCI', 'GRFS', 'IMVT', 'NUVL', 'AXSM', 'OGN', 'ALVO', 'MLTX', 'OLK', 'SMMT', 'VKTX', 'EVO', 'MOR', 'GLPG', 'CNMD', 'INDV', 'GPCR', 'VERA', 'HRMY', 'SNDX', 'APGE', 'EWTX', 'KROS', 'AMRX', 'ALPN', 'KURA', 'ATRC', 'PHVS', 'STAA', 'EYPT', 'MRVI', 'TNGX', 'BLTE', 'SANA', 'IMTX', 'MDXG', 'RLAY', 'CABA', 'AKRO', 'AMLX', 'TARS', 'RNA', 'CRGX', 'PLRX', 'AGTI', 'QTRX', 'ORIC', 'SLN', 'CRLBF', 'ZYME', 'ETNB', 'ABVX', 'EXAI', 'CVAC', 'PHAR', 'ICVX', 'HLVX', 'MPLN', 'IGMS', 'VREX', 'PRTC', 'BMEA', 'MLYS', 'ANTX', 'PRAX', 'EDIT', 'AVTE', 'CALT', 'MREO', 'VALN', 'ARQT', 'IVVD', 'LUNG', 'ADPT', 'CVRX', 'FULC', 'ORGO', 'TRDA', 'ESPR', 'PLSE', 'OCS', 'KRRO', 'LIAN', 'NPCE', 'EPIX', 'ABUS', 'GHRS', 'ZYXI', 'JANX', 'PROC', 'VYGR', 'AURA', 'NBTX', 'THRD', 'CGC', 'CELC', 'KMDA', 'NAUT', 'RPTX', 'SPOK', 'HUMA', 'NYXH', 'ADCT', 'AAGH', 'TSHA', 'SOPH', 'IMMP', 'ACIU', 'KOD', 'IPSC', 'UTMD', 'LRMR', 'ADAP', 'TLSI', 'HOWL', 'LYRA', 'GNLX', 'OPT', 'FGEN', 'GLUE', 'LMDXF', 'DRTS', 'LFMD', 'BDTX', 'CLLS', 'VRCA', 'INMB', 'SGHT', 'PROF', 'CDT', 'CORBF', 'IPHA', 'AUGX', 'GLYC', 'APLT', 'CDXS', 'OGI', 'OMGA', 'STOK', 'SGMT', 'STXS', 'CGEN', 'GNFT', 'ACB', 'QIPT', 'IVA', 'ALDX', 'SCPH', 'THRX', 'MNMD', 'ABOS', 'IMRX', 'DBVT', 'PRQR', 'LDDD', 'TELA', 'ZURA', 'XBIT', 'CRMD', 'MESO', 'VOR', 'RLMD', 'MOLN', 'CPSI', 'CYBN', 'VTYX', 'ZTEK', 'HITI', 'INO', 'DSGN', 'ELEV', 'PETS', 'ATHA', 'GTH', 'NVCT', 'RVPH', 'NGM', 'DMAC', 'ANVS', 'SEER', 'RNAC', 'MDWD', 'PLX', 'MDXH', 'GLSI', 'SHLT', 'BWAY', 'MYO', 'RGC', 'DCTH', 'IRME', 'COYA', 'IFRX', 'PMVP', 'LPTX', 'ELMD', 'CLSD', 'VAXX', 'ONCY', 'ACRV', 'BLRX', 'MLEC', 'CMRX', 'AFMD', 'THTX', 'GRUSF', 'ELYM', 'MURA', 'CRDL', 'INCR', 'RBOT', 'IKNA', 'SKYE', 'ANEB', 'IMMX', 'ICCM', 'VICP', 'APLM', 'HLCO', 'PRE', 'CNTB', 'IPA', 'RTGN', 'HRGN', 'DRIO', 'LNSR', 'CLNN', 'PHCI', 'ICU', 'INAB', 'TLSA', 'ALGS', 'IXHL', 'BIVI', 'SSIC', 'CKPT', 'INTS', 'PVCT', 'BEAT', 'PNPL', 'OKYO', 'BYSI', 'LVTX', 'OMIC', 'ESLA', 'ACXP', 'DYAI', 'DXR', 'PNXP', 'FIXX', 'ICCC', 'NRXP', 'NYMXF', 'EVGN', 'YS', 'ELTX', 'EUDA', 'PMN', 'NKGN', 'ONMD', 'SYRA', 'MDAI', 'CCM', 'PYPD', 'BGXX', 'HUGE', 'PLUR', 'BFRG', 'NSYS', 'BKUH', 'ENTX', 'INKT', 'CNTG', 'RLFTY', 'RNXT', 'GDTC', 'PHXM', 'MAIA', 'MDNAF', 'ACST', 'HSTI', 'PPBT', 'COCH', 'FBRX', 'MYNZ', 'AIH', 'EVAX', 'NRBO', 'CLDI', 'ITRM', 'VTVT', 'TRIB', 'AIM', 'SNTI', 'BCLI', 'OCEA', 'NRSN', 'IKT', 'NLSP', 'GLTO', 'OTLC', 'LABP', 'RDHL', 'NCNA', 'BIXT', 'MIRA', 'RASP', 'INDP', 'ICCT', 'ATHE', 'NNVC', 'OSA', 'PRTG', 'MBIO', 'IINN', 'CVKD', 'ADXN', 'ALRTF', 'GBNH', 'NTBL', 'IMRN', 'ELAB', 'MCUJF', 'AVCRF', 'TBIO', 'ZCMD', 'ASLN', 'ARTH', 'MGRX', 'DRUG', 'AEZS', 'SONX', 'INTI', 'VIRI', 'HSCS', 'LVRLF', 'GENE', 'KZIA', 'BNOX', 'GTBP', 'CMMB', 'GNPX', 'PKTX', 'ACBM', 'QLIS', 'ADTX', 'KTTA', 'HENC', 'ALZN', 'HOTH', 'SHPH', 'AFIB', 'ABTI', 'BPTH', 'ATXI', 'XTLB', 'XCUR', 'MDGS', 'MEDS', 'BPTS', 'XRTX', 'MNPR', 'LIXT', 'CMND', 'VRPX', 'MDVL', 'ARTL', 'LSDI', 'CPMV', 'HSDT', 'SILO', 'PRFX', 'ISPC', 'PTIX', 'PBLA', 'PCSA', 'ONCO', 'ENSC', 'AGRX', 'BDRX', 'CING', 'QNRX', 'IMCC', 'RGBP', 'SXTP', 'IPIX', 'FOXO', 'CYTO', 'QRON', 'HSTC', 'PCYN', 'NXL', 'EVOK', 'CNSP', 'AKAN', 'AGTX', 'ADIL', 'KRBP', 'VRAX', 'ATNF', 'SPRC', 'PXMD', 'SEQL', 'NEPT', 'BBLG', 'GSTC', 'SINT', 'CMRA', 'BXRX', 'REVB', 'PAXH', 'BFRI', 'HADV', 'NXEN', 'THAR', 'ZVSA', 'PKBO', 'BLPH', 'GRI', 'INQR', 'TCBP', 'GCAN', 'ENMI', 'VYND', 'KTRA', 'CNBX', 'TPIA', 'CSTF', 'SIGY', 'BLMS', 'VNTH', 'GLSHQ', 'RGMP', 'QBIO', 'PEARQ', 'INFIQ', 'TMBRQ', 'GNRS', 'NMTRQ', 'TELO', 'FBLG', 'ABCZF', 'SWGHF', 'BFFTF', 'RAPH', 'XTXXF', 'SKYI', 'PMEDF', 'TMDIF', 'CLYYF', 'IGEX', 'CANQF', 'ABMT', 'GRNF', 'IGPK', 'SNNC', 'EVLO', 'WCUI', 'MYMX', 'PHBI', 'CBGL', 'SCPS', 'CLCS', 'GRYN', 'CNNA', 'SYBE', 'SSTC', 'WLSS', 'AMJT', 'DHAI']
# missing income prop sales
# []
# missing div intPaid
# ['ISRG', 'MRNA', 'VEEV', 'KRTX', 'MEDP', 'CRSP', 'DOCS', 'NUVL', 'AXSM', 'SHC', 'RCM', 'ACAD', 'SGRY', 'BHVN', 'RARE', 'MLTX', 'AXNX', 'IDYA', 'ACLX', 'VKTX', 'NMRA', 'NTLA', 'DNLI', 'BEAM', 'VRNOF', 'GPCR', 'KYMR', 'SDGR', 'PTCT', 'APGE', 'EWTX', 'DYN', 'INBX', 'AMRX', 'WRBY', 'TARO', 'CPRX', 'TNDM', 'ABCL', 'SAGE', 'RCUS', 'AGIO', 'KNSA', 'MIRM', 'VIR', 'SANA', 'FDMT', 'RLAY', 'CABA', 'SAVA', 'ARCT', 'AMLX', 'ACCD', 'EMBC', 'TYRA', 'TRML', 'VERV', 'RAPT', 'SYRE', 'ZNTL', 'ORIC', 'HSTM', 'ZYME', 'SLRN', 'CGEM', 'IGMS', 'LBPH', 'PRME', 'BMEA', 'ELVN', 'ALEC', 'MLYS', 'ANTX', 'PRAX', 'EDIT', 'IRMD', 'URGN', 'YMAB', 'HCAT', 'IVVD', 'COGT', 'NKTX', 'FULC', 'TRDA', 'LYEL', 'STTK', 'ANNX', 'NRIX', 'JANX', 'TALK', 'AURA', 'TERN', 'ITOS', 'NUVB', 'AVIR', 'TNYA', 'TCMD', 'PEPG', 'ANIK', 'NAUT', 'RPTX', 'NNOX', 'VMD', 'AEON', 'TSVT', 'AMWL', 'AKYA', 'BTMD', 'BVS', 'SLDB', 'CCCC', 'ERAS', 'OVID', 'ADAP', 'SERA', 'LYRA', 'GTHX', 'GNLX', 'VNDA', 'GLUE', 'DRTS', 'GLYC', 'APLT', 'BLUE', 'STOK', 'SGMT', 'THRX', 'IMRX', 'GRPH', 'LDDD', 'ZURA', 'XBIT', 'PYXS', 'VOR', 'PRLD', 'JYNT', 'CYBN', 'VTYX', 'DSGN', 'GBIO', 'PETS', 'NVCT', 'NGM', 'DMAC', 'LIFE', 'ANVS', 'ALLK', 'CYT', 'KNTE', 'GLSI', 'SY', 'VIGL', 'MGRM', 'RGC', 'CRVS', 'COYA', 'SGMO', 'CLSD', 'ONCY', 'CTCX', 'CELU', 'ACRV', 'ACRS', 'CSBR', 'AFMD', 'THTX', 'ALVR', 'ELYM', 'HYPR', 'SPRO', 'MURA', 'CRDL', 'INCR', 'IKNA', 'ICCM', 'VICP', 'GNTA', 'RPHM', 'PASG', 'CALC', 'INAB', 'TSBX', 'LTRN', 'MTNB', 'ESLA', 'CLRB', 'ELDN', 'ACXP', 'DYAI', 'DXR', 'FIXX', 'BOLT', 'ACHL', 'EUDA', 'NKGN', 'SLGL', 'SNCE', 'BGXX', 'MEIP', 'ENTX', 'CARA', 'FRLN', 'ATIP', 'APRE', 'MDNAF', 'ALRN', 'CWBHF', 'COCH', 'ITRM', 'CMAX', 'CCLD', 'SNTI', 'SRZN', 'XLO', 'EDSA', 'INDP', 'ICCT', 'RNLX', 'TLIS', 'NXGL', 'ORGS', 'TOVX', 'PRPO', 'DRUG', 'AEZS', 'SONX', 'NHIQ', 'BNTC', 'CYCN', 'QLIS', 'BPTH', 'CLVR', 'TTNP', 'RSLS', 'FNCH', 'SNPX', 'BZYR', 'ONCO', 'AVTX', 'NURO', 'APVO', 'ARDS', 'LOWLF', 'SLRX', 'INBS', 'ADIL', 'VRAX', 'GLMD', 'HADV', 'NBY', 'BLPH', 'GRI', 'INQR', 'SDCCQ', 'STMH', 'GNRS', 'RAPH', 'SKYI', 'SQZB', 'TOMDF', 'WLSS']
# missing div totalPaid
# []
# missing div shares
# []
# missing roic total equity
# ['SLN', 'SKYI']
# missing income years:
# ['ALC', 'SGRY', 'SMMT', 'LIVN', 'LFST', 'MDRX', 'MNKD', 'ESPR', 'RENB', 'RLMD', 'KRMD', 'CRDF', 'CRVO', 'SSIC', 'RZLT', 'NMTC', 'ETST', 'ABIO', 'AURX', 'HSTI', 'IMTH', 'BCLI', 'PETV', 'RXMD', 'EDSA', 'RASP', 'ADXS', 'BUDZ', 'CANN', 'ALID', 'HENC', 'MRZM', 'CPMV', 'HSDT', 'SILO', 'AXIM', 'NSTM', 'CNNC', 'CYCC', 'ENVB', 'GBLX', 'AGTX', 'TENX', 'NVIV', 'GRST', 'GSTC', 'WHSI', 'CBDS', 'NTRR', 'SIGY', 'INLB', 'HDVY', 'ARPC', 'ABMT', 'GRNF', 'ENDV', 'THCT', 'NLBS']
# missing div years:
# ['ALC', 'ALNY', 'RGEN', 'SGRY', 'SMMT', 'LIVN', 'LFST', 'LGND', 'CABA', 'MDRX', 'MPLN', 'OABI', 'AAGH', 'OVID', 'RENB', 'JSPR', 'RLMD', 'KRMD', 'CRVO', 'MIST', 'RZLT', 'NMTC', 'ETST', 'AURX', 'HSTI', 'IMTH', 'PETV', 'RXMD', 'CLRD', 'EDSA', 'RASP', 'BUDZ', 'CANN', 'ALID', 'HENC', 'MRZM', 'AIMD', 'CPMV', 'HSDT', 'SILO', 'AXIM', 'AVTX', 'NSTM', 'ENVB', 'GBLX', 'AGTX', 'TENX', 'GRST', 'WHSI', 'CBDS', 'NTRR', 'SIGY', 'INLB', 'HDVY', 'ARPC', 'GPFT', 'GRNF', 'ENDV', 'THCT', 'NLBS']
# missing roic years:
# ['ALC', 'MNKD', 'ESPR', 'RENB', 'QIPT', 'RLMD', 'CRDF', 'CRVO', 'RZLT', 'NMTC', 'ETST', 'ABIO', 'LEXX', 'IMTH', 'BCLI', 'RXMD', 'ADXS', 'BUDZ', 'HENC', 'MRZM', 'SILO', 'AXIM', 'NSTM', 'CYCC', 'ENVB', 'GBLX', 'NVIV', 'GRST', 'GSTC', 'CBDS', 'NTRR', 'SIGY', 'INLB', 'HDVY', 'ARPC', 'ABMT', 'GRNF', 'ENDV', 'THCT', 'NLBS']
# wrong income end year
# ['MDT', 'MCK', 'TAK', 'STE', 'RDY', 'IMGN', 'ROIV', 'GRFS', 'DOCS', 'IMVT', 'HAE', 'NEOG', 'PBH', 'EVO', 'PDCO', 'TARO', 'SUPN', 'PHVS', 'TLRY', 'ACCD', 'MDRX', 'CVAC', 'ICVX', 'PRTC', 'CALT', 'KALV', 'REPL', 'LIAN', 'CDMO', 'PROC', 'HARP', 'NBTX', 'CGC', 'NNOX', 'OPRX', 'ME', 'TLSI', 'ANGO', 'LFCR', 'LMDXF', 'CLLS', 'CDT', 'CORBF', 'BLUE', 'INFU', 'ACB', 'ELTP', 'THRX', 'AHG', 'CYDY', 'IMAB', 'CYBN', 'OCGN', 'ZTEK', 'VTGN', 'PETS', 'GTH', 'RVPH', 'YI', 'CYT', 'MDXH', 'GLSI', 'SY', 'LIFW', 'SHLT', 'ZJYL', 'BNR', 'CELU', 'CSBR', 'AFMD', 'FFNTF', 'TIHE', 'INCR', 'EGRX', 'XAIR', 'VICP', 'CDTX', 'PRE', 'CNTB', 'IPA', 'EAR', 'CUTR', 'ICU', 'TLSA', 'ENLV', 'CXXIF', 'PNPL', 'OKYO', 'BYSI', 'ESLA', 'DXR', 'PNXP', 'NYMXF', 'YS', 'EUDA', 'BIMI', 'YBGJ', 'NKGN', 'ONMD', 'SNCE', 'MOVE', 'CCM', 'BGXX', 'SRNEQ', 'MODD', 'UBX', 'CNTG', 'RLFTY', 'GDTC', 'ETST', 'ETAO', 'PHXM', 'OCX', 'AURX', 'MDNAF', 'MHUA', 'ACRHF', 'STRM', 'ACST', 'HSTI', 'ALRN', 'MYNZ', 'AIH', 'NTRB', 'OHCS', 'TRIB', 'SRZN', 'PMCB', 'PETV', 'OCEA', 'RXMD', 'IGC', 'NBIO', 'NLSP', 'OTLC', 'VBIV', 'RDHL', 'CLRD', 'ICCT', 'RMSL', 'BMRA', 'COSM', 'CHEK', 'NXGL', 'ADXS', 'NEXI', 'CRYM', 'ADXN', 'ALRTF', 'GBNH', 'NTBL', 'BCEL', 'MCUJF', 'AVCRF', 'ONVO', 'ORGS', 'EIGR', 'ZCMD', 'ASLN', 'BTTX', 'PFHO', 'FRES', 'CANN', 'NHIQ', 'EDXC', 'BETRF', 'HSCS', 'RADCQ', 'BSGM', 'SIEN', 'BTCY', 'APM', 'NSTG', 'PBIO', 'HEPA', 'CJJD', 'XWEL', 'ACBM', 'QLIS', 'ADTX', 'NVTA', 'HENC', 'ALZN', 'ABTI', 'ECIA', 'JRSS', 'ADMT', 'BTAX', 'XTLB', 'XCUR', 'EMMA', 'MDGS', 'MEDS', 'BPTS', 'XRTX', 'OTRK', 'MRZM', 'MDVL', 'CPMV', 'AEMD', 'AXIM', 'TSOI', 'CLSH', 'VFRM', 'RNVA', 'OPGN', 'BZYR', 'ONCO', 'BDRX', 'ARDS', 'STEK', 'OWPC', 'AVRW', 'FOXO', 'CWBR', 'CYTO', 'QRON', 'VYCO', 'WINT', 'NBSE', 'ELOX', 'NMRD', 'INQD', 'CNNC', 'QLGN', 'BACK', 'THMO', 'INVO', 'SNOA', 'LGMK', 'NAOV', 'AKAN', 'GBLX', 'SCNI', 'AGTX', 'VRAX', 'IONM', 'SEQL', 'IPCIF', 'NEPT', 'NVIV', 'GRST', 'KOAN', 'WORX', 'CSUI', 'DVLP', 'NREG', 'CBDS', 'BSPK', 'SXTC', 'CMRA', 'BXRX', 'PAXH', 'ATHXQ', 'HADV', 'CANB', 'MJNE', 'KAYS', 'NTRR', 'BLCM', 'PKBO', 'BLPH', 'INQR', 'RSPI', 'ENMI', 'SDCCQ', 'GMVDF', 'QTXB', 'EMED', 'SGBI', 'IMPLQ', 'TPIA', 'CSTF', 'BLMS', 'BBBT', 'MITI', 'VNTH', 'GLSHQ', 'MMNFF', 'RGMP', 'QBIO', 'ATRX', 'RGTPQ', 'ACUR', 'INLB', 'STAB', 'HDVY', 'RVLPQ', 'IVRN', 'PEARQ', 'RBSH', 'INFIQ', 'STMH', 'BIOCQ', 'ABMC', 'TMBRQ', 'HTGMQ', 'NOVNQ', 'USRM', 'ONCSQ', 'VRAYQ', 'HGENQ', 'PHASQ', 'BBLNF', 'GNRS', 'NMTRQ', 'ABCZF', 'SWGHF', 'BFFTF', 'RAIN', 'AKUMQ', 'BIOE', 'SIOX', 'XTXXF', 'SKYI', 'GBCS', 'FZMD', 'LNDZF', 'NHWK', 'PMEDF', 'TMDIF', 'INND', 'UTRS', 'CLYYF', 'IGEX', 'NAVB', 'CANQF', 'ABMT', 'REMI', 'ARAV', 'MCOA', 'DMK', 'GPFT', 'HSTO', 'GRNF', 'IGPK', 'IMUC', 'SQZB', 'GENN', 'SNNC', 'TOMDF', 'KGKG', 'EVLO', 'WCUI', 'ENDV', 'VIVE', 'MYMX', 'PHBI', 'CBGL', 'SCPS', 'CALA', 'CENBF', 'EVIO', 'CLCS', 'PHCG', 'NLBS', 'GRYN', 'EWLL', 'NPHC', 'CNNA', 'TAUG', 'CPMD', 'CMXC', 'NBRVF', 'SSTC', 'DHAI', 'MDNC']
# wrong div end year
# ['MDT', 'MCK', 'TAK', 'STE', 'RDY', 'IMGN', 'ROIV', 'GRFS', 'DOCS', 'IMVT', 'HAE', 'NEOG', 'PBH', 'EVO', 'PDCO', 'DYN', 'TARO', 'SUPN', 'TLRY', 'ACCD', 'GRCL', 'MDRX', 'CVAC', 'ICVX', 'CALT', 'KALV', 'REPL', 'LIAN', 'CDMO', 'PROC', 'HARP', 'NBTX', 'CGC', 'NNOX', 'OPRX', 'ME', 'ANGO', 'LFCR', 'LMDXF', 'CLLS', 'CDT', 'CORBF', 'BLUE', 'INFU', 'ACB', 'ELTP', 'THRX', 'AHG', 'CYDY', 'IMAB', 'CYBN', 'OCGN', 'ZTEK', 'VTGN', 'PETS', 'GTH', 'RVPH', 'YI', 'CYT', 'MDXH', 'GLSI', 'SY', 'LIFW', 'SHLT', 'ZJYL', 'VNRX', 'BNR', 'CELU', 'CSBR', 'AFMD', 'FFNTF', 'TIHE', 'INCR', 'EGRX', 'XAIR', 'VICP', 'CDTX', 'PRE', 'CNTB', 'IPA', 'EAR', 'CUTR', 'ICU', 'TLSA', 'VANI', 'ENLV', 'CXXIF', 'PNPL', 'OKYO', 'BYSI', 'ESLA', 'DXR', 'PNXP', 'NYMXF', 'YS', 'EUDA', 'BIMI', 'YBGJ', 'NKGN', 'SNCE', 'MOVE', 'CCM', 'BGXX', 'SRNEQ', 'MODD', 'UBX', 'CNTG', 'FRLN', 'RLFTY', 'ETST', 'ETAO', 'PHXM', 'OCX', 'AURX', 'MDNAF', 'MHUA', 'ACRHF', 'STRM', 'ACST', 'HSTI', 'ALRN', 'MYNZ', 'AIH', 'NTRB', 'LEXX', 'OHCS', 'TRIB', 'SRZN', 'PMCB', 'PETV', 'RXMD', 'IGC', 'NBIO', 'NLSP', 'OTLC', 'VBIV', 'RDHL', 'CLRD', 'EDSA', 'ICCT', 'RMSL', 'BMRA', 'COSM', 'PRTG', 'CHEK', 'NXGL', 'BMMJ', 'ADXS', 'NEXI', 'CRYM', 'ADXN', 'ALRTF', 'GBNH', 'NTBL', 'BCEL', 'MCUJF', 'AVCRF', 'ONVO', 'ORGS', 'NDRA', 'EIGR', 'ZCMD', 'ASLN', 'BTTX', 'PFHO', 'FRES', 'CANN', 'NHIQ', 'EDXC', 'BETRF', 'HSCS', 'RADCQ', 'BSGM', 'SIEN', 'BTCY', 'NSTG', 'PBIO', 'HEPA', 'CJJD', 'XWEL', 'ACBM', 'QLIS', 'ADTX', 'NVTA', 'HENC', 'ALZN', 'CELZ', 'ABTI', 'ECIA', 'JRSS', 'ADMT', 'BTAX', 'XTLB', 'XCUR', 'EMMA', 'MDGS', 'MEDS', 'BPTS', 'OTRK', 'MRZM', 'MDVL', 'CPMV', 'AEMD', 'AXIM', 'TSOI', 'CLSH', 'VFRM', 'RNVA', 'OPGN', 'BZYR', 'ONCO', 'BDRX', 'QNRX', 'ARDS', 'STEK', 'OWPC', 'VTAK', 'AVRW', 'FOXO', 'CWBR', 'CYTO', 'QRON', 'VYCO', 'WINT', 'NBSE', 'ELOX', 'NMRD', 'INQD', 'CNNC', 'QLGN', 'CYCC', 'BACK', 'THMO', 'INVO', 'SNOA', 'LGMK', 'NAOV', 'AKAN', 'GBLX', 'SCNI', 'AGTX', 'VRAX', 'IONM', 'SEQL', 'IPCIF', 'NEPT', 'NVIV', 'DRMA', 'GRST', 'KOAN', 'WORX', 'CSUI', 'DVLP', 'NREG', 'CBDS', 'BSPK', 'SXTC', 'CMRA', 'BXRX', 'PAXH', 'ATHXQ', 'HADV', 'CANB', 'MJNE', 'KAYS', 'NTRR', 'BLCM', 'PKBO', 'BLPH', 'INQR', 'RSPI', 'ENMI', 'SDCCQ', 'GMVDF', 'QTXB', 'EMED', 'SGBI', 'IMPLQ', 'TPIA', 'CSTF', 'BLMS', 'BBBT', 'MITI', 'VNTH', 'GLSHQ', 'MMNFF', 'RGMP', 'QBIO', 'ATRX', 'RGTPQ', 'ACUR', 'INLB', 'STAB', 'HDVY', 'RVLPQ', 'IVRN', 'PEARQ', 'RBSH', 'INFIQ', 'STMH', 'BIOCQ', 'ABMC', 'TMBRQ', 'HTGMQ', 'NOVNQ', 'USRM', 'ONCSQ', 'VRAYQ', 'HGENQ', 'PHASQ', 'BBLNF', 'GNRS', 'NMTRQ', 'ABCZF', 'SWGHF', 'BFFTF', 'RAIN', 'AKUMQ', 'BIOE', 'SIOX', 'XTXXF', 'SKYI', 'GBCS', 'FZMD', 'LNDZF', 'NHWK', 'PMEDF', 'TMDIF', 'INND', 'UTRS', 'CLYYF', 'IGEX', 'NAVB', 'CANQF', 'ABMT', 'REMI', 'ARAV', 'MCOA', 'DMK', 'GPFT', 'HSTO', 'GRNF', 'IGPK', 'IMUC', 'SQZB', 'GENN', 'SNNC', 'TOMDF', 'KGKG', 'EVLO', 'WCUI', 'ENDV', 'VIVE', 'MYMX', 'PHBI', 'CBGL', 'SCPS', 'CALA', 'CENBF', 'EVIO', 'CLCS', 'PHCG', 'NLBS', 'GRYN', 'EWLL', 'NPHC', 'TAUG', 'CPMD', 'CMXC', 'NBRVF', 'SSTC', 'AMJT', 'MDNC']
# wrong roic end year
# ['MDT', 'MCK', 'TAK', 'STE', 'RDY', 'IMGN', 'ROIV', 'GRFS', 'DOCS', 'IMVT', 'HAE', 'NEOG', 'PBH', 'EVO', 'PDCO', 'TARO', 'SUPN', 'TLRY', 'ACCD', 'GRCL', 'MDRX', 'CVAC', 'ICVX', 'CALT', 'KALV', 'REPL', 'LIAN', 'CDMO', 'PROC', 'HARP', 'CGC', 'NNOX', 'OPRX', 'ME', 'ANGO', 'LFCR', 'LMDXF', 'CLLS', 'CDT', 'CORBF', 'BLUE', 'INFU', 'ACB', 'ELTP', 'THRX', 'AHG', 'CYDY', 'IMAB', 'OCGN', 'ZTEK', 'VTGN', 'PETS', 'GTH', 'RVPH', 'YI', 'CYT', 'MDXH', 'GLSI', 'SY', 'LIFW', 'SHLT', 'ZJYL', 'BNR', 'CELU', 'CSBR', 'AFMD', 'FFNTF', 'TIHE', 'INCR', 'EGRX', 'XAIR', 'VICP', 'CDTX', 'PRE', 'CNTB', 'IPA', 'EAR', 'CUTR', 'ICU', 'TLSA', 'ENLV', 'CXXIF', 'PNPL', 'OKYO', 'BYSI', 'ESLA', 'DXR', 'PNXP', 'NYMXF', 'YS', 'EUDA', 'BIMI', 'YBGJ', 'NKGN', 'SNCE', 'MOVE', 'CCM', 'BGXX', 'SRNEQ', 'MODD', 'UBX', 'CNTG', 'FRLN', 'RLFTY', 'ETST', 'ETAO', 'PHXM', 'OCX', 'AURX', 'MDNAF', 'MHUA', 'ACRHF', 'STRM', 'ACST', 'HSTI', 'ALRN', 'MYNZ', 'AIH', 'NTRB', 'OHCS', 'TRIB', 'SRZN', 'PMCB', 'PETV', 'RXMD', 'IGC', 'NBIO', 'NLSP', 'OTLC', 'VBIV', 'RDHL', 'CLRD', 'ICCT', 'RMSL', 'BMRA', 'COSM', 'CHEK', 'NXGL', 'ADXS', 'NEXI', 'CRYM', 'ADXN', 'ALRTF', 'GBNH', 'NTBL', 'BCEL', 'MCUJF', 'AVCRF', 'ONVO', 'ORGS', 'EIGR', 'ZCMD', 'ASLN', 'BTTX', 'PFHO', 'FRES', 'CANN', 'NHIQ', 'EDXC', 'BETRF', 'HSCS', 'RADCQ', 'BSGM', 'SIEN', 'BTCY', 'APM', 'NSTG', 'PBIO', 'HEPA', 'CJJD', 'XWEL', 'ACBM', 'QLIS', 'ADTX', 'NVTA', 'HENC', 'ALZN', 'ABTI', 'ECIA', 'JRSS', 'ADMT', 'BTAX', 'XCUR', 'EMMA', 'MDGS', 'MEDS', 'OTRK', 'MRZM', 'MDVL', 'CPMV', 'AEMD', 'AXIM', 'TSOI', 'CLSH', 'VFRM', 'RNVA', 'OPGN', 'BZYR', 'ONCO', 'BDRX', 'ARDS', 'STEK', 'OWPC', 'AVRW', 'FOXO', 'CWBR', 'CYTO', 'QRON', 'VYCO', 'WINT', 'NBSE', 'ELOX', 'NMRD', 'INQD', 'CNNC', 'QLGN', 'BACK', 'THMO', 'INVO', 'SNOA', 'LGMK', 'NAOV', 'AKAN', 'GBLX', 'SCNI', 'AGTX', 'VRAX', 'IONM', 'SEQL', 'IPCIF', 'NEPT', 'NVIV', 'GRST', 'KOAN', 'WORX', 'CSUI', 'DVLP', 'NREG', 'CBDS', 'BSPK', 'SXTC', 'CMRA', 'BXRX', 'PAXH', 'ATHXQ', 'HADV', 'CANB', 'MJNE', 'KAYS', 'NTRR', 'BLCM', 'PKBO', 'BLPH', 'INQR', 'RSPI', 'ENMI', 'SDCCQ', 'GMVDF', 'QTXB', 'EMED', 'SGBI', 'IMPLQ', 'TPIA', 'CSTF', 'BLMS', 'BBBT', 'MITI', 'VNTH', 'GLSHQ', 'MMNFF', 'RGMP', 'QBIO', 'ATRX', 'RGTPQ', 'ACUR', 'INLB', 'STAB', 'HDVY', 'RVLPQ', 'IVRN', 'PEARQ', 'RBSH', 'INFIQ', 'STMH', 'BIOCQ', 'ABMC', 'TMBRQ', 'HTGMQ', 'NOVNQ', 'USRM', 'ONCSQ', 'VRAYQ', 'HGENQ', 'PHASQ', 'BBLNF', 'GNRS', 'NMTRQ', 'ABCZF', 'SWGHF', 'BFFTF', 'RAIN', 'AKUMQ', 'BIOE', 'SIOX', 'XTXXF', 'SKYI', 'GBCS', 'FZMD', 'LNDZF', 'NHWK', 'PMEDF', 'TMDIF', 'INND', 'UTRS', 'CLYYF', 'IGEX', 'NAVB', 'CANQF', 'ABMT', 'REMI', 'ARAV', 'MCOA', 'DMK', 'GPFT', 'HSTO', 'GRNF', 'IGPK', 'IMUC', 'SQZB', 'GENN', 'SNNC', 'TOMDF', 'KGKG', 'EVLO', 'WCUI', 'ENDV', 'VIVE', 'MYMX', 'PHBI', 'CBGL', 'SCPS', 'CALA', 'CENBF', 'EVIO', 'CLCS', 'PHCG', 'NLBS', 'GRYN', 'EWLL', 'NPHC', 'TAUG', 'CPMD', 'CMXC', 'NBRVF', 'SSTC', 'MDNC']
###

###NEW Finance
# finrecaplist = ['V', 'IBN', 'ANZGY', 'NU', 'ARES', 'BSBR', 'CM',]
#                ### 'PPERY', 'CRARY', 'BDORY', 'GWLIF', 'ERIE', 'SMPNY', 'PTBRY', 'RYAN', 'JBAXY', 'DSEEY', 'ASXFY', 'EGFEY', 'CBSH', 'CRCBY', 'HLNE', 'PDI', 'OZK', 'CADE', 'THG', 'ACT', 'AB', 'PJT', 'MC', 'AMTD', 'NEA', 'DNP', 'NAD', 'NVG', 'CSQ', 'EXG', 'ADX', 'NZF', 'UTF', 'PTY', 'ETY', 'UTG', 'GDV', 'NUV', 'BIGZ', 'USA', 'GOF', 'DWAC', 'BBUC', 'NWLI', 'EVT', 'CLM', 'RVT', 'RQI', 'NAC', 'GAB', 'TY', 'BTT', 'ETV', 'BDJ', 'KYN', 'STEW', 'BSTZ', 'HYT', 'BXMX', 'ETG', 'DSL', 'BST', 'OXLC', 'NFJ', 'EVV', 'QQQX', 'JFR', 'FSCO', 'NMZ', 'CET', 'GAM', 'MUC', 'FPF', 'PTA', 'BBN', 'EOS', 'BTZ', 'SCRM', 'CVII', 'RNP', 'PFBC', 'NRK', 'SII', 'CHY', 'AWF', 'MQY', 'ETW', 'CII', 'MUI', 'HQH', 'AOD', 'CHI', 'THQ', 'CRF', 'ECC', 'MYI', 'NOAH', 'JPC', 'PHK', 'EIM', 'BCX', 'JQC', 'RA', 'EOI', 'IGR', 'GHIX', 'NXP', 'FFC', 'HTD', 'PCN', 'FAX', 'HUT', 'AACT', 'PAXS', 'VMO', 'VVR', 'PFN', 'BOE', 'MHD', 'MUJ', 'NIE', 'BME', 'IFN', 'BHK', 'BIT', 'GGN', 'PML', 'CCD', 'IIM', 'MMU', 'BTO', 'ETJ', 'STK', 'NKX', 'EMD', 'BGY', 'CEM', 'VGM', 'PDT', 'SAGA', 'DIAX', 'VKQ', 'DSU', 'WIW', 'PEO', 'BGB', 'BLE', 'IQI', 'NXJ', 'MYD', 'BLW', 'THW', 'DGICA', 'GHY', 'HPS', 'BUI', 'NBB', 'VCV', 'MMD', 'ALCC', 'HFRO', 'BFK', 'MVF', 'FRA', 'EMO', 'RMT', 'NQP', 'SLAM', 'HPI', 'ISD', 'JPI', 'MUA', 'NPFD', 'AVK', 'GUT', 'EVN', 'IGD', 'ETO', 'EAD', 'NETD', 'MYN', 'GBAB', 'CHW', 'ETB', 'FSD', 'FEI', 'EFR', 'VKI', 'GHI', 'HIO', 'MCI', 'DFP', 'LEO', 'HQL', 'FFA', 'NML', 'PPT', 'BFZ', 'RRAC', 'KTF', 'ACP', 'KIO', 'ANSC', 'EFT', 'HPF', 'PMO', 'BGR', 'NAN', 'SVII', 'SOR', 'DPG', 'MIY', 'PFL', 'IPXX', 'MHN', 'TYG', 'FOF', 'AWP', 'JRI', 'MIN', 'RFI', 'BRW', 'ASG', 'ARDC', 'AFB', 'IVCB', 'EDD', 'HYAC', 'NBH', 'HIX', 'JWSM', 'RMM', 'NCV', 'NPCT', 'OIA', 'BYM', 'NCA', 'JGH', 'SKGR', 'PMM', 'DSM', 'BGH', 'RCS', 'BGT', 'TWN', 'ASA', 'MXF', 'SPXX', 'FEN', 'HYI', 'CAF', 'MCR', 'PRLH', 'ERC', 'EOT', 'MMT', 'EMLD', 'DBL', 'LCAA', 'FCT', 'BNY', 'FTF', 'BKT', 'TDF', 'PLAO', 'CTR', 'PMX', 'AEF', 'RIV', 'FIF', 'PMF', 'TEI', 'NUW', 'SCD', 'VPV', 'APTM', 'RLTY', 'ACV', 'PSF', 'AGD', 'EVM', 'MQT', 'IIF', 'FUND', 'TSI', 'MVT', 'CNDA', 'NCZ', 'USCB', 'CONX', 'MUE', 'JCE', 'JRS', 'PHT', 'JOF', 'SABA', 'MFM', 'SBXC', 'AFT', 'NHS', 'GLO', 'PHYT', 'CFFS', 'AIF', 'VTN', 'DHY', 'BKN', 'LGI', 'NFYS', 'MHI', 'SEDA', 'MCAA', 'NPV', 'HIE', 'OPP', 'MNTN', 'ETX', 'EOD', 'MAV', 'WIA', 'DMB', 'GDO', 'PCK', 'PEGR', 'IGI', 'NTG', 'VBF', 'IVCA', 'PCQ', 'ENX', 'TRIS', 'BSL', 'EMF', 'APCA', 'INSI', 'HYB', 'DHF', 'PZC', 'GAQ', 'MPV', 'LCW', 'EHI', 'BRKH', 'FT', 'GRX', 'PIM', 'HCMA', 'CIK', 'CBH', 'NRO', 'NNY', 'ALCY', 'FPL', 'EIC', 'MPA', 'HHLA', 'FLC', 'TEAF', 'BGX', 'IDE', 'ESHA', 'ROSS', 'BFAC', 'GGT', 'IFIN', 'NSTD', 'KRNL', 'MCN', 'BMN', 'NSTC', 'BCSA', 'TLGY', 'EVG', 'MSD', 'AVBH', 'FLME', 'GF', 'MHF', 'LCA', 'WNNR', 'VCXB', 'BWG', 'BTA', 'DMF', 'ISRL', 'LYBC', 'IRRX', 'SPE', 'EDF', 'CNDB', 'IGA', 'NNAG', 'VMCA', 'BANX', 'DHCA', 'WEA', 'DMO', 'PFD', 'ACAH', 'ZLS', 'JHS', 'FMN', 'OAKC', 'HEQ', 'NAZ', 'GATE', 'VFL', 'DSAQ', 'NPAB', 'KCGI', 'PLMI', 'EVGR', 'NSTB', 'PPYA', 'PHD', 'GLQ', 'CPTK', 'BOCN', 'IXAQ', 'JHI', 'PAI', 'TCOA', 'PCF', 'ARRW', 'PGSS', 'CXE', 'NIM', 'TOP', 'CDAQ', 'KF', 'OCCI', 'IAF', 'COOL', 'SBI', 'CITE', 'TGAA', 'CHAA', 'ECF', 'CBRG', 'DPCS', 'PFO', 'EVF', 'MCAC', 'PORT', 'BMBN', 'MITA', 'MDBH', 'MGF', 'SWZ', 'SPKL', 'FNVT', 'GGZ', 'PCM', 'NMT', 'CNGL', 'GAMC', 'PWUP', 'LATG', 'GDL', 'KSM', 'QDRO', 'CGO', 'CCIF', 'IHD', 'CHN', 'NMI', 'HNW', 'OSI', 'WEL', 'PFX', 'JLS', 'GLAC', 'NXG', 'BLEU', 'ALTU', 'BCV', 'EAC', 'AACI', 'ARYD', 'VGI', 'WRAC', 'TMTC', 'USCT', 'IVCP', 'SRBK', 'GLST', 'XFIN', 'PNI', 'NXC', 'PGP', 'CMU', 'FICV', 'TPZ', 'RCAC', 'JEQ', 'ERH', 'BACA', 'GNT', 'AEAE', 'OAKU', 'LIBY', 'GLU', 'ASCB', 'RFAC', 'GGAAF', 'DTF', 'IRAA', 'SRV', 'CEV', 'INAQ', 'SWIN', 'FEXD', 'TRON', 'TETE', 'BWAQ', 'UNIB', 'FORL', 'GCV', 'APAC', 'DWNX', 'FCO', 'GLV', 'VLT', 'QFTA', 'PGZ', 'MAQC', 'IAE', 'KYCH', 'DMA', 'RGT', 'NMS', 'PNF', 'FAM', 'MFD', 'AFAR', 'CXH', 'REDW', 'CEE', 'ACAC', 'PTWO', 'ASCA', 'HAIA', 'EEA', 'TTP', 'JMM', 'HTY', 'PEPL', 'KSBI', 'CLRC', 'VSAC', 'FGB', 'FMY', 'MXE', 'AQU', 'WTMA', 'NDP', 'NXN', 'INTE', 'KWAC', 'CUBA', 'TGVC', 'PFTA', 'CPBI', 'TURN', 'WBQNL', 'EGF', 'GRF', 'PYN', 'INFT', 'DECA', 'CIF', 'PBAX', 'OAKV', 'MFV', 'PPHP', 'BTM', 'CWD', 'NOM', 'OGGIF', 'EQS', 'BHV', 'RBNK', 'MSBB', 'FRCB', 'RCG', 'FXBY', 'CDSG', 'TDCB', 'BMNM', 'DEFG', 'SIPN', 'SFIO', 'LGCP', 'GSBX', 'GEGP', 'BNCM', 'DXF', 'TLIF', 'KEGS', 'AMLH', 'GMZP', 'RINO', 'CBBB', 'BISA', 'SCGX', 'SMCE', 'VTXB', 'SFCO', 'BNPQF', 'ATH-PA', 'DEFTF', 'OFSTF', 'CMHF', 'TETAA', 'CBTC', 'GYGC', 'AERS', 'FAVO', 'AQUI', 'FIGP']
# finmissingincomerevenue = ['GS', 'TFC', 'BSBR', 'DFS', 'RKT', 'FCNCA', 'SYF', 'BAM', 'ARCC', 'CBSH', 'PNFP', 'SSB', 'PB', 'OBDC', 'FSK', 'BOKF', 'OMF', 'BXSL', 'HOMB', 
#                             'FNB', 'FFIN', 'SLM', 'VLY', 'UMBF', 'MAIN', 'AB', 'TFSL', 'MC', 'HWC', 'SFBS', 'IBOC', 'ABCB', 'BANF', 'FIBK', 'GBDC', 'HTGC', 'AUB', 'BOH', 
#                             'PSEC', 'CVBF', 'CBU', 'PPBI', 'INDB', 'SFNC', 'PRK', 'FFBC', 'SBCF', 'FRME', 'AGM', 'TSLX',]
                            ### 'IBTX', 'CLBK', 'TFIN', 'DWAC', 'RNST', 'MBIN', 
                            # 'WSBC', 'FBK', 'LOB', 'GSBD', 'TRMK', 'OCSL', 'BANR', 'FNMA', 'NWBI', 'EFSC', 'FCF', 'STEL', 'NMFC', 'HOPE', 'BUSE', 'SRCE', 'STBA', 'WABC', 
                            # 'NIC', 'VBTX', 'SASR', 'SCRM', 'CVII', 'BCSF', 'BBDC', 'GABC', 'OCFC', 'OBK', 'PBAJ', 'SBSI', 'BY', 'MFIC', 'GHLD', 'BRKL', 'BFC', 'LDI', 'SLRC', 
                            # 'CNOB', 'CGBD', 'FBMS', 'AMTB', 'AMAL', 'FMCB', 'FMBH', 'CTBI', 'PFC', 'GHIX', 'FMCC', 'EGBN', 'PFLT', 'AACT', 'TRIN', 'TCPC', 'HFWA', 'FCBC', 
                            # 'HBT', 'OSBC', 'MBWM', 'HBIA', 'NBBK', 'CION', 'CCAP', 'GSBC', 'MCBS', 'RWAY', 'HBNC', 'FDUS', 'SAGA', 'TRST', 'MSBI', 'VEL', 'CATC', 'FMNB', 
                            # 'CCB', 'EQBK', 'GAIN', 'CCBG', 'HONE', 'AMNB', 'LBC', 'SMBC', 'ALCC', 'HAFC', 'THFF', 'ALRS', 'PNNT', 'HRZN', 'SLAM', 'GLAD', 'CCNE', 'SPFI', 
                            # 'BHRB', 'AROW', 'BETR', 'FSBC', 'NETD', 'TPVG', 'ESQ', 'HCVI', 'MOFG', 'SMBK', 'OPFI', 'RRAC', 'RRBI', 'ANSC', 'MPB', 'MCBC', 'GNTY', 'SVII', 
                            # 'EBTC', 'BWB', 'IPXX', 'RENE', 'SAR', 'ACNB', 'SCM', 'IVCB', 'HYAC', 'JWSM', 'FRST', 'HBCP', 'WTBA', 'SKGR', 'WHF', 'FISI', 'CZNC', 'CBNK', 'FBIZ', 
                            # 'BCAL', 'PFIS', 'FMAO', 'BMRC', 'TRTL', 'BSRR', 'NEWT', 'BKCC', 'UNTY', 'PRLH', 'FDBC', 'EMLD', 'FNLC', 'LCAA', 'TCBX', 'LNKB', 'WSBF', 'BSVN', 
                            # 'PLAO', 'JMSB', 'OBT', 'APTM', 'MFIN', 'BCML', 'CNDA', 'USCB', 'NECB', 'CONX', 'BLFY', 'TSBK', 'PDLB', 'CVLY', 'SBXC', 'CHMG', 'PHYT', 'CFFS', 
                            # 'OVLY', 'PKBK', 'CVCY', 'CBAN', 'NFYS', 'KVAC', 'BPRN', 'SEDA', 'CALB', 'MBCN', 'COFS', 'MCAA', 'MNTN', 'XPDB', 'PEGR', 'IVCA', 'ESSA', 'TRIS', 
                            # 'OXSQ', 'PTMN', 'APCA', 'BCBP', 'PVBC', 'VAQC', 'HWBK', 'EVE', 'ISTR', 'GAQ', 'CFNB', 'LCW', 'BRKH', 'ATLO', 'HCMA', 'VABK', 'MRCC', 'HHLA', 'OFS', 
                            # 'ESHA', 'ROSS', 'BFAC', 'IFIN', 'NSTD', 'KRNL', 'PEBK', 'TWLV', 'NSTC', 'BCSA', 'BVFL', 'CNF', 'TLGY', 'FLME', 'LCA', 'WNNR', 'VCXB', 'FGBI', 'CFBK', 
                            # 'FLFV', 'ALSA', 'ISRL', 'IRRX', 'CNDB', 'ATEK', 'FINW', 'NNAG', 'VMCA', 'DHCA', 'HNVR', 'UNB', 'ACAH', 'ZLS', 'FNRN', 'RMGC', 'FRAF', 'FIAC', 'GATE', 
                            # 'DSAQ', 'NPAB', 'OVBC', 'KCGI', 'PLMI', 'EVGR', 'NSTB', 'CCFN', 'CZWI', 'PPYA', 'ECBK', 'CPTK', 'BOCN', 'RCFA', 'IXAQ', 'RMBI', 'TCOA', 'ARRW', 'PGSS', 
                            # 'BYNO', 'APXI', 'EMYB', 'CDAQ', 'WMPN', 'SHAP', 'TWOA', 'CMCA', 'COOL', 'CITE', 'TGAA', 'CHAA', 'CBRG', 'LARK', 'AFBI', 'BSBK', 'DPCS', 'SLAC', 'BLUA', 
                            # 'MCAC', 'PORT', 'SBFG', 'MITA', 'MDBH', 'CSLM', 'GPAC', 'SZZL', 'RVSB', 'EBMT', 'THCP', 'SPKL', 'FNWD', 'FNVT', 'LVPA', 'CSBB', 'FTII', 'SFBC', 'ATMV', 
                            # 'PROV', 'MARX', 'CNGL', 'GAMC', 'TENK', 'PWUP', 'LATG', 'HMNF', 'PMGM', 'QDRO', 'BOWN', 'FKYS', 'BLAC', 'RWOD', 'TBMC', 'ESAC', 'GODN', 'CMTV', 'HSPO', 
                            # 'OSI', 'WEL', 'PFX', 'QNBC', 'SSSS', 'BITE', 'FOTB', 'BLEU', 'ALTU', 'EMCG', 'PSBQ', 'EAC', 'GLLI', 'AACI', 'ARYD', 'WRAC', 'ONYX', 'NRAC', 'ENBP', 
                            # 'USCT', 'IVCP', 'ACAB', 'SRBK', 'GLST', 'XFIN', 'IMAQ', 'BHAC', 'DUET', 'FICV', 'OCAX', 'RCAC', 'AITR', 'SFDL', 'GDST', 'BACA', 'PUCK', 'BUJA', 'AEAE', 
                            # 'LIBY', 'CETU', 'ASCB', 'GECC', 'MGYR', 'CULL', 'GBBK', 'RFAC', 'GTAC', 'FHLT', 'GGAAF', 'VHAQ', 'IRAA', 'INAQ', 'FEXD', 'FRLA', 'ATMC', 'TRON', 'PMHG', 
                            # 'PFBX', 'SWSS', 'TETE', 'BWAQ', 'FORL', 'PBHC', 'MSSA', 'APAC', 'GMFI', 'NVAC', 'UBCP', 'DIST', 'LGST', 'QFTA', 'MAQC', 'DMYY', 'CLOE', 'KYCH', 'PMVC', 
                            # 'FMBM', 'ROCL', 'AFAR', 'NBST', 'SLBK', 'SEPA', 'ENCP', 'TCBC', 'JUVF', 'IGTA', 'ACAC', 'PTWO', 'LRFC', 'ASCA', 'BNIX', 'HAIA', 'MBTC', 'SUND', 'ARIZ', 
                            # 'IROQ', 'CLST', 'CHEA', 'CCTS', 'HHGC', 'PEPL', 'RACY', 'PLTN', 'BRAC', 'UWHR', 'BAFN', 'CLRC', 'KACL', 'VSAC', 'ICMB', 'AQU', 'BREZ', 'WTMA', 'CFSB', 
                            # 'BCOW', 'HUDA', 'AOGO', 'WINV', 'TCBS', 'INTE', 'KWAC', 'MCAF', 'FSEA', 'AIB', 'ADOC', 'MACA', 'YOTA', 'TGVC', 'NOVV', 'PFTA', 'DHAC', 'ACBA', 'LBBB', 
                            # 'QOMO', 'BCTF', 'WAVS', 'ADRT', 'RAND', 'MCAG', 'AVHI', 'DECA', 'VWFB', 'PBAX', 'OPHC', 'QNTO', 'WRPT', 'PPHP', 'BTM', 'GNRV', 'YTFD', 'RMCO', 'GLBZ', 
                            # 'MDWK', 'PNBK', 'PFSB', 'PMIN', 'FMFG', 'MSBB', 'GOVB', 'HNRA', 'SLTN', 'WNFT', 'PCMC', 'DHCC', 'WLYW', 'OOGI', 'GPLL', 'BEGI', 'ATYG', 'VCOR', 'HGYN', 
                            # 'VHLD', 'BZRD', 'WWSG', 'IROH', 'BDVC', 'FSUN', 'WBHC', 'RVRF', 'BKSC', 'ODTC', 'OFED', 'FFBW', 'CIZN', 'MBBC', 'TBBA', 'WVFC', 'ERKH', 'SICP', 'SVVC', 'SHGI', 'RBRXF', 'MSCF']
# finmissingincomenetIncome = ['PFX']
# finmissingincomeopCF =  ['ATMV', 'ATMC']
# finmissingincomecapEx =  ['JPM', 'BAC', 'WFC', 'MS', 'RY', 'TD', 'CB', 'UBS', 'USB', 'APO', 'PNC', 'BNS', 'MET', 'TRV', 'NU', 'AFL', 'CM', 'MFC', 'IBKR', 'PRU', 'IX', 'PFG', 'RF', 'TPG', 'SYF', 'BAM', 'EG', 'CRBG', 'RNR', 'ARCC', 'EQH', 'ALLY', 'AFG', 'ORI', 'CMA', 'WAL', 'FG', 'OBDC', 'FSK', 'OMF', 'BXSL', 'AXS', 'AGO', 'LNC', 'SLM', 'ESGR', 'ACT', 'JXN', 'WTM', 'MAIN', 'AB', 'BHF', 'ASB', 'CNO', 'LU', 'GNW', 'FIBK', 'GBDC', 'FULT', 'AUB', 'EBC', 'PSEC', 'SBCF', 'FRME', 'SPNT', 'AGM', 'TSLX', 'NAVI', 'DWAC', 'CCYC', 'GSBD', 'OCSL', 'AHL-PC', 'FNMA', 'HMN', 'NMFC', 'BRDG', 'BBAR', 'SCRM', 'CVII', 'BCSF', 'BBDC', 'PBAJ', 'BSIG', 'MFIC', 'HG', 'SLRC', 'CGBD', 'AMBC', 'AC', 'GHIX', 'FMCC', 'PFLT', 'AACT', 'TRIN', 'TCPC', 'PVNC', 'MBWM', 'CION', 'CCAP', 'RWAY', 'UFCS', 'FDUS', 'SAGA', 'GAIN', 'ALCC', 'PNNT', 'HRZN', 'SLAM', 'GLAD', 'BETR', 'GBLI', 'NETD', 'TPVG', 'HCVI', 'NOTR', 'RRAC', 'ANSC', 'SUPV', 'SVII', 'IPXX', 'RENE', 'SAR', 'SCM', 'IVCB', 'HYAC', 'JWSM', 'SKGR', 'WHF', 'TRTL', 'BKCC', 'PRLH', 'EMLD', 'LCAA', 'PLAO', 'APTM', 'MFIN', 'CNDA', 'CONX', 'SBXC', 'PHYT', 'CFFS', 'NFYS', 'KVAC', 'SEDA', 'MCAA', 'MNTN', 'XPDB', 'PEGR', 'IVCA', 'TRIS', 'OXSQ', 'PTMN', 'APCA', 'VAQC', 'EVE', 'VERY', 'GAQ', 'CFNB', 'LCW', 'BRKH', 'HCMA', 'SVMB', 'MRCC', 'HHLA', 'OFS', 'ESHA', 'ROSS', 'BFAC', 'IFIN', 'NSTD', 'KRNL', 'TWLV', 'NSTC', 'BCSA', 'TLGY', 'FLME', 'LCA', 'WNNR', 'VCXB', 'FLFV', 'ALSA', 'ISRL', 'IRRX', 'LGVC', 'CNDB', 'ATEK', 'NNAG', 'VMCA', 'DHCA', 'ACAH', 'ZLS', 'LGYV', 'RMGC', 'FIAC', 'GATE', 'DSAQ', 'NPAB', 'KCGI', 'PLMI', 'EVGR', 'NSTB', 'PPYA', 'CPTK', 'BOCN', 'RCFA', 'IXAQ', 'TCOA', 'ARRW', 'PGSS', 'BYNO', 'APXI', 'CDAQ', 'SHAP', 'TWOA', 'CMCA', 'COOL', 'CITE', 'TGAA', 'CHAA', 'CBRG', 'DPCS', 'SLAC', 'BLUA', 'MCAC', 'PORT', 'MITA', 'CSLM', 'GPAC', 'SZZL', 'THCP', 'SPKL', 'FNVT', 'LVPA', 'FTII', 'ATMV', 'MARX', 'CNGL', 'GAMC', 'TENK', 'PWUP', 'LATG', 'PMGM', 'QDRO', 'BOWN', 'BLAC', 'BFGX', 'GIA', 'RWOD', 'NPFC', 'TBMC', 'ESAC', 'GODN', 'HSPO', 'OSI', 'WEL', 'PFX', 'QNBC', 'SSSS', 'BITE', 'FOTB', 'BLEU', 'ALTU', 'EMCG', 'EAC', 'GLLI', 'AACI', 'ARYD', 'WRAC', 'ONYX', 'NRAC', 'USCT', 'IVCP', 'ACAB', 'GLST', 'XFIN', 'IMAQ', 'BHAC', 'DUET', 'FICV', 'OCAX', 'RCAC', 'AITR', 'GDST', 'BACA', 'PUCK', 'BUJA', 'AVNI', 'AEAE', 'LIBY', 'TGLO', 'CETU', 'ASCB', 'GECC', 'GBBK', 'RFAC', 'GTAC', 'FHLT', 'GGAAF', 'VHAQ', 'IRAA', 'INAQ', 'FEXD', 'FRLA', 'ATMC', 'TRON', 'SWSS', 'TETE', 'BWAQ', 'FORL', 'MSSA', 'APAC', 'GMFI', 'NVAC', 'DIST', 'LGST', 'QFTA', 'MAQC', 'DMYY', 'CLOE', 'KYCH', 'PMVC', 'ROCL', 'AFAR', 'NBST', 'SDIG', 'SEPA', 'ENCP', 'JUVF', 'IGTA', 'ACAC', 'PTWO', 'LRFC', 'ASCA', 'BNIX', 'HAIA', 'MBTC', 'SUND', 'ARIZ', 'CHEA', 'CCTS', 'HHGC', 'PEPL', 'RACY', 'PLTN', 'BRAC', 'CLRC', 'KACL', 'ASRV', 'VSAC', 'ICMB', 'AQU', 'MATH', 'OWVI', 'BREZ', 'WTMA', 'BCOW', 'HUDA', 'AOGO', 'WINV', 'INTE', 'KWAC', 'MCAF', 'AIB', 'ADOC', 'MACA', 'YOTA', 'TGVC', 'NOVV', 'PFTA', 'DHAC', 'ACBA', 'LBBB', 'MGLD', 'QOMO', 'WAVS', 'ADRT', 'RAND', 'ABTS', 'MCAG', 'AVHI', 'DECA', 'GREE', 'PBAX', 'WRPT', 'PPHP', 'BTM', 'PIAC', 'ILUS', 'CAHO', 'WNLV', 'LOGQ', 'YTFD', 'XITO', 'RMCO', 'MDWK', 'MEGL', 'MCVT', 'NFTN', 'TGGI', 'PWM', 'HNRA', 'SLTN', 'BWMY', 'FDCT', 'WNFT', 'PCMC', 'DHCC', 'WLYW', 'OOGI', 'NLSC', 'ECGR', 'SITS', 'LGHL', 'WHLT', 'ALDA', 'LSMG', 'NCPL', 'STQN', 'FSTJ', 'GPLL', 'BEGI', 'GMPW', 'ATYG', 'CLOW', 'YBCN', 'FCIC', 'KATX', 'RDGA', 'VCOR', 'BFYW', 'EMAX', 'BOTH', 'VHLD', 'CONC', 'BZRD', 'WWSG', 'NIMU', 'SDON', 'MMMM', 'PARG', 'MUSS', 'IROH', 'ATH-PA', 'TKCM', 'BDVC', 'GAMI', 'FIGI', 'BQST', 'BLYQ', 'SVVC', 'PUGE', 'SHGI', 'APSI', 'RBRXF', 'BABL', 'EXCL', 'MSCF', 'SSRT']        
# finmissingincomenetCF = ['HYAC', 'LVPA', 'BFGX', 'ATMC', 'OOGI', 'AASP', 'ATYG', 'HGYN', 'PMPG']
# finmissingincomedepreNAmor = ['JPM', 'BX', 'AXP', 'HSBC', 'RY', 'PGR', 'TD', 'C', 'CB', 'UBS', 'SMFG', 'ITUB', 'BMO', 'BN', 'USB', 'SAN', 'BBVA', 'BNS', 'AJG', 'MET', 'AIG', 'TFC', 'NU', 'ING', 'ALL', 'ARES', 'BSBR', 'BK', 'CM', 'MFC', 'IBKR', 'LYG', 'ACGL', 'SLF', 'PUK', 'BCS', 'DB', 'TROW', 'NWG', 'OWL', 'FRFHF', 'FITB', 'BRO', 'STT', 'KB', 'MKL', 'CINF', 'SHG', 'RF', 'NTRS', 'BAM', 'EG', 'CRBG', 'CFG', 'XP', 'BAP', 'RNR', 'GL', 'ARCC', 'BCH', 'RYAN', 'ALLY', 'AEG', 'AFG', 'AIZ', 'SEIC', 'BSAC', 'WF', 'CIB', 'ORI', 'SF', 'CACC', 'CBSH', 'RLI', 'SIGI', 'OBDC', 'FSK', 'FCFS', 'BXSL', 'MTG', 'AXS', 'BMA', 'AGO', 'UBSI', 'BNRE', 'LNC', 'FFIN', 'SLM', 'ACT', 'GBCI', 'JXN', 'MAIN', 'KMPR', 'AB', 'AMTD', 'BHF', 'IBOC', 'UCBI', 'AVAL', 'NYCB', 'LU', 'IFS', 'GNW', 'GGAL', 'GBDC', 'WSFS', 'AUB', 'PSEC', 'INTR', 'MCY', 'PAX', 'SBCF', 'SPNT', 'AGM', 'TSLX', 'NAVI', 'IBTX', 'WAFD', 'TFIN', 'DWAC', 'BBUC', 'CCYC', 'OFG', 'GSBD', 'TRMK', 'CUBI', 'OCSL', 'BRP', 'FNMA', 'FIHL', 'PUYI', 'CHCO', 'FBNC', 'NTB', 'FCF', 'CASH', 'NMFC', 'NBHC', 'SKWD', 'JMKJ', 'TCBK', 'NIC', 'PX', 'BBAR', 'SCRM', 'PEBO', 'CVII', 'BCSF', 'QCRH', 'AMSF', 'BBDC', 'SII', 'OBK', 'PBAJ', 'BY', 'MFIC', 'BLX', 'HG', 'SLRC', 'BITF', 'CGBD', 'WRLD', 'FMBH', 'AMBC', 'GHIX', 'FMCC', 'ABIT', 'PFLT', 'AACT', 'CFB', 'TRIN', 'BETS', 'TCPC', 'HFWA', 'PVNC', 'IGIC', 'MBWM', 'HBIA', 'CION', 'CCAP', 'GSBC', 'VINP', 'UVSP', 'MCBS', 'RWAY', 'FDUS', 'SAGA', 'TRST', 'GAIN', 'CCBG', 'AMNB', 'SMBC', 'ALCC', 'DHIL', 'GCBC', 'PNNT', 'QDMI', 'HRZN', 'SLAM', 'GLAD', 'PGC', 'KRNY', 'BETR', 'GLRE', 'SMMF', 'NETD', 'TPVG', 'HCVI', 'WDH', 'NOTR', 'RRAC', 'RRBI', 'ANSC', 'SUPV', 'MPB', 'MCBC', 'GNTY', 'IREN', 'SVII', 'EBTC', 'IPXX', 'FANH', 'ITIC', 'RENE', 'SAR', 'MBI', 'ACNB', 'SCM', 'IVCB', 'HYAC', 'JWSM', 'HIVE', 'WTBA', 'SKGR', 'WHF', 'VBNK', 'CBNK', 'FBIZ', 'BCAL', 'PFIS', 'TRTL', 'BKCC', 'UNTY', 'INBK', 'PRLH', 'FDBC', 'EMLD', 'LCAA', 'TCBX', 'FDOC', 'LNKB', 'BSVN', 'PLAO', 'FLIC', 'JMSB', 'OBT', 'CZFS', 'APTM', 'SSBK', 'PCB', 'CNDA', 'NECB', 'CONX', 'NWFL', 'SBXC', 'CHMG', 'PHYT', 'CFFS', 'OVLY', 'FVCB', 'CBAN', 'NFYS', 'KVAC', 'BPRN', 'SEDA', 'CALB', 'MBCN', 'COFS', 'MCAA', 'MNTN', 'XPDB', 'PEGR', 'IVCA', 'TRIS', 'OXSQ', 'PTMN', 'APCA', 'BCBP', 'VAQC', 'NKSH', 'HWBK', 'EVE', 'VERY', 'GAQ', 'CFNB', 'LCW', 'BRKH', 'ATLO', 'EVBN', 'HCMA', 'MRCC', 'HHLA', 'OFS', 'ESHA', 'ROSS', 'BFAC', 'IFIN', 'NSTD', 'KRNL', 'PEBK', 'TWLV', 'NSTC', 'BCSA', 'BVFL', 'FUNC', 'TLGY', 'FLME', 'LCA', 'WNNR', 'VCXB', 'FGBI', 'CFBK', 'FLFV', 'ALSA', 'ISRL', 'IRRX', 'CIA', 'LGVC', 'CNDB', 'ATEK', 'NNAG', 'VMCA', 'DHCA', 'FCCO', 'UNB', 'ACAH', 'ZLS', 'LGYV', 'RMGC', 'FIAC', 'GATE', 'DSAQ', 'NPAB', 'UBFO', 'KCGI', 'PLMI', 'ARBK', 'EVGR', 'NSTB', 'CZWI', 'PPYA', 'CPTK', 'BOCN', 'RCFA', 'SRL', 'IXAQ', 'TCOA', 'ARRW', 'PGSS', 'OPRT', 'BYNO', 'TOP', 'APXI', 'CDAQ', 'WMPN', 'SHAP', 'TWOA', 'CMCA', 'COOL', 'CITE', 'TGAA', 'CHAA', 'CBRG', 'LARK', 'AFBI', 'BSBK', 'ROOT', 'DPCS', 'SLAC', 'BLUA', 'MCAC', 'PORT', 'EFSI', 'MITA', 'CSLM', 'GPAC', 'SZZL', 'RVSB', 'THCP', 'SPKL', 'FNVT', 'LVPA', 'FTII', 'RBKB', 'ATMV', 'MARX', 'CNGL', 'GAMC', 'TENK', 'PWUP', 'LATG', 'PMGM', 'QDRO', 'BOWN', 'BLAC', 'UTGN', 'GIA', 'RWOD', 'NPFC', 'TBMC', 'ESAC', 'GODN', 'HSPO', 'OSI', 'WEL', 'PFX', 'SSSS', 'BITE', 'BLEU', 'ALTU', 'EMCG', 'EAC', 'GLLI', 'AACI', 'ARYD', 'WRAC', 'ONYX', 'NRAC', 'ENBP', 'OPOF', 'USCT', 'IVCP', 'ACAB', 'SRBK', 'GLST', 'XFIN', 'IMAQ', 'BHAC', 'DUET', 'FICV', 'OCAX', 'RCAC', 'AITR', 'GDST', 'BACA', 'PUCK', 'BUJA', 'AEAE', 'LIBY', 'TGLO', 'CETU', 'ASCB', 'GECC', 'MGYR', 'GBBK', 'RFAC', 'GTAC', 'FHLT', 'GGAAF', 'VHAQ', 'IRAA', 'INAQ', 'FEXD', 'FRLA', 'ATMC', 'TRON', 'SWSS', 'TETE', 'BWAQ', 'FORL', 'MSSA', 'APAC', 'GMFI', 'NVAC', 'DIST', 'LGST', 'QFTA', 'MAQC', 'DMYY', 'CLOE', 'LSBK', 'KYCH', 'PMVC', 'ROCL', 'AFAR', 'NBST', 'SDIG', 'SLBK', 'SEPA', 'PPBN', 'ENCP', 'JUVF', 'IGTA', 'ACAC', 'PTWO', 'LRFC', 'ASCA', 'BNIX', 'NWPP', 'HAIA', 'MBTC', 'SUND', 'ARIZ', 'IROQ', 'BYFC', 'CLST', 'CHEA', 'CCTS', 'HHGC', 'PEPL', 'RACY', 'CBKM', 'PLTN', 'BRAC', 'CLRC', 'KACL', 'NICK', 'VSAC', 'NSTS', 'ICMB', 'AAME', 'AQU', 'OWVI', 'BREZ', 'ICCH', 'WTMA', 'BCOW', 'HUDA', 'AOGO', 'WINV', 'TCBS', 'INTE', 'KWAC', 'MCAF', 'FSEA', 'AIB', 'ADOC', 'MACA', 'YOTA', 'TGVC', 'NOVV', 'PFTA', 'DHAC', 'HFBL', 'ACBA', 'LBBB', 'QOMO', 'WAVS', 'ADRT', 'ABTS', 'MCAG', 'AVHI', 'DECA', 'VWFB', 'PBAX', 'OPHC', 'WRPT', 'PPHP', 'BTM', 'PIAC', 'ILUS', 'AGBA', 'CAHO', 'GBNY', 'GNRV', 'TCRI', 'LOGQ', 'YTFD', 'XITO', 'RMCO', 'GLBZ', 'MDWK', 'STLY', 'MEGL', 'PFSB', 'CURO', 'NFTN', 'FGF', 'GOVB', 'PWM', 'PAPL', 'HNRA', 'SLTN', 'BWMY', 'OLKR', 'CARV', 'GFOO', 'WNFT', 'PCMC', 'DHCC', 'NHMD', 'WLYW', 'OOGI', 'AIHS', 'NLSC', 'ECGR', 'TRXA', 'WHLT', 'ALDA', 'LSMG', 'MGTI', 'TMIN', 'NCPL', 'STQN', 'FSTJ', 'GPLL', 'BEGI', 'GMPW', 'ATYG', 'DXF', 'WINSF', 'YBCN', 'FCIC', 'KATX', 'EEGI', 'RDGA', 'VCOR', 'EMAX', 'BOTH', 'VHLD', 'CONC', 'BZRD', 'CWNOF', 'WWSG', 'SDON', 'MMMM', 'PLYN', 'EQOSQ', 'PMPG', 'PARG', 'MUSS', 'IROH', 'CILJF', 'WEBNF', 'ATH-PA', 'TKCM', 'CIXXF', 'BDVC', 'GWIN', 'FFBW', 'OSBK', 'MBBC', 'FIGI', 'BQST', 'TBBA', 'WVFC', 'SICP', 'FBDS', 'BLYQ', 'SVVC', 'IMPM', 'MGHL', 'PUGE', 'SHGI', 'JMTM', 'RBRXF', 'EXCL', 'MSCF', 'SSRT', 'STGC']
# finmissingdivintPaid = ['AMP', 'PUK', 'PFG', 'XP', 'HLI', 'AGLY', 'CRVL', 'CNS', 'PIPR', 'HGTY', 'GSBD', 'FIHL', 'LMND', 'JMKJ', 'QD', 'GAIN', 'DHIL', 'GLAD', 'VALU', 'BETR', 
#                           'HCVI', 'WDH', 'ITIC', 'RENE', 'NODK', 'TRTL', 'BTBT', 'HIPO', 'KVAC', 'XPDB', 'XYF', 'VAQC', 'EVE', 'TWLV', 'FLFV', 'CIA', 'LGVC', 'ATEK', 'RMGC', 'FIAC', 
#                           'RCFA', 'OPRT', 'BYNO', 'TOP', 'APXI', 'SHAP', 'TWOA', 'CMCA', 'WHG', 'SLAC', 'BLUA', 'SZZL', 'THCP', 'LVPA', 'ATMV', 'MARX', 'TENK', 'PMGM', 'BOWN', 'BLAC', 'RWOD', 
#                           'TBMC', 'ESAC', 'GODN', 'HSPO', 'BITE', 'EMCG', 'ONYX', 'NRAC', 'ACAB', 'IMAQ', 'BHAC', 'DUET', 'OCAX', 'AITR', 'GDST', 'PUCK', 'BUJA', 'CETU', 'GBBK', 'GTAC', 'FHLT', 
#                           'FRLA', 'ATMC', 'SWSS', 'GMFI', 'NVAC', 'DIST', 'LGST', 'DMYY', 'CLOE', 'PMVC', 'ROCL', 'NBST', 'SEPA', 'ENCP', 'IGTA', 'BNIX', 'MBTC', 'CHEA', 'CCTS', 'HHGC', 'RACY', 
#                           'PLTN', 'KACL', 'OWVI', 'BREZ', 'AOGO', 'WINV', 'MCAF', 'AIB', 'MACA', 'YOTA', 'ACBA', 'LBBB', 'QOMO', 'WAVS', 'HYW', 'MCAG', 'AVHI', 'BMNR', 'WRPT', 'ILUS', 'CRMZ', 
#                           'TCJH', 'SAI', 'RMCO', 'ARGC', 'PT', 'MEGL', 'JT', 'PMIN', 'NFTN', 'FGF', 'TGGI', 'HNRA', 'ATIF', 'FDCT', 'OXBR', 'OOGI', 'NLSC', 'IWSH', 'WHLT', 'RELI', 'STQN', 'FSTJ', 'GPLL', 'ATYG', 'STRG', 'KATX', 'VCOR', 'BFYW', 'HGYN', 'CONC', 'BZRD', 'UNAM', 'SDON', 'IROH', 'UMAC', 'ODTC', 'ENDI', 'BLYQ', 'SVVC', 'MGHL', 'SHGI', 'RBRXF', 'EXCL', 'SSRT', 'STGC']
# finmissingdivtotalPaid =  []
# finmissingdivshares =  []
# finmissingroictotalequity =  ['LVPA', 'TGLO', 'MCVT', 'SLTN', 'OOGI']
# finmissingincomeyears =  ['ITUB', 'BBD', 'TW', 'JEF', 'COOP', 'JMKJ', 'CSWC', 'LC', 'MFIC', 'AMBC', 'WULF', 'QDMI', 'FDOC', 'CCFN', 'FOA', 'PPBN', 'SUND', 'BCTF', 'ILUS', 'WNLV', 'MCVT', 'NFTN', 'GFOO', 'WNFT', 'NHMD', 'WLYW', 'YBCN', 'FOMC', 'HGYN', 'WWSG', 'CDIX', 'TKCM', 'BQST', 'ADMG', 'FGCO', 'FBDS', 'BOPO', 'PUGE', 'APSI']
# finmissingdivyears = ['ITUB', 'BBD', 'TW', 'JEF', 'FRHC', 'COOP', 'JMKJ', 'CSWC', 'LC', 'MFIC', 'AMBC', 'WULF', 'QDMI', 'FDOC', 'CCFN', 'OCAX', 'FOA', 'PPBN', 'SUND', 'AIB', 'BCTF', 'BTCS', 'WNLV', 'MCVT', 'NFTN', 'GFOO', 'WNFT', 'NHMD', 'WLYW', 'STQN', 'FCIC', 'FOMC', 'HGYN', 'WWSG', 'CDIX', 'TKCM', 'BQST', 'ADMG', 'FGCO', 'FBDS', 'BOPO', 'SVVC', 'PUGE', 'APSI']
# finmissingroicyears = ['ITUB', 'BBD', 'JEF', 'JMKJ', 'CSWC', 'AMBC', 'QDMI', 'FDOC', 'CCFN', 'PPBN', 'BCTF', 'ILUS', 'MCVT', 'NFTN', 'GFOO', 'WNFT', 'NHMD', 'WLYW', 'YBCN', 'FOMC', 'HGYN', 'WWSG', 'CDIX', 'BQST', 'ADMG', 'FBDS', 'BOPO', 'PUGE', 'SHGI', 'APSI']

# finwrongincomeendyear =  ['HDB', 'MUFG', 'ITUB', 'NU', 'MFG', 'BBD', 'IX', 'KB', 'SHG', 'NMR', 'XP', 'BAP', 'BCH', 'HLI', 'WF', 'FUTU', 'HLNE', 'BMA', 'FRHC', 'CRVL', 'STEP', 'AMTD', 'AVAL', 'LU', 'IFS', 'GGAL', 'QFIN', 'INTR', 'PAX', 'FINV', 'BBAR', 'CSWC', 'BLX', 'NOAH', 'WRLD', 'AMBC', 'ABIT', 'PVNC', 'IGIC', 'APLD', 'TIGR', 'VINP', 'RILY', 'SAGA', 'QD', 'GAIN', 'LBC', 'QDMI', 'VALU', 'YRD', 'BETR', 'WDH', 'SUPV', 'FANH', 'VADP', 'SAR', 'IVCB', 'JWSM', 'FRST', 'HIVE', 'LX', 'PRLH', 'LCAA', 'APTM', 'PHYT', 'NFYS', 'SEDA', 'MCAA', 'MNTN', 'MFH', 'XYF', 'PEGR', 'IVCA', 'TRIS', 'VAQC', 'EVE', 'CFNB', 'BRKH', 'HCMA', 'SVMB', 'HHLA', 'ROSS', 'NSTD', 'TWLV', 'NSTC', 'BCSA', 'CNF', 'LCA', 'VCXB', 'ALSA', 'IRRX', 'ATEK', 'ACAH', 'ZLS', 'RMGC', 'FIAC', 'CWBC', 'ARBK', 'NSTB', 'CPTK', 'RCFA', 'SRL', 'TCOA', 'APXI', 'SHAP', 'CMCA', 'CHAA', 'SLAC', 'SZZL', 'RVSB', 'LVPA', 'ATMV', 'CNGL', 'TENK', 'LATG', 'PMGM', 'QDRO', 'BLAC', 'RWOD', 'NPFC', 'OSI', 'FOTB', 'BLEU', 'ALTU', 'EMCG', 'PSBQ', 'EAC', 'WRAC', 'NRAC', 'BUUZ', 'USCT', 'IMAQ', 'BHAC', 'FICV', 'RCAC', 'GDST', 'BACA', 'PUCK', 'AEAE', 'LIBY', 'BENF', 'GBBK', 'RFAC', 'VHAQ', 'IRAA', 'INAQ', 'FEXD', 'ATMC', 'SWSS', 'MSSA', 'APAC', 'GMFI', 'DIST', 'LGST', 'QFTA', 'SIEB', 'MAQC', 'KYCH', 'NBST', 'SEPA', 'PPBN', 'ENCP', 'BNIX', 'HAIA', 'MBTC', 'SUND', 'BYFC', 'CHEA', 'CCTS', 'PEPL', 'RACY', 'PLTN', 'NICK', 'VSAC', 'AQU', 'MATH', 'OWVI', 'WTMA', 'HUDA', 'AOGO', 'WINV', 'INTE', 'KWAC', 'MCAF', 'ADOC', 'YOTA', 'TGVC', 'PFTA', 'DHAC', 'LBBB', 'QOMO', 'WAVS', 'ADRT', 'ABTS', 'HUIZ', 'MCAG', 'GREE', 'PPHP', 'BTM', 'ILUS', 'CAHO', 'GNRV', 'WNLV', 'TCRI', 'TCJH', 'LOGQ', 'QMCI', 'XITO', 'SAI', 'RMCO', 'MDWK', 'ARGC', 'PT', 'NISN', 'MEGL', 'JT', 'TNBI', 'CURO', 'TGGI', 'HNRA', 'SLTN', 'CARV', 'SIVBQ', 'FDCT', 'SNTG', 'TNRG', 'NHMD', 'OOGI', 'AIHS', 'NLSC', 'ECGR', 'SITS', 'LGHL', 'ADAD', 'WHLT', 'MGTI', 'FRBK', 'NCPL', 'GLAE', 'TIRX', 'BEGI', 'JPPYY', 'GMPW', 'ATYG', 'DXF', 'STRG', 'YBCN', 'FCIC', 'FOMC', 'KATX', 'EEGI', 'MTLK', 'VCOR', 'BFYW', 'HGYN', 'COSG', 'RAHGF', 'BOTH', 'PLTYF', 'CONC', 'BZRD', 'CWNOF', 'WWSG', 'UNAM', 'SDON', 'MMMM', 'AFHIF', 'PLYN', 'EQOSQ', 'PMPG', 'SYSX', 'LFAP', 'PARG', 'MUSS', 'CILJF', 'CIXXF', 'BDVC', 'GAMI', 'BKSC', 'ODTC', 'GWIN', 'OFED', 'UBOH', 'FFBW', 'MSVB', 'OSBK', 'FIGI', 'BQST', 'TBBA', 'WVFC', 'ADMG', 'ERKH', 'SICP', 'FGCO', 'BOPO', 'HALL', 'IMPM', 'MGHL', 'PUGE', 'PLPL', 'APSI', 'CNGT', 'JMTM', 'RBRXF', 'BABL', 'EXCL', 'STGC']
# finwrongdivendyear =  ['HDB', 'MUFG', 'SMFG', 'ITUB', 'MFG', 'BBD', 'IX', 'KB', 'SHG', 'XP', 'BAP', 'BCH', 'HLI', 'WF', 'FUTU', 'BMA', 'FRHC', 'CRVL', 'STEP', 'AVAL', 'LU', 'HGTY', 'IFS', 'GGAL', 'QFIN', 'INTR', 'PAX', 'FINV', 'BBAR', 'CSWC', 'BLX', 'WRLD', 'AMBC', 'ABIT', 'PVNC', 'APLD', 'TIGR', 'VINP', 'RILY', 'QD', 'GAIN', 'LBC', 'QDMI', 'VALU', 'YRD', 'BETR', 'HCVI', 'WDH', 'NOTR', 'SUPV', 'FANH', 'VADP', 'RENE', 'FRST', 'HIVE', 'LX', 'TRTL', 'XPDB', 'MFH', 'XYF', 'VAQC', 'EVE', 'CFNB', 'SVMB', 'TWLV', 'CNF', 'ALSA', 'LGVC', 'ATEK', 'RMGC', 'FIAC', 'CWBC', 'ARBK', 'RCFA', 'SRL', 'BYNO', 'TOP', 'APXI', 'SHAP', 'TWOA', 'CMCA', 'SLAC', 'BLUA', 'GPAC', 'SZZL', 'RVSB', 'THCP', 'LVPA', 'ATMV', 'MARX', 'TENK', 'PMGM', 'BLAC', 'RWOD', 'NPFC', 'ESAC', 'FOTB', 'EMCG', 'PSBQ', 'ONYX', 'NRAC', 'BUUZ', 'ACAB', 'IMAQ', 'BHAC', 'DUET', 'GDST', 'PUCK', 'BENF', 'GBBK', 'GTAC', 'FHLT', 'VHAQ', 'FRLA', 'ATMC', 'SWSS', 'MSSA', 'GMFI', 'DIST', 'LGST', 'SIEB', 'CLOE', 'PMVC', 'NBST', 'SEPA', 'PPBN', 'ENCP', 'BNIX', 'MBTC', 'SUND', 'BYFC', 'CHEA', 'CCTS', 'HHGC', 'RACY', 'PLTN', 'NICK', 'MATH', 'OWVI', 'HUDA', 'AOGO', 'WINV', 'MCAF', 'ADOC', 'MACA', 'YOTA', 'DHAC', 'LBBB', 'QOMO', 'WAVS', 'ADRT', 'ABTS', 'HUIZ', 'MCAG', 'GREE', 'WRPT', 'ILUS', 'CAHO', 'GNRV', 'WNLV', 'TCRI', 'TCJH', 'LOGQ', 'QMCI', 'XITO', 'SAI', 'RMCO', 'MDWK', 'ARGC', 'PT', 'NISN', 'MEGL', 'JT', 'TNBI', 'CURO', 'NFTN', 'TGGI', 'HNRA', 'SLTN', 'CARV', 'SIVBQ', 'FDCT', 'SNTG', 'TNRG', 'NHMD', 'OOGI', 'AIHS', 'NLSC', 'ECGR', 'SITS', 'LGHL', 'ADAD', 'TRXA', 'WHLT', 'LSMG', 'MGTI', 'FRBK', 'NCPL', 'GLAE', 'FSTJ', 'TIRX', 'BEGI', 'JPPYY', 'GMPW', 'ATYG', 'DXF', 'STRG', 'YBCN', 'FCIC', 'FOMC', 'KATX', 'EEGI', 'MTLK', 'VCOR', 'BFYW', 'HGYN', 'COSG', 'RAHGF', 'BOTH', 'PLTYF', 'CONC', 'BZRD', 'CWNOF', 'WWSG', 'UNAM', 'SDON', 'MMMM', 'AFHIF', 'PLYN', 'EQOSQ', 'PMPG', 'SYSX', 'LFAP', 'PARG', 'MUSS', 'CILJF', 'TKCM', 'CIXXF', 'BDVC', 'GAMI', 'BKSC', 'ODTC', 'GWIN', 'OFED', 'UBOH', 'FFBW', 'MSVB', 'OSBK', 'FIGI', 'BQST', 'TBBA', 'WVFC', 'ADMG', 'ERKH', 'SICP', 'FGCO', 'BLYQ', 'BOPO', 'HALL', 'IMPM', 'MGHL', 'PUGE', 'PLPL', 'APSI', 'CNGT', 'JMTM', 'RBRXF', 'BABL', 'EXCL', 'STGC']
# finwrongroicendyear =  ['HDB', 'MUFG', 'SMFG', 'ITUB', 'MFG', 'BBD', 'KB', 'SHG', 'NMR', 'XP', 'BAP', 'BCH', 'HLI', 'WF', 'FUTU', 'BMA', 'FRHC', 'CRVL', 'STEP', 'AVAL', 'LU', 'IFS', 'GGAL', 'QFIN', 'INTR', 'PAX', 'FINV', 'BBAR', 'CSWC', 'BLX', 'WRLD', 'AMBC', 'ABIT', 'PVNC', 'IGIC', 'APLD', 'TIGR', 'VINP', 'RILY', 'QD', 'GAIN', 'LBC', 'QDMI', 'VALU', 'YRD', 'BETR', 'WDH', 'SUPV', 'FANH', 'VADP', 'SAR', 'FRST', 'HIVE', 'LX', 'MFH', 'XYF', 'VAQC', 'EVE', 'CFNB', 'SVMB', 'TWLV', 'CNF', 'ALSA', 'ATEK', 'RMGC', 'FIAC', 'CWBC', 'ARBK', 'RCFA', 'SRL', 'APXI', 'SHAP', 'CMCA', 'SLAC', 'SZZL', 'RVSB', 'LVPA', 'ATMV', 'TENK', 'PMGM', 'BLAC', 'RWOD', 'NPFC', 'FOTB', 'EMCG', 'PSBQ', 'NRAC', 'BUUZ', 'IMAQ', 'BHAC', 'GDST', 'PUCK', 'BENF', 'GBBK', 'VHAQ', 'ATMC', 'SWSS', 'MSSA', 'GMFI', 'DIST', 'LGST', 'SIEB', 'NBST', 'SEPA', 'PPBN', 'ENCP', 'BNIX', 'MBTC', 'SUND', 'BYFC', 'CHEA', 'CCTS', 'RACY', 'PLTN', 'NICK', 'MATH', 'OWVI', 'HUDA', 'AOGO', 'WINV', 'MCAF', 'ADOC', 'YOTA', 'DHAC', 'LBBB', 'QOMO', 'WAVS', 'ADRT', 'ABTS', 'HUIZ', 'MCAG', 'GREE', 'ILUS', 'CAHO', 'GNRV', 'WNLV', 'TCRI', 'TCJH', 'LOGQ', 'QMCI', 'XITO', 'SAI', 'RMCO', 'MDWK', 'ARGC', 'PT', 'NISN', 'MEGL', 'JT', 'TNBI', 'CURO', 'TGGI', 'HNRA', 'SLTN', 'CARV', 'SIVBQ', 'FDCT', 'SNTG', 'TNRG', 'NHMD', 'OOGI', 'AIHS', 'NLSC', 'ECGR', 'SITS', 'LGHL', 'ADAD', 'WHLT', 'MGTI', 'FRBK', 'NCPL', 'GLAE', 'TIRX', 'BEGI', 'JPPYY', 'GMPW', 'ATYG', 'STRG', 'YBCN', 'FCIC', 'FOMC', 'KATX', 'EEGI', 'MTLK', 'VCOR', 'BFYW', 'HGYN', 'COSG', 'RAHGF', 'BOTH', 'PLTYF', 'CONC', 'BZRD', 'CWNOF', 'WWSG', 'UNAM', 'SDON', 'MMMM', 'AFHIF', 'PLYN', 'EQOSQ', 'PMPG', 'SYSX', 'LFAP', 'PARG', 'MUSS', 'CILJF', 'CIXXF', 'BDVC', 'GAMI', 'BKSC', 'ODTC', 'GWIN', 'OFED', 'UBOH', 'FFBW', 'MSVB', 'OSBK', 'FIGI', 'BQST', 'TBBA', 'WVFC', 'ADMG', 'ERKH', 'SICP', 'FGCO', 'BOPO', 'HALL', 'IMPM', 'MGHL', 'PUGE', 'PLPL', 'APSI', 'CNGT', 'JMTM', 'RBRXF', 'BABL', 'EXCL', 'STGC']
###

####NEW UTIL
# recap list: 
# ['OEZVY', 'BEP', 'BIP', 'SBS', 'RDEIY', 'CMS-PB', 'UELMO', 'CIG', 'BIPC', 'BEPC', 'AILIH', 'EDN', 'ALCE', 'CLNV', 'UGEIF', 'ELIQ', 'CNTHP']
# missing income revenue
# ['MGEE', 'ALCE', 'VGAS', 'WNDW', 'ELIQ', 'MMMW', 'PPWLM', 'VXIT']
# missing income netIncome
# []
# missing income opCF
# ['NGG']
# missing income capEx
# ['NEE', 'DTE', 'BIPC', 'CWT', 'SJW', 'ALCE', 'GEBRF', 'ADN', 'ASRE', 'ARAO', 'ELIQ']
# missing income netCF
# []
# missing income depreNAmor
# ['SO', 'NGG', 'CEG', 'PCG', 'XEL', 'EBR', 'PPL', 'AEE', 'BEP', 'BIP', 'SBS', 'KEP', 'ELP', 'CIG', 'BIPC', 'BEPC', 'ENIC', 'OGS', 'NEP', 'RNW', 'PAM', 'MGEE', 'TAC', 'AY', 'ENLT', 'CEPU', 
#  'KEN', 'EDN', 'AMPS', 'OPAL', 'UTL', 'ARIS', 'ELLO', 'ALCE', 'VGAS', 'GEBRF', 'HTOO', 'ADN', 'BNRG', 'ASRE', 'WAVE', 'ARAO', 'ELIQ', 'CPWR', 'GSFI', 'PPWLM', 'HUNGF', 'VXIT']
# missing income prop sales
# []
# missing div intPaid
# ['NEE', 'NWN', 'HLGN', 'PWCO']
# missing div totalPaid
# []
# missing div shares
# []
# missing roic total equity
# []
# missing income years:
# ['EMRAF', 'GWRS', 'MMMW']
# missing div years:
# ['EMRAF', 'VGAS', 'MMMW']
# missing roic years:
# ['EMRAF', 'MMMW']
# wrong income end year
# ['NGG', 'EBR', 'SBS', 'KEP', 'ELP', 'CIG', 'ENIC', 'RNW', 'PAM', 'CEPU', 'EDN', 'ELLO', 'AZREF', 'ALCE', 'GEBRF', 'HTOO', 'ADN', 'CREG', 'ARAO', 'ELIQ', 'MMMW', 'GSFI', 'VENG', 'PPWLM', 'HUNGF', 'PWCO', 'VXIT']
# wrong div end year
# ['NGG', 'EBR', 'KEP', 'ELP', 'ENIC', 'RNW', 'PAM', 'CEPU', 'ELLO', 'AZREF', 'GEBRF', 'HTOO', 'ADN', 'CREG', 'ARAO', 'MMMW', 'GSFI', 'VENG', 'PPWLM', 'HUNGF', 'PWCO', 'VXIT']
# wrong roic end year
# ['NGG', 'EBR', 'KEP', 'ELP', 'ENIC', 'RNW', 'PAM', 'CEPU', 'ELLO', 'AZREF', 'GEBRF', 'HTOO', 'ADN', 'CREG', 'ARAO', 'MMMW', 'GSFI', 'VENG', 'PPWLM', 'HUNGF', 'PWCO', 'VXIT']
#####



###NEW RE
# recap list = ['HLDCY', 'BPYPP', 'HNGKY', 'VTMX', 'SKT', 'HASI', 'ESBA', 'PKST', 'FPH', 'AOMR', 'NEN', 'SDHC', 'AIRE', 'LRHC', 'UCASU', 'MSTO', 'SFRT', 'PVOZ']
# missing income revenue =  ['NLY', 'AGNC', 'SKT', 'RC', 'LADR', 'TWO', 'CIM', 'EFC', 'ARR', 'RWT', 'DX', 'NYMT', 'KREF', 'ORC', 'TRTX', 'IVR', 'NREF', 'GPMT', 'AOMR', 'AJX', 'LFT', 'CHMI', 'EARN', 'SGD', 'MTPP', 'ABCP', 'MSPC', 'SFRT']
# missing income netIncome =  ['SKT']
# missing income opCF =  ['SKT']
# missing income capEx =  ['DLR', 'ARE', 'WPC', 'REG', 'CPT', 'NLY', 'NNN', 'FR', 'BRX', 'AGNC', 'STWD', 'TRNO', 'RITM', 'PECO', 'MAC', 'CUZ', 'BXMT', 'SBRA', 'TCN', 'DOC', 'SITC', 'SKT', 'HIW', 'ABR', 'EQC', 'MPW', 'JBGS', 'NXRT', 'RC', 'VRE', 'ARI', 'NTST', 'CMTG', 'TWO', 'PMT', 'DEA', 'ALX', 'PGRE', 'AHH', 'CIM', 'FBRT', 'ARR', 'RWT', 'BDN', 'DX', 'KREF', 'GMRE', 'FPI', 'REAX', 'SRG', 'CLDT', 'GOOD', 'LAND', 'LSEA', 'OLP', 'ORC', 'STRW', 'IVR', 'NLCP', 'NLOP', 'NREF', 'BRT', 'REFI', 'ONL', 'GPMT', 'AOMR', 'NXDT', 'NEN', 'AFCG', 'OZ', 'CIO', 'MITT', 'SEVN', 'NHHS', 'STHO', 'LFT', 'MDV', 'CHMI', 'EARN', 'SELF', 'HWTR', 'CMRF', 'LEJU', 'SQFT', 'CRDV', 'MTPP', 'ABCP', 'NIHK', 'AOXY', 'MYCB', 'MSPC', 'SFRT']
# missing income netCF =  ['SKT']
# missing income depreNAmor =  ['AMT', 'CCI', 'VICI', 'AVB', 'SBAC', 'EQR', 'INVH', 'BEKE', 'ELS', 'NLY', 'AGNC', 'BXMT', 'TCN', 'SKT', 'NHI', 'CMTG', 
#                               'TWO', 'CIM', 'EFC', 'UMH', 'ARR', 'DX', 'KREF', 'IRS', 'REAX', 'ORC', 'TRTX', 'IVR', 'REFI', 'AOMR', 'AFCG', 'STRS', 'SACH', 
#                               'AJX', 'FREVS', 'CHMI', 'EARN', 'CPTP', 'FGNV', 'LOAN', 'IHT', 'SGD', 'CRDV', 'GGE', 'ABCP', 'NIHK', 'AOXY', 'MYCB', 'HCDIQ', 'MSPC', 'SFRT']
# missing income prop sales = []
# missing div intPaid = ['DEA', 'RMR', 'BRT', 'DOUG', 'SACH', 'STHO', 'AWCA', 'KANP', 'BHM', 'LOAN', 'MTPP', 'DUO']
# missing div totalPaid = []
# missingdivshares =  []
# missingroictotalequity = []
# missingincomeyears= ['GRP-UN', 'FOR', 'CBL', 'GMRE', 'NXDT', 'AWCA', 'MHPC', 'TPHS', 'ZDPY', 'ACAN', 'MAA']
# missingdivyears = ['GRP-UN', 'FOR', 'CSR', 'CBL', 'GMRE', 'NXDT', 'AWCA', 'MHPC', 'TPHS', 'ZDPY', 'MYCB', 'MAA']
# missingroicyears=  ['HST', 'GRP-UN', 'FOR', 'AWCA', 'SRRE', 'MHPC', 'TPHS', 'ZDPY', 'ACAN', 'MAA']
# wrongincomeendyear = ['BEKE', 'SKT', 'NTPIF', 'AXR', 'FGNV', 'HWTR', 'SRRE', 'OMH', 'GIPR', 'LEJU', 'XIN', 'MDJH', 'SQFT', 'GYRO', 'IHT', 'MHPC', 'CRDV', 'WEWKQ', 'ILAL', 'ALBT', 'CORR', 'VINO', 'WETH', 'DUO', 'PDNLA', 'HBUV', 'UK', 'NIHK', 'DPWW', 'SRC', 'MSPC', 'SFRT']
# wrongdendyear =  ['BEKE', 'NTPIF', 'AXR', 'FGNV', 'HWTR', 'SRRE', 'OMH', 'GIPR', 'LEJU', 'XIN', 'MDJH', 'SQFT', 'GYRO', 'IHT', 'MHPC', 'CRDV', 'WEWKQ', 'ILAL', 'ALBT', 'CORR', 'VINO', 'WETH', 'DUO', 'PDNLA', 'HBUV', 'UK', 'NIHK', 'DPWW', 'SRC', 'SGIC', 'MSPC']
# wrongrendyear =  ['BEKE', 'NTPIF', 'AXR', 'FGNV', 'HWTR', 'SRRE', 'OMH', 'GIPR', 'LEJU', 'XIN', 'MDJH', 'SQFT', 'GYRO', 'IHT', 'MHPC', 'CRDV', 'WEWKQ', 'ILAL', 'ALBT', 'CORR', 'VINO', 'WETH', 'DUO', 'PDNLA', 'HBUV', 'UK', 'NIHK', 'DPWW', 'SRC', 'MSPC']
####

# print(set(wrong).difference(REincwrongendyear))
# print(len(techmissingincomecapEx))
# print(len(techmissingincomecapex2))

##Tech
# techrecap2 = ['TOELY', 'MRAAY', 'DSCSY', 'NTDTY', 'OMRNY', 'ROHCY', 'CNXC', 'ASMVY', 'VERX', 'SRAD', 'ODD', 'BELFA', 'GB', 'RDZN', 'ABXXF', 'WBX', 'OPTX', 'EAXR', 'FEBO', 'SPPL', 'GRRR', 'NVNI', 'YIBO', 'DGHI', 'BTQQF', 'LVER', 'MMTIF', 'MRT', 'ITMSF', 'MAPPF', 'CXAI', 'SYNX', 'NOWG', 'HLRTF', 'MCLDF', 'MHUBF', 'PKKFF', 'CAUD', 'VJET', 'SSCC', 'AWIN', 'IMTE', 'VSOLF', 'YQAI', 'VPER', 'SRMX', 'TPPM', 'ASFT', 'GBUX', 'CMCZ', 'ZICX', 'FLXT', 'BCNN', 'FERN', 'SMXT', 'XYLB', 'SELX', 'ATCH', 'WONDF', 'MTMV', 'SWISF', 'DCSX', 'RONN']
# # print(len(techrecap2))
# techwrongendyearincome = ['TSM', 'ORCL', 'SONY', 'INFY', 'ADSK', 'MCHP', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'PCRFY', 'UMC', 'NTAP', 'DIDIY', 'DT', 'GEN', 'LOGI', 'ESTC', 'QRVO', 'FLEX', 'NXT', 'YMM', 'ALGM', 'STNE', 'CRUS', 'KD', 'PAGS', 'CVLT', 'DXC', 'CRDO', 'LPL', 'AI', 'WNS', 'RAMP', 'VSAT', 'AGYS', 'SIMO', 'LSPD', 'PLUS', 'NTCT', 'CSIQ', 'JKS', 'DQ', 'INFN', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'WALD', 'GB', 'HKD', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'MTWO', 'SPWR', 'MGIC', 'CGNT', 'ITRN', 'MLAB', 'AEHR', 'RDZN', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'CAN', 'QIWI', 'DAKT', 'EGHT', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'API', 'LUNA', 'MAXN', 'ITI', 'MIXT', 'WEWA', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'TIO', 'OPTX', 'MAPS', 'AIXI', 'LTCH', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'FEIM', 'SOL', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'ZEPP', 'MOBX', 'EBIXQ', 'PXDT', 'GRRR', 'ALLT', 'BCRD', 'GWSO', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'EBON', 'DZSI', 'EGIO', 'GSIT', 'DGHI', 'KPLT', 'STIX', 'APGT', 'LVER', 'RCAT', 'BTCM', 'AGMH', 'MOGO', 'DSWL', 'MRT', 'QMCO', 'SODI', 'SWVL', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'MFON', 'UTSI', 'WKEY', 'AITX', 'SEAV', 'JG', 'SGMA', 'CXAI', 'SPI', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'EBZT', 'FTFT', 'CISO', 'MARK', 'KULR', 'HUBC', 'MCLDF', 'MINM', 'VSMR', 'CAUD', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'HTCR', 'INPX', 'VJET', 'ISUN', 'IFBD', 'DPLS', 'WRNT', 'MIND', 'IONI', 'WETG', 'NAHD', 'QH', 'ELWS', 'SUIC', 'NXTP', 'AWIN', 'VIDE', 'SOPA', 'IMTE', 'KCRD', 'FRGT', 'MICS', 'WDLF', 'CAMP', 'SUNW', 'LGIQ', 'VEII', 'MWRK', 'LYT', 'WTO', 'SRCO', 'IRNTQ', 'RKFL', 'SASI', 'DUSYF', 'LZGI', 'ASFT', 'SING', 'XALL', 'UCLE', 'BRQSF', 'ATDS', 'CHJI', 'EDGM', 'CUEN', 'CTKYY', 'AEY', 'ZRFY', 'SYTA', 'GAHC', 'MLRT', 'WOWI', 'XNDA', 'ONCI', 'ODII', 'PSWW', 'TTCM', 'IGEN', 'TPTW', 'LAAB', 'GIGA', 'FLXT', 'WDDD', 'DCLT', 'ITOX', 'PTOS', 'CRCW', 'MAPT', 'MCCX', 'NOGNQ', 'AGILQ', 'IINX', 'RDAR', 'GAXY', 'NIRLQ', 'KBNT', 'GTCH', 'TMPOQ', 'ALFIQ', 'TMNA', 'ISGN', 'IMCI', 'DSGT', 'OGBLY', 'NIPNF', 'AUOTY', 'PBTS', 'LCHD', 'AATC', 'EXEO', 'AKOM', 'WSTL', 'IEHC', 'CATG', 'SEAC', 'BNSOF', 'EVOL', 'FALC', 'HPTO', 'IPTK', 'VQSSF', 'RBCN', 'TKOI', 'BDRL', 'GSPT', 'ANDR', 'DROP', 'SPYR', 'TCCO', 'EHVVF', 'DUUO', 'ABCE', 'BTZI', 'MJDS', 'SMIT', 'SEII', 'XDSL', 'TRIRF', 'SANP', 'ADGO', 'TKLS', 'MAXD', 'SDVI', 'DIGAF', 'GDLG', 'HMELF']
# techwrongdivendyear = ['TSM', 'ORCL', 'SONY', 'INFY', 'ADSK', 'MCHP', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'PCRFY', 'UMC', 'NTAP', 'DIDIY', 'DT', 'GEN', 'LOGI', 'ESTC', 'QRVO', 'FLEX', 'NXT', 'YMM', 'ALGM', 'STNE', 'CRUS', 'KD', 'PAGS', 'CVLT', 'DXC', 'CRDO', 'LPL', 'AI', 'YOU', 'WNS', 'RAMP', 'VSAT', 'AGYS', 'SIMO', 'LSPD', 'PLUS', 'NTCT', 'CSIQ', 'JKS', 'DQ', 'INFN', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'WALD', 'HKD', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'MTWO', 'SPWR', 'MGIC', 'CGNT', 'ITRN', 'MLAB', 'AEHR', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'CAN', 'QIWI', 'DAKT', 'EGHT', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'API', 'LUNA', 'MAXN', 'ITI', 'WEWA', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'TIO', 'MAPS', 'AIXI', 'LTCH', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'FEIM', 'SOL', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'ZEPP', 'MOBX', 'EBIXQ', 'PXDT', 'ALLT', 'BCRD', 'GWSO', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'EBON', 'DZSI', 'EGIO', 'GSIT', 'KPLT', 'STIX', 'APGT', 'RCAT', 'BTCM', 'AGMH', 'HSTA', 'MOGO', 'DSWL', 'QMCO', 'SODI', 'SWVL', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'MFON', 'UTSI', 'WKEY', 'AITX', 'SEAV', 'JG', 'SGMA', 'SPI', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'EBZT', 'FTFT', 'CISO', 'MARK', 'KULR', 'HUBC', 'MINM', 'VSMR', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'HTCR', 'INPX', 'VJET', 'ISUN', 'IFBD', 'DPLS', 'WRNT', 'MIND', 'IONI', 'WETG', 'NAHD', 'QH', 'NUGN', 'ELWS', 'SUIC', 'NXTP', 'VIDE', 'SOPA', 'VS', 'KCRD', 'FRGT', 'CIIT', 'MICS', 'WDLF', 'CAMP', 'SUNW', 'LGIQ', 'VEII', 'MWRK', 'LYT', 'WTO', 'SRCO', 'IRNTQ', 'RKFL', 'SASI', 'DUSYF', 'LZGI', 'TAOP', 'ASFT', 'SING', 'XALL', 'UCLE', 'BRQSF', 'ATDS', 'FCCN', 'CHJI', 'EDGM', 'CUEN', 'CTKYY', 'AEY', 'ZRFY', 'SYTA', 'GAHC', 'MLRT', 'WOWI', 'XNDA', 'ONCI', 'ODII', 'PSWW', 'TTCM', 'IGEN', 'TPTW', 'LAAB', 'GIGA', 'FLXT', 'WDDD', 'DCLT', 'ITOX', 'PTOS', 'CRCW', 'MAPT', 'MCCX', 'NOGNQ', 'AGILQ', 'IINX', 'RDAR', 'GAXY', 'NIRLQ', 'KBNT', 'GTCH', 'TMPOQ', 'ALFIQ', 'TMNA', 'ISGN', 'IMCI', 'DSGT', 'OGBLY', 'NIPNF', 'AUOTY', 'PBTS', 'LCHD', 'AATC', 'EXEO', 'AKOM', 'WSTL', 'IEHC', 'CATG', 'SEAC', 'BNSOF', 'EVOL', 'FALC', 'HPTO', 'IPTK', 'VQSSF', 'RBCN', 'TKOI', 'BDRL', 'GSPT', 'ANDR', 'DROP', 'SPYR', 'TCCO', 'EHVVF', 'DUUO', 'ABCE', 'BTZI', 'MJDS', 'SMIT', 'SEII', 'XDSL', 'TRIRF', 'SANP', 'ADGO', 'TKLS', 'MAXD', 'SDVI', 'DIGAF', 'GDLG', 'HMELF']
# techwrongroicendyear = ['TSM', 'ORCL', 'SONY', 'INFY', 'ADSK', 'MCHP', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'PCRFY', 'UMC', 'NTAP', 'DIDIY', 'DT', 'GEN', 'LOGI', 'ESTC', 'QRVO', 'FLEX', 'NXT', 'YMM', 'ALGM', 'STNE', 'CRUS', 'KD', 'PAGS', 'CVLT', 'DXC', 'CRDO', 'LPL', 'AI', 'WNS', 'RAMP', 'VSAT', 'AGYS', 'SIMO', 'LSPD', 'PLUS', 'NTCT', 'CSIQ', 'JKS', 'DQ', 'INFN', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'WALD', 'HKD', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'MTWO', 'SPWR', 'MGIC', 'CGNT', 'ITRN', 'MLAB', 'AEHR', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'CAN', 'QIWI', 'DAKT', 'EGHT', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'API', 'LUNA', 'MAXN', 'ITI', 'MIXT', 'WEWA', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'TIO', 'MAPS', 'AIXI', 'LTCH', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'FEIM', 'SOL', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'ZEPP', 'MOBX', 'EBIXQ', 'PXDT', 'ALLT', 'BCRD', 'GWSO', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'EBON', 'DZSI', 'EGIO', 'GSIT', 'KPLT', 'STIX', 'APGT', 'RCAT', 'BTCM', 'AGMH', 'MOGO', 'DSWL', 'QMCO', 'SODI', 'SWVL', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'MFON', 'UTSI', 'WKEY', 'AITX', 'SEAV', 'JG', 'SGMA', 'SPI', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'EBZT', 'FTFT', 'CISO', 'MARK', 'KULR', 'HUBC', 'MINM', 'VSMR', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'HTCR', 'INPX', 'ISUN', 'IFBD', 'DPLS', 'WRNT', 'MIND', 'IONI', 'WETG', 'NAHD', 'QH', 'ELWS', 'SUIC', 'NXTP', 'VIDE', 'SOPA', 'KCRD', 'FRGT', 'MICS', 'WDLF', 'CAMP', 'SUNW', 'LGIQ', 'VEII', 'MWRK', 'LYT', 'WTO', 'SRCO', 'IRNTQ', 'RKFL', 'SASI', 'DUSYF', 'LZGI', 'TAOP', 'SING', 'XALL', 'UCLE', 'BRQSF', 'ATDS', 'CHJI', 'EDGM', 'CUEN', 'CTKYY', 'AEY', 'ZRFY', 'GAHC', 'MLRT', 'WOWI', 'XNDA', 'ONCI', 'ODII', 'PSWW', 'TTCM', 'IGEN', 'TPTW', 'LAAB', 'GIGA', 'WDDD', 'DCLT', 'ITOX', 'PTOS', 'CRCW', 'MAPT', 'MCCX', 'NOGNQ', 'AGILQ', 'IINX', 'RDAR', 'GAXY', 'NIRLQ', 'KBNT', 'GTCH', 'TMPOQ', 'ALFIQ', 'TMNA', 'ISGN', 'IMCI', 'DSGT', 'OGBLY', 'NIPNF', 'AUOTY', 'PBTS', 'LCHD', 'AATC', 'EXEO', 'AKOM', 'WSTL', 'IEHC', 'CATG', 'SEAC', 'BNSOF', 'EVOL', 'FALC', 'HPTO', 'IPTK', 'VQSSF', 'RBCN', 'TKOI', 'BDRL', 'GSPT', 'ANDR', 'DROP', 'SPYR', 'TCCO', 'EHVVF', 'DUUO', 'ABCE', 'BTZI', 'MJDS', 'SMIT', 'SEII', 'XDSL', 'TRIRF', 'SANP', 'ADGO', 'TKLS', 'MAXD', 'SDVI', 'DIGAF', 'GDLG', 'HMELF']

# techmissingincomeyears = ['INST', 'LPL', 'WNS', 'BBAI', 'ARAT', 'SURG', 'ZFOX', 'RELL', 'LINK', 'AKTS', 'DPSI', 'FCUV', 'CPTN', 'ALMU', 'INVU', 'SODI', 'AITX', 'HWNI', 'ONEI', 'CYCA', 'MTBL', 'APYP', 'SLNH', 'FWFW', 'NUGN', 'INTV', 'VEII', 'LZGI', 'MYSZ', 'CHJI', 'CUEN', 'ONCI', 'PTOS', 'CRCW', 'GAXY', 'IMCI', 'BTZI', 'MJDS']
# techmissingdivyears =['INST', 'LPL', 'WNS', 'RPAY', 'BBAI', 'ARAT', 'SURG', 'ZFOX', 'RELL', 'LINK', 'AKTS', 'DPSI', 'FCUV', 'CPTN', 'ALMU', 'INVU', 'SODI', 'AITX', 'HWNI', 'ONEI', 'CYCA', 'APYP', 'BLBX', 'SLNH', 'FWFW', 'SUIC', 'INTV', 'VEII', 'CHJI', 'CUEN', 'TTCM', 'CYAP', 'PTOS', 'CRCW', 'GAXY', 'MJDS']
# techmissingroicyears = ['EPAM', 'LPL', 'WNS', 'ARAT', 'LINK', 'AKTS', 'DPSI', 'CPTN', 'ALMU', 'SODI', 'AITX', 'ONEI', 'FTFT', 'CYCA', 'APYP', 'SLNH', 'FWFW', 'NUGN', 'VEII', 'LZGI', 'MYSZ', 'CHJI', 'CUEN', 'PTOS', 'MCCX', 'GAXY', 'IMCI', 'BTZI', 'MJDS']

# techmissingrev = ['RDZN', 'NUKK', 'OPTX', 'MOBX', 'XBP', 'HYSR', 'MRT', 'AVAI', 'CXAI', 'MVLA', 'VSMR', 'CAUD', 'AWIN', 'NEWH', 'SMME', 'NIRLQ', 'CATG', 'GSPT', 'SANP']
# techmissingnetincome = ['MMTIF']
# techmissingincomecapEx = ['GRAB', 'LYFT', 'DAVA', 'BMBL', 'AVDX', 'PLUS', 'CRCT', 'BIGC', 'KC', 'MTWO', 'STEM', 'RDZN', 'NUKK', 'BKSY', 'RPMT', 'SQNS', 'OPTX', 'MOBX', 'LVER', 'APCX', 'HSTA', 'ALMU', 'AISP', 'MRT', 'ULY', 'SEAV', 'SGMA', 'CXAI', 'GOLQ', 'MVLA', 'ONEI', 'CLOQ', 'CYCA', 'SOBR', 'VSMR', 'CAUD', 'BOXL', 'FWFW', 'AWIN', 'VMNT', 'DTSS', 'CIIT', 'WDLF', 'LGIQ', 'MWRK', 'OVTZ', 'LZGI', 'XALL', 'ALDS', 'SMME', 'PSWW', 'LAAB', 'VISM', 'FLXT', 'WDDD', 'ITOX', 'PTOS', 'NIRLQ', 'CDAY', 'WBSR', 'IPTK', 'GSPT', 'DROP', 'EHVVF', 'MJDS', 'SANP', 'ADGO', 'SDVI', 'DIGAF', 'GDLG', 'TFLM', 'ANKM', 'TRSO']

# techmissingincomeopCF = ['BCAN']
# techmissingincomenetCF = ['VSMR', 'EXEO']

# techmissdivpaid = []
# techmissingdivshares = []
# techmissingroictotalequity = ['VSMR']
# techmissingdivintPaid =['SNOW', 'MPWR', 'ZM', 'CHKP', 'IOT', 'EPAM', 'NTNX', 'PATH', 'GTLB', 'DBX', 'MNDY', 'CYBR', 'FFIV', 'CFLT', 'PCTY', 'MSTR', 'NXT', 'DUOL', 'UI', 'FRSH', 'CGNX', 'BRZE', 'AUR', 'HCP', 'FROG', 'BOX', 'CRDO', 'RUN', 'AI', 'ALRM', 'MQ', 'YOU', 'QTWO', 'NABL', 'BMBL', 'APPN', 'AMBA', 'SWI', 'PAY', 'EVCM', 'CLBT', 'PAYO', 'SEMR', 'AMPL', 'VZIO', 'DCBO', 'PDFS', 'TUYA', 'WKME', 'BTDR', 'RSKD', 'PGY', 'RDWR', 'DMRC', 'YALA', 'CORZ', 'LASR', 'VMEO', 'SCWX', 'ITRN', 'CEVA', 'LAW', 'XPER', 'DOMO', 'NVEC', 'AMSWA', 'EGHT', 'NUKK', 'API', 'CLMB', 'KOPN', 'EGAN', 'VLN', 'AEVA', 'ITI', 'IMMR', 'MAPS', 'AIXI', 'ARBE', 'ZFOX', 'AXTI', 'UEIC', 'WHEN', 'PXPC', 'MKTW', 'SYT', 'NA', 'LINK', 'MOBX', 'ALLT', 'GWSO', 'GSIT', 'DSWL', 'AWRE', 'GUER', 'REFR', 'JFU', 'VHC', 'MSAI', 'SEAV', 'BNZI', 'GOLQ', 'MVLA', 'EBZT', 'INRD', 'JNVR', 'SGN', 'HMBL', 'QURT', 'WLDS', 'MITQ', 'LEDS', 'WETG', 'LIDR', 'NAHD', 'AMST', 'KCRD', 'WDLF', 'ELST', 'FCCN', 'CTKYY', 'WOWI', 'NIRLQ', 'THPTF', 'FALC', 'GSPT', 'TCCO', 'BTZI', 'MJDS', 'SANP', 'SDVI', 'GDLG', 'HMELF', 'TFLM', 'ANKM']


#################
# harvestMasterCSVs(consStaples)  #comms #

# checkYearsIntegritySector(consCyclical)

# write_Master_csv_from_EDGAR('SIMO',ultimateTagsList,'2024','2') #'0000726728'
# write_Master_csv_from_EDGAR('EGP','0000049600',ultimateTagsList,'2024','2')
# write_Master_csv_from_EDGAR('ABR','0001253986',ultimateTagsList,'2024','2')
# for x in incRERecap:
#     nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
#     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
# 
# nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
# print(nameCikDict)

ticker100 = 'ARCC' #ABR
year100 = '2024'
version100 = '2'
# print(consolidateSingleAttribute(ticker100, year100, version100, totalCommonStockDivsPaid, False))
# print(cleanDividends(consolidateSingleAttribute(ticker100, year100, version100, totalCommonStockDivsPaid, False), 
#                                     consolidateSingleAttribute(ticker100, year100, version100, declaredORPaidCommonStockDivsPerShare, False),
#                                     consolidateSingleAttribute(ticker100, year100, version100, basicSharesOutstanding, False)))

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
# print(makeROICtableEntry(ticker12,'2024','0',False))

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

#########################################################

# write_Master_csv_from_EDGAR('AMZN', '0001018724', ultimateTagsList, '2024','0')
#########################################################################################
# for x in yearsOff2:
#     nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
#     write_Master_csv_from_EDGAR(x,ultimateTagsList,'2024','2') #nameCikDict[x],
#There's no overlap! Yay!
# print(set(fullNulls).difference(yearsOff))
# print(set(fullNulls).difference(fullNulls))

# print(set(divsYearsOff).intersection(incYearsOff))
# fullNullOverlap = set(incFullNulls).intersection(divsFullNulls)
# yearsOffOverlap = set(divsYearsOff).intersection(incYearsOff)
# print(fullNullOverlap)
# print(yearsOffOverlap)
# print(set(fullNullOverlap).intersection(yearsOffOverlap))

# print(len(incFullNulls))

#THROW THIS INTO ANALYSIS/METRICS TABLE
        # eps_df = cleanEPS(consolidateSingleAttribute(ticker, year, version, eps, False))
        # print('eps_df df: ')
        # print(eps_df)
        # pluseps = pd.merge(addfcfMargin, eps_df, on=['year','start','end','Ticker','CIK'], how='outer')
        # pluseps['Units'] = pluseps['Units_x']
        # pluseps = pluseps.drop(columns=['Units_x', 'Units_y'])
        # print('pluseps: ')
        # print(pluseps)
        
        #TEST EPS FILLING PRINT EITHER SIDE
        #Put this at the end with a filling function!
        # if pluseps['eps'].isnull().any():
        #         integrity_flag = 'Acceptable'
        #         pluseps['eps'] = pluseps['eps'].replace("", None).ffill()

#---------------------------------------------------------------------
# Things to calculate
#---------------------------------------------------------------------
#payout ratio = divs paid / net income
#ffo/(dividend bulk payment + interest expense) gives idea of how much money remains after paying interest and dividends for reits. aim for ratio > 1
#leverage ratio used by credit rating agencies: Debt / FFO
#---------------------------------------------------------------------

### LUKE
# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm

# debate how to calculate metrics and ratios
#debate how to output it all, or to save it as DF over the years. we'll see. 
#Good work!
###

#---------------------------------------------------------------------
#The testing zone - includes yahoo finance examples
#---------------------------------------------------------------------
# ticker = 'MSFT'
# stock = yf.Ticker(ticker)
# dict1 = stock.info
# marketCap = dict1['marketCap']

# # pe = dict1['pe']
# # for x in dict1:
# #     print(x)
# print(marketCap)

#---------------------------------------------------------------------
#Make files to be called upon
#---------------------------------------------------------------------
# write_Master_csv_from_EDGAR('O','0000726728',ultimateTagsList,'2024','0')
# write_Master_csv_from_EDGAR('MSFT', '0000789019', ultimateTagsList, '2024','0')
# write_to_csv_from_EDGAR('STAG', '0001479094', ultimateTagsList, '2024', '0') #OMG IT WORKS #WIN!
#---------------------------------------------------------------------

#---------------------------------------------------------------------
#DB interaction notes
#---------------------------------------------------------------------
def uploadToDB(table, df):
    return null
##LUKE OK THIS WORKS. need to add it to consolidation: remove useless columns, add an end year where appropriate, then add it all to DB tables. 
# conn = sql.connect(db_path)
# query = conn.cursor()

# q = 'SELECT * FROM Dividends ;'
# query.execute(q)

# df13.to_sql('Revenue',conn, if_exists='replace', index=False) # 'append' adds to DB, more useful for this app. 

# thequery = 'INSERT INTO Revenue (start,end,val,ticker,cik) VALUES ('+str(df13['start'])+',' +str(df13['end'])+',' +df13['val']+',' +df13['ticker']+',' +df13['cik']+');'
# query.execute(thequery)
# conn.commit()


# df12 = pd.DataFrame(query.execute('SELECT * FROM Revenue;'))
# df12 = pd.read_sql('SELECT * FROM Revenue;', conn)
# print(df12)

# query.close()
# conn.close()
#----------------------------------------------------------------------------------------------


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

##drop all except fy records notes
###luke this worked, trying to automate above
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
        
#         if shares.empty:# and total.empty and perShare.empty: #LUKE maybe think about how to fill the shares dataframe. could be a useful tactic. maybe yahoo has a way?
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