from django.urls import path
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
]