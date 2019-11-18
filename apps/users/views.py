from datetime import datetime
import re
import json
import logging
from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator, EmptyPage
from django_redis import get_redis_connection

from myblog import settings
from utils.fastdfs.client import FDFS_Client
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from utils.paginator.paginator_func import get_page_list
from .forms import RegisterForm, LoginForm, NewsPubForm
from django.db.models import Q, Sum, Count
from .models import User, Fans, Follow
from news import models
from news.models import News, Tag, Comments
from django.views import View
from django.http import Http404
from .constants import USER_SESSION_EXPIRE_TIME
from django.contrib.auth import login, logout


logger = logging.getLogger('django')


class LoginView(View):
    def get(self, request):
        return render(request, 'users/login.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        form = LoginForm(data=dict_data)
        if form.is_valid():
            hold_login = form.cleaned_data.get('remember_me')
            user_account = form.cleaned_data.get('user_account')
            user = User.objects.filter(Q(username=user_account) | Q(phone=user_account)).first()
            if hold_login:
                request.session.set_expiry(USER_SESSION_EXPIRE_TIME)
            else:
                request.session.set_expiry(0)
            login(request, user)
            return to_json_data(errmsg='恭喜您，登录成功！！！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class RegisterView(View):
    def get(self, request):
        return render(request, 'users/register.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        form = RegisterForm(data=dict_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            phone = form.cleaned_data.get('mobile')
            user = User.objects.create_user(username=username, password=password, phone=phone)
            login(request, user)
            return to_json_data(errmsg='恭喜您，注册成功！！！')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


def logout_view(request):
    logout(request)
    return redirect(reverse('news:index'))


class ProfileView(View):
    def get(self, request):
        return render(request, 'users/profile.html')


class UserBlogView(View):
    def get(self, request):
        newes = News.objects.select_related('tag', 'author').filter(is_delete=False, author_id=request.user.id)
        tags = Tag.objects.only('id', 'name').filter(is_delete=False)
        # 计算文章的数量，若大于10则进行分页，否则直接返回文章
        num = newes.count()
        if num > 10:
            try:
                page_num = int(request.GET.get('page', '1'))
            except Exception as e:
                logger.info('获取页码出错：{}'.format(e))
                # 若获取页码出错则返回第一页数据
                page_num = 1
            paginator = Paginator(newes, 10)
            total_page = paginator.num_pages
            page_list = get_page_list(page_num, paginator)
            newes = paginator.get_page(page_num).object_list
        count_list = [news.comments_set.all().count for news in newes]
        dict_data = dict([(count_list[i], newes[i]) for i in range(newes.count())])
        return render(request, 'users/user_blog.html', locals())

    def post(self, request):
        newes = News.objects.select_related('tag', 'author').filter(is_delete=False, author_id=request.user.id)
        try:
            start_time = request.POST.get('start_time', '')
            end_time = request.POST.get('end_time', '')
            start_time = datetime.strptime(start_time, '%Y-%m-%d')
            end_time = datetime.strptime(end_time, '%Y-%m-%d')
        except Exception as e:
            logger.info('获取时间出错：{}'.format(e))
            start_time = end_time = ''
        if start_time and not end_time:
            newes = newes.filter(update_time__gte=start_time)
        if end_time and not start_time:
            newes = newes.filter(update_time__lte=end_time)
        if start_time and end_time:
            newes = newes.filter(update_time__range=(start_time, end_time))
        try:
            tag_id = int(request.POST.get('tag_id', '0'))
            if tag_id:
                if not Tag.objects.only('id').filter(id=tag_id).exists():
                    return Http404('要请求的页面不存在')
        except Exception as e:
            logger.info('获取标签id出错：{}'.format(e))
            return Http404('要请求的页面不存在！')
        title = request.POST.get('title', '')
        if tag_id:
            newes = newes.filter(tag_id=tag_id)
        if title:
            newes = newes.filter(title__icontains=title)
        tags = Tag.objects.only('id', 'name').filter(is_delete=False)
        num = newes.count()
        if num > 10:
            try:
                page_num = int(request.GET.get('page', '1'))
            except Exception as e:
                logger.info('获取页码出错：{}'.format(e))
                # 若获取页码出错则返回第一页数据
                page_num = 1
            paginator = Paginator(newes, 10)
            total_page = paginator.num_pages
            page_list = get_page_list(page_num, paginator)
            newes = paginator.get_page(page_num).object_list
        count_list = [news.comments_set.all().count for news in newes]
        dict_data = dict([(count_list[i], newes[i]) for i in range(newes.count())])
        return render(request, 'users/user_blog.html', locals())


class UploadImage(View):
    def post(self, request):
        image_file = request.FILES.get('image_file', '')
        if not image_file:
            return to_json_data(errno=Code.PARAMERR, errmsg='未选择图片上传')
        if image_file.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
            return to_json_data(errno=Code.PARAMERR, errmsg='不能上传非图片类型！')
        try:
            image_ext_name = image_file.name.split('.')[-1]
        except Exception as e:
            logger.info('获取图片扩展名异常：{}'.format(e))
            image_ext_name = 'jpg'
        # image_file.read():读取文件
        result = FDFS_Client.upload_by_buffer(image_file.read(), image_ext_name)
        if result['Status'] == 'Upload successed.':
            image_url = settings.FASTDFS_SERVER_DOMAIN + result['Remote file_id']
            user = request.user
            user.avatar_url = image_url
            user.save(update_fields = ['avatar_url'])
            return to_json_data(data={'image_url': image_url}, errmsg='图片上传成功！')
        else:
            logger.info('图片上传到FastDFS服务器失败')
            return to_json_data(errno=Code.UNKOWNERR, errmsg='上传图片到服务器失败！')


class NewsPubView(View):
    def get(self, request):
        tags = Tag.objects.only('id', 'name').filter(is_delete=False)
        return render(request, 'users/news_pub.html', locals())


class NewsEditView(View):
    def get(self, request, news_id):
        news = News.objects.filter(id=news_id, is_delete=False).first()
        tags = Tag.objects.only('id', 'name').filter(is_delete=False)
        if not news:
            return Http404('需要编辑的文章不存在！')
        return render(request, 'users/news_pub.html', locals())

    def delete(self, request, news_id):
        news = News.objects.only('id').filter(id=news_id, is_delete=False).first()
        if not news:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的文章不存在！')
        news.is_delete = True
        news.save(update_fields=['is_delete', 'update_time'])
        return to_json_data(errmsg='文章删除成功！')


class FollowView(View):
    def get(self, request):
        follow_count = Follow.objects.filter(user_id=request.user.id, status=True).count()
        followers = Follow.objects.filter(user_id=request.user.id, status=True)
        return render(request, 'users/follow-list.html', locals())


class FansView(View):
    def get(self, request):
        fans_count = Fans.objects.filter(user_id=request.user.id, status=True).count()
        fanses = Fans.objects.filter(user_id=request.user.id, status=True)
        return render(request, 'users/fans-list.html', locals())


class HomePageView(View):
    def get(self, request, author_id):
        author = User.objects.filter(id=author_id).first()
        if not author:
            return render(request, 'base/404notfound.html')
        newes = News.objects.filter(is_delete=False, author=author)
        return render(request, 'users/home_page.html', locals())


class NewsByUserView(View):
    def get(self, request, username):
        author = User.objects.filter(username=username).first()
        if not author:
            return render(request, 'base/404notfound.html')
        order = request.GET.get('order', '')
        if order == 'time':
            newses = models.News.objects.filter(is_delete=False, author=author).\
                         order_by('-update_time').annotate(comment_count=Count('comments'))
        elif order == 'visits':
            newses = models.News.objects.filter(is_delete=False, author=author).\
                         order_by('-clicks').annotate(comment_count=Count('comments'))
        else:
            newses = models.News.objects.filter(is_delete=False, author=author).annotate(comment_count=Count('comments'))
        num = newses.count()
        if num > 10:
            try:
                page_num = int(request.GET.get('page', '1'))
            except Exception as e:
                logger.info('获取页码出错：{}'.format(e))
                # 若获取页码出错则返回第一页数据
                page_num = 1
            paginator = Paginator(newses, 10)
            total_page = paginator.num_pages
            page_list = get_page_list(page_num, paginator)
            newses = paginator.get_page(page_num).object_list
        follow_queryset = Follow.objects.filter(user_id=request.user.id, followed_id=author.id)
        if not follow_queryset:
            focus_status = False
        else:
            follow = follow_queryset.first()
            focus_status = follow.status
        # 计算粉丝数量
        fans_count = Fans.objects.filter(user_id=author.id, status=True).count()
        # 计算作者的文章数量
        news_count = models.News.objects.filter(author_id=author.id, is_delete=False).count()
        # 获取总评论数，总浏览量
        total_clicks = models.News.objects.filter(author_id=author.id, is_delete=False).aggregate(
                clicks=Sum('clicks')).get( 'clicks')
        if total_clicks > 400000:
            total_clicks = '40万+'
        total_comment = models.News.objects.filter(author_id=author.id).aggregate(comments=Count('comments')).get(
            'comments')
        # 获取作者最新的五篇文章，若不足五篇则返回所有
        latest_news = models.News.objects.only('id', 'title'). \
            filter(author_id=author.id, is_delete=False).order_by('-update_time')
        latest_news = latest_news[:5] if latest_news.count() > 5 else latest_news
        tags = Tag.objects.filter(is_delete=False, news__author=author).values('id', 'name'). \
            annotate(news_count=Count('news')).order_by('-news_count')
        data_dict = tags[:5] if tags.count() > 5 else tags
        hot_news = models.News.objects.only('id', 'title', 'clicks'). \
            filter(author=author, is_delete=False).order_by('-clicks')
        hot_news = hot_news[:5] if hot_news.count() > 5 else hot_news
        return render(request, 'users/news-list.html', locals())


class ForgetView(View):
    def get(self, request):
        return render(request, 'users/forget.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        phone = dict_data.get('mobile', '')
        sms_code = dict_data.get('sms_code', '')
        if not phone or not sms_code:
            return to_json_data(errno=Code.DATAERR, errmsg='手机号或验证码不能为空！')
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return to_json_data(errno=Code.DATAERR, errmsg='手机号格式有误！')
        if not User.objects.filter(phone=phone).exists():
            return to_json_data(errno=Code.DATAERR, errmsg='此手机号未被注册！')
        redis_conn = get_redis_connection('verify_codes')
        sms_key = 'sms_{}'.format(phone)
        real_sms_text = redis_conn.get(sms_key)
        if not real_sms_text or sms_code != real_sms_text.decode('utf-8'):
            return to_json_data(errno=Code.DATAERR, errmsg='短信验证失败！')
        res = to_json_data(errmsg='通过验证！！！')
        cookie_key = 'sms_code'.format(phone)
        res.set_cookie(cookie_key, phone, 300)
        return res


class ResetPassword(View):
    def get(self, request):
        return render(request, 'users/reset_password.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        password = dict_data.get('password', '')
        password_repeat = dict_data.get('password_repeat', '')
        if not password or not password_repeat:
            return to_json_data(errno=Code.PARAMERR, errmsg='密码或确认密码不能为空！')
        if password_repeat != password:
            return to_json_data(errno=Code.PARAMERR, errmsg='两次输入的密码不一致！')
        phone = request.COOKIES.get('sms_code', '')
        if not phone:
            return to_json_data(errno=Code.PARAMERR, errmsg='操作时间过长，请重新验证！')
        user = User.objects.filter(phone=phone).first()
        user.set_password(password)
        user.save()
        return to_json_data(errmsg='密码修改成功！')