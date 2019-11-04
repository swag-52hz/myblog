from datetime import datetime
import json
import logging
from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator, EmptyPage
from myblog import settings
from utils.fastdfs.client import FDFS_Client
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from utils.paginator.paginator_func import get_page_list
from .forms import RegisterForm, LoginForm, NewsPubForm
from django.db.models import Q
from .models import User
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

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.NODATA, errmsg=error_map[Code.NODATA])
        dict_data = json.loads(json_data.decode('utf8'))
        form = NewsPubForm(data=dict_data)
        if form.is_valid():
            # 延缓保存
            news_instance = form.save(commit=False)
            news_instance.author = request.user
            news_instance.save()
            # return to_json_data(errmsg='文章发布成功！')
            return redirect(reverse('news:index') + '/' + str(news_instance.id))
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)