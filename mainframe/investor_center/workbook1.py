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

#gives tags to get from SEC. returns dataframe filled with info!
def EDGAR_query(ticker, cik, header, tag: list=None) -> pd.DataFrame:
    url = ep["cf"] + 'CIK' + cik + '.json'
    response = requests.get(url, headers=header)

    if tag == None:
        tags = list(response.json()['facts']['us-gaap'].keys())
        # print('in query tags: ')
        # print(tags)
        if tags.empty or (len(tags) <= 0):
            tags = list(response.json()['facts']['ifrs-full'].keys())
    else:
        tags = tag

    company_data = pd.DataFrame()

    for i in range(len(tags)):
        try:
            tag = tags[i] 
            units = list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
            data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units])
            data['Tag'] = tag
            data['Units'] = units
            data['Ticker'] = ticker
            data['CIK'] = cik
            company_data = pd.concat([company_data, data], ignore_index = True)
        except Exception as err:
            print(str(tags[i]) + ' not found for ' + ticker + ' in US-Gaap.')
            # print("Edgar query error: ")
            # print(err)
        finally:
            time.sleep(0.1)

    if company_data.empty or str(type(company_data)) == "<class 'NoneType'>":
        for i in range(len(tags)):
            try:
                tag = tags[i] 
                units = list(response.json()['facts']['ifrs-full'][tag]['units'].keys())[0]
                data = pd.json_normalize(response.json()['facts']['ifrs-full'][tag]['units'][units])
                data['Tag'] = tag
                data['Units'] = units
                data['Ticker'] = ticker
                data['CIK'] = cik
                company_data = pd.concat([company_data, data], ignore_index = True)
            except Exception as err:
                print(str(tags[i]) + ' not found for ' + ticker + 'in ifrs-full.')
                # print("Edgar query error: ")
                # print(err)
            finally:
                time.sleep(0.1)

    return company_data

#organizing data titles into variable lists
# altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
# cashOnHand = ['CashCashEquivalentsAndShortTermInvestments', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 
#                 'CashAndCashEquivalentsAtCarryingValue', 'CashEquivalentsAtCarryingValue', 
#                 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations']
netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 'IncreaseDecreaseInCashAndCashEquivalents'] #operCF + InvestCF + FinancingCF
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities','CashFlowsFromUsedInOperatingActivities']
investingCashFlow = ['CashFlowsFromUsedInInvestingActivities']
financingCashFlow = ['CashFlowsFromUsedInFinancingActivities']
revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues', 'RealEstateRevenueNet', 'Revenue']
netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 'ProfitLossAttributableToOwnersOfParent']
operatingIncome = ['OperatingIncomeLoss','ProfitLossFromOperatingActivities'] #IDK if REITS even have this filed with SEC. Finding it from SEC is hard right now.
taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense','FinanceCosts'] #seems accurate for REITs, not for MSFT. hmmm
shortTermDebt = ['LongTermDebtCurrent','ShorttermBorrowings']
longTermDebt1 = ['LongTermDebtNoncurrent']#,'LongTermDebt']
longTermDebt2 = ['OperatingLeaseLiabilityNoncurrent']
totalAssets = ['Assets']
totalLiabilities = ['Liabilities']
exchangeRate = ['EffectOfExchangeRateChangesOnCashAndCashEquivalents'] #LUKE You'll want to know this is here eventually

capEx = ['PaymentsToAcquirePropertyPlantAndEquipment','PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'] #NetCashProvidedByUsedInInvestingActivities # possible addition, questionable
totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends','DividendsCommonStock','DividendsCommonStockCash'] #DividendsPaid could be useful later
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid']
eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare','BasicEarningsLossPerShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic', 'EntityCommonStockSharesOutstanding']#'WeightedAverageShares']
gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes']
deprecAndAmor = ['DepreciationDepletionAndAmortization']

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow, 
                investingCashFlow, financingCashFlow, exchangeRate ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow', 
                'investingCashFlow', 'financingCashFlow', 'exchangeRate' ]
# removedFromUltList = [netCashFlow, cashOnHand, altVariables]

ultimateTagsList = [item for sublist in ultimateList for item in sublist]

#Saves MASTER CSV containing data most pertinent to calculations.
def write_Master_csv_from_EDGAR(ticker, cik, tagList, year, version):
    try:
        company_data = EDGAR_query(ticker, cik, header, tagList)
    except Exception as err:
        print('write to csv from edgar error:')
        print(err)                
    finally:
        csv.simple_saveDF_to_csv(stock_data, company_data, ticker + '_Master_' + year + '_V' + version, False)

#Begin data cleaning process
def get_Only_10k_info(df):
    try:
        filtered_data = pd.DataFrame()
        filtered_data = df[df['form'].str.contains('10-K') == True]
        filtered_data1 = df[df['form'].str.contains('20-F') == True] #ADDED FOR ex-US stocks
    except Exception as err:
        print("10k filter error")
        print(err)
    finally:
        if str(type(filtered_data)) == "<class 'NoneType'>" or filtered_data.empty:
            return filtered_data1
        else:
            return filtered_data

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
        filtered_data = pd.DataFrame()
        filtered_data = df.drop_duplicates(subset=['val'])
        filtered_data = df.drop_duplicates(subset=['start','end'], keep='last') #LUKE 'start' may be redundant, we'll see
    except Exception as err:
        print("drop duplicates error")
        print(err)
    finally:
        return filtered_data

def dropAllExceptFYRecords(df):
    try:
        returned_data = df[(df['start'].str.contains('-01-')==True) & (df['end'].str.contains('-12-')==True)] #LUKE Edited dates to include some weird day-files
        if returned_data.empty:
            returned_data = df[(df['start'].str.contains('-07-')==True) & (df['end'].str.contains('-06-')==True)]

        if returned_data.empty:
            return df
        else:
            return returned_data
    except Exception as err:
        print("drop all except FY data rows error")
        print(err)

def dropUselessColumns(df):
    try:
        returned_data = df.drop(['accn','fy','fp','form','filed','frame','Tag'],axis=1)

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
            
        returned_data = get_Only_10k_info(returned_data)
        returned_data = orderAttributeDF(returned_data)

        #LUKE might need to edit this, and the functions above, once we get to them en masse
        # if tagList == gainSaleProperty:# or tagList == revenue:
        #     returned_data = dropDuplicatesInDF_property(returned_data)
        # else:
        #     returned_data = dropDuplicatesInDF(returned_data)
        #In the meantime: bon voyage!
        returned_data = dropDuplicatesInDF(returned_data)
        returned_data = dropAllExceptFYRecords(returned_data) #was held data
        returned_data = dropUselessColumns(returned_data)
        
        # csv.simple_saveDF_to_csv('./sec_related/stocks/',held_data, ticker+'_'+'dataFilter'+'_V'+outputVersion,False)
        # csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_' + year + '_' + outputName,False)
        return returned_data

    except Exception as err:
        print("consolidate single attr error: ")
        print(err)

def cleanRevenue(df):
    try:
        df_col_added = df.rename(columns={'val':'revenue'})
        df_col_added['revGrowthRate'] = df_col_added['revenue'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("cleanRevenue error: ")
        print(err)

def cleanNetIncome(df):
    try:
        df_col_added = df.rename(columns={'val':'netIncome'})
        df_col_added['netIncomeGrowthRate'] = df_col_added['netIncome'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("cleanNetIncome error: ")
        print(err)

def cleanOperatingCashFlow(df):
    try:
        df_col_added = df.rename(columns={'val':'operatingCashFlow'})
        df_col_added['operatingCashFlowGrowthRate'] = df_col_added['operatingCashFlow'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean oper cash flow error: ")
        print(err)

def cleanInvestingCashFlow(df):
    try:
        df_col_added = df.rename(columns={'val':'investingCashFlow'})
        df_col_added['investingCashFlowGrowthRate'] = df_col_added['investingCashFlow'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean investing cash flow error: ")
        print(err)

def cleanFinancingCashFlow(df):
    try:
        df_col_added = df.rename(columns={'val':'financingCashFlow'})
        df_col_added['financingCashFlowGrowthRate'] = df_col_added['financingCashFlow'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean financingCashFlow error: ")
        print(err)

def cleanNetCashFlow(df):
    try:
        df_col_added = df.rename(columns={'val':'netCashFlow'})
        df_col_added['netCashFlowGrowthRate'] = df_col_added['netCashFlow'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean netCashFlow error: ")
        print(err)

def cleanCapEx(df):
    try:
        df_col_added = df.rename(columns={'val':'capEx'})
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean capEx error: ")
        print(err)

def cleanEPS(df):
    try:
        df_col_added = df.rename(columns={'val':'eps'})
        df_col_added['epsGrowthRate'] = df_col_added['eps'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean eps error: ")
        print(err)

def cleanfcf(df): #Requires a pre-built DF include OCF and CapEX!!!
    #Gives error warning of deprecation if there are null values. Filled values produce no warning. LUKE Edit later if necessary due to deprecation.
    try:
        df_col_added = df
        df_col_added['fcf'] = df_col_added['operatingCashFlow'] - df_col_added['capEx']
        df_col_added['fcfGrowthRate'] = df_col_added['fcf'].pct_change()*100

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
        df_col_added['fcfMarginGrowthRate'] = df_col_added['fcfMargin'].pct_change()*100

        return df_col_added

    except Exception as err:
        print("clean fcfMargin error: ")
        print(err)

def cleanOperatingIncome(df):
    try:
        df_col_added = df.rename(columns={'val':'operatingIncome'})
        df_col_added['operatingIncomeGrowthRate'] = df_col_added['operatingIncome'].pct_change()*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanTaxRate(df):
    try:
        df_col_added = df.rename(columns={'val':'taxRate'})
        # df_col_added['taxRateGrowthRate'] = df_col_added['operatingIncome'].pct_change(periods=1)*100
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean operatingIncome error: ")
        print(err)

def cleanDebt(short, long1, long2):
    try:
        #take short, long1, long2 debt, create year column, reproduce df with just year and debt column 
        short['year'] = short.end.str[:4]
        long1['year'] = long1.end.str[:4]
        long2['year'] = long2.end.str[:4]

        shortNlong1 = pd.merge(short, long1, on=['year','start','end','Ticker','CIK'], how='outer')
        shortNlong1['val_x'] = shortNlong1['val_x'].fillna(0)
        shortNlong1['val_y'] = shortNlong1['val_y'].fillna(0)
        shortNlong1['subTotalDebt'] = shortNlong1['val_x'] + shortNlong1['val_y']
        shortNlong1 = shortNlong1.drop(['val_x','val_y'],axis=1)
        
        plusLong2 = pd.merge(shortNlong1, long2, on=['year','start','end','Ticker','CIK'], how='outer')
        plusLong2['val'] = plusLong2['val'].fillna(0)
        plusLong2['TotalDebt'] = plusLong2['subTotalDebt'] + plusLong2['val']
        plusLong2 = plusLong2.drop(['subTotalDebt','val'],axis=1)

        return plusLong2

    except Exception as err:
        print("clean Debt error: ")
        print(err)

def cleanTotalEquity(assets, liabilities):
    try:
        #take assets and liabilities and get total equity from them
        assets['year'] = assets.end.str[:4]
        liabilities['year'] = liabilities.end.str[:4]
        #Because Equity is important to calculations, we need to verify non-reported values as being a lower approximation of the man of all liabilities over time.
        assAndLies = pd.merge(assets, liabilities, on=['year','start','end','Ticker','CIK'], how='outer')
        assAndLies['assets'] = assAndLies['val_x']
        assetsMean = assAndLies['assets'].mean() / len(assAndLies['assets'])
        assAndLies['assets'] = assAndLies['assets'].fillna(assetsMean)
        assAndLies['liabilities'] = assAndLies['val_y']
        liaMean = assAndLies['liabilities'].mean() / len(assAndLies['liabilities'])
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
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added
    except Exception as err:
        print("clean deprNAmor error: ")
        print(err)

def cleanGainSaleProp(df):
    try:
        df_col_added = df.rename(columns={'val':'gainSaleProp'})
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added
    except Exception as err:
        print("clean gainSaleProp error: ")
        print(err)

def cleanInterestPaid(df):
    try:
        df_col_added = df.rename(columns={'val':'interestPaid'})
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean interestPaid error: ")
        print(err)

#ASML case study: shares are working. per share works, but throws off data as nulls are filled because total paid loads fine, but then we try to fill nulls both ways and make a bunch of nulls.
def cleanDividends(total, perShare, shares): 

    try:
        shares['year'] = shares.end.str[:4]
        shares = shares.rename(columns={'val':'shares'})       
        total['year'] = total.end.str[:4]
        total = total.rename(columns={'val':'totalDivsPaid'})
        perShare['year'] = perShare.end.str[:4]
        perShare = perShare.rename(columns={'val':'divsPaidPerShare'})

        sharesNperShare = pd.merge(shares, perShare, on=['year','start','end','Ticker','CIK'], how='outer')
        df_col_added = pd.merge(total, sharesNperShare, on=['year','start','end','Ticker','CIK'], how='outer')
        df_col_added['shares'] = df_col_added['shares'].replace("", None).ffill() #any missing shares values?
        df_col_added['sharesGrowthRate'] = df_col_added['shares'].pct_change()*100 #now we can add the growth rate once nulls filled
        df_col_added['sharesGrowthRate'] = df_col_added['sharesGrowthRate'].replace(np.nan,0) #fill in null values so later filter doesn't break dataset

        df_col_added['divGrowthRate'] = df_col_added['divsPaidPerShare'].pct_change()*100 #This needs to be added after all nan editing
        df_col_added['divGrowthRate'] = df_col_added['divGrowthRate'].replace(np.nan,0)

        integrity_flag = 'Good'

        #first we check for nans
        nanList = []
        for x in df_col_added:
            
            if df_col_added[x].isnull().any():
                integrity_flag = 'Acceptable'
                nanList.append(x)
        #How to handle those empty values in each column
        df_col_added['tempPerShare'] = df_col_added['totalDivsPaid'] / df_col_added['shares']
        df_col_added['tempTotalDivs'] = df_col_added['divsPaidPerShare'] * df_col_added['shares']

        for x in nanList:
            if x == 'divsPaidPerShare':
                df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].fillna(df_col_added['tempPerShare'])#, inplace=True)
                # df_col_added['divsPaidPerShare'] = divsPerShareList
                # df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].replace(np.nan, (df_col_added['totalDivsPaid'] / df_col_added['shares']))
            elif x == 'totalDivsPaid':
                df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].fillna(df_col_added['tempTotalDivs'])#, inplace=True)
                # df_col_added['totalDivsPaid'] = totalDivsList
                # df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].replace(np.nan, (df_col_added['divsPaidPerShare'] * df_col_added['shares']))
        df_col_added = df_col_added.drop(columns=['tempTotalDivs','tempPerShare'])

        # divsPerShareList = df_col_added['totalDivsPaid'] / df_col_added['shares']
        # totalDivsList = df_col_added['divsPaidPerShare'] * df_col_added['shares']
        
        # for x in nanList: 
        #     if x == 'divsPaidPerShare':
        #         df_col_added['divsPaidPerShare'] = divsPerShareList
        #         # df_col_added['divsPaidPerShare'] = df_col_added['divsPaidPerShare'].replace(np.nan, (df_col_added['totalDivsPaid'] / df_col_added['shares']))
        #     elif x == 'totalDivsPaid':
        #         df_col_added['totalDivsPaid'] = totalDivsList
        #         # df_col_added['totalDivsPaid'] = df_col_added['totalDivsPaid'].replace(np.nan, (df_col_added['divsPaidPerShare'] * df_col_added['shares']))
        
        #try filling null values before the following: 
        #then we calculate growth rates per share
        df_col_added['divGrowthRate'] = df_col_added['divsPaidPerShare'].pct_change()*100
        df_col_added['divGrowthRate'] = df_col_added['divGrowthRate'].replace(np.nan,0)

        #Now add a flag to let user know if data is worth looking at
        for x in df_col_added:
            if df_col_added[x].isnull().any():
                integrity_flag = 'Bad'

        df_col_added['integrityFlag'] = integrity_flag

        return df_col_added
    except Exception as err:
        print("clean dividends error: ")
        print(err)

#Making tables for DB insertion
def makeIncomeTableEntry(ticker, year, version, index_flag): #LUKE. this one is working for tsm, broken because microsoft can't find cash flow's. all other table entry functions need work. you got this!
    try:
        integrity_flag = 'Good'
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
        eps_df = cleanEPS(consolidateSingleAttribute(ticker, year, version, eps, False))
        # print('eps_df df: ')
        # print(eps_df)
        depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))
        # print('depAmor_df df: ')
        # print(depAmor_df)
        gainSaleProp_df = cleanGainSaleProp(consolidateSingleAttribute(ticker, year, version, gainSaleProperty, False))
        # print('gainSaleProp_df: ')
        # print(gainSaleProp_df)

        revNinc = pd.merge(rev_df, netInc_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # revNinc['units'] = revNinc['Units_x']
        # revNinc = revNinc.drop(columns=['Units_x', 'Units_y'])
        # print('revNinc: ')
        # print(revNinc)
        plusopcf = pd.merge(revNinc, opcf_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # plusopcf = plusopcf.drop(columns=['units'])
        # print('plusopcf: ')
        # print(plusopcf)
        plusinvcf = pd.merge(plusopcf, invcf_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # plusinvcf['units'] = plusinvcf['Units_x']
        # plusinvcf = plusinvcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusinvcf: ')
        # print(plusinvcf)
        plusfincf = pd.merge(plusinvcf, fincf_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # plusfincf = plusfincf.drop(columns=['units'])
        # print('plusfincf: ')
        # print(plusfincf)

        #fill all the cf's here
        #going to need to fill netcash flow by adding all cf's, similar to how done to fill dividend table!
        if plusopcf['operatingCashFlow'].isnull().any():
                integrity_flag = 'Acceptable'
                plusopcf['operatingCashFlow'].ffill()
        if plusinvcf['investingCashFlow'].isnull().any():
                integrity_flag = 'Acceptable'
                plusinvcf['investingCashFlow'].ffill()
        if plusfincf['financingCashFlow'].isnull().any():
                integrity_flag = 'Acceptable'
                plusfincf['financingCashFlow'].ffill()

        plusnetcf = pd.merge(plusfincf, netcf_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # plusnetcf['units'] = plusnetcf['Units_x']
        # plusnetcf = plusnetcf.drop(columns=['Units_x', 'Units_y'])
        # print('plusnetcf: ')
        # print(plusnetcf)
        #going to need to fill netcash flow by adding all cf's, similar to how done to fill dividend table!

        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # pluscapex = pluscapex.drop(columns=['units'])
        # print('pluscapex: ')
        # print(pluscapex)

        if pluscapex['capEx'].isnull().any():
                integrity_flag = 'Acceptable'
                pluscapex['capEx'] = pluscapex['capEx'].replace("", None).ffill()
        # pluscapex['capEx'] = pluscapex['capEx'].replace("", None).ffill()#.replace(np.nan,method='pad')#.ffill()

        #Cleaning gaps in data due to variable equity filings data seen as .fillna(), above and below
        addfcf = cleanfcf(pluscapex)
        
        addfcfMargin = cleanfcfMargin(addfcf)
        
        pluseps = pd.merge(addfcfMargin, eps_df, on=['year','start','end','Ticker','CIK'], how='outer')
        pluseps['Units'] = pluseps['Units_x']
        pluseps = pluseps.drop(columns=['Units_x', 'Units_y'])
        

        #come back and fill eps with net income / shares for better values-fill
        if pluseps['eps'].isnull().any():
                integrity_flag = 'Acceptable'
                pluseps['eps'] = pluseps['eps'].replace("", None).ffill()

        # if pluseps['epsGrowthRate'].isnull().any():
        #         integrity_flag = 'Acceptable'
        #         pluseps['epsGrowthRate']=pluseps['epsGrowthRate'].replace(np.nan,0)
        pluseps['epsGrowthRate']=pluseps['epsGrowthRate'].replace(np.nan,0)#.method(0)#fillna(0, inplace=True)

        plusDepAmor = pd.merge(pluseps , depAmor_df, on=['year','start','end','Ticker','CIK','Units'], how='outer') #Testing joining on Units
        # plusDepAmor = pluseps.drop(columns=['Units_x', 'Units_y'])
        
        plusSaleProp = pd.merge(plusDepAmor , gainSaleProp_df, on=['year','start','end','Ticker','CIK','Units'], how='outer')
        # print('plusSaleProp: ')
        # print(plusSaleProp)

        # if plusSaleProp['gainSaleProp'].isnull().any():
        #         integrity_flag = 'Acceptable'
        #         plusSaleProp['gainSaleProp']=plusSaleProp['gainSaleProp'].replace(np.nan,0)
        #It's possible that the scraping is just missing sales records, but it's also possible that those years simply had no sales. Keep an eye on analyses later.
        plusSaleProp['gainSaleProp']=plusSaleProp['gainSaleProp'].replace(np.nan,0)#.method(0)#.fillna(0, inplace=True)

        plusSaleProp['ffo'] = plusSaleProp['netIncome'] + plusSaleProp['depreNAmor'] - plusSaleProp['gainSaleProp']
        plusSaleProp['ffoGrowthRate'] = plusSaleProp['ffo'].pct_change()*100
        plusSaleProp['ffoGrowthRate'] = plusSaleProp['ffoGrowthRate'].replace(np.nan,0)

        #To implement this, need to fill leading NaN's for calculated columns
        # for x in plusSaleProp:
        #     if plusSaleProp[x].isnull().any():
        #         integrity_flag = 'Bad'

        plusSaleProp['integrityFlag'] = integrity_flag

        return plusSaleProp

    except Exception as err:
        print("makeIncomeTable error: ")
        print(err)

def makeROICtableEntry(ticker, year, version, index_flag):
    try:
        opIncome_df = cleanOperatingIncome(consolidateSingleAttribute(ticker, year, version, operatingIncome, False))
        taxRate_df = cleanTaxRate(consolidateSingleAttribute(ticker, year, version, taxRate, False))
        totalDebt_df = cleanDebt(consolidateSingleAttribute(ticker, year, version, shortTermDebt, False), 
                                    consolidateSingleAttribute(ticker, year, version, longTermDebt1, False), consolidateSingleAttribute(ticker, year, version, longTermDebt2, False))
        totalEquity_df = cleanTotalEquity(consolidateSingleAttribute(ticker, year, version, totalAssets, False), 
                                    consolidateSingleAttribute(ticker, year, version, totalLiabilities, False))

        opIncNtax = pd.merge(opIncome_df, taxRate_df, on=['year','start','end','Ticker','CIK'], how='outer')
        plustDebt = pd.merge(opIncNtax, totalDebt_df, on=['year','end','Ticker','CIK'], how='outer')
        plustDebt = plustDebt.rename(columns={'start_x': 'start'})
        plustDebt = plustDebt.drop(['start_y'],axis=1)
        plustEquity = pd.merge(plustDebt, totalEquity_df, on=['year', 'end','Ticker','CIK'], how='outer')
        plustEquity = plustEquity.rename(columns={'start_x': 'start'})
        plustEquity = plustEquity.drop(['start_y'],axis=1)
        plustEquity['nopat'] = plustEquity['operatingIncome'] * (1 - plustEquity['taxRate'])
        plustEquity['investedCapital'] = plustEquity['TotalEquity'] + plustEquity['TotalDebt']
        plustEquity['roic'] = plustEquity['nopat'] / plustEquity['investedCapital'] * 100

        #To implement this, need to fill leading NaN's for calculated columns
        #ROIC section nearly impossible to setup Integrity flags for. How do you backfill debt/equity levels? You can just use what you find, honestly.
        # for x in plustEquity:
        #     if plustEquity[x].isnull().any():
        #         integrity_flag = 'Bad'

        return plustEquity

    except Exception as err:
        print("makeROIC table error: ")
        print(err)

def makeDividendTableEntry(ticker, year, version, index_flag): 
    try:
        intPaid_df = cleanInterestPaid(consolidateSingleAttribute(ticker, year, version, interestPaid, False))
        divs_df = cleanDividends(consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, False), 
                                    consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, False),
                                    consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, False))

        # intNshares = pd.merge(intPaid_df, shares_df, on=['year','start','end','Ticker','CIK'], how='outer')
        intNdivs = pd.merge(intPaid_df, divs_df, on=['year','start', 'end','Ticker','CIK'], how='outer')

        return intNdivs
    
    except Exception as err:
        print("makeDividend table error: ")
        print(err)
    
    # print('you got this!')

def makeStockAnalysisTableEntry():
    return null
    #not sure if this should have yearly values, cumulative values, averaged values and given years of average. huh

def harvestMasterCSVs(sectorTarget):
    try:
        df_full = sectorTarget
        tickerList = df_full['Ticker']
        cikList = df_full['CIK']
    
        for i in range(len(tickerList)):
            write_Master_csv_from_EDGAR(tickerList[i], cikList[i], ultimateTagsList, '2024', '0')
        
        #full_cik_sectInd_list
        # return null

    except Exception as err:
        print("harvestMasters error: ")
        print(err)

# harvestMasterCSVs(tech)

def checkTechYears():
    try:
        incomeNoYears = pd.DataFrame(columns=['Ticker'])
        divsNoYears = pd.DataFrame(columns=['Ticker'])
        noIncData = pd.DataFrame(columns=['Ticker'])
        noDivData = pd.DataFrame(columns=['Ticker'])

        nameCheckList = tech['Ticker']
        incTracker = []
        divTracker = []
        IncomeNullTracker = []
        DivNullTracker = []
        for x in nameCheckList:
            incTable = makeIncomeTableEntry(x, '2024', '0', False)
            if str(type(incTable)) == "<class 'NoneType'>" :#.empty:
                IncomeNullTracker.append(x)
                continue

            divsTable = makeDividendTableEntry(x, '2024', '0', False)
            if str(type(divsTable)) == "<class 'NoneType'>":#.empty:
                DivNullTracker.append(x)
                continue

            yearsList = ['2022','2023','2024']

            if (divsTable['year'].max() not in yearsList) or (divsTable['year'].empty):
                # print(str(x) + ' divYears are good!')
                divTracker.append(x)                

            if (incTable['year'].max() not in yearsList) or (incTable['year'].empty):
                # print(str(x) + ' incYears are good!')
                incTracker.append(x)      

        if len(incTracker) > 0:
            incomeNoYears['Ticker']=incTracker
            csv.simple_saveDF_to_csv(fr_iC_toSEC, incomeNoYears, 'techBadYearsIncome', False)

        if len(divTracker) > 0:
            divsNoYears['Ticker']=divTracker
            csv.simple_saveDF_to_csv(fr_iC_toSEC, divsNoYears, 'techBadYearsDivs', False)

        if len(IncomeNullTracker) > 0:
            noIncData['Ticker']=IncomeNullTracker
            csv.simple_saveDF_to_csv(fr_iC_toSEC, noIncData, 'techNoIncomeData', False)

        if len(DivNullTracker) > 0:
            noDivData['Ticker']=DivNullTracker
            csv.simple_saveDF_to_csv(fr_iC_toSEC, noDivData, 'techNoDivData', False)

        
        
    except Exception as err:
        print("check tech years error: ")
        print(err)

# checkTechYears()
ticker123 = 'TSM'
year123 = '2024'
version123 = '0'
# write_Master_csv_from_EDGAR(ticker123,'0001046179',ultimateTagsList,year123,version123)
# write_Master_csv_from_EDGAR('MSFT', '0000789019', ultimateTagsList, '2024','1')
print('income:')
print(makeIncomeTableEntry(ticker123,'2024','0',False))
print('divs:')
print(makeDividendTableEntry(ticker123,'2024','0',False))
print('roic: ')
print(makeROICtableEntry(ticker123,'2024','0',False))

ticker234 = 'MSFT'
year234 = '2024'
version234 = '0'
# print('income:')
# print(makeIncomeTableEntry(ticker234,year234,version234,False))
# print('divs:')
# print(makeDividendTableEntry(ticker234,year234,version234,False))
# print('roic: ')
# print(makeROICtableEntry(ticker234,year234,version234,False))

ticker235 = 'MSFT'
year235 = '2024'
version235 = '1'
# print('income:')
# print(makeIncomeTableEntry(ticker235,year235,version235,False))
# print('divs:')
# print(makeDividendTableEntry(ticker235,year235,version235,False))
# print('roic: ')
# print(makeROICtableEntry(ticker235,year235,version235,False))

# print('total div returns: ')
# print(cleanDividends(consolidateSingleAttribute(ticker123, year123, version123, totalCommonStockDivsPaid, False), 
#                                     consolidateSingleAttribute(ticker123, year123, version123, declaredORPaidCommonStockDivsPerShare, False),
#                                     consolidateSingleAttribute(ticker123, year123, version123, basicSharesOutstanding, False)))
# print('total paid')
# print(consolidateSingleAttribute(ticker123, year123, version123, totalCommonStockDivsPaid, False))
# print('pershare')
# print(consolidateSingleAttribute(ticker123, year123, version123, declaredORPaidCommonStockDivsPerShare, False))
# print('shares')
# print(consolidateSingleAttribute(ticker123, year123, version123, basicSharesOutstanding, False))

#deep dive to find them data's: ONTO, TSM, ASML, CRM, SAP, ARM, SONY, WIX, shop, infy, uctt, ttmi
#newer company: ZI
#dead company: GAHC


def uploadToDB(table, df):
    return null

#tickers_cik
# for i in range(math.floor(len(full_cik_list)/10531)):
#     cik = full_cik_list['CIK'][i] #tickers_cik['cik_str'][i]
#     ticker = full_cik_list['Ticker'][i] #tickers_cik['ticker'][i]
#     title = full_cik_list['Company Name'][i] #tickers_cik['title'][i]
# test
#     company_data = EDGAR_query(cik, header,['EarningsPerShareBasic','CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid']) #remember no tags is possible
    
#     company_data['Ticker'] = ticker #'ticker'
#     company_data['Company Name'] = title #'title'
#     company_data['CIK'] = cik #'cik' all in brackets

# #    #Filter for annual data only
#     try:
#         company_data = company_data[company_data['form'].str.contains('10-K') == True] #Keep only annual data
#     except:
#         print('frame/form not a column.')
    
#     EDGAR_data = pd.concat([EDGAR_data, company_data], ignore_index = True)
#     time.sleep(0.1)

# csv.simple_saveDF_to_csv('./sec_related/', EDGAR_data, 'EDGAR1', False)

#---------------------------------------------------------------------
# Things to calculate
#---------------------------------------------------------------------
#payout ratio = divs paid / net income
#ffo/(dividend bulk payment + interest expense) gives idea of how much money remains after paying interest and dividends for reits. aim for ratio > 1
#---------------------------------------------------------------------

### LUKE
# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm

# debate how to calculate metrics and ratios
#debate how to output it all, or to save it as DF over the years. we'll see. 
#Good work!
###

#---------------------------------------------------------------------
#The testing zone
#---------------------------------------------------------------------
# print(consolidateSingleAttribute('O', '2024', '0', tota, False))

# print('O income: ')
# print(makeIncomeTableEntry('O', '2024', '0', False))
# print('O divs: ')
# print(makeDividendTableEntry('O', '2024', '0', False))
# print('o roic: ')
# print(makeROICtableEntry('O', '2024', '0', False))
# print('MSFT income: ')
# print(makeIncomeTableEntry('MSFT', '2024', '0', False))
# print('msft divs: ')
# print(makeDividendTableEntry('MSFT', '2024', '0', False))
# print('msft roic: ')
# print(makeROICtableEntry('MSFT', '2024', '0', False))

# for x in makeROICtableEntry('MSFT', '2024', '0', False):
#     print(x)
# print(cleanDeprNAmor(consolidateSingleAttribute('O', '2024', '0', deprecAndAmor, False)))

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



#This one is going to be long and arduous: Each tag needs to calculate the final values. longdebt1/2+shortdebt all calc'd, then added together, THEN uploaded to DB as TotalDebt, for example. 
#See models.py for help with each part! you got this!
def createAllAttributesInsertToDB(ticker, year, version):
    try:
        consolidateSingleAttribute(ticker, year, version, revenue, 'revenue')
        consolidateSingleAttribute(ticker, year, version, netIncome, 'netIncome')
        consolidateSingleAttribute(ticker, year, version, operatingIncome,  'operatingIncome')
        consolidateSingleAttribute(ticker, year, version, taxRate, 'taxRate')
        consolidateSingleAttribute(ticker, year, version, interestPaid, 'interestPaid')
        consolidateSingleAttribute(ticker, year, version, shortTermDebt, 'shortTermDebt')
        consolidateSingleAttribute(ticker, year, version, longTermDebt1, 'longTermDebt1')
        consolidateSingleAttribute(ticker, year, version, longTermDebt2, 'longTermDebt2')
        consolidateSingleAttribute(ticker, year, version, totalAssets, 'totalAssets')
        consolidateSingleAttribute(ticker, year, version, totalLiabilities, 'totalLiabilities')
        consolidateSingleAttribute(ticker, year, version, operatingCashFlow, 'operatingCashFlow')
        consolidateSingleAttribute(ticker, year, version, capEx, 'capEx')
        consolidateSingleAttribute(ticker, year, version, totalCommonStockDivsPaid, 'totalCommonStockDivsPaid')
        consolidateSingleAttribute(ticker, year, version, declaredORPaidCommonStockDivsPerShare, 'declaredORPaidCommonStockDivsPerShare')
        consolidateSingleAttribute(ticker, year, version, eps, 'eps')
        consolidateSingleAttribute(ticker, year, version, basicSharesOutstanding, 'basicSharesOutstanding')
        consolidateSingleAttribute(ticker, year, version, gainSaleProperty, 'gainSaleProperty')
        consolidateSingleAttribute(ticker, year, version, deprecAndAmor, 'deprecAndAmor')
        consolidateSingleAttribute(ticker, year, version, netCashFlow, 'netCashFlow')

        ### If anyone can explain to me why this only returns a series of CSV's, all named with the appropriate list-naming, but only containing revenue's values... 
        # ##    There may or may not be a prize involved...
        ###    This is when the function took in a list, the ultimateListNames above, iterated through it to generate csv's. They all contained the same values, however, 
        ###     i would iterate through the appropriate names/titles. Stumped me. So I hard coded the above while crying.
        # for i in tagList:
        #     checker = i
        #     consolidateSingleAttribute(ticker, year, version, checker, checker)
                    
    except Exception as err:
        print("create all error: ")
        print(err)


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