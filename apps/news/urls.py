from django.urls import path
from . import views


app_name = 'news'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/banners/', views.BannerListView.as_view(), name='news_banner'),
    path('news/<int:news_id>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
]