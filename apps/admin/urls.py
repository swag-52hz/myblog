from django.urls import path
from . import views


app_name = 'admin'
urlpatterns = [
    path('', views.index, name='index'),
    path('tags/', views.TagsManageView.as_view(), name='tags_manage'),
    path('tags/<int:tag_id>/', views.TagsEditView.as_view(), name='tags_edit'),
]