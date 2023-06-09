# Generated by Django 3.2.16 on 2023-03-18 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_episodecompletion_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='Paid',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user', models.UUIDField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Viewed',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('user', models.UUIDField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ViewedItem',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('course', models.UUIDField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.viewed')),
            ],
        ),
        migrations.CreateModel(
            name='PaidItem',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('course', models.UUIDField(blank=True, null=True)),
                ('tokenID', models.CharField(blank=True, max_length=256, null=True)),
                ('contractAddress', models.CharField(blank=True, max_length=256, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.paid')),
            ],
        ),
    ]
