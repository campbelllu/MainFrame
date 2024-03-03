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

class CapEx(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'CapEx'

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

class DepreciationAndAmortization(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'DepNAmor'

class EPS(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.FloatField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'EPS'

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

class TotalDebt(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    shortTermDebt = models.IntegerField()
    longTermDebt1 = models.IntegerField()
    longTermDebt2 = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'TotalDebt'

class TotalEquity(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    totalAssets = models.IntegerField()
    totalLiabilities = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'TotalEquity'

class NetCashFlow(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'NetCashFlow'

class OperatingCashFlow(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'OperatingCashFlow'

class OperatingIncome(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'OperatingIncome'

class Revenue(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.IntegerField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'Revenue'

class TaxRate(models.Model):
    start = models.CharField(max_length=12)
    end = models.CharField(max_length=12)
    year = models.CharField(max_length=4)
    val = models.FloatField()
    ticker = models.CharField(max_length=10)
    cik = models.CharField(max_length=10)

    class Meta:
        db_table = 'TaxRate'