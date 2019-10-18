from django.urls import path, re_path
from . import views


app_name = 'verifications'
urlpatterns = [
    path('image_codes/<uuid:image_code_id>/', views.ImageCode.as_view(), name='image_code'),
    re_path(r'usernames/(?P<username>\w{4,20})/', views.CheckUsername.as_view(), name='check_username'),
    re_path(r'mobiles/(?P<mobile>1[345789]\d{9})/', views.CheckPhone.as_view(), name='check_phone'),
    path('sms_codes/', views.SmsCodeView.as_view(), name='sms_code'),
]