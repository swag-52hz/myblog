from django import template


register = template.Library()


@register.filter
def change(value):
    num_list = str(value).split('.')
    if len(num_list[1]) == 1:
        num_list[1] = num_list[1] + '0'
    res = '00:0' + num_list[0] + ':' + num_list[1]
    return res