from django.shortcuts import render
from datetime import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
import json
from django.http import JsonResponse, HttpResponse
from .models import Depart
from django.views import View
from .serializers import DeptSerializer


@method_decorator(csrf_exempt, name='dispatch')
class DeptView(View):
    def get(self, request):
        depts = Depart.objects.filter(is_delete=False)
        dept_list = []
        for dept in depts:
            dept_list.append({
                'name': dept.name,
                'slogan': dept.slogan,
                'cost': dept.cost,
                'profit': dept.profit,
                'c_time': dept.c_time
            })
        return JsonResponse(dept_list, safe=False)

    def post(self, request):
        json_data = request.body.decode('utf8')
        dict_data = json.loads(json_data)
        dept = Depart.objects.create(
            name=dict_data.get('name'),
            slogan=dict_data.get('slogan'),
            cost=dict_data.get('cost'),
            profit=dict_data.get('profit'),
            c_time=datetime.strptime(dict_data.get('c_time'), '%Y-%m-%d')
        )
        return JsonResponse({
            'id': dept.id,
            'name': dept.name,
            'slogan': dept.slogan,
            'cost': dept.cost,
            'profit': dept.profit,
            'c_time': dept.c_time
        })


@method_decorator(csrf_exempt, name='dispatch')
class DeptInfoView(View):
    def put(self, request, pk):
        try:
            dept = Depart.objects.get(pk=pk)
        except Depart.DoesNotExist:
            return HttpResponse(status=404)
        json_data = request.body.decode('utf8')
        dict_data = json.loads(json_data)
        name = dict_data.get('name')

        dept.name = dict_data.get('name'),
        dept.slogan = dict_data.get('slogan'),
        dept.cost = dict_data.get('cost')
        dept.profit = dict_data.get('profit')
        dept.c_time = datetime.strptime(dict_data.get('c_time'), '%Y-%m-%d')
        dept.save()

        return JsonResponse({
            'id': dept.id,
            'name': dept.name[0],
            'slogan': dept.slogan[0],
            'cost': dept.cost,
            'profit': dept.profit,
            'c_time': dept.c_time
        })

    def delete(self, request, pk):
        try:
            dept = Depart.objects.get(pk=pk)
        except Depart.DoesNotExist:
            return HttpResponse(status=404)
        dept.delete()
        return HttpResponse('删除成功！！！')


class DeptsViewset(viewsets.ModelViewSet):
    queryset = Depart.objects.all()
    serializer_class = DeptSerializer


