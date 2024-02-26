import numpy as np
import pandas as pd
import pandas_datareader.data as web
#docu: https://pandas-datareader.readthedocs.io/en/latest/ 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# %matplotlib inline
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
from itertools import chain

import csv_modules as csv
# import nasdaq_related.nasdaq_list_related as ndl #remove at discretion, how to import modules across project

#Header needed with each request
header = {'User-Agent':'campbelllu3@gmail.com'}

# #Automated pulling of tickers and cik's
# tickers_cik = requests.get('https://www.sec.gov/files/company_tickers.json', headers = header)
# tickers_cik = pd.json_normalize(pd.json_normalize(tickers_cik.json(), max_level=0).values[0])
# tickers_cik['cik_str'] = tickers_cik['cik_str'].astype(str).str.zfill(10)

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

#Set types for each column in df, to retain leading zeroes upon csv -> df loading.
type_converter = {'Ticker': str,'Company Name': str,'CIK': str}
full_cik_list = csv.get_df_from_csv_with_typeset('./sec_related/', 'full_tickers_and_ciks', type_converter)
#csv.simple_get_df_from_csv('./sec_related/', 'full_tickers_and_ciks') #removes leading zeroes from csv tickers. need those for api call. above fixed it.

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
        except:
            print(str(tags[i]) + ' not found for ' + ticker + '.')
        finally:
            time.sleep(0.1)
        
    return company_data

#organizing data titles into variable lists
# altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
# cashOnHand = ['CashCashEquivalentsAndShortTermInvestments', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 
#                 'CashAndCashEquivalentsAtCarryingValue', 'CashEquivalentsAtCarryingValue', 
#                 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations']
# netCashFlow = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect'] #operCF + InvestCF + FinancingCF
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

ultimateList = [revenue, netIncome, operatingIncome, taxRate, interestPaid, shortTermDebt, longTermDebt1, 
                longTermDebt2, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredORPaidCommonStockDivsPerShare, eps, basicSharesOutstanding, gainSaleProperty, deprecAndAmor ]
# removedFromUltList = [netCashFlow, cashOnHand, altVariables]

ultimateTagsList = [item for sublist in ultimateList for item in sublist]

#Good working version! grabs that data, saves it to csv
def write_to_csv_from_EDGAR(ticker, cik, tagList, year, version):
    try:
        company_data = EDGAR_query(ticker, cik, header, tagList) #remember no tags is possible
    except Exception as err:
        print('write to csv has broken')
        print(err)                
    finally:
        csv.simple_appendTo_csv('./sec_related/stocks/', company_data, ticker + '_' + year + '_V' + version, False)

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

# simple_saveDF_to_csv(folder, df, name, index_flag)
def consolidateAttribute(ticker, year, version, tagList, outputVersion):
    try:
        #get csv to df from params
        filtered_data = csv.simple_get_df_from_csv('./sec_related/stocks/',ticker + '_' + year + '_V' + version)
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

        held_data = dropAllExceptFYRecords(returned_data)
        
        csv.simple_saveDF_to_csv('./sec_related/stocks/',held_data, ticker+'_'+'dataFilter'+'_V'+outputVersion,False)
    except Exception as err:
        print(err)

#need to check: declaredORPaidCommonStockDivsPerShare,revenue,netIncome
inputvar = netIncome
namevar = 'netIncome1'

consolidateAttribute('MSFT','2024','0',inputvar, namevar)

# write_to_csv_from_EDGAR('O','0000726728',ultimateTagsList,'2024','0')
consolidateAttribute('O','2024','0',inputvar, namevar)

# write_to_csv_from_EDGAR('STAG','0001479094',ultimateTagsList, '2024','0')
consolidateAttribute('STAG','2024','0',inputvar, namevar)

# write_to_csv_from_EDGAR('TXN','0000097476',ultimateTagsList, '2024','0')
consolidateAttribute('TXN','2024','0',inputvar, namevar)

##LUKE You did so great! Let's crunch some numbers now!


# dftesterman = dropAllExceptFYRecords(dftesterlady)
# csv.simple_saveDF_to_csv('.sec_related/stocks/', dftesterman,'MSFT_yr_drop',False)

# print(EDGAR_query('MSFT', '0001479094',header,ultimateTagsList))
# print(len(ultimateList))

# write_to_csv_from_EDGAR('STAG', '0001479094', ultimateTagsList, '2024', '0') #OMG IT WORKS #WIN!

### Later when checking what data wasn't gathered:
# csv.simple_appendTo_csv('./sec_related/stocks/',df_notFound,ticker+'_NotFoundTags'+'_'+year+'_V'+version,False)

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