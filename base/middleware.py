from django.utils.deprecation import MiddlewareMixin


class AccessControlMiddleware(MiddlewareMixin):

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        return super_new(cls)

    def __call__(self, request):
        if request.user.is_authenticated:
            ...
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, *view_args, **view_kwargs):
        view_class = getattr(view_func, 'view_class', None)
        if view_class is None:
            return
        request.is_api = getattr(view_class, 'is_api', False)
