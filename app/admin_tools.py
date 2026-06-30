import os
import json
import shutil
import logging
import threading
from datetime import datetime

from flask import request
from app import db
from app.models import Analise, Comentario

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
AUDIT_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'audit.log')

BLOQUEIOS = {}


def auditoria(acao, detalhe=''):
    try:
        with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat()}] {request.remote_addr} | '
                    f'{session.get("username", "anónimo")} | {acao} | {detalhe}\n')
    except Exception:
        pass


def obter_logs_auditoria(limite=200):
    if not os.path.exists(AUDIT_LOG):
        return []
    try:
        with open(AUDIT_LOG, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        logs = []
        for linha in linhas[-limite:]:
            partes = linha.strip().split(' | ')
            if len(partes) >= 3:
                logs.append({
                    'data': partes[0].strip('[]'),
                    'ip': partes[1],
                    'usuario': partes[2],
                    'acao': ' | '.join(partes[3:-1]) if len(partes) > 4 else partes[3] if len(partes) > 3 else '',
                    'detalhe': partes[-1] if len(partes) > 4 else '',
                })
        return logs
    except Exception:
        return []


def backup_bd():
    from app import db
    from app import create_app as _ca
    db_path = db.engine.url.database
    if not db_path or not os.path.exists(db_path):
        return {'sucesso': False, 'erro': 'BD não encontrada'}
    data_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'cyberbullying_backup_{data_str}.db')
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f'Backup criado: {backup_path}')
        _limpar_backups_antigos()
        return {'sucesso': True, 'path': backup_path}
    except Exception as e:
        logger.error(f'Erro backup: {e}')
        return {'sucesso': False, 'erro': str(e)}


def _limpar_backups_antigos(manter=10):
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('cyberbullying_backup_')])
    while len(backups) > manter:
        remover = os.path.join(BACKUP_DIR, backups.pop(0))
        try:
            os.remove(remover)
        except Exception:
            pass


def backup_auto(intervalo_segundos=3600):
    while True:
        threading.Event().wait(intervalo_segundos)
        try:
            backup_bd()
        except Exception as e:
            logger.error(f'Backup automático falhou: {e}')


def iniciar_backup_auto(intervalo=3600):
    t = threading.Thread(target=backup_auto, args=(intervalo,), daemon=True)
    t.start()
    logger.info(f'Backup automático iniciado a cada {intervalo}s')
    return t


def ip_bloqueado():
    ip = request.remote_addr
    if ip in BLOQUEIOS:
        if BLOQUEIOS[ip] > datetime.now():
            return True
        else:
            del BLOQUEIOS[ip]
    return False


def bloquear_ip(ip, minutos=60):
    from datetime import timedelta
    BLOQUEIOS[ip] = datetime.now() + timedelta(minutes=minutos)
    auditoria('BLOQUEIO_IP', f'{ip} por {minutos}min')


def desbloquear_ip(ip):
    BLOQUEIOS.pop(ip, None)
    auditoria('DESBLOQUEIO_IP', ip)


def obter_ips_bloqueados():
    now = datetime.now()
    return {ip: exp.isoformat() for ip, exp in BLOQUEIOS.items() if exp > now}
