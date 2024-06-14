# Generated by Django 4.2.11 on 2024-06-10 03:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_center', '0003_metadata'),
    ]

    operations = [
        migrations.RenameField(
            model_name='metadata',
            old_name='mixedEquityGrowthAVG',
            new_name='aggEquityGrowthAVG',
        ),
        migrations.AddField(
            model_name='metadata',
            name='calcDivYieldAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='calcDivYieldLatest',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='calcDivsPerShareLatest',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='financingCashFlowAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='financingCashFlowAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='financingCashFlowAVGnz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='investingCashFlowAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='investingCashFlowAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='investingCashFlowAVGnz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='netCashFlowAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='netCashFlowAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='netCashFlowAVGnz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='operatingCashFlowAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='operatingCashFlowAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='operatingCashFlowAVGnz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='priceLatest',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='repDivYieldAVG',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='repDivYieldLatest',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='metadata',
            name='repDivsPerShareLatest',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='AveragedOverYears',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='FirstYear',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='Industry',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='LatestYear',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='Sector',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='Ticker',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='calcBookValueGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='calcDivsPerShareGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='calculatedEquityGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='capexGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='fcfGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='fcfMarginGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='fcfPayoutRatioAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='ffoGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='ffoPayoutRatioAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='financingCashFlowGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='investingCashFlowGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='netCashFlowGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='netIncomeGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='netIncomeNCIGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='operatingCashFlowGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='payoutRatioAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='repBookValueGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='repDivsPerShareGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='reportedEquityGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='revGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='metadata',
            name='totalDivsPaidGrowthAVGintegrity',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]