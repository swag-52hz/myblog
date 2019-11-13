$(function () {
  // 新闻列表功能
  let iPage = 1;  //默认第1页
  let iTotalPage = 1; //默认总页数为1
  let sCurrentTagId = Number(window.location.href.split("/")[5]); //获取当前页面的分类id
  let bIsLoadData = true;   // 是否正在向后台加载数据

  // 加载新闻列表信息
  fn_load_content();

  //页面滚动加载相关
  $(window).scroll(function () {
    // 浏览器窗口高度
    let showHeight = $(window).height();

    // 整个网页的高度
    let pageHeight = $(document).height();

    // 页面可以滚动的距离
    let canScrollHeight = pageHeight - showHeight;

    // 页面滚动了多少,这个是随着页面滚动实时变化的
    let nowScroll = $(document).scrollTop();

    if ((canScrollHeight - nowScroll) < 100) {
      // 判断页数，去更新新闻数据
      if (!bIsLoadData) {
        bIsLoadData = true;
        // 如果当前页数据如果小于总页数，那么才去加载数据
        if (iPage < iTotalPage) {
          iPage += 1;
          $(".btn-more").remove();  // 删除标签
          // 去加载数据
          fn_load_content()
        } else {
          message.showInfo('已全部加载，没有更多内容！');
          $(".btn-more").remove();  // 删除标签
          $(".news-list").append($('<a href="javascript:void(0);" class="btn-more">已全部加载，没有更多内容！</a>'))

        }
      }
    }
  });


  // 定义向后端获取新闻列表数据的请求
  function fn_load_content() {
    // let sCurrentTagId = $('.active a').attr('data-id');

    // 创建请求参数
    let sDataParams = {
      "tag_id": sCurrentTagId,
      "page": iPage
    };

    // 创建ajax请求
    $.ajax({
      // 请求地址
      url: "/news/",  // url尾部需要添加/
      // 请求方式
      type: "GET",
      data: sDataParams,
      // 响应数据的格式（后端返回给前端的格式）
      dataType: "json",
    })
      .done(function (res) {
        if (res.errno === "0") {
          iTotalPage = res.data.total_pages;  // 后端传过来的总页数
          if (iPage === 1) {
            $(".category-article-list").html("")
          }

          res.data.news.forEach(function (one_news) {
            let content = `
              <li>
                <a href="/news/${one_news.id}/">
                    <div class="category-title"><span>原创</span> <h3>${one_news.title}</h3></div>
                    <div class="category-desc">${one_news.digest}</div>
                    <div class="category-info">
                        <p>
                            <span>${one_news.update_time}</span>
                            <span>阅读数：${one_news.clicks}</span>
                            <span>评论数：${one_news.comment_count}</span>
                        </p>
                    </div>
                </a>
            </li>`;
            $(".category-article-list").append(content)
          });

          $(".news-list").append($('<a href="javascript:void(0);" class="btn-more">滚动加载更多</a>'));
          // 数据加载完毕，设置正在加载数据的变量为false，表示当前没有在加载数据
          bIsLoadData = false;

        } else {
          // 登录失败，打印错误信息
          message.showError(res.errmsg);
        }
      })
      .fail(function () {
        message.showError('服务器超时，请重试！');
      });
  }

});