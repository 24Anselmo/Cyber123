import json
from app import db
from app.models import Usuario, Fonte


def _login_admin(client):
    return client.post('/login', data={
        'username': 'Alberto Baptista',
        'password': '240520'
    }, follow_redirects=False)


def _login_mod(client):
    Usuario.query.delete()
    db.session.commit()
    from app.routes import _hash_senha
    u = Usuario(nome='mod', email='mod@test.com',
                senha=_hash_senha('1234'), papel='moderador')
    db.session.add(u)
    db.session.commit()
    return client.post('/login', data={
        'username': 'mod',
        'password': '1234'
    }, follow_redirects=False)


class TestEstatisticas:
    def test_get_estatisticas_returns_json_with_keys(self, client):
        _login_admin(client)
        resp = client.get('/api/estatisticas')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_comentarios' in data
        assert 'total_analisados' in data
        assert 'casos_criticos' in data
        assert 'casos_resolvidos' in data
        assert 'taxa_deteccao' in data


class TestDetectar:
    def test_detectar_analisa_e_salva(self, client, app_ctx):
        _login_admin(client)
        f = Fonte(url='http://test.com', nome='Teste', tipo='API')
        db.session.add(f)
        db.session.commit()
        resp = client.post('/api/detectar', json={
            'texto': 'Você é um idiota',
            'autor': 'TestUser'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'classificacao' in data
        assert 'confianca' in data
        assert 'palavras' in data


class TestAlertas:
    def test_get_alertas_returns_list(self, client, app_ctx):
        _login_admin(client)
        f = Fonte(url='http://test.com', nome='Teste', tipo='API')
        db.session.add(f)
        db.session.commit()
        client.post('/api/detectar', json={'texto': 'Você é um idiota'})
        resp = client.get('/api/alertas')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestUsuarios:
    def test_criar_usuario_requer_admin(self, client, app_ctx):
        _login_mod(client)
        resp = client.post('/api/usuarios', json={
            'nome': 'novo', 'email': 'novo@test.com',
            'senha': '1234', 'papel': 'moderador'
        })
        assert resp.status_code == 403

    def test_criar_usuario_como_admin(self, client, app_ctx):
        _login_admin(client)
        resp = client.post('/api/usuarios', json={
            'nome': 'novo', 'email': 'novo@test.com',
            'senha': '1234', 'papel': 'moderador'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome'] == 'novo'


class TestUnauthenticated:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get('/api/estatisticas')
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'erro' in data
