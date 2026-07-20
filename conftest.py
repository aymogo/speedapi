import pytest
from app import SpeedAPI


@pytest.fixture
def app():
    return SpeedAPI()


@pytest.fixture
def test_client(app):
    return app.test_session()
