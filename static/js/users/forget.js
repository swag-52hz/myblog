$(function () {
  let $mobile = $('#mobile');  // 选择id为mobile的网页元素，需要定义一个id为mobile
  let $smsCodeBtn = $('.form-item .sms-captcha');  // 获取短信验证码按钮元素，需要定义一个id为input_smscode
  let $register = $('.form-contain');  // 获取下一步表单元素

  // 判断用户手机号是否注册
  $mobile.blur(function () {
    fn_check_mobile();
  });

  // 4、发送短信验证码逻辑
  $smsCodeBtn.click(function () {
    // 判断手机号是否输入
    if (fn_check_mobile() !== "success") {
      return
    }

    let sMobile = $mobile.val();  // 获取用户输入的手机号码字符串

    // 向后端发送请求
    $.ajax({
      url: '/phone/' + sMobile + '/',
      type: 'GET',
      dataType: 'json',
      async: false
    })
      .done(function (res) {
        if (res.errno === "0") {
          // 倒计时60秒，60秒后允许用户再次点击发送短信验证码的按钮
           message.showSuccess('短信验证码发送成功');
          let num = 60;
          // 设置一个计时器
          let t = setInterval(function () {
            if (num === 1) {
              // 如果计时器到最后, 清除计时器对象
              clearInterval(t);
              // 将点击获取验证码的按钮展示的文本恢复成原始文本
              $smsCodeBtn.html("获取验证码");
            } else {
              num -= 1;
              // 展示倒计时信息
              $smsCodeBtn.html(num + "秒");
            }
          }, 1000);
        } else {
          message.showError(res.errmsg);
        }
      })
      .fail(function(){
        message.showError('服务器超时，请重试！');
      });

  });


  // 5、点击下一步逻辑逻辑
  $register.submit(function (e) {
    // 阻止默认提交操作
    e.preventDefault();
    let sMobile = $mobile.val();  // 获取用户输入的手机号码字符串
    let sSmsCode = $("input[name=sms_captcha]").val();
    // 判断用户输入的短信验证码是否为4位数字
    if (!(/^\d{4}$/).test(sSmsCode)) {
      message.showError('短信验证码格式不正确，必须为4位数字！');
      return
    }

    // 发起注册请求
    // 1、创建请求参数
    let SdataParams = {
      "mobile": sMobile,
      "sms_code": sSmsCode
    };

    // 2、创建ajax请求
    $.ajax({
      // 请求地址
      url: "/users/forget/",  // url尾部需要添加/
      // 请求方式
      type: "POST",
      data: JSON.stringify(SdataParams),
      // 请求内容的数据类型（前端发给后端的格式）
      contentType: "application/json; charset=utf-8",
      // 响应数据的格式（后端返回给前端的格式）
      dataType: "json",
    })
      .done(function (res) {
        if (res.errno === "0") {
          // 注册成功
          message.showSuccess('验证通过');
          setTimeout(function () {
            // 注册成功之后重定向到主页
            window.location.href = 'http://127.0.0.1:8000/users/reset/';
          }, 1000)
        } else {
          // 注册失败，打印错误信息
          message.showError(res.errmsg);
        }
      })
      .fail(function(){
        message.showError('服务器超时，请重试！');
      });

  });


  // 判断手机号是否注册
  function fn_check_mobile() {
    let sMobile = $mobile.val();  // 获取用户输入的手机号码字符串
    let sReturnValue = "";
    if (sMobile === "") {
      message.showError('手机号不能为空！');
      return
    }
    if (!(/^1[345789]\d{9}$/).test(sMobile)) {
      message.showError('手机号码格式不正确，请重新输入！');
      return
    }

    $.ajax({
      url: '/mobiles/' + sMobile + '/',
      type: 'GET',
      dataType: 'json',
      async: false
    })
      .done(function (res) {
        if (res.data.count !== 0) {
          message.showSuccess(res.data.mobile + '为合法账号');
          sReturnValue = "success"
        } else {
          message.showError(res.data.mobile + '未进行注册！');
          sReturnValue = ""
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
        sReturnValue = ""
      });
    return sReturnValue

  }


  // get cookie using jQuery
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  // Setting the token on the AJAX request
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      }
    }
  });

});