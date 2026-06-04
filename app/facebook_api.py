import os
import logging
import time
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

API_BASE = 'https://graph.facebook.com/v19.0'
REQUEST_TIMEOUT = 30


class FacebookMonitor:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.environ.get('FACEBOOK_ACCESS_TOKEN')
        if not self.access_token:
            logger.warning('Nenhum token de acesso do Facebook fornecido. '
                           'Defina a variável de ambiente FACEBOOK_ACCESS_TOKEN '
                           'ou passe access_token no construtor.')

    def _headers(self):
        return {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}

    def obter_publicacoes(self, grupo_id: str, limite: int = 10) -> list:
        if not self.access_token:
            logger.warning('Sem token do Facebook — retornando lista vazia')
            return []
        url = f'{API_BASE}/{grupo_id}/posts'
        params = {'limit': min(limite, 100), 'fields': 'id,message,created_time,from'}
        try:
            resp = requests.get(url, headers=self._headers(), params=params,
                                timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            posts = []
            for p in data.get('data', []):
                posts.append({
                    'id': p['id'],
                    'mensagem': p.get('message', ''),
                    'autor': p.get('from', {}).get('name', 'Desconhecido') if p.get('from') else 'Desconhecido',
                    'data': p.get('created_time', ''),
                })
            return posts
        except requests.exceptions.Timeout:
            logger.error(f'Timeout ao buscar publicações do grupo {grupo_id}')
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f'Erro ao buscar publicações do grupo {grupo_id}: {e}')
            return []

    def obter_comentarios(self, publicacao_id: str, limite: int = 50) -> list:
        if not self.access_token:
            logger.warning('Sem token do Facebook — retornando lista vazia')
            return []
        url = f'{API_BASE}/{publicacao_id}/comments'
        params = {
            'limit': min(limite, 100),
            'fields': 'id,message,from,created_time,like_count',
            'summary': 'true',
            'order': 'chronological',
        }
        try:
            resp = requests.get(url, headers=self._headers(), params=params,
                                timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            comentarios = []
            for c in data.get('data', []):
                comentarios.append({
                    'id': c['id'],
                    'autor': c.get('from', {}).get('name', 'Desconhecido') if c.get('from') else 'Desconhecido',
                    'texto': c.get('message', ''),
                    'data': c.get('created_time', ''),
                    'like_count': c.get('like_count', 0),
                })
            return comentarios
        except requests.exceptions.Timeout:
            logger.error(f'Timeout ao buscar comentários da publicação {publicacao_id}')
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f'Erro ao buscar comentários da publicação {publicacao_id}: {e}')
            return []

    def analisar_comentarios(self, grupo_id: str, detector) -> dict:
        from app import db
        from app.models import Fonte, Comentario, Analise

        publicacoes = self.obter_publicacoes(grupo_id, limite=10)
        if not publicacoes:
            return {'total': 0, 'analisados': 0, 'ofensivos': [], 'erros': 0}

        fonte_url = f'https://facebook.com/{grupo_id}'
        fonte = Fonte.query.filter_by(url=fonte_url).first()
        if not fonte:
            fonte = Fonte(url=fonte_url, nome=f'Facebook {grupo_id}', tipo='API')
            db.session.add(fonte)
            db.session.commit()

        total = 0
        analisados = 0
        ofensivos = []
        erros = 0

        for pub in publicacoes:
            comentarios = self.obter_comentarios(pub['id'], limite=50)
            for fb_c in comentarios:
                total += 1
                try:
                    comentario = Comentario(
                        fonte_id=fonte.id,
                        texto=fb_c['texto'],
                        autor=fb_c['autor'],
                        data=fb_c.get('data', datetime.now().isoformat()),
                    )
                    db.session.add(comentario)
                    db.session.commit()

                    resultado = detector.analisar(fb_c['texto'])
                    analisados += 1

                    girias_str = ', '.join(
                        [g['termo'] for g in resultado['girias']]
                    ) if resultado['girias'] else ''

                    analise = Analise(
                        comentario_id=comentario.id,
                        classificacao=resultado['classificacao'],
                        confianca=resultado['confianca'],
                        girias=girias_str,
                        data=datetime.now().isoformat(),
                    )
                    db.session.add(analise)
                    db.session.commit()

                    if resultado['confianca'] >= 50:
                        ofensivos.append({
                            'comentario': fb_c,
                            'analise': {
                                'classificacao': resultado['classificacao'],
                                'confianca': resultado['confianca'],
                                'girias': resultado['girias'],
                                'palavras': resultado['palavras'],
                                'nivel_geral': resultado['nivel_geral'],
                            },
                        })
                except Exception as e:
                    logger.error(f'Erro ao processar comentário {fb_c.get("id")}: {e}')
                    erros += 1

        return {
            'total': total,
            'analisados': analisados,
            'ofensivos': ofensivos,
            'erros': erros,
        }

    def monitorar(self, grupo_id: str, detector, intervalo: int = 300):
        from app import db
        while True:
            logger.info(f'Monitorando Facebook grupo {grupo_id}...')
            resultado = self.analisar_comentarios(grupo_id, detector)
            yield resultado
            logger.info(f'Aguardando {intervalo}s para próxima verificação...')
            time.sleep(intervalo)
