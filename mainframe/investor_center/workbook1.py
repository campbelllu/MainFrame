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
                    units = list(response.json()['facts'][x][tag]['units'].keys())[0]
                    data = pd.json_normalize(response.json()['facts'][x][tag]['units'][units])
                    data['Tag'] = tag
                    data['Units'] = units
                    data['Ticker'] = ticker
                    data['CIK'] = cik
                    company_data = pd.concat([company_data, data], ignore_index = True)
                except Exception as err:
                    # print(str(tags[i]) + ' not found for ' + ticker + ' in ' + x)
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
            'Revenue','RevenueFromContractWithCustomerIncludingAssessedTax','RetainedEarnings']
netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 
                'ProfitLossAttributableToOwnersOfParent','ProfitLoss']
operatingIncome = ['OperatingIncomeLoss','ProfitLossFromOperatingActivities'] #IDK if REITS even have this filed with SEC. Finding it from SEC is hard right now.
taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense','FinanceCosts'] #seems accurate for REITs, not for MSFT. hmmm
incomeTaxPaid = ['IncomeTaxExpenseContinuingOperations']
shortTermDebt = ['LongTermDebtCurrent','ShorttermBorrowings']
longTermDebt1 = ['LongTermDebtNoncurrent','NoncurrentPortionOfNoncurrentBondsIssued']#,'LongTermDebt']
longTermDebt2 = ['OperatingLeaseLiabilityNoncurrent','NoncurrentPortionOfNoncurrentLoansReceived']
longTermDebt3 = ['NoncurrentLeaseLiabilities']
longTermDebt4 = ['LongtermBorrowings']
totalAssets = ['Assets']
totalLiabilities = ['Liabilities']
currentLiabilities = ['LiabilitiesCurrent']
nonCurrentLiabilities = ['LiabilitiesNoncurrent']

exchangeRate = ['EffectOfExchangeRateChangesOnCashAndCashEquivalents'] #LUKE You'll want to know this is here eventually

capEx = ['PaymentsToAcquirePropertyPlantAndEquipment','PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'] #NetCashProvidedByUsedInInvestingActivities # possible addition, questionable
totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends','DividendsCommonStock','DividendsCommonStockCash',
                            'DividendsPaidClassifiedAsFinancingActivities','DividendsPaid'] #DividendsPaid could be useful later
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid']
eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare','BasicEarningsLossPerShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic', 'EntityCommonStockSharesOutstanding','WeightedAverageShares', 'CommonStockSharesOutstanding',
                            'WeightedAverageNumberOfDilutedSharesOutstanding', 'WeightedAverageNumberOfShareOutstandingBasicAndDiluted']#'WeightedAverageShares']
gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes','GainsLossesOnSalesOfInvestmentRealEstate']
deprecAndAmor = ['DepreciationDepletionAndAmortization'] 
deprecAndAmor2 = ['AmortizationOfMortgageServicingRightsMSRs']
deprecAndAmor3 = ['DepreciationAndAmortization']

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, longTermDebt3, longTermDebt4, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow, 
                investingCashFlow, financingCashFlow, exchangeRate, incomeTaxPaid, currentLiabilities, nonCurrentLiabilities, deprecAndAmor2, deprecAndAmor3 ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'exchangeRate', 'longTermDebt3', 'longTermDebt4', 'incomeTaxPaid', 'currentLiabilities','nonCurrentLiabilities',
                'deprecAndAmor2', 'deprecAndAmor3']
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
        cikList = df_full['CIK']
    
        for i in range(len(tickerList)):
            write_Master_csv_from_EDGAR(tickerList[i], cikList[i], ultimateTagsList, '2024', '2')
        
        #full_cik_sectInd_list
        # return null

    except Exception as err:
        print("harvestMasters error: ")
        print(err)

# harvestMasterCSVs(realEstate)

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
        #LUKE PROGRAMMATICALLY GO THRU THIS. combine the three steps into some for loops so it's much less copy paste. you got this!
        #1-6,7,11
        #now we have to iterate through monthly reportings because of some strange reporting practices
        # print('df outside of the if????')
        # print(df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-11-')==True)])
        # if returned_data.empty:
            # print('df in if????')
            # print(df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-11-')==True)])
            #iterate thru revCD to find latest they report, log that number, use it as start to check to the 12th.
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
                ### LUKE. one major thing here is if the only records are montly reported. 
                ### 1-12 nothing? cool, caught it for 1-x, x-12. what about 1-2, 2-3, 3-4... ?
                ### SEe below. this might actually not be an issue. you may just be rusty
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

        

        #Monthly reporting sometimes also throws things off. #luke uncomment
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
    #LUKE drop down to the years columns. hit a run. see the years are kinda weird. figure it out. you got this!
    try:
        # filtered_data = pd.DataFrame()
        # print('pre drop dupes')
        # print(df)
        filtered_data = df
        endYear = []
        endMonth = []
        startYear = []
        # for x in filtered_data: ###LUKE: val in debt and such are floats. they need to be int's or str or other. check which things may need to be floats. deal with them accordingly.
        #     print(x)
        #     print(type(x))
        #     print(type(filtered_data[x].loc[0])) 
        # if filtered_data['end'].isnull().all(): #LUKE just delete these if's ### Why would end ever be empty? 
        #     filtered_data['end'] = filtered_data['end'].fillna(0)
        #     filtered_data['endYear'] = filtered_data['end']#0#'0000-00-00'
        # else:
        for x in filtered_data['end']: #Prep endyear-related for year calc's
            # print(type(filtered_data['end']))
            #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
            endYear.append(int(x[:4]))
            endMonth.append(int(x[5:7]))
            # print(filtered_data)
        filtered_data['endYear'] = endYear
        filtered_data['endMonth'] = endMonth
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
            
            filtered_data['startYear'] = 0#filtered_data['start']#'0000-00-00' #this one
            filtered_data['year'] = filtered_data.end.str[:4].where(filtered_data['endMonth'] == 12, other=filtered_data['yearMinusOne'])
            # print('start null')
            # print(filtered_data)

        else: #Otherwise fill necessary columns for year calc's
            # print('start filled')
            for x in filtered_data['start']:
                #fill list, make col with the list, compare column vals, make new column of trues if they're x-apart
                startYear.append(int(x[:4]))
                # print(filtered_data)
            filtered_data['startYear'] = startYear
            # print('start problem?')
            # print(startYear)
            # print(filtered_data['startYear'])
            ###LUKE TRY LEAVING START EMPTY. EASIER TO CHEKC. LESS ERRORS. MUCH CODE. WOW
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
            filtered_data['year3'] = filtered_data['endYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] >= 6))
            filtered_data['year4'] = filtered_data['startYear'].where((filtered_data['yearDiff'] == 1) & (filtered_data['endMonth'] < 6))
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
        #get csv to df from params
        filtered_data = csv.simple_get_df_from_csv(stock_data, ticker + '_Master_' + year + '_V' + version, indexFlag)
        held_data = pd.DataFrame()
        returned_data = pd.DataFrame()
    
        for x in tagList:
            
            held_data = filtered_data[filtered_data['Tag'].str.contains(x) == True]
            returned_data = pd.concat([returned_data, held_data], ignore_index = True)
            # print(x)
            # if 'PerShare' in x:
            #     print('in consolidate')
            #     print(returned_data)
        returned_data = get_Only_10k_info(returned_data)
        # print(returned_data)
        
        # print('pre drop fy records')
        # print(returned_data.to_string())
        # print(returned_data.shape)
        returned_data = dropAllExceptFYRecords(returned_data) #was held data
        # print('post drop fy records pre order')
        # print(returned_data.to_string())
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
    #Gives error warning of deprecation if there are null values. Filled values produce no warning. LUKE Edit later if necessary due to deprecation error code.
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
        plusLong2['subTotalDebt'] = plusLong2['subTotalDebt'].fillna(0) #Luke omg debt needs to fit together. and i think this block did it. copy paste. let's gooooooo!sss
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

def cleanLiabilities(nonCurrent, current):
    try:
        # nonCurrent['year'] = nonCurrent.end.str[:4]
        # current['year'] = current.end.str[:4]

        # nonCurrent = nonCurrent.drop(columns=['start','end'])
        # current = current.drop(columns=['start','end'])

        anl = pd.merge(nonCurrent, current, on=['year','Ticker','CIK','Units'], how='outer')
        anl['liabilities'] = anl['val_x'] + anl['val_y']
        anl = anl.drop(['val_x','val_y'],axis=1)
        return anl

    except Exception as err:
        print("clean Liabilities error: ")
        print(err)

def cleanTotalEquity(assets, liabilities, nc, cu):
    try:
        #take assets and liabilities and get total equity from them
        # assets['year'] = assets.end.str[:4]
        # liabilities['year'] = liabilities.end.str[:4]

        # assets = assets.drop(columns=['start','end'])
        # liabilities = liabilities.drop(columns=['start','end'])

        if liabilities.empty:
            liabilities = cleanLiabilities(nc, cu)

        #Because Equity is important to calculations, we need to verify non-reported values as being a lower approximation of the mean of all liabilities over time. LUKE RETHINK THIS
        assAndLies = pd.merge(assets, liabilities, on=['year','Ticker','CIK','Units'], how='outer')
        assAndLies['assets'] = assAndLies['val_x']
        assetsMean = assAndLies['assets'].mean() #/ ((len(assAndLies['assets'])/2)+1)
        assAndLies['assets'] = assAndLies['assets'].fillna(assetsMean)
        assAndLies['liabilities'] = assAndLies['val_y']
        liaMean = assAndLies['liabilities'].mean() #/ ((len(assAndLies['liabilities'])/2)+1)
        assAndLies['liabilities'] = assAndLies['liabilities'].fillna(liaMean)
        assAndLies = assAndLies.drop(['val_x','val_y'],axis=1)
        assAndLies['TotalEquity'] = assAndLies['assets']-assAndLies['liabilities']

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
        
        if shares.empty:# and total.empty and perShare.empty:
            cols = {'Units': -1, 'Ticker': -1, 'CIK': -1, 'year': -1, 'totalDivsPaid': -1, 'shares': -1,
                     'divsPaidPerShare': -1, 'sharesGrowthRate': -1, 'divGrowthRate': -1, 'integrityFlag': -1}#, 'Ticker': total['Ticker'] #'interestPaid': -1, 'start': -1, 'end': -1,
            # vals = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
            df_col_added = pd.DataFrame(cols, index=[0])
            return df_col_added
        else:
            sharesNperShare = pd.merge(shares, perShare, on=['year','Ticker','CIK'], how='outer')#'start','end',
            # print('sharesNperShare: ')
            # print(sharesNperShare)
            df_col_added = pd.merge(total, sharesNperShare, on=['year','Ticker','CIK'], how='outer')#'start','end',
            # print('total + shares + per share: ')
            # print(df_col_added)
            df_col_added['shares'] = df_col_added['shares'].replace("", None).ffill().bfill() #any missing shares values?
            # if df_col_added['shares'].empty:
            #     df_col_added['sharesGrowthRate'] = np.NaN
            # else:
            growthCol = grManualCalc(df_col_added['shares'])
            df_col_added['sharesGrowthRate'] = growthCol #df_col_added['shares'].pct_change()*100 #now we can add the growth rate once nulls filled
            # df_col_added['sharesGrowthRate'] = df_col_added['sharesGrowthRate'].replace(np.nan,0) #fill in null values so later filter doesn't break dataset

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

            # df42 = pd.DataFrame()
            # df42['temp'] = df_col_added['tempPerShare']
            # df42['actual'] = df_col_added['divsPaidPerShare']
            # print(df42)

            for x in nanList: #Values in ex-US currencies seem weird versus common stock analysis sites. Could be an exchange rate issue I haven't accounted for in the exchange to USD.
                if x == 'divsPaidPerShare':
                    df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['tempPerShare'])
                    # growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
                    # df_col_added['divGrowthRate'] = growthCol1 
                elif x == 'totalDivsPaid':
                    df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])
                    # growthCol1 = grManualCalc(df_col_added['divsPaidPerShare'])
                    # df_col_added['divGrowthRate'] = growthCol1 
            df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempPerShare'])

            growthCol1 = grManualCalc(df_col_added['totalDivsPaid'])
            df_col_added['divGrowthRateBOT'] = growthCol1 
            growthCol2 = grManualCalc(df_col_added['divsPaidPerShare'])
            df_col_added['divGrowthRateBOPS'] = growthCol2
            
            # if df_col_added['divsPaidPerShares'].empty:
            #     df_col_added['divGrowthRate'] = np.NaN
            # else:
            
            # print('average growth rate: ')
            # print(df_col_added['divGrowthRate'].mean())

            return df_col_added
    except Exception as err:
        print("clean dividends error: ")
        print(err)

def fillEmptyIncomeGrowthRates(df):
    try:
        tarList = ['revenue','netIncome','operatingCashFlow','investingCashFlow','financingCashFlow','netCashFlow', 'capEx','depreNAmor']
        df_filled = df
        fixTracker = 0
        for x in tarList:
            tarGrowthRate = x + 'GrowthRate'
            meanReplacement = df_filled[x].mean()
            savedCol = df_filled[x]
            # df_filled[x] = df_filled[x].replace(np.NaN, meanReplacement)#.ffill() LUKE we trying backfilling instead
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
            print('all shares null')
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
        #     #LUKE MAKE sure this isn't messing up final table once presented
            df_filled['divGrowthRateBOT'] = df_filled['divGrowthRateBOT'].fillna(df_filled.pop('temp2'))#['temp2'])
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)

        if df_filled['divGrowthRateBOPS'].isnull().any():
            growthCol = grManualCalc(df_filled['divsPaidPerShare'])
            df_filled['temp3'] = growthCol
        #     #LUKE MAKE sure this isn't messing up final table once presented
            df_filled['divGrowthRateBOPS'] = df_filled['divGrowthRateBOPS'].fillna(df_filled.pop('temp3'))#['temp2'])
        #     df_filled = df_filled.drop(columns=['temp2'],axis=1)
            # print('div GR')
            # print(df_filled)


        # df_filled = df_filled.drop(columns=['temp1'])
        
        # print('ppost drop shares and div GR')
        # print(df_filled)

        if fixTracker == 4:
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
                                    consolidateSingleAttribute(ticker, year, version, currentLiabilities, False))
        # print('TEquity df')
        # print(totalEquity_df)

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','Ticker','CIK'], how='outer')
        opIncNtaxNinc = pd.merge(opIncNtax, netInc_df, on=['year','Ticker','CIK','Units'], how='outer')
        opIncNtaxNinc = opIncNtaxNinc.drop(columns=['netIncomeGrowthRate'])
        # print('opincntax df')
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
        plustEquity['roce'] = plustEquity['netIncome'] / plustEquity['TotalEquity'] * 100


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

def checkYearsIntegrity(sector):
    try:
        nameCheckList = sector['Ticker']
        nameCikDict = sector.set_index('Ticker')['CIK'].to_dict()
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
                iMissingYears = sorted(set(range(istart,iend)) - set(iyearsint))
                if len(iMissingYears) > 0:
                    incMissingYearTracker.append(x)
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
                dMissingYears = sorted(set(range(dstart,dend)) - set(dyearsint))
                if len(dMissingYears) > 0:
                    dMissingYearTracker.append(x)
                if dend != 2023:
                    dEndYearTracker.append(x)
                if divsTable['interestPaid'].isnull().any():
                    dIntPaid.append(x)
                if divsTable['totalDivsPaid'].isnull().any():
                    dTotalPaid.append(x)
                if divsTable['shares'].isnull().any():
                    dShares.append(x)
                 


                # #make lists of years columns, use to track years
                ryears = list(roicTable['year'])
                ryearsint = []
                for a in ryears:
                    ryearsint.append(int(a))
                rstart, rend = ryearsint[0], ryearsint[-1]
                rMissingYears = sorted(set(range(rstart,rend)) - set(ryearsint))
                if len(rMissingYears) > 0:
                    rMissingYearTracker.append(x)
                if rend != 2023:
                    rEndYearTracker.append(x)
                if roicTable['TotalEquity'].isnull().any():
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
        print('missing income years:')
        print(incMissingYearTracker)
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
        print('missing div years:')
        print(dMissingYearTracker)
        print('wrong div end year')
        print(dEndYearTracker)
        print('missing div intPaid')
        print(dIntPaid)
        print('missing div totalPaid')
        print(dTotalPaid)
        print('missing div shares')
        print(dShares)
        print('missing roic years:')
        print(rMissingYearTracker)
        print('wrong roic end year')
        print(rEndYearTracker)
        print('missing roic total equity')
        print(rTotalEq)
        

def checkTechIncYears():
    try:
        # incomeBadYears = pd.DataFrame(columns=['Ticker', 'Column'])
        # noIncData = pd.DataFrame(columns=['Ticker', 'Column'])
        nameCheckList = tech['Ticker']
        nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
        incYearTracker = []
        incomeNullTracker = []
        toRecapture = []
        yearsList = ['2023','2024'] #2022
        version123 = '2'
        for x in nameCheckList:
            print(x)
            try:
                incTable = makeIncomeTableEntry(x, '2024', version123, False)
                #Checking if returned tables are just empty
                if str(type(incTable)) == "<class 'NoneType'>" or incTable.empty:
                    incomeNullTracker.append(x)
                    continue
                #checking latest data from the pull             
                if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
                    # print(str(x) + ' incYears are good!')
                    incYearTracker.append(x)     
            except Exception as err:
                print("nested check tech years error: ")
                print(err)
                toRecapture.append(x)
                continue                

    except Exception as err:
        print("check tech years error: ")
        print(err)
        # toRecapture.append(x)
        # continue
    finally:
        print('recap list: ')
        print(toRecapture)
        print('full nulls:')
        print(incomeNullTracker)
        print('years off')
        print(incYearTracker)
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

def checkTechDivYears():
    try:
        nameCheckList = tech['Ticker']
        nameCikDict = tech.set_index('Ticker')['CIK'].to_dict()
    
        divYearTracker = []
        divNullTracker = []
        toRecapture = []
        yearsList = ['2023','2024'] #2022
        version123 = '2'

        for x in nameCheckList:
            print(x)
            try:
              
                divsTable = makeDividendTableEntry(x, '2024', version123, False)
                
                #Checking if returned tables are just empty
                # if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
                #     incomeNullTracker.append(x)
                if str(type(divsTable)) == "<class 'NoneType'>" or divsTable.empty:#.empty:
                    divNullTracker.append(x)
                    continue
                #checking latest data from the pull
                if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
                    # print(str(x) + ' divYears are good!')
                    divYearTracker.append(x)                

                # if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
                #     # print(str(x) + ' incYears are good!')
                #     incYearTracker.append(x)     
            except Exception as err:
                print("nested check tech div years error: ")
                print(err)
                toRecapture.append(x)
                continue                

       
    except Exception as err:
        print("check tech years error: ")
        print(err)
        # toRecapture.append(x)
        # continue
    finally:
        # if len(incYearTracker) > 0:
        #     incomeBadYears['Ticker'] = incYearTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

        # if len(divTracker) > 0:
        #     divsBadYears['Ticker']=divTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

        # if len(incomeNullTracker) > 0:
        #     noIncData['Ticker']=incomeNullTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

        # if len(DivNullTracker) > 0:
        #     noDivData['Ticker']=DivNullTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

        # for x in toRecapture:
        #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
        print('recap list: ')
        print(toRecapture)
        print('full nulls:')
        print(divNullTracker)
        print('years off')
        print(divYearTracker)

def checkREIncYears():
    try:
        # incomeBadYears = pd.DataFrame(columns=['Ticker', 'Column'])
        # noIncData = pd.DataFrame(columns=['Ticker', 'Column'])
        nameCheckList = realEstate['Ticker']
        nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
        incYearTracker = []
        incomeNullTracker = []
        toRecapture = []
        yearsList = ['2023','2024'] #2022
        version123 = '2'
        for x in nameCheckList:
            print(x)
            try:
               
                incTable = makeIncomeTableEntry(x, '2024', version123, False)
                #Checking if returned tables are just empty
                if str(type(incTable)) == "<class 'NoneType'>" or incTable.empty:
                    incomeNullTracker.append(x)
                    continue
                #checking latest data from the pull             
                if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
                    # print(str(x) + ' incYears are good!')
                    incYearTracker.append(x)     
            except Exception as err:
                print("nested check realEstate years error: ")
                print(err)
                toRecapture.append(x)
                continue                

    except Exception as err:
        print("check realEstate years error: ")
        print(err)
        # toRecapture.append(x)
        # continue
    finally:
        print('recap list: ')
        print(toRecapture)
        print('full nulls:')
        print(incomeNullTracker)
        print('years off')
        print(incYearTracker)
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

def checkREDivYears():
    try:
        nameCheckList = realEstate['Ticker']
        nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
    
        divYearTracker = []
        divNullTracker = []
        toRecapture = []
        yearsList = ['2023','2024'] #2022
        version123 = '2'

        for x in nameCheckList:
            print(x)
            try:
               
                divsTable = makeDividendTableEntry(x, '2024', version123, False)
                
                #Checking if returned tables are just empty
                # if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
                #     incomeNullTracker.append(x)
                if str(type(divsTable)) == "<class 'NoneType'>" or divsTable.empty:#.empty:
                    divNullTracker.append(x)
                    continue
                #checking latest data from the pull
                if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
                    # print(str(x) + ' divYears are good!')
                    divYearTracker.append(x)                

                # if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
                #     # print(str(x) + ' incYears are good!')
                #     incYearTracker.append(x)     
            except Exception as err:
                print("nested check realEstate div years error: ")
                print(err)
                toRecapture.append(x)
                continue                

       
    except Exception as err:
        print("check realEstate years error: ")
        print(err)
        # toRecapture.append(x)
        # continue
    finally:
        # if len(incYearTracker) > 0:
        #     incomeBadYears['Ticker'] = incYearTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeBadYears, 'techBadYearsIncome', False)

        # if len(divTracker) > 0:
        #     divsBadYears['Ticker']=divTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, divsBadYears, 'techBadYearsDivs', False)

        # if len(incomeNullTracker) > 0:
        #     noIncData['Ticker']=incomeNullTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

        # if len(DivNullTracker) > 0:
        #     noDivData['Ticker']=DivNullTracker
        #     csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

        # for x in toRecapture:
        #     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
        print('recap list: ')
        print(toRecapture)
        print('full nulls:')
        print(divNullTracker)
        print('years off')
        print(divYearTracker)

# checkYearsIntegrity(tech)

# write_Master_csv_from_EDGAR('ACN',ultimateTagsList,'2024','2') #'0000726728'
# write_Master_csv_from_EDGAR('EGP','0000049600',ultimateTagsList,'2024','2')
# write_Master_csv_from_EDGAR('ABR','0001253986',ultimateTagsList,'2024','2')
# for x in incRERecap:
#     nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
#     write_Master_csv_from_EDGAR(x,nameCikDict[x],ultimateTagsList,'2024','2')
# 
# nameCikDict = realEstate.set_index('Ticker')['CIK'].to_dict()
# print(nameCikDict)

ticker100 = 'ACN' #ABR
year100 = '2024'
version100 = '2'
# print(consolidateSingleAttribute(ticker100, year100, version100, currentLiabilities, False))
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

ticker12 = 'NVDA' #ABR
year12 = '2024'
version12 = '2'
# print(ticker12 + ' income:')
# print(makeIncomeTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' divs:')
# print(makeDividendTableEntry(ticker12,'2024',version12,False))
# print(ticker12 + ' roic: ')
# print(makeROICtableEntry(ticker12,'2024',version12,False))

ticker13 = 'MSFT' #EGP
year13 = '2024'
version13 = '2'
# print(ticker13 + ' income:')
# print(makeIncomeTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + ' divs:')
# print(makeDividendTableEntry(ticker13,'2024',version13,False))
# print(ticker13 + '  roic: ')
# print(makeROICtableEntry(ticker13,'2024',version13,False))

ticker12 = 'CRM' #ABR
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

#refined screener results:
#income
REincrecap = ['HLDCY', 'HNGKY', 'VTMX', 'SDHC', 'AIRE', 'LRHC', 'SGD', 'UCASU', 'MSTO', 'PVOZ']
REincmissingyears = ['GRP-UN', 'FOR', 'CBL', 'GMRE', 'NXDT', 'AWCA', 'MHPC', 'TPHS', 'ZDPY', 'ACAN', 'MAA']
REincwrongendyear = ['BEKE', 'SKT', 'SRG', 'PCOK', 'MLP', 'NTPIF', 'OZ', 'STRS', 'SACH', 'KANP', 'CMCT', 'FGNV', 'HWTR', 'AEI', 'SRRE', 
                    'OMH', 'GIPR', 'NYC', 'CMRF', 'LEJU', 'XIN', 'BRST', 'SQFT', 'GYRO', 'MHPC', 'TPHS', 'CRDV', 'MTPP', 'WEWKQ', 'ILAL', 
                    'GBR', 'ALBT', 'CORR', 'VINO', 'WETH', 'DUO', 'PDNLA', 'PW', 'HBUV', 'UK', 'NIHK', 'HCDIQ', 'DPWW', 'SRC', 'SGIC', 'MSPC', 'SFRT']

# print(set(wrong).difference(REincwrongendyear))

techrecap2 =['INTC', 'ARM', 'SHOP', 'ADI', 'TOELY', 'CDNS', 'NXPI', 'ADSK', 'MSI', 'MCHP', 'MRAAY', 'DSCSY', 'ANSS', 'FTV', 'HPQ', 'GRMN', 'PCRFY', 'NTDTY', 'FLT', 'ENTG', 'GDDY', 'MANH', 'NICE', 'AZPN', 'OMRNY', 'ROHCY', 'SAIC', 'ARW', 'CNXC', 'VRNS', 'CRUS', 'ASMVY', 'SEDG', 'BMI', 'CVLT', 'VERX', 'WOLF', 'BDC', 'SANM', 'SRAD', 'ODD', 'PRGS', 'AGYS', 'SIMO', 'ROG', 'VIAV', 'EXTR', 'NATL', 'COHU', 'SPNS', 'TTMI', 'KN', 'SMTC', 'INFN', 'BELFA', 'GB', 'RDWR', 'VMEO', 'ITRN', 'CEVA', 'UIS', 'RDZN', 'DJCO', 'LYTS', 'ABXXF', 'GILT', 'DAKT', 'WBX', 'TCX', 'CRNT', 'RPMT', 'OPTX', 'ARBE', 'EAXR', 'CCRD', 'ELTK', 'ALAR', 'FEBO', 'SPPL', 'GRRR', 'XBP', 'ALLT', 'CSLR', 'NVNI', 'YIBO', 'SMSI', 'DGHI', 'BTQQF', 'KNW', 'MOGO', 'MMTIF', 'MRT', 'AWRE', 'DAIO', 'ITMSF', 'ULY', 'LAES', 'BMR', 'MAPPF', 'CXAI', 'SYNX', 'BOSC', 'ELSE', 'NOWG', 'HLRTF', 'MCLDF', 'JNVR', 'MHUBF', 'PKKFF', 'CAUD', 'VJET', 'SGN', 'SSCC', 'SGE', 'INTZ', 'AMST', 'AWIN', 'SOPA', 'VS', 'IMTE', 'VSOLF', 'AUUD', 'YQAI']
techmissingincomeyears = ['INST', 'LPL', 'WNS', 'BBAI', 'ARAT', 'SURG', 'ZFOX', 'RELL', 'LINK', 'AKTS', 'DPSI', 'FCUV', 'CPTN', 'ALMU', 'INVU', 'SODI', 'AITX', 'HWNI', 'CYCA', 'MTBL', 'APYP', 'SLNH', 'FWFW', 'NUGN', 'INTV']
techwrongendyearincome = ['TSM', 'ORCL', 'SONY', 'INFY', 'SNOW', 'DELL', 'ADSK', 'MCHP', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'PCRFY', 'ASX', 'UMC', 'CHKP', 'IOT', 'NTAP', 'DIDIY', 'DT', 'PSTG', 'NICE', 'PATH', 'GEN', 'LOGI', 'GRAB', 'ESTC', 'GTLB', 'QRVO', 'FLEX', 'DOCU', 'S', 'NXT', 'WIX', 'SAIC', 'YMM', 'SMAR', 'ALGM', 'BRZE', 'STNE', 'CRUS', 'KD', 'HCP', 'PAGS', 'CVLT', 'DXC', 'CAMT', 'NCNO', 'CXM', 'CRDO', 'LPL', 'AI', 'WNS', 'RAMP', 'VSAT', 'AGYS', 'RUM', 'SIMO', 'LSPD', 'AMBA', 'PLUS', 'VRNT', 'BB', 'SPNS', 'NTCT', 'CSIQ', 'BASE', 'JKS', 'SMTC', 'DQ', 'ZUO', 'GCT', 'INFN', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'HIMX', 'BTDR', 'WALD', 'GB', 'PSFE', 'RDWR', 'HKD', 'ASTS', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'SCWX', 'MTWO', 'NNDM', 'SPWR', 'CINT', 'MGIC', 'CGNT', 'ITRN', 'MLAB', 'AEHR', 'TSAT', 'RDZN', 'AUDC', 'DOMO', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'GILT', 'CAN', 'QIWI', 'DAKT', 'EGHT', 'BLZE', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'FRGE', 'API', 'PERF', 'SSTI', 'LUNA', 'MAXN', 'TCX', 'ITI', 'CRNT', 'MIXT', 'WEWA', 'OUST', 'BKSY', 'REKR', 'RPMT', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'QUIK', 'PAYS', 'TIO', 'OPTX', 'MAPS', 'AIXI', 'QBTS', 'LTCH', 'INTT', 'ARBE', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'ELTK', 'FEIM', 'MPTI', 'SOL', 'AUID', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'TYGO', 'ALAR', 'CYRB', 'ONDS', 'LINK', 'BKKT', 'ZEPP', 'MOBX', 'PET', 'EBIXQ', 'PXDT', 'GRRR', 'XBP', 'ALLT', 'BCRD', 'GWSO', 'VLD', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'VERI', 'CSLR', 'POET', 'SNCR', 'EBON', 'DZSI', 'DPSI', 'EGIO', 'GSIT', 'QUBT', 'DGHI', 'KPLT', 'STIX', 'APGT', 'LVER', 'FCUV', 'BTTC', 'RCAT', 'OSS', 'USIO', 'BTCM', 'AGMH', 'APCX', 'CPTN', 'MOGO', 'AISP', 'DSWL', 'MRT', 'QMCO', 'INVU', 'SODI', 'LGL', 'GUER', 'IDN', 'CREX', 'SATX', 'SWVL', 'SCTC', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'DUOT', 'DAIO', 'INLX', 'MFON', 'SONM', 'UTSI', 'WYY', 'WKEY', 'BMTX', 'DTST', 'GETR', 'CLRO', 'MSAI', 'AITX', 'SEAV', 'BNZI', 'RVYL', 'JG', 'SGMA', 'AMPG', 'TAIT', 'CXAI', 'SPI', 'SCND', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'ONEI', 'EBZT', 'FTFT', 'CISO', 'CLOQ', 'MARK', 'PRKR', 'MMAT', 'CTM', 'INRD', 'KULR', 'MTBL', 'ELSE', 'XELA', 'KLDI', 'HUBC', 'SOBR', 'MCLDF', 'IDAI', 'MINM', 'PAYD', 'VSMR', 'CAUD', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'APYP', 'SVRE', 'HTCR', 'UAVS', 'INPX', 'VJET', 'BCAN', 'HMBL', 'ISUN', 'QURT', 'IFBD', 'WATT', 'DPLS', 'WRNT', 'TNLX', 'CRTG', 'BLBX', 'MIND', 'IONI', 'SCKT', 'WETG', 'SLNH', 'VISL', 'LCTC', 'LIDR', 'NAHD', 'JTAI', 'QH', 'NUGN', 'MOB', 'INTZ', 'TSSI', 'ELWS', 'SUIC', 'NXTP', 'EZFL', 'AWIN', 'VIDE', 'OMQS', 'SOPA', 'VMNT', 'SBIG', 'VS', 'IMTE', 'KCRD', 'FRGT', 'SMTK', 'AUUD', 'MICS', 'WDLF', 'WAVD', 'GVP', 'AVOI', 'CAMP', 'SUNW', 'LGIQ']
techmissingrev = ['RDZN', 'NUKK', 'OPTX', 'TYGO', 'ALAR', 'MOBX', 'XBP', 'CSLR', 'HYSR', 'AISP', 'MRT', 'AVAI', 'MSAI', 'BNZI', 'CXAI', 'MVLA', 'VSMR', 'CAUD', 'JTAI', 'AWIN', 'VS', 'NEWH']
techmissingnetincome = ['ALAR', 'MMTIF']
techmissingincomeopCF = ['ALAR', 'XBP', 'MOGO', 'BCAN', 'VS']
techmissingincomecapEx = ['SAP', 'QCOM', 'SONY', 'PANW', 'LRCX', 'WDAY', 'ROP', 'MSI', 'FTNT', 'IT', 'ANSS', 'HPQ', 'GLW', 'NOK', 'HPE', 'DIDIY', 'GRAB', 'JNPR', 'ZI', 'OTEX', 'CACI', 'PSN', 'YMM', 'LYFT', 'ST', 'CLS', 'DAVA', 'VSH', 'WNS', 'ESE', 'BMBL', 'AVDX', 'AGYS', 'RUM', 'SIMO', 'PLUS', 'CTS', 'CRCT', 'EVBG', 'DGII', 'TUYA', 'SCSC', 'BIGC', 'KC', 'MTWO', 'CINT', 'ITRN', 'STEM', 'RDZN', 'VPG', 'APPS', 'NUKK', 'RMNI', 'CLMB', 'BKSY', 'NOTE', 'REKR', 'RPMT', 'SQNS', 'INVE', 'OPTX', 'RELL', 'PHUN', 'PWFL', 'TYGO', 'ALAR', 'CYRB', 'BKKT', 'MOBX', 'XBP', 'AKTS', 'CSLR', 'SMSI', 'LVER', 'APCX', 'HSTA', 'CPTN', 'MOGO', 'ALMU', 'AISP', 'MRT', 'JFU', 'AVAI', 'SOS', 'MSAI', 'SEAV', 'BNZI', 'SGMA', 'CXAI', 'GOLQ', 'MVLA', 'ONEI', 'CLOQ', 'CYCA', 'SOBR', 'VSMR', 'CAUD', 'VJET', 'QURT', 'BOXL', 'JTAI', 'FWFW', 'AWIN', 'VMNT', 'VS', 'DTSS', 'CIIT', 'WDLF', 'AVOI', 'LGIQ']
techmissingincomenetCF = ['SIMO', 'MOGO', 'ONEI', 'VSMR', 'PRST', 'VS']
techmissingincomedepreNAmor = ['MSFT', 'TSM', 'AVGO', 'ORCL', 'SAP', 'INTU', 'INTC', 'IBM', 'TXN', 'SONY', 'LRCX', 'ADI', 'INFY', 'CRWD', 'MRVL', 'STM', 'ZS', 'WIT', 'GFS', 'ANSS', 'GLW', 'CAJPY', 'GIB', 'GRMN', 'PCRFY', 'NOK', 'TDY', 'ASX', 'UMC', 'FLT', 'WDC', 'ERIC', 'DIDIY', 'SWKS', 'OKTA', 'NICE', 'PATH', 'TRMB', 'GRAB', 'ZBRA', 'JKHY', 'DBX', 'ZI', 'QRVO', 'GLOB', 'CFLT', 'COHR', 'GWRE', 'OLED', 'BILL', 'CIEN', 'CACI', 'WIX', 'DSGX', 'FN', 'PSN', 'CCCS', 'G', 'CGNX', 'RMBS', 'STNE', 'CNXC', 'ALIT', 'KD', 'DLO', 'TDC', 'HCP', 'CLS', 'POWI', 'BLKB', 'SLAB', 'BMI', 'PAGS', 'VERX', 'DAVA', 'BOX', 'BL', 'NVEI', 'PYCR', 'INST', 'SPT', 'LPL', 'ALRM', 'LITE', 'DIOD', 'RNG', 'SRAD', 'WNS', 'TIXT', 'PRFT', 'VSAT', 'JAMF', 'AGYS', 'SIMO', 'LSPD', 'IONQ', 'ROG', 'ZETA', 'VIAV', 'UCTT', 'UPBD', 'AMPL', 'CSGS', 'TTMI', 'HLIT', 'MLNK', 'VTEX', 'ADEA', 'DCBO', 'NOVA', 'CRSR', 'BASE', 'JKS', 'DQ', 'ZUO', 'INFN', 'ICHR', 'ETWO', 'INDI', 'NVTS', 'GDS', 'TASK', 'ACMR', 'GDYN', 'IMOS', 'BTDR', 'GB', 'TTEC', 'NYAX', 'HKD', 'DMRC', 'RPAY', 'KARO', 'YALA', 'YEXT', 'AAOI', 'DDD', 'CRNC', 'AOSL', 'VMEO', 'SNPO', 'MTWO', 'NNDM', 'NRDY', 'CINT', 'MGIC', 'AEHR', 'TSAT', 'CEVA', 'XPER', 'RDZN', 'COMM', 'AUDC', 'DOMO', 'APPS', 'BAND', 'CAN', 'QIWI', 'RXT', 'MTLS', 'MTC', 'WBX', 'NUKK', 'PERF', 'BBAI', 'LUNA', 'TCX', 'EGAN', 'VLN', 'AEVA', 'ITI', 'CRNT', 'WEWA', 'LTRX', 'VCSA', 'NOTE', 'MRAM', 'ATGL', 'SQNS', 'QUIK', 'TIO', 'OPTX', 'ARBE', 'ARAT', 'ZFOX', 'MYNA', 'PHUN', 'HOLO', 'MKFG', 'CMBM', 'DHX', 'ALYA', 'LDTC', 'PXPC', 'MPTI', 'SANG', 'ZENV', 'OCFT', 'SYT', 'TYGO', 'ALAR', 'CYRB', 'ARQQ', 'ONDS', 'TACT', 'MOBX', 'GRRR', 'XBP', 'BCRD', 'GMM', 'SPRU', 'CSLR', 'FTCI', 'POET', 'AEYE', 'EBON', 'DZSI', 'QUBT', 'DGHI', 'STIX', 'APGT', 'LVER', 'FCUV', 'HKIT', 'RCAT', 'OSS', 'USIO', 'AIRG', 'BTCM', 'APCX', 'HSTA', 'CPTN', 'MOGO', 'AISP', 'MMTIF', 'MRT', 'LGL', 'FKWL', 'SATX', 'SWVL', 'ARBB', 'SCTC', 'JFU', 'AVAI', 'BMTX', 'GETR', 'MSAI', 'SCIA', 'SEAV', 'BNZI', 'JG', 'AMPG', 'CXAI', 'SPI', 'GOLQ', 'VIAO', 'MVLA', 'ONEI', 'FTFT', 'CLOQ', 'SKKY', 'CYCA', 'KULR', 'HUBC', 'AHI', 'MCLDF', 'MINM', 'STRC', 'VSMR', 'PRST', 'CAUD', 'LKCO', 'UPYY', 'APYP', 'TURB', 'SVRE', 'HTCR', 'DSNY', 'SDCH', 'VJET', 'BCAN', 'MTEK', 'ISUN', 'QURT', 'IFBD', 'WLDS', 'MITQ', 'CRTG', 'SCKT', 'WETG', 'VISL', 'LCTC', 'LIDR', 'NAHD', 'JTAI', 'QH', 'FWFW', 'MOB', 'OST', 'ELWS', 'TGL', 'EZFL', 'AWIN', 'INTV', 'BBLR', 'VS', 'IMTE', 'VVPR', 'KCRD', 'SMTK', 'CIIT', 'WDLF', 'GVP', 'LGIQ', 'TGCB']
techmissingincomepropsales = []
techmissingdivyears =['WIX', 'VRNS', 'INST', 'LPL', 'WNS', 'HLIT', 'MODN', 'YEXT', 'MVIS', 'DJCO', 'EGHT', 'MTC', 'LUNA', 'KOPN', 'WEWA', 'ATOM', 'EACO', 'ARAT', 'SURG', 'ZFOX', 'RELL', 'PXLW', 'WHEN', 'BCOV', 'RSSS', 'LINK', 'ALLT', 'AKTS', 'AEYE', 'DPSI', 'FCUV', 'CPTN', 'PALT', 'INVU', 'SODI', 'LGL', 'IDN', 'ANY', 'MPAD', 'SCTC', 'NXPL', 'DUOT', 'MFON', 'INSG', 'VHC', 'AITX', 'TSRI', 'HWNI', 'SKKY', 'MMAT', 'CYCA', 'KULR', 'PAYD', 'APYP', 'INPX', 'SDCH', 'GSTX', 'BLIN', 'LEDS', 'SLNH', 'VISL', 'CLRI', 'FWFW', 'SUIC', 'INTV', 'OMQS', 'DTSS', 'CIIT', 'SUNW', 'LGIQ']
techwrongdivendyear = ['TSM', 'ORCL', 'SONY', 'INFY', 'SNOW', 'DELL', 'ADSK', 'MCHP', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'PCRFY', 'ASX', 'UMC', 'CHKP', 'IOT', 'NTAP', 'DIDIY', 'DT', 'PSTG', 'NICE', 'PATH', 'GEN', 'LOGI', 'GRAB', 'ESTC', 'GTLB', 'QRVO', 'FLEX', 'DOCU', 'S', 'NXT', 'DUOL', 'WIX', 'SAIC', 'YMM', 'SMAR', 'ALGM', 'BRZE', 'STNE', 'CRUS', 'KD', 'HCP', 'PAGS', 'CVLT', 'DXC', 'CAMT', 'NCNO', 'CXM', 'CRDO', 'LPL', 'AI', 'YOU', 'WNS', 'RAMP', 'VSAT', 'AGYS', 'RUM', 'SIMO', 'LSPD', 'AMBA', 'PLUS', 'VRNT', 'BB', 'SPNS', 'NTCT', 'CSIQ', 'BASE', 'JKS', 'SMTC', 'DQ', 'ZUO', 'GCT', 'INFN', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'HIMX', 'BTDR', 'WALD', 'PSFE', 'RDWR', 'HKD', 'ASTS', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'SCWX', 'MTWO', 'NNDM', 'SPWR', 'CINT', 'MGIC', 'CGNT', 'ITRN', 'MLAB', 'AEHR', 'TSAT', 'AUDC', 'DOMO', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'GILT', 'CAN', 'QIWI', 'DAKT', 'EGHT', 'BLZE', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'FRGE', 'API', 'PERF', 'SSTI', 'LUNA', 'MAXN', 'TCX', 'ITI', 'CRNT', 'MIXT', 'WEWA', 'OUST', 'BKSY', 'REKR', 'RPMT', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'QUIK', 'PAYS', 'TIO', 'MAPS', 'AIXI', 'QBTS', 'LTCH', 'INTT', 'ARBE', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'HOLO', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'ELTK', 'FEIM', 'MPTI', 'SOL', 'AUID', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'TYGO', 'CYRB', 'ONDS', 'LINK', 'BKKT', 'ZEPP', 'MOBX', 'PET', 'EBIXQ', 'PXDT', 'ALLT', 'BCRD', 'GWSO', 'VLD', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'VERI', 'POET', 'SNCR', 'EBON', 'DZSI', 'DPSI', 'EGIO', 'GSIT', 'QUBT', 'KPLT', 'STIX', 'APGT', 'LVER', 'FCUV', 'BTTC', 'RCAT', 'OSS', 'USIO', 'BTCM', 'AGMH', 'APCX', 'HSTA', 'CPTN', 'AISP', 'DSWL', 'QMCO', 'INVU', 'SODI', 'LGL', 'GUER', 'IDN', 'CREX', 'SATX', 'SWVL', 'SCTC', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'DUOT', 'DAIO', 'INLX', 'MFON', 'SONM', 'UTSI', 'WYY', 'WKEY', 'BMTX', 'DTST', 'GETR', 'CLRO', 'MSAI', 'AITX', 'SEAV', 'BNZI', 'RVYL', 'JG', 'SGMA', 'AMPG', 'TAIT', 'SPI', 'SCND', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'ONEI', 'EBZT', 'FTFT', 'CISO', 'CLOQ', 'MARK', 'PRKR', 'MMAT', 'BOSC', 'CTM', 'INRD', 'KULR', 'MTBL', 'ELSE', 'XELA', 'KLDI', 'HUBC', 'SOBR', 'IDAI', 'MINM', 'PAYD', 'VSMR', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'APYP', 'SVRE', 'HTCR', 'UAVS', 'INPX', 'VJET', 'BCAN', 'HMBL', 'ISUN', 'QURT', 'IFBD', 'WATT', 'DPLS', 'WRNT', 'TNLX', 'CRTG', 'BLBX', 'MIND', 'IONI', 'SCKT', 'WETG', 'SLNH', 'VISL', 'LCTC', 'LIDR', 'NAHD', 'JTAI', 'QH', 'NUGN', 'MOB', 'INTZ', 'TSSI', 'ELWS', 'SUIC', 'NXTP', 'EZFL', 'VIDE', 'OMQS', 'SOPA', 'VMNT', 'SBIG', 'KCRD', 'FRGT', 'SMTK', 'CIIT', 'AUUD', 'MICS', 'WDLF', 'WAVD', 'GVP', 'AVOI', 'CAMP', 'SUNW', 'LGIQ', 'TGCB']
techmissingdivintPaid =['INTU', 'TXN', 'SNOW', 'ADSK', 'MPWR', 'GLW', 'BR', 'ZM', 'CHKP', 'IOT', 'TYL', 'DT', 'EPAM', 'APP', 'MANH', 'AFRM', 'NTNX', 'PATH', 'GEN', 'AZPN', 'GTLB', 'DBX', 'OTEX', 'MNDY', 'CYBR', 'FFIV', 'CFLT', 'PCTY', 'MSTR', 'NXT', 'DUOL', 'UI', 'G', 'FRSH', 'CGNX', 'ARW', 'BRZE', 'VNT', 'AUR', 'HCP', 'NVMI', 'BMI', 'FROG', 'BOX', 'CXM', 'CRDO', 'RUN', 'AI', 'ALRM', 'MQ', 'YOU', 'QTWO', 'NABL', 'BMBL', 'PRFT', 'JAMF', 'APPN', 'RUM', 'SIMO', 'AMBA', 'IONQ', 'SWI', 'ROG', 'PLAB', 'PAY', 'VICR', 'EVCM', 'CLBT', 'PAYO', 'SEMR', 'BB', 'PRO', 'AMPL', 'SPNS', 'VZIO', 'AVPT', 'KN', 'GRND', 'ADEA', 'DCBO', 'NOVA', 'CRSR', 'PDFS', 'STER', 'SGH', 'NVTS', 'TUYA', 'GDYN', 'LIFX', 'WKME', 'BTDR', 'RSKD', 'PGY', 'RDWR', 'ASTS', 'DMRC', 'RPAY', 'PUBM', 'YALA', 'MEI', 'CORZ', 'LASR', 'VMEO', 'IIIV', 'SCWX', 'SMRT', 'ITRN', 'CEVA', 'LAW', 'XPER', 'DOMO', 'OSPN', 'NVEC', 'NTGR', 'NLST', 'AMSWA', 'BAND', 'EGHT', 'IBEX', 'NUKK', 'FRGE', 'API', 'CLMB', 'SSTI', 'KOPN', 'TCX', 'EGAN', 'VLN', 'AEVA', 'ITI', 'IMMR', 'MIXT', 'LPSN', 'NOTE', 'INVE', 'MAPS', 'AIXI', 'LTCH', 'UPLD', 'ARBE', 'ZFOX', 'AXTI', 'UEIC', 'CCRD', 'WHEN', 'PXPC', 'MPTI', 'IZM', 'MKTW', 'SYT', 'NA', 'TYGO', 'CYRB', 'LINK', 'BKKT', 'MOBX', 'PET', 'ALLT', 'GWSO', 'MLGO', 'KWIK', 'AKTS', 'FTCI', 'EBON', 'SMSI', 'GSIT', 'QUBT', 'LVER', 'CPTN', 'PALT', 'AISP', 'DSWL', 'AWRE', 'CPSH', 'GUER', 'REFR', 'FKWL', 'JFU', 'AVAI', 'INSG', 'VHC', 'BMR', 'CLPS', 'MSAI', 'SCIA', 'SEAV', 'BNZI', 'GOLQ', 'MVLA', 'EBZT', 'INRD', 'ELSE', 'XELA', 'CYN', 'IDAI', 'STRC', 'HMBL', 'QURT', 'WLDS', 'MITQ', 'WATT', 'BLIN', 'LEDS', 'WETG', 'LIDR', 'NAHD', 'JTAI', 'AMST', 'VMNT', 'SBIG', 'KCRD', 'WDLF', 'GVP', 'TGCB']
techmissdivpaid = []
techmissingdivshares = []
techmissingroicyears = ['EPAM', 'LPL', 'WNS', 'ARAT', 'LINK', 'AKTS', 'DPSI', 'CPTN', 'ALMU', 'SODI', 'AITX', 'FTFT', 'CYCA', 'APYP', 'SLNH', 'FWFW', 'NUGN']
techwrongroicendyear = ['TSM', 'ORCL', 'SONY', 'INFY', 'SNOW', 'DELL', 'ATEYY', 'WIT', 'GFS', 'CAJPY', 'SPLK', 'ASX', 'UMC', 'CHKP', 'IOT', 'NTAP', 'DIDIY', 'DT', 'PSTG', 'PATH', 'GEN', 'LOGI', 'GRAB', 'ESTC', 'GTLB', 'QRVO', 'FLEX', 'DOCU', 'S', 'NXT', 'WIX', 'YMM', 'SMAR', 'ALGM', 'BRZE', 'STNE', 'KD', 'HCP', 'PAGS', 'DXC', 'CAMT', 'NCNO', 'CXM', 'CRDO', 'LPL', 'AI', 'WNS', 'RAMP', 'VSAT', 'RUM', 'LSPD', 'AMBA', 'PLUS', 'VRNT', 'BB', 'NTCT', 'CSIQ', 'BASE', 'JKS', 'DQ', 'ZUO', 'GCT', 'ETWO', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'HIMX', 'BTDR', 'WALD', 'PSFE', 'HKD', 'ASTS', 'KARO', 'YALA', 'MEI', 'DDD', 'KC', 'SCWX', 'MTWO', 'NNDM', 'SPWR', 'CINT', 'MGIC', 'CGNT', 'MLAB', 'AEHR', 'TSAT', 'AUDC', 'DOMO', 'VNET', 'NVEC', 'APPS', 'AMSWA', 'CAN', 'QIWI', 'EGHT', 'BLZE', 'MTLS', 'MTC', 'TGAN', 'NUKK', 'FRGE', 'API', 'PERF', 'SSTI', 'LUNA', 'MAXN', 'ITI', 'MIXT', 'WEWA', 'OUST', 'BKSY', 'REKR', 'WRAP', 'VOXX', 'TROO', 'SQNS', 'QUIK', 'PAYS', 'TIO', 'MAPS', 'AIXI', 'QBTS', 'LTCH', 'INTT', 'ARAT', 'MYNA', 'RELL', 'ALOT', 'PWFL', 'ALYA', 'BEEM', 'VUZI', 'WHEN', 'FEIM', 'MPTI', 'SOL', 'AUID', 'SOTK', 'ZENV', 'OCFT', 'SYT', 'NA', 'TYGO', 'CYRB', 'ONDS', 'LINK', 'BKKT', 'ZEPP', 'MOBX', 'PET', 'EBIXQ', 'PXDT', 'BCRD', 'GWSO', 'VLD', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'VERI', 'POET', 'SNCR', 'EBON', 'DZSI', 'DPSI', 'EGIO', 'GSIT', 'QUBT', 'KPLT', 'STIX', 'APGT', 'LVER', 'FCUV', 'HKIT', 'BTTC', 'RCAT', 'OSS', 'USIO', 'BTCM', 'AGMH', 'APCX', 'CPTN', 'AISP', 'DSWL', 'QMCO', 'INVU', 'SODI', 'LGL', 'GUER', 'IDN', 'CREX', 'SATX', 'SWVL', 'SCTC', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 'DUOT', 'INLX', 'MFON', 'SONM', 'UTSI', 'WYY', 'WKEY', 'BMTX', 'DTST', 'GETR', 'CLRO', 'MSAI', 'AITX', 'SEAV', 'BNZI', 'RVYL', 'JG', 'SGMA', 'AMPG', 'TAIT', 'SPI', 'SCND', 'TSRI', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'ONEI', 'EBZT', 'FTFT', 'CISO', 'CLOQ', 'MARK', 'PRKR', 'MMAT', 'CTM', 'INRD', 'KULR', 'MTBL', 'XELA', 'KLDI', 'HUBC', 'SOBR', 'IDAI', 'MINM', 'PAYD', 'VSMR', 'MSN', 'AIAD', 'LKCO', 'OLB', 'UPYY', 'APYP', 'SVRE', 'HTCR', 'UAVS', 'INPX', 'BCAN', 'HMBL', 'ISUN', 'QURT', 'IFBD', 'WATT', 'DPLS', 'WRNT', 'TNLX', 'CRTG', 'BLBX', 'MIND', 'IONI', 'SCKT', 'WETG', 'SLNH', 'VISL', 'LCTC', 'LIDR', 'NAHD', 'JTAI', 'QH', 'NUGN', 'MOB', 'TSSI', 'ELWS', 'SUIC', 'NXTP', 'EZFL', 'VIDE', 'OMQS', 'VMNT', 'SBIG', 'KCRD', 'FRGT', 'SMTK', 'MICS', 'WDLF', 'WAVD', 'GVP', 'AVOI', 'CAMP', 'SUNW', 'LGIQ']
techmissingroictotalequity = ['VSMR']

print(set(techmissingincomeyears).difference(techmissingroicyears))
#################

TECHincrecap = ['TOELY', 'MRAAY', 'DSCSY', 'NTDTY', 'OMRNY', 'ROHCY', 'ASMVY', 'NATL', 'ABXXF', 'EAXR', 'FEBO', 'SPPL', 'NVNI', 'YIBO', 'BTQQF', 'ITMSF', 
                'ULY', 'LAES', 'MAPPF', 'SYNX', 'NOWG', 'HLRTF', 'JNVR', 'MHUBF', 'PKKFF', 'SGN', 'SSCC', 'SGE', 'VSOLF', 'YQAI', 'VPER', 'SRMX', 'TPPM', 
                'GBUX', 'CMCZ', 'ZICX', 'BCNN', 'FERN', 'SMXT', 'XYLB', 'SELX', 'ATCH', 'WONDF', 'MTMV', 'SWISF', 'DCSX', 'RONN']
TECHincmissingyears = ['CDNS', 'WDAY', 'TDY', 'LDOS', 'TRMB', 'LSCC', 'ONTO', 'LFUS', 'KD', 'SLAB', 'INST', 'LPL', 'WNS', 'TTMI', 'HCKT', 'SPWR', 'NLST', 
                        'TGAN', 'BBAI', 'MAXN', 'QUIK', 'ARAT', 'ZFOX', 'LINK', 'BKKT', 'AKTS', 'DPSI', 'CPTN', 'ALMU', 'SODI', 'AITX', 'CYCA', 'MTBL', 'APYP', 
                        'SLNH', 'FWFW', 'NUGN', 'VEII', 'RKFL', 'LZGI', 'MYSZ', 'CHJI', 'CUEN', 'ONCI', 'PTOS', 'CRCW', 'GAXY', 'IMCI', 'BTZI', 'MJDS']
TECHincwrongendyear = ['NVDA', 'TSM', 'CRM', 'WDAY', 'CRWD', 'MRVL', 'MDB', 'ATEYY', 'GFS', 'CAJPY', 'PCRFY', 'ASX', 'UMC', 'ZM', 'CHKP', 'DIDIY', 'OKTA', 'NICE', 
                        'GRAB', 'WIX', 'DSGX', 'YMM', 'STNE', 'PAGS', 'ASAN', 'BOX', 'CAMT', 'LPL', 'RUM', 'SIMO', 'PD', 'SPNS', 'TTMI', 'CSIQ', 'JKS', 'DQ', 'GCT', 
                        'INFN', 'DBD', 'GDS', 'TUYA', 'IMOS', 'FORTY', 'HIMX', 'BTDR', 'WALD', 'PSFE', 'RDWR', 'HKD', 'ASTS', 'YALA', 'YEXT', 'DDD', 'KC', 'MTWO', 
                        'NNDM', 'CINT', 'MGIC', 'ITRN', 'TSAT', 'RDZN', 'AUDC', 'VNET', 'GILT', 'CAN', 'QIWI', 'BLZE', 'MTLS', 'MTC', 'NUKK', 'FRGE', 'API', 'PERF', 
                        'SSTI', 'LUNA', 'TCX', 'CRNT', 'OUST', 'BKSY', 'REKR', 'RPMT', 'WRAP', 'TROO', 'SQNS', 'PAYS', 'TIO', 'OPTX', 'MAPS', 'AIXI', 'QBTS', 'LTCH', 
                        'INTT', 'ARBE', 'ARAT', 'ZFOX', 'MYNA', 'PWFL', 'BEEM', 'VUZI', 'WHEN', 'ELTK', 'MPTI', 'SOL', 'AUID', 'ZENV', 'OCFT', 'SYT', 'NA', 'TYGO', 
                        'ALAR', 'ONDS', 'LINK', 'BKKT', 'ZEPP', 'MOBX', 'PET', 'EBIXQ', 'GRRR', 'XBP', 'ALLT', 'GWSO', 'VLD', 'MLGO', 'KWIK', 'SPRU', 'RAASY', 'VERI', 
                        'CSLR', 'POET', 'SNCR', 'EBON', 'DZSI', 'DPSI', 'EGIO', 'QUBT', 'DGHI', 'KPLT', 'STIX', 'APGT', 'LVER', 'FCUV', 'BTTC', 'OSS', 'USIO', 'BTCM', 
                        'AGMH', 'APCX', 'CPTN', 'MOGO', 'AISP', 'MRT', 'INVU', 'LGL', 'GUER', 'IDN', 'CREX', 'SATX', 'SWVL', 'SCTC', 'JFU', 'AVAI', 'SOS', 'CASA', 'NXPL', 
                        'DUOT', 'DAIO', 'INLX', 'MFON', 'SONM', 'UTSI', 'WYY', 'WKEY', 'BMTX', 'DTST', 'GETR', 'CLRO', 'MSAI', 'SEAV', 'BNZI', 'RVYL', 'JG', 'AMPG', 'TAIT', 
                        'CXAI', 'SPI', 'SCND', 'HWNI', 'GOLQ', 'VIAO', 'MVLA', 'ONEI', 'FTFT', 'CISO', 'CLOQ', 'MARK', 'PRKR', 'MMAT', 'CTM', 'INRD', 'KULR', 'MTBL', 'ELSE', 
                        'XELA', 'KLDI', 'HUBC', 'SOBR', 'MCLDF', 'IDAI', 'MINM', 'PAYD', 'VSMR', 'CAUD', 'AIAD', 'LKCO', 'OLB', 'APYP', 'SVRE', 'HTCR', 'UAVS', 'INPX', 'VJET', 
                        'BCAN', 'HMBL', 'ISUN', 'QURT', 'IFBD', 'WATT', 'DPLS', 'TNLX', 'CRTG', 'BLBX', 'IONI', 'SCKT', 'WETG', 'SLNH', 'VISL', 'LCTC', 'LIDR', 'NAHD', 'JTAI', 
                        'QH', 'NUGN', 'MOB', 'INTZ', 'TSSI', 'SUIC', 'NXTP', 'EZFL', 'AWIN', 'OMQS', 'SOPA', 'VMNT', 'SBIG', 'VS', 'IMTE', 'FRGT', 'SMTK', 'AUUD', 'WDLF', 'WAVD', 
                        'GVP', 'AVOI', 'SUNW', 'LGIQ', 'VEII', 'ASNS', 'MWRK', 'IPSI', 'DATS', 'VERB', 'WISA', 'SASI', 'DUSYF', 'LZGI', 'ASFT', 'SING', 'XALL', 'VBIX', 'MYSZ', 
                        'UCLE', 'BRQSF', 'ATDS', 'PRSO', 'FCCN', 'CHJI', 'EDGM', 'CUEN', 'CTKYY', 'AEY', 'TWOH', 'PEGY', 'ZRFY', 'SYTA', 'GAHC', 'MLRT', 'WOWI', 'XNDA', 'ONCI', 
                        'ODII', 'PSWW', 'TTCM', 'IGEN', 'TPTW', 'GIGA', 'SATT', 'FLXT', 'WDDD', 'DCLT', 'ITOX', 'CRCW', 'MAPT', 'MCCX', 'NOGNQ', 'AGILQ', 'IINX', 'RDAR', 'GAXY', 
                        'NIRLQ', 'KBNT', 'GTCH', 'TMPOQ', 'ALFIQ', 'TMNA', 'ISGN', 'IMCI', 'DSGT', 'OGBLY', 'NIPNF', 'AUOTY', 'PBTS', 'RBT', 'LCHD', 'AATC', 'EXEO', 'AKOM', 'WSTL', 
                        'CATG', 'WBSR', 'BNSOF', 'EVOL', 'FALC', 'HPTO', 'IPTK', 'VQSSF', 'RBCN', 'TKOI', 'BDRL', 'GSPT', 'ANDR', 'DROP', 'SPYR', 'TCCO', 'EHVVF', 'ABCE', 'BTZI', 
                        'MJDS', 'SMIT', 'SEII', 'XDSL', 'TRIRF', 'SANP', 'ADGO', 'TKLS', 'MAXD', 'SDVI', 'DIGAF', 'HMELF']

#divs


#roic

ticker235 = 'AAPL'
year235 = '2024'
version235 = '2'
# print(ticker235 + ' income:')
# print(makeIncomeTableEntry(ticker235,year235,version235,False))
# print(ticker235 + ' divs:')
# print(makeDividendTableEntry(ticker235,year235,version235,False))
# print(ticker235 + '  roic: ')
# print(makeROICtableEntry(ticker235,year235,version235,False))

# write_Master_csv_from_EDGAR(ticker235,'0000313838',ultimateTagsList,year235,version235)

ticker234 = 'MSFT'
year234 = '2024'
version234 = '2'
# print('MSFT income:')
# print(makeIncomeTableEntry(ticker234,year234,version234,False))
# print('MSFT divs:')
# print(makeDividendTableEntry(ticker234,year234,version234,False))
# print('MSFT roic: ')
# print(makeROICtableEntry(ticker234,year234,version234,False))

# write_Master_csv_from_EDGAR('MSFT', '0000789019', ultimateTagsList, '2024','2')

ticker123 = 'AMZN' #AMZN
year123 = '2024'
version123 = '0'
# print('AMZN income:')
# print(makeIncomeTableEntry(ticker123,'2024',version123,False))
# print('AMZN divs:')
# print(makeDividendTableEntry(ticker123,'2024',version123,False))
# print('AMZN roic: ')
# print(makeROICtableEntry(ticker123,'2024',version123,False))

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

# def dropDuplicatesInDF(df):
#     #LUKE
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