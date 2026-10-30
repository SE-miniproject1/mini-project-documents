from . import context


class CurrentRequestMiddleware:
    """Makes the request available to audit entries made deeper in the call stack."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = context.set_request(request)
        try:
            return self.get_response(request)
        finally:
            context.reset(token)
