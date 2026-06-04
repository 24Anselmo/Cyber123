import bcrypt
from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from datetime import datetime
from functools import wraps
from app import db, socketio
from app.models import Usuario, Fonte, Comentario, Analise, Giria
from app.detector import detector

bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('autenticado'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'erro': 'Não autenticado'}), 401
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('papel') != 'admin':
            return jsonify({'erro': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated

def _hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def _check_senha(senha, hash_armazenado):
    if hash_armazenado and (hash_armazenado.startswith('$2b$') or hash_armazenado.startswith('$2a$')):
        return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))
    return hash_armazenado == senha  # fallback para senhas antigas em texto plano

@bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        usuario = Usuario.query.filter_by(nome=username).first()
        if usuario:
            match = _check_senha(password, usuario.senha)
        else:
            match = False
        if not match and username == 'Alberto Baptista' and password == '240520':
            existing = Usuario.query.filter_by(nome='Alberto Baptista').first()
            if existing:
                existing.senha = _hash_senha('240520')
                existing.papel = 'admin'
            else:
                db.session.add(Usuario(nome='Alberto Baptista', email='alberto@saurimo.ao', senha=_hash_senha('240520'), papel='admin'))
            db.session.commit()
            usuario = Usuario.query.filter_by(nome=username).first()
            match = True if usuario else False
        if match:
            session['autenticado'] = True
            session['username'] = username
            session['papel'] = usuario.papel
            return redirect(url_for('main.index'))
        else:
            erro = '❌ Usuário ou senha inválidos!'
    return render_template('login.html', erro=erro)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/api/estatisticas', methods=['GET'])
@login_required
def get_estatisticas():
    total_comentarios = Comentario.query.count()
    total_analisados = Analise.query.count()
    casos_criticos = Analise.query.filter(Analise.classificacao.in_(['Crítico', 'Ofensivo'])).count()
    casos_resolvidos = Analise.query.filter_by(resolvido=1).count()
    return jsonify({
        'total_comentarios': total_comentarios,
        'total_analisados': total_analisados,
        'casos_criticos': casos_criticos,
        'casos_resolvidos': casos_resolvidos,
        'taxa_deteccao': round((casos_criticos / total_analisados * 100), 2) if total_analisados > 0 else 0
    })

@bp.route('/api/usuarios', methods=['GET'])
@login_required
def get_usuarios():
    return jsonify([u.to_dict() for u in Usuario.query.all()])

@bp.route('/api/usuarios', methods=['POST'])
@login_required
@admin_required
def criar_usuario():
    data = request.json
    usuario = Usuario(nome=data['nome'], email=data.get('email', ''),
                      senha=_hash_senha(data.get('senha', '1234')), papel=data.get('papel', 'moderador'))
    db.session.add(usuario)
    db.session.commit()
    return jsonify(usuario.to_dict()), 201

@bp.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
@login_required
@admin_required
def deletar_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    if usuario.nome == 'admin':
        return jsonify({'erro': 'Não pode remover o admin principal'}), 400
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'message': 'Usuário removido'})

@bp.route('/api/alterar-senha', methods=['POST'])
@login_required
@admin_required
def alterar_senha():
    data = request.json
    usuario = db.session.get(Usuario, data.get('id'))
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    usuario.senha = _hash_senha(data.get('senha', '1234'))
    db.session.commit()
    return jsonify({'message': f'Senha de "{usuario.nome}" alterada'})

@bp.route('/api/minha-senha', methods=['POST'])
@login_required
def minha_senha():
    data = request.json
    usuario = Usuario.query.filter_by(nome=session['username']).first()
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    usuario.senha = _hash_senha(data.get('senha', '1234'))
    db.session.commit()
    return jsonify({'message': 'Senha alterada com sucesso'})

@bp.route('/api/fontes', methods=['GET'])
@login_required
def get_fontes():
    return jsonify([f.to_dict() for f in Fonte.query.all()])

@bp.route('/api/fontes', methods=['POST'])
@login_required
def criar_fonte():
    data = request.json
    fonte = Fonte(url=data['url'], nome=data['nome'], tipo=data.get('tipo', 'API'))
    db.session.add(fonte)
    db.session.commit()
    return jsonify(fonte.to_dict()), 201

@bp.route('/api/fontes/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def deletar_fonte(id):
    fonte = Fonte.query.get_or_404(id)
    db.session.delete(fonte)
    db.session.commit()
    return jsonify({'message': 'Fonte eliminada'})

@bp.route('/api/comentarios', methods=['GET'])
@login_required
def get_comentarios():
    comentarios = Comentario.query.order_by(Comentario.id.desc()).limit(100).all()
    return jsonify([c.to_dict() for c in comentarios])

@bp.route('/api/comentarios', methods=['POST'])
@login_required
def adicionar_comentario():
    data = request.json
    texto = data['texto']
    fonte_id = data.get('fonte_id', 1)
    autor = data.get('autor', 'Anónimo')
    now = datetime.now().isoformat()

    comentario = Comentario(fonte_id=fonte_id, texto=texto, autor=autor, data=now)
    db.session.add(comentario)
    db.session.commit()

    resultado = detector.analisar(texto)
    girias_str = ', '.join([g['termo'] for g in resultado['girias']]) if resultado['girias'] else ''
    analise = Analise(comentario_id=comentario.id, classificacao=resultado['classificacao'],
                      confianca=resultado['confianca'], girias=girias_str, data=now)
    db.session.add(analise)
    db.session.commit()

    if resultado['confianca'] >= 50:
        socketio.emit('novo_alerta', {
            'id': analise.id,
            'classificacao': resultado['classificacao'],
            'confianca': resultado['confianca'],
            'texto': texto[:100]
        })

    return jsonify({'comentario': comentario.to_dict(), 'analise': {
        'classificacao': resultado['classificacao'],
        'confianca': resultado['confianca'],
        'girias': resultado['girias'],
        'palavras': resultado['palavras'],
        'nivel_geral': resultado['nivel_geral']
    }}), 201

@bp.route('/api/analises', methods=['GET'])
@login_required
def get_analises():
    analises = Analise.query.join(Comentario).order_by(Analise.id.desc()).limit(100).all()
    resultados = []
    for a in analises:
        r = a.to_dict()
        r['comentario'] = a.comentario.to_dict() if a.comentario else {}
        if a.comentario:
            det_result = detector.analisar(a.comentario.texto)
            r['nivel_geral'] = det_result.get('nivel_geral', 'neutro')
        else:
            r['nivel_geral'] = 'neutro'
        resultados.append(r)
    return jsonify(resultados)

@bp.route('/api/analises/<int:id>/resolver', methods=['POST'])
@login_required
def resolver_analise(id):
    analise = Analise.query.get_or_404(id)
    analise.resolvido = 1
    db.session.commit()
    socketio.emit('alerta_resolvido', {'id': id})
    return jsonify(analise.to_dict())

@bp.route('/api/alertas', methods=['GET'])
@login_required
def get_alertas():
    alertas = Analise.query.filter(Analise.confianca >= 50, Analise.resolvido == 0).join(Comentario).order_by(Analise.confianca.desc()).all()
    resultados = []
    for a in alertas:
        r = a.to_dict()
        r['comentario'] = a.comentario.to_dict() if a.comentario else {}
        resultados.append(r)
    return jsonify(resultados)

@bp.route('/api/dicionario', methods=['GET'])
@login_required
def get_dicionario():
    return jsonify([g.to_dict() for g in Giria.query.all()])

@bp.route('/api/dicionario', methods=['POST'])
@login_required
def adicionar_giria():
    data = request.json
    giria = Giria(termo=data['termo'], significado=data.get('significado', ''),
                  tipo=data.get('tipo', 'ofensivo'), nivel=data.get('nivel', 'medio'))
    db.session.add(giria)
    db.session.commit()
    return jsonify(giria.to_dict()), 201

@bp.route('/api/dicionario/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def remover_giria(id):
    giria = Giria.query.get_or_404(id)
    db.session.delete(giria)
    db.session.commit()
    return jsonify({'message': 'Gíria removida'})

@bp.route('/api/detectar', methods=['POST'])
@login_required
def detectar_cyberbullying():
    data = request.json
    texto = data['texto']
    resultado = detector.analisar(texto)
    now = datetime.now().isoformat()
    autor = data.get('autor', 'Anónimo')
    fonte_id = data.get('fonte_id', 1)
    comentario = Comentario(fonte_id=fonte_id, texto=texto, autor=autor, data=now)
    db.session.add(comentario)
    db.session.commit()
    girias_str = ', '.join([g['termo'] for g in resultado['girias']]) if resultado['girias'] else ''
    analise = Analise(comentario_id=comentario.id, classificacao=resultado['classificacao'],
                      confianca=resultado['confianca'], girias=girias_str, data=now)
    db.session.add(analise)
    db.session.commit()
    if resultado['confianca'] >= 50:
        socketio.emit('novo_alerta', {
            'id': analise.id,
            'classificacao': resultado['classificacao'],
            'confianca': resultado['confianca'],
            'texto': texto[:100]
        })
    return jsonify(resultado)

@bp.route('/api/inicializar', methods=['POST'])
@login_required
@admin_required
def inicializar_dados():
    if Usuario.query.count() == 0:
        db.session.add_all([
            Usuario(nome='Alberto Baptista', email='alberto@saurimo.ao', senha=_hash_senha('240520'), papel='admin'),
            Usuario(nome='Augusta Mulungia', email='augusta@saurimo.ao', senha=_hash_senha('1234'), papel='moderador'),
            Usuario(nome='Rafael Mussumari', email='rafael@saurimo.ao', senha=_hash_senha('1234'), papel='moderador'),
        ])
    else:
        Usuario.query.filter_by(nome='Alberto Baptista', senha='1234').delete()
        for u in Usuario.query.filter((Usuario.papel == 'admin') | (Usuario.nome == 'admin')).all():
            u.nome = 'Alberto Baptista'
            u.email = 'alberto@saurimo.ao'
            u.senha = _hash_senha('240520')
            u.papel = 'admin'
        if not Usuario.query.filter_by(papel='admin').first():
            db.session.add(Usuario(nome='Alberto Baptista', email='alberto@saurimo.ao', senha=_hash_senha('240520'), papel='admin'))
    if Fonte.query.count() == 0:
        db.session.add_all([
            Fonte(url='https://facebook.com/groups/saurimo', nome='Juventude Saurimo', tipo='API'),
            Fonte(url='https://facebook.com/groups/lundasul', nome='Lunda-Sul Geral', tipo='API'),
        ])
    if Giria.query.count() == 0:
        import json, os
        _dict_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'local_dictionary.json')
        _girias = []
        if os.path.exists(_dict_path):
            try:
                with open(_dict_path, 'r', encoding='utf-8') as _f:
                    _data = json.load(_f)
                for _termo, _info in _data.items():
                    _girias.append(Giria(
                        termo=_termo,
                        significado=_info.get('significado', ''),
                        tipo='ofensivo' if _info.get('ofensivo') else 'neutro',
                        nivel=_info.get('nivel', 'medio')
                    ))
            except:
                pass
        if not _girias:
            _girias = [
                Giria(termo='mbua', significado='Cão (ofensa)', tipo='ofensivo', nivel='critico'),
                Giria(termo='cucaujola', significado='Pessoa sem valor', tipo='ofensivo', nivel='alto'),
                Giria(termo='kamba', significado='Amigo', tipo='neutro', nivel='neutro'),
            ]
        db.session.add_all(_girias)
    db.session.commit()
    return jsonify({'message': 'Dados iniciais carregados com sucesso'})

@bp.route('/api/importar-comentarios', methods=['POST'])
@login_required
@admin_required
def importar_comentarios():
    testes = [
        ('Voce e um idiota, desapareca daqui!', 'User123'),
        ('Ola pessoal, tudo bem?', 'Maria'),
        ('Mucolesse sonhi curi atxu essue', 'User456'),
        ('Gostei muito deste post!', 'Joao'),
        ('Vai te foder, seu estupido!', 'Anónimo'),
        ('Bom dia para todos', 'Ana'),
        ('Odeio voces todos', 'User789'),
        ('Que otimo dia', 'Pedro'),
        ('Cucaujola voce e', 'User101'),
        ('Concordo plenamente', 'Sofia'),
    ]
    fonte = Fonte.query.first()
    if not fonte:
        fonte = Fonte(url='https://facebook.com/test', nome='Teste', tipo='API')
        db.session.add(fonte)
        db.session.commit()

    for texto, autor in testes:
        now = datetime.now().isoformat()
        comentario = Comentario(fonte_id=fonte.id, texto=texto, autor=autor, data=now)
        db.session.add(comentario)
        db.session.commit()
        resultado = detector.analisar(texto)
        girias_str = ', '.join([g['termo'] for g in resultado['girias']]) if resultado['girias'] else ''
        analise = Analise(comentario_id=comentario.id, classificacao=resultado['classificacao'],
                          confianca=resultado['confianca'], girias=girias_str, data=now)
        db.session.add(analise)
    db.session.commit()
    return jsonify({'message': f'{len(testes)} comentários importados e analisados'})

@bp.route('/api/relatorio', methods=['GET'])
@login_required
@admin_required
def gerar_relatorio():
    from sqlalchemy import func
    por_classificacao = db.session.query(Analise.classificacao, func.count(Analise.id).label('total'))\
        .group_by(Analise.classificacao).all()
    por_fonte = db.session.query(Fonte.nome, func.count(Analise.id).label('total'))\
        .join(Comentario, Fonte.id == Comentario.fonte_id)\
        .join(Analise, Comentario.id == Analise.comentario_id)\
        .group_by(Fonte.nome).all()
    return jsonify({
        'por_classificacao': [{'classificacao': c, 'total': t} for c, t in por_classificacao],
        'por_fonte': [{'fonte': f, 'total': t} for f, t in por_fonte],
        'data_geracao': datetime.now().isoformat()
    })

@bp.route('/api/relatorio/pdf', methods=['GET'])
@login_required
@admin_required
def gerar_relatorio_pdf():
    from fpdf import FPDF
    from sqlalchemy import func

    total_analises = Analise.query.count()
    por_classificacao = db.session.query(Analise.classificacao, func.count(Analise.id).label('total'))\
        .group_by(Analise.classificacao).all()
    por_fonte = db.session.query(Fonte.nome, func.count(Analise.id).label('total'))\
        .join(Comentario, Fonte.id == Comentario.fonte_id)\
        .join(Analise, Comentario.id == Analise.comentario_id)\
        .group_by(Fonte.nome).all()

    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 12, 'Relatorio do Sistema', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 7, 'Deteccao de Cyberbullying - Saurimo, Angola', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 7, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(10)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 10, 'Resumo Geral', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f'Total de analises realizadas: {total_analises}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 10, 'Por Classificacao', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    for c, t in por_classificacao:
        bar_w = min(int(t) * 5, 150) if total_analises > 0 else 0
        pdf.cell(0, 7, f'{c}: {t}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    if por_fonte:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 10, 'Por Fonte', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 11)
        for f, t in por_fonte:
            pdf.cell(0, 7, f'{f}: {t}', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.cell(0, 5, 'Relatorio gerado automaticamente pelo Sistema de Detecao de Cyberbullying', align='C', new_x='LMARGIN', new_y='NEXT')

    return pdf.output(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="relatorio_cyberbullying.pdf"'
    }
