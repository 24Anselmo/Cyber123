import os
import sys
import bcrypt
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()

def create_app(db_path=None):
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = 'cyberbullying-detector-secret-key-2026'

    if db_path is None:
        db_path = os.environ.get('CYBERBULLYING_DB_PATH')
    if db_path is None:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_dir = os.path.join(base_dir, 'data')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'cyberbullying.db')
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'timeout': 10},
        'pool_pre_ping': True,
    }
    
    CORS(flask_app)
    socketio.init_app(flask_app, cors_allowed_origins="*")
    db.init_app(flask_app)
    
    with flask_app.app_context():
        import app.models
        db.create_all()
        # migration: add senha column if missing
        try:
            from sqlalchemy import inspect
            if 'senha' not in [c['name'] for c in inspect(db.engine).get_columns('usuarios')]:
                from sqlalchemy import text
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN senha TEXT DEFAULT '1234'"))
                db.session.commit()
        except:
            pass
        # migration: hash existing plaintext passwords
        try:
            from sqlalchemy import text
            rows = db.session.execute(text("SELECT id, senha FROM usuarios")).fetchall()
            for row in rows:
                if row.senha and not row.senha.startswith('$2'):
                    hashed = bcrypt.hashpw(row.senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    db.session.execute(text("UPDATE usuarios SET senha=:s WHERE id=:i"), {'s': hashed, 'i': row.id})
            db.session.commit()
        except:
            pass
    
    with flask_app.app_context():
        from app.routes import bp
        flask_app.register_blueprint(bp)
    
    with flask_app.app_context():
        from app import socket_events
    
    return flask_app
