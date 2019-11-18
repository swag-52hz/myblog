import json
import random
import string
import logging
from django.http import HttpResponse
from django_redis import get_redis_connection
from utils.captcha.captcha import captcha
from .constants import IMAGE_CODE_EXPIRE_TIME, SMS_CODE_NUM
from .forms import SmsCodeForm
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from utils import zhenzismsclient as smsclient
from users.models import User
from django.views import View


# 导入在setting中设置好的日志器
logger = logging.getLogger('django')


class ImageCode(View):
    def get(self, request, image_code_id):
        # 生成验证码以及图片
        text, image = captcha.generate_captcha()
        # 与redis数据库建立连接
        redis_conn = get_redis_connection(alias='verify_codes')
        # 生成图片验证码的键
        img_key = 'img_{}'.format(image_code_id)
        # 存入redi数据库，并设置过期时间
        redis_conn.setex(img_key, IMAGE_CODE_EXPIRE_TIME, text)
        # 输出日志，打印验证码信息，便于调试
        logger.info('image_code: {}'.format(text))
        # 返回给前端图片验证码，并指定图片格式
        return HttpResponse(content=image, content_type='image/jpg')


class CheckUsername(View):
    def get(self, request, username):
        # 从数据库中查询是否存在这个用户名
        count = User.objects.filter(username=username).count()
        # 构建数据字典
        data = {
            'count': count,
            'username': username
        }
        # 返回json数据给前端
        return to_json_data(data=data)


class CheckPhone(View):
    def get(self, request, mobile):
        # 从数据库中查询是否存在这个手机号
        count = User.objects.filter(phone=mobile).count()
        # 构建数据字典
        data = {
            'count': count,
            'mobile': mobile
        }
        # 返回json数据给前端
        return to_json_data(data=data)


class SmsCodeView(View):
    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        form = SmsCodeForm(data=dict_data)
        if form.is_valid():
            mobile = form.cleaned_data.get('mobile')
            sms_num = ''.join([random.choice(string.digits) for _ in range(SMS_CODE_NUM)])
            redis_conn = get_redis_connection('verify_codes')
            sms_key = 'sms_{}'.format(mobile)
            sms_flag_key = 'sms_flag_{}'.format(mobile)
            p1 = redis_conn.pipeline()
            try:
                p1.setex(sms_flag_key, 60, 1)
                p1.setex(sms_key, 300, sms_num)
                p1.execute()
            except Exception as e:
                logger.debug('redis执行异常: {}'.format(e))
                return to_json_data(errno=Code.UNKOWNERR, errmsg='redis执行异常')
            try:
                client = smsclient.ZhenziSmsClient('https://sms_developer.zhenzikj.com', '101357',
                                                   'bf00ccbc-1f60-4f1c-a739-ba9ec7f4872d')
                # result = client.send(mobile, '您的验证码为' + sms_num)
                # res = int(result[8])
                res = 0
            except Exception as e:
                logger.debug('短信验证码发送[异常]: {}'.format(e))
                return to_json_data(errno=Code.SMSERROR, errmsg=error_map[Code.SMSERROR])
            else:
                if res == 0:
                    logger.info('{}短信验证码发送[成功]: {}'.format(mobile, sms_num))
                    return to_json_data(errmsg='短信验证码发送成功')
                else:
                    logger.debug('{}短信验证码发送[失败]: {}'.format(mobile, sms_num))
                    return to_json_data(errno=Code.SMSFAIL, errmsg=error_map[Code.SMSFAIL])
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class SendSmsCode(View):
    def get(self, request, phone):
        sms_num = ''.join([random.choice(string.digits) for _ in range(SMS_CODE_NUM)])
        redis_conn = get_redis_connection('verify_codes')
        sms_key = 'sms_{}'.format(phone)
        sms_flag_key = 'sms_flag_{}'.format(phone)
        p1 = redis_conn.pipeline()
        try:
            p1.setex(sms_flag_key, 60, 1)
            p1.setex(sms_key, 300, sms_num)
            p1.execute()
        except Exception as e:
            logger.debug('redis执行异常: {}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='redis执行异常')
        try:
            client = smsclient.ZhenziSmsClient('https://sms_developer.zhenzikj.com', '101357',
                                               'bf00ccbc-1f60-4f1c-a739-ba9ec7f4872d')
            # result = client.send(mobile, '您的验证码为' + sms_num)
            # res = int(result[8])
            res = 0
        except Exception as e:
            logger.debug('短信验证码发送[异常]: {}'.format(e))
            return to_json_data(errno=Code.SMSERROR, errmsg=error_map[Code.SMSERROR])
        else:
            if res == 0:
                logger.info('{}短信验证码发送[成功]: {}'.format(phone, sms_num))
                return to_json_data(errmsg='短信验证码发送成功')
            else:
                logger.debug('{}短信验证码发送[失败]: {}'.format(phone, sms_num))
                return to_json_data(errno=Code.SMSFAIL, errmsg=error_map[Code.SMSFAIL])
