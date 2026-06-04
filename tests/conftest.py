import pytest
import tempfile
import os
from app import create_app, db as _db

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app(db_path=db_path)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.close()
        _db.engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield
