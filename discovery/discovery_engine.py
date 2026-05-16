"""
discovery_engine.py
===================
Descobre automaticamente notícias de IA relevantes sem intervenção manual.

Fontes monitoradas:
  - RSS feeds (9 blogs oficiais de empresas de IA)
  - Hacker News Top Stories (Firebase API)
  - Hacker News AI Search (Algolia API)
  - GitHub Trending AI repositories

Virality Score (0.0 → 1.0):
  recency      30%  — quão recente é a notícia
  authority    25%  — peso da fonte (blog oficial > HN > GitHub)
  ai_relevance 25%  — presença de keywords de IA no título
  engagement   20%  — upvotes, comentários, stars (normalizado)
  Boost +20%        — se contém sinal de alto impacto (launch, release…)

Como rodar:
  python discovery/discovery_engine.py              # descoberta completa
  python discovery/discovery_engine.py --fonte rss  # só RSS
  python discovery/discovery_engine.py --fonte hn   # só Hacker News
  python discovery/discovery_engine.py --listar     # top discoveries salvos
  python discovery/discovery_engine.py --dry-run    # preview sem salvar
  python discovery/discovery_engine.py --enviar     # envia ao articles.db

Output:
  data/discoveries.db   — banco de dados de discoveries
  relatório TOP DISCOVERIES TODAY no terminal
"""

import hashlib
import json
import logging
import math
import os
import sqlite3
import time
import argparse
import calendar
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

BASE_DIR     = Path(__file__).parent.parent
DB_PATH      = BASE_DIR / "data" / "discoveries.db"
ARTICLES_DB  = BASE_DIR / "data" / "articles.db"
LOG_DIR      = BASE_DIR / "automation" / "logs"

VIRALITY_MIN  = 0.30   # score mínimo para salvar no banco
SEND_MIN      = 0.50   # score mínimo para enviar ao processor
REQUEST_DELAY = 1.2    # segundos entre requests (rate limiting educado)
TIMEOUT       = 12     # timeout de cada request HTTP

USER_AGENT = "AIBlogDiscoveryBot/1.0 (research; contact via github)"

# ── RSS: Blogs oficiais de empresas de IA ─────────────────────────────────────
RSS_SOURCES = [
    {"nome": "OpenAI Blog",       "url": "https://openai.com/blog/rss.xml",                              "authority": 1.00},
    {"nome": "Anthropic Blog",    "url": "https://www.anthropic.com/rss.xml",                             "authority": 1.00},
    {"nome": "Google AI Blog",    "url": "https://blog.google/technology/ai/rss/",                        "authority": 0.95},
    {"nome": "DeepMind Blog",     "url": "https://deepmind.google/blog/rss.xml",                          "authority": 0.92},
    {"nome": "NVIDIA Blog",       "url": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",    "authority": 0.88},
    {"nome": "Meta AI Blog",      "url": "https://ai.meta.com/blog/rss/",                                 "authority": 0.90},
    {"nome": "HuggingFace Blog",  "url": "https://huggingface.co/blog/feed.xml",                         "authority": 0.88},
    {"nome": "Mistral AI",        "url": "https://mistral.ai/news/rss.xml",                               "authority": 0.82},
    {"nome": "Cohere Blog",       "url": "https://cohere.com/blog/rss",                                   "authority": 0.78},
]

# ── Keywords de IA para relevância ───────────────────────────────────────────
AI_KEYWORDS = [
    "gpt", "claude", "gemini", "llm", "llms", "ai", "artificial intelligence",
    "machine learning", "deep learning", "neural", "transformer", "diffusion",
    "anthropic", "openai", "google deepmind", "deepmind", "meta ai", "mistral",
    "nvidia", "huggingface", "hugging face", "cohere", "xai", "elon musk",
    "agent", "agents", "agi", "reasoning", "multimodal", "vision language",
    "fine-tuning", "finetuning", "inference", "benchmark", "model",
    "open source", "open-source", "api", "context window", "token", "tokens",
    "robotics", "automation", "copilot", "chatbot", "retrieval", "rag",
]

# ── Sinais de alto impacto (boost +20%) ──────────────────────────────────────
HIGH_IMPACT_SIGNALS = [
    "launch", "launches", "launched", "release", "released", "announces",
    "announced", "partnership", "partners", "acquires", "acquisition",
    "raises", "funding", "billion", "million", "breakthrough", "beats",
    "surpasses", "outperforms", "open source", "free", "new model",
    "lança", "parceria", "anuncia", "adquire", "captação", "supera",
    "primeiro", "gratuito", "open weights",
]


# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id               TEXT PRIMARY KEY,
            titulo           TEXT NOT NULL,
            url              TEXT NOT NULL,
            fonte            TEXT NOT NULL,
            subfonte         TEXT DEFAULT '',
            upvotes          INTEGER DEFAULT 0,
            comentarios      INTEGER DEFAULT 0,
            virality_score   REAL DEFAULT 0.0,
            recency_score    REAL DEFAULT 0.0,
            authority_score  REAL DEFAULT 0.0,
            relevance_score  REAL DEFAULT 0.0,
            engagement_score REAL DEFAULT 0.0,
            high_impact      INTEGER DEFAULT 0,
            keywords         TEXT DEFAULT '[]',
            data_publicacao  TEXT,
            data_coleta      TEXT,
            enviado          INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS discovery_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            data         TEXT NOT NULL,
            coletados    INTEGER DEFAULT 0,
            salvos       INTEGER DEFAULT 0,
            enviados     INTEGER DEFAULT 0,
            fontes       TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    return conn


def make_id(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def upsert(conn: sqlite3.Connection, item: dict) -> str:
    """Insere novo item ou ignora duplicatas. Retorna 'inserted' ou 'skipped'."""
    existing = conn.execute(
        "SELECT id FROM discoveries WHERE id = ?", (item["id"],)
    ).fetchone()

    if existing:
        return "skipped"

    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO discoveries
            (id, titulo, url, fonte, subfonte, upvotes, comentarios,
             virality_score, recency_score, authority_score, relevance_score,
             engagement_score, high_impact, keywords, data_publicacao, data_coleta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"],
        item["titulo"],
        item["url"],
        item["fonte"],
        item.get("subfonte", ""),
        item.get("upvotes", 0),
        item.get("comentarios", 0),
        item["virality_score"],
        item["recency_score"],
        item["authority_score"],
        item["relevance_score"],
        item["engagement_score"],
        item.get("high_impact", 0),
        json.dumps(item.get("keywords", [])),
        item.get("data_publicacao", now),
        now,
    ))
    conn.commit()
    return "inserted"


# ─────────────────────────────────────────────
# VIRALITY SCORER
# ─────────────────────────────────────────────

class ViralityScorer:
    """Calcula score de viralidade 0.0 → 1.0 para cada discovery."""

    def recency(self, published_at) -> float:
        """Decaimento exponencial: score = e^(-0.025 * horas_de_idade)."""
        if not published_at:
            return 0.5
        try:
            if isinstance(published_at, (int, float)):
                pub = datetime.fromtimestamp(published_at, tz=timezone.utc)
            elif isinstance(published_at, str):
                pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            else:
                pub = published_at.replace(tzinfo=timezone.utc) if pub.tzinfo is None else published_at
            hours = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
            return round(max(0.05, min(1.0, math.exp(-0.025 * hours))), 4)
        except Exception:
            return 0.50

    def ai_relevance(self, titulo: str) -> tuple[float, list[str], bool]:
        """Conta keywords de IA. Retorna (score, lista_encontrada, high_impact)."""
        titulo_lower = titulo.lower()
        found = [kw for kw in AI_KEYWORDS if kw in titulo_lower]
        high_impact = any(s in titulo_lower for s in HIGH_IMPACT_SIGNALS)
        # Score: cada keyword adiciona, cap em 1.0
        score = min(1.0, len(found) * 0.18 + (0.1 if found else 0))
        return round(score, 4), found, high_impact

    def engagement(self, fonte: str, upvotes: int = 0, comentarios: int = 0) -> float:
        """Engagement normalizado por fonte."""
        if fonte == "hackernews":
            return round(min(1.0, upvotes / 600) * 0.70 + min(1.0, comentarios / 250) * 0.30, 4)
        if fonte == "github":
            return round(min(1.0, upvotes / 300), 4)  # upvotes = stars
        # RSS/blogs: sem dado de engagement
        return 0.45

    def score(self, item: dict, authority: float) -> dict:
        rec = self.recency(item.get("data_publicacao"))
        eng = self.engagement(item["fonte"], item.get("upvotes", 0), item.get("comentarios", 0))
        rel_score, keywords, high_impact = self.ai_relevance(item.get("titulo", ""))

        virality = (rec * 0.30) + (authority * 0.25) + (rel_score * 0.25) + (eng * 0.20)

        if high_impact:
            virality = min(1.0, virality * 1.20)

        return {
            **item,
            "authority_score":  round(authority, 4),
            "recency_score":    rec,
            "engagement_score": eng,
            "relevance_score":  rel_score,
            "virality_score":   round(virality, 4),
            "keywords":         keywords,
            "high_impact":      1 if high_impact else 0,
        }


# ─────────────────────────────────────────────
# COLETORES
# ─────────────────────────────────────────────

class RSSCollector:
    """Coleta posts via RSS de blogs oficiais de empresas de IA."""

    def __init__(self, scorer: ViralityScorer):
        self.scorer = scorer

    def _parse_date(self, entry) -> str:
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                ts = calendar.timegm(entry.published_parsed)
                return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except Exception:
            pass
        return datetime.now(timezone.utc).isoformat()

    def fetch(self, source: dict) -> list[dict]:
        nome      = source["nome"]
        url       = source["url"]
        authority = source["authority"]
        items     = []

        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logging.warning(f"RSS {nome}: sem entradas (bozo={feed.get('bozo')})")
                return []

            for entry in feed.entries[:20]:
                link   = (entry.get("link") or "").strip()
                titulo = (entry.get("title") or "").strip()
                if not link or len(titulo) < 8:
                    continue

                raw = {
                    "id":              make_id(link),
                    "titulo":          titulo,
                    "url":             link,
                    "fonte":           "rss",
                    "subfonte":        nome,
                    "upvotes":         0,
                    "comentarios":     0,
                    "data_publicacao": self._parse_date(entry),
                }
                scored = self.scorer.score(raw, authority)
                # Blogs com authority >= 0.90 entram com threshold reduzido
                threshold = VIRALITY_MIN * 0.60 if authority >= 0.90 else VIRALITY_MIN
                if scored["virality_score"] >= threshold:
                    items.append(scored)

            logging.info(f"RSS {nome}: {len(items)} itens relevantes de {len(feed.entries)}")
            time.sleep(REQUEST_DELAY * 0.5)
        except Exception as e:
            logging.error(f"RSS {nome}: erro — {e}")

        return items

    def collect(self, sources=None) -> list[dict]:
        sources = sources or RSS_SOURCES
        all_items = []
        for src in sources:
            all_items.extend(self.fetch(src))
        return all_items


class HackerNewsCollector:
    """Coleta stories do Hacker News via Firebase API e Algolia Search."""

    HN_BASE    = "https://hacker-news.firebaseio.com/v0"
    ALGOLIA    = "https://hn.algolia.com/api/v1/search"
    AUTHORITY  = 0.82
    HEADERS    = {"User-Agent": USER_AGENT}

    def __init__(self, scorer: ViralityScorer):
        self.scorer = scorer

    def _fetch_item(self, story_id: int) -> dict | None:
        try:
            r = requests.get(
                f"{self.HN_BASE}/item/{story_id}.json",
                headers=self.HEADERS, timeout=TIMEOUT
            )
            s = r.json()
            if not s or s.get("type") != "story" or s.get("dead") or s.get("deleted"):
                return None
            return s
        except Exception:
            return None

    def fetch_top(self, limit: int = 40) -> list[dict]:
        items = []
        try:
            r = requests.get(
                f"{self.HN_BASE}/topstories.json",
                headers=self.HEADERS, timeout=TIMEOUT
            )
            ids = r.json()[:limit]
        except Exception as e:
            logging.error(f"HN top stories list: {e}")
            return []

        for sid in ids:
            s = self._fetch_item(sid)
            if not s:
                continue

            url    = s.get("url") or f"https://news.ycombinator.com/item?id={sid}"
            titulo = (s.get("title") or "").strip()
            if not titulo:
                continue

            raw = {
                "id":              make_id(url),
                "titulo":          titulo,
                "url":             url,
                "fonte":           "hackernews",
                "subfonte":        "HN Top",
                "upvotes":         s.get("score", 0),
                "comentarios":     s.get("descendants", 0),
                "data_publicacao": datetime.fromtimestamp(
                    s.get("time", time.time()), tz=timezone.utc
                ).isoformat(),
            }
            scored = self.scorer.score(raw, self.AUTHORITY)
            if scored["virality_score"] >= VIRALITY_MIN:
                items.append(scored)
            time.sleep(0.15)

        logging.info(f"HN Top: {len(items)} itens relevantes de {len(ids)}")
        return items

    def search_ai(self) -> list[dict]:
        """Busca stories sobre IA publicadas nas últimas 48h via Algolia."""
        queries = ["artificial intelligence LLM", "GPT Claude Gemini", "machine learning"]
        cutoff  = int(time.time()) - (48 * 3600)
        items   = []
        seen    = set()

        for query in queries:
            try:
                r = requests.get(self.ALGOLIA, params={
                    "query":          query,
                    "tags":           "story",
                    "numericFilters": f"created_at_i>{cutoff}",
                    "hitsPerPage":    20,
                }, headers=self.HEADERS, timeout=TIMEOUT)
                hits = r.json().get("hits", [])

                for h in hits:
                    url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                    if url in seen:
                        continue
                    seen.add(url)

                    titulo = (h.get("title") or "").strip()
                    if not titulo:
                        continue

                    try:
                        pub = datetime.fromisoformat(h["created_at"].replace("Z", "+00:00")).isoformat()
                    except Exception:
                        pub = datetime.now(timezone.utc).isoformat()

                    raw = {
                        "id":              make_id(url),
                        "titulo":          titulo,
                        "url":             url,
                        "fonte":           "hackernews",
                        "subfonte":        "HN Search",
                        "upvotes":         h.get("points", 0),
                        "comentarios":     h.get("num_comments", 0),
                        "data_publicacao": pub,
                    }
                    scored = self.scorer.score(raw, self.AUTHORITY)
                    if scored["virality_score"] >= VIRALITY_MIN:
                        items.append(scored)

                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logging.error(f"HN Search '{query}': {e}")

        logging.info(f"HN Search AI: {len(items)} itens relevantes")
        return items

    def collect(self) -> list[dict]:
        top    = self.fetch_top(limit=40)
        search = self.search_ai()
        # Deduplicar (mesmo item pode aparecer em top e search)
        seen  = set()
        final = []
        for item in top + search:
            if item["id"] not in seen:
                seen.add(item["id"])
                final.append(item)
        return final


class GitHubCollector:
    """Coleta repositórios de IA em trending/criados recentemente no GitHub."""

    SEARCH_API = "https://api.github.com/search/repositories"
    AUTHORITY  = 0.70
    HEADERS    = {
        "Accept":     "application/vnd.github.v3+json",
        "User-Agent": USER_AGENT,
    }

    def __init__(self, scorer: ViralityScorer):
        self.scorer = scorer
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self.HEADERS["Authorization"] = f"Bearer {token}"

    def fetch(self, days_back: int = 7) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        queries = [
            f"topic:llm created:>{since} stars:>20",
            f"topic:large-language-model pushed:>{since} stars:>50",
            f"topic:ai-agent created:>{since} stars:>30",
        ]
        items = []
        seen  = set()

        for query in queries:
            try:
                r = requests.get(self.SEARCH_API, headers=self.HEADERS, params={
                    "q":        query,
                    "sort":     "stars",
                    "order":    "desc",
                    "per_page": 15,
                }, timeout=TIMEOUT)

                if r.status_code == 403:
                    logging.warning("GitHub API: rate limit. Defina GITHUB_TOKEN no .env para mais requests.")
                    break
                if r.status_code != 200:
                    logging.warning(f"GitHub API: HTTP {r.status_code}")
                    continue

                for repo in r.json().get("items", []):
                    url = repo.get("html_url", "")
                    if url in seen:
                        continue
                    seen.add(url)

                    name  = repo.get("full_name", "")
                    desc  = (repo.get("description") or "").strip()
                    titulo = f"{name}: {desc[:80]}" if desc else name
                    stars = repo.get("stargazers_count", 0)

                    try:
                        pub = datetime.fromisoformat(
                            repo["created_at"].replace("Z", "+00:00")
                        ).isoformat()
                    except Exception:
                        pub = datetime.now(timezone.utc).isoformat()

                    raw = {
                        "id":              make_id(url),
                        "titulo":          titulo,
                        "url":             url,
                        "fonte":           "github",
                        "subfonte":        "GitHub Trending AI",
                        "upvotes":         stars,
                        "comentarios":     0,
                        "data_publicacao": pub,
                    }
                    scored = self.scorer.score(raw, self.AUTHORITY)
                    if scored["virality_score"] >= VIRALITY_MIN:
                        items.append(scored)

                time.sleep(REQUEST_DELAY * 2)

            except requests.RequestException as e:
                logging.error(f"GitHub query '{query}': {e}")

        logging.info(f"GitHub: {len(items)} repos relevantes")
        return items

    def collect(self) -> list[dict]:
        return self.fetch(days_back=7)


# ─────────────────────────────────────────────
# DISCOVERY ENGINE (ORQUESTRADOR)
# ─────────────────────────────────────────────

class DiscoveryEngine:

    def __init__(self, db_path: Path = DB_PATH, dry_run: bool = False):
        self.dry_run = dry_run
        self.conn    = init_db(db_path)
        scorer       = ViralityScorer()
        self.rss     = RSSCollector(scorer)
        self.hn      = HackerNewsCollector(scorer)
        self.github  = GitHubCollector(scorer)

    def run(self, fontes: list[str] | None = None) -> dict:
        fontes = fontes or ["rss", "hn", "github"]
        all_items: list[dict] = []

        logging.info(f"Discovery iniciado — fontes: {fontes}")

        if "rss" in fontes:
            logging.info("Coletando RSS feeds...")
            all_items.extend(self.rss.collect())

        if "hn" in fontes:
            logging.info("Coletando Hacker News...")
            all_items.extend(self.hn.collect())

        if "github" in fontes:
            logging.info("Coletando GitHub Trending AI...")
            all_items.extend(self.github.collect())

        # Deduplicar cross-fonte pelo ID
        seen  = set()
        unique: list[dict] = []
        for item in all_items:
            if item["id"] not in seen:
                seen.add(item["id"])
                unique.append(item)

        # Ordenar por virality
        unique.sort(key=lambda x: x["virality_score"], reverse=True)

        # Salvar no banco
        inserted = 0
        if not self.dry_run:
            for item in unique:
                if upsert(self.conn, item) == "inserted":
                    inserted += 1

            self.conn.execute("""
                INSERT INTO discovery_runs (data, coletados, salvos, fontes)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                len(unique),
                inserted,
                json.dumps(fontes),
            ))
            self.conn.commit()

        return {"total": len(unique), "inserted": inserted, "items": unique}

    def list_top(self, limit: int = 20, apenas_nao_enviados: bool = True) -> list[dict]:
        where = "WHERE enviado = 0" if apenas_nao_enviados else ""
        rows = self.conn.execute(f"""
            SELECT * FROM discoveries {where}
            ORDER BY virality_score DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def send_to_processor(self, min_virality: float = SEND_MIN) -> int:
        """Copia discoveries qualificados para articles.db como status='raw'."""
        rows = self.conn.execute("""
            SELECT * FROM discoveries
            WHERE virality_score >= ? AND enviado = 0
            ORDER BY virality_score DESC
        """, (min_virality,)).fetchall()

        if not rows:
            logging.info("Nenhum discovery para enviar ao processor.")
            return 0

        try:
            art_conn = sqlite3.connect(str(ARTICLES_DB))
            art_conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id           TEXT PRIMARY KEY,
                    title        TEXT NOT NULL,
                    url          TEXT NOT NULL,
                    summary      TEXT DEFAULT '',
                    source       TEXT,
                    company      TEXT DEFAULT '',
                    published_at TEXT,
                    status       TEXT DEFAULT 'raw',
                    collected_at TEXT DEFAULT (datetime('now')),
                    resumo       TEXT,
                    score        REAL DEFAULT 0,
                    relevancia   TEXT
                )
            """)
            art_conn.commit()

            sent = 0
            for row in rows:
                d = dict(row)
                exists = art_conn.execute(
                    "SELECT id FROM articles WHERE id = ?", (d["id"],)
                ).fetchone()
                if not exists:
                    art_conn.execute("""
                        INSERT INTO articles (id, title, url, source, published_at, status)
                        VALUES (?, ?, ?, ?, ?, 'raw')
                    """, (d["id"], d["titulo"], d["url"], f"discovery:{d['fonte']}", d["data_publicacao"]))
                    sent += 1

            art_conn.commit()
            art_conn.close()

            # Marcar como enviados
            ids = [dict(r)["id"] for r in rows]
            self.conn.executemany(
                "UPDATE discoveries SET enviado = 1 WHERE id = ?",
                [(i,) for i in ids]
            )
            self.conn.commit()

            logging.info(f"Enviados {sent} discoveries ao processor.")
            return sent

        except Exception as e:
            logging.error(f"Erro ao enviar para articles.db: {e}")
            return 0


# ─────────────────────────────────────────────
# RELATÓRIO: TOP DISCOVERIES TODAY
# ─────────────────────────────────────────────

def print_report(items: list[dict], title: str = "TOP DISCOVERIES TODAY"):
    w = 72
    print(f"\n{'═' * w}")
    print(f"  🔍  {title}")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}  —  {len(items)} item(s)")
    print(f"{'═' * w}")

    if not items:
        print("  (nenhum discovery encontrado)\n")
        return

    for i, item in enumerate(items, 1):
        score     = item.get("virality_score", 0)
        fonte     = item.get("fonte", "?")
        subfonte  = item.get("subfonte", "")
        titulo    = item.get("titulo", "")[:60]
        upvotes   = item.get("upvotes", 0)
        high      = "🔥" if item.get("high_impact") else "  "
        rec       = item.get("recency_score", 0)
        auth      = item.get("authority_score", 0)

        bar_len = int(score * 24)
        bar     = "█" * bar_len + "░" * (24 - bar_len)

        kw = item.get("keywords", [])
        if isinstance(kw, str):
            try:
                kw = json.loads(kw)
            except Exception:
                kw = []

        print(f"\n  {i:02d}. {high} {bar}  {score:.2f}")
        print(f"      {titulo}")
        print(f"      📍 {fonte}/{subfonte}  ▲ {upvotes}  rec:{rec:.2f}  auth:{auth:.2f}")
        if kw:
            print(f"      🏷  {', '.join(kw[:5])}")

    print(f"\n{'═' * w}\n")


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_file


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Discovery Engine — encontra oportunidades de conteúdo de IA automaticamente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python discovery/discovery_engine.py
  python discovery/discovery_engine.py --fonte rss hn
  python discovery/discovery_engine.py --listar
  python discovery/discovery_engine.py --enviar
  python discovery/discovery_engine.py --dry-run
        """,
    )
    parser.add_argument(
        "--fonte", nargs="+",
        choices=["rss", "hn", "github"],
        default=["rss", "hn", "github"],
        help="Fontes a coletar (padrão: todas)",
    )
    parser.add_argument(
        "--listar", action="store_true",
        help="Lista os top discoveries já salvos no banco",
    )
    parser.add_argument(
        "--enviar", action="store_true",
        help=f"Envia discoveries com virality >= {SEND_MIN} ao processor",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Coleta e pontua, mas não salva no banco",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Logging detalhado (DEBUG)",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_file  = setup_logging(log_level)
    logging.info(f"Log: {log_file.name}")

    engine = DiscoveryEngine(dry_run=args.dry_run)

    if args.listar:
        items = engine.list_top(limit=20)
        print_report(items, title="TOP DISCOVERIES SALVOS")
        return

    # ── Executa descoberta ────────────────────────────────────────────
    result = engine.run(fontes=args.fonte)

    top_items = result["items"][:20]
    print_report(top_items)

    print(f"  📊 Total único coletado : {result['total']}")
    if not args.dry_run:
        print(f"  ✅ Novos salvos no banco : {result['inserted']}")

    # ── Envia ao processor ────────────────────────────────────────────
    if args.enviar and not args.dry_run:
        print(f"\n  📤 Enviando ao processor (virality >= {SEND_MIN})...")
        sent = engine.send_to_processor(min_virality=SEND_MIN)
        print(f"  ✅ {sent} item(s) inseridos em articles.db\n")
    elif args.dry_run:
        print("  ℹ️  Dry-run: banco não foi modificado.\n")


if __name__ == "__main__":
    main()
