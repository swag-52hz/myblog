from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class NewUserManager(UserManager):
    def create_superuser(self, username, password, email=None, **extra_fields):
        super(NewUserManager, self).create_superuser(username=username, password=password, email=email, **extra_fields)


class User(AbstractUser):

    objects = NewUserManager()

    phone = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['phone']

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
