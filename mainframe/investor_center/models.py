from django.db import models

class SharesOutstanding(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'SharesOutstanding'



class DepreciationAndAmortization(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'DepNAmor'

class GainLossSaleProperty(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'GainPropSales'

class InterestPaid(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'InterestPaid'


class Dividends(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    perShare = models.FloatField()
    totalPaid = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'Dividends'



class ROIC(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    operatingIncome = models.IntegerField()
    operatingIncomeGrowthRate = models.FloatField()
    taxRate = models.FloatField()
    totalDebt = models.IntegerField()
    assets = models.IntegerField()
    liabilities = models.IntegerField()
    TotalEquity = models.IntegerField()
    nopat = models.IntegerField()
    investedCapital = models.IntegerField()
    roic = models.FloatField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'ROIC'

class Income(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    revenue = models.IntegerField()
    revGrowthRate = models.FloatField()
    netIncome = models.IntegerField()
    netIncomeGrowthRate = models.FloatField()
    operatingCashFlow = models.IntegerField()
    operatingCashFlowGrowthRate = models.FloatField()
    netCashFlow = models.IntegerField()
    netCashFlowGrowthRate = models.FloatField()
    capEx = models.IntegerField()
    fcf = models.IntegerField()
    fcfGrowthRate = models.FloatField()
    eps = models.IntegerField()
    epsGrowthRate = models.FloatField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'Income'