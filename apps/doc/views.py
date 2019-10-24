from django.shortcuts import render
from .models import Docs
from django.views import View


class DocDownloadView(View):
    def get(self, request):
        docs = Docs.objects.only('title', 'image_url', 'desc').filter(is_delete=False)
        return render(request, 'doc/docDownload.html', locals())