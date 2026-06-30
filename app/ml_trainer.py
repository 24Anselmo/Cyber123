import os
import json
import pickle
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    _sklearn_available = True
except ImportError:
    _sklearn_available = False

try:
    from textblob import TextBlob
    _textblob_available = True
except ImportError:
    _textblob_available = False

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, 'cyberbullying_model.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')


def _obter_dados_treino():
    from app import db
    from app.models import Comentario, Analise
    dados = db.session.query(Comentario.texto, Analise.classificacao)\
        .join(Analise, Comentario.id == Analise.comentario_id)\
        .filter(Analise.classificacao != 'Neutro').all()
    textos = [d[0] for d in dados]
    labels = [d[1] for d in dados]
    neutros = db.session.query(Comentario.texto, Analise.classificacao)\
        .join(Analise, Comentario.id == Analise.comentario_id)\
        .filter(Analise.classificacao == 'Neutro').order_by(Analise.id.desc()).limit(500).all()
    textos += [d[0] for d in neutros]
    labels += [d[1] for d in neutros]
    return textos, labels


class CyberbullyingML:
    def __init__(self):
        self._model = None
        self._vectorizer = None
        self._loaded = False
        self._carregar()

    def _carregar(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    self._model = pickle.load(f)
                with open(VECTORIZER_PATH, 'rb') as f:
                    self._vectorizer = pickle.load(f)
                self._loaded = True
            except Exception as e:
                logger.error(f'Erro ao carregar modelo: {e}')

    def treinar(self, forcar=False):
        if not _sklearn_available:
            return {'sucesso': False, 'erro': 'scikit-learn não instalado'}
        if self._loaded and not forcar:
            return {'sucesso': True, 'msg': 'Modelo já carregado. Use forcar=True para re-treinar.'}
        textos, labels = _obter_dados_treino()
        if len(textos) < 10:
            return {'sucesso': False, 'erro': f'Poucos dados ({len(textos)}). Mínimo 10.'}
        try:
            self._vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 3),
                                                stop_words=None, max_df=0.85)
            X = self._vectorizer.fit_transform(textos)
            self._model = LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced')
            self._model.fit(X, labels)
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self._model, f)
            with open(VECTORIZER_PATH, 'wb') as f:
                pickle.dump(self._vectorizer, f)
            self._loaded = True
            return {'sucesso': True, 'msg': f'Modelo treinado com {len(textos)} amostras',
                    'amostras': len(textos), 'classes': list(self._model.classes_)}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    def classificar(self, texto):
        if not self._loaded:
            return {'classificacao': 'Neutro', 'confianca': 0.0}
        try:
            X = self._vectorizer.transform([texto])
            probs = self._model.predict_proba(X)[0]
            pred = self._model.predict(X)[0]
            confianca = float(max(probs) * 100)
            return {
                'classificacao': pred,
                'confianca': round(confianca, 2),
                'probabilidades': dict(zip(self._model.classes_, [round(float(p) * 100, 2) for p in probs])),
            }
        except Exception as e:
            logger.error(f'Erro ML classification: {e}')
            return {'classificacao': 'Neutro', 'confianca': 0.0}


class SarcasmoDetector:
    def _pontos_exclamacao_interrogacao(self, texto):
        exc = texto.count('!')
        interr = texto.count('?')
        return (exc + interr) / max(len(texto), 1)

    def _palavras_maiusculas(self, texto):
        if not texto.strip():
            return 0.0
        caps = sum(1 for c in texto if c.isupper())
        return caps / len(texto)

    def _contraste_sentimento(self, texto):
        if not _textblob_available:
            return 0.0
        try:
            blob = TextBlob(texto)
            frases = [s for s in blob.sentences if len(s.words) > 2]
            if len(frases) < 2:
                return 0.0
            polaridades = [s.sentiment.polarity for s in frases]
            return abs(polaridades[0] - polaridades[-1])
        except Exception:
            return 0.0

    def detetar(self, texto):
        score = 0.0
        score += min(self._pontos_exclamacao_interrogacao(texto) * 50, 20)
        score += min(self._palavras_maiusculas(texto) * 30, 20)
        score += min(self._contraste_sentimento(texto) * 30, 30)

        padroes_sarcasmo = [
            'ah claro', 'pois sim', 'incrivel', 'parabens',
            'muito bom', 'que beleza', 'que maravilha', 'genial',
            'certamente', 'com certeza', 'grande coisa',
            'ta bom', 'tá bom', 'isso mesmo', 'exatamente',
        ]
        texto_lower = texto.lower()
        for padrao in padroes_sarcasmo:
            if padrao in texto_lower:
                score += 10
                break

        score = min(score, 100)
        return {
            'sarcasmo': score >= 50,
            'confianca': round(score, 2),
            'score': round(score, 2),
        }
