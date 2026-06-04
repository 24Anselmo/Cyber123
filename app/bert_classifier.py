import numpy as np


class BertDetector:
    CLASSES = ['Crítico', 'Ofensivo', 'Suspeito', 'Neutro']

    LABEL_EXEMPLOS = {
        'Crítico': [
            'vou te matar seu animal',
            'vou te assassinar',
            'vou te cortar em pedaços',
            'vai morrer desgraçado',
            'vou acabar com sua vida',
            'merece morrer seu lixo',
        ],
        'Ofensivo': [
            'filho da puta seu idiota',
            'vai se foder seu estupido',
            'caralho que merda',
            'seu otario desgraçado',
            'burro do caralho vai tomar no cu',
        ],
        'Suspeito': [
            'cala a boca seu burro',
            'nao enche o saco',
            'para de ser chato',
            'ja chega de voce seu trouxa',
        ],
        'Neutro': [
            'bom dia como esta tudo bem',
            'obrigado pela sua ajuda',
            'que belo trabalho em equipe',
            'concordo plenamente com voce',
            'gostei muito do seu post',
        ],
    }

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._label_embs = None
        self._loaded = False

    def _carregar(self):
        if self._loaded:
            return True
        try:
            from transformers import AutoTokenizer, AutoModel
            self._tokenizer = AutoTokenizer.from_pretrained(
                "distilbert-base-multilingual-cased"
            )
            self._model = AutoModel.from_pretrained(
                "distilbert-base-multilingual-cased"
            )
            self._label_embs = self._precomputar_label_embeddings()
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False

    def _embedding(self, texto):
        inputs = self._tokenizer(
            texto, return_tensors="pt", truncation=True, padding=True, max_length=128
        )
        outputs = self._model(**inputs)
        mask = inputs['attention_mask'].unsqueeze(-1).float()
        masked = outputs.last_hidden_state * mask
        summed = masked.sum(dim=1)
        counts = mask.sum(dim=1)
        emb = (summed / counts).detach().numpy()
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb

    def _embedding_medio(self, exemplos):
        embs = [self._embedding(ex) for ex in exemplos]
        return np.mean(embs, axis=0)

    def _precomputar_label_embeddings(self):
        return {
            nome: self._embedding_medio(exemplos)
            for nome, exemplos in self.LABEL_EXEMPLOS.items()
        }

    def classificar(self, texto):
        if not self._carregar():
            return {
                'classificacao': 'Neutro',
                'confianca': 0.0,
                'probabilidades': {c: 0.25 for c in self.CLASSES},
            }

        text_emb = self._embedding(texto)
        scores = {}
        for cls_name in self.CLASSES:
            sim = float(np.dot(text_emb, self._label_embs[cls_name].T)[0, 0])
            scores[cls_name] = max(sim, 0)

        exp = np.exp(list(scores.values()))
        total = exp.sum()
        probs = exp / total if total > 0 else np.ones(len(scores)) / len(scores)
        prob_dict = dict(zip(self.CLASSES, [round(float(v), 4) for v in probs]))
        best = max(self.CLASSES, key=lambda c: prob_dict[c])

        return {
            'classificacao': best,
            'confianca': round(prob_dict[best] * 100, 2),
            'probabilidades': prob_dict,
        }
