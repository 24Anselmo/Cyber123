from app.detector import detector


def test_analisar_structure():
    result = detector.analisar("Bom dia pessoal")
    assert isinstance(result, dict)
    assert 'classificacao' in result
    assert 'confianca' in result
    assert 'girias' in result
    assert 'palavras' in result
    assert 'nivel_geral' in result
    assert 'critico' in result


def test_neutral_text():
    result = detector.analisar("Bom dia pessoal")
    assert result['classificacao'] == 'Neutro'
    assert result['confianca'] == 0
    assert result['critico'] is False
    assert result['nivel_geral'] == 'neutro'


def test_offensive_text():
    result = detector.analisar("Você é um idiota")
    assert result['confianca'] > 0
    palavras_encontradas = [p['termo'] for p in result['palavras']]
    assert 'idiota' in palavras_encontradas
    assert result['nivel_geral'] == 'medio'


def test_critical_girias():
    result = detector.analisar("mucolesse sonhi curi atxu essue")
    assert result['classificacao'] in ('Crítico', 'Ofensivo')
    assert result['confianca'] >= 45
    assert result['critico'] is True
    girias_encontradas = [g['termo'] for g in result['girias']]
    assert 'mucolesse sonhi curi atxu essue' in girias_encontradas


def test_empty_text():
    result = detector.analisar("")
    assert result['classificacao'] == 'Neutro'
    assert result['confianca'] == 0
    assert result['critico'] is False
