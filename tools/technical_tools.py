
from pathlib import Path

import chromadb
import ollama


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge_base" / "technical_faq.txt"
VECTOR_DB_PATH = PROJECT_ROOT / "memory" / "chroma_db"

# Local embedding model
EMBEDDING_MODEL = "nomic-embed-text"

# Retrieval configuration
COLLECTION_NAME = "technical_faq"
TOP_K = 3
MIN_SIMILARITY = 0.60


def _load_articles() -> list[dict]:
    """Read and split the technical FAQ into individual articles."""

    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(
            f"Technical knowledge base not found: {KNOWLEDGE_BASE_PATH}"
        )

    content = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    sections = content.split("ARTICLE ")

    articles = []

    for index, section in enumerate(sections):
        section = section.strip()

        if not section:
            continue

        lines = section.splitlines()
        title = lines[0].strip()

        articles.append({
            "id": str(index),
            "title": title,
            "content": section
        })

    return articles


def _get_collection():
    """Create or retrieve the persistent ChromaDB collection."""

    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    return collection


def _ensure_index(collection, articles: list[dict]):
    """Create the vector index or refresh it when FAQ content changes."""

    existing = collection.get(include=["documents"])

    existing_ids = existing.get("ids", [])
    existing_documents = existing.get("documents") or []

    expected_ids = [article["id"] for article in articles]
    expected_documents = [article["content"] for article in articles]

    # Avoid regenerating embeddings when the knowledge base is unchanged.
    if (
        existing_ids == expected_ids
        and existing_documents == expected_documents
    ):
        return

    # Rebuild the collection when the FAQ has changed.
    if existing_ids:
        collection.delete(ids=existing_ids)

    if not articles:
        return

    documents = [article["content"] for article in articles]

    embedding_response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=documents
    )

    embeddings = embedding_response["embeddings"]

    collection.upsert(
        ids=expected_ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=[
            {
                "title": article["title"],
                "source": "technical_faq.txt"
            }
            for article in articles
        ]
    )


def search_technical_knowledge(query: str) -> dict:
    """
    Retrieve relevant technical FAQ articles using
    Ollama embeddings and ChromaDB vector similarity.
    """

    if not query or not query.strip():
        return {"found": False, "results": []}

    articles = _load_articles()
    collection = _get_collection()

    _ensure_index(collection, articles)

    if collection.count() == 0:
        return {"found": False, "results": []}

    query_response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=query
    )

    query_embedding = query_response["embeddings"][0]

    retrieved = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(TOP_K, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    results = []

    documents = retrieved["documents"][0]
    metadatas = retrieved["metadatas"][0]
    distances = retrieved["distances"][0]

    for document, metadata, distance in zip(
        documents, metadatas, distances
    ):
        similarity = 1.0 - distance

        if similarity < MIN_SIMILARITY:
            continue

        results.append({
            "content": document,
            "title": metadata["title"],
            "source": metadata["source"],
            "score": round(similarity, 4)
        })

    return {
        "found": len(results) > 0,
        "results": results
    }


def validate_technical_solution(solution: str) -> dict:
    """Check whether a proposed solution contains useful instructions."""

    if not solution or len(solution.strip()) < 15:
        return {
            "valid": False,
            "reason": "Technical solution is incomplete."
        }

    return {
        "valid": True,
        "reason": "Technical solution contains sufficient information."
    }


def check_error_severity(message: str) -> dict:
    """Identify potentially serious technical errors."""

    text = message.lower()

    critical_keywords = [
        "data loss",
        "security breach",
        "database corruption",
        "system compromised"
    ]

    matched = [
        word for word in critical_keywords
        if word in text
    ]

    if matched:
        return {
            "severity": "high",
            "requires_human": True,
            "reason": f"Critical issue detected: {matched}"
        }

    return {
        "severity": "normal",
        "requires_human": False,
        "reason": "No critical technical keywords detected."
    }
