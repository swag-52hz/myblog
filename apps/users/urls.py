from django.urls import path, re_path
from . import views


app_name = 'users'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('blog/', views.UserBlogView.as_view(), name='blog'),
    path('upload/', views.UploadImage.as_view(), name='upload'),
    path('news/pub/', views.NewsPubView.as_view(), name='news_pub'),
    path('news/<int:news_id>/', views.NewsEditView.as_view(), name='news_edit'),
    path('follow/', views.FollowView.as_view(), name='follow'),
    path('fans/', views.FansView.as_view(), name='fans'),
    path('personal/<int:author_id>/', views.HomePageView.as_view(), name='hp'),
    path('forget/', views.ForgetView.as_view(), name='forget'),
    path('reset/', views.ResetPassword.as_view(), name='reset'),
    re_path('(?P<username>\w{4,20})/', views.NewsByUserView.as_view(), name='news'),
]