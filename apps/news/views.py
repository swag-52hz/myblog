import logging
from django.shortcuts import render
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage
from django.views import View
from utils.json_fun import to_json_data
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
            only('title', 'author__username', 'tag__name', 'content', 'update_time').\
            filter(is_delete=False, id=news_id).first()
        if news:
            return render(request, 'news/news_detail.html', locals())
        else:
            return Http404('id为{}的文章不存在！！！'.format(news_id))


class SearchView(View):
    def get(self, request):
        return render(request, 'news/search.html')