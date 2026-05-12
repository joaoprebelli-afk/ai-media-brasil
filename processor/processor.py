"""
processor.py
============
Pega artigos com status 'raw' no banco, envia para Claude API e:
  1. Gera um resumo em português (3-4 frases)
  2. Classifica a relevância para o público brasileiro (score 0-10)
  3. Salva o resumo e o score no banco
  4. Atualiza o status para 'processed' (ou 'rejected' se score < 4)

Como rodar:
  1. Defina ANTHROPIC_API_KEY no arquivo .env (ou como variável de ambiente)
  2. pip install anthropic python-dotenv
  3. python processor/processor.py

Fluxo de status:
  raw → processed  (score >= 4, relevante)
  raw → rejected   (score <  4, pouco relevante)
"""

import sqlite3
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

load_dotenv()  # lê o arquivo .env na raiz do projeto

BASE_DIR   = Path(__file__).parent.parent
DB_PATH    = BASE_DIR / "data" / "articles.db"
API_KEY    = os.getenv("ANTHROPIC_API_KEY")
MODEL      = "claude-haiku-4-5-20251001"   # rápido e barato para triagem
SCORE_MIN  = 4                              # abaixo disso → rejected


# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def migrate_db(conn: sqlite3.Connection):
    """
    Adiciona as colunas novas caso ainda não existam.
    Seguro de rodar múltiplas vezes (ignora se coluna já existe).
    """
    colunas_novas = [
        ("resumo",      "TEXT"),
        ("score",       "REAL DEFAULT 0"),
        ("relevancia",  "TEXT"),   # ex: "Alta", "Média", "Baixa"
    ]
    colunas_existentes = {
        row[1]
        for row in conn.execute("PRAGMA table_info(articles)").fetchall()
    }
    for coluna, tipo in colunas_novas:
        if coluna not in colunas_existentes:
            conn.execute(f"ALTER TABLE articles ADD COLUMN {coluna} {tipo}")
            print(f"   🔧 Coluna '{coluna}' adicionada ao banco.")
    conn.commit()


def fetch_raw_articles(conn: sqlite3.Connection) -> list[dict]:
    """Retorna todos os artigos com status 'raw'."""
    rows = conn.execute("""
        SELECT id, title, url, summary, source, company
        FROM articles
        WHERE status = 'raw'
        ORDER BY collected_at DESC
    """).fetchall()

    return [
        {
            "id":      row[0],
            "title":   row[1],
            "url":     row[2],
            "summary": row[3] or "",
            "source":  row[4],
            "company": row[5],
        }
        for row in rows
    ]


def save_result(conn: sqlite3.Connection, article_id: str, resumo: str,
                score: float, relevancia: str, status: str):
    """Salva o resumo, score e novo status no banco."""
    conn.execute("""
        UPDATE articles
        SET resumo     = ?,
            score      = ?,
            relevancia = ?,
            status     = ?
        WHERE id = ?
    """, (resumo, score, relevancia, status, article_id))
    conn.commit()


# ─────────────────────────────────────────────
# PROMPT + CHAMADA À API
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um editor de um blog brasileiro especializado em 
inteligência artificial e produtividade. Seu público é brasileiro, curioso, 
quer entender como a IA afeta o dia a dia e o trabalho deles.

Ao analisar uma notícia, você retorna um JSON com exatamente estes campos:
{
  "resumo": "Resumo em português em 3-4 frases, linguagem clara e direta.",
  "score": <número de 0 a 10>,
  "relevancia": "<Alta|Média|Baixa>",
  "motivo": "Uma frase explicando o score."
}

Critérios de score para o público brasileiro de IA e produtividade:
  9-10 → lançamento ou grande novidade de modelo (GPT, Claude, Gemini etc.)
  7-8  → nova ferramenta de IA, caso de uso prático, impacto no trabalho
  5-6  → artigo técnico ou de pesquisa com aplicação prática relevante
  3-4  → notícia corporativa/financeira com pouco impacto prático
  0-2  → não é sobre IA ou produtividade, ou é irrelevante para brasileiros

Retorne SOMENTE o JSON, sem texto adicional."""


def analyze_article(client: anthropic.Anthropic, article: dict) -> dict:
    """
    Envia o artigo para Claude e retorna o JSON com resumo + score.
    """
    user_message = f"""Analise esta notícia sobre IA:

TÍTULO: {article['title']}
FONTE: {article['source']} ({article['company']})
URL: {article['url']}
DESCRIÇÃO ORIGINAL: {article['summary'][:800]}

Retorne o JSON de análise."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    raw_text = response.content[0].text.strip()

    # Remove blocos de código markdown se o modelo os incluir
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    return json.loads(raw_text)


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run():
    if not API_KEY:
        print("❌ ANTHROPIC_API_KEY não encontrada.")
        print("   Crie um arquivo .env na raiz com: ANTHROPIC_API_KEY=sua_chave")
        return

    print("=" * 60)
    print("🔍  PROCESSOR — Resumo e Classificação de Relevância")
    print("=" * 60)

    conn   = sqlite3.connect(str(DB_PATH))
    migrate_db(conn)

    artigos = fetch_raw_articles(conn)

    if not artigos:
        print("\nℹ️  Nenhum artigo novo para processar.")
        print("   Rode primeiro: python collector/rss_collector.py\n")
        conn.close()
        return

    print(f"\n📋 {len(artigos)} artigo(s) para processar...\n")

    client    = anthropic.Anthropic(api_key=API_KEY)
    aprovados = 0
    rejeitados = 0
    erros     = 0

    for i, artigo in enumerate(artigos, 1):
        print(f"[{i}/{len(artigos)}] {artigo['title'][:65]}...")

        try:
            resultado   = analyze_article(client, artigo)
            resumo      = resultado["resumo"]
            score       = float(resultado["score"])
            relevancia  = resultado["relevancia"]
            motivo      = resultado.get("motivo", "")

            # Define status pelo score
            status = "processed" if score >= SCORE_MIN else "rejected"

            save_result(conn, artigo["id"], resumo, score, relevancia, status)

            icone = "✅" if status == "processed" else "🗑️ "
            print(f"   {icone} Score: {score:.1f}/10 | {relevancia} | {motivo[:60]}")

            if status == "processed":
                aprovados += 1
            else:
                rejeitados += 1

        except json.JSONDecodeError as e:
            print(f"   ⚠️  Erro ao parsear JSON da API: {e}")
            erros += 1
        except Exception as e:
            print(f"   ❌ Erro inesperado: {e}")
            erros += 1

    conn.close()

    # ── RESUMO FINAL ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"✅  Processamento concluído!")
    print(f"   Aprovados  : {aprovados}  (status → processed)")
    print(f"   Rejeitados : {rejeitados}  (status → rejected)")
    if erros:
        print(f"   Erros      : {erros}")
    print("=" * 60)

    show_top_articles()


def show_top_articles():
    """Mostra os melhores artigos processados para conferência."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("""
        SELECT title, score, relevancia, resumo, source
        FROM articles
        WHERE status = 'processed'
        ORDER BY score DESC
        LIMIT 5
    """).fetchall()
    conn.close()

    if not rows:
        return

    print("\n🏆 TOP ARTIGOS PROCESSADOS:\n")
    for title, score, relevancia, resumo, source in rows:
        print(f"  [{score:.1f}/10] {relevancia} — {title[:60]}")
        print(f"  Fonte : {source}")
        print(f"  Resumo: {resumo[:120]}...")
        print()


# ─────────────────────────────────────────────
# ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    run()
