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

REQUEST_TIMEOUT = 5

_SIMULATED_COMMENTS = [
    'Vou te matar seu otario', 'Linda foto!', 'Mucolesse sonhi',
    'Arrasou', 'Vai se foder sua puta',
    'Obrigado pelo follow', 'Odeio voce', 'Maravilhosa',
    'Cucaujola ridicula', 'Amei',
    'cutxuala-phula', 'Seu feia',
    'Lindo sorriso', 'Gosto muito',
]


class InstagramMonitor:
    def __init__(self, access_token=None, user_id=None):
        self.access_token = access_token or os.environ.get('INSTAGRAM_ACCESS_TOKEN')
        self.user_id = user_id or os.environ.get('INSTAGRAM_USER_ID')

    @property
    def offline(self):
        return not self.access_token or not _requests_available

    def _api_get(self, url, params):
        if self.offline:
            return None
        params['access_token'] = self.access_token
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning('Instagram API timeout - modo offline')
            return None
        except Exception as e:
            logger.error(f'Instagram API error: {e}')
            return None

    def _simular_comentarios(self, media_id, limit=25):
        import random
        n = min(limit, len(_SIMULATED_COMMENTS))
        selecionados = random.sample(_SIMULATED_COMMENTS, n)
        return [{
            'id': f'sim_ig_{i}',
            'texto': t,
            'autor': f'user_{random.randint(100,999)}',
            'data': datetime.now().isoformat(),
            'fonte': 'instagram_simulado',
            'media_id': media_id,
        } for i, t in enumerate(selecionados)]

    def obter_comentarios_media(self, media_id, limit=25):
        if self.offline:
            logger.info(f'Instagram offline: simulando dados para media {media_id}')
            return self._simular_comentarios(media_id, limit)
        url = f'https://graph.facebook.com/v19.0/{media_id}/comments'
        params = {
            'fields': 'id,text,username,timestamp,like_count',
            'limit': min(limit, 50),
        }
        data = self._api_get(url, params)
        if not data or 'data' not in data:
            logger.info('Instagram API sem dados - modo offline')
            return self._simular_comentarios(media_id, limit)
        return [{
            'id': c['id'], 'texto': c.get('text', ''),
            'autor': c.get('username', 'Desconhecido'),
            'data': c.get('timestamp', datetime.now().isoformat()),
            'fonte': 'instagram', 'media_id': media_id,
        } for c in data['data']]

    def obter_media_recentes(self, limit=10):
        if self.offline:
            return []
        url = f'https://graph.facebook.com/v19.0/{self.user_id}/media'
        params = {'fields': 'id,caption,media_type,permalink,timestamp', 'limit': min(limit, 25)}
        data = self._api_get(url, params)
        if not data or 'data' not in data:
            return []
        return data['data']

    def analisar_comentarios(self, media_id, detector):
        from app import db
        from app.models import Fonte, Comentario, Analise
        comments = self.obter_comentarios_media(media_id)
        if not comments:
            return {'total': 0, 'analisados': 0, 'ofensivos': []}
        fonte = Fonte.query.filter_by(url=f'instagram://{media_id}').first()
        if not fonte:
            nome = f'Instagram: {media_id[:20]}'
            if self.offline:
                nome += ' (simulado)'
            fonte = Fonte(url=f'instagram://{media_id}', nome=nome, tipo='API')
            db.session.add(fonte)
            db.session.commit()
        resultados = []
        for c in comments:
            comentario = Comentario(fonte_id=fonte.id, texto=c['texto'],
                                    autor=c['autor'], data=c['data'])
            db.session.add(comentario)
            db.session.commit()
            res = detector.analisar(c['texto'])
            analise = Analise(comentario_id=comentario.id,
                              classificacao=res['classificacao'],
                              confianca=res['confianca'],
                              girias=', '.join([g['termo'] for g in res['girias']]),
                              data=datetime.now().isoformat())
            db.session.add(analise)
            db.session.commit()
            resultados.append({'comentario': c, 'analise': res})
        return {'total': len(comments), 'analisados': len(resultados), 'ofensivos': resultados, 'offline': self.offline}

    def monitorar(self, media_id, detector, intervalo=300):
        while True:
            logger.info(f'Instagram: monitorando media {media_id}...')
            resultado = self.analisar_comentarios(media_id, detector)
            yield resultado
            time.sleep(intervalo)
