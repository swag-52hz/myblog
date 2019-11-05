import requests
import logging
from django.shortcuts import render
from django.utils.encoding import escape_uri_path

from .models import Docs
from django.http import HttpResponse, FileResponse, Http404
from myblog.settings import SITE_DOMAIN_PORT
from django.views import View


logger = logging.getLogger('django')


def doc_index(request):
    docs = Docs.objects.only('title', 'image_url', 'desc').filter(is_delete=False)
    return render(request, 'doc/docDownload.html', locals())

class DocDownloadView(View):
    def get(self, request, doc_id):
        doc = Docs.objects.only('file_url').filter(is_delete=False, id=doc_id).first()
        if doc:
            file_url = doc.file_url
            if  '127.0.0.1:8888' in file_url:
                doc_url = file_url
            else:
                doc_url = SITE_DOMAIN_PORT + file_url
            try:
                # 设置stream=True在下载大文件的时候可以提升下载速度
                file = requests.get(doc_url, stream=True)
                res = FileResponse(file)
            except Exception as e:
                logger.info('文档下载出错：{}'.format(e))
                return Http404('文档下载异常！！！')
            # 获取文件类型(后缀名)
            ex_name = doc_url.split('.')[-1]
            if not ex_name:
                raise Http404('文件url异常！')
            else:
                # 将文件类型转换为小写
                ex_name = ex_name.lower()
            if ex_name == "pdf":
                res["Content-type"] = "application/pdf"
            elif ex_name == "zip":
                res["Content-type"] = "application/zip"
            elif ex_name == "doc":
                res["Content-type"] = "application/msword"
            elif ex_name == "xls":
                res["Content-type"] = "application/vnd.ms-excel"
            elif ex_name == "docx":
                res["Content-type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ex_name == "ppt":
                res["Content-type"] = "application/vnd.ms-powerpoint"
            elif ex_name == "pptx":
                res["Content-type"] = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            else:
                raise Http404("文档格式不正确！")
            # 获取文件名,将其进行转码
            doc_filename = escape_uri_path(doc.title + '.' + ex_name)
            # http1.1 中的规范
            # 设置为inline，会直接打开
            # attachment 浏览器会开始下载
            res["Content-Disposition"] = "attachment; filename*=UTF-8''{}".format(doc_filename)
            # 返回文件对象
            return res
        else:
            return Http404('该文档不存在！！！')

