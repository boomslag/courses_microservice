# Generated by Django 3.2.16 on 2023-03-06 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='instructor_first_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='certificate',
            name='instructor_last_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]