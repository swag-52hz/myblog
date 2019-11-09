from django.urls import path
from . import views


app_name = 'admin'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
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
    path('markdown/images/', views.MarkDownUploadImage.as_view(), name='markdown_image_upload'),
    path('banners/', views.BannerManageView.as_view(), name='banners'),
    path('banners/<int:banner_id>/', views.BannerEditView.as_view(), name='banners_edit'),
    path('banners/add/', views.BannerAddView.as_view(), name='banner_add'),
    path('docs/', views.DocManageView.as_view(), name='doc'),
    path('docs/<int:doc_id>/', views.DocEditView.as_view(), name='docs_edit'),
    path('docs/pub/', views.DocPubView.as_view(), name='doc_pub'),
    path('docs/files/', views.DocUploadFiles.as_view(), name='upload_files'),
    path('courses/', views.CourseManageView.as_view(), name='courses'),
    path('courses/<int:course_id>/', views.CourseEditView.as_view(), name='course_edit'),
    path('courses/pub/', views.CoursePubView.as_view(), name='courses_pub'),
    path('courses/video/', views.UploadVideo.as_view(), name='upload_video'),
    path('groups/', views.GroupManageView.as_view(), name='groups'),
    path('groups/<int:group_id>/', views.GroupEditView.as_view(), name='group_edit'),
    path('groups/add/', views.GroupAddView.as_view(), name='group_add'),
    path('users/', views.UserManageView.as_view(), name='users'),
    path('users/<int:user_id>/', views.UserEditView.as_view(), name='users_edit'),
]