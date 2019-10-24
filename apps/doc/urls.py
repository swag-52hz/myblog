from django.urls import path
from . import views


app_name = 'doc'
urlpatterns = [
    path('doc_download/', views.doc_index, name='doc_index'),
    path('doc_download/<int:doc_id>/', views.DocDownloadView.as_view(), name='doc_download'),
]