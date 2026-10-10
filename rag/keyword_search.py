"""BM25 keyword search over the indexed scripture chunks.

Complements the FAISS embedding search: embeddings capture meaning, while
BM25 rewards exact terms, which matters for Sanskrit words and names
(sthita-prajña, brahma-bhūta, Kurukṣetra) that a general English embedding
model represents poorly.
"""

import math
import re
import unicodedata
from collections import Counter, defaultdict

import numpy as np


# Okapi BM25 parameters (standard defaults).
K1 = 1.5
B = 0.75

STOPWORDS = frozenset("""
a about above after again against all am an and any are as at be because been
before being below between both but by can could did do does doing down during
each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just me more most my myself no
nor not now of off on once only or other our ours ourselves out over own same
she should so some such than that the their theirs them themselves then there
these they this those through to too under until up very was we were what when
where which while who whom why will with would you your yours yourself
yourselves also unto thus one may shall upon thee thou thy o
explain tell please describe mean meaning bhagavad gita verse verses chapter
""".split())

# Common English spellings of Sanskrit names, mapped to the folded forms used
# in Bhagavad-gita As It Is (e.g. "Kṛṣṇa" folds to "krsna").
ALIASES = {
    "krishna": "krsna", "krushna": "krsna", "vishnu": "visnu",
    "rishi": "rsi", "rishis": "rsis", "dhritarashtra": "dhrtarastra",
    "kurukshetra": "kuruksetra", "kshatriya": "ksatriya", "kshatriyas": "ksatriyas",
    "sanyasa": "sannyasa", "shloka": "sloka", "shiva": "siva",
}

_TOKEN = re.compile(r"[a-z0-9]+")


def fold(text):
    """Lowercase and strip diacritics: 'Kṛṣṇa' -> 'krsna'."""
    decomposed = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def tokenize(text):
    tokens = []
    for token in _TOKEN.findall(fold(text)):
        token = ALIASES.get(token, token)
        # "sh" is a common English rendering of ś/ṣ, which fold to plain "s".
        token = token.replace("sh", "s")
        if len(token) > 1 and token not in STOPWORDS:
            tokens.append(token)
    return tokens


class BM25Index:
    def __init__(self, texts):
        self.size = len(texts)
        self.postings = defaultdict(list)  # term -> [(doc index, term frequency)]
        lengths = np.zeros(self.size, dtype=np.float32)
        for doc_index, text in enumerate(texts):
            counts = Counter(tokenize(text))
            lengths[doc_index] = sum(counts.values())
            for term, frequency in counts.items():
                self.postings[term].append((doc_index, frequency))
        average = float(lengths.mean()) if self.size else 0.0
        self.length_norm = K1 * (1 - B + B * lengths / (average or 1.0))
        self.idf = {
            term: math.log(1 + (self.size - len(docs) + 0.5) / (len(docs) + 0.5))
            for term, docs in self.postings.items()
        }

    def scores(self, query):
        scores = np.zeros(self.size, dtype=np.float32)
        for term in set(tokenize(query)):
            postings = self.postings.get(term)
            if not postings:
                continue
            idf = self.idf[term]
            for doc_index, frequency in postings:
                scores[doc_index] += idf * frequency * (K1 + 1) / (
                    frequency + self.length_norm[doc_index]
                )
        return scores

    def search(self, query, limit):
        """Return [(doc index, score)] for the best matches with a positive score."""
        scores = self.scores(query)
        candidates = np.flatnonzero(scores > 0)
        if candidates.size == 0:
            return []
        top = candidates[np.argsort(-scores[candidates])[:limit]]
        return [(int(i), float(scores[i])) for i in top]


def document_text(document):
    """Searchable text for one indexed chunk.

    Translation chunks also include the word-for-word glossary, which is where
    Sanskrit terms appear alongside their English meanings.
    """
    if not isinstance(document, dict):
        return str(document or "")
    parts = [document.get("text") or ""]
    if document.get("content_type") == "translation":
        glossary = document.get("word_for_word")
        if isinstance(glossary, str):
            parts.append(glossary)
    return "\n".join(parts)
