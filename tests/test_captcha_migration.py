from flask_migrate import upgrade, downgrade
from sqlalchemy import inspect, text
from app.extensions import db


def test_migration_preserves_existing_tickets(app):
    db.drop_all()
    upgrade(revision='b5c6d7e8f9a0')
    db.session.execute(text("INSERT INTO tickets (tracking_code, municipality_or_destination, category, full_name, email, description, status) VALUES ('BUZ-2026-EXISTING', 'Lavalleja', 'camineria_rural', 'Existing citizen', 'existing@example.com', 'Existing report', 'NEW')"))
    db.session.commit()
    upgrade()
    assert 'captcha_challenges' in inspect(db.engine).get_table_names()
    assert db.session.execute(text('SELECT COUNT(*) FROM tickets')).scalar() == 1
    downgrade(revision='b5c6d7e8f9a0')
    assert 'captcha_challenges' not in inspect(db.engine).get_table_names()
    assert db.session.execute(text('SELECT COUNT(*) FROM tickets')).scalar() == 1
