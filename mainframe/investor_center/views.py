from django.shortcuts import render
from django.http import HttpResponse
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
    
    if request.method=="POST":
        
        #luke here this works. go forth from here!
        filterSector = request.POST.get('sectorDropDown')
        if filterSector is None:
            filterSector = 'K'
        # print(filterSector)
        filterROCE = request.POST.get('vfroce')
        # print(filterROCE)
        if filterROCE is None:
            filterROCE = -5
        # print(filterROCE)
        filterROIC = request.POST.get('vfroic')
        if filterROIC is None:
            filterROIC = -5
        filterREV = request.POST.get('vfrev')
        if filterREV is None:
            filterREV = -5
        filterNI = request.POST.get('vfni')
        if filterNI is None:
            filterNI = -5
        filterFCF = request.POST.get('vffcf')
        if filterFCF is None:
            filterFCF = -5
        filterFCFM = request.POST.get('vffcfm')
        if filterFCFM is None:
            filterFCFM = -5
        filterCF = request.POST.get('vfcf')
        if filterCF is None:
            filterCF = -5
        filterDP = request.POST.get('vfdp')
        if filterDP is None:
            filterDP = -1
        filterDIVGR = request.POST.get('vfdivgr')
        if filterDIVGR is None:
            filterDIVGR = -5
        filterPO = request.POST.get('vfpo')
        if filterPO is None:
            filterPO = -5
        filterSHARES = request.POST.get('vfshares')
        if filterSHARES is None:
            filterSHARES = -5
        filterDEBT = request.POST.get('vfdebt')
        if filterDEBT is None:
            filterDEBT = -5
        filterBV = request.POST.get('vfbv')
        if filterBV is None:
            filterBV = -5
        filterEQ = request.POST.get('vfeq')
        if filterEQ is None:
            filterEQ = -5
        filterROC = request.POST.get('vfroc')
        if filterROC is None:
            filterROC = -5
        filterFFO = request.POST.get('vfffo')
        if filterFFO is None:
            filterFFO = -5
        filterREITROCE = request.POST.get('vfreitroce')
        if filterREITROCE is None:
            filterREITROCE = -5
        filterFFOPO = request.POST.get('vfffopo')
        if filterFFOPO is None:
            filterFFOPO = -5
        searchFilter = Sector_Rankings.objects.filter(Sector=filterSector, roce__gte=filterROCE, roic__gte=filterROIC, rev__gte=filterREV, ni__gte=filterNI,
                                fcf__gte=filterFCF, fcfm__gte=filterFCFM, cf__gte=filterCF, divpay__gte=filterDP, divgr__gte=filterDIVGR, po__gte=filterPO, )
                                # shares__gte=filterSHARES, debt__gte=filterDEBT, bv__gte=filterBV, equity__gte=filterEQ, roc__gte=filterROC, ffo__gte=filterFFO, 
                                # reitroce__gte=filterREITROCE, ffopo__gte=filterFFOPO)
        # print(searchFilter.query)

        context = {
        'sectors': sectors,
        'lt': searchFilter,
        }
        return render(request, 'investor_center/sectorRankings.html', context)
    else:
        context = {
        'sectors': sectors,
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