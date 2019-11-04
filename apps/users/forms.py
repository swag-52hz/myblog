from django import forms
from django_redis import get_redis_connection
from django.db.models import Q
from users.models import User
from news.models import Tag, News
import re


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20, min_length=4,
                               error_messages={
                                   'max_length': '用户名长度不能超过20',
                                   'min_length': '用户名长度不能小于4',
                                   'required': '用户名不能为空',
                               })
    password = forms.CharField(max_length=20, min_length=6,
                               error_messages={
                                   'max_length': '密码长度不能超过20',
                                   'min_length': '密码长度不能小于4',
                                   'required': '密码不能为空',
                               })
    password_repeat = forms.CharField(max_length=20, min_length=6,
                                      error_messages={
                                        'max_length': '确认密码长度不能超过20',
                                        'min_length': '确认密码长度不能小于4',
                                        'required': '确认密码不能为空',
                                      })
    mobile = forms.CharField(max_length=11, min_length=11,
                             error_messages={
                                 'max_length': '手机号码长度有误',
                                 'min_length': '手机号码长度有误',
                                 'required': '手机号不能为空'
                             })
    sms_code = forms.CharField(max_length=4, min_length=4,
                               error_messages={
                                   'max_length': '短信验证码长度为4',
                                   'min_length': '短信验证码长度为4',
                                   'required': '短信验证码不能为空',
                               })

    def clean_mobile(self):
        mobile_num = self.cleaned_data.get('mobile')
        if not re.match(r'^1[3-9]\d{9}$', mobile_num):
            raise forms.ValidationError('手机号格式有误！！！')
        if User.objects.filter(phone=mobile_num).exists():
            raise forms.ValidationError('此手机号已被注册！！！')
        return mobile_num

    def clean(self):
        cleaned_data = super().clean()
        passwd = cleaned_data.get('password')
        passwd_repeat = cleaned_data.get('password_repeat')
        phone = cleaned_data.get('mobile')
        sms_text = cleaned_data.get('sms_code')
        if passwd != passwd_repeat:
            raise forms.ValidationError('两次输入的密码不一致！！！')
        redis_conn = get_redis_connection('verify_codes')
        sms_key = 'sms_{}'.format(phone)
        real_sms_text = redis_conn.get(sms_key)
        if not real_sms_text or sms_text != real_sms_text.decode('utf-8'):
            raise forms.ValidationError('短信验证失败！！！')


class LoginForm(forms.Form):
    user_account = forms.CharField(max_length=20, min_length=4,
                                   error_messages={
                                       'max_length': '用户名长度不能超过20',
                                       'min_length': '用户名长度不能小于4',
                                       'required': '用户名不能为空',
                                   })
    password = forms.CharField(max_length=20, min_length=6,
                               error_messages={
                                   'max_length': '密码长度不能超过20',
                                   'min_length': '密码长度不能小于6',
                                   'required': '密码不能为空',
                               })
    remember_me = forms.BooleanField(required=False)

    def clean_user_account(self):
        account = self.cleaned_data.get('user_account')
        if not account:
            raise forms.ValidationError('账号不能为空')
        if not re.match(r'^1[3-9]\d{9}$', account) and (len(account) < 4 or len(account) > 20):
            raise forms.ValidationError('账号格式有误')
        return account

    def clean(self):
        cleaned_data = super().clean()
        account_user = cleaned_data.get('user_account')
        passwd = cleaned_data.get('password')
        user = User.objects.filter(Q(username=account_user) | Q(phone=account_user)).first()
        if not user:
            raise forms.ValidationError('该账号不存在')
        if not user.check_password(passwd):
            raise forms.ValidationError('密码错误')


class NewsPubForm(forms.ModelForm):
    image_url = forms.URLField(error_messages={'required': '图片url不能为空！'})
    # 确保所选标签为数据库中存在的标签
    tag = forms.ModelChoiceField(queryset=Tag.objects.only('id').filter(is_delete=False),
                                 error_messages={
                                     'required': '文章标签不能为空！',
                                     'invalid_choice': '文章标签id不存在',
                                 })

    class Meta:
        model = News
        fields = ['title', 'digest', 'content', 'image_url', 'tag']
        error_messages = {
            'title': {
                'max_length': '文章标题最大长度不能超过150',
                'min_length': '文章标题最小长度不能小于1',
                'required': '文章标题不能为空！'
            },
            'digest': {
                'max_length': '文章摘要最大长度不能超过150',
                'min_length': '文章摘要最小长度不能小于1',
                'required': '文章摘要不能为空！'
            },
            'content': {
                'required': '文章内容不能为空！',
            }
        }