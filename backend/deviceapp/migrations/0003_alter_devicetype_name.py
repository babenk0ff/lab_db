# Generated by Django 4.1.7 on 2023-04-14 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deviceapp', '0002_alter_decimalnumber_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devicetype',
            name='name',
            field=models.CharField(help_text='Аппарат, Блок, Комплекс, Ячейка и т.п.', max_length=64, unique=True, verbose_name='Наименование типа изделия'),
        ),
    ]