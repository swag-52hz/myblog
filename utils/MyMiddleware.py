from django.middleware.csrf import get_token
from django.utils.deprecation import MiddlewareMixin


class MyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        get_token(request)


