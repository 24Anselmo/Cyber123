import json


def test_login_success(client):
    resp = client.post('/login', data={
        'username': 'Alberto Baptista',
        'password': '240520'
    }, follow_redirects=False)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get('autenticado') is True
        assert sess.get('username') == 'Alberto Baptista'


def test_login_wrong_password(client):
    resp = client.post('/login', data={
        'username': 'Alberto Baptista',
        'password': 'wrongpass'
    }, follow_redirects=False)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('autenticado') is not True


def test_logout_clears_session(client):
    client.post('/login', data={
        'username': 'Alberto Baptista',
        'password': '240520'
    }, follow_redirects=False)
    resp = client.get('/logout', follow_redirects=False)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert not sess.get('autenticado')


def test_protected_route_redirects_when_not_authenticated(client):
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/login' in resp.location
