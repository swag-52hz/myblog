from django.urls import path
from . import views


app_name = 'course'
urlpatterns = [
    path('course/', views.CourseView.as_view(), name='course'),
]