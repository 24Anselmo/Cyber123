from flask import request
from flask_socketio import emit
from app import socketio


@socketio.on('connect')
def connect():
    print(f'[WebSocket] Cliente conectado: {request.sid}')


@socketio.on('disconnect')
def disconnect():
    print(f'[WebSocket] Cliente desconectado: {request.sid}')


@socketio.on('novo_alerta')
def handle_novo_alerta(data):
    print(f'[WebSocket] Novo alerta emitido: {data.get("id")}')
    emit('novo_alerta', data, broadcast=True)


@socketio.on('alerta_resolvido')
def handle_alerta_resolvido(data):
    print(f'[WebSocket] Alerta resolvido: {data.get("id")}')
    emit('alerta_resolvido', data, broadcast=True)
