import os
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import requests
    _requests_available = True
except ImportError:
    _requests_available = False

TWITTER_API_BASE = 'https://api.twitter.com/2'
REQUEST_TIMEOUT = 5

_SIMULATED_TWEETS = [
    'Vou te matar seu idiota',
    'Ola pessoal, tudo bem?',
    'Mucolesse sonhi curi atxu essue',
    'Gostei muito deste post!',
    'Vai te foder, seu estupido!',
    'Bom dia para todos',
    'Odeio voces todos',
    'Que otimo dia',
    'Cucaujola voce e',
    'Concordo plenamente',
    'cutxuala-phula nao presta',
    'kizua mentiroso',
    'Bom trabalho em equipe',
    'Obrigado pela ajuda',
    'Seu burro incompetente',
]


class TwitterMonitor:
    def __init__(self, bearer_token=None):
        self.bearer_token = bearer_token or os.environ.get('TWITTER_BEARER_TOKEN')

    @property
    def offline(self):
        return not self.bearer_token or not _requests_available

    def _headers(self):
        if self.offline:
            return {}
        return {'Authorization': f'Bearer {self.bearer_token}'}

    def _api_get(self, endpoint, params):
        if self.offline:
            return None
        url = f'{TWITTER_API_BASE}/{endpoint}'
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning('Twitter API timeout - modo offline ativado')
            return None
        except Exception as e:
            logger.error(f'Twitter API error: {e}')
            return None

    def _simular_tweets(self, query, max_results=10):
        import random
        n = min(max_results, len(_SIMULATED_TWEETS))
        selecionados = random.sample(_SIMULATED_TWEETS, n)
        return [{
            'id': f'sim_{i}',
            'texto': t,
            'autor': f'User_{random.randint(100,999)}',
            'data': datetime.now().isoformat(),
            'lingua': 'pt',
            'fonte': 'twitter_simulado',
        } for i, t in enumerate(selecionados)]

    def search_recent(self, query, max_results=10):
        if self.offline:
            logger.info(f'Twitter offline: simulando dados para "{query}"')
            return self._simular_tweets(query, max_results)
        data = self._api_get('tweets/search/recent', {
            'query': query,
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,author_id,lang',
        })
        if not data or 'data' not in data:
            logger.info('Twitter API sem dados - modo offline')
            return self._simular_tweets(query, max_results)
        return [{
            'id': t['id'], 'texto': t['text'],
            'autor': t.get('author_id', 'desconhecido'),
            'data': t.get('created_at', datetime.now().isoformat()),
            'lingua': t.get('lang', ''), 'fonte': 'twitter',
        } for t in data['data']]

    def analisar_comentarios(self, query, detector):
        from app import db
        from app.models import Fonte, Comentario, Analise
        tweets = self.search_recent(query)
        if not tweets:
            return {'total': 0, 'analisados': 0, 'ofensivos': []}
        fonte = Fonte.query.filter_by(url=f'twitter://{query}').first()
        if not fonte:
            nome = f'Twitter: {query[:30]}'
            if self.offline:
                nome += ' (simulado)'
            fonte = Fonte(url=f'twitter://{query}', nome=nome, tipo='API')
            db.session.add(fonte)
            db.session.commit()
        resultados = []
        for t in tweets:
            comentario = Comentario(fonte_id=fonte.id, texto=t['texto'],
                                    autor=t['autor'], data=t['data'])
            db.session.add(comentario)
            db.session.commit()
            res = detector.analisar(t['texto'])
            analise = Analise(comentario_id=comentario.id,
                              classificacao=res['classificacao'],
                              confianca=res['confianca'],
                              girias=', '.join([g['termo'] for g in res['girias']]),
                              data=datetime.now().isoformat())
            db.session.add(analise)
            db.session.commit()
            resultados.append({'comentario': t, 'analise': res})
        return {'total': len(tweets), 'analisados': len(resultados), 'ofensivos': resultados, 'offline': self.offline}

    def monitorar(self, query, detector, intervalo=300):
        while True:
            logger.info(f'Twitter: monitorando "{query}"...')
            resultado = self.analisar_comentarios(query, detector)
            yield resultado
            time.sleep(intervalo)
