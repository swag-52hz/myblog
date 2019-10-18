from django import forms
from users.models import User
from django_redis import get_redis_connection
from django.core.validators import RegexValidator


mobile_validator = RegexValidator(r'^1[345789]\d{9}$', '手机号格式不正确')


class SmsCodeForm(forms.Form):
    mobile = forms.CharField(max_length=11, min_length=11, validators=[mobile_validator, ],
                             error_messages={'max_length': '手机号长度有误',
                                             'min_length': '手机号长度有误',
                                             'required': '手机号不能为空'})
    text = forms.CharField(max_length=4, error_messages={
        'max_length': '图片验证码长度不能超过4',
        'required': '图片验证码不饿能为空',
    })
    image_code_id = forms.UUIDField(error_messages={'required': '图片验证码uuid不能为空'})

    def clean(self):
        clean_data = super().clean()
        phone = clean_data.get('mobile')
        img_text = clean_data.get('text')
        image_id = clean_data.get('image_code_id')

        # 判断手机号是否已注册
        if User.objects.filter(phone=phone):
            raise forms.ValidationError('此手机号已注册！！！')

        redis_conn = get_redis_connection(alias='verify_codes')
        img_key = 'img_{}'.format(image_id)
        img_text_origin = redis_conn.get(img_key)
        real_img_text = img_text_origin.decode('utf-8') if img_text_origin else None
        if (not real_img_text) or real_img_text != img_text:
            raise forms.ValidationError('图形验证失败！！！')
        # 验证发送标记是否存在
        sms_flag_key = 'sms_flag_{}'.format(phone)
        sms_flag = redis_conn.get(sms_flag_key)
        if sms_flag:
            raise forms.ValidationError('获取验证码过于频繁！请稍后再试！')