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

YOUTUBE_API_BASE = 'https://www.googleapis.com/youtube/v3'
REQUEST_TIMEOUT = 5

_SIMULATED_COMMENTS = [
    'Vou te matar seu animal', 'Muito bom video!', 'Mucolesse sonhi curi',
    'Compartilha mais conteudo', 'Vai se foder seu palhaco',
    'Obrigado pelo video', 'Odeio esse canal', 'Excelente trabalho',
    'Cucaujola voce e um lixo', 'Amei o conteudo',
    'cutxuala-phula nao presta', 'Seu burro, nao sabe de nada',
    'Muito educativo', 'Concordo plenamente',
]


class YouTubeMonitor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('YOUTUBE_API_KEY')

    @property
    def offline(self):
        return not self.api_key or not _requests_available

    def _api_get(self, endpoint, params):
        if self.offline:
            return None
        params['key'] = self.api_key
        url = f'{YOUTUBE_API_BASE}/{endpoint}'
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning('YouTube API timeout - modo offline')
            return None
        except Exception as e:
            logger.error(f'YouTube API error: {e}')
            return None

    def _simular_comentarios(self, video_id, max_results=50):
        import random
        n = min(max_results, len(_SIMULATED_COMMENTS))
        selecionados = random.sample(_SIMULATED_COMMENTS, n)
        return [{
            'id': f'sim_yt_{i}',
            'texto': t,
            'autor': f'Usuario_{random.randint(100,999)}',
            'data': datetime.now().isoformat(),
            'fonte': 'youtube_simulado',
            'video_id': video_id,
        } for i, t in enumerate(selecionados)]

    def obter_comentarios(self, video_id, max_results=50):
        if self.offline:
            logger.info(f'YouTube offline: simulando dados para vídeo {video_id}')
            return self._simular_comentarios(video_id, max_results)
        params = {
            'part': 'snippet', 'videoId': video_id,
            'maxResults': min(max_results, 100),
            'textFormat': 'plainText', 'order': 'time',
        }
        data = self._api_get('commentThreads', params)
        if not data or 'items' not in data:
            logger.info('YouTube API sem dados - modo offline')
            return self._simular_comentarios(video_id, max_results)
        comentarios = []
        for item in data['items']:
            snippet = item['snippet']['topLevelComment']['snippet']
            comentarios.append({
                'id': item['id'], 'texto': snippet.get('textDisplay', ''),
                'autor': snippet.get('authorDisplayName', 'Desconhecido'),
                'data': snippet.get('publishedAt', datetime.now().isoformat()),
                'fonte': 'youtube', 'video_id': video_id,
            })
        return comentarios

    def analisar_comentarios(self, video_id, detector):
        from app import db
        from app.models import Fonte, Comentario, Analise
        comments = self.obter_comentarios(video_id)
        if not comments:
            return {'total': 0, 'analisados': 0, 'ofensivos': []}
        fonte = Fonte.query.filter_by(url=f'youtube://{video_id}').first()
        if not fonte:
            nome = f'YouTube: {video_id[:20]}'
            if self.offline:
                nome += ' (simulado)'
            fonte = Fonte(url=f'youtube://{video_id}', nome=nome, tipo='API')
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

    def monitorar(self, video_id, detector, intervalo=300):
        while True:
            logger.info(f'YouTube: monitorando vídeo {video_id}...')
            resultado = self.analisar_comentarios(video_id, detector)
            yield resultado
            time.sleep(intervalo)
