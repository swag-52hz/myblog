import json
import logging
from datetime import datetime
from urllib.parse import urlencode

from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count
from django.shortcuts import render
from django.views import View
from news import models
from . import constants
# Create your views here.
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from utils import paginator_script


logger = logging.getLogger('django')

def index(request):
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


class TagsEditView(View):
    """负责标签删除以及编辑功能的类视图"""
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


class HotNewsManageView(View):
    """热门文章管理视图"""
    def get(self, request):
        hot_news = models.HotNews.objects.select_related('news__tag').\
            only('priority', 'news__title', 'news_id', 'news__tag__name').\
            filter(is_delete=False).order_by('-news__clicks', '-priority')[:constants.HOT_NEWS_COUNT]
        return render(request, 'admin/news/news_hot.html', locals())


class HotNewsEditView(View):
    """负责热门文章的删除以及编辑功能类视图"""
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


class HotNewsAddView(View):
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


class NewsManageView(View):
    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        newes = models.News.objects.select_related('author', 'tag').\
            only('title', 'author__username', 'tag__name', 'update_time').filter(is_delete=False)
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


class NewsEditView(View):
    def delete(self, request, news_id):
        news = models.News.objects.only('id').filter(id=news_id).first()
        if news:
            news.is_delete = True
            news.save(update_fields=['is_delete', 'update_time'])
            return to_json_data(errmsg='文章删除成功！')
        else:
            return to_json_data(errno=Code.NODATA, errmsg='要删除的文章不存在！')

    def put(self, request, news_id):
        pass

