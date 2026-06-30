import re
import unicodedata

try:
    from nltk.stem import RSLPStemmer, PorterStemmer
    from nltk.corpus import stopwords
    _nltk_available = True
except ImportError:
    _nltk_available = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 42
    _langdetect_available = True
except ImportError:
    _langdetect_available = False

try:
    from spacy.lang.pt import Portuguese as PtNLP
    from spacy.lang.en import English as EnNLP
    _spacy_available = True
except ImportError:
    _spacy_available = False

DIALETOS_ANGOLA = {
    'umbundu': ['ochilume', 'olamba', 'onjango', 'kumbu', 'ukuale', 'pandua', 'osoma', 'ekamba'],
    'kimbundu': ['kudia', 'kuzola', 'kutombela', 'ngola', 'cassule', 'ngana muene'],
    'cokwe': ['mwangana wa kuata'],
    'cabinda': ['buta', 'nkanda'],
    'kuando': ['kuteka'],
    'luanda_slang': ['banga', 'musseque', 'calombeta', 'kamba yange', 'gata', 'kota dia kota'],
}

LINGUAS_ANGOLA = ['pt', 'pt-ao', 'umbundu', 'kimbundu', 'cokwe']


def normalizar_texto(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


class AnalisadorNLP:
    def __init__(self):
        self._stemmer_pt = None
        self._stemmer_en = None
        self._stopwords_pt = set()
        self._stopwords_en = set()
        self._nlp_pt = None
        self._nlp_en = None
        self._init()

    def _init(self):
        if _nltk_available:
            try:
                self._stemmer_pt = RSLPStemmer()
            except Exception:
                pass
            try:
                self._stemmer_en = PorterStemmer()
            except Exception:
                pass
            try:
                self._stopwords_pt = set(stopwords.words('portuguese'))
            except Exception:
                pass
            try:
                self._stopwords_en = set(stopwords.words('english'))
            except Exception:
                pass
        if _spacy_available:
            try:
                self._nlp_pt = PtNLP()
            except Exception:
                pass
            try:
                self._nlp_en = EnNLP()
            except Exception:
                pass

    def detetar_idioma(self, texto):
        if not _langdetect_available or not texto.strip():
            return 'pt'
        try:
            lang = detect(texto)
            if lang in ['pt', 'pt-br', 'pt-pt']:
                return 'pt'
            return lang
        except Exception:
            return 'pt'

    def detetar_dialeto_angolano(self, texto):
        texto_lower = texto.lower()
        for dialeto, palavras in DIALETOS_ANGOLA.items():
            for palavra in palavras:
                if palavra in texto_lower:
                    return dialeto
        return None

    def stemming(self, texto):
        if not _nltk_available:
            return texto
        palavras = texto.split()
        resultado = []
        for p in palavras:
            if self._stemmer_pt:
                try:
                    p = self._stemmer_pt.stem(p)
                except Exception:
                    pass
            resultado.append(p)
        return ' '.join(resultado)

    def lematizar(self, texto, lingua='pt'):
        nlp = self._nlp_pt if lingua == 'pt' else self._nlp_en
        if nlp is None or not _spacy_available:
            return texto
        try:
            doc = nlp(texto)
            return ' '.join([token.lemma_ for token in doc])
        except Exception:
            return texto

    def remover_stopwords(self, texto, lingua='pt'):
        stop = self._stopwords_pt if lingua == 'pt' else self._stopwords_en
        if not stop:
            return texto
        palavras = texto.split()
        return ' '.join([p for p in palavras if p not in stop])

    def analisar(self, texto):
        idioma = self.detetar_idioma(texto)
        dialeto = self.detetar_dialeto_angolano(texto)
        normalizado = normalizar_texto(texto)
        stemmed = self.stemming(normalizado)
        lematizado = self.lematizar(texto, idioma)
        sem_stop = self.remover_stopwords(normalizado, idioma)
        return {
            'idioma': idioma,
            'dialeto_angolano': dialeto,
            'normalizado': normalizado,
            'stemmed': stemmed,
            'lematizado': lematizado,
            'sem_stopwords': sem_stop,
        }
