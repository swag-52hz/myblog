import logging
import json
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View

from myblog import settings
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
            news_info_list.append(
                {
                    'id': item.id,
                    'title': item.title,
                    'digest': item.digest,
                    'author': item.author.username,
                    'tag_name': item.tag.name,
                    'update_time': item.update_time.strftime('%Y年%m月%d日 %H:%M'),
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
            news.save()
            comments = models.Comments.objects.select_related('author', 'parent').\
                only('content', 'author__username', 'update_time', 'parent__content',
                     'parent__author__username', 'parent__update_time').filter(is_delete=False, news_id=news_id)
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
