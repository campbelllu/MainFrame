# Generated by Django 4.2.11 on 2024-06-11 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_center', '0004_rename_mixedequitygrowthavg_metadata_aggequitygrowthavg_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata_Backup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Ticker', models.CharField(blank=True, max_length=10, null=True)),
                ('FirstYear', models.CharField(blank=True, max_length=4, null=True)),
                ('LatestYear', models.CharField(blank=True, max_length=4, null=True)),
                ('AveragedOverYears', models.CharField(blank=True, max_length=4, null=True)),
                ('Sector', models.CharField(blank=True, max_length=30, null=True)),
                ('Industry', models.CharField(blank=True, max_length=50, null=True)),
                ('revGrowthAVG', models.FloatField(blank=True, null=True)),
                ('revGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('revGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('netIncomeLow', models.IntegerField(blank=True, null=True)),
                ('netIncomeGrowthAVG', models.FloatField(blank=True, null=True)),
                ('netIncomeGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('netIncomeGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('netIncomeNCILow', models.IntegerField(blank=True, null=True)),
                ('netIncomeNCIGrowthAVG', models.FloatField(blank=True, null=True)),
                ('netIncomeNCIGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('netIncomeNCIGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('ffoLow', models.IntegerField(blank=True, null=True)),
                ('ffoGrowthAVG', models.FloatField(blank=True, null=True)),
                ('ffoGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('ffoGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('fcfLow', models.IntegerField(blank=True, null=True)),
                ('fcfGrowthAVG', models.FloatField(blank=True, null=True)),
                ('fcfGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('fcfGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('fcfMarginLow', models.FloatField(blank=True, null=True)),
                ('fcfMarginHigh', models.FloatField(blank=True, null=True)),
                ('fcfMarginAVG', models.FloatField(blank=True, null=True)),
                ('fcfMarginGrowthAVG', models.FloatField(blank=True, null=True)),
                ('fcfMarginGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('fcfMarginGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('priceLow', models.FloatField(blank=True, null=True)),
                ('priceHigh', models.FloatField(blank=True, null=True)),
                ('priceLatest', models.FloatField(blank=True, null=True)),
                ('priceAVG', models.FloatField(blank=True, null=True)),
                ('priceGrowthAVG', models.FloatField(blank=True, null=True)),
                ('debtGrowthAVG', models.FloatField(blank=True, null=True)),
                ('reportedEquityLow', models.IntegerField(blank=True, null=True)),
                ('reportedEquityGrowthAVG', models.FloatField(blank=True, null=True)),
                ('reportedEquityGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('reportedEquityGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('calculatedEquityLow', models.IntegerField(blank=True, null=True)),
                ('calculatedEquityGrowthAVG', models.FloatField(blank=True, null=True)),
                ('calculatedEquityGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('calculatedEquityGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('aggEquityGrowthAVG', models.FloatField(blank=True, null=True)),
                ('operatingCashFlowLow', models.IntegerField(blank=True, null=True)),
                ('operatingCashFlowAVG', models.FloatField(blank=True, null=True)),
                ('operatingCashFlowAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('operatingCashFlowAVGnz', models.FloatField(blank=True, null=True)),
                ('operatingCashFlowGrowthAVG', models.FloatField(blank=True, null=True)),
                ('operatingCashFlowGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('operatingCashFlowGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('investingCashFlowLow', models.IntegerField(blank=True, null=True)),
                ('investingCashFlowAVG', models.FloatField(blank=True, null=True)),
                ('investingCashFlowAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('investingCashFlowAVGnz', models.FloatField(blank=True, null=True)),
                ('investingCashFlowGrowthAVG', models.FloatField(blank=True, null=True)),
                ('investingCashFlowGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('investingCashFlowGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('financingCashFlowLow', models.IntegerField(blank=True, null=True)),
                ('financingCashFlowAVG', models.FloatField(blank=True, null=True)),
                ('financingCashFlowAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('financingCashFlowAVGnz', models.FloatField(blank=True, null=True)),
                ('financingCashFlowGrowthAVG', models.FloatField(blank=True, null=True)),
                ('financingCashFlowGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('financingCashFlowGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('netCashFlowLow', models.IntegerField(blank=True, null=True)),
                ('netCashFlowAVG', models.FloatField(blank=True, null=True)),
                ('netCashFlowAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('netCashFlowAVGnz', models.FloatField(blank=True, null=True)),
                ('netCashFlowGrowthAVG', models.FloatField(blank=True, null=True)),
                ('netCashFlowGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('netCashFlowGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('capexGrowthAVG', models.FloatField(blank=True, null=True)),
                ('capexGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('capexGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('sharesGrowthAVG', models.FloatField(blank=True, null=True)),
                ('dilutedSharesGrowthAVG', models.FloatField(blank=True, null=True)),
                ('totalDivsPaidGrowthAVG', models.FloatField(blank=True, null=True)),
                ('totalDivsPaidGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('totalDivsPaidGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareLow', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareHigh', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareLatest', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareAVG', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareGrowthLow', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareGrowthHigh', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareGrowthAVG', models.FloatField(blank=True, null=True)),
                ('calcDivsPerShareGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('calcDivsPerShareGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareLow', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareHigh', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareLatest', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareAVG', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareGrowthLow', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareGrowthHigh', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareGrowthAVG', models.FloatField(blank=True, null=True)),
                ('repDivsPerShareGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('repDivsPerShareGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('aggDivsPSLow', models.FloatField(blank=True, null=True)),
                ('aggDivsPSHigh', models.FloatField(blank=True, null=True)),
                ('aggDivsPSAVG', models.FloatField(blank=True, null=True)),
                ('aggDivsPSGrowthLow', models.FloatField(blank=True, null=True)),
                ('aggDivsPSGrowthHigh', models.FloatField(blank=True, null=True)),
                ('aggDivsPSGrowthAVG', models.FloatField(blank=True, null=True)),
                ('aggDivsGrowthLow', models.FloatField(blank=True, null=True)),
                ('aggDivsGrowthHigh', models.FloatField(blank=True, null=True)),
                ('aggDivsGrowthAVG', models.FloatField(blank=True, null=True)),
                ('payoutRatioLow', models.FloatField(blank=True, null=True)),
                ('payoutRatioHigh', models.FloatField(blank=True, null=True)),
                ('payoutRatioAVG', models.FloatField(blank=True, null=True)),
                ('payoutRatioAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('payoutRatioAVGnz', models.FloatField(blank=True, null=True)),
                ('fcfPayoutRatioLow', models.FloatField(blank=True, null=True)),
                ('fcfPayoutRatioHigh', models.FloatField(blank=True, null=True)),
                ('fcfPayoutRatioAVG', models.FloatField(blank=True, null=True)),
                ('fcfPayoutRatioAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('fcfPayoutRatioAVGnz', models.FloatField(blank=True, null=True)),
                ('ffoPayoutRatioLow', models.FloatField(blank=True, null=True)),
                ('ffoPayoutRatioHigh', models.FloatField(blank=True, null=True)),
                ('ffoPayoutRatioAVG', models.FloatField(blank=True, null=True)),
                ('ffoPayoutRatioAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('ffoPayoutRatioAVGnz', models.FloatField(blank=True, null=True)),
                ('ROCpsAVG', models.FloatField(blank=True, null=True)),
                ('numYearsROCpaid', models.IntegerField(blank=True, null=True)),
                ('roicLow', models.FloatField(blank=True, null=True)),
                ('roicHigh', models.FloatField(blank=True, null=True)),
                ('roicAVG', models.FloatField(blank=True, null=True)),
                ('aroicLow', models.FloatField(blank=True, null=True)),
                ('aroicHigh', models.FloatField(blank=True, null=True)),
                ('aroicAVG', models.FloatField(blank=True, null=True)),
                ('raroicLow', models.FloatField(blank=True, null=True)),
                ('raroicHigh', models.FloatField(blank=True, null=True)),
                ('raroicAVG', models.FloatField(blank=True, null=True)),
                ('aggaroicLow', models.FloatField(blank=True, null=True)),
                ('aggaroicHigh', models.FloatField(blank=True, null=True)),
                ('aggaroicAVG', models.FloatField(blank=True, null=True)),
                ('croceLow', models.FloatField(blank=True, null=True)),
                ('croceHigh', models.FloatField(blank=True, null=True)),
                ('croceAVG', models.FloatField(blank=True, null=True)),
                ('rroceLow', models.FloatField(blank=True, null=True)),
                ('rroceHigh', models.FloatField(blank=True, null=True)),
                ('rroceAVG', models.FloatField(blank=True, null=True)),
                ('aggroceLow', models.FloatField(blank=True, null=True)),
                ('aggroceHigh', models.FloatField(blank=True, null=True)),
                ('aggroceAVG', models.FloatField(blank=True, null=True)),
                ('calcBookValueLow', models.FloatField(blank=True, null=True)),
                ('calcBookValueAVG', models.FloatField(blank=True, null=True)),
                ('calcBookValueGrowthAVG', models.FloatField(blank=True, null=True)),
                ('calcBookValueGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('calcBookValueGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('repBookValueLow', models.FloatField(blank=True, null=True)),
                ('repBookValueAVG', models.FloatField(blank=True, null=True)),
                ('repBookValueGrowthAVG', models.FloatField(blank=True, null=True)),
                ('repBookValueGrowthAVGintegrity', models.CharField(blank=True, max_length=10, null=True)),
                ('repBookValueGrowthAVGnz', models.FloatField(blank=True, null=True)),
                ('aggBookValueLow', models.FloatField(blank=True, null=True)),
                ('aggBookValueAVG', models.FloatField(blank=True, null=True)),
                ('aggBookValueGrowthAVG', models.FloatField(blank=True, null=True)),
                ('navAVG', models.FloatField(blank=True, null=True)),
                ('navGrowthAVG', models.FloatField(blank=True, null=True)),
                ('calcDivYieldLatest', models.FloatField(blank=True, null=True)),
                ('calcDivYieldAVG', models.FloatField(blank=True, null=True)),
                ('repDivYieldLatest', models.FloatField(blank=True, null=True)),
                ('repDivYieldAVG', models.FloatField(blank=True, null=True)),
            ],
            options={
                'db_table': 'Metadata_Backup',
            },
        ),
    ]
