import pytest
from conftest import app, test_client


def test_basic_route_adding(app):
    @app.route("/home")
    def home(req, resp):
        resp.text = "You are in Home!"


def test_duplicate_routes(app):
    @app.route("/home")
    def home(req, resp):
        resp.text = "You are in Home!"

    with pytest.raises(AssertionError):
        @app.route("/home")
        def home2(req, resp):
            resp.text = "You are in second Home!"


def test_requests_send_by_test_client(app, test_client):
    @app.route("/home")
    def home(req):
        return "You are in Home!"

    response = test_client.get("http://testserver/home")
    assert response.text == "You are in Home!"


def test_parametrized_router(app, test_client):
    @app.route("/hello/{name}")
    def hello(request, name):
        return f"Hello for {name}"

    assert test_client.get("http://testserver/hello/Earling").text == "Hello for Earling"
    assert test_client.get("http://testserver/hello/Braut").text == "Hello for Braut"
    assert test_client.get("http://testserver/hello/Haaland").text == "Hello for Haaland"


def test_default_response(app, test_client):
    response = test_client.get("http://testserver/non-existed-url")
    assert response.status_code == 404
    assert response.text == "Page Not Found"


def test_class_based_get(app, test_client):
    @app.route("/book")
    class Book:
        def get(self, request):
            return "Books List"

    assert test_client.get("http://testserver/book").text == "Books List"


def test_class_based_post(app, test_client):
    @app.route("/book")
    class Book:
        def post(self, request):
            return "Book Created"

    assert test_client.post("http://testserver/book").text == "Book Created"


def test_class_based_not_allowed_method(app, test_client):
    @app.route("/book")
    class Book:
        def get(self, request):
            return "Books List"

    response = test_client.put("http://testserver/book")
    assert response.status_code == 405
    assert response.text == "Method not allowed"


def test_custom_exception_handler(app, test_client):
    def on_exception(request, exc):
        return "OOPS something went wrong!"

    app.add_exception_handler(on_exception)

    @app.route("/exception", counter=True)
    def exception_throwing_api(request):
        raise AttributeError("Attribute Error")

    response = test_client.get("http://testserver/exception")

    assert response.text == "OOPS something went wrong!"

def test_non_existed_static_file(test_client):
    assert test_client.get("http://testserver/nonexisted.cpp").status_code == 404

def test_css_static_file(test_client):
    response = test_client.get("http://testserver/static/test.css")

    assert response.text == "body { background-color: navy; }"

