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
    path('news_edit/<int:news_id>/', views.NewsEditView.as_view(), name='news_edit'),
]