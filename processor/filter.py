"""
filter.py
Filtra os artigos coletados com base em palavras-chave relevantes.
Artigos que passam no filtro recebem status 'filtered'.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"

# Palavras-chave que indicam relevância para o nicho de IA
KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "large language model", "llm", "gpt", "claude", "gemini", "mistral",
    "open source", "chatgpt", "generative ai", "neural network",
    "ai model", "ai tool", "automation", "robotics", "chatbot"
]


def filter_articles():
    """Marca artigos relevantes com status 'filtered'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM articles WHERE status = 'raw'")
    articles = cursor.fetchall()

    approved = 0
    rejected = 0

    for article_id, title, content in articles:
        text = f"{title} {content}".lower()
        is_relevant = any(kw in text for kw in KEYWORDS)

        if is_relevant:
            cursor.execute(
                "UPDATE articles SET status = 'filtered' WHERE id = ?",
                (article_id,)
            )
            approved += 1
        else:
            cursor.execute(
                "UPDATE articles SET status = 'rejected' WHERE id = ?",
                (article_id,)
            )
            rejected += 1

    conn.commit()
    conn.close()
    print(f"✅ Filtro concluído: {approved} aprovados, {rejected} rejeitados.")


if __name__ == "__main__":
    filter_articles()
