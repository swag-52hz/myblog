$(function () {
    // let $e = window.wangEditor;
    // window.editor = new $e('#news-content');
    // window.editor.create();

    // 获取图片元素
    var img = document.getElementById('user-img');

    // ================== 上传图片文件至服务器 ================
    let $upload_to_server = $("#upload-news-thumbnail");
    $upload_to_server.change(function () {
        let file = this.files[0];   // 获取文件
        let oFormData = new FormData();  // 创建一个 FormData
        oFormData.append("image_file", file); // 把文件添加进去
        // 发送请求
        $.ajax({
            url: "/users/upload/",
            method: "POST",
            data: oFormData,
            processData: false,   // 定义文件的传输
            contentType: false,
        })
            .done(function (res) {
                if (res.errno === "0") {
                    // 更新标签成功
                    message.showSuccess("头像修改成功");
                    img.src = res["data"]["image_url"];
                    setTimeout(function () {
                        window.location.reload();
                    }, 1000)
                } else {
                    message.showError(res.errmsg)
                }
            })
            .fail(function () {
                message.showError('服务器超时，请重试！');
            });

    });

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
