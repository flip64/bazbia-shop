from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomCategoryPagination(PageNumberPagination):
    page_size = 10                    # تعداد پیش‌فرض آیتم‌ها در هر صفحه
    page_size_query_param = "page_size"  # حالا ?page_size=... کار می‌کنه
    max_page_size = 100               # حداکثر تعداد قابل تنظیم
    page_query_param = 'page'         # نام پارامتر صفحه

    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count / self.get_page_size(self.request))
        return Response({
            'current_page': self.page.number,
            'total_pages': total_pages,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'data': data
        })
