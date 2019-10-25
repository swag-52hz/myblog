from django.db import models
from utils.model_base import ModelBase


class Course(ModelBase):
    name = models.CharField(verbose_name='课程名称', max_length=200)
    cover_url = models.URLField(default='', verbose_name='课程封面url')
    video_url = models.URLField(default='', verbose_name='课程视频url')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, verbose_name='课程讲师')
    introduce = models.CharField(verbose_name='课程简介', max_length=200)
    outline = models.CharField(verbose_name='课程大纲', max_length=300)
    file_id = models.CharField(verbose_name='课程视频id', max_length=30)
    duration = models.FloatField(default=0.0, verbose_name='课程时长')
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='课程分类')

    class Meta:
        db_table = 'tb_courses'
        verbose_name = '课程'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Teacher(ModelBase):
    name = models.CharField(verbose_name='讲师姓名', max_length=30)
    avatar_url = models.URLField(default='', verbose_name='头像url')
    profession = models.CharField(verbose_name='职称', max_length=50)
    profile = models.CharField(verbose_name='讲师简介', max_length=300)

    class Meta:
        db_table = 'tb_teachers'
        verbose_name = '讲师'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class CourseCategory(ModelBase):
    name = models.CharField(max_length=200, verbose_name='课程分类名', help_text='课程分类名')

    class Meta:
        db_table = 'tb_course_category'
        verbose_name = '课程分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name