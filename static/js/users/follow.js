$(function () {
    let $focusBtn = $('.focus-btn');
    let $takeoffBtn = $('.watch-btn');

    // 用户点击关注按钮
  $focusBtn.click(function () {
    let sDataParams = {
      "focus_id": $focusBtn[0].id
    };
    $.ajax({
      url: "/focus/",
      type: "GET",
      data: sDataParams,
      dataType: "json",
    })
        .done(function (res) {
          if (res.errno === "0") {
            $focusBtn.html('取消关注');
            $focusBtn.attr('class', 'common watch-btn');
            window.location.reload();
          } else {
            // 失败，打印错误信息
            message.showError(res.errmsg);
          }
        })
        .fail(function () {
          message.showError('服务器超时，请重试！');
        });
  });

  // 用户点击取关按钮
  $takeoffBtn.click(function () {
    let sDataParams = {
      "focus_id": $takeoffBtn[0].id
    };
    $.ajax({
      url: "/takeoff/",
      type: "GET",
      data: sDataParams,
      dataType: "json",
    })
        .done(function (res) {
          if (res.errno === "0") {
            $takeoffBtn.html("关注");
            $takeoffBtn.attr('class', 'common focus-btn');
            window.location.reload();
          } else {
            // 失败，打印错误信息
            message.showError(res.errmsg);
          }
        })
        .fail(function () {
          message.showError('服务器超时，请重试！');
        });
  });
});