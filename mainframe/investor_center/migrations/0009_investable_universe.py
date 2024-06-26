# Generated by Django 4.2.11 on 2024-06-26 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_center', '0008_sector_rankings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Investable_Universe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Ticker', models.CharField(blank=True, max_length=10, null=True)),
                ('Sector', models.CharField(blank=True, max_length=5, null=True)),
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
                ('score', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'Investable_Universe',
            },
        ),
    ]
