from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views


app_name = 'department'
urlpatterns = [
    path('depts/', views.DeptView.as_view(), name='depts'),
    path('depts/<int:pk>/', views.DeptInfoView.as_view(), name='dept_info'),
]

route = DefaultRouter()
route.register(r'dps', views.DeptsViewset)
urlpatterns += route.urls