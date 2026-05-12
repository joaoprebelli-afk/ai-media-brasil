"""
rss_collector.py
================
Coleta posts de feeds RSS de grandes empresas de IA e salva no SQLite.

Fontes monitoradas:
  - OpenAI Blog
  - Anthropic News
  - NVIDIA Blog (IA)
  - Google AI Blog

Como rodar:
  1. pip install feedparser python-dotenv
  2. python collector/rss_collector.py

Resultado:
  → Artigos salvos em data/articles.db
  → Duplicatas são ignoradas automaticamente
"""

import feedparser
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent

# ATENÇÃO WINDOWS: SQLite não funciona bem em pastas sincronizadas
# (OneDrive, Google Drive). Se der erro de "disk I/O", mova o projeto
# para C:\projetos\ ou similar.
DB_PATH = BASE_DIR / "data" / "articles.db"

FEEDS = [
    {
        "name":    "OpenAI Blog",
        "url":     "https://openai.com/blog/rss.xml",
        "company": "openai",
    },
    {
        "name":    "Anthropic News",
        "url":     "https://www.anthropic.com/rss.xml",
        "company": "anthropic",
    },
    {
        "name":    "NVIDIA Blog - AI",
        "url":     "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
        "company": "nvidia",
    },
    {
        "name":    "Google AI Blog",
        "url":     "https://blog.google/technology/ai/rss/",
        "company": "google",
    },
]

# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def init_db(conn: sqlite3.Connection):
    """
    Cria a tabela 'articles' se não existir.

    Colunas:
      id           → hash MD5 da URL (chave única, evita duplicatas)
      title        → título do post
      url          → link original
      summary      → descrição/resumo (pode vir vazio)
      source       → nome do feed (ex: "OpenAI Blog")
      company      → empresa (ex: "openai")
      published_at → data de publicação em formato ISO
      status       → controla o pipeline:
                       raw → filtered → scored → generated → published
      collected_at → quando nosso sistema coletou
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id           TEXT PRIMARY KEY,
            title        TEXT NOT NULL,
            url          TEXT NOT NULL,
            summary      TEXT,
            source       TEXT,
            company      TEXT,
            published_at TEXT,
            status       TEXT DEFAULT 'raw',
            collected_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


# ─────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────

def make_id(url: str) -> str:
    """ID único baseado na URL — mesmo artigo nunca entra duas vezes."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def parse_date(entry) -> str:
    """Extrai a data do entry RSS. Usa 'agora' como fallback."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6]).isoformat()
    return datetime.now().isoformat()


def already_exists(conn: sqlite3.Connection, article_id: str) -> bool:
    """Retorna True se o artigo já está no banco."""
    return conn.execute(
        "SELECT 1 FROM articles WHERE id = ?", (article_id,)
    ).fetchone() is not None


# ─────────────────────────────────────────────
# COLETA
# ─────────────────────────────────────────────

def collect_feed(conn: sqlite3.Connection, feed_config: dict) -> int:
    """
    Faz o parse de um feed RSS e insere artigos novos.
    Retorna a quantidade de artigos novos salvos.
    """
    name    = feed_config["name"]
    url     = feed_config["url"]
    company = feed_config["company"]

    print(f"\n📡 {name}")

    feed = feedparser.parse(url)

    if not feed.entries:
        msg = getattr(feed, "bozo_exception", "resposta vazia")
        print(f"   ⚠️  Sem dados — {msg}")
        return 0

    novos = 0
    for entry in feed.entries:
        link = entry.get("link", "").strip()
        if not link:
            continue

        article_id = make_id(link)

        # ← DEDUPLICAÇÃO: pula se já existe
        if already_exists(conn, article_id):
            continue

        title   = entry.get("title", "Sem título").strip()
        summary = entry.get("summary", "").strip()
        pub     = parse_date(entry)

        conn.execute("""
            INSERT INTO articles (id, title, url, summary, source, company, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (article_id, title, link, summary, name, company, pub))

        print(f"   ✅ {title[:70]}")
        novos += 1

    conn.commit()

    if novos == 0:
        print(f"   ℹ️  Sem posts novos ({len(feed.entries)} verificados)")

    return novos


# ─────────────────────────────────────────────
# RESUMO
# ─────────────────────────────────────────────

def show_summary(conn: sqlite3.Connection):
    """Exibe quantos artigos temos por empresa."""
    print("\n📊 BANCO DE DADOS:")
    rows = conn.execute("""
        SELECT company, COUNT(*) FROM articles GROUP BY company ORDER BY COUNT(*) DESC
    """).fetchall()

    for company, total in rows:
        print(f"   {company:<15} → {total} artigos")

    total_geral = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"\n   Total geral : {total_geral} artigos")
    print(f"   Arquivo     : {DB_PATH}\n")


# ─────────────────────────────────────────────
# ENTRADA PRINCIPAL
# ─────────────────────────────────────────────

def run():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("🤖  RSS COLLECTOR — Blog de IA em Português")
    print("=" * 55)

    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    total_novos = 0
    for feed_config in FEEDS:
        total_novos += collect_feed(conn, feed_config)

    print("\n" + "=" * 55)
    print(f"✅  Coleta concluída! {total_novos} novo(s) artigo(s) salvos.")
    show_summary(conn)
    conn.close()


if __name__ == "__main__":
    run()
