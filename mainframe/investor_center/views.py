from django.shortcuts import render
from django.http import HttpResponse
# from django.template import loader

from .models import Metadata, Sector_Rankings

# Create your views here.
def index(request):
    return render(request, 'investor_center/index.html', {})
    #HttpResponse('<h1>Welcome to The Investor Center.</h1>')

def sr(request):
    wholeTable = Sector_Rankings.objects.order_by('-scorerank')[:10]
    
    context = {
        'wt': wholeTable,
    }
    return render(request, 'investor_center/sectorRankings.html', context)
    #template = loader.get_template("investor_center/metadata.html")
    #HttpResponse(template.render(context,request))
        #'<h1>One Piston. Very unique ICEngine.</h1>')

        # options = ['Materials', 'Communications', 'Energy', 'Financials ex-BDC\'s', 'BDC\'s', 
                    # 'Industrials', 'Technology', 'Consumer Staples', 'Real Estate', 'Utilities', 
                    # 'Healthcare', 'Consumer Cyclical'],