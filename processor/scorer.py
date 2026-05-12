"""
scorer.py
Pontua os artigos filtrados por relevância e novidade.
Artigos com score alto são priorizados para geração de conteúdo.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"

# Palavras que aumentam a pontuação (temas quentes)
HIGH_VALUE_KEYWORDS = {
    "gpt": 3, "claude": 3, "gemini": 3, "llm": 2,
    "open source": 2, "launch": 2, "release": 2, "new model": 3,
    "breakthrough": 3, "billion": 1, "funding": 1, "agent": 2,
    "multimodal": 2, "agi": 3
}


def score_articles():
    """Pontua artigos com status 'filtered'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM articles WHERE status = 'filtered'")
    articles = cursor.fetchall()

    for article_id, title, content in articles:
        text = f"{title} {content}".lower()
        score = 0

        for keyword, value in HIGH_VALUE_KEYWORDS.items():
            if keyword in text:
                score += value

        cursor.execute(
            "UPDATE articles SET score = ?, status = 'scored' WHERE id = ?",
            (score, article_id)
        )

    conn.commit()
    conn.close()
    print(f"✅ {len(articles)} artigos pontuados.")


if __name__ == "__main__":
    score_articles()
