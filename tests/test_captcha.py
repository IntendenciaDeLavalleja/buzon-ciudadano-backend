from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import Mock

import pytest
from PIL import Image
from app.extensions import db
from app.models.captcha import CaptchaChallenge
from app.models.ticket import Ticket, TicketAttachment
from app.services.minio_service import minio_service


def challenge(client):
    response = client.get('/api/captcha')
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    data = response.json
    assert set(data) == {'id', 'question', 'expires_in'}
    left, right = data['question'].split(' + ')
    return {'captcha_id': data['id'], 'captcha_answer': str(int(left) + int(right))}


def payload(**extra):
    return dict(municipality_or_destination='Intendencia de Lavalleja', category='camineria_rural',
                full_name='Prueba automatizada', email='test@example.com',
                description='Problema en un camino rural de prueba', location_lat='-33.9', location_lng='-54.8', **extra)


def photo():
    image = BytesIO()
    Image.new('RGB', (20, 20)).save(image, format='PNG')
    image.seek(0)
    return (image, 'camino.png')


@pytest.mark.parametrize('extra', [{}, {'captcha_id': 'forged', 'captcha_answer': '2'},
                                     {'captcha_id': [], 'captcha_answer': {} }])
def test_missing_or_malformed_captcha_creates_nothing(client, extra):
    response = client.post('/api/tickets', json=payload(**extra))
    assert response.status_code == 400
    assert response.json['code'] == 'captcha_invalid'
    assert Ticket.query.count() == 0


def test_wrong_answer_consumes_challenge(client):
    data = challenge(client)
    response = client.post('/api/tickets', data=payload(**{**data, 'captcha_answer': '99'}))
    assert response.json['code'] == 'captcha_invalid'
    assert client.post('/api/tickets', data=payload(**data)).status_code == 400
    assert Ticket.query.count() == 0


def test_expired_challenge(client):
    data = challenge(client)
    db.session.get(CaptchaChallenge, data['captcha_id']).expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.session.commit()
    assert client.post('/api/tickets', data=payload(**data)).json['code'] == 'captcha_invalid'


def test_success_with_photo_and_no_replay(client, monkeypatch):
    upload = Mock(return_value=dict(object_key='test/camino.png', file_name='camino.png', content_type='image/png', size_bytes=75))
    monkeypatch.setattr(minio_service, 'upload_file', upload)
    data = challenge(client)
    response = client.post('/api/tickets', data=payload(**data, file=photo()))
    assert response.status_code == 201, response.json
    assert Ticket.query.count() == TicketAttachment.query.count() == 1
    upload.assert_called_once()
    assert client.post('/api/tickets', data=payload(**data, file=photo())).status_code == 400
    assert Ticket.query.count() == 1


def test_storage_failure_rolls_back_captcha_and_ticket_for_retry(client, monkeypatch):
    upload = Mock(side_effect=RuntimeError('storage unavailable'))
    monkeypatch.setattr(minio_service, 'upload_file', upload)
    data = challenge(client)
    assert client.post('/api/tickets', data=payload(**data, file=photo())).status_code == 500
    assert Ticket.query.count() == 0
    assert db.session.get(CaptchaChallenge, data['captcha_id']) is not None
    upload.side_effect = None
    upload.return_value = dict(object_key='test/image', file_name='camino.png', content_type='image/png', size_bytes=75)
    assert client.post('/api/tickets', data=payload(**data, file=photo())).status_code == 201


def test_other_validation_does_not_consume_captcha(client):
    data = challenge(client)
    invalid = payload(**data)
    invalid['email'] = 'invalid'
    assert client.post('/api/tickets', data=invalid).status_code == 400
    assert db.session.get(CaptchaChallenge, data['captcha_id']) is not None


def test_staged_rollout_flag_keeps_old_client_compatible(app, client):
    app.config['CAPTCHA_REQUIRED'] = False
    assert client.post('/api/tickets', data=payload()).status_code == 201
    assert client.post('/api/tickets', data=payload(captcha_id='bad', captcha_answer='1')).status_code == 400


def test_non_object_json_is_rejected(client):
    assert client.post('/api/tickets', json=['invalid']).status_code == 400


def test_challenge_failure_returns_recoverable_error(client, monkeypatch):
    monkeypatch.setattr('app.routes.public.routes.create_challenge', Mock(side_effect=RuntimeError('database down')))
    response = client.get('/api/captcha')
    assert response.status_code == 503
    assert 'database down' not in response.get_data(as_text=True)


def test_challenges_do_not_share_answers(client):
    first, second = challenge(client), challenge(client)
    assert first['captcha_id'] != second['captcha_id']
    assert client.post('/api/tickets', data=payload(**first)).status_code == 201
    assert client.post('/api/tickets', data=payload(**second)).status_code == 201
