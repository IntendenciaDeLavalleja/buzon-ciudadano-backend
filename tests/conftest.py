import os
os.environ['SECRET_KEY'] = 'test-only-secret-not-for-production'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://127.0.0.1:1/0'

import pytest
from app import create_app
from app.extensions import db
from app.services.minio_service import minio_service
from app.services.mail_service import mail_service


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr('app.init_redis', lambda app: False)
    monkeypatch.setattr(minio_service, 'init_app', lambda app: None)
    monkeypatch.setattr(mail_service, 'send_ticket_received_email', lambda ticket: None)
    application = create_app('testing')
    application.config['CAPTCHA_REQUIRED'] = True
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
