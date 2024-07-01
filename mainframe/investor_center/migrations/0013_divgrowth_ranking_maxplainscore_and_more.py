# Generated by Django 4.2.11 on 2024-06-28 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investor_center', '0012_qualnondivpayers_ranking_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='divgrowth_ranking',
            name='maxplainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='divgrowth_ranking',
            name='plainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='growth_ranking',
            name='maxplainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='growth_ranking',
            name='plainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='investable_universe',
            name='Type',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='qualnondivpayers_ranking',
            name='maxplainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qualnondivpayers_ranking',
            name='plainscore',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]