import inspect
import os
import requests
import wsgiadapter

from jinja2 import Environment, FileSystemLoader
from parse import parse
from webob import Request, Response
from whitenoise import WhiteNoise

from middleware import BaseMiddleware


class SpeedAPI:
    def __init__(self, template_dir="templates", staticfiles_dir="static"):
        self.routes = dict()
        self.count = 0
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.abspath(template_dir))
        )
        self.custom_exception_handler = None
        self.staticfiles_prefix = "/static"
        self.whitenoise_app = WhiteNoise(self.get_wsgi_app, root=staticfiles_dir, prefix=self.staticfiles_prefix)
        self.middleware = BaseMiddleware(app=self)
        self.ALL_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "CONNECT", "TRACE"]

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        if path_info.startswith(self.staticfiles_prefix):
            return self.whitenoise_app(environ, start_response)
        return self.middleware(environ, start_response)

    def get_wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.handle_request(request)
        return response(environ, start_response)

    def route(self, path, allowed_methods=None, *args, **kwargs):
        assert path not in self.routes, "Duplicate path is not allowed"

        def wrapper(handler):
            nonlocal allowed_methods
            if allowed_methods is None:
                allowed_methods = self.ALL_HTTP_METHODS
            self.routes[path] = dict(handler=handler, allowed_methods=allowed_methods)
            handler._counter = kwargs.get("counter", False)
            return handler

        return wrapper

    def handle_request(self, request):
        response = Response()

        handler_data, kwargs = self.find_handler(request)

        if handler_data is None:
            self.default_response(response)
            return response

        handler = handler_data["handler"]
        allowed_methods = handler_data["allowed_methods"]

        if inspect.isclass(handler):
            request_method = request.method.lower()
            handler = getattr(handler(), request_method, None)
            if handler is None:
                return self.method_not_allwed_response(response)

        if getattr(handler, '_counter', False):
            self.count += 1

        if request.method not in allowed_methods:
            return self.method_not_allwed_response(response)

        try:
            response.text = handler(request, **kwargs)
        except Exception as e:
            if self.custom_exception_handler is None:
                raise e
            response.text = self.custom_exception_handler(request, e)

        return response

    def find_handler(self, request):
        for path, handler_data in self.routes.items():
            parsed_path = parse(path, request.path)
            if parsed_path:
                return handler_data, parsed_path.named
        return None, None

    def default_response(self, response):
        response.status_code = 404
        response.text = "Page Not Found"

    def method_not_allwed_response(self, response):
        response.status_code = 405
        response.text = "Method not allowed"
        return response

    def test_session(self):
        session = requests.Session()
        session.mount("http://testserver", wsgiadapter.WSGIAdapter(self))
        return session

    def template(self, html_path, context=None):
        context = context or {}
        return self.template_env.get_template(html_path).render(**context)

    def add_exception_handler(self, handler):
        self.custom_exception_handler = handler

    def add_middleware(self, middleware_cls):
        self.middleware.add(middleware_cls)
