"""
blog_generator.py
=================
Pega artigos com score alto do banco e gera artigos completos
em português, otimizados para SEO, salvos como arquivos Markdown.

Cada artigo gerado contém:
  - Título SEO chamativo
  - Meta description (155 chars)
  - Corpo com H2/H3, parágrafos, listas
  - Seção "Por que isso importa para você?"
  - CTA final para newsletter
  - Frontmatter YAML (compatível com WordPress/Ghost/Hugo)

Como rodar:
  python content/blog_generator.py

  Opções:
    --score 7       processa artigos com score >= 7 (padrão: 6)
    --limite 3      gera até 3 artigos por rodada (padrão: 5)
    --dry-run       mostra o que geraria sem salvar nem chamar a API
"""

import sqlite3
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

load_dotenv()

BASE_DIR   = Path(__file__).parent.parent
DB_PATH    = BASE_DIR / "data" / "articles.db"
OUTPUT_DIR = BASE_DIR / "content" / "output"
API_KEY    = os.getenv("ANTHROPIC_API_KEY")
MODEL      = "claude-opus-4-6"   # Opus para máxima qualidade de escrita

# CTA padrão — edite com o link real da sua newsletter
NEWSLETTER_URL  = os.getenv("NEWSLETTER_URL", "https://seublog.com/newsletter")
NEWSLETTER_NOME = os.getenv("NEWSLETTER_NOME", "IA para Brasileiros")


# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def fetch_articles(conn: sqlite3.Connection,
                   score_min: float,
                   limite: int) -> list[dict]:
    """Busca artigos processados com score alto, ainda não publicados."""
    rows = conn.execute("""
        SELECT id, title, url, summary, resumo, score, relevancia, source, company
        FROM articles
        WHERE status    = 'processed'
          AND score    >= ?
        ORDER BY score DESC
        LIMIT ?
    """, (score_min, limite)).fetchall()

    return [
        {
            "id":        r[0],
            "title":     r[1],
            "url":       r[2],
            "summary":   r[3] or "",
            "resumo":    r[4] or "",
            "score":     r[5],
            "relevancia":r[6],
            "source":    r[7],
            "company":   r[8],
        }
        for r in rows
    ]


def mark_as_generated(conn: sqlite3.Connection,
                       article_id: str,
                       filepath: str):
    """Atualiza o status e registra o caminho do arquivo gerado."""
    # Adiciona coluna 'filepath' se não existir
    colunas = {r[1] for r in conn.execute("PRAGMA table_info(articles)")}
    if "filepath" not in colunas:
        conn.execute("ALTER TABLE articles ADD COLUMN filepath TEXT")

    conn.execute("""
        UPDATE articles
        SET status   = 'generated',
            filepath = ?
        WHERE id = ?
    """, (filepath, article_id))
    conn.commit()


# ─────────────────────────────────────────────
# PROMPT DE GERAÇÃO
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um redator especialista em conteúdo sobre inteligência artificial 
para o público brasileiro. Escreve com clareza, entusiasmo e sem jargão desnecessário.

Seu estilo:
- Explica conceitos complexos de forma simples
- Usa exemplos do cotidiano brasileiro
- Tom informativo mas acessível, como conversar com um amigo inteligente
- Nunca usa "delve", "realm", "groundbreaking" ou clichês de IA
- Parágrafos curtos (3-4 linhas máximo)

Retorne SOMENTE um JSON com esta estrutura exata:
{
  "titulo_seo": "Título principal com palavra-chave, até 65 chars",
  "titulo_chamativo": "Versão mais criativa/emocional para redes sociais",
  "meta_description": "Resumo atraente para Google, entre 140-155 caracteres",
  "slug": "titulo-em-slug-para-url",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "corpo": "Corpo completo do artigo em Markdown"
}

Estrutura obrigatória do campo 'corpo' (em Markdown):
1. Parágrafo de abertura (gancho — 2-3 linhas que prendem o leitor)
2. ## O que aconteceu
3. ## Por que isso é importante
4. ## O que muda na prática (com exemplos concretos para brasileiros)
5. ## Vale a pena ficar de olho?
6. [BLOCO_CTA] — deixe este marcador exato no final, antes do fechamento
7. Parágrafo de fechamento (1-2 linhas)

Tamanho alvo do corpo: 600-900 palavras."""


def build_prompt(article: dict) -> str:
    return f"""Crie um artigo de blog completo sobre esta notícia de IA:

TÍTULO ORIGINAL: {article['title']}
FONTE: {article['source']} ({article['company']})
URL ORIGINAL: {article['url']}
RESUMO EM PORTUGUÊS: {article['resumo']}
DESCRIÇÃO TÉCNICA: {article['summary'][:600]}
SCORE DE RELEVÂNCIA: {article['score']}/10
NÍVEL DE RELEVÂNCIA: {article['relevancia']}

Gere o artigo seguindo as instruções do sistema."""


# ─────────────────────────────────────────────
# GERAÇÃO VIA API
# ─────────────────────────────────────────────

def generate_article(client: anthropic.Anthropic, article: dict) -> dict:
    """Chama Claude e retorna o dicionário com o artigo gerado."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(article)}]
    )

    raw = response.content[0].text.strip()

    # Remove markdown code fence se presente
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


# ─────────────────────────────────────────────
# MONTAGEM DO MARKDOWN FINAL
# ─────────────────────────────────────────────

CTA_BLOCK = """---

### 📬 Quer ficar por dentro de tudo que acontece em IA?

Todo dia útil, a gente garimpа as notícias mais relevantes sobre inteligência artificial 
e entrega no seu e-mail — em português, sem enrolação.

**[Assine grátis a newsletter {nome} →]({url})**

---""".format(nome=NEWSLETTER_NOME, url=NEWSLETTER_URL)


def build_markdown(article: dict, generated: dict) -> str:
    """
    Monta o arquivo Markdown final com frontmatter YAML.
    O frontmatter é lido pelo WordPress (plugin WP Markdown),
    Ghost, Hugo e outros geradores de site.
    """
    now        = datetime.now()
    data_br    = now.strftime("%d/%m/%Y")
    data_iso   = now.strftime("%Y-%m-%d")
    tags_yaml  = "\n".join(f'  - "{t}"' for t in generated.get("tags", []))

    # Substitui o marcador [BLOCO_CTA] pelo CTA real
    corpo = generated["corpo"].replace("[BLOCO_CTA]", CTA_BLOCK)

    frontmatter = f"""---
titulo: "{generated['titulo_seo']}"
titulo_chamativo: "{generated['titulo_chamativo']}"
meta_description: "{generated['meta_description']}"
slug: "{generated['slug']}"
tags:
{tags_yaml}
fonte_original: "{article['url']}"
empresa: "{article['company']}"
score_relevancia: {article['score']}
status: "rascunho"
data_geracao: "{data_iso}"
modelo_ia: "{MODEL}"
---"""

    header = f"""# {generated['titulo_seo']}

> **Fonte:** [{article['source']}]({article['url']})  
> **Publicado em:** {data_br}  
> **Score de relevância:** {article['score']:.1f}/10 ({article['relevancia']})

---

"""

    return frontmatter + "\n\n" + header + corpo


# ─────────────────────────────────────────────
# SALVAR ARQUIVO
# ─────────────────────────────────────────────

def save_markdown(slug: str, content: str) -> Path:
    """
    Salva o artigo em content/output/<data>_<slug>.md
    Nunca sobrescreve — adiciona sufixo numérico se já existir.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_prefix = datetime.now().strftime("%Y%m%d")
    # Limpa o slug: só letras, números e hífens
    slug_clean = re.sub(r"[^a-z0-9\-]", "", slug.lower())[:60]
    base_name  = f"{date_prefix}_{slug_clean}"

    filepath = OUTPUT_DIR / f"{base_name}.md"
    counter  = 1
    while filepath.exists():
        filepath = OUTPUT_DIR / f"{base_name}_{counter}.md"
        counter += 1

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run(score_min: float = 6.0, limite: int = 5, dry_run: bool = False):
    if not API_KEY and not dry_run:
        print("❌ ANTHROPIC_API_KEY não encontrada.")
        print("   Crie um arquivo .env com: ANTHROPIC_API_KEY=sk-ant-...")
        return

    print("=" * 60)
    print("✍️   BLOG GENERATOR — Artigos SEO em Português")
    print("=" * 60)
    print(f"   Score mínimo : {score_min}/10")
    print(f"   Limite       : {limite} artigo(s) por rodada")
    if dry_run:
        print("   Modo         : DRY RUN (sem chamadas à API)")
    print()

    conn    = sqlite3.connect(str(DB_PATH))
    artigos = fetch_articles(conn, score_min, limite)

    if not artigos:
        print("ℹ️  Nenhum artigo elegível.")
        print(f"   Critério: status='processed' e score >= {score_min}")
        print("   Rode primeiro: python processor/processor.py\n")
        conn.close()
        return

    print(f"📋 {len(artigos)} artigo(s) elegível(is) para geração:\n")
    for a in artigos:
        print(f"   [{a['score']:.1f}] {a['title'][:65]}")

    if dry_run:
        print("\n✅ Dry-run concluído. Nenhum arquivo salvo.")
        conn.close()
        return

    print()
    client  = anthropic.Anthropic(api_key=API_KEY)
    gerados = 0
    erros   = 0

    for i, artigo in enumerate(artigos, 1):
        print(f"\n[{i}/{len(artigos)}] Gerando artigo...")
        print(f"   📰 {artigo['title'][:65]}")

        try:
            generated = generate_article(client, artigo)

            markdown  = build_markdown(artigo, generated)
            filepath  = save_markdown(generated["slug"], markdown)

            mark_as_generated(conn, artigo["id"], str(filepath))

            print(f"   ✅ Salvo em : {filepath.name}")
            print(f"   🏷️  Título   : {generated['titulo_seo']}")
            print(f"   📝 Meta     : {generated['meta_description'][:70]}...")
            print(f"   🏷️  Tags     : {', '.join(generated['tags'])}")

            gerados += 1

        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON inválido da API: {e}")
            erros += 1
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            erros += 1

    conn.close()

    print("\n" + "=" * 60)
    print(f"✅  Geração concluída!")
    print(f"   Artigos gerados : {gerados}")
    if erros:
        print(f"   Erros           : {erros}")
    print(f"   Pasta de saída  : {OUTPUT_DIR}")
    print("=" * 60)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera artigos de blog SEO em português a partir do banco de artigos."
    )
    parser.add_argument("--score",   type=float, default=6.0,
                        help="Score mínimo para gerar artigo (padrão: 6)")
    parser.add_argument("--limite",  type=int,   default=5,
                        help="Máximo de artigos por rodada (padrão: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Apenas lista artigos elegíveis, sem gerar")
    args = parser.parse_args()

    run(score_min=args.score, limite=args.limite, dry_run=args.dry_run)
