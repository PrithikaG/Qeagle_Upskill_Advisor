"""
Hybrid retrieval:
- BM25 (rank-bm25, in-memory over courses)
- MongoDB Atlas Vector Search (embeddings via HuggingFace)
- Cross-Encoder reranker (optional)
This replaces your placeholder hash-embedding and merges with your token-based logic.
"""
import os, json
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from pymongo import MongoClient
from pymongo.collection import Collection
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from sentence_transformers import CrossEncoder

from . import store

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER", "cross-encoder/ms-marco-MiniLM-L-6-v2")
MONGO_URI = os.getenv("MONGODB_ATLAS_URI")
DB_NAME = os.getenv("MONGODB_DB", "upskill")
COURSE_COLL = os.getenv("MONGODB_COURSES_COLL", "courses")
INDEX_NAME = os.getenv("MONGO_VECTOR_INDEX", "vector_index")


_client = MongoClient(MONGO_URI) if MONGO_URI else None
_db = _client[DB_NAME] if _client is not None else None
_courses_coll: Collection = _db[COURSE_COLL] if _db is not None else None

_embed = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
try:
    _ce = CrossEncoder(CROSS_ENCODER_MODEL)
except Exception:
    _ce = None

store_vs = MongoDBAtlasVectorSearch(
    collection=_courses_coll,
    embedding=_embed,
    index_name=INDEX_NAME,
    text_key="text"
)

def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in (s or "") if ch.isalnum() or ch.isspace()).strip()

def _course_text(c: Dict) -> str:
    return "\n".join([
        c.get("title", ""),
        "Skills: " + ", ".join(c.get("skills", []) or []),
        "Outcomes: " + ", ".join(c.get("outcomes", []) or []),
        "Prereq: " + ", ".join(c.get("prerequisites", []) or []),
        f"Level: {c.get('difficulty','')}"
    ])

def bootstrap_courses() -> bool:
    """Upsert courses w/ embeddings into Mongo if collection empty."""
    if _courses_coll is None:
        return False

    if _courses_coll.estimated_document_count() > 0:
        return True

    docs = []
    for c in store.COURSES:
        it = c.model_dump() if hasattr(c, "model_dump") else c.dict()
        txt = _course_text(it)
        emb = _embed.embed_query(txt)
        docs.append({
            "course_id": it["course_id"],
            "title": it["title"],
            "skills": it.get("skills", []),
            "difficulty": it.get("difficulty"),
            "duration_weeks": it.get("duration_weeks"),
            "prerequisites": it.get("prerequisites", []),
            "outcomes": it.get("outcomes", []),
            "text": txt,
            "embedding": emb
        })
    if docs:
        _courses_coll.insert_many(docs)
    return True

# --------- BM25 (in-memory) ----------
_tokenized = None
_bm25 = None

def _build_bm25_corpus() -> List[str]:
    return [_course_text(c.model_dump()) for c in store.COURSES]

def ensure_bm25():
    global _tokenized, _bm25
    if _bm25 is not None:
        return
    corpus = _build_bm25_corpus()
    _tokenized = [doc.lower().split() for doc in corpus]
    _bm25 = BM25Okapi(_tokenized)

def bm25_candidates(query: str, k: int = 20) -> List[Tuple[int, float]]:
    ensure_bm25()
    toks = query.lower().split()
    scores = _bm25.get_scores(toks)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [(i, float(scores[i])) for i in order]

def vector_candidates(query: str, k: int = 20) -> List[Tuple[int, float]]:
    # OLD (ok but make it explicit too): if not _courses_coll: return []
    if _courses_coll is None:
        return []

    store_vs = MongoDBAtlasVectorSearch(
        collection=_courses_coll,
        embedding=_embed,
        index_name="vector_index",
        text_key="text"
    )
    docs = store_vs.similarity_search_with_relevance_scores(query, k=k)
    id_to_idx = {c.course_id: i for i, c in enumerate(store.COURSES)}
    out: List[Tuple[int, float]] = []
    for d, s in docs:
        cid = (getattr(d, "metadata", None) or {}).get("course_id")
        if not cid:
            # fallback: match by title header
            header = (d.page_content or "").split("\n")[0]
            for c in store.COURSES:
                title = c.title if hasattr(c, "title") else c.get("title")
                if title == header:
                    cid = c.course_id if hasattr(c, "course_id") else c.get("course_id")
                    break
        if cid in id_to_idx:
            out.append((id_to_idx[cid], float(s)))
    return out

def hybrid(query: str, k: int = 20, w_bm25: float = 0.5, w_vec: float = 0.5) -> List[Tuple[int, float]]:
    bm = dict(bm25_candidates(query, k))
    vc = dict(vector_candidates(query, k))
    keys = set(bm) | set(vc)
    scores = {i: w_bm25*bm.get(i, 0.0) + w_vec*vc.get(i, 0.0) for i in keys}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return ranked

def rerank(query: str, idxs_and_scores: List[Tuple[int, float]], k: int = 10) -> List[int]:
    if not idxs_and_scores:
        return []
    if _ce is None:
        return [i for i, _ in idxs_and_scores[:k]]
    pairs = [(query, _course_text(store.COURSES[i].model_dump())) for i, _ in idxs_and_scores]
    ce_scores = _ce.predict(pairs)
    order = sorted(range(len(ce_scores)), key=lambda j: ce_scores[j], reverse=True)[:k]
    return [int(idxs_and_scores[j][0]) for j in order]