from django.db import models

class Dividends(models.Model):
    # start = models.CharField(max_length=12)
    # end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    interestPaid = models.IntegerField()
    divsPaidPerShare = models.FloatField()
    totalDivsPaid = models.IntegerField()
    shares = models.IntegerField()
    sharesGrowthRate = models.FloatField()
    divGrowthRateBOT = models.FloatField()
    divGrowthRateBOPS = models.FloatField()
    integrityFlag = models.CharField(max_length=10)

    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)
    units = models.CharField(max_length=10)

    class Meta:
        db_table = 'Dividends'

class ROIC(models.Model):
    # start = models.CharField(max_length=12)
    # end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    operatingIncome = models.IntegerField()
    operatingIncomeGrowthRate = models.FloatField()
    netIncome = models.IntegerField()
    taxRate = models.FloatField()
    TotalDebt = models.IntegerField()
    assets = models.IntegerField()
    liabilities = models.IntegerField()
    TotalEquity = models.IntegerField()
    nopat = models.IntegerField()
    investedCapital = models.IntegerField()
    roic = models.FloatField()
    adjRoic = models.FloatField()
    roce = models.FloatField()
    integrityFlag = models.CharField(max_length=10)

    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)
    units = models.CharField(max_length=10)

    class Meta:
        db_table = 'ROIC'

class Income(models.Model):
    # start = models.CharField(max_length=12)
    # end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    revenue = models.IntegerField()
    revenueGrowthRate = models.FloatField()
    netIncome = models.IntegerField()
    netIncomeGrowthRate = models.FloatField()
    operatingCashFlow = models.IntegerField()
    operatingCashFlowGrowthRate = models.FloatField()
    investingCashFlow = models.IntegerField()
    investingCashFlowGrowthRate = models.FloatField()
    financingCashFlow = models.IntegerField()
    financingCashFlowGrowthRate = models.FloatField()
    netCashFlow = models.IntegerField()
    netCashFlowGrowthRate = models.FloatField()
    capEx = models.IntegerField()
    capExGrowthRate = models.FloatField()
    fcf = models.IntegerField()
    fcfGrowthRate = models.FloatField()
    fcfMargin = models.FloatField()
    fcfMarginGrowthRate = models.FloatField()
    # eps = models.IntegerField()
    # epsGrowthRate = models.FloatField()
    depreNAmor = models.IntegerField()
    gainSaleProp = models.IntegerField()
    ffo = models.IntegerField()
    ffoGrowthRate = models.FloatField()
    integrityFlag = models.CharField(max_length=10)
    
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)
    units = models.CharField(max_length=10)

    class Meta:
        db_table = 'Income'