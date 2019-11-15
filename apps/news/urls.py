from django.urls import path
from . import views


app_name = 'news'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/banners/', views.BannerListView.as_view(), name='news_banner'),
    path('news/<int:news_id>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('news/<int:news_id>/comments/', views.AddCommentsView.as_view(), name='news_comments'),
    path('search/', views.SearchView(), name='search'),
    path('news/category/<int:tag_id>/', views.CategoryView.as_view(), name='category'),
    path('focus/', views.FocusView.as_view(), name='focus'),
    path('takeoff/', views.TakeOffView.as_view(), name='takeoff'),
]