from django.db import models

# class Dividends(models.Model):
#     # start = models.CharField(max_length=12)
#     # end = models.CharField(max_length=12)
#     year = models.CharField(max_length=4)
#     interestPaid = models.IntegerField()
#     divsPaidPerShare = models.FloatField()
#     totalDivsPaid = models.IntegerField()
#     shares = models.IntegerField()
#     sharesGrowthRate = models.FloatField()
#     divGrowthRateBOT = models.FloatField()
#     divGrowthRateBOPS = models.FloatField()
#     integrityFlag = models.CharField(max_length=10)

#     ticker = models.CharField(max_length=10)
#     cik = models.CharField(max_length=10)
#     units = models.CharField(max_length=10)

#     class Meta:
#         db_table = 'Dividends'

# class ROIC(models.Model):
#     # start = models.CharField(max_length=12)
#     # end = models.CharField(max_length=12)
#     year = models.CharField(max_length=4)
#     operatingIncome = models.IntegerField()
#     operatingIncomeGrowthRate = models.FloatField()
#     netIncome = models.IntegerField()
#     taxRate = models.FloatField()
#     TotalDebt = models.IntegerField()
#     assets = models.IntegerField()
#     liabilities = models.IntegerField()
#     TotalEquity = models.IntegerField()
#     nopat = models.IntegerField()
#     investedCapital = models.IntegerField()
#     roic = models.FloatField()
#     adjRoic = models.FloatField()
#     roce = models.FloatField()
#     integrityFlag = models.CharField(max_length=10)

#     ticker = models.CharField(max_length=10)
#     cik = models.CharField(max_length=10)
#     units = models.CharField(max_length=10)

#     class Meta:
#         db_table = 'ROIC'

# class Income(models.Model):
#     # start = models.CharField(max_length=12)
#     # end = models.CharField(max_length=12)
#     year = models.CharField(max_length=4)
#     revenue = models.IntegerField()
#     revenueGrowthRate = models.FloatField()
#     netIncome = models.IntegerField()
#     netIncomeGrowthRate = models.FloatField()
#     operatingCashFlow = models.IntegerField()
#     operatingCashFlowGrowthRate = models.FloatField()
#     investingCashFlow = models.IntegerField()
#     investingCashFlowGrowthRate = models.FloatField()
#     financingCashFlow = models.IntegerField()
#     financingCashFlowGrowthRate = models.FloatField()
#     netCashFlow = models.IntegerField()
#     netCashFlowGrowthRate = models.FloatField()
#     capEx = models.IntegerField()
#     capExGrowthRate = models.FloatField()
#     fcf = models.IntegerField()
#     fcfGrowthRate = models.FloatField()
#     fcfMargin = models.FloatField()
#     fcfMarginGrowthRate = models.FloatField()
#     # eps = models.IntegerField()
#     # epsGrowthRate = models.FloatField()
#     depreNAmor = models.IntegerField()
#     gainSaleProp = models.IntegerField()
#     ffo = models.IntegerField()
#     ffoGrowthRate = models.FloatField()
#     integrityFlag = models.CharField(max_length=10)
    
#     ticker = models.CharField(max_length=10)
#     cik = models.CharField(max_length=10)
#     units = models.CharField(max_length=10)

#     class Meta:
#         db_table = 'Income'

class Mega(models.Model):
    
    revenue = models.IntegerField(blank=True, null=True)
    revenueGrowthRate = models.FloatField(blank=True, null=True)
    netIncome = models.IntegerField(blank=True, null=True)
    netIncomeGrowthRate = models.FloatField(blank=True, null=True)
    netIncomeNCI = models.IntegerField(blank=True, null=True)
    netIncomeNCIGrowthRate = models.FloatField(blank=True, null=True)
    interestPaid = models.IntegerField(blank=True, null=True)
    operatingIncome = models.IntegerField(blank=True, null=True)
    operatingIncomeGrowthRate = models.FloatField(blank=True, null=True)
    taxRate = models.FloatField(blank=True, null=True)
    capEx = models.IntegerField(blank=True, null=True)
    capExGrowthRate = models.FloatField(blank=True, null=True)
    depreNAmor = models.IntegerField(blank=True, null=True)
    gainSaleProp = models.IntegerField(blank=True, null=True)

    operatingCashFlow = models.IntegerField(blank=True, null=True)
    operatingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
    investingCashFlow = models.IntegerField(blank=True, null=True)
    investingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
    financingCashFlow = models.IntegerField(blank=True, null=True)
    financingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
    netCashFlow = models.IntegerField(blank=True, null=True)
    netCashFlowGrowthRate = models.FloatField(blank=True, null=True)

    fcf = models.IntegerField(blank=True, null=True)
    fcfGrowthRate = models.FloatField(blank=True, null=True)
    fcfMargin = models.FloatField(blank=True, null=True)
    fcfMarginGrowthRate = models.FloatField(blank=True, null=True)
    
    ffo = models.IntegerField(blank=True, null=True)
    ffoGrowthRate = models.FloatField(blank=True, null=True)
    reitEPS = models.FloatField(blank=True, null=True)
    reitEPSGrowthRate = models.FloatField(blank=True, null=True)

    TotalDebt = models.IntegerField(blank=True, null=True)
    assets = models.IntegerField(blank=True, null=True)
    liabilities = models.IntegerField(blank=True, null=True)
    TotalEquity = models.IntegerField(blank=True, null=True)
    ReportedTotalEquity = models.IntegerField(blank=True, null=True)

    nopat = models.IntegerField(blank=True, null=True)
    investedCapital = models.IntegerField(blank=True, null=True)
    roic = models.FloatField(blank=True, null=True)
    adjRoic = models.FloatField(blank=True, null=True)
    reportedAdjRoic = models.FloatField(blank=True, null=True)
    reportedRoce = models.FloatField(blank=True, null=True)
    calculatedRoce = models.FloatField(blank=True, null=True)
    
    shares = models.IntegerField(blank=True, null=True)
    sharesGrowthRate = models.FloatField(blank=True, null=True)
    dilutedShares = models.IntegerField(blank=True, null=True)
    reportedEPS = models.FloatField(blank=True, null=True)
    reportedEPSGrowthRate = models.FloatField(blank=True, null=True)
    calculatedEPS = models.FloatField(blank=True, null=True)
    calculatedEPSGrowthRate = models.FloatField(blank=True, null=True)

    divsPaidPerShare = models.FloatField(blank=True, null=True)
    calcDivsPerShare = models.FloatField(blank=True, null=True)
    totalDivsPaid = models.IntegerField(blank=True, null=True)
    divGrowthRateBOT = models.FloatField(blank=True, null=True)
    divGrowthRateBORPS = models.FloatField(blank=True, null=True)
    divGrowthRateBOCPS = models.FloatField(blank=True, null=True)
    payoutRatio = models.FloatField(blank=True, null=True)
    fcfPayoutRatio = models.FloatField(blank=True, null=True)
    ffoPayoutRatio = models.FloatField(blank=True, null=True)

    ROCTotal = models.IntegerField(blank=True, null=True)
    ROCTotalGrowthRate = models.FloatField(blank=True, null=True)
    ROCperShare = models.FloatField(blank=True, null=True)
    ROCperShareGrowthRate = models.FloatField(blank=True, null=True)

    nav = models.FloatField(blank=True, null=True)
    navGrowthRate = models.FloatField(blank=True, null=True)
    calcBookValue = models.FloatField(blank=True, null=True)
    calcBookValueGrowthRate = models.FloatField(blank=True, null=True)
    reportedBookValue = models.FloatField(blank=True, null=True)
    reportedBookValueGrowthRate = models.FloatField(blank=True, null=True)

    price = models.FloatField(blank=True, null=True)
    priceGrowthRate = models.FloatField(blank=True, null=True)

    DIVintegrityFlag = models.CharField(max_length=10)
    INCintegrityFlag = models.CharField(max_length=10)
    ROICintegrityFlag = models.CharField(max_length=10)

    year = models.CharField(max_length=4)
    Ticker = models.CharField(max_length=10)
    CIK = models.CharField(max_length=10)
    Units = models.CharField(max_length=10)
    Sector = models.CharField(max_length=30)
    Industry = models.CharField(max_length=50)

    class Meta:
        db_table = 'Mega'