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

# ------------------------------------------
# The above represents organizing ticker data, below is getting company data from API calls to SEC EDGAR.
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
type_converter = {'Ticker': str,'Company Name': str,'CIK': str}
full_cik_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickers_and_ciks', type_converter)
full_cik_sectInd_list = csv.get_df_from_csv_with_typeset(fr_iC_toSEC, 'full_tickersCik_sectorsInd', type_converter)

#Take full cik list and append sector, industry, marketcap info onto it
def updateTickersCiksSectors():
    #'quoteType' might be useful later to verify equity=stock vs etf=etf, uncertain, currently not included
    try:
        df2save = pd.DataFrame(columns=['Ticker','Company Name','CIK','Sector', 'Industry', 'Market Cap'])
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
                marketCap = dict1['marketCap']

                cikList.append(cik)
                tickerList.append(ticker)
                titleList.append(title)
                sectorList.append(sector)
                industryList.append(industry)
                marketCapList.append(marketCap)

                time.sleep(0.1) #As a courtesy to yahoo finance, IDK if they have rate limits and will kick me, also.
            except Exception as err:
                print('try update tickers append lists error: ')
                print('ticker, sector, marketcap: ',ticker,sector,marketCap)
                errorTracker.append(ticker)
                print(err)

            if print_tracker % 10 == 0:
                print("Finished data pull for(ticker, mrktcap): " + ticker + ', ' + str(marketCap))
            
        df2save['Ticker'] = tickerList
        df2save['Company Name'] = titleList
        df2save['CIK'] = cikList
        df2save['Sector'] = sectorList
        df2save['Industry'] = industryList
        df2save['Market Cap'] = marketCapList
        # print(df2save)
        df3 = pd.DataFrame(errorTracker)
        csv.simple_saveDF_to_csv(fr_iC_toSEC, df3, 'badtickers',False)
        csv.simple_saveDF_to_csv(fr_iC_toSEC, df2save, 'full_tickersCik_sectorsInd', False)
    except Exception as err:
        print('update tickerscikssectorsindustry error: ')
        print(err)
# updateTickersCiksSectors()

#gives tags to get from SEC. returns dataframe filled with info!
def EDGAR_query(ticker, cik, header, tag: list=None) -> pd.DataFrame:
    url = ep["cf"] + 'CIK' + cik + '.json'
    response = requests.get(url, headers=header)

    if tag == None:
        tags = list(response.json()['facts']['us-gaap'].keys())
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
            print(str(tags[i]) + ' not found for ' + ticker + '.')
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
netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect'] #operCF + InvestCF + FinancingCF
revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues', 'RealEstateRevenueNet']
netIncome = ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations']
operatingIncome = ['OperatingIncomeLoss'] #IDK if REITS even have this. Finding it from SEC is hard right now.
taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
interestPaid = ['InterestExpense'] #seems accurate for REITs, not for MSFT. hmmm
shortTermDebt = ['LongTermDebtCurrent']
longTermDebt1 = ['LongTermDebtNoncurrent']#,'LongTermDebt']
longTermDebt2 = ['OperatingLeaseLiabilityNoncurrent']
totalAssets = ['Assets']
totalLiabilities = ['Liabilities']
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities']
capEx = ['PaymentsToAcquirePropertyPlantAndEquipment'] #NetCashProvidedByUsedInInvestingActivities # possible addition, questionable
totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock','PaymentsOfDividends']
declaredORPaidCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared','CommonStockDividendsPerShareCashPaid']
eps = ['EarningsPerShareBasic','IncomeLossFromContinuingOperationsPerBasicShare']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic']
gainSaleProperty = ['GainLossOnSaleOfProperties', 'GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnSaleOfPropertiesBeforeApplicableIncomeTaxes']
deprecAndAmor = ['DepreciationDepletionAndAmortization']

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor, netCashFlow ]
ultimateListNames = ['revenue', 'netIncome', 'operatingIncome', 'taxRate', 'interestPaid', 'shortTermDebt', 'longTermDebt1', 
                'longTermDebt2', 'totalAssets', 'totalLiabilities', 'operatingCashFlow', 'capEx', 'totalCommonStockDivsPaid', 
                'declaredORPaidCommonStockDivsPerShare', 'eps', 'basicSharesOutstanding', 'gainSaleProperty', 'deprecAndAmor', 'netCashFlow' ]
# removedFromUltList = [netCashFlow, cashOnHand, altVariables]

ultimateTagsList = [item for sublist in ultimateList for item in sublist]

#Saves (possibly)two different CSV's: The MASTER will contain all company data. All of it! Truncated_Master saves what is most pertinent to current calculations.
def write_Master_csv_from_EDGAR(ticker, cik, tagList, year, version):
    try:
        # company_data_truncated = EDGAR_query(ticker, cik, header, tagList)
        # company_data_full = EDGAR_query(ticker, cik, header)
        company_data = EDGAR_query(ticker, cik, header, tagList)
    except Exception as err:
        print('write to csv from edgar error:')
        print(err)                
    finally:
        csv.simple_saveDF_to_csv(stock_data, company_data, ticker + '_Master_' + year + '_V' + version, False)
        # csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, company_data_truncated, ticker + '_Truncated_Master_' + year + '_V' + version, False)

def get_Only_10k_info(df):
    try:
        filtered_data = pd.DataFrame()
        filtered_data = df[df['form'].str.contains('10-K') == True]
    except Exception as err:
        print("10k filter error")
        print(err)
    finally:
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

#might get deprecated!
def dropDuplicatesInDF_property(df):
    try:
        filtered_data = pd.DataFrame()
        filtered_data = df.drop_duplicates(subset=['val'])
        filtered_data = df.drop_duplicates(subset=['end'], keep='last')
    except Exception as err:
        print("drop duplicates property error")
        print(err)
    finally:
        return filtered_data

def dropAllExceptFYRecords(df):
    try:
        returned_data = df[(df['start'].str.contains('01-01')==True) & (df['end'].str.contains('12-31')==True)]
        if returned_data.empty:
            returned_data = df[(df['start'].str.contains('07-01')==True) & (df['end'].str.contains('06-30')==True)]

        if returned_data.empty:
            return df
        else:
            return returned_data
    except Exception as err:
        print("drop all except FY data rows error")
        print(err)

def dropUselessColumns(df):
    try:
        returned_data = df.drop(['accn','fy','fp','form','filed','frame','Tag','Units'],axis=1)

        # if returned_data.empty:
        #     return df
        # else:
        return returned_data
    except Exception as err:
        print("drop uselss columns error")
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

# write_Master_csv_from_EDGAR('MSFT', '0000789019', ultimateTagsList, '2024','0')
#---------------------------------------------------------------------
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
        # df_col_added['netCashFlowGrowthRate'] = df_col_added['netCashFlow'].pct_change(periods=1)*100
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
        print("clean interestPaid error: ")
        print(err)

#Requires a pre-built DF include OCF and CapEX!!!
def cleanfcf(df):
    try:
        df_col_added = df
        df_col_added['fcf'] = df_col_added['operatingCashFlow'] - df_col_added['capEx']
        df_col_added['fcfGrowthRate'] = df_col_added['fcf'].pct_change()*100

        return df_col_added

    except Exception as err:
        print("clean fcf error: ")
        print(err)

#Requires a pre-built DF including fcf!!!
def cleanfcfMargin(df):
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

def cleanInterestPaid(df):
    try:
        df_col_added = df.rename(columns={'val':'interestPaid'})
        df_col_added['year'] = df_col_added.end.str[:4]

        return df_col_added

    except Exception as err:
        print("clean interestPaid error: ")
        print(err)

#---------------------------------------------------------------------
def makeIncomeTableEntry(ticker, year, version, index_flag):
    try:
        rev_df = cleanRevenue(consolidateSingleAttribute(ticker, year, version, revenue, False))
        netInc_df = cleanNetIncome(consolidateSingleAttribute(ticker, year, version, netIncome, False))
        opcf_df = cleanOperatingCashFlow(consolidateSingleAttribute(ticker, year, version, operatingCashFlow, False))
        netcf_df = cleanNetCashFlow(consolidateSingleAttribute(ticker, year, version, netCashFlow, False))
        capex_df = cleanCapEx(consolidateSingleAttribute(ticker, year, version, capEx, False))
        eps_df = cleanEPS(consolidateSingleAttribute(ticker, year, version, eps, False))
        depAmor_df = cleanDeprNAmor(consolidateSingleAttribute(ticker, year, version, deprecAndAmor, False))

        revNinc = pd.merge(rev_df, netInc_df, on=['year','start','end','Ticker','CIK'], how='outer')
        plusopcf = pd.merge(revNinc, opcf_df, on=['year','start','end','Ticker','CIK'], how='outer')
        plusnetcf = pd.merge(plusopcf, netcf_df, on=['year','start','end','Ticker','CIK'], how='outer')
        pluscapex = pd.merge(plusnetcf, capex_df, on=['year','start','end','Ticker','CIK'], how='outer')
        addfcf = cleanfcf(pluscapex)
        addfcfMargin = cleanfcfMargin(addfcf)
        pluseps = pd.merge(addfcfMargin, eps_df, on=['year','start','end','Ticker','CIK'], how='outer')
        plusDepAmor = pd.merge(pluseps , depAmor_df, on=['year','start','end','Ticker','CIK'], how='outer')


        # ffo = netincomeloss + depr&amor - gainloss sale of property
        return eps_df

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

        return plustEquity

    except Exception as err:
        print("makeROIC table error: ")
        print(err)


#payout ratio = divs paid / net income
# modded payout ratio = divs paid / fcf
# ffo = netincomeloss + depr&amor - gainloss sale of property and it matches their reporting, albeit slightly lower due to minor costs not included/found on sec reportings.
# You almost end up with a bas****ized affo value because of the discrepancy tho!
#ffo/(dividend bulk payment + interest expense) gives idea of how much money remains after paying interest and dividends for reits. aim for ratio > 1

### LUKE
# Need to go through all the filters: look for 'if df is empty' and deprecate it if unnecessary. you got this.
# Fill in NAN values in final income and roic tables. 
# don't lose heart! you can do this! you got this! don't stop! don't quit! get this built and live forever in glory!
# such is the rule of honor: https://youtu.be/q1jrO5PBXvs?si=I-hTTcLSRiNDnBAm
###
# print(makeROICtableEntry('MSFT', '2024', '0', False).shape)
print(makeIncomeTableEntry('O', '2024', '0', False))
# print(cleanDeprNAmor(consolidateSingleAttribute('O', '2024', '0', deprecAndAmor, False)))

#---------------------------------------------------------------------

##LUKE OK THIS WORKS. need to add it to consolidation: remove useless columns, add an end year where appropriate, then add it all to DB tables. 
# conn = sql.connect(db_path)
# query = conn.cursor()

# cleanTotalEquity(consolidateSingleAttribute('MSFT', '2024', '0', totalAssets, False), consolidateSingleAttribute('MSFT', '2024', '0', totalLiabilities, False))

# df14 = consolidateSingleAttribute('MSFT', '2024', '0', shortTermDebt, False)
# print(df14)

# write_Master_csv_from_EDGAR('O','0000726728',ultimateTagsList,'2024','0')

# df13 = cleanDeprNAmor(consolidateSingleAttribute('O', '2024', '0', deprecAndAmor, False))
# print(df13)
# df14 = cleanNetIncome(consolidateSingleAttribute('MSFT', '2024', '0', netIncome, False))
# # print(df14)
# df15 = cleanOperatingCashFlow(consolidateSingleAttribute('MSFT', '2024', '0', operatingCashFlow, False))
# # print(df15)
# df16 = cleanNetCashFlow(consolidateSingleAttribute('MSFT', '2024', '0', netCashFlow, False))
# # print(df16)
# df17 = cleanCapEx(consolidateSingleAttribute('MSFT', '2024', '0', capEx, False))
# # print(df17)
# df18 = cleanEPS(consolidateSingleAttribute('MSFT', '2024', '0', eps, False))
# print(df18)

# print(makeIncomeTableEntry('MSFT', '2024', '0', False))

# df18 = df17['capEx'].tolist()
# print(df18)

# result = pd.merge(df15,df17, on=['year','start','end','Ticker','CIK'], how='outer')
# # result2 = pd.merge(df13,result, on=['year','start','end','Ticker','CIK'])
# # result = pd.merge(df14,df15, on=['year'])
# # result2 = pd.merge(df13,result, on=['year'])
# print(result)
# df18 = cleanfcf(result)
# # result['fcf'] = result['operatingCashFlow']-result['capEx']
# print(df18)
# print(result2)

# dfList = []
# print(df13['end'])

# for x in df13['end']:
#     dfList.append(x[:4])
# #     print(df13['end'][x])
#     # print(x[:4])
# df13.insert(2, 'year', dfList)

# df13.insert(2,'year',dfList)
# print("updated df13")
# print(df13)

# df13.to_sql('Revenue',conn, if_exists='replace',index=False) # 'append' adds to DB, more useful for this app. 

# thequery = 'INSERT INTO Revenue (start,end,val,ticker,cik) VALUES ('+str(df13['start'])+',' +str(df13['end'])+',' +df13['val']+',' +df13['ticker']+',' +df13['cik']+');'
# query.execute(thequery)
# conn.commit()
# df12 = pd.DataFrame(query.execute('SELECT * FROM Revenue;'))

# print(conn)

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

# Consolidate debt into TotalDebt csv
def consolidateDebt(ticker, year): 
    #in DB we use 'year', 'val', ticker, cik, still grabbing that end date
    try:
        dfShortDebt = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_shortTermDebt')
        dfLongDebt1 = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_longTermDebt1')
        dfLongDebt2 = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_longTermDebt2')
        shortDict = {}
        longDict1 = {}
        longDict2 = {}
        for x in range(len(dfShortDebt['end'])):
            shortDict[dfShortDebt['end'][x][:4]] = dfShortDebt['val'][x]
        for y in range(len(dfLongDebt1['end'])):
            longDict1[dfLongDebt1['end'][y][:4]] = dfLongDebt1['val'][y]
        for z in range(len(dfLongDebt2['end'])):
            longDict2[dfLongDebt2['end'][z][:4]] = dfLongDebt2['val'][z]

        totalDebtdict = dict(counter(shortDict) + counter(longDict1) + counter(longDict2))
        tdebtholder = list(totalDebtdict.keys())
        tdebtholder.sort() #make sure the keys(years) are in proper order for easier iteration later
        sortedTotalDebt = {i: totalDebtdict[i] for i in tdebtholder}

        returned_data = pd.DataFrame(sortedTotalDebt.items(), columns=['Year', 'Val'])

        csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_TotalDebt', False)

    except Exception as err:
        print("consolidate debt error: ")
        print(err)

#Consolidate TotalEquity csv
def consolidateEquity(ticker, year):
    #
    try:
        dfAssets = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_totalAssets')
        dfLiabilities = csv.simple_get_df_from_csv(fr_iC_toSEC_stocks, ticker + '_' + year + '_totalLiabilities')
        assetsDict = {}
        liaDict = {}
        for x in range(len(dfAssets['end'])):
            assetsDict[dfAssets['end'][x][:4]] = dfAssets['val'][x]
        for y in range(len(dfLiabilities['end'])):
            liaDict[dfLiabilities['end'][y][:4]] = dfLiabilities['val'][y]

        #If either assets or liabilities are missing each other's matching years, it'll throw off calculations later. Pop them outta' there!
        noMatchingYear1 = []
        noMatchingYear2 = []
        for key in assetsDict:
            if key not in liaDict:
                noMatchingYear1.append(key)
        for key2 in liaDict:
            if key not in assetsDict:
                noMatchingYear2.append(key2)
        for x in noMatchingYear1:
            assetsDict.pop(x,None)
        for y in noMatchingYear2:
            liaDict.pop(y,None)

        totalEquitydict = dict(counter(assetsDict) - counter(liaDict))
        teqholder = list(totalEquitydict.keys())
        teqholder.sort() #make sure the keys(years) are in proper order for easier iteration later
        sortedTotaEquity = {i: totalEquitydict[i] for i in teqholder}

        returned_data = pd.DataFrame(sortedTotaEquity.items(), columns=['Year', 'Val'])

        csv.simple_saveDF_to_csv(fr_iC_toSEC_stocks, returned_data, ticker + '_TotalEquity', False)

    except Exception as err:
        print("consolidate debt error: ")
        print(err)

# Create df -> csv including: operating income, taxRate -> nopat, invested capital, roic 
###
#roic = nopat / invested capital
#nopat = operating income * (1-tax rate)
# invested capital = total equity + total debt 
####


# consolidateEquity('MSFT','2024')
# consolidateDebt('MSFT','2024')

# inputvar = netIncome
# namevar = 'sanityCheck_netIncome'


# Create df -> csv including: operatingCashFlow - capEx -> free cash flow, fcf / rev = fcf margin
# Create df -> csv including: total divs paid, tdp / net income = payout ratio, tdp / fcf = modded payout
# Automate the process of getting cik/ticker list from SEC, via functions, as well as cleaning list and adding sectors in later functions
# Determine Divs/Share 

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
 
# consolidateSingleAttribute('MSFT','2024','0',inputvar, namevar)
# consolidateSingleAttribute('MSFT', '2024','0',netCashFlow,'netCashFlow')
# write_Master_csv_from_EDGAR('MSFT', '0000789019', ultimateTagsList, '2024','0')

# # write_to_csv_from_EDGAR('O','0000726728',ultimateTagsList,'2024','0')
# consolidateAttribute('O','2024','0',inputvar, namevar)

# # write_to_csv_from_EDGAR('STAG','0001479094',ultimateTagsList, '2024','0')
# consolidateAttribute('STAG','2024','0',inputvar, namevar)

# # write_to_csv_from_EDGAR('TXN','0000097476',ultimateTagsList, '2024','0')
# consolidateAttribute('TXN','2024','0',inputvar, namevar)

# consolidateSingleAttribute('TXN','2024','0',inputvar, namevar)

# createAllAttributeFiles('MSFT','2024','0')


#----------------------------------



# dftesterman = dropAllExceptFYRecords(dftesterlady)
# csv.simple_saveDF_to_csv('.sec_related/stocks/', dftesterman,'MSFT_yr_drop',False)

# print(EDGAR_query('MSFT', '0001479094',header,ultimateTagsList))
# print(len(ultimateList))

# write_to_csv_from_EDGAR('STAG', '0001479094', ultimateTagsList, '2024', '0') #OMG IT WORKS #WIN!

### Later when checking what data wasn't gathered:
# csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)



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

### SAVED IN CASE IT BREAKS OVER NIGHT! again. guh.
# #Good working version!
# #tag must be a list! or a list of lists! but no deeper than those two levels!
# def write_to_csv_from_EDGAR(ticker, cik, tag, year, version):
#     if len(tag) > 1:
#         for y in tag:
#             if (str(type(y)) == "<class 'str'>"): 
#                 try:
#                     tag_target = y
#                     company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#                     company_data['Ticker'] = ticker #'ticker'
#                     company_data['CIK'] = cik #'cik' all in brackets
#                     # csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_' + version, False)
#                     time.sleep(0.1)
#                 except:
#                     print('Could not access ' + tag_target + ".")
#                     df_notFound = pd.DataFrame(columns=['Ticker','CIK','Tag'])
#                     df_notFound['Ticker'] = ticker
#                     df_notFound['CIK'] = cik
#                     df_notFound['Tag'] = tag
#                     csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#                 finally:
#                     csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)
                    
#             else:
#                 for z in y:
#                     try:
#                         tag_target = z
#                         company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#                         company_data['Ticker'] = ticker #'ticker'
#                         company_data['CIK'] = cik #'cik' all in brackets
#                         # csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_' + version, False)
#                         time.sleep(0.1)
#                     except:
#                         print('Could not access ' + tag_target + ".")
#                         df_notFound = pd.DataFrame(columns=['Ticker','CIK','Tag'])
#                         df_notFound['Ticker'] = ticker
#                         df_notFound['CIK'] = cik
#                         df_notFound['Tag'] = tag
#                         csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#                     finally:
#                         csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)

#     else:
#         try:
#             tag_target = tag[0]
#             company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#             company_data['Ticker'] = ticker #'ticker'
#             company_data['CIK'] = cik #'cik' all in brackets
#             # csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
#             time.sleep(0.1)
#         except:
#             print('Could not access ' + tag_target + ".")
#             csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#         finally:
#             csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)
#### bad version, but something to start with if it breaks again mysteriously.
# def write_to_csv_from_EDGAR(ticker, cik, tag, year, version):
#     if len(tag) > 1:
#         # print("tag type: " + str(type(tag)))
#         for y in tag:
#             # print("y n type: " + y + ", " +  str(type(y)))
#             if (str(type(y)) == "<class 'str'>"): #if y > 1:
#                 # print("y: " + y)
#                 for z in y:
#                     print("z: " + z)
#                     print("z n  type: " + z+ ", " +  str(type(z)))
#                     try:
#                         tag_target = z
#                         # print("try: " + tag_target)
#                         company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#                         company_data['Ticker'] = ticker #'ticker'
#                         company_data['CIK'] = cik #'cik' all in brackets
#                         # csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_' + version, False)
#                         time.sleep(0.1)
#                     except:
#                         print('Could not access ' + tag_target + ".")
#                         df_notFound = pd.DataFrame(columns=['Ticker','CIK','Tag'])
#                         df_notFound['Ticker'] = ticker
#                         df_notFound['CIK'] = cik
#                         df_notFound['Tag'] = tag
#                         csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#                     finally:
#                         exe = csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)
#             else:
#                 try:

#                     tag_target = y[0]
#                     # print("try: " + tag_target)
#                     company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#                     company_data['Ticker'] = ticker #'ticker'
#                     company_data['CIK'] = cik #'cik' all in brackets
#                     # csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_' + version, False)
#                     # csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
#                     time.sleep(0.1)
#                 except:
#                     print('Could not access ' + tag_target + ".")
#                     df_notFound = pd.DataFrame(columns=['Ticker','CIK','Tag'])
#                     df_notFound['Ticker'] = ticker
#                     df_notFound['CIK'] = cik
#                     df_notFound['Tag'] = tag
#                     csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#                 finally:
#                     exe = csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)

#     else:
#         try:
#             tag_target = tag[0]
#             # print("else: " + tag_target)
#             company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#             company_data['Ticker'] = ticker #'ticker'
#             company_data['CIK'] = cik #'cik' all in brackets
#             # csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
#             time.sleep(0.1)
#         except:
#             print('Could not access ' + tag_target + ".")
#             csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)
#         finally:
#             exe = csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)