class CurrentAppMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    # https://stackoverflow.com/a/9807233
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.current_app = view_func.__module__.split('.')[1]

