O servidor web está funcional. Vou abrir o navegador para testar a interface.

Resumo do que foi feito:

1. **app/__init__.py** — DB aponta para `data/cyberbullying.db` (mesmo do desktop)
2. **app/models.py** — Esquema idêntico ao desktop: `usuarios`, `fontes`, `comentarios`, `analises`, `girias_db`
3. **app/detector.py** — Detector com 170+ palavras com níveis (crítico/alto/médio/baixo), mesmo scoring do desktop
4. **app/routes.py** — 15 endpoints, alertas com threshold ≥ 50%, dicionário com nível, reportar ao Facebook
5. **app/static/js/main.js** — Mostra níveis com ícones, botões "Resolver" e "Reportar ao Facebook" nos alertas
6. **index.html / style.css** — Interface atualizada com coluna nível, seletor de nível nas gírias
