import os
import json
import hashlib
import secrets
import time
from datetime import datetime
from functools import wraps

from flask import request, jsonify

TOKENS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'data', 'api_tokens.json')

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30
_requests_ip = {}


def _carregar_tokens():
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _salvar_tokens(tokens):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)


def gerar_token(nome, papel='moderador'):
    tokens = _carregar_tokens()
    token = secrets.token_hex(32)
    tokens[token] = {
        'nome': nome,
        'papel': papel,
        'criado': datetime.now().isoformat(),
        'ativo': True,
    }
    _salvar_tokens(tokens)
    return token


def revogar_token(token):
    tokens = _carregar_tokens()
    if token in tokens:
        tokens[token]['ativo'] = False
        _salvar_tokens(tokens)
        return True
    return False


def listar_tokens():
    tokens = _carregar_tokens()
    return [{'prefixo': t[:8] + '...', **v} for t, v in tokens.items()]


def autenticar_token():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        tokens = _carregar_tokens()
        info = tokens.get(token)
        if info and info.get('ativo'):
            return info
    return None


def rate_limit():
    ip = request.remote_addr or 'unknown'
    now = time.time()
    if ip not in _requests_ip:
        _requests_ip[ip] = []
    _requests_ip[ip] = [t for t in _requests_ip[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_requests_ip[ip]) >= RATE_LIMIT_MAX:
        return True
    _requests_ip[ip].append(now)
    return False


def api_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if rate_limit():
            return jsonify({'erro': 'Rate limit excedido. Máx 30 req/min'}), 429
        info = autenticar_token()
        if not info:
            return jsonify({'erro': 'Token inválido ou ausente'}), 401
        return f(*args, **kwargs)
    return decorated
