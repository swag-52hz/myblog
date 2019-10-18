import json
from django.shortcuts import render, redirect, reverse
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from .forms import RegisterForm, LoginForm
from django.db.models import Q
from .models import User
from django.views import View
from .constants import USER_SESSION_EXPIRE_TIME
from django.contrib.auth import login, logout


class LoginView(View):
    def get(self, request):
        return render(request, 'users/login.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        form = LoginForm(data=dict_data)
        if form.is_valid():
            hold_login = form.cleaned_data.get('remember_me')
            user_account = form.cleaned_data.get('user_account')
            user = User.objects.filter(Q(username=user_account) | Q(phone=user_account)).first()
            if hold_login:
                request.session.set_expiry(USER_SESSION_EXPIRE_TIME)
            else:
                request.session.set_expiry(0)
            login(request, user)
            return to_json_data(errmsg='恭喜您，登录成功！！！')
        else:
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)
            return to_json_data(errno=Code.DATAERR, errmsg=err_msg_str)


class RegisterView(View):
    def get(self, request):
        return render(request, 'users/register.html')

    def post(self, request):
        json_data = request.body.decode('utf8')
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        dict_data = json.loads(json_data)
        form = RegisterForm(data=dict_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            phone = form.cleaned_data.get('mobile')
            user = User.objects.create_user(username=username, password=password, phone=phone)
            login(request, user)
            return to_json_data(errmsg='恭喜您，注册成功！！！')
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串
            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)


def logout_view(request):
    logout(request)
    return redirect(reverse('news:index'))
