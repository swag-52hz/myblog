from django.db import models
import pytz
from django.core.validators import MinLengthValidator
from utils.model_base import ModelBase


class Tag(ModelBase):
    name = models.CharField(max_length=64, verbose_name='文章标签名', help_text='文章标签名')

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = 'tb_tag'
        verbose_name = '文章标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class News(ModelBase):
    title = models.CharField(max_length=150, validators=[MinLengthValidator(1)], verbose_name='文章标题', help_text='文章标题')
    digest = models.CharField(max_length=200, validators=[MinLengthValidator(1)], verbose_name='文章摘要', help_text='文章摘要')
    content = models.TextField(verbose_name='文章内容', help_text='文章内容')
    clicks = models.IntegerField(default=0, verbose_name='访问量', help_text='访问量')
    image_url = models.URLField(default='', verbose_name='文章缩略图', help_text='文章缩略图')
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = 'tb_news'
        verbose_name = '文章'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Comments(ModelBase):
    content = models.TextField(verbose_name='评论内容', help_text='评论内容')
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    news = models.ForeignKey('News', on_delete=models.CASCADE)
    # 添加父级评论，关联表自身
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def to_dict_data(self):
        # 将时区转换为中国上海
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        # 转换为本地时间
        local_time = shanghai_tz.normalize(self.update_time)
        comment_dict = {
            'content_id': self.id,
            'news_id': self.news_id,
            'content': self.content,
            'update_time': local_time.strftime("%Y-%m-%d %H:%M"),
            'author': self.author.username,
            'avatar_url': self.author.avatar_url,
            'parent': self.parent.to_dict_data() if self.parent else None
        }
        return comment_dict

    class Meta:
        ordering = ['-update_time', '-id']
        db_table = 'tb_comments'
        verbose_name = '文章评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '<评论：{}>'.format(self.id)


class HotNews(ModelBase):
    CHOICES = [
        (1, '第一级'),
        (2, '第二级'),
        (3, '第三级')
    ]
    news = models.OneToOneField('News', on_delete=models.CASCADE)
    priority = models.IntegerField(choices=CHOICES, default=3, verbose_name='热门新闻优先级')

    class Meta:
        ordering = ['-priority', '-update_time', '-id']
        db_table = 'tb_hotnews'
        verbose_name = '热门文章'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '<热门文章：{}>'.format(self.id)


class Banner(ModelBase):
    CHOICES = [
        (1, '第一级'),
        (2, '第二级'),
        (3, '第三级'),
        (4, '第四级'),
        (5, '第五级'),
        (6, '第六级')
    ]
    image_url = models.URLField(verbose_name='轮播图url', help_text='轮播图url')
    priority = models.IntegerField(choices=CHOICES, default=6, verbose_name='轮播图优先级')
    news = models.OneToOneField('News', on_delete=models.CASCADE)

    class Meta:
        ordering = ['priority', '-update_time', '-id']
        db_table = 'tb_banner'
        verbose_name = '轮播图'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '<轮播图：{}>'.format(self.id)