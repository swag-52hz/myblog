# Generated by Django 2.2.6 on 2019-10-08 05:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Depart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='部门名称', max_length=50, verbose_name='部门名称')),
                ('slogan', models.CharField(help_text='口号', max_length=100, verbose_name='口号')),
                ('cost', models.IntegerField(default=0, verbose_name='消费')),
                ('profit', models.IntegerField(default=0, verbose_name='收益')),
                ('c_time', models.DateField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '部门信息表',
                'verbose_name_plural': '部门信息表',
                'db_table': 'depart',
            },
        ),
    ]
