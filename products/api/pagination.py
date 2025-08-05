from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomCategoryPagination(PageNumberPagination):
    page_size = 10  # تعداد آیتم در هر صفحه (دلخواه)
    page_query_param = 'page'  # نام پارامتر صفحه

    def get_paginated_response(self, data):
        return Response({
            'current_page': self.page.number,
            'data': data
        })
