const API_BASE = '';

async function api(endpoint, options = {}) {
    const response = await fetch(API_BASE + endpoint, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options
    });
    if (response.status === 401) {
        window.location.href = '/login';
        return;
    }
    return response.json();
}

const icones_nivel = {'critico': '🔴', 'alto': '🟠', 'medio': '🟡', 'baixo': '🟤', 'neutro': '⚪'};

function mostrarPagina(nome) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.menu-btn[data-page]').forEach(b => b.classList.remove('active'));
    const page = document.getElementById('page-' + nome);
    if (page) page.classList.add('active');
    const btn = document.querySelector(`.menu-btn[data-page="${nome}"]`);
    if (btn) btn.classList.add('active');
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.remove('open');
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

async function carregarEstatisticas() {
    try {
        const stats = await api('/api/estatisticas');
        document.getElementById('total-comentarios').textContent = stats.total_comentarios || 0;
        document.getElementById('total-analisados').textContent = stats.total_analisados || 0;
        document.getElementById('casos-criticos').textContent = stats.casos_criticos || 0;
        document.getElementById('taxa-deteccao').textContent = (stats.taxa_deteccao || 0) + '%';
    } catch (e) { console.error('Erro ao carregar estatísticas:', e); }
}

async function carregarAlertas() {
    try {
        const alertas = await api('/api/alertas');
        const container = document.getElementById('alertas-lista');
        if (alertas.length === 0) {
            container.innerHTML = '<p class="empty-message">Nenhum alerta pendente (confiança ≥ 50%)</p>';
            return;
        }
        container.innerHTML = alertas.map(a => `
            <div class="alerta-item ${a.classificacao.toLowerCase()}">
                <p><strong>Autor:</strong> ${a.comentario.autor || 'Anónimo'}</p>
                <p><strong>Texto:</strong> ${a.comentario.texto}</p>
                <p><strong>Classificação:</strong> <span class="classificacao ${a.classificacao.toLowerCase()}">${a.classificacao}</span></p>
                <p><strong>Confiança:</strong> ${a.confianca}%</p>
                <p><strong>Data:</strong> ${new Date(a.data).toLocaleString('pt-AO')}</p>
                <div class="alerta-actions">
                    <button class="small success" onclick="resolverAlerta(${a.id})">✅ Resolver</button>
                    <button class="small" onclick="reportarFacebook(${a.id})">📢 Reportar ao Facebook</button>
                </div>
            </div>
        `).join('');
        const badge = document.getElementById('badge-alertas');
        if (badge) {
            badge.textContent = alertas.length;
            badge.style.display = alertas.length > 0 ? 'inline' : 'none';
        }
    } catch (e) { console.error('Erro ao carregar alertas:', e); }
}

async function carregarAnalises() {
    try {
        const analises = await api('/api/analises');
        const tbody = document.getElementById('analises-body');
        if (analises.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-message">Nenhuma análise realizada</td></tr>';
            return;
        }
        tbody.innerHTML = analises.map(a => {
            const classLower = a.classificacao.toLowerCase();
            return `<tr>
                <td>${new Date(a.data).toLocaleDateString('pt-AO')}</td>
                <td>${a.comentario.autor || 'Anónimo'}</td>
                <td class="truncate" title="${a.comentario.texto}">${a.comentario.texto}</td>
                <td><span class="classificacao ${classLower}">${a.classificacao}</span></td>
                <td>${a.confianca}%</td>
                <td>${a.girias || '-'}</td>
                <td>${a.nivel_geral ? icones_nivel[a.nivel_geral] || '' : ''}</td>
                <td>${!a.resolvido ? `<button class="small success" onclick="resolverAnalise(${a.id})">✓</button>` : '<span style="color:#16a34a">✓</span>'}</td>
            </tr>`;
        }).join('');
    } catch (e) { console.error('Erro ao carregar análises:', e); }
}

async function carregarFontes() {
    try {
        const fontes = await api('/api/fontes');
        const container = document.getElementById('fontes-lista');
        if (fontes.length === 0) {
            container.innerHTML = '<p class="empty-message">Nenhuma fonte cadastrada</p>';
            return;
        }
        container.innerHTML = fontes.map(f => `
            <div class="fonte-item">
                <div><strong>${f.nome}</strong><br><small>${f.url}</small></div>
                <button class="small danger" onclick="removerFonte(${f.id})">✕</button>
            </div>
        `).join('');
    } catch (e) { console.error('Erro ao carregar fontes:', e); }
}

async function carregarDicionario() {
    try {
        const girias = await api('/api/dicionario');
        const container = document.getElementById('dicionario-lista');
        if (girias.length === 0) {
            container.innerHTML = '<p class="empty-message">Nenhuma gíria cadastrada</p>';
            return;
        }
        container.innerHTML = girias.map(g => `
            <div class="giria-item">
                <div>
                    <strong>"${g.termo}"</strong> - ${g.significado || 'Sem significado'}
                    <span class="classificacao ${g.nivel}" style="margin-left:0.5rem">${icones_nivel[g.nivel] || ''} ${g.nivel}</span>
                </div>
                <button class="small danger" onclick="removerGiria(${g.id})">✕</button>
            </div>
        `).join('');
    } catch (e) { console.error('Erro ao carregar dicionário:', e); }
}

async function carregarUsuarios() {
    try {
        const usuarios = await api('/api/usuarios');
        const container = document.getElementById('usuarios-lista');
        if (usuarios.length === 0) {
            container.innerHTML = '<p class="empty-message">Nenhum usuário cadastrado</p>';
            return;
        }
        container.innerHTML = usuarios.map(u => `
            <div class="usuario-item">
                <div><strong>${u.nome}</strong> - ${u.email}</div>
                <div>
                    <span class="classificacao ${u.papel === 'admin' ? 'critico' : 'ofensivo'}">${u.papel}</span>
                    <button class="btn-small btn-primary" onclick="alterarSenha(${u.id}, '${u.nome}')">🔑</button>
                    ${u.nome !== 'admin' ? `<button class="btn-small btn-danger" onclick="deletarUsuario(${u.id}, '${u.nome}')">🗑️</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) { console.error('Erro ao carregar usuários:', e); }
}

async function analisarTexto() {
    const texto = document.getElementById('texto-analise').value.trim();
    if (!texto) { alert('Por favor, digite um texto para análise'); return; }
    try {
        const resultado = await api('/api/detectar', { method: 'POST', body: JSON.stringify({ texto }) });
        const box = document.getElementById('resultado-analise');
        box.style.display = 'block';
        let tipoClass = 'neutro';
        if (resultado.classificacao === 'Crítico') tipoClass = 'critico';
        else if (resultado.classificacao === 'Ofensivo' || resultado.classificacao === 'Suspeito') tipoClass = 'ofensivo';
        box.className = `resultado-box ${tipoClass}`;

        let html = `<h4>${icones_nivel[resultado.nivel_geral] || '⚪'} Classificação: ${resultado.classificacao}</h4>
            <p><strong>Confiança:</strong> ${resultado.confianca}%</p>`;

        if (resultado.palavras && resultado.palavras.length > 0) {
            html += '<p><strong>Palavras ofensivas:</strong></p><ul>';
            resultado.palavras.forEach(p => {
                html += `<li>${icones_nivel[p.nivel] || '⚪'} "${p.termo}" [${p.nivel.toUpperCase()}]</li>`;
            });
            html += '</ul>';
        }

        if (resultado.girias && resultado.girias.length > 0) {
            html += '<p><strong>Gírias detetadas:</strong></p><ul>';
            resultado.girias.forEach(g => {
                html += `<li>${icones_nivel[g.nivel] || '⚪'} "${g.termo}" - ${g.significado} [${g.nivel.toUpperCase()}]</li>`;
            });
            html += '</ul>';
        }

        if (resultado.critico) {
            html += '<p style="color:#dc2626"><strong>⚠️ ALERTA — Conteúdo suspeito detetado!</strong></p>';
        }
        box.innerHTML = html;
    } catch (e) { console.error('Erro na análise:', e); alert('Erro ao realizar análise'); }
}

async function adicionarComentario() {
    const texto = document.getElementById('novo-comentario').value.trim();
    const autor = document.getElementById('autor-comentario').value.trim();
    if (!texto) { alert('Por favor, digite o comentário'); return; }
    try {
        await api('/api/comentarios', { method: 'POST', body: JSON.stringify({ texto, autor }) });
        document.getElementById('novo-comentario').value = '';
        document.getElementById('autor-comentario').value = '';
        carregarTudo();
        alert('Comentário adicionado e analisado com sucesso!');
    } catch (e) { console.error('Erro ao adicionar comentário:', e); alert('Erro ao adicionar comentário'); }
}

async function adicionarFonte() {
    const url = document.getElementById('nova-url').value.trim();
    const nome = document.getElementById('novo-nome').value.trim();
    if (!url || !nome) { alert('Preencha URL e nome'); return; }
    try {
        await api('/api/fontes', { method: 'POST', body: JSON.stringify({ url, nome }) });
        document.getElementById('nova-url').value = '';
        document.getElementById('novo-nome').value = '';
        carregarFontes();
        alert('Fonte adicionada com sucesso!');
    } catch (e) { console.error('Erro ao adicionar fonte:', e); }
}

async function adicionarGiria() {
    const termo = document.getElementById('nova-giria').value.trim();
    const significado = document.getElementById('significado-giria').value.trim();
    const tipo = document.getElementById('tipo-giria').value;
    const nivel = document.getElementById('nivel-giria').value;
    if (!termo) { alert('Digite a gíria'); return; }
    try {
        await api('/api/dicionario', { method: 'POST', body: JSON.stringify({ termo, significado, tipo, nivel }) });
        document.getElementById('nova-giria').value = '';
        document.getElementById('significado-giria').value = '';
        carregarDicionario();
        alert('Gíria adicionada com sucesso!');
    } catch (e) { console.error('Erro ao adicionar gíria:', e); }
}

async function resolverAnalise(id) {
    try {
        await api(`/api/analises/${id}/resolver`, { method: 'POST' });
        carregarTudo();
    } catch (e) { console.error('Erro ao resolver análise:', e); }
}

async function resolverAlerta(id) { await resolverAnalise(id); }

async function reportarFacebook(id) {
    try {
        const analises = await api('/api/analises');
        const a = analises.find(x => x.id === id);
        if (!a) { alert('Alerta não encontrado'); return; }
        const texto = `🚨 Comentário ofensivo detetado (Cyberbullying Detector)\n\nAutor: ${a.comentario.autor}\nTexto: ${a.comentario.texto}\nClassificação: ${a.classificacao}\nConfiança: ${a.confianca}%\n\nPor favor, revisem este conteúdo.`;
        await navigator.clipboard.writeText(texto);
        alert(`📢 Informação copiada para a área de transferência!\n\nCole manualmente no grupo do Facebook.\n\nComentário: "${a.comentario.texto.substring(0, 80)}"\nAutor: ${a.comentario.autor}\nConfiança: ${a.confianca}%`);
    } catch (e) { console.error('Erro ao reportar:', e); alert('Erro ao copiar para área de transferência'); }
}

async function removerFonte(id) {
    if (!confirm('Tem certeza?')) return;
    try { await api(`/api/fontes/${id}`, { method: 'DELETE' }); carregarFontes(); }
    catch (e) { console.error(e); }
}

async function removerGiria(id) {
    if (!confirm('Tem certeza?')) return;
    try { await api(`/api/dicionario/${id}`, { method: 'DELETE' }); carregarDicionario(); }
    catch (e) { console.error(e); }
}

async function gerarRelatorio() {
    try {
        const relatorio = await api('/api/relatorio');
        let html = '<h4>Por Classificação:</h4><ul>';
        relatorio.por_classificacao.forEach(item => { html += `<li>${item.classificacao}: ${item.total}</li>`; });
        html += '</ul>';
        if (relatorio.por_fonte.length > 0) {
            html += '<h4>Por Fonte:</h4><ul>';
            relatorio.por_fonte.forEach(item => { html += `<li>${item.fonte}: ${item.total}</li>`; });
            html += '</ul>';
        }
        html += `<p><small>Gerado em: ${new Date(relatorio.data_geracao).toLocaleString('pt-AO')}</small></p>`;
        document.getElementById('relatorio-resultado').innerHTML = html;
    } catch (e) { console.error('Erro ao gerar relatório:', e); }
}

async function inicializarDados() {
    if (!confirm('Inicializar dados padrão?')) return;
    try { await api('/api/inicializar', { method: 'POST' }); carregarTudo(); alert('Dados inicializados!'); }
    catch (e) { console.error(e); }
}

async function importarComentarios() {
    try { const r = await api('/api/importar-comentarios', { method: 'POST' }); carregarTudo(); alert(r.message); }
    catch (e) { console.error(e); }
}

async function adicionarUsuario() {
    const nome = document.getElementById('novo-usuario-nome').value.trim();
    const email = document.getElementById('novo-usuario-email').value.trim();
    const senha = document.getElementById('novo-usuario-senha').value.trim();
    const papel = document.getElementById('novo-usuario-papel').value;
    if (!nome) { alert('Preencha o nome do usuário'); return; }
    try {
        await api('/api/usuarios', { method: 'POST', body: JSON.stringify({ nome, email, senha, papel }) });
        document.getElementById('novo-usuario-nome').value = '';
        document.getElementById('novo-usuario-email').value = '';
        document.getElementById('novo-usuario-senha').value = '1234';
        carregarUsuarios();
        alert('Usuário criado com sucesso!');
    } catch (e) { console.error('Erro ao criar usuário:', e); }
}

async function deletarUsuario(id, nome) {
    if (!confirm(`Remover usuário "${nome}"?`)) return;
    try {
        await api(`/api/usuarios/${id}`, { method: 'DELETE' });
        carregarUsuarios();
        alert(`Usuário "${nome}" removido!`);
    } catch (e) { console.error('Erro ao remover usuário:', e); }
}

async function alterarSenha(id, nome) {
    const senha = prompt(`Nova senha para "${nome}":`, '1234');
    if (!senha) return;
    try {
        await api('/api/alterar-senha', { method: 'POST', body: JSON.stringify({ id, senha }) });
        alert(`Senha de "${nome}" alterada!`);
    } catch (e) { console.error('Erro ao alterar senha:', e); }
}

async function minhaSenha() {
    const senha = prompt('Nova senha:');
    if (!senha) return;
    const conf = prompt('Confirmar nova senha:');
    if (senha !== conf) { alert('As senhas não coincidem!'); return; }
    try {
        await api('/api/minha-senha', { method: 'POST', body: JSON.stringify({ senha }) });
        alert('Senha alterada com sucesso!');
    } catch (e) { console.error('Erro ao alterar senha:', e); }
}

function carregarTudo() {
    carregarEstatisticas(); carregarAlertas(); carregarAnalises();
    carregarFontes(); carregarDicionario(); carregarUsuarios();
}

document.addEventListener('DOMContentLoaded', function() {
    const papel = document.documentElement.dataset.papel || 'moderador';
    if (papel !== 'admin') {
        document.querySelectorAll('[data-admin]').forEach(el => el.style.display = 'none');
    }
    carregarTudo();
    setInterval(carregarTudo, 5000);
});
