from app import SpeedAPI
from middleware import BaseMiddleware

app = SpeedAPI()


@app.route("/home", allowed_methods=["GET"])
def home(request):
    return "You are in Home!"


@app.route("/hello/{name}")
def hello(request, name):
    return f"Hello for {name}"


@app.route("/about", counter=True)
def about(request):
    return f"About PAGE, {app.count} people visited!!"


@app.route("/book")
class Book:
    def get(self, request):
        return "Books List"

    def post(self, request):
        return "Books created"


@app.route("/template")
def template(request):
    context = dict(title="Home title", body="Home Body")
    return app.template(
        "home.html",
        context=context,
    )


def on_exception(request, exc):
    return "OOPS something went wrong!"


app.add_exception_handler(on_exception)


@app.route("/exception")
def exception_throwing_api(request):
    raise AttributeError("Attribute Error")


class LoggingMiddleware(BaseMiddleware):
    def process_request(self, request):
        print("Request is being processed...")

    def process_response(self, request, response):
        print("Response has been send.")


app.add_middleware(LoggingMiddleware)
