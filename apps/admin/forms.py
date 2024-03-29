from django import forms
from doc.models import Docs
from news.models import Tag, News


class NewsPubForm(forms.ModelForm):
    image_url = forms.URLField(error_messages={'required': '图片url不能为空！'})
    # 确保所选标签为数据库中存在的标签
    tag = forms.ModelChoiceField(queryset=Tag.objects.only('id').filter(is_delete=False),
                                 error_messages={
                                     'required': '文章标签不能为空！',
                                     'invalid_choice': '文章标签id不存在',
                                 })

    class Meta:
        model = News
        fields = ['title', 'digest', 'content', 'image_url', 'tag']
        error_messages = {
            'title': {
                'max_length': '文章标题最大长度不能超过150',
                'min_length': '文章标题最小长度不能小于1',
                'required': '文章标题不能为空！'
            },
            'digest': {
                'max_length': '文章摘要最大长度不能超过150',
                'min_length': '文章摘要最小长度不能小于1',
                'required': '文章摘要不能为空！'
            },
            'content': {
                'required': '文章内容不能为空！',
            }
        }


class DocsPubForm(forms.ModelForm):
    image_url = forms.URLField(label='文档封面图url', error_messages={'required': '图片url不能为空'})
    file_url = forms.URLField(label='文档url', error_messages={'required':'文档url不能够为空'})

    class Meta:
        model = Docs
        fields = ['title', 'desc', 'image_url', 'file_url']
        error_messages = {
            'title':{
                'max_length': '文档标题长度不能超过200',
                'min_length': '文档标题长度不能小于1',
                'required': '文档标题不能为空！'
            },
            'desc':{
                'max_length': '文档描述长度不能超过200',
                'min_length': '文档描述长度不能小于1',
                'required': '文档描述不能为空！'
            }
        }