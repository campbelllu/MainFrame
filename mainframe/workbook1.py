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

# To retrieve the EDGAR data we’ll define the following function 
# that can both pull down the entire EDGAR database (given enough time), 
# or specific data from a list of tags. 
# We’ll build it around the companyfacts endpoint to give us flexibility 
# in the tags we want returned and reduce the number of API calls. 
# The function will take three arguments: a company CIK, a header dictionary, and a list of tags. 
# If no tags are given, we’ll define the default to return all tags for the given company (the full EDGAR download).

def list_of_tags_EDGAR_query(cik, header, tag: list=None) -> pd.DataFrame:
    url = ep["cf"] + 'CIK' + cik + '.json'
    response = requests.get(url, headers=header)
    print("response: ")
    print(response)

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
            company_data = pd.concat([company_data, data], ignore_index = True)
        except:
            print(tag + ' not found.')
        finally:
            time.sleep(0.1)
        
    return company_data

def single_tag_EDGAR_query(cik, header, tag) -> pd.DataFrame:
    url = ep["cf"] + 'CIK' + cik + '.json'
    response = requests.get(url, headers=header)
    # print("response: ")
    # print(response)

    company_data = pd.DataFrame()

    try:
        units = list(response.json()['facts']['us-gaap'][tag]['units'].keys())[0]
        data = pd.json_normalize(response.json()['facts']['us-gaap'][tag]['units'][units])
        data['Tag'] = tag
        data['Units'] = units
        company_data = pd.concat([company_data, data], ignore_index = True)
    except:
        print(tag + ' not found.')
    finally:
        time.sleep(0.1)
        
    return company_data

#organize data titles into variable lists
revenue = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet']
netIncome = ['NetIncomeLoss']
operatingIncome = ['OperatingIncomeLoss']
taxRate = ['EffectiveIncomeTaxRateContinuingOperations']
altVariables = ['GrossProfit', 'OperatingExpenses', 'IncomeTaxesPaidNet']
shortTermDebt = ['LongTermDebtCurrent']
longTermDebt1 = ['LongTermDebtNoncurrent']
longTermDebt2 = ['OperatingLeaseLiabilityNoncurrent']
totalAssets = ['Assets']
totalLiabilities = ['Liabilities']
operatingCashFlow = ['NetCashProvidedByUsedInOperatingActivities']
capEx = ['PaymentsToAcquirePropertyPlantAndEquipment']
totalCommonStockDivsPaid = ['PaymentsOfDividendsCommonStock']
declaredCommonStockDivsPerShare = ['CommonStockDividendsPerShareDeclared']
paidCommonStockDivsPerShare = ['CommonStockDividendsPerShareCashPaid']
cashOnHand = ['CashCashEquivalentsAndShortTermInvestments']
eps = ['EarningsPerShareBasic']
basicSharesOutstanding = ['WeightedAverageNumberOfSharesOutstandingBasic']

ultimateList = [revenue,netIncome, operatingIncome, taxRate, altVariables, shortTermDebt, longTermDebt1, 
                longTermDebt2, totalAssets, totalLiabilities, operatingCashFlow, capEx, totalCommonStockDivsPaid, 
                declaredCommonStockDivsPerShare, paidCommonStockDivsPerShare, cashOnHand, eps, basicSharesOutstanding]

#make a function that writes csv's based on variable data for each company
### Deprecated with combined below function working for all data gathering, regardless of list size!
# def write_single_stat_to_csv_from_EDGAR(ticker, cik, tag):
#     for i in range(len(tag)):
#         # print(tag[i])
#         # print(i)
#         try:
#             tag_target = tag[i]
#             # print(tag_target)
#             company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
#             company_data['Ticker'] = ticker #'ticker'
#             company_data['CIK'] = cik #'cik' all in brackets
#             csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
#             time.sleep(0.3)
#         except:
#             print('Could not access ' + tag[i] + ".")

# write_single_stat_to_csv_from_EDGAR('MSFT', '0000789019', revenue) #IT WORKS!

#tag must be a list!
def write_to_csv_from_EDGAR(ticker, cik, tag):
    if len(tag) > 1:
        for y in tag:
            if len(y) > 1:
                for z in y:
                    try:
                        tag_target = z
                        # print("try: " + tag_target)
                        company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
                        company_data['Ticker'] = ticker #'ticker'
                        company_data['CIK'] = cik #'cik' all in brackets
                        csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
                        time.sleep(0.3)
                    except:
                        print('Could not access ' + tag_target + ".")
            else:
                try:

                    tag_target = y[0]
                    # print("try: " + tag_target)
                    company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
                    company_data['Ticker'] = ticker #'ticker'
                    company_data['CIK'] = cik #'cik' all in brackets
                    csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
                    time.sleep(0.3)
                except:
                    print('Could not access ' + tag_target + ".")

    else:
        try:
            tag_target = tag[0]
            # print("else: " + tag_target)
            company_data = single_tag_EDGAR_query(cik, header, tag_target) #remember no tags is possible
            company_data['Ticker'] = ticker #'ticker'
            company_data['CIK'] = cik #'cik' all in brackets
            csv.simple_saveDF_to_csv('./sec_related/stocks/', company_data, ticker + '_' + tag_target, False)
            time.sleep(0.3)
        except:
            print('Could not access ' + tag_target + ".")

# write_to_csv_from_EDGAR('MSFT', '0000789019', ultimateList)
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

# print(ultimateList) #aw lawdy
# print(ultimateList[0]) #a list!
# print(ultimateList[0][0]) #a list's content!

#roic = nopat / invested capital
#nopat = operating income * (1-tax rate)
# invested capital = total equity + total debt + non operating cash
#tequity = t assets - t liabilities
#ocf - capex = free cash flow
#fcf margin = fcf / revenue
#payout ratio = divs paid / net income
# modded payout ratio = divs paid / fcf

# To build the data frame, we’ll execute this function 
# by looping over each company in the tickers_CIK dataframe we built above. 
# We added exception handling in the function above so the iterations 
# complete even if a company doesn’t have data for the tag we’re interested in. 
# By iterating through the companies we’ll also be able to ensure we don’t get 
# booted from the API by respecting the rate limit of 1 request every 0.1 seconds. 
# To preserve all our computer’s hard work, we’ll save the dataframe to a csv at the end.

#tickers_cik
# for i in range(math.floor(len(full_cik_list)/10531)):
#     cik = full_cik_list['CIK'][i] #tickers_cik['cik_str'][i]
#     ticker = full_cik_list['Ticker'][i] #tickers_cik['ticker'][i]
#     title = full_cik_list['Company Name'][i] #tickers_cik['title'][i]

#     company_data = EDGAR_query(cik, header,['EarningsPerShareBasic','CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid']) #remember no tags is possible
    
#     company_data['Ticker'] = ticker #'ticker'
#     company_data['Company Name'] = title #'title'
#     company_data['CIK'] = cik #'cik' all in brackets

# #    #Filter for annual data only
#     try:
#         company_data = company_data[company_data['form'].str.contains('10-K') == True] #Keep only annual data
#     except:
#         print('frame not a column.')
    
#     EDGAR_data = pd.concat([EDGAR_data, company_data], ignore_index = True)
#     time.sleep(0.1)

# csv.simple_saveDF_to_csv('./sec_related/', EDGAR_data, 'EDGAR1', False)

###

# Let’s quickly visualize some of the data we just downloaded. 
# As an example we’ll look at quarterly revenues for one of the largest 
# US-based global logistics companies, Expeditors International of Washington Inc. 
# We’ll also clean up the data a bit to make a more readable figure.

# EDGAR_data2 = pd.read_csv('./sec_related/' + 'EDGAR_data' + '.csv')
# EXPD_data = EDGAR_data2[EDGAR_data2['ticker'] == 'EXPD'].copy()
# EXPD_data['frame'] = EXPD_data['frame'].str.replace('CY',"")
# EXPD_data['val_billions'] = EXPD_data['val'] / 1000000000

# sns.set_theme(style='darkgrid')
# fig = sns.lineplot(data=EXPD_data, x='frame', y='val_billions')
# fig.set(xlabel='Quarter', ylabel='Revenue(billions USD)', title='EXPD')
# plt.show()


# testlist = [1,2,3]
# for i in testlist:
#     print(i)
# for i in range(len(testlist)):
#     print(testlist[i])



# f = open('./demoData.txt', 'a')
    # f.write(company_data)
    # f.close()

# f = open('./demoData.txt', 'r')
# print(f.read())