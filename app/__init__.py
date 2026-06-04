import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

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
    
    with flask_app.app_context():
        from app.routes import bp
        flask_app.register_blueprint(bp)
    
    return flask_app
