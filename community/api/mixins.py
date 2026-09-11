from rest_framework.permissions import AllowAny, IsAuthenticated


class PublicReadAuthenticatedWriteMixin:
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]