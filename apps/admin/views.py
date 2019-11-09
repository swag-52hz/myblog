import json
import logging
from datetime import datetime
from urllib.parse import urlencode

import qiniu
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views import View

from myblog import settings
from news import models
from users.models import User
from course.models import Course, CourseCategory, Teacher
from doc.models import Docs
from utils.qiniu_secrets import qiniu_secrets_info
from . import constants
from . import forms
# Create your views here.
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from utils.vod_test import get_video_url
from utils import paginator_script
from utils.fastdfs.client import FDFS_Client


logger = logging.getLogger('django')

class IndexView(LoginRequiredMixin, View):
    redirect_field_name = 'next'
    def get(self, request):
        if not request.user.is_staff:
            return render(request, '403.html')
        return render(request, 'admin/index/index.html')


class TagsManageView(View):
    """标签管理类视图，负责标签管理页面的展示以及添加标签"""
    def get(self, request):
        tags = models.Tag.objects.select_related('news').filter(is_delete=False).\
            annotate(num_news=Count('news__tag_id')).values('id', 'name', 'num_news').order_by('-num_news')
        return render(request, 'admin/news/tags_manage.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name:
            tag_name = tag_name.strip()
            data_tuple = models.Tag.objects.get_or_create(name=tag_name)
            tag_instance, status = data_tuple
            if status:
                return to_json_data(errmsg='标签添加成功')
            else:
                return to_json_data(errno=Code.DATAEXIST, errmsg='此标签已存在！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='标签名不能为空！')


class TagsEditView(PermissionRequiredMixin, View):
    """负责标签删除以及编辑功能的类视图"""
    permission_required = ('news.change_tag', 'news.delete_tag')

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限！')

    def delete(self, request, tag_id):
        tag = models.Tag.objects.filter(id=tag_id).first()
        if tag:
            tag.is_delete = True
            tag.save(update_fields=['is_delete'])
            return to_json_data(errmsg='标签删除成功！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='需要删除的标签不存在！')

    def put(self, request, tag_id):
        tag = models.Tag.objects.filter(id=tag_id).first()
        if not tag:
            return to_json_data('正在编辑的标签不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name:
            tag_name = tag_name.strip()
            if not models.Tag.objects.only('name').filter(name=tag_name).exists():
                tag.name = tag_name
                tag.save(update_fields=['name', 'update_time'])
                return to_json_data(errmsg='标签修改成功！')
            else:
                return to_json_data(errno=Code.DATAEXIST, errmsg='此标签已存在！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='标签名不能为空！')


class HotNewsManageView(PermissionRequiredMixin, View):
    """热门文章管理视图"""
    permission_required = ('news.view_hotnews')
    raise_exception = True

    def get(self, request):
        hot_news = models.HotNews.objects.select_related('news__tag').\
            only('priority', 'news__title', 'news_id', 'news__tag__name').\
            filter(is_delete=False).order_by('-news__clicks', '-priority')[:constants.HOT_NEWS_COUNT]
        return render(request, 'admin/news/news_hot.html', locals())


class HotNewsEditView(PermissionRequiredMixin, View):
    """负责热门文章的删除以及编辑功能类视图"""
    permission_required = ('news.delete_hotnews', 'news.change_hotnews')
    raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')

    def delete(self, request, hotnews_id):
        hot_new = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if hot_new:
            hot_new.is_delete = True
            hot_new.save(update_fields=['is_delete', 'update_time'])
            return to_json_data(errmsg='热门文章删除成功！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='要删除的热门文章不存在！')

    def put(self, request, hotnews_id):
        hot_new = models.HotNews.objects.only('id').filter(id=hotnews_id).first()
        if not hot_new:
            return to_json_data(errno=Code.PARAMERR, errmsg='要更新的热门文章不存在')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        priority = dict_data.get('priority')
        try:
            priority = int(priority)
            priority_list = [i for i,_ in models.HotNews.CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='优先级设置错误！')
        except Exception as e:
            logger.info('优先级获取错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='优先级获取错误！')
        hot_new.priority = priority
        hot_new.save(update_fields=['priority', 'update_time'])
        return to_json_data(errmsg='热门文章更新成功！')


class HotNewsAddView(PermissionRequiredMixin, View):
    permission_required = ('news.add_hotnews', 'news.view_hotnews')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(HotNewsAddView, self).handle_no_permission()

    def get(self, request):
        tags = models.Tag.objects.only('name').filter(is_delete=False)
        priority_dict = dict(models.HotNews.CHOICES)
        return render(request, 'admin/news/news_hot_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        priority = dict_data.get('priority')
        try:
            priority = int(priority)
            priority_list = [i for i,_ in models.HotNews.CHOICES]
            if priority not in priority_list:
                return to_json_data(errno=Code.PARAMERR, errmsg='优先级设置错误！')
        except Exception as e:
            logger.info('优先级获取错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='优先级获取错误！')
        try:
            news_id = int(dict_data.get('news_id'))
        except Exception as e:
            logger.info('热门文章参数错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        if not models.News.objects.only('id').filter(id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在')
        hot_news, status = models.HotNews.objects.get_or_create(news_id=news_id)
        hot_news.priority = priority
        hot_news.save(update_fields=['priority', 'update_time'])
        return to_json_data(errmsg='热门文章创建成功！')


class NewsByTagIdView(View):
    """根据标签id获取对应的文章"""
    def get(self, request, tag_id):
        news = models.News.objects.only('id', 'title').filter(is_delete=False, tag_id=tag_id).values()
        news_list = [i for i in news]
        return to_json_data(data={'news': news_list})


class NewsManageView(PermissionRequiredMixin, View):
    permission_required = ('news.view_news')
    raise_exception = True

    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        newes = models.News.objects.select_related('author', 'tag').\
            only('title', 'author__username', 'tag__name', 'update_time').filter(is_delete=False).order_by('-update_time')
        try:
            tag_id = int(request.GET.get('tag_id', 0))
        except Exception as e:
            logger.info('获取标签id出错：{}'.format(e))
            tag_id = 0
        if tag_id:
            newes = newes.filter(tag_id=tag_id)
        try:
            start_time = request.GET.get('start_time', '')
            start_time = datetime.strptime(start_time, '%Y/%m/%d') if start_time else ''
            end_time = request.GET.get('end_time', '')
            end_time = datetime.strptime(end_time, '%Y/%m/%d') if end_time else ''
        except Exception as e:
            logger.info('时间有误：{}'.format(e))
            start_time = end_time = ''
        if start_time and not end_time:
            newes = newes.filter(update_time__gte=start_time)
        if end_time and not start_time:
            newes = newes.filter(update_time__lte=end_time)
        if start_time and end_time:
            newes.filter(update_time__range=(start_time, end_time))
        title = request.GET.get('title', '')
        if title:
            newes = newes.filter(title__icontains=title)
        author_name = request.GET.get('author_name', '')
        if author_name:
            newes = newes.filter(author__username__icontains=author_name)
        # 创建分页，第一个是数据，第二个是每页显示的数据量
        paginator = Paginator(newes, constants.NEWS_PER_PAGE)
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.info('获取页码出错：{}'.format(e))
            page = 1
        try:
            news_info = paginator.page(page)
        except EmptyPage as e:
            logger.info('用户访问页数大于总页数：{}'.format(e))
            news_info = paginator.page(paginator.num_pages)
        paginator_data = paginator_script.get_paginator_data(paginator, news_info)
        other_param = urlencode({
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id
        })
        context = {
            'other_param': other_param,
            'news_info': news_info,
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id,
            'author_name': author_name,
            'tags': tags
        }
        context.update(paginator_data)
        return render(request, 'admin/news/news_manage.html', context=context)


class NewsEditView(PermissionRequiredMixin, View):
    permission_required = ('news.change_news', 'news.delete_news')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限！')
        else:
            return super(NewsEditView, self).handle_no_permission()

    def delete(self, request, news_id):
        news = models.News.objects.only('id').filter(id=news_id).first()
        if news:
            news.is_delete = True
            news.save(update_fields=['is_delete', 'update_time'])
            return to_json_data(errmsg='文章删除成功！')
        else:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的文章不存在！')

    def get(self, request, news_id):
        news = models.News.objects.filter(id=news_id).first()
        if news:
            tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
            return render(request, 'admin/news/news_pub.html', locals())
        else:
            return to_json_data(errno=Code.NODATA, errmsg='要编辑的文章不存在！')

    def put(self, request, news_id):
        news = models.News.objects.only('id').filter(id=news_id).first()
        if not news:
            return to_json_data(errno=Code.PARAMERR, errmsg='要更新的文章不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.NODATA, errmsg=error_map[Code.NODATA])
        dict_data = json.loads(json_data.decode('utf8'))
        form = forms.NewsPubForm(data=dict_data)
        if form.is_valid():
            news.title = form.cleaned_data.get('title')
            news.digest = form.cleaned_data.get('digest')
            news.content = form.cleaned_data.get('content')
            news.tag = form.cleaned_data.get('tag')
            news.image_url = form.cleaned_data.get('image_url')
            news.save()
            return to_json_data(errmsg='文章更新成功！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class NewsPubView(View):
    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        return render(request, 'admin/news/news_pub.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.NODATA, errmsg=error_map[Code.NODATA])
        dict_data = json.loads(json_data.decode('utf8'))
        form = forms.NewsPubForm(data=dict_data)
        if form.is_valid():
            # 延缓保存
            news_instance = form.save(commit=False)
            news_instance.author = request.user
            news_instance.save()
            return to_json_data(errmsg='文章发布成功！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class NewsUploadImage(View):
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
            return to_json_data(data={'image_url': image_url}, errmsg='图片上传成功！')
        else:
            logger.info('图片上传到FastDFS服务器失败')
            return to_json_data(errno=Code.UNKOWNERR, errmsg='上传图片到服务器失败！')


class UploadToken(View):
    """七牛云上传图片需要调用token"""
    def get(self, request):
        access_key = qiniu_secrets_info.QI_NIU_ACCESS_KEY
        secret_key = qiniu_secrets_info.QI_NIU_SECRET_KEY
        bucket_name = qiniu_secrets_info.QI_NIU_BUCKET_NAME
        # 构建鉴权对象
        q = qiniu.Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        return JsonResponse({'uptoken': token})


@method_decorator(csrf_exempt, name='dispatch')
class MarkDownUploadImage(View):
    """markdown上传图片"""
    @csrf_exempt
    def post(self, request):
        image_file = request.FILES.get('editormd-image-file')
        if not image_file:
            logger.info('从前端获取图片失败')
            return JsonResponse({'success': 0, 'message': '从前端获取图片失败'})
        if image_file.content_type not in ('image/jpeg', 'image/png', 'image/gif', 'image/jpg'):
            return JsonResponse({'success': 0, 'message': '不能上传非图片文件'})
        try:
            image_ext_name = image_file.name.split('.')[-1]
        except Exception as e:
            logger.info('图片拓展名异常：{}'.format(e))
            image_ext_name = 'jpg'
        try:
            upload_res = FDFS_Client.upload_by_buffer(image_file.read(), file_ext_name=image_ext_name)
        except Exception as e:
            logger.error('图片上传出现异常：{}'.format(e))
            return JsonResponse({'success': 0, 'message': '图片上传异常'})
        else:
            if upload_res.get('Status') != 'Upload successed.':
                logger.info('图片上传到FastDFS服务器失败')
                return JsonResponse({'success': 0, 'message': '图片上传到服务器失败'})
            else:
                image_name = upload_res.get('Remote file_id')
                image_url = settings.FASTDFS_SERVER_DOMAIN + image_name
                return JsonResponse({'success': 1, 'message': '图片上传成功', 'url': image_url})


class BannerManageView(PermissionRequiredMixin, View):
    permission_required = ('news.view_banner')
    raise_exception = True

    def get(self, request):
        banners = models.Banner.objects.only('id', 'priority', 'image_url').filter(is_delete=False)
        priority_dict = dict(models.Banner.CHOICES)
        return render(request, 'admin/news/news_banner.html', locals())


class BannerEditView(PermissionRequiredMixin, View):
    permission_required = ('news.delete_banner', 'news.change_banner')
    raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限！')

    def delete(self, request, banner_id):
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if banner:
            banner.is_delete = True
            banner.save(update_fields=['is_delete', 'update_time'])
            return to_json_data(errmsg='轮播图删除成功！')
        else:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的轮播图不存在！')

    def put(self, request, banner_id):
        banner = models.Banner.objects.only('id').filter(id=banner_id).first()
        if not banner:
            return to_json_data(errno=Code.NODATA, errmsg='要更新的轮播图不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.NODATA, errmsg=error_map[Code.NODATA])
        dict_data = json.loads(json_data.decode('utf8'))
        try:
            priority = int(dict_data.get('priority'))
            if priority:
                priority_list = [i for i, _ in models.Banner.CHOICES]
                if priority not in priority_list:
                    return to_json_data(errno=Code.PARAMERR, errmsg='优先级设置错误！')
            else:
                return to_json_data(Code.NODATA, errmsg='优先级设置错误！')
        except Exception as e:
            logger.info('获取优先级出错：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        image_url = dict_data.get('image_url')
        if not image_url:
            return to_json_data(errno=Code.NODATA, errmsg='未上传图片！')
        banner.priority = priority
        banner.image_url = image_url
        banner.save()
        return to_json_data(errmsg='轮播图更新成功！')


class BannerAddView(PermissionRequiredMixin, View):
    permission_required = ('news.add_banner')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(BannerAddView, self).handle_no_permission()

    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        priority_dict = dict(models.Banner.CHOICES)
        return render(request, 'admin/news/news_banner_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.NODATA, errmsg=error_map[Code.NODATA])
        dict_data = json.loads(json_data.decode('utf8'))
        try:
            priority = int(dict_data.get('priority'))
            if priority:
                priority_list = [i for i, _ in models.Banner.CHOICES]
                if priority not in priority_list:
                    return to_json_data(errno=Code.PARAMERR, errmsg='优先级设置错误！')
            else:
                return to_json_data(Code.NODATA, errmsg='优先级设置错误！')
        except Exception as e:
            logger.info('获取优先级出错：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        try:
            news_id = int(dict_data.get('news_id'))
            if news_id:
                if not models.News.objects.only('id').filter(id=news_id, is_delete=False).exists():
                    return to_json_data(errno=Code.DATAERR, errmsg='该文章不存在！')
                if models.Banner.objects.filter(news_id=news_id).exists():
                    return to_json_data(errno=Code.DATAEXIST, errmsg='关联该文章的轮播图已存在！')
            else:
                return to_json_data(errno=Code.PARAMERR, errmsg='文章设置错误！')
        except Exception as e:
            logger.info('获取文章id出错：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='文章设置错误！')
        image_url = dict_data.get('image_url')
        if not image_url:
            return to_json_data(errno=Code.NODATA, errmsg='未上传图片！')
        banner = models.Banner()
        banner.news_id = news_id
        banner.image_url = image_url
        banner.priority = priority
        banner.save()
        return to_json_data(errmsg='轮播图添加成功！')


class DocManageView(PermissionRequiredMixin, View):
    permission_required = ('doc.view_docs')
    raise_exception = True

    def get(self, request):
        docs = Docs.objects.only('id', 'title', 'update_time').filter(is_delete=False)
        return render(request, 'admin/doc/docs_manage.html', locals())


class DocEditView(PermissionRequiredMixin, View):
    permission_required = ('doc.view_docs', 'doc.delete_docs', 'doc.change_docs')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(DocEditView, self).handle_no_permission()

    def get(self, request, doc_id):
        doc = Docs.objects.filter(id=doc_id, is_delete=False).first()
        if not doc:
            return Http404('要编辑的文档不存在！')
        return render(request, 'admin/doc/docs_pub.html', locals())

    def delete(self, request, doc_id):
        doc = Docs.objects.filter(is_delete=False, id=doc_id).first()
        if not doc:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的文档不存在！')
        doc.is_delete = True
        doc.save(update_fields=['is_delete', 'update_time'])
        return to_json_data(errmsg='文档删除成功！')

    def put(self, request, doc_id):
        doc = Docs.objects.filter(id=doc_id, is_delete=False).first()
        if not doc:
            return to_json_data(errno=Code.NODATA, errmsg='要更新的文档不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        form = forms.DocsPubForm(data=dict_data)
        if form.is_valid():
            for key, value in form.cleaned_data.items():
                setattr(doc, key, value)
            doc.save()
            return to_json_data(errmsg='文档更新成功！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class DocUploadFiles(PermissionRequiredMixin, View):
    permission_required = ('doc.add_docs')
    raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')

    def post(self, request):
        text_file = request.FILES.get('text_file')
        if not text_file:
            return to_json_data(errno=Code.PARAMERR, errmsg='未选择文件上传')
        if text_file.content_type not in ('application/octet-stream', 'application/pdf', 'application/msword',
                                          'application/zip', 'text/plain', 'application/x-rar'):
            return to_json_data(errno=Code.PARAMERR, errmsg='不能上传非文档类型的文件！')
        try:
            text_ext_name = text_file.name.split('.')[-1]
        except Exception as e:
            logger.info('获取文档扩展名异常：{}'.format(e))
            text_ext_name = 'jpg'
        try:
            result = FDFS_Client.upload_by_buffer(text_file.read(), text_ext_name)
        except Exception as e:
            logger.info('文档上传出现异常：{}'.format(e))
            return to_json_data(errno=Code.UNKOWNERR, errmsg='文档上传出现异常！')
        if result['Status'] == 'Upload successed.':
            text_url = settings.FASTDFS_SERVER_DOMAIN + result['Remote file_id']
            return to_json_data(data={'text_file': text_url}, errmsg='文档上传成功！')
        else:
            logger.info('文档上传到FastDFS服务器失败')
            return to_json_data(errno=Code.UNKOWNERR, errmsg='上传文档到服务器失败！')


class DocPubView(PermissionRequiredMixin, View):
    permission_required = ('doc.view_docs', 'doc.add_docs')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(DocPubView, self).handle_no_permission()

    def get(self, request):
        return render(request, 'admin/doc/docs_pub.html')

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        form = forms.DocsPubForm(data=dict_data)
        if form.is_valid():
            doc_instance = form.save(commit=False)
            doc_instance.author = request.user
            doc_instance.save()
            return to_json_data(errmsg='文档创建成功！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class CourseManageView(PermissionRequiredMixin, View):
    permission_required = ('course.view_course')
    raise_exception = True

    def get(self, request):
        courses = Course.objects.select_related('teacher', 'category').\
            only('id', 'name', 'teacher__name', 'category__name').filter(is_delete=False)
        return render(request, 'admin/course/courses_manage.html', locals())


class CourseEditView(PermissionRequiredMixin, View):
    permission_required = ('course.view_course', 'course.delete_course', 'course.change_course')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(CourseEditView, self).handle_no_permission()

    def delete(self, request, course_id):
        course = Course.objects.only('id').filter(id=course_id, is_delete=False).first()
        if not course:
            return to_json_data(errno=Code.NODATA, errmsg='需要删除的视频不存在！')
        course.is_delete = True
        course.save(update_fields=['is_delete', 'update_time'])
        return to_json_data(errmsg='视频删除成功！')

    def get(self, request, course_id):
        course = Course.objects.only('id').filter(id=course_id, is_delete=False).first()
        if not course:
            return to_json_data(errno=Code.NODATA, errmsg='需要编辑的视频不存在！')
        categories = CourseCategory.objects.filter(is_delete=False)
        teachers = Teacher.objects.filter(is_delete=False)
        return render(request, 'admin/course/courses_pub.html', locals())


class CoursePubView(PermissionRequiredMixin, View):
    permission_required = ('course.view_course', 'course.add_course')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(CoursePubView, self).handle_no_permission()

    def get(self, request):
        categories = CourseCategory.objects.filter(is_delete=False)
        teachers = Teacher.objects.filter(is_delete=False)
        return render(request, 'admin/course/courses_pub.html', locals())

    def post(self, request):
        pass


class UploadVideo(PermissionRequiredMixin, View):
    permission_required = 'course.add_course'
    raise_exception = True

    def handle_no_permission(self):
        return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')

    def post(self, request):
        video_file = request.FILES.get('video_file', '')
        if video_file.content_type != 'video/mp4':
           return to_json_data(errno=Code.PARAMERR, errmsg='视频类型错误！')
        video_name = video_file.name
        res = get_video_url(video_name)
        if res:
            return to_json_data(data={'video_url': res})
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='视频上传失败')


class GroupManageView(PermissionRequiredMixin, View):
    permission_required = ('auth.view_group')
    raise_exception = True

    def get(self, request):
        groups = Group.objects.values('id', 'name').annotate(num_users=Count('user')).order_by('-num_users')
        return render(request, 'admin/user/groups_manage.html', locals())


class GroupEditView(PermissionRequiredMixin, View):
    permission_required = ('auth.delete_group', 'auth.change_group')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(GroupEditView, self).handle_no_permission()

    def get(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return to_json_data(errno=Code.PARAMERR, errmsg='要编辑的组不存在！')
        permissions = Permission.objects.all()
        return render(request, 'admin/user/groups_add.html', locals())

    def delete(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的组不存在！')
        group.permissions.clear()
        group.delete()
        return to_json_data(errmsg='组删除成功！')

    def put(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return to_json_data(errno=Code.NODATA, errmsg='要更新的组不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名不能为空！')
        if group_name != group.name and Group.objects.filter(name=group_name).exists():
            return to_json_data(errno=Code.DATAEXIST, errmsg='此组名已存在！')
        permissions = dict_data.get('group_permissions', '')
        if not permissions:
            return to_json_data(errno=Code.NODATA, errmsg='未给用户组选择权限！')
        try:
            permissions_set = set(int(i) for i in permissions)
        except Exception as e:
            logger.info('权限参数错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数错误！')
        real_set = set(j.id for j in Permission.objects.only('id'))
        if not permissions_set.issubset(real_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数！')
        exists_perm_set = set(perm.id for perm in group.permissions.all())
        if group.name == group_name and permissions_set == exists_perm_set:
            return to_json_data(errno=Code.DATAEXIST, errmsg='用户组信息未修改！')
        # 先清空之前的权限，再添加选择的权限
        group.permissions.clear()
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            group.permissions.add(p)
        group.name = group_name
        group.save()
        return to_json_data(errmsg='用户组更新成功！')


class GroupAddView(PermissionRequiredMixin, View):
    permission_required = ('auth.add_group')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(GroupAddView, self).handle_no_permission()

    def get(self, request):
        permissions = Permission.objects.all()
        return render(request, 'admin/user/groups_add.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        group_name = dict_data.get('name', '').strip()
        if not group_name:
            return to_json_data(errno=Code.PARAMERR, errmsg='组名不能为空！')
        if Group.objects.filter(name=group_name).exists():
            return to_json_data(errno=Code.DATAEXIST, errmsg='此组名已存在！')
        permissions = dict_data.get('group_permissions', '')
        if not permissions:
            return to_json_data(errno=Code.NODATA, errmsg='未给用户组选择权限！')
        try:
            permissions_set = set(int(i) for i in permissions)
        except Exception as e:
            logger.info('权限参数错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='权限参数错误！')
        real_set = set(j.id for j in Permission.objects.only('id'))
        if not permissions_set.issubset(real_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的权限参数！')
        group = Group.objects.create(name=group_name)
        for perm_id in permissions_set:
            p = Permission.objects.get(id=perm_id)
            group.permissions.add(p)
        group.save()
        return to_json_data(errmsg='用户组添加成功！')


class UserManageView(PermissionRequiredMixin, View):
    permission_required = ('users.view_user')
    raise_exception = True

    def get(self, request):
        users = User.objects.only('is_active', 'is_staff', 'is_superuser').all()
        return render(request, 'admin/user/users_manage.html', locals())


class UserEditView(PermissionRequiredMixin, View):
    permission_required = ('user.change_user', 'user.delete_user')
    raise_exception = True

    def handle_no_permission(self):
        if self.request.method != 'GET':
            return to_json_data(errno=Code.ROLEERR, errmsg='没有操作权限')
        else:
            return super(UserEditView, self).handle_no_permission()

    def get(self, request, user_id):
        user_instance = User.objects.filter(id=user_id).first()
        if not user_instance:
            return to_json_data(errno=Code.NODATA, errmsg='要编辑的用户不存在！')
        groups = Group.objects.only('name').all()
        return render(request, 'admin/user/users_edit.html', locals())

    def delete(self, request, user_id):
        user_instance = User.objects.filter(id=user_id).first()
        if not user_instance:
            return to_json_data(errno=Code.PARAMERR, errmsg='要删除的用户不存在！')
        user_instance.groups.clear()
        user_instance.user_permissions.clear()
        user_instance.is_active = False
        user_instance.save()
        return to_json_data(errmsg='用户删除成功！')

    def put(self, request, user_id):
        user_instance = User.objects.filter(id=user_id).first()
        if not user_instance:
            return to_json_data(errno=Code.NODATA, errmsg='要更新的用户不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        try:
            is_staff = int(dict_data.get('is_staff'))
            is_active = int(dict_data.get('is_active'))
            is_superuser = int(dict_data.get('is_superuser'))
            data_list = [is_staff, is_active, is_superuser]
            # 判断数据是否为0或1
            if False in [data in (0, 1) for data in data_list]:
                return to_json_data(errno=Code.DATAERR, errmsg='参数错误！！！')
        except Exception as e:
            logger.info('从前端获取参数错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='从前端获取参数错误！')
        groups = dict_data.get('groups', '')
        if not groups:
            return to_json_data(errno=Code.PARAMERR, errmsg='未选择组！')
        try:
            group_set = set(int(i) for i in groups)
        except Exception as e:
            logger.info('组参数错误：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg='组参数错误！')
        real_group_set = set(i.id for i in Group.objects.only('id').all())
        if not group_set.issubset(real_group_set):
            return to_json_data(errno=Code.PARAMERR, errmsg='有不存在的组参数！')
        gs = Group.objects.filter(id__in=group_set)
        user_instance.groups.clear()    # 先清空之前的组
        # 多对多操作，set可一次添加多个
        user_instance.groups.set(gs)
        user_instance.is_active = bool(is_active)
        user_instance.is_superuser = bool(is_superuser)
        user_instance.is_staff = bool(is_staff)
        user_instance.save()
        return to_json_data(errmsg='用户信息更新成功！')