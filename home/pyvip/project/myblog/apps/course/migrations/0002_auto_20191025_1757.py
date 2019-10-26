# Generated by Django 2.2.6 on 2019-10-25 09:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, help_text='逻辑删除', verbose_name='逻辑删除')),
                ('name', models.CharField(help_text='课程分类名', max_length=200, verbose_name='课程分类名')),
            ],
            options={
                'verbose_name': '课程分类',
                'verbose_name_plural': '课程分类',
                'db_table': 'tb_course_category',
            },
        ),
        migrations.AddField(
            model_name='course',
            name='duration',
            field=models.FloatField(default=0.0, verbose_name='课程时长'),
        ),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='course.CourseCategory', verbose_name='课程分类'),
        ),
    ]