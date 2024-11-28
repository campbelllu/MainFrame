"""
URL configuration for mainframe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

# from helloThere import views as htviews
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('About/', views.info, name='info'),
    path('TechnicalDetails/', views.technical, name='technical'),
    # path('Contact/', views.contact, name='contact'),
    # path('Contact/Success/', views.successfulemail, name='successfulemail'),
    path('TipJar/', views.tips, name='tips'),
    # path('SectorRankings/', views.sr, name='sr'),
    # path('SectorRankings/Explained/', views.srinfo, name='srinfo'),
    path('StockScreener/', views.stockScreen, name='stockScreen'),
    path('CompareHighlights/', views.compare, name='compare'),
    path('Highlights/', views.highlights, name='highlights'),
    path('Highlights/Summary/<str:ticker>/', views.summaryHighlights, name='overh'),
    path('Highlights/Income/<str:ticker>/', views.incomeHighlights, name='ih'),
    path('Highlights/Balance/<str:ticker>/', views.balanceHighlights, name='bh'),
    path('Highlights/CashFlow/<str:ticker>/', views.cashflowHighlights, name='cfh'),
    path('Highlights/Efficiency/<str:ticker>/', views.efficiencyHighlights, name='effh'),
    path('Highlights/Dividends/<str:ticker>/', views.dividendHighlights, name='divsh'),

    # path('Report/<slug:ticker>/', views.report, name='slugincome'), #r'^(?P<ticker>[\w-]+)/$'
    # path('Report/Income', views.report, name='income'),
    # path('Report/<str:ticker>/', views.reportDetails, name='reportDetails'),
    path('Valuation/', views.valuation, name='val')
   
]
