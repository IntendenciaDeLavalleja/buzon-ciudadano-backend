"""Local integration server. Real routes/SQL/validation, fake storage and mail.

Run from repository root: python -m tests.serve_integration
Never use this entry point for production.
"""
import os
os.environ['SECRET_KEY'] = 'integration-tests-only'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['CORS_ORIGINS'] = 'http://127.0.0.1:4173'

import app as app_module
from app.extensions import db
from app.services.minio_service import minio_service
from app.services.mail_service import mail_service

app_module.init_redis = lambda app: False
minio_service.init_app = lambda app: None
minio_service.upload_file = lambda file, code: dict(
    object_key=f'test/{code}/{file.filename}', file_name=file.filename,
    content_type=file.content_type, size_bytes=len(file.read()),
)
mail_service.send_ticket_received_email = lambda ticket: None
application = app_module.create_app('testing')
application.config['CAPTCHA_REQUIRED'] = True
with application.app_context():
    db.create_all()

if __name__ == '__main__':
    application.run(host='127.0.0.1', port=5001, use_reloader=False)
