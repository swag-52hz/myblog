import logging
import json

import pytz
from django.db.models import Count
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.db.models import Count, Sum

from myblog import settings
from news.models import Tag
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from haystack.views import SearchView as _SearchView
from .contants import NEWS_PER_PAGE
from . import models


logger = logging.getLogger('django')


class IndexView(View):
    def get(self, request):
        tags = models.Tag.objects.only('id', 'name').filter(is_delete=False)
        hot_news = models.HotNews.objects.select_related('news').only('news__title', 'news__image_url', 'news_id').\
                      filter(is_delete=False).order_by('-priority', '-news__clicks')[0:3]
        return render(request, 'news/index.html', locals())


class NewsListView(View):
    def get(self, request):
        try:
            tag_id = int(request.GET.get('tag_id', 0))
        except Exception as e:
            logger.info('获取标签出错：{}'.format(e))
            tag_id = 0
        try:
            page = int(request.GET.get('page', 1))
        except Exception as e:
            logger.info('获取页码出错：{}'.format(e))
            page = 1
        news_queryset = models.News.objects.select_related('tag', 'author')\
            .only('title', 'digest', 'author__username', 'update_time', 'tag__name', 'image_url')
        news = news_queryset.filter(is_delete=False, tag_id=tag_id) or news_queryset.filter(is_delete=False)
        paginator = Paginator(news, NEWS_PER_PAGE)
        try:
            news_info = paginator.page(page)
        except EmptyPage as e:
            logger.info('页数大于总页数：{}'.format(e))
            news_info = paginator.page(paginator.num_pages)
        news_info_list = []
        for item in news_info:
            # 将时区转换为中国上海
            shanghai_tz = pytz.timezone('Asia/Shanghai')
            # 转换为本地时间
            local_time = shanghai_tz.normalize(item.update_time)
            news_info_list.append(
                {
                    'id': item.id,
                    'title': item.title,
                    'digest': item.digest,
                    'author': item.author.username,
                    'tag_name': item.tag.name,
                    'update_time': local_time.strftime('%Y年%m月%d日 %H:%M'),
                    'image_url': item.image_url
                }
            )
        data = {
            'news': news_info_list,
            'total_pages': paginator.num_pages
        }
        return to_json_data(data=data)


class BannerListView(View):
    def get(self, request):
        banners = models.Banner.objects.select_related('news').only('image_url', 'news__id', 'news__title').\
                      order_by('priority').filter(is_delete=False)[0:6]
        banner_info_list = []
        for item in banners:
            banner_info_list.append(
                {
                    'image_url': item.image_url,
                    'news_id': item.news.id,
                    'news_title': item.news.title,
                }
            )
        data = {
            'banners': banner_info_list
        }
        return to_json_data(data=data)


class NewsDetailView(View):
    def get(self, request, news_id):
        news = models.News.objects.select_related('author', 'tag').\
            only('title', 'author__username', 'tag__name', 'content', 'update_time', 'clicks').\
            filter(is_delete=False, id=news_id).first()
        if news:
            news.clicks = int(news.clicks) + 1
            news.save(update_fields=['clicks'])
            # 计算作者的文章数量
            news_count = models.News.objects.filter(author_id=news.author.id).count()
            all_news = models.News.objects.filter(author_id=news.author.id, is_delete=False)
            # 获取总评论数，总浏览量
            total_clicks = models.News.objects.filter(author_id=news.author.id).aggregate(clicks=Sum('clicks')).get('clicks')
            if total_clicks > 400000:
                total_clicks = '40万+'
            total_comment = models.News.objects.filter(author_id=news.author.id).aggregate(comments=Count('comments')).get('comments')
            # 获取作者最新的五篇文章，若不足五篇则返回所有
            latest_news = models.News.objects.only('id', 'title').\
                filter(author_id=news.author.id, is_delete=False).order_by('-update_time')
            latest_news = latest_news[:5] if latest_news.count() > 5 else latest_news
            tags = Tag.objects.filter(is_delete=False, news__author=news.author).values('id', 'name').\
                annotate(news_count = Count('news')).order_by('-news_count')
            data_dict = tags[:5] if tags.count() > 5 else tags
            hot_news = models.News.objects.only('id', 'title', 'clicks').\
                filter(author=news.author, is_delete=False).order_by('-clicks')
            hot_news = hot_news[:5] if hot_news.count() > 5 else hot_news
            comments = models.Comments.objects.select_related('author', 'parent').\
                only('content', 'author__username', 'author__avatar_url', 'update_time', 'parent__content',
                     'parent__author__username', 'parent__author__avatar_url', 'parent__update_time').filter(is_delete=False, news_id=news_id)
            comments_list = []
            comment_count = comments.count()
            for comm in comments:
                comments_list.append(comm.to_dict_data())
            return render(request, 'news/news_detail.html', locals())
        else:
            return Http404('id为{}的文章不存在！！！'.format(news_id))


class AddCommentsView(View):
    def post(self, request, news_id):
        if not request.user.is_authenticated:
            return to_json_data(errno=Code.SESSIONERR, errmsg=error_map[Code.SESSIONERR])
        if not models.News.objects.only('id').filter(is_delete=False, id=news_id).exists():
            return to_json_data(errno=Code.PARAMERR, errmsg='文章不存在！！！')
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        parent_id = dict_data.get('parent_id')
        content = dict_data.get('content')
        try:
            if parent_id:
                parent_id = int(parent_id)
                query_set = models.Comments.objects.filter(id=parent_id, news_id=news_id)
                if not query_set.exists():
                    return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
                if query_set.first().author.username == request.user.username:
                    return to_json_data(errno=Code.PARAMERR, errmsg='不可评论自己的发言！！！')
        except Exception as e:
            logger.info('处理数据出错：{}'.format(e))
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])

        new_comment = models.Comments()
        new_comment.news_id = news_id
        new_comment.author = request.user
        new_comment.content = content
        new_comment.parent_id = parent_id if parent_id else None
        new_comment.save()

        return to_json_data(data=new_comment.to_dict_data())


class SearchView(_SearchView):
    # 模版文件
    template = 'news/search.html'

    # 重写响应方式，如果请求参数q为空，返回模型News的热门新闻数据，否则根据参数q搜索相关数据
    def create_response(self):
        kw = self.request.GET.get('q', '')
        if not kw:
            show_all = True
            hot_news = models.HotNews.objects.select_related('news'). \
                only('news__title', 'news__image_url', 'news__id'). \
                filter(is_delete=False).order_by('priority', '-news__clicks')

            paginator = Paginator(hot_news, settings.HAYSTACK_SEARCH_RESULTS_PER_PAGE)
            try:
                page = paginator.page(int(self.request.GET.get('page', 1)))
            except PageNotAnInteger:
                # 如果参数page的数据类型不是整型，则返回第一页数据
                page = paginator.page(1)
            except EmptyPage:
                # 用户访问的页数大于实际页数，则返回最后一页的数据
                page = paginator.page(paginator.num_pages)
            return render(self.request, self.template, locals())
        else:
            show_all = False
            qs = super(SearchView, self).create_response()
            return qs


class CategoryView(View):
    def get(self, request, tag_id):
        tag = Tag.objects.filter(id=tag_id, is_delete=False).first()
        if not tag:
            return render(request, 'base/404notfound.html')
        newes = models.News.objects.only('title', 'digest', 'update_time', 'clicks')\
            .filter(tag_id=tag.id, is_delete=False).annotate(comment_count=Count('comments'))[:10]
        author = tag.news_set.first().author
        # 该标签下的文章数量
        tag_data = Tag.objects.filter(id=tag_id).annotate(Count('news'), Sum('news__clicks'))[0]
        # 计算作者的文章数量
        news_count = models.News.objects.filter(author_id=author.id, is_delete=False).count()
        # 获取总评论数，总浏览量
        total_clicks = models.News.objects.filter(author_id=author.id, is_delete=False).aggregate(clicks=Sum('clicks')).get(
            'clicks')
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
        return render(request, 'users/category.html', locals())
