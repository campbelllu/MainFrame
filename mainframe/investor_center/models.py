from django.db import models
# from django.db import transaction
# with transaction.atomic():
#     for obj in Mega.objects.all():
#         Mega_Backup.objects.create(**obj.__dict__)

class stockList(models.Model):
    Ticker = models.CharField(max_length=10, blank=True, null=True, unique=True)
    CIK = models.IntegerField(blank=True, null=True)
    Sector = models.CharField(max_length=30, blank=True, null=True)
    Industry = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'stockList'

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

    profitMargin = models.FloatField(blank=True, null=True)
    profitMarginGrowthRate = models.FloatField(blank=True, null=True)

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
    TotalDebtGrowthRate = models.FloatField(blank=True, null=True)
    assets = models.IntegerField(blank=True, null=True)
    liabilities = models.IntegerField(blank=True, null=True)
    TotalEquity = models.IntegerField(blank=True, null=True)
    TotalEquityGrowthRate = models.FloatField(blank=True, null=True)
    ReportedTotalEquity = models.IntegerField(blank=True, null=True)
    ReportedTotalEquityGrowthRate = models.FloatField(blank=True, null=True)

    # nopat = models.IntegerField(blank=True, null=True)
    investedCapital = models.IntegerField(blank=True, null=True)
    # roic = models.FloatField(blank=True, null=True)
    adjRoic = models.FloatField(blank=True, null=True)
    reportedAdjRoic = models.FloatField(blank=True, null=True)
    reportedRoce = models.FloatField(blank=True, null=True)
    calculatedRoce = models.FloatField(blank=True, null=True)
    cReitROE = models.FloatField(blank=True, null=True)
    # cReitROEGrowthRate = models.FloatField(blank=True, null=True)
    rReitROE = models.FloatField(blank=True, null=True)
    # rReitROEGrowthRate = models.FloatField(blank=True, null=True)
    
    shares = models.IntegerField(blank=True, null=True)
    sharesGrowthRate = models.FloatField(blank=True, null=True)
    # dilutedShares = models.IntegerField(blank=True, null=True)
    # dilutedSharesGrowthRate = models.FloatField(blank=True, null=True)
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

    # ROCTotal = models.IntegerField(blank=True, null=True)
    # ROCTotalGrowthRate = models.FloatField(blank=True, null=True)
    # ROCperShare = models.FloatField(blank=True, null=True)
    # ROCperShareGrowthRate = models.FloatField(blank=True, null=True)

    nav = models.FloatField(blank=True, null=True)
    navGrowthRate = models.FloatField(blank=True, null=True)
    calcBookValue = models.FloatField(blank=True, null=True)
    calcBookValueGrowthRate = models.FloatField(blank=True, null=True)
    reportedBookValue = models.FloatField(blank=True, null=True)
    reportedBookValueGrowthRate = models.FloatField(blank=True, null=True)

    price = models.FloatField(blank=True, null=True)
    priceGrowthRate = models.FloatField(blank=True, null=True)

    # DIVintegrityFlag = models.CharField(max_length=10)
    # INCintegrityFlag = models.CharField(max_length=10)
    # ROICintegrityFlag = models.CharField(max_length=10)

    year = models.CharField(max_length=4)
    Ticker = models.CharField(max_length=10)
    CIK = models.CharField(max_length=10)
    Units = models.CharField(max_length=10)
    Sector = models.CharField(max_length=30)
    Industry = models.CharField(max_length=50)

    # @property
    # def profit_margin(self):
    #     if self.revenue is None or self.revenue == 0:
    #         return None
    #     elif self.netIncome is None:
    #         return None
    #     else:
    #         return self.netIncome / self.revenue * 100

    # @property
    # def profit_margin_avg(self):
    #     if self.revenue is None or self.revenue == 0:
    #         return None
    #     elif self.netIncome is None:
    #         return None
    #     else:
    #         return self.netIncome / self.revenue * 100

    # @property
    # def creit_roce(self):
    #     if self.TotalEquity is None or self.ReportedTotalEquity == 0:
    #         return None
    #     elif self.ffo is None:
    #         return None
    #     else:
    #         return self.ffo / self.TotalEquity * 100

    # @property
    # def rreit_roce(self): #luke this
    #     if self.ReportedTotalEquity is None or self.ReportedTotalEquity == 0:
    #         return None
    #     elif self.ffo is None:
    #         return None
    #     else:
    #         return self.ffo / self.ReportedTotalEquity * 100

    # @property
    # def por100(self):
    #     if self.payoutRatio is None:
    #         return None
    #     else:
    #         return self.payoutRatio * 100

    # @property
    # def fcfpor100(self):
    #     if self.fcfPayoutRatio is None:
    #         return None
    #     else:
    #         return self.fcfPayoutRatio * 100

    # @property
    # def ffopor100(self):
    #     if self.ffoPayoutRatio is None:
    #         return None
    #     else:
    #         return self.ffoPayoutRatio * 100

    class Meta:
        db_table = 'Mega'

class Metadata(models.Model):
    Ticker = models.CharField(max_length=10, blank=True, null=True)
    FirstYear = models.CharField(max_length=4, blank=True, null=True)
    LatestYear = models.CharField(max_length=4, blank=True, null=True)
    AveragedOverYears  = models.CharField(max_length=4, blank=True, null=True)
    Sector = models.CharField(max_length=30, blank=True, null=True)
    Industry = models.CharField(max_length=50, blank=True, null=True)
    # revGrowthAVG = models.FloatField(blank=True, null=True)
    # revGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    revGrowthAVGnz = models.FloatField(blank=True, null=True)

    netIncomeLow = models.IntegerField(blank=True, null=True)
    # netIncomeGrowthAVG = models.FloatField(blank=True, null=True)
    # netIncomeGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    netIncomeGrowthAVGnz = models.FloatField(blank=True, null=True)
    # netIncomeNCILow = models.IntegerField(blank=True, null=True)
    # netIncomeNCIGrowthAVG = models.FloatField(blank=True, null=True)
    # netIncomeNCIGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    # netIncomeNCIGrowthAVGnz = models.FloatField(blank=True, null=True)

    ffoLow = models.IntegerField(blank=True, null=True)
    # ffoGrowthAVG = models.FloatField(blank=True, null=True)
    # ffoGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    ffoGrowthAVGnz = models.FloatField(blank=True, null=True)

    repsLow = models.FloatField(blank=True, null=True)
    # repsAVG = models.FloatField(blank=True, null=True)
    # repsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    repsAVGnz = models.FloatField(blank=True, null=True)
        
    # repsGrowthAVG = models.FloatField(blank=True, null=True)
    # repsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    repsGrowthAVGnz = models.FloatField(blank=True, null=True)

    # cepsLow = models.FloatField(blank=True, null=True)
    # cepsAVG = models.FloatField(blank=True, null=True)
    # cepsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    cepsAVGnz = models.FloatField(blank=True, null=True)

    # cepsGrowthAVG = models.FloatField(blank=True, null=True)
    # cepsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    cepsGrowthAVGnz = models.FloatField(blank=True, null=True)

    # reitepsLow = models.FloatField(blank=True, null=True)
    # reitepsAVG = models.FloatField(blank=True, null=True)
    # reitepsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    reitepsAVGnz = models.FloatField(blank=True, null=True)

    # reitepsGrowthAVG = models.FloatField(blank=True, null=True)
    # reitepsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    reitepsGrowthAVGnz = models.FloatField(blank=True, null=True)

    # fcfLow = models.IntegerField(blank=True, null=True)
    fcfAVGnz = models.FloatField(blank=True, null=True)
    # fcfGrowthAVG = models.FloatField(blank=True, null=True)
    # fcfGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    fcfGrowthAVGnz = models.FloatField(blank=True, null=True)

    # fcfMarginLow = models.FloatField(blank=True, null=True)
    # fcfMarginHigh = models.FloatField(blank=True, null=True)
    # fcfMarginAVG = models.FloatField(blank=True, null=True)
    fcfMarginAVGnz = models.FloatField(blank=True, null=True)

    # fcfMarginGrowthAVG = models.FloatField(blank=True, null=True)
    # fcfMarginGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    fcfMarginGrowthAVGnz = models.FloatField(blank=True, null=True)

    profitMarginAVGnz = models.FloatField(blank=True, null=True)
    profitMarginGrowthAVGnz = models.FloatField(blank=True, null=True)

    # priceLow = models.FloatField(blank=True, null=True)
    # priceHigh = models.FloatField(blank=True, null=True)
    # priceLatest = models.FloatField(blank=True, null=True)
    priceAVG = models.FloatField(blank=True, null=True)
    priceGrowthAVG = models.FloatField(blank=True, null=True)

    debtGrowthAVG = models.FloatField(blank=True, null=True)

    reportedEquityAVG = models.IntegerField(blank=True, null=True)
    # reportedEquityGrowthAVG = models.FloatField(blank=True, null=True)
    # reportedEquityGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    reportedEquityGrowthAVGnz = models.FloatField(blank=True, null=True)

    calculatedEquityAVG = models.IntegerField(blank=True, null=True)
    # calculatedEquityGrowthAVG = models.FloatField(blank=True, null=True)
    # calculatedEquityGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    calculatedEquityGrowthAVGnz = models.FloatField(blank=True, null=True)

    # aggEquityGrowthAVG = models.FloatField(blank=True, null=True)

    # operatingCashFlowLow = models.IntegerField(blank=True, null=True)
    # operatingCashFlowAVG = models.FloatField(blank=True, null=True)
    # operatingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    operatingCashFlowAVGnz = models.FloatField(blank=True, null=True)

    # operatingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
    # operatingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    operatingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)

    # investingCashFlowLow = models.IntegerField(blank=True, null=True)
    # investingCashFlowAVG = models.FloatField(blank=True, null=True)
    # investingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    investingCashFlowAVGnz = models.FloatField(blank=True, null=True)
    # investingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
    # investingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    investingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)

    # financingCashFlowLow = models.IntegerField(blank=True, null=True)
    # financingCashFlowAVG = models.FloatField(blank=True, null=True)
    # financingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    financingCashFlowAVGnz = models.FloatField(blank=True, null=True)
    # financingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
    # financingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    financingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)

    # netCashFlowLow = models.IntegerField(blank=True, null=True)
    # netCashFlowAVG = models.FloatField(blank=True, null=True)
    # netCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    netCashFlowAVGnz = models.FloatField(blank=True, null=True)
    # netCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
    # netCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    netCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)

    # capexGrowthAVG = models.FloatField(blank=True, null=True)
    # capexGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    capexGrowthAVGnz = models.FloatField(blank=True, null=True)

    sharesGrowthAVG = models.FloatField(blank=True, null=True)
    # dilutedSharesGrowthAVG = models.FloatField(blank=True, null=True)

    # totalDivsPaidGrowthAVG = models.FloatField(blank=True, null=True)
    # totalDivsPaidGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    totalDivsPaidGrowthAVGnz = models.FloatField(blank=True, null=True)

    # calcDivsPerShareLow = models.FloatField(blank=True, null=True)
    # calcDivsPerShareHigh = models.FloatField(blank=True, null=True)
    # calcDivsPerShareLatest = models.FloatField(blank=True, null=True)
    calcDivsPerShareAVG = models.FloatField(blank=True, null=True)
    # calcDivsPerShareGrowthLow = models.FloatField(blank=True, null=True)
    # calcDivsPerShareGrowthHigh = models.FloatField(blank=True, null=True)
    # calcDivsPerShareGrowthAVG = models.FloatField(blank=True, null=True)
    # calcDivsPerShareGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    calcDivsPerShareGrowthAVGnz = models.FloatField(blank=True, null=True)

    # repDivsPerShareLow = models.FloatField(blank=True, null=True)
    # repDivsPerShareHigh = models.FloatField(blank=True, null=True)
    # repDivsPerShareLatest = models.FloatField(blank=True, null=True)
    repDivsPerShareAVG = models.FloatField(blank=True, null=True)
    # repDivsPerShareGrowthLow = models.FloatField(blank=True, null=True)
    # repDivsPerShareGrowthHigh = models.FloatField(blank=True, null=True)
    # repDivsPerShareGrowthAVG = models.FloatField(blank=True, null=True)
    # repDivsPerShareGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    repDivsPerShareGrowthAVGnz = models.FloatField(blank=True, null=True)

    # aggDivsPSLow = models.FloatField(blank=True, null=True)
    # aggDivsPSHigh = models.FloatField(blank=True, null=True)
    # aggDivsPSAVG = models.FloatField(blank=True, null=True)
    # aggDivsPSGrowthLow = models.FloatField(blank=True, null=True)
    # aggDivsPSGrowthHigh = models.FloatField(blank=True, null=True)
    # aggDivsPSGrowthAVG = models.FloatField(blank=True, null=True)
    # aggDivsGrowthLow = models.FloatField(blank=True, null=True)
    # aggDivsGrowthHigh = models.FloatField(blank=True, null=True)
    # aggDivsGrowthAVG = models.FloatField(blank=True, null=True)

    # payoutRatioLow = models.FloatField(blank=True, null=True)
    # payoutRatioHigh = models.FloatField(blank=True, null=True)
    # payoutRatioAVG = models.FloatField(blank=True, null=True)
    # payoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    payoutRatioAVGnz = models.FloatField(blank=True, null=True)

    # fcfPayoutRatioLow = models.FloatField(blank=True, null=True)
    # fcfPayoutRatioHigh = models.FloatField(blank=True, null=True)
    # fcfPayoutRatioAVG = models.FloatField(blank=True, null=True)
    # fcfPayoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    fcfPayoutRatioAVGnz = models.FloatField(blank=True, null=True)

    # ffoPayoutRatioLow = models.FloatField(blank=True, null=True)
    # ffoPayoutRatioHigh = models.FloatField(blank=True, null=True)
    # ffoPayoutRatioAVG = models.FloatField(blank=True, null=True)
    # ffoPayoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    ffoPayoutRatioAVGnz = models.FloatField(blank=True, null=True)

    # ROCpsAVG = models.FloatField(blank=True, null=True)
    # numYearsROCpaid = models.IntegerField(blank=True, null=True)

    # roicLow = models.FloatField(blank=True, null=True)
    # roicHigh = models.FloatField(blank=True, null=True)
    # roicAVG = models.FloatField(blank=True, null=True)
    # aroicLow = models.FloatField(blank=True, null=True)
    # aroicHigh = models.FloatField(blank=True, null=True)
    aroicAVG = models.FloatField(blank=True, null=True)
    # raroicLow = models.FloatField(blank=True, null=True)
    # raroicHigh = models.FloatField(blank=True, null=True)
    raroicAVG = models.FloatField(blank=True, null=True)

    # aggaroicLow = models.FloatField(blank=True, null=True)
    # aggaroicHigh = models.FloatField(blank=True, null=True)
    # aggaroicAVG = models.FloatField(blank=True, null=True)

    # croceLow = models.FloatField(blank=True, null=True)
    # croceHigh = models.FloatField(blank=True, null=True)
    croceAVG = models.FloatField(blank=True, null=True)
    # rroceLow = models.FloatField(blank=True, null=True)
    # rroceHigh = models.FloatField(blank=True, null=True)
    rroceAVG = models.FloatField(blank=True, null=True)
    rreitroeAVG = models.FloatField(blank=True, null=True)
    creitroeAVG = models.FloatField(blank=True, null=True)
    # aggroceLow = models.FloatField(blank=True, null=True)
    # aggroceHigh = models.FloatField(blank=True, null=True)
    # aggroceAVG = models.FloatField(blank=True, null=True)

    # calcBookValueLow = models.FloatField(blank=True, null=True)
    calcBookValueAVG = models.FloatField(blank=True, null=True)
    # calcBookValueGrowthAVG = models.FloatField(blank=True, null=True)
    # calcBookValueGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    calcBookValueGrowthAVGnz = models.FloatField(blank=True, null=True)
    # repBookValueLow = models.FloatField(blank=True, null=True)
    repBookValueAVG = models.FloatField(blank=True, null=True)
    # repBookValueGrowthAVG = models.FloatField(blank=True, null=True)
    # repBookValueGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
    repBookValueGrowthAVGnz = models.FloatField(blank=True, null=True)
    # aggBookValueLow = models.FloatField(blank=True, null=True)
    # aggBookValueAVG = models.FloatField(blank=True, null=True)
    # aggBookValueGrowthAVG = models.FloatField(blank=True, null=True)

    navAVG = models.FloatField(blank=True, null=True)
    navGrowthAVG = models.FloatField(blank=True, null=True)

    # calcDivYieldLatest = models.FloatField(blank=True, null=True)
    # calcDivYieldAVG = models.FloatField(blank=True, null=True)
    # repDivYieldLatest = models.FloatField(blank=True, null=True)
    # repDivYieldAVG = models.FloatField(blank=True, null=True)

    # @property
    # def poravg100(self):
    #     if self.payoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.payoutRatioAVG * 100

    # @property
    # def fcfporavg100(self):
    #     if self.fcfPayoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.fcfPayoutRatioAVG * 100
        
    # @property
    # def ffoporavg100(self):
    #     if self.ffoPayoutRatioAVG is None:
    #         return None
    #     else:
    #         return self.ffoPayoutRatioAVG * 100

    class Meta:
        db_table = 'Metadata'

class Sector_Rankings(models.Model):
    Ticker = models.CharField(max_length=10, blank=True, null=True)
    Sector = models.CharField(max_length=30, blank=True, null=True)
    reitroce = models.IntegerField(blank=True, null=True)
    roce = models.IntegerField(blank=True, null=True)
    roic = models.IntegerField(blank=True, null=True)
    roc = models.IntegerField(blank=True, null=True)
    ffopo = models.IntegerField(blank=True, null=True)
    po = models.IntegerField(blank=True, null=True)
    divgr = models.IntegerField(blank=True, null=True)
    divpay = models.IntegerField(blank=True, null=True)
    shares = models.IntegerField(blank=True, null=True)
    cf = models.IntegerField(blank=True, null=True)
    bv = models.IntegerField(blank=True, null=True)
    equity = models.IntegerField(blank=True, null=True)
    debt = models.IntegerField(blank=True, null=True)
    fcfm = models.IntegerField(blank=True, null=True)
    fcf = models.IntegerField(blank=True, null=True)
    ffo = models.IntegerField(blank=True, null=True)
    ni = models.IntegerField(blank=True, null=True)
    rev = models.IntegerField(blank=True, null=True)
    divyield = models.IntegerField(blank=True, null=True)
    maxscore = models.IntegerField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    scorerank = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'Sector_Rankings'

####################################################################################################
# Deprecated
#######################################################################################

# class Mega_Backup(models.Model):
#     revenue = models.IntegerField(blank=True, null=True)
#     revenueGrowthRate = models.FloatField(blank=True, null=True)
#     netIncome = models.IntegerField(blank=True, null=True)
#     netIncomeGrowthRate = models.FloatField(blank=True, null=True)
#     netIncomeNCI = models.IntegerField(blank=True, null=True)
#     netIncomeNCIGrowthRate = models.FloatField(blank=True, null=True)
#     interestPaid = models.IntegerField(blank=True, null=True)
#     operatingIncome = models.IntegerField(blank=True, null=True)
#     operatingIncomeGrowthRate = models.FloatField(blank=True, null=True)
#     taxRate = models.FloatField(blank=True, null=True)
#     capEx = models.IntegerField(blank=True, null=True)
#     capExGrowthRate = models.FloatField(blank=True, null=True)
#     depreNAmor = models.IntegerField(blank=True, null=True)
#     gainSaleProp = models.IntegerField(blank=True, null=True)

#     profitMargin = models.FloatField(blank=True, null=True)
#     profitMarginGrowthRate = models.FloatField(blank=True, null=True)

#     operatingCashFlow = models.IntegerField(blank=True, null=True)
#     operatingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
#     investingCashFlow = models.IntegerField(blank=True, null=True)
#     investingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
#     financingCashFlow = models.IntegerField(blank=True, null=True)
#     financingCashFlowGrowthRate = models.FloatField(blank=True, null=True)
#     netCashFlow = models.IntegerField(blank=True, null=True)
#     netCashFlowGrowthRate = models.FloatField(blank=True, null=True)

#     fcf = models.IntegerField(blank=True, null=True)
#     fcfGrowthRate = models.FloatField(blank=True, null=True)
#     fcfMargin = models.FloatField(blank=True, null=True)
#     fcfMarginGrowthRate = models.FloatField(blank=True, null=True)
    
#     ffo = models.IntegerField(blank=True, null=True)
#     ffoGrowthRate = models.FloatField(blank=True, null=True)
#     reitEPS = models.FloatField(blank=True, null=True)
#     reitEPSGrowthRate = models.FloatField(blank=True, null=True)

#     TotalDebt = models.IntegerField(blank=True, null=True)
#     TotalDebtGrowthRate = models.FloatField(blank=True, null=True)
#     assets = models.IntegerField(blank=True, null=True)
#     liabilities = models.IntegerField(blank=True, null=True)
#     TotalEquity = models.IntegerField(blank=True, null=True)
#     TotalEquityGrowthRate = models.FloatField(blank=True, null=True)
#     ReportedTotalEquity = models.IntegerField(blank=True, null=True)
#     ReportedTotalEquityGrowthRate = models.FloatField(blank=True, null=True)

#     #luke this block; nopat and roic
#     nopat = models.IntegerField(blank=True, null=True)
#     investedCapital = models.IntegerField(blank=True, null=True)
#     roic = models.FloatField(blank=True, null=True)
#     adjRoic = models.FloatField(blank=True, null=True)
#     reportedAdjRoic = models.FloatField(blank=True, null=True)
#     reportedRoce = models.FloatField(blank=True, null=True)
#     calculatedRoce = models.FloatField(blank=True, null=True)
#     cReitROE = models.FloatField(blank=True, null=True)
#     cReitROEGrowthRate = models.FloatField(blank=True, null=True)
#     rReitROE = models.FloatField(blank=True, null=True)
#     rReitROEGrowthRate = models.FloatField(blank=True, null=True)
    
#     shares = models.IntegerField(blank=True, null=True)
#     sharesGrowthRate = models.FloatField(blank=True, null=True)
#     #luke all diluteds
#     dilutedShares = models.IntegerField(blank=True, null=True)
#     dilutedSharesGrowthRate = models.FloatField(blank=True, null=True)
#     reportedEPS = models.FloatField(blank=True, null=True)
#     reportedEPSGrowthRate = models.FloatField(blank=True, null=True)
#     calculatedEPS = models.FloatField(blank=True, null=True)
#     calculatedEPSGrowthRate = models.FloatField(blank=True, null=True)

#     divsPaidPerShare = models.FloatField(blank=True, null=True)
#     calcDivsPerShare = models.FloatField(blank=True, null=True)
#     totalDivsPaid = models.IntegerField(blank=True, null=True)
#     divGrowthRateBOT = models.FloatField(blank=True, null=True)
#     divGrowthRateBORPS = models.FloatField(blank=True, null=True)
#     divGrowthRateBOCPS = models.FloatField(blank=True, null=True)
#     payoutRatio = models.FloatField(blank=True, null=True)
#     fcfPayoutRatio = models.FloatField(blank=True, null=True)
#     ffoPayoutRatio = models.FloatField(blank=True, null=True)

#     #luke this block
#     ROCTotal = models.IntegerField(blank=True, null=True)
#     ROCTotalGrowthRate = models.FloatField(blank=True, null=True)
#     ROCperShare = models.FloatField(blank=True, null=True)
#     ROCperShareGrowthRate = models.FloatField(blank=True, null=True)

#     nav = models.FloatField(blank=True, null=True)
#     navGrowthRate = models.FloatField(blank=True, null=True)
#     calcBookValue = models.FloatField(blank=True, null=True)
#     calcBookValueGrowthRate = models.FloatField(blank=True, null=True)
#     reportedBookValue = models.FloatField(blank=True, null=True)
#     reportedBookValueGrowthRate = models.FloatField(blank=True, null=True)

#     price = models.FloatField(blank=True, null=True)
#     priceGrowthRate = models.FloatField(blank=True, null=True)

#     #luke this block
#     DIVintegrityFlag = models.CharField(max_length=10, blank=True, null=True)
#     INCintegrityFlag = models.CharField(max_length=10, blank=True, null=True)
#     ROICintegrityFlag = models.CharField(max_length=10, blank=True, null=True)

#     year = models.CharField(max_length=4, blank=True, null=True)
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     CIK = models.CharField(max_length=10, blank=True, null=True)
#     Units = models.CharField(max_length=10,blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     Industry = models.CharField(max_length=50, blank=True, null=True)

#     class Meta:
#         db_table = 'Mega_Backup'

# class Metadata_Backup(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     FirstYear = models.CharField(max_length=4, blank=True, null=True)
#     LatestYear = models.CharField(max_length=4, blank=True, null=True)
#     AveragedOverYears  = models.CharField(max_length=4, blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     Industry = models.CharField(max_length=50, blank=True, null=True)
#     revGrowthAVG = models.FloatField(blank=True, null=True)
#     revGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     revGrowthAVGnz = models.FloatField(blank=True, null=True)
#     netIncomeLow = models.IntegerField(blank=True, null=True)
#     netIncomeGrowthAVG = models.FloatField(blank=True, null=True)
#     netIncomeGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     netIncomeGrowthAVGnz = models.FloatField(blank=True, null=True)
#     netIncomeNCILow = models.IntegerField(blank=True, null=True)
#     netIncomeNCIGrowthAVG = models.FloatField(blank=True, null=True)
#     netIncomeNCIGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     netIncomeNCIGrowthAVGnz = models.FloatField(blank=True, null=True)
#     ffoLow = models.IntegerField(blank=True, null=True)
#     ffoGrowthAVG = models.FloatField(blank=True, null=True)
#     ffoGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     ffoGrowthAVGnz = models.FloatField(blank=True, null=True)

#     repsLow = models.FloatField(blank=True, null=True)
#     repsAVG = models.FloatField(blank=True, null=True)
#     repsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     repsAVGnz = models.FloatField(blank=True, null=True)
        
#     repsGrowthAVG = models.FloatField(blank=True, null=True)
#     repsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     repsGrowthAVGnz = models.FloatField(blank=True, null=True)

#     cepsLow = models.FloatField(blank=True, null=True)
#     cepsAVG = models.FloatField(blank=True, null=True)
#     cepsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     cepsAVGnz = models.FloatField(blank=True, null=True)

#     cepsGrowthAVG = models.FloatField(blank=True, null=True)
#     cepsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     cepsGrowthAVGnz = models.FloatField(blank=True, null=True)

#     reitepsLow = models.FloatField(blank=True, null=True)
#     reitepsAVG = models.FloatField(blank=True, null=True)
#     reitepsAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     reitepsAVGnz = models.FloatField(blank=True, null=True)

#     reitepsGrowthAVG = models.FloatField(blank=True, null=True)
#     reitepsGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     reitepsGrowthAVGnz = models.FloatField(blank=True, null=True)

#     fcfLow = models.IntegerField(blank=True, null=True)
#     fcfGrowthAVG = models.FloatField(blank=True, null=True)
#     fcfGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     fcfGrowthAVGnz = models.FloatField(blank=True, null=True)
#     fcfMarginLow = models.FloatField(blank=True, null=True)
#     fcfMarginHigh = models.FloatField(blank=True, null=True)
#     fcfMarginAVG = models.FloatField(blank=True, null=True)
#     fcfMarginGrowthAVG = models.FloatField(blank=True, null=True)
#     fcfMarginGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     fcfMarginGrowthAVGnz = models.FloatField(blank=True, null=True)
#     priceLow = models.FloatField(blank=True, null=True)
#     priceHigh = models.FloatField(blank=True, null=True)
#     priceLatest = models.FloatField(blank=True, null=True)
#     priceAVG = models.FloatField(blank=True, null=True)
#     priceGrowthAVG = models.FloatField(blank=True, null=True)
#     debtGrowthAVG = models.FloatField(blank=True, null=True)
#     reportedEquityLow = models.IntegerField(blank=True, null=True)
#     reportedEquityGrowthAVG = models.FloatField(blank=True, null=True)
#     reportedEquityGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     reportedEquityGrowthAVGnz = models.FloatField(blank=True, null=True)
#     calculatedEquityLow = models.IntegerField(blank=True, null=True)
#     calculatedEquityGrowthAVG = models.FloatField(blank=True, null=True)
#     calculatedEquityGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     calculatedEquityGrowthAVGnz = models.FloatField(blank=True, null=True)
#     aggEquityGrowthAVG = models.FloatField(blank=True, null=True)
#     operatingCashFlowLow = models.IntegerField(blank=True, null=True)
#     operatingCashFlowAVG = models.FloatField(blank=True, null=True)
#     operatingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     operatingCashFlowAVGnz = models.FloatField(blank=True, null=True)
#     operatingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
#     operatingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     operatingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)
#     investingCashFlowLow = models.IntegerField(blank=True, null=True)
#     investingCashFlowAVG = models.FloatField(blank=True, null=True)
#     investingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     investingCashFlowAVGnz = models.FloatField(blank=True, null=True)
#     investingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
#     investingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     investingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)
#     financingCashFlowLow = models.IntegerField(blank=True, null=True)
#     financingCashFlowAVG = models.FloatField(blank=True, null=True)
#     financingCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     financingCashFlowAVGnz = models.FloatField(blank=True, null=True)
#     financingCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
#     financingCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     financingCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)
#     netCashFlowLow = models.IntegerField(blank=True, null=True)
#     netCashFlowAVG = models.FloatField(blank=True, null=True)
#     netCashFlowAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     netCashFlowAVGnz = models.FloatField(blank=True, null=True)
#     netCashFlowGrowthAVG = models.FloatField(blank=True, null=True)
#     netCashFlowGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     netCashFlowGrowthAVGnz = models.FloatField(blank=True, null=True)
#     capexGrowthAVG = models.FloatField(blank=True, null=True)
#     capexGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     capexGrowthAVGnz = models.FloatField(blank=True, null=True)
#     sharesGrowthAVG = models.FloatField(blank=True, null=True)
#     dilutedSharesGrowthAVG = models.FloatField(blank=True, null=True)
#     totalDivsPaidGrowthAVG = models.FloatField(blank=True, null=True)
#     totalDivsPaidGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     totalDivsPaidGrowthAVGnz = models.FloatField(blank=True, null=True)
#     calcDivsPerShareLow = models.FloatField(blank=True, null=True)
#     calcDivsPerShareHigh = models.FloatField(blank=True, null=True)
#     calcDivsPerShareLatest = models.FloatField(blank=True, null=True)
#     calcDivsPerShareAVG = models.FloatField(blank=True, null=True)
#     calcDivsPerShareGrowthLow = models.FloatField(blank=True, null=True)
#     calcDivsPerShareGrowthHigh = models.FloatField(blank=True, null=True)
#     calcDivsPerShareGrowthAVG = models.FloatField(blank=True, null=True)
#     calcDivsPerShareGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     calcDivsPerShareGrowthAVGnz = models.FloatField(blank=True, null=True)
#     repDivsPerShareLow = models.FloatField(blank=True, null=True)
#     repDivsPerShareHigh = models.FloatField(blank=True, null=True)
#     repDivsPerShareLatest = models.FloatField(blank=True, null=True)
#     repDivsPerShareAVG = models.FloatField(blank=True, null=True)
#     repDivsPerShareGrowthLow = models.FloatField(blank=True, null=True)
#     repDivsPerShareGrowthHigh = models.FloatField(blank=True, null=True)
#     repDivsPerShareGrowthAVG = models.FloatField(blank=True, null=True)
#     repDivsPerShareGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     repDivsPerShareGrowthAVGnz = models.FloatField(blank=True, null=True)
#     aggDivsPSLow = models.FloatField(blank=True, null=True)
#     aggDivsPSHigh = models.FloatField(blank=True, null=True)
#     aggDivsPSAVG = models.FloatField(blank=True, null=True)
#     aggDivsPSGrowthLow = models.FloatField(blank=True, null=True)
#     aggDivsPSGrowthHigh = models.FloatField(blank=True, null=True)
#     aggDivsPSGrowthAVG = models.FloatField(blank=True, null=True)
#     aggDivsGrowthLow = models.FloatField(blank=True, null=True)
#     aggDivsGrowthHigh = models.FloatField(blank=True, null=True)
#     aggDivsGrowthAVG = models.FloatField(blank=True, null=True)
#     payoutRatioLow = models.FloatField(blank=True, null=True)
#     payoutRatioHigh = models.FloatField(blank=True, null=True)
#     payoutRatioAVG = models.FloatField(blank=True, null=True)
#     payoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     payoutRatioAVGnz = models.FloatField(blank=True, null=True)
#     fcfPayoutRatioLow = models.FloatField(blank=True, null=True)
#     fcfPayoutRatioHigh = models.FloatField(blank=True, null=True)
#     fcfPayoutRatioAVG = models.FloatField(blank=True, null=True)
#     fcfPayoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     fcfPayoutRatioAVGnz = models.FloatField(blank=True, null=True)
#     ffoPayoutRatioLow = models.FloatField(blank=True, null=True)
#     ffoPayoutRatioHigh = models.FloatField(blank=True, null=True)
#     ffoPayoutRatioAVG = models.FloatField(blank=True, null=True)
#     ffoPayoutRatioAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     ffoPayoutRatioAVGnz = models.FloatField(blank=True, null=True)
#     ROCpsAVG = models.FloatField(blank=True, null=True)
#     numYearsROCpaid = models.IntegerField(blank=True, null=True)
#     roicLow = models.FloatField(blank=True, null=True)
#     roicHigh = models.FloatField(blank=True, null=True)
#     roicAVG = models.FloatField(blank=True, null=True)
#     aroicLow = models.FloatField(blank=True, null=True)
#     aroicHigh = models.FloatField(blank=True, null=True)
#     aroicAVG = models.FloatField(blank=True, null=True)
#     raroicLow = models.FloatField(blank=True, null=True)
#     raroicHigh = models.FloatField(blank=True, null=True)
#     raroicAVG = models.FloatField(blank=True, null=True)
#     aggaroicLow = models.FloatField(blank=True, null=True)
#     aggaroicHigh = models.FloatField(blank=True, null=True)
#     aggaroicAVG = models.FloatField(blank=True, null=True)
#     croceLow = models.FloatField(blank=True, null=True)
#     croceHigh = models.FloatField(blank=True, null=True)
#     croceAVG = models.FloatField(blank=True, null=True)
#     rroceLow = models.FloatField(blank=True, null=True)
#     rroceHigh = models.FloatField(blank=True, null=True)
#     rroceAVG = models.FloatField(blank=True, null=True)
#     aggroceLow = models.FloatField(blank=True, null=True)
#     aggroceHigh = models.FloatField(blank=True, null=True)
#     aggroceAVG = models.FloatField(blank=True, null=True)
#     calcBookValueLow = models.FloatField(blank=True, null=True)
#     calcBookValueAVG = models.FloatField(blank=True, null=True)
#     calcBookValueGrowthAVG = models.FloatField(blank=True, null=True)
#     calcBookValueGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     calcBookValueGrowthAVGnz = models.FloatField(blank=True, null=True)
#     repBookValueLow = models.FloatField(blank=True, null=True)
#     repBookValueAVG = models.FloatField(blank=True, null=True)
#     repBookValueGrowthAVG = models.FloatField(blank=True, null=True)
#     repBookValueGrowthAVGintegrity = models.CharField(max_length=10, blank=True, null=True)
#     repBookValueGrowthAVGnz = models.FloatField(blank=True, null=True)
#     aggBookValueLow = models.FloatField(blank=True, null=True)
#     aggBookValueAVG = models.FloatField(blank=True, null=True)
#     aggBookValueGrowthAVG = models.FloatField(blank=True, null=True)
#     navAVG = models.FloatField(blank=True, null=True)
#     navGrowthAVG = models.FloatField(blank=True, null=True)
#     calcDivYieldLatest = models.FloatField(blank=True, null=True)
#     calcDivYieldAVG = models.FloatField(blank=True, null=True)
#     repDivYieldLatest = models.FloatField(blank=True, null=True)
#     repDivYieldAVG = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Metadata_Backup'

# class Materials_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Materials_Ranking'

# class Communications_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Communications_Ranking'

# class Energy_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Energy_Ranking'

# class Financials_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Financials_Ranking'

# class BDC_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'BDC_Ranking'

# class Industrials_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Industrials_Ranking'

# class Tech_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Tech_Ranking'

# class ConsumerDefensive_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'ConsumerDefensive_Ranking'

# class RealEstate_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     reitroce = models.IntegerField(blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'RealEstate_Ranking'

# class Utilities_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Utilities_Ranking'

# class Healthcare_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'Healthcare_Ranking'

# class ConsumerCyclical_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)
#     scorerank = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'ConsumerCyclical_Ranking'

# class PDValuation(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)

#     currentPrice = models.FloatField(blank=True, null=True)
#     currentDiv = models.FloatField(blank=True, null=True)
#     currentValuation = models.FloatField(blank=True, null=True)

#     priceGR = tenYearDiv = models.FloatField(blank=True, null=True)
#     divGR = models.FloatField(blank=True, null=True)

#     tenYearPrice = models.FloatField(blank=True, null=True)
#     tenYearDiv = models.FloatField(blank=True, null=True)
#     tenYearValuation = models.FloatField(blank=True, null=True)
    
#     twentyYearPrice = models.FloatField(blank=True, null=True)
#     twentyYearDiv = models.FloatField(blank=True, null=True)
#     twentyYearValuation = models.FloatField(blank=True, null=True)

#     class Meta:
#         db_table = 'PDValuation'

# class Investable_Universe(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=5, blank=True, null=True)
#     Type = models.CharField(max_length=5, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'Investable_Universe'

# class Growth_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxplainscore = models.IntegerField(blank=True, null=True)
#     plainscore = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'Growth_Ranking'

# class QualNonDivPayers_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     maxplainscore = models.IntegerField(blank=True, null=True)
#     plainscore = models.IntegerField(blank=True, null=True)
#     maxscore = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'QualNonDivPayers_Ranking'

# class FullWeight_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'FullWeight_Ranking'

# class REITFullWeight_Ranking(models.Model):
#     Ticker = models.CharField(max_length=10, blank=True, null=True)
#     Sector = models.CharField(max_length=30, blank=True, null=True)
#     roce = models.IntegerField(blank=True, null=True)
#     roic = models.IntegerField(blank=True, null=True)
#     roc = models.IntegerField(blank=True, null=True)
#     ffopo = models.IntegerField(blank=True, null=True)
#     po = models.IntegerField(blank=True, null=True)
#     divgr = models.IntegerField(blank=True, null=True)
#     divpay = models.IntegerField(blank=True, null=True)
#     shares = models.IntegerField(blank=True, null=True)
#     cf = models.IntegerField(blank=True, null=True)
#     bv = models.IntegerField(blank=True, null=True)
#     equity = models.IntegerField(blank=True, null=True)
#     debt = models.IntegerField(blank=True, null=True)
#     fcfm = models.IntegerField(blank=True, null=True)
#     fcf = models.IntegerField(blank=True, null=True)
#     ffo = models.IntegerField(blank=True, null=True)
#     ni = models.IntegerField(blank=True, null=True)
#     rev = models.IntegerField(blank=True, null=True)
#     divyield = models.IntegerField(blank=True, null=True)
#     score = models.IntegerField(blank=True, null=True)

#     class Meta:
#         db_table = 'REITFullWeight_Ranking'