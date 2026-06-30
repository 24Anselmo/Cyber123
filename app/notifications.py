import os
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import requests
    _requests = True
except ImportError:
    _requests = False


class EmailNotifier:
    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_pass = os.environ.get('SMTP_PASS', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_user)
        self.to_emails = os.environ.get('ALERT_EMAILS', '').split(',')

    @property
    def disponivel(self):
        return bool(self.smtp_user and self.smtp_pass and self.to_emails and self.to_emails != [''])

    def enviar(self, assunto, corpo_html):
        if not self.disponivel:
            logger.warning('Email notifier não configurado')
            return False
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            parte_texto = MIMEText(corpo_html.replace('<br>', '\n').replace('<[^>]+>', ''), 'plain', 'utf-8')
            parte_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(parte_texto)
            msg.attach(parte_html)
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.from_email, self.to_emails, msg.as_string())
            logger.info(f'Email enviado: {assunto}')
            return True
        except Exception as e:
            logger.error(f'Erro ao enviar email: {e}')
            return False

    def alerta_critico(self, texto, classificacao, confianca):
        assunto = f'🚨 Alerta Cyberbullying - {classificacao} ({confianca}%)'
        corpo = f"""
        <h2>🚨 Alerta de Cyberbullying</h2>
        <p><strong>Classificação:</strong> {classificacao}</p>
        <p><strong>Confiança:</strong> {confianca}%</p>
        <p><strong>Texto:</strong> {texto}</p>
        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        <hr><p><small>Sistema de Deteção de Cyberbullying - Saurimo, Angola</small></p>
        """
        return self.enviar(assunto, corpo)

    def relatorio_diario(self, estatisticas):
        data = datetime.now().strftime('%d/%m/%Y')
        assunto = f'📊 Relatório Diário Cyberbullying - {data}'
        corpo = f"""
        <h2>📊 Relatório Diário - {data}</h2>
        <p><strong>Total de análises:</strong> {estatisticas.get('total_analises', 0)}</p>
        <p><strong>Casos críticos:</strong> {estatisticas.get('casos_criticos', 0)}</p>
        <p><strong>Alertas ativos:</strong> {estatisticas.get('alertas_ativos', 0)}</p>
        <hr><p><small>Gerado automaticamente pelo Sistema de Deteção</small></p>
        """
        return self.enviar(assunto, corpo)


class TelegramNotifier:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    @property
    def disponivel(self):
        return bool(self.token and self.chat_id)

    def enviar(self, mensagem):
        if not self.disponivel or not _requests:
            return False
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        try:
            resp = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': mensagem,
                'parse_mode': 'HTML',
            }, timeout=15)
            return resp.ok
        except Exception as e:
            logger.error(f'Telegram error: {e}')
            return False

    def alerta_critico(self, texto, classificacao, confianca):
        msg = (f'🚨 <b>Alerta Cyberbullying</b>\n'
               f'Classificação: {classificacao}\n'
               f'Confiança: {confianca}%\n'
               f'Texto: {texto[:200]}')
        return self.enviar(msg)


class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')

    @property
    def disponivel(self):
        return bool(self.webhook_url) and _requests

    def enviar(self, mensagem):
        if not self.disponivel:
            return False
        try:
            resp = requests.post(self.webhook_url, json={
                'content': mensagem,
                'username': 'Cyberbullying Detector',
            }, timeout=15)
            return resp.ok
        except Exception as e:
            logger.error(f'Discord error: {e}')
            return False

    def alerta_critico(self, texto, classificacao, confianca):
        msg = (f'🚨 **Alerta Cyberbullying**\n'
               f'Classificação: {classificacao}\n'
               f'Confiança: {confianca}%\n'
               f'Texto: {texto[:200]}')
        return self.enviar(msg)
