from django.urls import path
from . import views


app_name = 'admin'
urlpatterns = [
    path('', views.index, name='index'),
    path('tags/', views.TagsManageView.as_view(), name='tags_manage'),
    path('tags/<int:tag_id>/', views.TagsEditView.as_view(), name='tags_edit'),
    path('hotnews/', views.HotNewsManageView.as_view(), name='hot_news'),
    path('hotnews/<int:hotnews_id>/', views.HotNewsEditView.as_view(), name='hotnews_edit'),
    path('hotnews/add/', views.HotNewsAddView.as_view(), name='hotnews_add'),
    path('tags/<int:tag_id>/news/', views.NewsByTagIdView.as_view(), name='news_by_tag_id'),
    path('news/', views.NewsManageView.as_view(), name='news_manage'),
    path('news/<int:news_id>/', views.NewsEditView.as_view(), name='news_edit'),
    path('news/pub/', views.NewsPubView.as_view(), name='news_pub'),
    path('news/images/', views.NewsUploadImage.as_view(), name='upload_images'),
    path('token/', views.UploadToken.as_view(), name='token'),
    path('banners/', views.BannerManageView.as_view(), name='banners'),
    path('banners/<int:banner_id>/', views.BannerEditView.as_view(), name='banners_edit'),
    path('banners/add/', views.BannerAddView.as_view(), name='banner_add'),
]