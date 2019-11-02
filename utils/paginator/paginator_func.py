def get_page_list(page, paginator):
    num = 3
    # total_num = paginator.count     # 文章总数
    total_page = paginator.num_pages    # 总页数
    page_list = []
    if page - (num - 1) // 2 <= 0:  # 显示左边的页码以及当前页码
        for i in range(page):
            page_list.append(i + 1)
    else:  # 说明当前页码足够大
        for i in range(page - (num - 1) // 2, page + 1):
            page_list.append(i)
    if page + (num - 1) / 2 >= total_page:
        for i in range(page + 1, total_page + 1):
            page_list.append(i)
    else:
        for i in range(page + 1, page + (num - 1) // 2 + 1):
            page_list.append(i)
    return page_list
