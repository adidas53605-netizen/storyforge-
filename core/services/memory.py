import logging

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.Client(Settings(anonymized_telemetry=False))
    return _client


def _get_collection(story_id):
    client = _get_client()
    return client.get_or_create_collection(name=f"story_{story_id}")


def add_lore(story_id, text, lore_id=None):
    collection = _get_collection(story_id)
    doc_id = f"lore_{lore_id}" if lore_id else f"lore_{hash(text)}"
    collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[{"type": "lore"}],
    )


def add_character(story_id, name, psychology, speech_style, character_id=None):
    collection = _get_collection(story_id)
    doc_text = f"Character: {name}. Psychology: {psychology}. Speech style: {speech_style}."
    doc_id = f"char_{character_id}" if character_id else f"char_{hash(name)}"
    collection.upsert(
        ids=[doc_id],
        documents=[doc_text],
        metadatas=[{"type": "character", "name": name}],
    )


def retrieve_relevant(story_id, query, k=5):
    collection = _get_collection(story_id)
    if collection.count() == 0:
        return []
    actual_k = min(k, collection.count())
    results = collection.query(
        query_texts=[query],
        n_results=actual_k,
    )
    return results.get("documents", [[]])[0]
