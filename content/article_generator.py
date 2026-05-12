"""
article_generator.py
Gera artigos em português a partir dos artigos mais bem pontuados.
Usa a API da Anthropic (Claude) para traduzir e reescrever o conteúdo.
"""

import sqlite3
import anthropic
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"
OUTPUT_DIR = Path(__file__).parent.parent / "content" / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_article(title: str, content: str, url: str) -> str:
    """Chama a API Claude para gerar artigo em português."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Você é um jornalista especializado em inteligência artificial escrevendo para brasileiros.

Com base nesta notícia em inglês, escreva um artigo em português brasileiro:

TÍTULO ORIGINAL: {title}
CONTEÚDO: {content}
FONTE: {url}

Escreva um artigo com:
- Título chamativo em português
- Introdução de 2 parágrafos explicando o que aconteceu
- Seção "Por que isso importa?" com impacto para brasileiros
- Conclusão com perspectivas futuras
- Tom: informativo mas acessível, sem jargão excessivo

Formato: Markdown"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def run():
    """Pega o artigo de maior score e gera conteúdo em português."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, content, url, source
        FROM articles
        WHERE status = 'scored'
        ORDER BY score DESC
        LIMIT 1
    """)
    row = cursor.fetchone()

    if not row:
        print("Nenhum artigo disponível para geração.")
        return

    article_id, title, content, url, source = row

    print(f"Gerando artigo para: {title}")
    article_pt = generate_article(title, content, url)

    # Salva como arquivo markdown
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"artigo_{timestamp}.md"
    filename.write_text(article_pt, encoding="utf-8")

    # Atualiza status no banco
    cursor.execute("UPDATE articles SET status = 'generated' WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()

    print(f"✅ Artigo salvo em: {filename}")


if __name__ == "__main__":
    run()
