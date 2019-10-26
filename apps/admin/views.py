import json

from django.db.models import Count
from django.shortcuts import render
from django.views import View
from news import models

# Create your views here.
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map


def index(request):
    return render(request, 'admin/index/index.html')

class TagsManageView(View):
    """标签管理类视图，负责标签管理页面的展示以及添加标签"""
    def get(self, request):
        tags = models.Tag.objects.select_related('news').filter(is_delete=False).\
            annotate(num_news=Count('news__tag_id')).values('id', 'name', 'num_news').order_by('-num_news')
        return render(request, 'admin/news/tags_manage.html', locals())

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name:
            tag_name = tag_name.strip()
            data_tuple = models.Tag.objects.get_or_create(name=tag_name)
            tag_instance, status = data_tuple
            if status:
                return to_json_data(errmsg='标签添加成功')
            else:
                return to_json_data(errno=Code.DATAEXIST, errmsg='此标签已存在！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='标签名不能为空！')

class TagsEditView(View):
    """负责标签删除以及编辑功能的类视图"""
    def delete(self, request, tag_id):
        tag = models.Tag.objects.filter(id=tag_id).first()
        if tag:
            tag.is_delete = True
            tag.save(update_fields=['is_delete'])
            return to_json_data(errmsg='标签删除成功！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='需要删除的标签不存在！')

    def put(self, request, tag_id):
        tag = models.Tag.objects.filter(id=tag_id).first()
        if not tag:
            return to_json_data('正在编辑的标签不存在！')
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data.decode('utf8'))
        tag_name = dict_data.get('name')
        if tag_name:
            tag_name = tag_name.strip()
            if not models.Tag.objects.only('name').filter(name=tag_name).exists():
                tag.name = tag_name
                tag.save(update_fields=['name', 'update_time'])
                return to_json_data(errmsg='标签修改成功！')
            else:
                return to_json_data(errno=Code.DATAEXIST, errmsg='此标签已存在！')
        else:
            return to_json_data(errno=Code.PARAMERR, errmsg='标签名不能为空！')
