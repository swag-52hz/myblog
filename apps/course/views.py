from django.shortcuts import render
from .models import Course
from django.http import Http404
from django.views import View


def course(request):
    courses = Course.objects.select_related('teacher').\
        only('teacher__name', 'name', 'cover_url').filter(is_delete=False)
    return render(request, 'course/course.html', locals())


class CourseDetailView(View):
    def get(self, request, course_id):
        courses = Course.objects.only('name').filter(is_delete=False)
        course = Course.objects.select_related('teacher').\
            only('name', 'teacher__name', 'teacher__avatar_url', 'teacher__profession',
                 'teacher__profile', 'introduce', 'outline').filter(is_delete=False, id=course_id).first()
        if course:
            return render(request, 'course/course_detail.html', locals())
        else:
            return Http404('此课程不存在！！！')