import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font
import sqlite3
import json
import os
import sys
import csv
import threading
import webbrowser
import traceback
from datetime import datetime

def _project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = _project_root()
DB_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DB_DIR, 'cyberbullying.db')
DICT_PATH = os.path.join(DB_DIR, 'local_dictionary.json')
if getattr(sys, 'frozen', False):
    LOGO_PATH = os.path.join(sys._MEIPASS, 'logo.png')
else:
    LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')

os.environ['CYBERBULLYING_DB_PATH'] = DB_PATH

def _debug_log(msg):
    try:
        log_path = os.path.join(DB_DIR, 'debug.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} | {msg}\n')
    except:
        pass

def _setup_db(db_path):
    """Create tables and migrate users. Call before login dialog."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _debug_log(f'_setup_db START path={db_path}')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nome TEXT, email TEXT, senha TEXT DEFAULT '1234', papel TEXT, avatar TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS fontes (id INTEGER PRIMARY KEY, url TEXT, nome TEXT, tipo TEXT DEFAULT 'API', ativo INTEGER DEFAULT 1)")
    c.execute("CREATE TABLE IF NOT EXISTS comentarios (id INTEGER PRIMARY KEY, fonte_id INTEGER, texto TEXT, autor TEXT, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS analises (id INTEGER PRIMARY KEY, comentario_id INTEGER, classificacao TEXT, confianca REAL, girias TEXT, resolvido INTEGER DEFAULT 0, data TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS girias_db (id INTEGER PRIMARY KEY, termo TEXT, significado TEXT, tipo TEXT, nivel TEXT DEFAULT 'medio')")
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(usuarios)").fetchall()]
        if 'senha' not in cols:
            c.execute("ALTER TABLE usuarios ADD COLUMN senha TEXT DEFAULT '1234'")
    except:
        pass
    try:
        c.execute("SELECT nivel FROM girias_db LIMIT 1")
    except:
        c.execute("ALTER TABLE girias_db ADD COLUMN nivel TEXT DEFAULT 'medio'")
    total = c.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    _debug_log(f'_setup_db total_usuarios={total}')
    for r in c.execute("SELECT id, nome, senha, papel FROM usuarios").fetchall():
        _debug_log(f'  user id={r[0]} nome={r[1]} senha={r[2]} papel={r[3]}')
    if total == 0:
        c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Alberto Baptista', 'alberto@saurimo.ao', '240520', 'admin')")
        c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Augusta Mulungia', 'augusta@saurimo.ao', '1234', 'moderador')")
        c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Rafael Mussumari', 'rafael@saurimo.ao', '1234', 'moderador')")
        _debug_log('_setup_db seeded initial users')
    else:
        c.execute("DELETE FROM usuarios WHERE nome='Alberto Baptista' AND senha='1234'")
        c.execute("UPDATE usuarios SET nome='Alberto Baptista', email='alberto@saurimo.ao', senha='240520', papel='admin' WHERE papel='admin' OR nome='admin'")
        if c.execute("SELECT COUNT(*) FROM usuarios WHERE papel='admin'").fetchone()[0] == 0:
            c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Alberto Baptista', 'alberto@saurimo.ao', '240520', 'admin')")
    c.execute("UPDATE usuarios SET nome='Alberto Baptista', email='alberto@saurimo.ao', senha='240520', papel='admin' WHERE nome='Alberto Baptista'")
    admin_ok = c.execute("SELECT id FROM usuarios WHERE nome='Alberto Baptista' AND senha='240520' AND papel='admin'").fetchone()
    if not admin_ok:
        c.execute("DELETE FROM usuarios WHERE nome='Alberto Baptista' AND papel='admin'")
        c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Alberto Baptista', 'alberto@saurimo.ao', '240520', 'admin')")
        _debug_log('_setup_db nuclear insert admin')
    conn.commit()
    for r in c.execute("SELECT id, nome, senha, papel FROM usuarios WHERE nome='Alberto Baptista'").fetchall():
        _debug_log(f'_setup_db FINAL user id={r[0]} nome={r[1]} senha={r[2]} papel={r[3]}')
    conn.close()
    _debug_log('_setup_db END')

if not getattr(sys, 'frozen', False):
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
from app.detector import detector as _detector

CORES = {
    'bg': '#f0f2f5',
    'card': '#ffffff',
    'primary': '#2563eb',
    'primary_light': '#3b82f6',
    'danger': '#dc2626',
    'danger_light': '#fee2e2',
    'warning': '#d97706',
    'warning_light': '#fef3c7',
    'success': '#16a34a',
    'success_light': '#dcfce7',
    'info': '#0891b2',
    'info_light': '#cffafe',
    'text': '#1f2937',
    'text_sec': '#6b7280',
    'border': '#e5e7eb',
}

class CyberbullyingApp:
    def __init__(self, root, papel='moderador', current_user_id=None, current_user_nome=None):
        self.root = root
        self.autenticado = True
        self.papel = papel
        self.current_user_id = current_user_id
        self.current_user_nome = current_user_nome
        self.detector = _detector
        self._init_db()
        self._build_gui()
        self._start_web_server()
        self._diagnose_db()
        self._auto_refresh_alertas()

    def _init_db(self):
        _setup_db(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if c.execute('SELECT COUNT(*) FROM fontes').fetchone()[0] == 0:
            c.execute("INSERT INTO fontes (url, nome) VALUES ('https://facebook.com/groups/saurimo', 'Juventude Saurimo')")
            c.execute("INSERT INTO fontes (url, nome) VALUES ('https://facebook.com/groups/lundasul', 'Lunda-Sul Geral')")
        if c.execute('SELECT COUNT(*) FROM girias_db').fetchone()[0] == 0:
            girias = [
                ('mucolesse sonhi curi atxu essue', 'Vai embora daqui (rude)', 'ofensivo', 'critico'),
                ('kamba dia bunda', 'Expressão de desprezo grave', 'ofensivo', 'critico'),
                ('mbua', 'Cão (comparação ofensiva grave)', 'ofensivo', 'critico'),
                ('mulemba', 'Ofensa racial relacionada a cor', 'ofensivo', 'critico'),
                ('cucaujola', 'Pessoa sem valor, inútil', 'ofensivo', 'alto'),
                ('cutxuala-phula', 'Expressão depreciativa grave', 'ofensivo', 'alto'),
                ('mukua', 'Pessoa ignorante', 'ofensivo', 'alto'),
                ('quinda', 'Ofensa sobre cabelo/aparência', 'ofensivo', 'alto'),
                ('ngulu', 'Porco (comparação ofensiva)', 'ofensivo', 'alto'),
                ('sukuata', 'Calar-se (forma rude)', 'ofensivo', 'alto'),
                ('tunda', 'Sair daqui (expulsão)', 'ofensivo', 'alto'),
                ('mbuji', 'Bode (comparação pejorativa)', 'ofensivo', 'alto'),
                ('kizua', 'Mentiroso, enganador', 'ofensivo', 'medio'),
                ('canhota', 'Pessoa de má índole', 'ofensivo', 'medio'),
                ('mujimbista', 'Pessoa que espalha boatos', 'ofensivo', 'medio'),
                ('kamba di kanimbo', 'Amigo traidor', 'ofensivo', 'medio'),
                ('xiyowa', 'Pessoa ingénua, tola', 'ofensivo', 'medio'),
                ('buzi', 'Cabra (comparação ofensiva)', 'ofensivo', 'medio'),
                ('kilapanga', 'Pessoa que gosta de confusão', 'ofensivo', 'medio'),
                ('quibuca', 'Pessoa que não cumpre promessas', 'ofensivo', 'baixo'),
                ('kibukula', 'Pessoa que fala demais', 'ofensivo', 'baixo'),
                ('txiwela', 'Pessoa fraca, medrosa', 'ofensivo', 'baixo'),
                ('cangundo', 'Pessoa desajeitada', 'ofensivo', 'baixo'),
                ('mussua', 'Pessoa suja, mal cuidada', 'ofensivo', 'baixo'),
                ('muxiluanda', 'Regionalismo pejorativo', 'ofensivo', 'baixo'),
                ('kisungu', 'Branco/estrangeiro (p. pejorativo)', 'ofensivo', 'baixo'),
                ('kamba', 'Amigo, camarada', 'neutro', 'neutro'),
                ('mbamba', 'Amigo verdadeiro', 'neutro', 'neutro'),
                ('sota', 'Amigo próximo, parceiro', 'neutro', 'neutro'),
                ('kota', 'Mais velho, sênior', 'neutro', 'neutro'),
                ('mutu', 'Pessoa, indivíduo', 'neutro', 'neutro'),
                ('kwanza', 'Dinheiro, moeda', 'neutro', 'neutro'),
                ('tchilar', 'Relaxar, descontrair', 'neutro', 'neutro'),
                ('bumbar', 'Trabalhar', 'neutro', 'neutro'),
                ('cumbar', 'Acompanhar', 'neutro', 'neutro'),
                ('bassula', 'Conversar, bater papo', 'neutro', 'neutro'),
                ('majimbo', 'Problema, confusão', 'neutro', 'neutro'),
                ('muxima', 'Coração, pessoa querida', 'neutro', 'neutro'),
            ]
            for g in girias:
                c.execute("INSERT INTO girias_db (termo, significado, tipo, nivel) VALUES (?, ?, ?, ?)", g)
        conn.commit()
        conn.close()

    def _build_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        self.tab_analise = ttk.Frame(self.notebook)
        self.tab_alertas = ttk.Frame(self.notebook)
        self.tab_dicionario = ttk.Frame(self.notebook)
        self.tab_fontes = ttk.Frame(self.notebook)
        self.tab_relatorio = ttk.Frame(self.notebook)
        self.tab_usuarios = ttk.Frame(self.notebook)
        papel = self.papel
        self.notebook.add(self.tab_analise, text='🔍 Análise')
        self.notebook.add(self.tab_alertas, text='🚨 Alertas')
        self.notebook.add(self.tab_dicionario, text='📚 Dicionário')
        self.notebook.add(self.tab_fontes, text='📰 Fontes')
        if papel == 'admin':
            self.notebook.add(self.tab_relatorio, text='📄 Relatório')
            self.notebook.add(self.tab_usuarios, text='👥 Usuários')

        status_bar = tk.Frame(self.root, bg=CORES['primary'], height=28)
        status_bar.pack(fill='x', side='bottom')
        self.status_web = tk.Label(status_bar, text="🌐 Web: iniciando...",
                                   bg=CORES['primary'], fg='white', font=('Segoe UI', 9), cursor='hand2')
        self.status_web.pack(side='left', padx=10)
        self.lbl_db_status = tk.Label(status_bar, text=f"📁 {DB_PATH}",
                                      bg=CORES['primary'], fg='white', font=('Segoe UI', 9))
        self.lbl_db_status.pack(side='right', padx=10)
        btn_logout = tk.Label(status_bar, text="🚪 Sair", bg=CORES['primary'], fg='white',
                              font=('Segoe UI', 9, 'bold'), cursor='hand2')
        btn_logout.pack(side='right', padx=(0, 10))
        btn_logout.bind('<Button-1>', lambda e: self._logout())
        btn_perfil = tk.Label(status_bar, text="👤 Alterar Senha", bg=CORES['primary'], fg='white',
                              font=('Segoe UI', 9), cursor='hand2')
        btn_perfil.pack(side='right', padx=(0, 5))
        btn_perfil.bind('<Button-1>', lambda e: self._alterar_minha_senha())

        self._build_analise()
        self._build_alertas()
        self._build_dicionario()
        self._build_fontes()
        if papel == 'admin':
            self._build_relatorio()
            self._build_usuarios()

    def _build_analise(self):
        f = ttk.LabelFrame(self.tab_analise, text="📝  Análise de Texto em Tempo Real", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        cards_frame = tk.Frame(f, bg=CORES['card'])
        cards_frame.pack(fill='x', pady=(0, 15))

        conn = self._get_conn()
        c = conn.cursor()
        total = c.execute('SELECT COUNT(*) FROM analises').fetchone()[0]
        crit = c.execute("SELECT COUNT(*) FROM analises WHERE confianca >= 95").fetchone()[0]
        resol = c.execute("SELECT COUNT(*) FROM analises WHERE resolvido = 1").fetchone()[0]
        conn.close()

        self._criar_card(cards_frame, 'Total Analisados', total, CORES['card'], CORES['primary'], '📊')
        self._criar_card(cards_frame, 'Casos Críticos', crit, CORES['card'], CORES['danger'], '⚠️')
        self._criar_card(cards_frame, 'Resolvidos', resol, CORES['card'], CORES['success'], '✅')
        self._criar_card(cards_frame, 'Gírias Locais', len(self.detector.dicionario_local), CORES['card'], CORES['info'], '📚')

        inp_frame = tk.LabelFrame(f, text="Texto para Análise", font=('Segoe UI', 9, 'bold'),
                                  bg=CORES['card'], fg=CORES['text'], padx=10, pady=8)
        inp_frame.pack(fill='x')

        self.txt_analise = scrolledtext.ScrolledText(inp_frame, height=4, font=('Segoe UI', 11),
                                                      relief='flat', borderwidth=1,
                                                      highlightbackground=CORES['border'],
                                                      highlightcolor=CORES['primary'],
                                                      highlightthickness=1)
        self.txt_analise.pack(fill='x', pady=5)
        self.txt_analise.bind('<Control-Return>', lambda e: self._analisar())

        btn_row = tk.Frame(inp_frame, bg=CORES['card'])
        btn_row.pack(fill='x', pady=(5, 0))

        ttk.Button(btn_row, text="🔍  Analisar", command=self._analisar).pack(side='left', padx=2)
        ttk.Button(btn_row, text="💾  Salvar & Analisar", command=self._adicionar_comentario).pack(side='left', padx=2)
        if self.papel == 'admin':
            ttk.Button(btn_row, text="📥  Importar Testes", command=self._importar_testes).pack(side='left', padx=2)
        ttk.Button(btn_row, text="🗑️  Limpar", command=lambda: self.txt_analise.delete('1.0', tk.END)).pack(side='left', padx=2)

        tk.Label(btn_row, text="💡 Ctrl+Enter para analisar rápido", font=('Segoe UI', 8),
                 bg=CORES['card'], fg=CORES['text_sec']).pack(side='right', padx=5)

        res_frame = tk.LabelFrame(f, text="Resultado da Análise", font=('Segoe UI', 9, 'bold'),
                                  bg=CORES['card'], fg=CORES['text'], padx=10, pady=8)
        res_frame.pack(fill='both', expand=True, pady=(10, 0))

        self.txt_resultado = scrolledtext.ScrolledText(res_frame, height=6, state='disabled',
                                                        font=('Consolas', 10), bg='#f8fafc',
                                                        relief='flat', borderwidth=1,
                                                        highlightbackground=CORES['border'],
                                                        highlightthickness=1)
        self.txt_resultado.pack(fill='both', expand=True)

        self.label_class = tk.Label(res_frame, text="", font=('Segoe UI', 14, 'bold'), bg=CORES['card'])
        self.label_class.pack(anchor='w', pady=(5, 0))

    def _build_alertas(self):
        f = ttk.LabelFrame(self.tab_alertas, text="🚨  Alertas (confiança ≥ 50%)", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        top = tk.Frame(f, bg=CORES['card'])
        top.pack(fill='x', pady=(0, 10))
        self.lbl_qtd_alertas = tk.Label(top, text="Carregando...", font=('Segoe UI', 11, 'bold'),
                                        bg=CORES['card'], fg=CORES['danger'])
        self.lbl_qtd_alertas.pack(side='left')

        columns = ('ID', 'Data', 'Autor', 'Texto', 'Confiança', 'Gírias')
        self.tree_alertas = ttk.Treeview(f, columns=columns, show='headings', height=14)
        for c in columns:
            self.tree_alertas.heading(c, text=c)
        self.tree_alertas.column('ID', width=40)
        self.tree_alertas.column('Data', width=140)
        self.tree_alertas.column('Autor', width=110)
        self.tree_alertas.column('Texto', width=420)
        self.tree_alertas.column('Confiança', width=90)
        self.tree_alertas.column('Gírias', width=180)

        scrollbar = ttk.Scrollbar(f, orient='vertical', command=self.tree_alertas.yview)
        self.tree_alertas.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_alertas.pack(fill='both', expand=True)

        btn_frame = tk.Frame(f, bg=CORES['card'])
        btn_frame.pack(fill='x', pady=(8, 0))
        ttk.Button(btn_frame, text="✅  Resolver", command=self._resolver).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📢  Reportar ao Facebook", command=self._reportar_facebook).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄  Atualizar", command=self._carregar_alertas).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📥  Importar Testes", command=self._importar_testes, style='Warning.TButton').pack(side='left', padx=2)

        self._carregar_alertas()

    def _start_web_server(self):
        try:
            if not getattr(sys, 'frozen', False):
                if BASE_DIR not in sys.path:
                    sys.path.insert(0, BASE_DIR)
            self._log(f'create_app(db_path={DB_PATH})')
            from app import create_app
            self.web_app = create_app(db_path=DB_PATH)
            self.web_thread = threading.Thread(target=self._run_web, daemon=True)
            self.web_thread.start()
            self.status_web.config(text="🌐 Web: localhost:5000")
            self.status_web.bind('<Button-1>', lambda e: webbrowser.open('http://localhost:5000'))
        except Exception as e:
            self.status_web.config(text="🌐 Web: erro")
            print(f"[Web] Erro ao iniciar servidor: {e}")

    def _run_web(self):
        self.web_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    def _on_closing(self):
        self.root.destroy()

    def _logout(self):
        self.root.destroy()
        main()

    def _abrir_web(self):
        webbrowser.open('http://localhost:5000')

    def _reportar_facebook(self):
        sel = self.tree_alertas.selection()
        if not sel:
            messagebox.showwarning('Atenção', 'Selecione um alerta para reportar!')
            return
        vals = self.tree_alertas.item(sel[0])['values']
        texto = vals[3]
        autor = vals[2]
        conf = vals[4]
        self.root.clipboard_clear()
        self.root.clipboard_append(f'🚨 Comentário ofensivo detetado (Cyberbullying Detector)\n\nAutor: {autor}\nTexto: {texto}\nConfiança: {conf}\n\nPor favor, revisem este conteúdo.')
        messagebox.showinfo('📢 Reportado ao Facebook',
            f'Informação copiada para a área de transferência!\n\nCole manualmente no grupo do Facebook.\n\nComentário: "{texto[:80]}"\nAutor: {autor}\nConfiança: {conf}')

    def _build_dicionario(self):
        f = ttk.LabelFrame(self.tab_dicionario, text="📚  Dicionário Local de Gírias - Saurimo", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        inp_frame = tk.Frame(f, bg=CORES['card'])
        inp_frame.pack(fill='x', pady=(0, 10))

        for label, attr, width in [("Gíria:", 'entry_giria', 18), ("Significado:", 'entry_significado', 22)]:
            sub = tk.Frame(inp_frame, bg=CORES['card'])
            sub.pack(side='left', padx=3)
            tk.Label(sub, text=label, font=('Segoe UI', 9), bg=CORES['card'], fg=CORES['text_sec']).pack(anchor='w')
            e = ttk.Entry(sub, width=width)
            e.pack()
            setattr(self, attr, e)

        sub = tk.Frame(inp_frame, bg=CORES['card'])
        sub.pack(side='left', padx=2)
        tk.Label(sub, text="Tipo:", font=('Segoe UI', 9), bg=CORES['card'], fg=CORES['text_sec']).pack(anchor='w')
        self.combo_tipo = ttk.Combobox(sub, values=['ofensivo', 'neutro'], width=8, state='readonly')
        self.combo_tipo.set('ofensivo')
        self.combo_tipo.pack()

        sub = tk.Frame(inp_frame, bg=CORES['card'])
        sub.pack(side='left', padx=2)
        tk.Label(sub, text="Nível:", font=('Segoe UI', 9), bg=CORES['card'], fg=CORES['text_sec']).pack(anchor='w')
        self.combo_nivel = ttk.Combobox(sub, values=['critico', 'alto', 'medio', 'baixo', 'neutro'], width=8, state='readonly')
        self.combo_nivel.set('medio')
        self.combo_nivel.pack()

        sub = tk.Frame(inp_frame, bg=CORES['card'])
        sub.pack(side='left', padx=5)
        tk.Label(sub, text="", bg=CORES['card']).pack()  # spacer
        ttk.Button(sub, text="➕  Adicionar", command=self._adicionar_giria, style='Success.TButton').pack(pady=(2, 0))

        columns = ('ID', 'Termo', 'Significado', 'Tipo', 'Nível')
        self.tree_girias = ttk.Treeview(f, columns=columns, show='headings', height=16)
        for c in columns:
            self.tree_girias.heading(c, text=c)
        self.tree_girias.column('ID', width=35)
        self.tree_girias.column('Termo', width=280)
        self.tree_girias.column('Significado', width=300)
        self.tree_girias.column('Tipo', width=80)
        self.tree_girias.column('Nível', width=80)

        scrollbar = ttk.Scrollbar(f, orient='vertical', command=self.tree_girias.yview)
        self.tree_girias.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_girias.pack(fill='both', expand=True)

        ttk.Button(f, text="🗑️  Remover Selecionada", command=self._remover_giria, style='Danger.TButton').pack(anchor='w', pady=(8, 0))

        self._carregar_girias()

    def _build_fontes(self):
        f = ttk.LabelFrame(self.tab_fontes, text="📰  Fontes Facebook Monitorizadas", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        inp_frame = tk.Frame(f, bg=CORES['card'])
        inp_frame.pack(fill='x', pady=(0, 10))

        for label, attr, width in [("URL da Página/Grupo:", 'entry_url', 40), ("Nome:", 'entry_nome_fonte', 30)]:
            sub = tk.Frame(inp_frame, bg=CORES['card'])
            sub.pack(side='left', padx=3)
            tk.Label(sub, text=label, font=('Segoe UI', 9), bg=CORES['card'], fg=CORES['text_sec']).pack(anchor='w')
            e = ttk.Entry(sub, width=width)
            e.pack()
            setattr(self, attr, e)

        sub = tk.Frame(inp_frame, bg=CORES['card'])
        sub.pack(side='left', padx=5)
        tk.Label(sub, text="", bg=CORES['card']).pack()
        ttk.Button(sub, text="➕  Adicionar Fonte", command=self._adicionar_fonte, style='Success.TButton').pack(pady=(2, 0))

        columns = ('ID', 'URL', 'Nome', 'Tipo')
        self.tree_fontes = ttk.Treeview(f, columns=columns, show='headings', height=16)
        for c in columns:
            self.tree_fontes.heading(c, text=c)
        self.tree_fontes.column('ID', width=35)
        self.tree_fontes.column('URL', width=450)
        self.tree_fontes.column('Nome', width=250)
        self.tree_fontes.column('Tipo', width=80)

        scrollbar = ttk.Scrollbar(f, orient='vertical', command=self.tree_fontes.yview)
        self.tree_fontes.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_fontes.pack(fill='both', expand=True)

        ttk.Button(f, text="🗑️  Remover Selecionada", command=self._remover_fonte, style='Danger.TButton').pack(anchor='w', pady=(8, 0))

        self._carregar_fontes()

    def _build_relatorio(self):
        f = ttk.LabelFrame(self.tab_relatorio, text="📊  Relatório e Estatísticas do Sistema", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(f, bg=CORES['card'])
        btn_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(btn_frame, text="📊  Gerar Estatísticas", command=self._gerar_stats).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📄  Exportar CSV", command=self._exportar_csv, style='Success.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📃  Exportar TXT", command=self._exportar_txt, style='Warning.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄  Atualizar Dados", command=self._gerar_stats).pack(side='left', padx=2)

        self.txt_relatorio = scrolledtext.ScrolledText(f, height=24, state='disabled',
                                                       font=('Consolas', 10), bg='#0f172a',
                                                       fg='#e2e8f0', relief='flat',
                                                       highlightbackground=CORES['border'],
                                                       highlightthickness=1)
        self.txt_relatorio.pack(fill='both', expand=True)

    def _log(self, msg):
        try:
            with open(os.path.join(DB_DIR, 'debug.log'), 'a', encoding='utf-8') as f:
                f.write(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}\n')
        except:
            pass

    def _criar_card(self, parent, titulo, valor, bg, fg, emoji=''):
        card = tk.Frame(parent, bg=CORES['card'], highlightbackground=CORES['border'],
                        highlightthickness=1, padx=12, pady=8)
        card.pack(side='left', padx=3, fill='x', expand=True)
        tk.Label(card, text=f'{emoji} {titulo}', font=('Segoe UI', 8),
                 bg=CORES['card'], fg=CORES['text_sec']).pack(anchor='w')
        tk.Label(card, text=str(valor), font=('Segoe UI', 18, 'bold'),
                 bg=CORES['card'], fg=fg).pack(anchor='w')

    def _auto_refresh_alertas(self):
        try:
            self._carregar_alertas()
        except Exception as e:
            self._log(f'auto_refresh ERRO: {e}')
            traceback.print_exc()
        self.root.after(5000, self._auto_refresh_alertas)

    def _build_usuarios(self):
        f = ttk.LabelFrame(self.tab_usuarios, text="👥  Equipa do Projeto", padding=15)
        f.pack(fill='both', expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(f, bg=CORES['card'])
        btn_frame.pack(fill='x', pady=(0, 10))
        ttk.Button(btn_frame, text="➕  Novo Usuário", command=self._criar_usuario,
                   style='Success.TButton').pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔑  Alterar Senha", command=self._alterar_senha).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🗑️  Remover", command=self._remover_usuario).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="🔄  Atualizar", command=self._carregar_usuarios).pack(side='left', padx=2)

        columns = ('ID', 'Nome', 'Email', 'Papel')
        self.tree_usuarios = ttk.Treeview(f, columns=columns, show='headings', height=14, selectmode='browse')
        for c in columns:
            self.tree_usuarios.heading(c, text=c)
        self.tree_usuarios.column('ID', width=50)
        self.tree_usuarios.column('Nome', width=250)
        self.tree_usuarios.column('Email', width=300)
        self.tree_usuarios.column('Papel', width=150)

        scrollbar = ttk.Scrollbar(f, orient='vertical', command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_usuarios.pack(fill='both', expand=True)

        info = tk.Frame(f, bg=CORES['info_light'], padx=15, pady=10)
        info.pack(fill='x', pady=(10, 0))
        tk.Label(info, text="ℹ️  Projeto desenvolvido para PP1 - Engenharia de Software I + Sistemas Operacionais",
                 font=('Segoe UI', 9), bg=CORES['info_light'], fg=CORES['info']).pack()

        self._carregar_usuarios()

    def _criar_usuario(self):
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Novo Usuário")
        dialogo.geometry("400x330")
        dialogo.configure(bg=CORES['card'])
        dialogo.transient(self.root)
        dialogo.grab_set()

        pad = tk.Frame(dialogo, bg=CORES['card'], padx=20, pady=15)
        pad.pack(fill='both', expand=True)

        tk.Label(pad, text="Criar Novo Usuário", font=('Segoe UI', 12, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(pady=(0, 15))

        tk.Label(pad, text="Nome:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_nome = ttk.Entry(pad, width=40, font=('Segoe UI', 10))
        entry_nome.pack(fill='x', pady=(2, 8))
        entry_nome.focus()

        tk.Label(pad, text="Email:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_email = ttk.Entry(pad, width=40, font=('Segoe UI', 10))
        entry_email.pack(fill='x', pady=(2, 8))

        tk.Label(pad, text="Senha:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_senha = ttk.Entry(pad, width=40, font=('Segoe UI', 10), show='•')
        entry_senha.pack(fill='x', pady=(2, 8))
        entry_senha.insert(0, '1234')

        tk.Label(pad, text="Papel:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        combo_papel = ttk.Combobox(pad, values=['moderador', 'admin'], state='readonly', font=('Segoe UI', 10))
        combo_papel.set('moderador')
        combo_papel.pack(fill='x', pady=(2, 15))

        def confirmar():
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showwarning('Atenção', 'Informe o nome!')
                return
            conn = self._get_conn()
            conn.cursor().execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES (?, ?, ?, ?)",
                                  (nome, entry_email.get().strip(), entry_senha.get().strip(), combo_papel.get()))
            conn.commit()
            conn.close()
            dialogo.destroy()
            self._carregar_usuarios()
            messagebox.showinfo('Sucesso', f'✅ Usuário "{nome}" criado como {combo_papel.get()}!')

        btn_frame = tk.Frame(pad, bg=CORES['card'])
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Cancelar", command=dialogo.destroy).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="💾  Salvar", command=confirmar, style='Success.TButton').pack(side='right', padx=2)
        entry_nome.bind('<Return>', lambda e: entry_email.focus())
        entry_email.bind('<Return>', lambda e: entry_senha.focus())
        entry_senha.bind('<Return>', lambda e: confirmar())

    def _alterar_senha(self):
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Alterar Senha")
        dialogo.geometry("400x250")
        dialogo.configure(bg=CORES['card'])
        dialogo.transient(self.root)
        dialogo.grab_set()

        pad = tk.Frame(dialogo, bg=CORES['card'], padx=20, pady=15)
        pad.pack(fill='both', expand=True)

        tk.Label(pad, text="Alterar Senha do Usuário", font=('Segoe UI', 12, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(pady=(0, 15))

        tk.Label(pad, text="Usuário:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        conn = self._get_conn()
        users = [(r[0], r[1]) for r in conn.cursor().execute("SELECT id, nome FROM usuarios ORDER BY nome").fetchall()]
        conn.close()
        var_user = tk.StringVar()
        combo_user = ttk.Combobox(pad, textvariable=var_user, values=[u[1] for u in users],
                                  state='readonly', font=('Segoe UI', 10))
        combo_user.pack(fill='x', pady=(2, 12))

        tk.Label(pad, text="Nova Senha:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_senha = ttk.Entry(pad, width=40, font=('Segoe UI', 10), show='•')
        entry_senha.pack(fill='x', pady=(2, 15))
        entry_senha.insert(0, '1234')

        def confirmar():
            nome = var_user.get()
            if not nome:
                messagebox.showwarning('Atenção', 'Selecione um usuário!')
                return
            nova = entry_senha.get().strip()
            if not nova:
                messagebox.showwarning('Atenção', 'Informe a nova senha!')
                return
            uid = [u[0] for u in users if u[1] == nome][0]
            conn = self._get_conn()
            conn.cursor().execute("UPDATE usuarios SET senha=? WHERE id=?", (nova, uid))
            conn.commit()
            conn.close()
            dialogo.destroy()
            messagebox.showinfo('Sucesso', f'Senha de "{nome}" alterada!')

        btn_frame = tk.Frame(pad, bg=CORES['card'])
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Cancelar", command=dialogo.destroy).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="💾  Salvar", command=confirmar, style='Success.TButton').pack(side='right', padx=2)
        entry_senha.bind('<Return>', lambda e: confirmar())

    def _alterar_minha_senha(self):
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Alterar Minha Senha")
        dialogo.geometry("380x250")
        dialogo.configure(bg=CORES['card'])
        dialogo.transient(self.root)
        dialogo.grab_set()

        pad = tk.Frame(dialogo, bg=CORES['card'], padx=20, pady=15)
        pad.pack(fill='both', expand=True)

        tk.Label(pad, text="Alterar Minha Senha", font=('Segoe UI', 12, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(pady=(0, 15))

        tk.Label(pad, text="Usuário:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        tk.Label(pad, text=self.current_user_nome or 'Desconhecido', font=('Segoe UI', 11, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(anchor='w', pady=(2, 12))

        tk.Label(pad, text="Nova Senha:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_senha = ttk.Entry(pad, width=40, font=('Segoe UI', 10), show='•')
        entry_senha.pack(fill='x', pady=(2, 8))

        tk.Label(pad, text="Confirmar Senha:", font=('Segoe UI', 9), bg=CORES['card'],
                 fg=CORES['text_sec']).pack(anchor='w')
        entry_conf = ttk.Entry(pad, width=40, font=('Segoe UI', 10), show='•')
        entry_conf.pack(fill='x', pady=(2, 15))

        def confirmar():
            nova = entry_senha.get().strip()
            conf = entry_conf.get().strip()
            if not nova:
                messagebox.showwarning('Atenção', 'Informe a nova senha!')
                return
            if nova != conf:
                messagebox.showwarning('Atenção', 'As senhas não coincidem!')
                return
            conn = self._get_conn()
            conn.cursor().execute("UPDATE usuarios SET senha=? WHERE id=?", (nova, self.current_user_id))
            conn.commit()
            conn.close()
            dialogo.destroy()
            messagebox.showinfo('Sucesso', 'Senha alterada com sucesso!')
            conn = self._get_conn()
            conn.cursor().execute("UPDATE usuarios SET senha=? WHERE id=?", (nova, uid))
            conn.commit()
            conn.close()
            dialogo.destroy()
            messagebox.showinfo('Sucesso', 'Senha alterada com sucesso!')

        btn_frame = tk.Frame(pad, bg=CORES['card'])
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Cancelar", command=dialogo.destroy).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="💾  Salvar", command=confirmar, style='Success.TButton').pack(side='right', padx=2)
        entry_senha.bind('<Return>', lambda e: entry_conf.focus())
        entry_conf.bind('<Return>', lambda e: confirmar())

    def _remover_usuario(self):
        sel = self.tree_usuarios.selection()
        if not sel:
            messagebox.showwarning('Atenção', 'Selecione um usuário na lista!')
            return
        item = self.tree_usuarios.item(sel[0])
        uid, nome = int(item['values'][0]), item['values'][1]
        if nome == 'admin':
            messagebox.showwarning('Atenção', 'Não pode remover o admin principal!')
            return
        if messagebox.askyesno('Confirmar', f'Remover usuário "{nome}"?'):
            conn = self._get_conn()
            conn.cursor().execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit()
            conn.close()
            self._carregar_usuarios()
            messagebox.showinfo('Sucesso', f'Usuário "{nome}" removido!')

    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _diagnose_db(self):
        self._log(f'=== DIAGNÓSTICO ===')
        self._log(f'DB_PATH = {DB_PATH}')
        self._log(f'DB exists: {os.path.exists(DB_PATH)}')
        try:
            conn = self._get_conn()
            c = conn.cursor()
            total_a = c.execute('SELECT COUNT(*) FROM analises').fetchone()[0]
            total_c = c.execute('SELECT COUNT(*) FROM comentarios').fetchone()[0]
            alertas = c.execute('SELECT COUNT(*) FROM analises WHERE confianca >= 50 AND resolvido = 0').fetchone()[0]
            self._log(f'analises={total_a} comentarios={total_c} alertas={alertas}')
            rows = c.execute('SELECT a.id, a.classificacao, a.confianca, a.resolvido FROM analises a ORDER BY a.id DESC LIMIT 5').fetchall()
            for r in rows:
                self._log(f'  id={r[0]} classif={r[1]} conf={r[2]} resolv={r[3]}')
            conn.close()
        except Exception as e:
            self._log(f'diagnose ERRO: {e}')
        self._log(f'=== FIM DIAGNÓSTICO ===')

    def _analisar(self):
        texto = self.txt_analise.get('1.0', tk.END).strip()
        if not texto:
            messagebox.showwarning('Atenção', 'Digite um texto para análise!')
            return
        r = self.detector.analisar(texto)
        girias_str = ', '.join([g['termo'] for g in r['girias']])
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO comentarios (fonte_id, texto, autor, data) VALUES (1, ?, ?, ?)",
                  (texto, 'Anónimo', datetime.now().isoformat()))
        com_id = c.lastrowid
        c.execute("INSERT INTO analises (comentario_id, classificacao, confianca, girias, data) VALUES (?, ?, ?, ?, ?)",
                  (com_id, r['classificacao'], r['confianca'], girias_str, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        self._mostrar_resultado(texto, r)
        self._carregar_alertas()
        messagebox.showinfo('Guardado', f'✅ Comentário analisado e guardado!\nClassificação: {r["classificacao"]} ({r["confianca"]:.1f}%)')

    def _mostrar_resultado(self, texto, r):
        self.txt_resultado.config(state='normal')
        self.txt_resultado.delete('1.0', tk.END)

        icones_nivel = {'critico': '🔴', 'alto': '🟠', 'medio': '🟡', 'baixo': '🟤', 'neutro': '⚪'}
        cores = {'Crítico': CORES['danger'], 'Ofensivo': CORES['warning'],
                 'Suspeito': '#ca8a04', 'Neutro': CORES['success']}
        cor = cores.get(r['classificacao'], CORES['text'])
        icone_cls = {'Crítico': '🔴', 'Ofensivo': '🟠', 'Suspeito': '🟡', 'Neutro': '🟢'}
        icone_geral = icones_nivel.get(r['nivel_geral'], '⚪')

        self.txt_resultado.tag_config('cls', font=('Consolas', 16, 'bold'), foreground=cor)
        self.txt_resultado.tag_config('lbl', font=('Consolas', 10, 'bold'), foreground=CORES['text'])
        self.txt_resultado.tag_config('val', font=('Consolas', 10), foreground=CORES['text'])
        self.txt_resultado.tag_config('danger', font=('Consolas', 10, 'bold'), foreground=CORES['danger'])
        self.txt_resultado.tag_config('sec', font=('Consolas', 9), foreground=CORES['text_sec'])
        self.txt_resultado.tag_config('nivel', font=('Consolas', 10, 'bold'), foreground=CORES['info'])

        self.txt_resultado.insert(tk.END, f"  {'═'*55}\n")
        self.txt_resultado.insert(tk.END, f"     {icone_cls.get(r['classificacao'],'')}  CLASSIFICAÇÃO:  {r['classificacao']}  ({r['confianca']:.1f}%)\n", 'cls')
        self.txt_resultado.insert(tk.END, f"  {'═'*55}\n\n")
        self.txt_resultado.insert(tk.END, f"  Texto analisado:\n", 'lbl')
        self.txt_resultado.insert(tk.END, f"  {texto}\n\n", 'val')

        if r['girias']:
            self.txt_resultado.insert(tk.END, f"  🔸 Gírias locais detetadas:\n", 'lbl')
            for g in r['girias']:
                ic = icones_nivel.get(g['nivel'], '⚪')
                niv = g['nivel'].upper()
                icon_of = '⚠️' if g['ofensivo'] else '✅'
                self.txt_resultado.insert(tk.END, f"     {ic} \"{g['termo']}\"  [{niv}]  {icon_of} {g['significado']}\n", 'val')
            self.txt_resultado.insert(tk.END, '\n')

        if r['palavras']:
            self.txt_resultado.insert(tk.END, f"  🔸 Palavras ofensivas detetadas:\n", 'lbl')
            for p in r['palavras']:
                ic = icones_nivel.get(p['nivel'], '⚪')
                niv = p['nivel'].upper()
                self.txt_resultado.insert(tk.END, f"     {ic} \"{p['termo']}\"  [{niv}]\n", 'val')
            self.txt_resultado.insert(tk.END, '\n')

        self.txt_resultado.insert(tk.END, f"  📊 Nível geral de ameaça: {icone_geral} {r['nivel_geral'].upper()}\n", 'nivel')

        if r['critico']:
            if r['confianca'] >= 90:
                self.txt_resultado.insert(tk.END, f"\n  ⚠️  ALERTA CRÍTICO — Requer atenção imediata!\n", 'danger')
            else:
                self.txt_resultado.insert(tk.END, f"\n  ⚠️  ALERTA — Conteúdo suspeito detetado\n", 'danger')
            self.txt_resultado.insert(tk.END, f"  {'─'*50}\n", 'sec')
            messagebox.showwarning('⚠️ Alerta', f'Texto classificado como {r["classificacao"]} ({r["confianca"]:.1f}%)\n\n"{texto[:100]}"')

        self.txt_resultado.insert(tk.END, f"\n  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'sec')
        self.txt_resultado.config(state='disabled')

    def _adicionar_comentario(self):
        texto = self.txt_analise.get('1.0', tk.END).strip()
        if not texto:
            messagebox.showwarning('Atenção', 'Digite um texto!')
            return

        dialogo = tk.Toplevel(self.root)
        dialogo.title("Nome do Autor")
        dialogo.geometry("350x130")
        dialogo.configure(bg=CORES['card'])
        dialogo.transient(self.root)
        dialogo.grab_set()

        tk.Label(dialogo, text="Informe o nome do autor (ou deixe anónimo):",
                 font=('Segoe UI', 10), bg=CORES['card']).pack(pady=(15, 5))
        entry_autor = ttk.Entry(dialogo, width=40)
        entry_autor.pack(pady=5)
        entry_autor.focus()

        def confirmar():
            autor = entry_autor.get().strip() or 'Anónimo'
            dialogo.destroy()
            self._salvar_comentario(texto, autor)

        ttk.Button(dialogo, text="Confirmar", command=confirmar).pack(pady=5)
        entry_autor.bind('<Return>', lambda e: confirmar())
        self.root.wait_window(dialogo)

    def _salvar_comentario(self, texto, autor):
        r = self.detector.analisar(texto)
        girias_str = ', '.join([g['termo'] for g in r['girias']])

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO comentarios (fonte_id, texto, autor, data) VALUES (1, ?, ?, ?)",
                  (texto, autor, datetime.now().isoformat()))
        com_id = c.lastrowid
        c.execute("INSERT INTO analises (comentario_id, classificacao, confianca, girias, data) VALUES (?, ?, ?, ?, ?)",
                  (com_id, r['classificacao'], r['confianca'], girias_str, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        self._mostrar_resultado(texto, r)
        messagebox.showinfo('Sucesso', f'✅ Comentário salvo e analisado!\nClassificação: {r["classificacao"]} ({r["confianca"]:.1f}%)')

    def _importar_testes(self):
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
            ('cutxuala-phula nao presta', 'Teste'),
            ('kizua mentiroso', 'Teste2'),
        ]

        conn = self._get_conn()
        c = conn.cursor()
        for texto, autor in testes:
            r = self.detector.analisar(texto)
            girias_str = ', '.join([g['termo'] for g in r['girias']])
            c.execute("INSERT INTO comentarios (fonte_id, texto, autor, data) VALUES (1, ?, ?, ?)",
                      (texto, autor, datetime.now().isoformat()))
            com_id = c.lastrowid
            c.execute("INSERT INTO analises (comentario_id, classificacao, confianca, girias, data) VALUES (?, ?, ?, ?, ?)",
                      (com_id, r['classificacao'], r['confianca'], girias_str, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        messagebox.showinfo('Sucesso', f'📥 {len(testes)} comentários importados e analisados!')
        self._carregar_alertas()

    def _carregar_alertas(self):
        for item in self.tree_alertas.get_children():
            self.tree_alertas.delete(item)

        conn = self._get_conn()
        c = conn.cursor()
        rows = c.execute("""
            SELECT a.id, a.data, c.autor, c.texto, a.confianca, a.girias
            FROM analises a JOIN comentarios c ON a.comentario_id = c.id
            WHERE a.confianca >= 50 AND a.resolvido = 0
            ORDER BY a.confianca DESC
        """).fetchall()
        self._log(f'carregar_alertas: {len(rows)} alertas encontrados')

        for row in rows:
            txt = (row[3][:75] + '...') if len(row[3]) > 75 else row[3]
            self.tree_alertas.insert('', 'end', values=(row[0], row[1][:16], row[2], txt,
                                                         f'{row[4]:.1f}%', row[5] or '-'))

        conn.close()
        qtd = len(rows)
        self.lbl_qtd_alertas.config(
            text=f"⚠️  {qtd} alerta(s) pendente(s)" if qtd > 0 else "✅  Nenhum alerta pendente",
            foreground=CORES['danger'] if qtd > 0 else CORES['success']
        )

    def _resolver(self):
        sel = self.tree_alertas.selection()
        if not sel:
            messagebox.showwarning('Atenção', 'Selecione um alerta para resolver!')
            return
        aid = self.tree_alertas.item(sel[0])['values'][0]
        conn = self._get_conn()
        conn.cursor().execute("UPDATE analises SET resolvido = 1 WHERE id = ?", (aid,))
        conn.commit()
        conn.close()
        self._carregar_alertas()
        messagebox.showinfo('Sucesso', '✅ Alerta marcado como resolvido!')

    def _carregar_girias(self):
        for item in self.tree_girias.get_children():
            self.tree_girias.delete(item)
        conn = self._get_conn()
        for row in conn.cursor().execute("SELECT id, termo, significado, tipo, nivel FROM girias_db"):
            niv = row[4] if row[4] else 'neutro'
            self.tree_girias.insert('', 'end', values=(row[0], row[1], row[2], row[3], niv.upper()))
        conn.close()

    def _adicionar_giria(self):
        termo = self.entry_giria.get().strip()
        sig = self.entry_significado.get().strip()
        tipo = self.combo_tipo.get()
        if not termo:
            messagebox.showwarning('Atenção', 'Digite o termo da gíria!')
            return
        conn = self._get_conn()
        nivel = self.combo_nivel.get()
        conn.cursor().execute("INSERT INTO girias_db (termo, significado, tipo, nivel) VALUES (?, ?, ?, ?)", (termo, sig, tipo, nivel))
        conn.commit()
        conn.close()
        self.entry_giria.delete(0, tk.END)
        self.entry_significado.delete(0, tk.END)
        self._carregar_girias()
        self.detector._load_dicionario_local()
        messagebox.showinfo('Sucesso', '✅ Gíria adicionada ao dicionário local!')

    def _remover_giria(self):
        sel = self.tree_girias.selection()
        if not sel:
            messagebox.showwarning('Atenção', 'Selecione uma gíria!')
            return
        gid = self.tree_girias.item(sel[0])['values'][0]
        conn = self._get_conn()
        conn.cursor().execute("DELETE FROM girias_db WHERE id = ?", (gid,))
        conn.commit()
        conn.close()
        self._carregar_girias()
        self.detector._load_dicionario_local()

    def _carregar_fontes(self):
        for item in self.tree_fontes.get_children():
            self.tree_fontes.delete(item)
        conn = self._get_conn()
        for row in conn.cursor().execute("SELECT id, url, nome, tipo FROM fontes"):
            self.tree_fontes.insert('', 'end', values=(row[0], row[1], row[2], row[3]))
        conn.close()

    def _adicionar_fonte(self):
        url = self.entry_url.get().strip()
        nome = self.entry_nome_fonte.get().strip()
        if not url or not nome:
            messagebox.showwarning('Atenção', 'Preencha URL e Nome!')
            return
        conn = self._get_conn()
        conn.cursor().execute("INSERT INTO fontes (url, nome) VALUES (?, ?)", (url, nome))
        conn.commit()
        conn.close()
        self.entry_url.delete(0, tk.END)
        self.entry_nome_fonte.delete(0, tk.END)
        self._carregar_fontes()
        messagebox.showinfo('Sucesso', '✅ Fonte adicionada!')

    def _remover_fonte(self):
        sel = self.tree_fontes.selection()
        if not sel:
            messagebox.showwarning('Atenção', 'Selecione uma fonte!')
            return
        fid = self.tree_fontes.item(sel[0])['values'][0]
        conn = self._get_conn()
        conn.cursor().execute("DELETE FROM fontes WHERE id = ?", (fid,))
        conn.commit()
        conn.close()
        self._carregar_fontes()

    def _carregar_usuarios(self):
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
        conn = self._get_conn()
        for row in conn.cursor().execute("SELECT id, nome, email, papel FROM usuarios"):
            self.tree_usuarios.insert('', 'end', values=(row[0], row[1], row[2], row[3]))
        conn.close()

    def _gerar_stats(self):
        conn = self._get_conn()
        c = conn.cursor()

        total = c.execute('SELECT COUNT(*) FROM comentarios').fetchone()[0]
        analisados = c.execute('SELECT COUNT(*) FROM analises').fetchone()[0]
        crit = c.execute("SELECT COUNT(*) FROM analises WHERE confianca >= 95").fetchone()[0]
        ofen = c.execute("SELECT COUNT(*) FROM analises WHERE classificacao = 'Ofensivo'").fetchone()[0]
        neut = c.execute("SELECT COUNT(*) FROM analises WHERE classificacao = 'Neutro'").fetchone()[0]
        susp = c.execute("SELECT COUNT(*) FROM analises WHERE classificacao = 'Suspeito'").fetchone()[0]
        resol = c.execute("SELECT COUNT(*) FROM analises WHERE resolvido = 1").fetchone()[0]
        girias_count = c.execute('SELECT COUNT(*) FROM girias_db').fetchone()[0]
        girias_of = c.execute("SELECT COUNT(*) FROM girias_db WHERE tipo='ofensivo'").fetchone()[0]
        fontes_count = c.execute('SELECT COUNT(*) FROM fontes').fetchone()[0]
        usuarios_count = c.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]

        self.txt_relatorio.config(state='normal')
        self.txt_relatorio.delete('1.0', tk.END)

        g_total = c.execute('SELECT COUNT(*) FROM girias_db').fetchone()[0]
        g_crit = c.execute("SELECT COUNT(*) FROM girias_db WHERE nivel='critico'").fetchone()[0]
        g_alto = c.execute("SELECT COUNT(*) FROM girias_db WHERE nivel='alto'").fetchone()[0]
        g_med = c.execute("SELECT COUNT(*) FROM girias_db WHERE nivel='medio'").fetchone()[0]
        g_baixo = c.execute("SELECT COUNT(*) FROM girias_db WHERE nivel='baixo'").fetchone()[0]
        g_neut = c.execute("SELECT COUNT(*) FROM girias_db WHERE nivel='neutro'").fetchone()[0]

        taxa = f"{(crit / analisados * 100):.1f}" if analisados > 0 else "0.0"

        texto = f"""
{'╔' + '═'*58 + '╗'}
{'║'}  🛡️  RELATÓRIO DO SISTEMA DE DETECÇÃO DE CYBERBULLYING  {'║'}
{'║'}     Saurimo, Angola  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}      {'║'}
{'╚' + '═'*58 + '╝'}

{'━'*60}
 📊 ESTATÍSTICAS GERAIS
{'━'*60}

 Total de Comentários     :  {total:>6}
 Total Analisados         :  {analisados:>6}
 Taxa de Casos Críticos   :  {taxa:>6}%
 Casos Resolvidos         :  {resol:>6}  ({f'{(resol/analisados*100):.1f}%' if analisados > 0 else '0.0%'})

{'─'*60}
 📈 CLASSIFICAÇÃO DOS CASOS
{'─'*60}

 Crítico   :  {'█' * min(crit, 30)}  ({crit})
 Ofensivo  :  {'█' * min(ofen, 30)}  ({ofen})
 Suspeito  :  {'█' * min(susp, 30)}  ({susp})
 Neutro    :  {'█' * min(neut, 30)}  ({neut})

{'─'*60}
 📚 DICIONÁRIO LOCAL DE GÍRIAS (POR NÍVEL DE AMEAÇA)
{'─'*60}

 Total de Gírias   :  {girias_count}
 🔴 Críticas       :  {g_crit}
 🟠 Altas          :  {g_alto}
 🟡 Médias         :  {g_med}
 🟤 Baixas         :  {g_baixo}
 ⚪ Neutras        :  {g_neut}

 Fontes Facebook   :  {fontes_count}
 Usuários Sistema  :  {usuarios_count}

{'━'*60}
 🔝 TOP 10 CASOS MAIS GRAVES
{'━'*60}
"""
        self.txt_relatorio.insert(tk.END, texto)

        for i, row in enumerate(c.execute("""
            SELECT c.texto, a.classificacao, a.confianca, a.girias, a.data
            FROM analises a JOIN comentarios c ON a.comentario_id = c.id
            ORDER BY a.confianca DESC LIMIT 10
        """), 1):
            txt = row[0][:55] + '...' if len(row[0]) > 55 else row[0]
            self.txt_relatorio.insert(tk.END,
                f" {i:2d}.  [{row[1]:8s}]  {row[2]:5.1f}%  |  {txt}\n")

        conn.close()
        self.txt_relatorio.config(state='disabled')

    def _exportar_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path: return
        conn = self._get_conn()
        rows = conn.cursor().execute("""
            SELECT c.texto, c.autor, a.classificacao, a.confianca, a.girias, a.data
            FROM analises a JOIN comentarios c ON a.comentario_id = c.id ORDER BY a.data
        """).fetchall()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Texto', 'Autor', 'Classificação', 'Confiança(%)', 'Gírias', 'Data'])
            w.writerows(rows)
        conn.close()
        messagebox.showinfo('Sucesso', f'📄 Relatório exportado com {len(rows)} registos!')

    def _exportar_txt(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('TXT', '*.txt')])
        if not path: return
        conn = self._get_conn()
        rows = conn.cursor().execute("""
            SELECT c.texto, c.autor, a.classificacao, a.confianca, a.girias, a.data
            FROM analises a JOIN comentarios c ON a.comentario_id = c.id ORDER BY a.data
        """).fetchall()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"SISTEMA DE DETECÇÃO DE CYBERBULLYING - RELATÓRIO\n")
            f.write(f"Saurimo, Angola - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"{'='*70}\n\n")
            for row in rows:
                f.write(f"Texto: {row[0]}\n")
                f.write(f"Autor: {row[1]}  |  Classificação: {row[2]} ({row[3]:.1f}%)\n")
                if row[4]: f.write(f"Gírias detetadas: {row[4]}\n")
                f.write(f"Data: {row[5]}\n")
                f.write("-" * 70 + "\n")
        conn.close()
        messagebox.showinfo('Sucesso', f'📃 Relatório exportado com {len(rows)} registos!')

class LoginDialog:
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Cyberbullying Detector - Login")
        self.janela.geometry("420x500")
        self.janela.configure(bg=CORES['primary'])
        self.janela.resizable(False, False)
        self.autenticado = False

        try:
            self.janela.iconbitmap(default='')
        except:
            pass
        if os.path.exists(LOGO_PATH):
            try:
                img = tk.PhotoImage(file=LOGO_PATH)
                self.janela.iconphoto(True, img)
            except:
                pass

        self.janela.overrideredirect(True)
        self._center(420, 500)
        self._build()

    def _center(self, w, h):
        sw = self.janela.winfo_screenwidth()
        sh = self.janela.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        outer = tk.Frame(self.janela, bg=CORES['primary'])
        outer.pack(fill='both', expand=True)

        card = tk.Frame(outer, bg=CORES['card'], padx=35, pady=30,
                        highlightbackground=CORES['border'], highlightthickness=1)
        card.pack(expand=True, fill='both', padx=30, pady=30)

        logo_path = LOGO_PATH
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                w = self.logo_img.width()
                s = max(w // 200, 1)
                self.logo_img = self.logo_img.subsample(s, s)
                img = tk.Label(card, image=self.logo_img, bg=CORES['card'])
                img.image = self.logo_img
                img.pack(pady=(0, 5))
            except:
                tk.Label(card, text="🛡️", font=('Segoe UI', 40), bg=CORES['card']).pack(pady=(0, 5))
        else:
            tk.Label(card, text="🛡️", font=('Segoe UI', 40), bg=CORES['card']).pack(pady=(0, 5))
        tk.Label(card, text="Cyberbullying Detector",
                 font=('Segoe UI', 16, 'bold'), bg=CORES['card'], fg=CORES['text']).pack()
        tk.Label(card, text="Sistema de Detecção de Cyberbullying",
                 font=('Segoe UI', 9), bg=CORES['card'], fg=CORES['text_sec']).pack()
        tk.Label(card, text="Saurimo, Angola",
                 font=('Segoe UI', 8), bg=CORES['card'], fg=CORES['text_sec']).pack(pady=(0, 20))

        tk.Label(card, text="Usuário", font=('Segoe UI', 9, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(anchor='w')
        self.entry_user = ttk.Entry(card, width=28, font=('Segoe UI', 11))
        self.entry_user.pack(fill='x', pady=(2, 12))
        self.entry_user.focus()
        self.entry_user.bind('<Return>', lambda e: self.entry_pass.focus())

        tk.Label(card, text="Senha", font=('Segoe UI', 9, 'bold'),
                 bg=CORES['card'], fg=CORES['text']).pack(anchor='w')
        self.entry_pass = ttk.Entry(card, width=28, font=('Segoe UI', 11), show='•')
        self.entry_pass.pack(fill='x', pady=(2, 20))
        self.entry_pass.bind('<Return>', lambda e: self._login())

        self.lbl_erro = tk.Label(card, text="", font=('Segoe UI', 9),
                                 bg=CORES['card'], fg=CORES['danger'])
        self.lbl_erro.pack(pady=(0, 5))

        ttk.Button(card, text="🔑  Entrar", command=self._login, style='TButton').pack(fill='x', ipady=4)

        tk.Label(card, text="PP1 - Eng. Software + SO | IPLS 2026",
                 font=('Segoe UI', 7), bg=CORES['card'], fg=CORES['text_sec']).pack(side='bottom', pady=(15, 0))

    def _login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        _debug_log(f'_login attempt user="{user}" pwd="{pwd}"')

        conn = sqlite3.connect(DB_PATH, timeout=10)
        c = conn.cursor()
        row = c.execute("SELECT id, papel FROM usuarios WHERE nome=? AND senha=?", (user, pwd)).fetchone()
        _debug_log(f'_login direct query result={row}')
        if not row:
            all_users = c.execute("SELECT id, nome, senha, papel FROM usuarios").fetchall()
            for r in all_users:
                _debug_log(f'  db user id={r[0]} nome="{r[1]}" senha="{r[2]}" papel="{r[3]}"')
            if user == 'Alberto Baptista' and pwd == '240520':
                _debug_log('_login fallback: fixing admin')
                c.execute("UPDATE usuarios SET senha='240520', papel='admin' WHERE nome='Alberto Baptista'")
                if c.rowcount == 0:
                    c.execute("INSERT INTO usuarios (nome, email, senha, papel) VALUES ('Alberto Baptista', 'alberto@saurimo.ao', '240520', 'admin')")
                    _debug_log('_login fallback: inserted admin')
                conn.commit()
                row = c.execute("SELECT id, papel FROM usuarios WHERE nome=? AND senha=?", (user, pwd)).fetchone()
                _debug_log(f'_login fallback result={row}')
        conn.close()
        if row:
            self.autenticado = True
            self.papel = row[1]
            self.login_id = row[0]
            self.login_nome = user
            self.janela.destroy()
        else:
            self.lbl_erro.config(text="❌ Usuário ou senha inválidos!")
            self.entry_pass.delete(0, tk.END)
            self.entry_user.focus()

    def run(self):
        self.janela.mainloop()
        return self.autenticado, getattr(self, 'papel', 'moderador'), getattr(self, 'login_id', None), getattr(self, 'login_nome', None)


def main():
    _setup_db(DB_PATH)
    login = LoginDialog()
    ok, papel, login_id, login_nome = login.run()
    if ok:
        root = tk.Tk()
        try: root.iconbitmap(default='')
        except: pass
        app = CyberbullyingApp(root, papel=papel, current_user_id=login_id, current_user_nome=login_nome)
        app.root.mainloop()

if __name__ == '__main__':
    main()
