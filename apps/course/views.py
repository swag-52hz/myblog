from django.shortcuts import render
from .models import Course, CourseCategory
from django.http import Http404
from django.views import View


def course(request):
    type = request.GET.get('type')
    if type and CourseCategory.objects.filter(name=type, is_delete=False).exists():
        courses = Course.objects.select_related('teacher'). \
            only('teacher__name', 'name', 'cover_url').filter(is_delete=False, category__name=type)
        index = CourseCategory.objects.only('id').filter(name=type).first().id
        types = CourseCategory.objects.only('id', 'name').filter(is_delete=False)
        return render(request, 'course/course.html', locals())
    else:
        return render(request, 'base/404notfound.html')


class CourseDetailView(View):
    def get(self, request, course_id):
        course = Course.objects.select_related('teacher').\
            only('name', 'teacher__name', 'teacher__avatar_url', 'teacher__profession',
                 'teacher__profile', 'introduce', 'outline').filter(is_delete=False, id=course_id).first()
        if course:
            courses = Course.objects.only('name').filter(is_delete=False, category=course.category)
            return render(request, 'course/course_detail.html', locals())
        else:
            return render(request, 'base/404notfound.html')