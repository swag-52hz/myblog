from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class NewUserManager(UserManager):
    def create_superuser(self, username, password, email=None, **extra_fields):
        super(NewUserManager, self).create_superuser(username=username, password=password, email=email, **extra_fields)


class User(AbstractUser):

    objects = NewUserManager()

    phone = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    avatar_url = models.URLField(default='/media/avatar.jpeg', verbose_name='用户头像url')
    email_active = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['phone']

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_groups_name(self):
        group_name_list = [group.name for group in self.groups.all()]
        return '|'.join(group_name_list)


class Follow(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='用户', related_name='user')
    followed = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='用户的关注', related_name='followed')
    status = models.BooleanField(default=False, verbose_name='是否关注')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_follow'
        verbose_name = '用户关注'
        verbose_name_plural = verbose_name


class Fans(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='用户', related_name='users')
    follower = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='用户的粉丝', related_name='follower')
    status = models.BooleanField(default=False, verbose_name='是否关注')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_fans'
        verbose_name = '用户粉丝'
        verbose_name_plural = verbose_name