# PDF-Suche (TF-IDF)
import os
import pickle
import re
from dataclasses import dataclass
from typing import List, Tuple
from PyPDF2 import PdfReader, errors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Container für Suchergebnisse
@dataclass
class PolicyHit:
    file: str
    page: int          
    score: float
    snippet: str
    orig_page: int    

CACHE_FILES = {
    "index": "index.pkl",
    "vectorizer": "vectorizer.pkl",
    "meta": "meta.pkl",
    "docs": "docs.pkl",
}

SNIPPET_MAX_CHARS = 900

# PDF-Seiten auslesen
def _read_pdf_pages(path: str) -> List[str]:
    pages = []
    try:
        reader = PdfReader(path)
        for p in reader.pages:
            try:
                text = p.extract_text()
                if text and len(text.strip()) > 30:
                    pages.append(text)
                else:
                    pages.append("")
            except Exception:
                pages.append("")
    except errors.PdfReadError:
        print(f"⚠️ {path} konnte nicht gelesen werden.")
    return pages

# PDF-Bestand aufbauen
def build_corpus(policy_dir: str) -> Tuple[List[str], List[Tuple[str,int]]]:
    docs = []; meta = []
    for fn in os.listdir(policy_dir):
        if not fn.lower().endswith(".pdf"):
            continue
        pages = _read_pdf_pages(os.path.join(policy_dir, fn))
        for i, txt in enumerate(pages): 
            docs.append(txt or "")
            meta.append((fn, i+1))
    return docs, meta

def _normalize_text(s: str) -> str:
    s = (s or "").replace("\u00ad", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _keywords_from_query(q: str) -> List[str]:
    toks = re.findall(r"[A-Za-zÄÖÜäöüß0-9\-]{4,}", (q or "").lower())
    out = []
    for t in toks:
        if t not in out:
            out.append(t)
    return out[:10]

# Hauptklasse für Richtlinien-Suche
class PolicySearch:
    def __init__(self, policy_dir: str):
        self.policy_dir = policy_dir
        self.docs: List[str] = []
        self.meta: List[Tuple[str, int]] = []
        self.vectorizer = None
        self.X = None
        self._load_or_build()

    def _cache_paths(self):
        return {k: os.path.join(self.policy_dir, v) for k, v in CACHE_FILES.items()}

    # Index laden oder neu erstellen
    def _load_or_build(self):
        os.makedirs(self.policy_dir, exist_ok=True)
        paths = self._cache_paths()
        if all(os.path.exists(p) for p in paths.values()):
            try:
                with open(paths["index"], "rb") as f: self.X = pickle.load(f)
                with open(paths["vectorizer"], "rb") as f: self.vectorizer = pickle.load(f)
                with open(paths["meta"], "rb") as f: self.meta = pickle.load(f)
                with open(paths["docs"], "rb") as f: self.docs = pickle.load(f)
                return
            except Exception as e:
                pass

        self.docs, self.meta = build_corpus(self.policy_dir)
        if not self.docs:
            return

        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_df=0.95,
            min_df=1,
            lowercase=True
        )
        self.X = self.vectorizer.fit_transform(self.docs)

        with open(paths["index"], "wb") as f: pickle.dump(self.X, f)
        with open(paths["vectorizer"], "wb") as f: pickle.dump(self.vectorizer, f)
        with open(paths["meta"], "wb") as f: pickle.dump(self.meta, f)
        with open(paths["docs"], "wb") as f: pickle.dump(self.docs, f)

    def rebuild(self):
        paths = self._cache_paths()
        for p in paths.values():
            if os.path.exists(p):
                os.remove(p)
        self._load_or_build()

    def _page_text(self, file: str, page: int) -> str:
        path = os.path.join(self.policy_dir, file)
        try:
            reader = PdfReader(path)
            idx = max(0, min(len(reader.pages)-1, page-1))
            raw = reader.pages[idx].extract_text() or ""
            return _normalize_text(raw)
        except Exception:
            return ""

    def _best_matching_page_with_snippet(self, file: str, page: int, query: str) -> Tuple[int, str]:
        kws = _keywords_from_query(query)
        candidates = [page]
        if page > 1: candidates.append(page-1)
        candidates.append(page+1)

        for p in candidates:
            txt = self._page_text(file, p)
            if not txt:
                continue
            if not kws or any(k in txt.lower() for k in kws):
                snippet = txt[:SNIPPET_MAX_CHARS]
                return p, snippet

        txt = self._page_text(file, page)
        return page, txt[:SNIPPET_MAX_CHARS] if txt else ""

    # Suche ausführen
    def search(self, query: str, k: int = 7) -> List[PolicyHit]:
        if self.vectorizer is None or self.X is None or self.X.shape[0] == 0:
            return []
        qv = self.vectorizer.transform([query])
        sims = linear_kernel(qv, self.X).ravel()
        idxs = sims.argsort()[::-1][:k]

        hits: List[PolicyHit] = []
        for i in idxs:
            if i < 0 or i >= len(self.meta):
                continue
            file, page = self.meta[i]
            ver_page, snippet = self._best_matching_page_with_snippet(file, page, query)
            hits.append(PolicyHit(
                file=file,
                page=ver_page,
                score=float(sims[i]),
                snippet=_normalize_text(snippet),
                orig_page=page
            ))
        return hits
    
    def list_files(self) -> List[str]:
        return sorted(list({fn for fn, _ in self.meta}))
