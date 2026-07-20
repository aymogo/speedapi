import inspect
import os
import requests
import wsgiadapter

from jinja2 import Environment, FileSystemLoader
from parse import parse
from webob import Request, Response


class SpeedAPI:
    def __init__(self, template_dir="templates"):
        self.routes = dict()
        self.count = 0
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.abspath(template_dir))
        )
        self.custom_exception_handler = None

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.handle_request(request)
        return response(environ, start_response)

    def route(self, path, *args, **kwargs):
        assert path not in self.routes, "Duplicate path is not allowed"

        def wrapper(handler):
            self.routes[path] = handler
            handler._counter = kwargs.get("counter", False)
            return handler

        return wrapper

    def handle_request(self, request):
        response = Response()

        handler, kwargs = self.find_handler(request)

        if handler is None:
            self.default_response(response)
            return response

        if inspect.isclass(handler):
            request_method = request.method.lower()
            handler = getattr(handler(), request_method, None)
            if handler is None:
                response.status_code = 405
                response.text = "Method not allowed"
                return response

        if getattr(handler, '_counter', False):
            self.count += 1

        try:
            response.text = handler(request, **kwargs)
        except Exception as e:
            if self.custom_exception_handler is None:
                raise e
            response.text = self.custom_exception_handler(request, e)

        return response

    def find_handler(self, request):
        for path, handler in self.routes.items():
            parsed_path = parse(path, request.path)
            if parsed_path:
                return handler, parsed_path.named
        return None, None

    def default_response(self, response):
        response.status_code = 404
        response.text = "Page Not Found"

    def test_session(self):
        session = requests.Session()
        session.mount("http://testserver", wsgiadapter.WSGIAdapter(self))
        return session

    def template(self, html_path, context=None):
        context = context or {}
        return self.template_env.get_template(html_path).render(**context)

    def add_exception_handler(self, handler):
        self.custom_exception_handler = handler
