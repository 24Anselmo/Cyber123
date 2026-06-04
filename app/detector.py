import re
import json
import os

class Detector:
    def __init__(self):
        self.dicionario_local = {}
        self._load_dicionario_local()
        self.pa = [
            ('vou te matar', 'critico'), ('vou matar te', 'critico'), ('vou te assassinar', 'critico'),
            ('vou te enforcar', 'critico'), ('vou te decapitar', 'critico'), ('vou te cortar', 'critico'),
            ('vou te esfaquear', 'critico'), ('vou te furar', 'critico'), ('vou te queimar', 'critico'),
            ('vou te explodir', 'critico'), ('vou te destruir', 'critico'), ('vou te partir', 'critico'),
            ('vou te esquartej', 'critico'), ('vai morrer', 'critico'), ('morre', 'critico'),
            ('vai para o inferno', 'critico'), ('vou te estuprar', 'critico'), ('vou te violar', 'critico'),
            ('morte', 'critico'), ('matar', 'critico'), ('assassinar', 'critico'), ('enforcar', 'critico'),
            ('suicida', 'critico'), ('suicidio', 'critico'), ('morta', 'critico'), ('morto', 'critico'),
            ('esfaquear', 'critico'), ('cortar pescoc', 'critico'), ('vinganca', 'critico'),
            ('vingar', 'critico'), ('exterminar', 'critico'), ('aniquilar', 'critico'),
            ('vou acabar com a sua vida', 'critico'), ('vou acabar com a tua vida', 'critico'),
            ('vou te caçar', 'critico'), ('vou te queimar vivo', 'critico'), ('sangue', 'critico'),
            ('morrer', 'critico'), ('assassino', 'critico'), ('massacre', 'critico'),
            ('vai se foder', 'critico'), ('vai tomar no cu', 'critico'),

            ('filho da puta', 'alto'), ('filha da puta', 'alto'), ('puta', 'alto'),
            ('puto', 'alto'), ('caralho', 'alto'), ('porra', 'alto'), ('desgraça', 'alto'),
            ('desgraçado', 'alto'), ('desgraçada', 'alto'), ('foder', 'alto'), ('foda', 'alto'),
            ('fodido', 'alto'), ('fodida', 'alto'), ('cuzão', 'alto'), ('cuzona', 'alto'),
            ('cuzao', 'alto'), ('vai se fuder', 'alto'), ('vai se foder', 'alto'),
            ('tomar no cu', 'alto'), ('tomar no cú', 'alto'), ('foda-se', 'alto'),
            ('foda se', 'alto'), ('vá se foder', 'alto'), ('va se foder', 'alto'),
            ('piranha', 'alto'), ('prostituta', 'alto'), ('putaria', 'alto'),
            ('escroto', 'alto'), ('escrota', 'alto'), ('merda', 'alto'),
            ('buceta', 'alto'), ('bucetao', 'alto'), ('bucetão', 'alto'),
            ('rabuda', 'alto'), ('vagabundo', 'alto'), ('vagabunda', 'alto'),
            ('corno', 'alto'), ('corna', 'alto'), ('arrombado', 'alto'), ('arrombada', 'alto'),
            ('pau no cu', 'alto'), ('pau no cú', 'alto'),

            ('idiota', 'medio'), ('estupido', 'medio'), ('estúpido', 'medio'), ('burra', 'medio'),
            ('otario', 'medio'), ('otário', 'medio'), ('imbecil', 'medio'), ('palhaço', 'medio'),
            ('palhaco', 'medio'), ('ridículo', 'medio'), ('ridiculo', 'medio'), ('nojo', 'medio'),
            ('nojento', 'medio'), ('nojenta', 'medio'), ('odeio', 'medio'), ('ódio', 'medio'),
            ('odio', 'medio'), ('desaparece', 'medio'), ('desapareça', 'medio'),
            ('lixo humano', 'medio'), ('lixo', 'medio'), ('feio', 'medio'), ('feia', 'medio'),
            ('besta', 'medio'), ('asno', 'medio'), ('tolo', 'medio'), ('tola', 'medio'),
            ('hipócrita', 'medio'), ('hipocrita', 'medio'), ('retardado', 'medio'),
            ('retardada', 'medio'), ('deficiente', 'medio'), ('mongol', 'medio'),
            ('mongoloide', 'medio'), ('anormal', 'medio'), ('semi analfabeto', 'medio'),
            ('semi-analfabeto', 'medio'), ('ignorante', 'medio'), ('calado', 'medio'),
            ('calada', 'medio'), ('chato', 'medio'), ('chata', 'medio'),
            ('chato de galocha', 'medio'), ('insuportavel', 'medio'), ('insuportável', 'medio'),
            ('chato do caralho', 'medio'), ('enche o saco', 'medio'), ('aborrecente', 'medio'),
            ('aborrecido', 'medio'), ('aborrecida', 'medio'),

            ('burro', 'baixo'), ('inutil', 'baixo'), ('inútil', 'baixo'), ('fraco', 'baixo'),
            ('fraca', 'baixo'), ('perdedor', 'baixo'), ('perdedora', 'baixo'), ('mentiroso', 'baixo'),
            ('mentirosa', 'baixo'), ('ladrão', 'baixo'), ('ladrao', 'baixo'), ('ladra', 'baixo'),
            ('preguiçoso', 'baixo'), ('preguicosa', 'baixo'), ('preguiçosa', 'baixo'),
            ('lento', 'baixo'), ('lenta', 'baixo'), ('lerdo', 'baixo'), ('lerda', 'baixo'),
            ('ralado', 'baixo'), ('ralada', 'baixo'), ('coxo', 'baixo'), ('mijao', 'baixo'),
            ('mijão', 'baixo'), ('fedorento', 'baixo'), ('fedorenta', 'baixo'),
            ('desajeitado', 'baixo'), ('desajeitada', 'baixo'), ('desastrado', 'baixo'),
            ('desastrada', 'baixo'), ('inocente', 'baixo'), ('desorganizado', 'baixo'),
            ('desorganizada', 'baixo'), ('bagunceiro', 'baixo'), ('bagunceira', 'baixo'),
            ('mau educado', 'baixo'), ('mal educado', 'baixo'), ('grosseiro', 'baixo'),
            ('grosseira', 'baixo'), ('maleducado', 'baixo'), ('mau carater', 'baixo'),
            ('sem carater', 'baixo'), ('fofoqueiro', 'baixo'), ('fofoqueira', 'baixo'),
            ('bisbilhoteiro', 'baixo'), ('chato de galocha', 'baixo'), ('pentelho', 'baixo'),
        ]

    def _load_dicionario_local(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dict_path = os.path.join(base_dir, 'data', 'local_dictionary.json')
        if os.path.exists(dict_path):
            with open(dict_path, 'r', encoding='utf-8') as f:
                self.dicionario_local = json.load(f)

    def _peso_nivel(self, nivel):
        pesos = {'critico': 45, 'alto': 25, 'medio': 15, 'baixo': 8, 'neutro': 0}
        return pesos.get(nivel, 10)

    def analisar(self, texto):
        texto_lower = texto.lower().strip()
        girias = []
        for g, info in self.dicionario_local.items():
            if g in texto_lower:
                girias.append({
                    'termo': g,
                    'significado': info.get('significado', ''),
                    'nivel': info.get('nivel', 'medio'),
                    'ofensivo': info.get('ofensivo', True)
                })

        encontradas = []
        for p, nivel in self.pa:
            if p in texto_lower:
                encontradas.append({'termo': p, 'nivel': nivel})

        conf = 5.0
        for g in girias:
            conf += self._peso_nivel(g['nivel'])
        for p in encontradas:
            conf += self._peso_nivel(p['nivel'])
        tem_critico = any(p['nivel'] == 'critico' for p in encontradas) or any(g['nivel'] == 'critico' for g in girias)
        if tem_critico:
            conf += 35
        caps = sum(1 for c in texto if c.isupper()) / max(len(texto), 1)
        if caps > 0.5:
            conf += 10
        excl = texto.count('!') + texto.count('?')
        conf += min(excl * 2, 10)
        conf = min(conf, 100)

        if conf >= 90:
            cls = 'Crítico'
        elif conf >= 70:
            cls = 'Ofensivo'
        elif conf >= 50:
            cls = 'Suspeito'
        else:
            cls = 'Neutro'

        nivel_geral = 'neutro'
        todos_niveis = [p['nivel'] for p in encontradas] + [g['nivel'] for g in girias]
        if todos_niveis:
            nivel_geral = max(todos_niveis, key=lambda n: self._peso_nivel(n))

        return {
            'classificacao': cls,
            'confianca': round(conf, 2),
            'girias': girias,
            'palavras': encontradas,
            'critico': conf >= 50,
            'nivel_geral': nivel_geral
        }

detector = Detector()
