from django.shortcuts import render
from django.http import HttpResponse
import numpy as np
# from django.template import loader

from .models import Metadata, Sector_Rankings

# Create your views here.
def index(request):
    return render(request, 'investor_center/index.html', {})
    #HttpResponse('<h1>Welcome to The Investor Center.</h1>')

def sr(request):
    # topTen = Sector_Rankings.objects.order_by('-scorerank')[:10]
    sectors = Sector_Rankings.objects.values('Sector').distinct()
    # randomSector = Sector_Rankings.objects.values('Sector').order_By('?').first()
    # divpayers = Sector_Rankings.objects.values('divpay').distinct()
    wholeTable = Sector_Rankings.objects.order_by('-scorerank')
    pageLandingTable = Sector_Rankings.objects.order_by('-scorerank')[:50]
    dropdownValues = {'sector':'Select Sector', 'roce':'>=', 'roic':'>=', 'rev':'>=', 'ni':'>=', 'fcf':'>=', 
                        'fcfm':'>=', 'cf':'>=', 'dp':'>=', 'divgr':'>=', 'po':'>=', 'shares':'>=', 'debt':'>=', 
                        'bv':'>=', 'eq':'>=', 'roc':'>=', 'ffo':'>=', 'reitroce':'>=', 'ffopo':'>='}
    
    if request.method=="POST":
        filterSector = request.POST.get('sectorDropDown')
        dropdownValues['sector'] = filterSector
        # if filterSector is None or filterSector == 'Select Sector':
        #     filterSector = 'K'
        #     dropdownValues['sector'] = filterSector
        
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
            print('reitroce in if' + str(filterREITROCE) +' '+ str(type(filterREITROCE)))
        dropdownValues['reitroce'] = filterREITROCE
        print('reitroce after all ' + str(filterREITROCE) +' '+ str(type(filterREITROCE)))

        filterFFOPO = request.POST.get('vfffopo')
        if filterFFOPO is None or filterFFOPO == '>=':
            filterFFOPO = -5
            print('ffo po in if ' + str(filterFFOPO) +' '+ str(type(filterFFOPO)))
        dropdownValues['ffopo'] = filterFFOPO
        print('ffo po after all ' + str(filterFFOPO) +' '+ str(type(filterFFOPO)))
            
        

        
        if filterSector == 'All':
            searchFilter = Sector_Rankings.objects.filter( roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)#.order_by('Sector','-scorerank')
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': searchFilter,
            }
            return render(request, 'investor_center/sectorRankings.html', context)
        else:
            searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO,
                                shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO,
                                reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)
            context = {
                'sectors': sectors,
                'dv': dropdownValues,
                'lt': searchFilter,
            }
            return render(request, 'investor_center/sectorRankings.html', context)
    else:
        context = {
        'sectors': sectors,
        'dv': dropdownValues,
        'lt': pageLandingTable,
        }
        return render(request, 'investor_center/sectorRankings.html', context)
    # return render(request, 'investor_center/sectorRankings.html', context)

    # if request.method=="POST":
    #    
    #  empsearch=Employee.objects.filter(gender=searchgender,designation=searchdesignation)

    #     return render(request,'home.html',{"data":empsearch})


    #template = loader.get_template("investor_center/metadata.html")
    #HttpResponse(template.render(context,request))
        #'<h1>One Piston. Very unique ICEngine.</h1>')

        # options = ['Materials', 'Communications', 'Energy', 'Financials ex-BDC\'s', 'BDC\'s', 
                    # 'Industrials', 'Technology', 'Consumer Staples', 'Real Estate', 'Utilities', 
                    # 'Healthcare', 'Consumer Cyclical'],

#this was so cool, but i have to name each individually so... dang.
# 'dd': dropdown,
        # 'dd2': dropdown2,
        # {{ dd|safe }} #this goes into the html
# dropdown = "<select name=\"valueFilter\"> \
#                 <option selected disabled=true> >= </option> \
#                 <option>5</option> \
#                 <option>4</option> \
#                 <option>3</option> \
#                 <option>2</option> \
#                 <option>1</option> \
#                 <option>0</option> \
#                 <option>-1</option> \
#                 <option>-2</option> \
#                 <option>-3</option> \
#                 <option>-4</option> \
#                 <option>-5</option> \
#                 </select>"
#     dropdown2 = "<select name=\"valueFilter2\"> \
#                 <option selected disabled=true>  </option> \
#                 <option>1</option> \
#                 <option>-1</option> \
#                 </select>"