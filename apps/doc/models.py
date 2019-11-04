from django.db import models
from django.core.validators import MaxLengthValidator, MinLengthValidator
from utils.model_base import ModelBase


class Docs(ModelBase):
    file_url = models.URLField(verbose_name='文档url', help_text='文档url')
    title = models.CharField(max_length=200, validators=[MinLengthValidator(1)], verbose_name='文档名称', help_text='文档蒙城')
    desc = models.TextField(validators=[MaxLengthValidator(200), MinLengthValidator(1)], verbose_name='文档描述', help_text='文档描述')
    image_url = models.URLField(default='', verbose_name='文档封面url', help_text='文档封面url')
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, verbose_name='文档上传者')

    class Meta:
        db_table = 'tb_docs'
        verbose_name = '文档'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title