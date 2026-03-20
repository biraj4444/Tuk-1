"""
db.py — Dual-mode database: MongoDB Atlas (Render) or JSON file (Termux).
- On Render:  set MONGO_URI env var → uses MongoDB Atlas automatically
- On Termux:  no MONGO_URI → falls back to local db.json file
All public methods are identical either way, so no other file needs changing.
"""
import json, os, uuid, threading
from datetime import datetime

# ── Detect mode ──────────────────────────────────────────────────────────────
MONGO_URI = os.getenv('MONGO_URI', '')
USE_MONGO  = bool(MONGO_URI)

_lock = threading.Lock()

# ── MongoDB setup ─────────────────────────────────────────────────────────────
if USE_MONGO:
    from pymongo import MongoClient
    _client = MongoClient(MONGO_URI)
    _db     = _client.get_database('etuktuk')

# ── JSON setup ────────────────────────────────────────────────────────────────
else:
    _BASE    = os.path.join(os.path.dirname(__file__), '..')
    DB_PATH  = os.path.join(_BASE, 'db.json')
    _DEFAULT = {
        "users": [], "drivers": [], "admins": [],
        "bookings": [], "zones": [], "payments": [], "sessions": [],
    }

    def _load() -> dict:
        if not os.path.exists(DB_PATH):
            _save(_DEFAULT.copy())
            return _DEFAULT.copy()
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in _DEFAULT.items():
            data.setdefault(k, v)
        return data

    def _save(data: dict):
        dirpath = os.path.dirname(DB_PATH)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _now():
    return datetime.utcnow().isoformat()

def _new_id():
    return str(uuid.uuid4())

def _clean(doc):
    if doc and '_id' in doc:
        doc = dict(doc)
        doc['_id'] = str(doc['_id'])
    return doc

# ── Public API ────────────────────────────────────────────────────────────────

def find(collection: str, query: dict = None):
    if USE_MONGO:
        return [_clean(d) for d in _db[collection].find(query or {})]
    else:
        with _lock:
            docs = _load().get(collection, [])
        if not query:
            return docs
        return [d for d in docs if all(d.get(k) == v for k, v in query.items())]

def find_one(collection: str, query: dict = None):
    if USE_MONGO:
        doc = _db[collection].find_one(query or {})
        return _clean(doc) if doc else None
    else:
        results = find(collection, query)
        return results[0] if results else None

def insert_one(collection: str, document: dict) -> dict:
    document = {"_id": _new_id(), "created_at": _now(), "updated_at": _now(), **document}
    if USE_MONGO:
        _db[collection].insert_one(dict(document))
        document['_id'] = str(document['_id'])
    else:
        with _lock:
            data = _load()
            data[collection].append(document)
            _save(data)
    return document

def update_one(collection: str, query: dict, updates: dict) -> bool:
    updates['updated_at'] = _now()
    if USE_MONGO:
        result = _db[collection].update_one(query, {'$set': updates})
        return result.matched_count > 0
    else:
        with _lock:
            data = _load()
            for doc in data[collection]:
                if all(doc.get(k) == v for k, v in query.items()):
                    doc.update(updates)
                    _save(data)
                    return True
        return False

def delete_one(collection: str, query: dict) -> bool:
    if USE_MONGO:
        result = _db[collection].delete_one(query)
        return result.deleted_count > 0
    else:
        with _lock:
            data = _load()
            original = len(data[collection])
            data[collection] = [d for d in data[collection] if not all(d.get(k) == v for k, v in query.items())]
            if len(data[collection]) < original:
                _save(data)
                return True
        return False

def count(collection: str, query: dict = None) -> int:
    if USE_MONGO:
        return _db[collection].count_documents(query or {})
    else:
        return len(find(collection, query))

def get_all_collections() -> dict:
    if USE_MONGO:
        result = {}
        for col in ['users','drivers','admins','bookings','zones','payments','sessions']:
            result[col] = [_clean(d) for d in _db[col].find({})]
        return result
    else:
        with _lock:
            return _load()
