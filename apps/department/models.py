from django.db import models


class Depart(models.Model):
    name = models.CharField(max_length=50, verbose_name='部门名称', help_text='部门名称')
    slogan = models.CharField(max_length=100, verbose_name='口号', help_text='口号')
    cost = models.IntegerField(default=0, verbose_name='消费')
    profit = models.IntegerField(default=0, verbose_name='收益')
    c_time = models.DateField(verbose_name='创建时间')
    is_delete = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'depart'
        verbose_name = '部门信息表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

