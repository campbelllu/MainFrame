# Generated by Django 4.2.11 on 2024-06-28 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_center', '0011_delete_fullweight_ranking'),
    ]

    operations = [
        migrations.CreateModel(
            name='QualNonDivPayers_Ranking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Ticker', models.CharField(blank=True, max_length=10, null=True)),
                ('Sector', models.CharField(blank=True, max_length=30, null=True)),
                ('roce', models.IntegerField(blank=True, null=True)),
                ('roic', models.IntegerField(blank=True, null=True)),
                ('roc', models.IntegerField(blank=True, null=True)),
                ('ffopo', models.IntegerField(blank=True, null=True)),
                ('po', models.IntegerField(blank=True, null=True)),
                ('divgr', models.IntegerField(blank=True, null=True)),
                ('divpay', models.IntegerField(blank=True, null=True)),
                ('shares', models.IntegerField(blank=True, null=True)),
                ('cf', models.IntegerField(blank=True, null=True)),
                ('bv', models.IntegerField(blank=True, null=True)),
                ('equity', models.IntegerField(blank=True, null=True)),
                ('debt', models.IntegerField(blank=True, null=True)),
                ('fcfm', models.IntegerField(blank=True, null=True)),
                ('fcf', models.IntegerField(blank=True, null=True)),
                ('ffo', models.IntegerField(blank=True, null=True)),
                ('ni', models.IntegerField(blank=True, null=True)),
                ('rev', models.IntegerField(blank=True, null=True)),
                ('divyield', models.IntegerField(blank=True, null=True)),
                ('maxscore', models.IntegerField(blank=True, null=True)),
                ('score', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'QualNonDivPayers_Ranking',
            },
        ),
        migrations.AddField(
            model_name='communications_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='communications_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consumercyclical_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='consumercyclical_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='consumerdefensive_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='consumerdefensive_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='divgrowth_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='energy_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='energy_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='financials_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='financials_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='growth_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='healthcare_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='healthcare_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='industrials_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='industrials_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='materials_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='materials_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='realestate_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='realestate_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sector_rankings',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tech_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='tech_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='utilities_ranking',
            name='Sector',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='utilities_ranking',
            name='maxscore',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
