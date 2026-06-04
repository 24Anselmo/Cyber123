from app import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text)
    email = db.Column(db.Text)
    senha = db.Column(db.Text, default='1234')
    papel = db.Column(db.Text)
    avatar = db.Column(db.Text)

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome, 'email': self.email, 'papel': self.papel}

class Fonte(db.Model):
    __tablename__ = 'fontes'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text)
    nome = db.Column(db.Text)
    tipo = db.Column(db.Text, default='API')
    ativo = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {'id': self.id, 'url': self.url, 'nome': self.nome, 'tipo': self.tipo, 'ativo': self.ativo}

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    fonte_id = db.Column(db.Integer, db.ForeignKey('fontes.id'))
    texto = db.Column(db.Text)
    autor = db.Column(db.Text)
    data = db.Column(db.Text)

    fonte = db.relationship('Fonte', backref='comentarios', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'fonte_id': self.fonte_id, 'texto': self.texto, 'autor': self.autor, 'data': self.data}

class Analise(db.Model):
    __tablename__ = 'analises'
    id = db.Column(db.Integer, primary_key=True)
    comentario_id = db.Column(db.Integer, db.ForeignKey('comentarios.id'))
    classificacao = db.Column(db.Text)
    confianca = db.Column(db.Float)
    girias = db.Column(db.Text)
    resolvido = db.Column(db.Integer, default=0)
    data = db.Column(db.Text)

    comentario = db.relationship('Comentario', backref='analises', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'comentario_id': self.comentario_id, 'classificacao': self.classificacao,
                'confianca': self.confianca, 'girias': self.girias, 'resolvido': self.resolvido, 'data': self.data}

class Giria(db.Model):
    __tablename__ = 'girias_db'
    id = db.Column(db.Integer, primary_key=True)
    termo = db.Column(db.Text)
    significado = db.Column(db.Text)
    tipo = db.Column(db.Text)
    nivel = db.Column(db.Text, default='medio')

    def to_dict(self):
        return {'id': self.id, 'termo': self.termo, 'significado': self.significado,
                'tipo': self.tipo, 'nivel': self.nivel}
