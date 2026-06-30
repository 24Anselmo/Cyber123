import os
import json
from flask import session

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translations')
os.makedirs(TRANSLATIONS_DIR, exist_ok=True)

_TRADUCOES = {}


def _carregar_idioma(lang):
    path = os.path.join(TRANSLATIONS_DIR, f'{lang}.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def t(chave, **kwargs):
    lang = session.get('lang', 'pt')
    if lang not in _TRADUCOES:
        _TRADUCOES[lang] = _carregar_idioma(lang)
    texto = _TRADUCOES[lang].get(chave, chave)
    if kwargs:
        texto = texto.format(**kwargs)
    return texto


def idiomas_disponiveis():
    arquivos = [f.replace('.json', '') for f in os.listdir(TRANSLATIONS_DIR)
                if f.endswith('.json')]
    if not arquivos:
        arquivos = ['pt']
    return arquivos
