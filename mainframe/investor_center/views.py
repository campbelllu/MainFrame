from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse
from django.db.models import Avg
import numpy as np
import statistics as stats
# from django.template import loader

from .models import Mega, Metadata, Sector_Rankings

# Create your views here.
def index(request):
    return render(request, 'investor_center/index.html', {})
    #HttpResponse('<h1>Welcome to The Investor Center.</h1>')

def valuation(request):
    # luke, i'm not sure how to display this
    # do we want tables, displaying current rankings altogether?
    # etfs could be added at request of the user, that introduces ease of use, minor headaches, but it wouldn't be unmanageable
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    context = {
        'sectors': sectors,
        # 'dv': dropdownValues,
        # 'lt': pageLandingTable,
        }
    return render(request, 'investor_center/valuation.html', context)

def summaryHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    # print(kwargs)
    if ticker is not None:
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        megaDataLength = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        #luke, the following can all be done away with once DB includes profit margin and avg's for it
        profitMarginRev = list(Mega.objects.values_list('revenue', flat=True).filter(Ticker=ticker.upper()))
        profitMarginNI = list(Mega.objects.values_list('netIncome', flat=True).filter(Ticker=ticker.upper()))
        pm = []
        for i in range(0,len(profitMarginNI)-1):
            try:
                pm.append(profitMarginNI[i] / profitMarginRev[i])
            except:
                pm.append(0)
        pmAVG = stats.fmean(pm) * 100

        rreitroenumer = list(Mega.objects.values_list('ffo', flat=True).filter(Ticker=ticker.upper()))
        rreitroedenom = list(Mega.objects.values_list('ReportedTotalEquity', flat=True).filter(Ticker=ticker.upper()))
        pm3 = []
        for i in range(0,len(rreitroenumer)-1):
            try:
                pm3.append(rreitroenumer[i] / rreitroedenom[i])
            except:
                pm3.append(0)
        pmAVG3 = stats.fmean(pm3) * 100

        creitroenumer = list(Mega.objects.values_list('ffo', flat=True).filter(Ticker=ticker.upper()))
        creitroedenom = list(Mega.objects.values_list('TotalEquity', flat=True).filter(Ticker=ticker.upper()))
        pm2 = []
        for i in range(0,len(creitroenumer)-1):
            try:
                pm2.append(creitroenumer[i] / creitroedenom[i])
            except:
                pm2.append(0)
        pmAVG2 = stats.fmean(pm2) * 100
        #above this line and any below context
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
            'pmavg': pmAVG,
            'years': megaDataLength,
            'rreitroe': pmAVG3,
            'creitroe': pmAVG2,
        }
        return render(request, 'investor_center/overview.html', context)
    else:
        print('ticker blank incomehighlights')
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def incomeHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    print('self.kwargs')
    # print(kwargs)
    if ticker is not None:
        print('ticker not blank incomehighlights')
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        #luke, the following can all be done away with once DB includes profit margin and avg's for it
        profitMarginRev = list(Mega.objects.values_list('revenue', flat=True).filter(Ticker=ticker.upper()))
        profitMarginNI = list(Mega.objects.values_list('netIncome', flat=True).filter(Ticker=ticker.upper()))
        pm = []
        for i in range(0,len(profitMarginNI)-1):
            try:
                pm.append(profitMarginNI[i] / profitMarginRev[i])
            except:
                pm.append(0)
        pmAVG = stats.fmean(pm) * 100
        #above this line and any below context
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
            'pmavg': pmAVG,
        }
        return render(request, 'investor_center/incomeDetails.html', context)
    else:
        print('ticker blank incomehighlights')
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def balanceHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    if ticker is not None:
        print('ticker not blank balancehighlights')
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
        }
        return render(request, 'investor_center/balanceDetails.html', context)
    else:
        print('ticker blank balancehighlights')
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def cashflowHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    if ticker is not None:
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
        }
        return render(request, 'investor_center/cfDetails.html', context)
    else:
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def efficiencyHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    if ticker is not None:
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        #luke, the following can all be done away with once DB includes profit margin and avg's for it
        rreitroenumer = list(Mega.objects.values_list('ffo', flat=True).filter(Ticker=ticker.upper()))
        rreitroedenom = list(Mega.objects.values_list('ReportedTotalEquity', flat=True).filter(Ticker=ticker.upper()))
        pm = []
        for i in range(0,len(rreitroenumer)-1):
            try:
                pm.append(rreitroenumer[i] / rreitroedenom[i])
            except:
                pm.append(0)
        pmAVG = stats.fmean(pm) * 100

        creitroenumer = list(Mega.objects.values_list('ffo', flat=True).filter(Ticker=ticker.upper()))
        creitroedenom = list(Mega.objects.values_list('TotalEquity', flat=True).filter(Ticker=ticker.upper()))
        pm2 = []
        for i in range(0,len(creitroenumer)-1):
            try:
                pm2.append(creitroenumer[i] / creitroedenom[i])
            except:
                pm2.append(0)
        pmAVG2 = stats.fmean(pm2) * 100
        #above this line and any below context
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
            'rreitroe': pmAVG,
            'creitroe': pmAVG2,
        }
        return render(request, 'investor_center/effDetails.html', context)
    else:
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def dividendHighlights(request, ticker):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    if ticker is not None:
        megaData = Mega.objects.filter(Ticker=ticker.upper()).order_by('-year')[:10]
        metaData = Metadata.objects.filter(Ticker=ticker.upper())
        context = {
            'sectors': sectors,
            # 'ticker': ticker,
            # 'dv': dropdownValues,
            'dt': ticker.upper(),
            'lt': megaData,
            'mt': metaData,
        }
        return render(request, 'investor_center/divsDetails.html', context)
    else:
        context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
        return render(request, 'investor_center/highlights.html', context)

def highlights(request):
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    # ticker = request.POST.get('ts').upper()

    # if ticker is None:
    #     context = {
    #         'sectors': sectors,
    #         # 'dv': dropdownValues,
    #         # 'lt': pageLandingTable,
    #         }
    #     return render(request, 'investor_center/highlights.html', context)

    if 'ih' in request.POST:
        try:

            return redirect(reverse('ih', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)
        # print('report income clicked')
        # ticker = request.POST.get('ts').upper()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)
        # context = {
        #     'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'dt': ticker,
        #     'lt': megaData,
        #     'mt': metaData,
        #     }
        # return render(request, 'investor_center/incomeDetails.html', context)

    elif 'overh' in request.POST:
        try:
            return redirect(reverse('overh', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)

    elif 'bh' in request.POST:
        try:
            return redirect(reverse('bh', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)
        # ticker = request.POST.get('ts').upper()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)

        # context = {
        #     'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'dt': ticker,
        #     'lt': megaData,
        #     'mt': metaData,
        #     }
        # return render(request, 'investor_center/balanceDetails.html', context)
    
    elif 'cfh' in request.POST:
        try:

            return redirect(reverse('cfh', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)
        # ticker = request.POST.get('ts').upper()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)

        # context = {
        #     'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'dt': ticker,
        #     'lt': megaData,
        #     'mt': metaData,
        #     }
        # return render(request, 'investor_center/cfDetails.html', context)
    
    elif 'effh' in request.POST:
        try:
            return redirect(reverse('effh', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)
        # ticker = request.POST.get('ts').upper()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)
        # # roce = Mega.objects.get('creit_roce_avg')#get_object_or_404(Mega, 'creit_roce_avg')#Mega.objects.get('creit_roce_avg')
        # # roceavg = Mega.objects.aggregate(Avg('ffo' / 'TotalEquity' * 100))

        # context = {
        #     'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'dt': ticker,
        #     'lt': megaData,
        #     'mt': metaData,
        #     # 'roce': roce,
        #     # 'roce': roceavg,
        #     }
        # return render(request, 'investor_center/effDetails.html', context)

    elif 'divsh' in request.POST:
        try:
            return redirect(reverse('divsh', kwargs={'ticker':request.POST.get('ts').upper()}))
        except:
            context = {
            'sectors': sectors,
            # 'dv': dropdownValues,
            # 'lt': pageLandingTable,
            }
            return render(request, 'investor_center/highlights.html', context)
        # ticker = request.POST.get('ts').upper()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)

        # # roce = Mega.objects.get('creit_roce_avg')#get_object_or_404(Mega, 'creit_roce_avg')#Mega.objects.get('creit_roce_avg')
        # # roceavg = Mega.objects.aggregate(Avg('ffo' / 'TotalEquity' * 100))

        # context = {
        #     'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'dt': ticker,
        #     'lt': megaData,
        #     'mt': metaData,
        #     # 'roce': roce,
        #     # 'roce': roceavg,
        #     }
        # return render(request, 'investor_center/divsDetails.html', context)

    # elif ''
    else:
        print('else report view')
        # try:
        #     print('gonna try to get the ticker now')
        #     # ticker = request.POST.get('income').upper()
        #     print(ticker)
        #     print(type(ticker))
        #     render(request, 'investor_center/incomeDetails.html', context)
        #     #luke figure out how to get values into this thing. or pass this view context or something.
        # except Exception as err:
        #     print('report else except')

        # ticker = request.POST.get('ts').upper()
        # try:

        #     ref = request.session.pop('sel')
        #     print('report else if not none')
        #     ticker = ref['income']
        #     megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        #     metaData = Metadata.objects.filter(Ticker=ticker)

        #     context = {
        #         'sectors': sectors,
        #         # 'ticker': ticker,
        #         # 'dv': dropdownValues,
        #         'dt': ticker,
        #         'lt': megaData,
        #         'mt': metaData,
        #         }
        #     return render(request, 'investor_center/incomeDetails.html', context)
        # except Exception as err:
        print('report else else')
        context = {
        'sectors': sectors,
        # 'dv': dropdownValues,
        # 'lt': pageLandingTable,
        }
        return render(request, 'investor_center/highlights.html', context)


def sr(request):
    # topTen = Sector_Rankings.objects.order_by('-scorerank')[:10]
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    # randomSector = Sector_Rankings.objects.values('Sector').order_By('?').first()
    # divpayers = Sector_Rankings.objects.values('divpay').distinct()
    wholeTable = Sector_Rankings.objects.order_by('-scorerank')
    pageLandingTable = Sector_Rankings.objects.order_by('-scorerank')[:25]
    dropdownValues = {'sector':'Select Sector', 'roce':'>=', 'roic':'>=', 'rev':'>=', 'ni':'>=', 'fcf':'>=', 
                        'fcfm':'>=', 'cf':'>=', 'dp':'>=', 'divgr':'>=', 'po':'>=', 'shares':'>=', 'debt':'>=', 
                        'bv':'>=', 'eq':'>=', 'roc':'>=', 'ffo':'>=', 'reitroce':'>=', 'ffopo':'>='}
    tickerToBeFound = "Type Ticker, Hit Enter or Click Button"
    
    #Manual table updates
    if 'updateTable' in request.POST:
        filterSector = request.POST.get('sectorDropDown')
        filterROCE = request.POST.get('vfroce')
        if filterROCE is None or filterROCE == '>=':
            filterROCE = -5
        dropdownValues['roce'] = filterROCE

        filterROIC = request.POST.get('vfroic')
        if filterROIC is None or filterROIC == '>=':
            filterROIC = -5
        dropdownValues['roic'] = filterROIC

        filterREV = request.POST.get('vfrev')
        if filterREV is None or filterREV == '>=':
            filterREV = -5
        dropdownValues['rev'] = filterREV

        filterNI = request.POST.get('vfni')
        if filterNI is None or filterNI == '>=':
            filterNI = -5
        dropdownValues['ni'] = filterNI

        filterFCF = request.POST.get('vffcf')
        if filterFCF is None or filterFCF == '>=':
            filterFCF = -5
        dropdownValues['fcf'] = filterFCF

        filterFCFM = request.POST.get('vffcfm')
        if filterFCFM is None or filterFCFM == '>=':
            filterFCFM = -5
        dropdownValues['fcfm'] = filterFCFM

        filterCF = request.POST.get('vfcf')
        if filterCF is None or filterCF == '>=':
            filterCF = -5
        dropdownValues['cf'] = filterCF

        filterDP = request.POST.get('vfdp')
        if filterDP is None or filterDP == '>=':
            filterDP = -1
        dropdownValues['dp'] = filterDP

        filterDIVGR = request.POST.get('vfdivgr')
        if filterDIVGR is None or filterDIVGR == '>=':
            filterDIVGR = -5
        dropdownValues['divgr'] = filterDIVGR

        filterPO = request.POST.get('vfpo')
        if filterPO is None or filterPO == '>=':
            filterPO = -5
        dropdownValues['po'] = filterPO

        filterSHARES = request.POST.get('vfshares')
        if filterSHARES is None or filterSHARES == '>=':
            filterSHARES = -5
        dropdownValues['shares'] = filterSHARES

        filterDEBT = request.POST.get('vfdebt')
        if filterDEBT is None or filterDEBT == '>=':
            filterDEBT = -5
        dropdownValues['debt'] = filterDEBT

        filterBV = request.POST.get('vfbv')
        if filterBV is None or filterBV == '>=':
            filterBV = -5
        dropdownValues['bv'] = filterBV

        filterEQ = request.POST.get('vfeq')
        if filterEQ is None or filterEQ == '>=':
            filterEQ = -5
        dropdownValues['eq'] = filterEQ

        filterROC = request.POST.get('vfroc')
        if filterROC is None or filterROC == '>=':
            filterROC = -5
        dropdownValues['roc'] = filterROC

        filterFFO = request.POST.get('vfffo')
        if filterFFO is None or filterFFO == '>=':
            filterFFO = -5
        dropdownValues['ffo'] = filterFFO

        filterREITROCE = request.POST.get('vfreitroce')
        if filterREITROCE is None or filterREITROCE == '>=':
            filterREITROCE = -5
        dropdownValues['reitroce'] = filterREITROCE

        filterFFOPO = request.POST.get('vfffopo')
        if filterFFOPO is None or filterFFOPO == '>=':
            filterFFOPO = -5
        dropdownValues['ffopo'] = filterFFOPO

        if filterSector == 'Select Sector':
            context = {
                    'sectors': sectors,
                    'dv': dropdownValues,
                    'lt': pageLandingTable,
                    'tickerToBeFound': tickerToBeFound,
            }
            return render(request, 'investor_center/sectorRankings.html', context)
            
            
        elif filterSector == 'All':
            print('we hitting all now')
            searchFilter = Sector_Rankings.objects.filter(roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)#.order_by('Sector','-scorerank')
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': searchFilter.order_by('-scorerank'),
                'tickerToBeFound': tickerToBeFound,
            }
            return render(request, 'investor_center/sectorRankings.html', context)
        else:
            #luke here: you could have another if filter, if filterSector=='Real Estate', a different table will load, set net income to -5. otherwise, ffo stats
            #would be dropped, 'normal' table displayed
            dropdownValues['sector'] = filterSector
            
            

            searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': searchFilter.order_by('-scorerank'),
                'tickerToBeFound': tickerToBeFound,
            }
            return render(request, 'investor_center/sectorRankings.html', context)

    elif 'resetTable' in request.POST:
        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': pageLandingTable,
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'tsButton' in request.POST:
        ticker = request.POST.get('ts').upper()
        row = Sector_Rankings.objects.filter(Ticker=ticker).first()
        print('what is ticker and row?')
        print(type(ticker))
        print(len(ticker))
        print((ticker))
        # print(type(row))
        # print(len(row))
        # print((row))
        if ticker != '':
            if row is None:
                print('we none row')
                context = {
                    'sectors': sectors,
                    'dv': dropdownValues,
                    'lt': pageLandingTable,
                    'tickerToBeFound': "No Such Ticker, Please Try Again",
                }
                return render(request, 'investor_center/sectorRankings.html', context)
            else:
                filterSector = dropdownValues['sector'] = row.Sector
                filterROCE = dropdownValues['roce'] = row.roce - 2
                filterROIC = dropdownValues['roic'] = row.roic - 2
                filterREV = dropdownValues['rev'] = row.rev - 2
                filterNI = dropdownValues['ni'] = row.ni - 2
                filterFCF = dropdownValues['fcf'] = row.fcf - 2
                filterFCFM = dropdownValues['fcfm'] = row.fcfm - 2
                filterCF = dropdownValues['cf'] = row.cf - 2
                filterDP = dropdownValues['dp'] = row.divpay
                filterDIVGR = dropdownValues['divgr'] = row.divgr - 2
                filterPO = dropdownValues['po'] = row.po - 2
                filterSHARES = dropdownValues['shares'] = row.shares - 2
                filterDEBT = dropdownValues['debt'] = row.debt - 2
                filterBV = dropdownValues['bv'] = row.bv - 2
                filterEQ = dropdownValues['eq'] = row.equity - 2
                filterROC = dropdownValues['roc'] = row.roc - 2
                filterFFO = dropdownValues['ffo'] = row.ffo - 2
                filterREITROCE = dropdownValues['reitroce'] = row.reitroce - 2
                filterFFOPO = dropdownValues['ffopo'] = row.ffopo - 2

                searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                    fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                    shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                    reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

                context = {
                    'sectors': sectors,
                    'dv': dropdownValues,
                    'lt': searchFilter.order_by('-scorerank'),
                    'tickerToBeFound': tickerToBeFound,
                }
                return render(request, 'investor_center/sectorRankings.html', context)

        elif row is None:
            print('we none ticker')
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': pageLandingTable,
                'tickerToBeFound': "No Such Ticker, Please Try Again",
            }
            return render(request, 'investor_center/sectorRankings.html', context)
        else:
            print('else sr')
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': pageLandingTable,
                'tickerToBeFound': tickerToBeFound,
            }
            return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericB' in request.POST:
        filterSector = dropdownValues['sector'] = 'Materials'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 2
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericC' in request.POST:
        filterSector = dropdownValues['sector'] = 'Communications'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 0
        filterNI = dropdownValues['ni'] = 0
        filterFCF = dropdownValues['fcf'] = 0
        filterFCFM = dropdownValues['fcfm'] = 0
        filterCF = dropdownValues['cf'] = 0
        filterDP = dropdownValues['dp'] = -1
        filterDIVGR = dropdownValues['divgr'] = 0
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -3
        filterBV = dropdownValues['bv'] = 0
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericE' in request.POST:
        filterSector = dropdownValues['sector'] = 'Energy'
        filterROCE = dropdownValues['roce'] = 3
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = -5
        filterNI = dropdownValues['ni'] = -5
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = 0
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 2
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 3
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = 3
        filterEQ = dropdownValues['eq'] = 3
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericBDC' in request.POST:
        filterSector = dropdownValues['sector'] = 'BDC'
        filterROCE = dropdownValues['roce'] = 3
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = -5
        filterNI = dropdownValues['ni'] = -5
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = -5
        filterPO = dropdownValues['po'] = -5
        filterSHARES = dropdownValues['shares'] = 1
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = 0
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 1
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericF' in request.POST:
        filterSector = dropdownValues['sector'] = 'Financials'
        filterROCE = dropdownValues['roce'] = 3
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = -5
        filterNI = dropdownValues['ni'] = 0
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 3
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = 3
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericI' in request.POST:
        filterSector = dropdownValues['sector'] = 'Industrials'
        filterROCE = dropdownValues['roce'] = 3
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 3
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericK' in request.POST:
        filterSector = dropdownValues['sector'] = 'Technology'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 2
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericP' in request.POST:
        filterSector = dropdownValues['sector'] = 'Consumer Staples'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 0
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 1
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = -5
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericRE' in request.POST:
        filterSector = dropdownValues['sector'] = 'Real Estate'
        filterROCE = dropdownValues['roce'] = -5
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = -5
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = -2
        filterPO = dropdownValues['po'] = -5
        filterSHARES = dropdownValues['shares'] = -5
        filterDEBT = dropdownValues['debt'] = -2
        filterBV = dropdownValues['bv'] = 1
        filterEQ = dropdownValues['eq'] = 1
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = 2
        filterREITROCE = dropdownValues['reitroce'] = 1
        filterFFOPO = dropdownValues['ffopo'] = 1

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericU' in request.POST:
        filterSector = dropdownValues['sector'] = 'Utilities'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 2
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericV' in request.POST:
        filterSector = dropdownValues['sector'] = 'Healthcare'
        filterROCE = dropdownValues['roce'] = 2
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 2
        filterNI = dropdownValues['ni'] = 2
        filterFCF = dropdownValues['fcf'] = -5
        filterFCFM = dropdownValues['fcfm'] = -5
        filterCF = dropdownValues['cf'] = -5
        filterDP = dropdownValues['dp'] = 1
        filterDIVGR = dropdownValues['divgr'] = 2
        filterPO = dropdownValues['po'] = 1
        filterSHARES = dropdownValues['shares'] = 2
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = -5
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = 0
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    elif 'genericY' in request.POST:
        filterSector = dropdownValues['sector'] = 'Consumer Cyclical'
        filterROCE = dropdownValues['roce'] = 3
        filterROIC = dropdownValues['roic'] = -5
        filterREV = dropdownValues['rev'] = 1
        filterNI = dropdownValues['ni'] = 1
        filterFCF = dropdownValues['fcf'] = -1
        filterFCFM = dropdownValues['fcfm'] = -1
        filterCF = dropdownValues['cf'] = 0
        filterDP = dropdownValues['dp'] = -1
        filterDIVGR = dropdownValues['divgr'] = -5
        filterPO = dropdownValues['po'] = -5
        filterSHARES = dropdownValues['shares'] = 0
        filterDEBT = dropdownValues['debt'] = -5
        filterBV = dropdownValues['bv'] = 0
        filterEQ = dropdownValues['eq'] = 0
        filterROC = dropdownValues['roc'] = -5
        filterFFO = dropdownValues['ffo'] = -5
        filterREITROCE = dropdownValues['reitroce'] = -5
        filterFFOPO = dropdownValues['ffopo'] = -5

        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)

        context = {
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': searchFilter.order_by('-scorerank'),
            'tickerToBeFound': tickerToBeFound,
        }
        return render(request, 'investor_center/sectorRankings.html', context)

    # elif 'income' in request.POST:
        # return redirect(report)
        # print('sr income clicked')
        # ticker = request.POST.get('ts').upper()
        # ticker = request.POST.get('income').upper()
        # form = 
        # print(form)
        # print(form['income'])
        
        # request.session['sel'] = request.POST
        # return redirect('highlights')

        # print('ticker: ' + str(ticker))
        # sectors = Sector_Rankings.objects.values('Sector').distinct()
        # megaData = Mega.objects.filter(Ticker=ticker).order_by('-year')
        # metaData = Metadata.objects.filter(Ticker=ticker)

        # context = {
        #     # 'sectors': sectors,
        #     # 'ticker': ticker,
        #     # 'dv': dropdownValues,
        #     'ts':ticker,
        #     'dt': ticker,
        #     # 'lt': megaData,
        #     # 'mt': metaData,
        #     }
        # return redirect(reverse('report', kwargs={'ts':ticker, 'dt':ticker})) #render(request, 'investor_center/incomeDetails.html', context) #redirect(report, context) #
    
    else:
        print('sr else')
        # try:
            
        #     ticker = request.POST.get('ts').upper()
        #     print('sr else try block')
        #     context = {
        #     'dt': ticker,    
        #     'sectors': sectors,
        #     'dv': dropdownValues,
        #     'lt': pageLandingTable,
        #     }
        #     return redirect(reverse('investor_center/incomeDetails.html', kwargs={context}))#render(request, 'investor_center/sectorRankings.html', context)
        # except:
        #     print('sr else except block')
        #     context = {
        #     # 'dt': ticker,    
        #     'sectors': sectors,
        #     'dv': dropdownValues,
        #     'lt': pageLandingTable,
        #     }
        #     return render(request, 'investor_center/sectorRankings.html', context)
        context = {
            # 'dt': ticker,    
            'sectors': sectors,
            'dv': dropdownValues,
            'lt': pageLandingTable,
            'tickerToBeFound': tickerToBeFound,
            }
        return render(request, 'investor_center/sectorRankings.html', context)
