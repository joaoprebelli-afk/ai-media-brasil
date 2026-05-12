"""
social_generator.py
===================
Lê um artigo Markdown gerado pelo blog_generator.py e produz
todos os assets de conteúdo para redes sociais em uma única
chamada à API (economiza tokens e tempo).

Outputs por artigo:
  content/social/tiktok/        → roteiro .md (hook + roteiro + CTA)
  content/social/instagram/     → legenda .md (caption otimizada)
  content/social/carousel/      → 7 slides .json
  content/social/twitter/       → post único + thread .md
  content/social/linkedin/      → post profissional .md
  content/social/newsletter/    → snippet .md (resumo + CTA)

Como rodar:
  # Processa o artigo mais recente
  python content/social_generator.py

  # Processa um artigo específico
  python content/social_generator.py --arquivo content/output/20260508_gpt-5.md

  # Processa todos os artigos gerados ainda não publicados
  python content/social_generator.py --todos

  # Dry-run: mostra o que geraria sem chamar a API
  python content/social_generator.py --dry-run
"""

import os
import re
import json
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────

load_dotenv()

BASE_DIR      = Path(__file__).parent.parent
DB_PATH       = BASE_DIR / "data" / "articles.db"
OUTPUT_DIR    = BASE_DIR / "content" / "output"
SOCIAL_DIR    = BASE_DIR / "content" / "social"
API_KEY       = os.getenv("ANTHROPIC_API_KEY")
MODEL         = "claude-opus-4-6"

BLOG_URL      = os.getenv("BLOG_URL",       "https://seublog.com")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL",  "link na bio")
NEWSLETTER_URL= os.getenv("NEWSLETTER_URL", "https://seublog.com/newsletter")


# ─────────────────────────────────────────────
# LEITURA DO ARTIGO
# ─────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Separa o frontmatter YAML do corpo do artigo.
    Retorna (metadados_dict, corpo_sem_frontmatter).
    """
    meta = {}
    corpo = text

    if text.startswith("---"):
        partes = text.split("---", 2)
        if len(partes) >= 3:
            for linha in partes[1].strip().splitlines():
                if ":" in linha:
                    chave, _, valor = linha.partition(":")
                    meta[chave.strip()] = valor.strip().strip('"')
            corpo = partes[2].strip()

    return meta, corpo


def load_article(filepath: Path) -> dict:
    """Carrega um arquivo Markdown e extrai metadados e corpo."""
    text = filepath.read_text(encoding="utf-8")
    meta, corpo = parse_frontmatter(text)

    # Remove a linha de cabeçalho (# Título) do corpo para não duplicar
    corpo_limpo = re.sub(r"^#[^#].*\n", "", corpo, count=1).strip()
    # Remove bloco de citação de fonte
    corpo_limpo = re.sub(r"^>.*\n", "", corpo_limpo, flags=re.MULTILINE).strip()
    # Remove linhas de separação
    corpo_limpo = re.sub(r"^---\n", "", corpo_limpo, flags=re.MULTILINE).strip()

    return {
        "titulo":      meta.get("titulo", filepath.stem),
        "slug":        meta.get("slug",   filepath.stem),
        "meta":        meta.get("meta_description", ""),
        "tags":        meta.get("tags",   ""),
        "empresa":     meta.get("empresa",""),
        "score":       meta.get("score_relevancia", ""),
        "fonte":       meta.get("fonte_original", ""),
        "corpo":       corpo_limpo,
        "filepath":    str(filepath),
    }


def find_articles(todos: bool = False) -> list[Path]:
    """
    Descobre artigos Markdown para processar.
    Se todos=False, pega apenas o mais recente.
    """
    arquivos = sorted(OUTPUT_DIR.glob("*.md"), reverse=True)
    if not arquivos:
        return []
    return arquivos if todos else [arquivos[0]]


# ─────────────────────────────────────────────
# PROMPT ÚNICO — TODOS OS FORMATOS DE UMA VEZ
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um estrategista de conteúdo digital especializado em IA 
para o mercado brasileiro. Cria conteúdo que educa, engaja e converte em cada plataforma.

Regras gerais:
- Português brasileiro natural, sem formalidade excessiva
- Emojis com moderação (máximo 5 por peça, exceto TikTok)
- Nunca menciona "IA gerou esse conteúdo"
- Cada peça deve funcionar sozinha, sem precisar do artigo original

Você receberá um artigo e retornará um JSON com EXATAMENTE esta estrutura:
{
  "tiktok": { ... },
  "instagram": { ... },
  "carousel": { ... },
  "twitter": { ... },
  "linkedin": { ... },
  "newsletter": { ... }
}

Especificações de cada formato — siga à risca:

TIKTOK:
{
  "hook": "Frase de 3-5 segundos. Deve causar curiosidade ou choque. Máximo 12 palavras.",
  "roteiro": "Roteiro de 30-45 segundos. Use quebras de linha para cada fala/cena. Inclua [PAUSA], [MOSTRAR TELA], [TEXTO NA TELA: ...] quando relevante.",
  "cta": "Chamada final de 1 frase levando para o link na bio.",
  "hashtags": ["#ia", "#inteligenciaartificial", ...] // 5-8 hashtags
}

INSTAGRAM:
{
  "caption": "Legenda completa. Começa com gancho forte (sem emojis na 1ª linha). Parágrafos curtos. Máximo 300 palavras.",
  "cta": "Última linha com CTA: comentar, salvar ou compartilhar.",
  "hashtags": ["#ia", ...] // 20-25 hashtags misturando grandes e nicho
}

CAROUSEL:
{
  "slides": [
    { "numero": 1, "tipo": "capa",    "titulo": "...", "subtitulo": "..." },
    { "numero": 2, "tipo": "ponto",   "titulo": "...", "texto": "...", "emoji": "..." },
    { "numero": 3, "tipo": "ponto",   "titulo": "...", "texto": "...", "emoji": "..." },
    { "numero": 4, "tipo": "ponto",   "titulo": "...", "texto": "...", "emoji": "..." },
    { "numero": 5, "tipo": "ponto",   "titulo": "...", "texto": "...", "emoji": "..." },
    { "numero": 6, "tipo": "ponto",   "titulo": "...", "texto": "...", "emoji": "..." },
    { "numero": 7, "tipo": "cta",     "titulo": "...", "cta": "...",   "acao": "Salve para não perder!" }
  ]
}
// Slide 1: headline chocante/curiosa. Slides 2-6: 1 ponto por slide, texto máx 2 linhas. Slide 7: CTA.

TWITTER:
{
  "post_unico": "Tweet de até 280 chars com link e 2-3 hashtags.",
  "thread": [
    "Tweet 1/N — abertura que prende (sem dizer 'thread')",
    "Tweet 2/N — ...",
    "Tweet 3/N — ...",
    "Tweet 4/N — ...",
    "Tweet 5/N — ...",
    "Tweet 6/N — CTA final com link"
  ]
}
// Thread de 5-6 tweets. Cada um max 280 chars. Numeração no início de cada tweet.

LINKEDIN:
{
  "post": "Post completo. Tom profissional mas acessível. Começa com 1 linha que aparece antes do 'ver mais'. Usa quebras de linha generosas. Termina com pergunta para engajar. Máximo 1300 chars.",
  "hashtags": ["#InteligenciaArtificial", "#Produtividade", ...] // 3-5 hashtags profissionais
}

NEWSLETTER:
{
  "assunto": "Linha de assunto do e-mail. Máximo 50 chars. Sem clickbait.",
  "preview": "Preview text do e-mail. 80-90 chars.",
  "snippet": "Parágrafo de 3-4 linhas apresentando a notícia com entusiasmo.",
  "cta_texto": "Texto do botão/link CTA. Ex: 'Ler artigo completo →'",
  "cta_url":   "URL do artigo no blog"
}

RETORNE SOMENTE O JSON. Nenhum texto antes ou depois."""


def build_prompt(article: dict) -> str:
    blog_url = f"{BLOG_URL}/{article['slug']}"
    return f"""Crie os assets de redes sociais para este artigo de blog sobre IA:

TÍTULO: {article['titulo']}
EMPRESA/TEMA: {article['empresa']}
SCORE DE RELEVÂNCIA: {article['score']}/10
URL DO ARTIGO: {blog_url}
URL DA NEWSLETTER: {NEWSLETTER_URL}

CORPO DO ARTIGO:
{article['corpo'][:2500]}

Gere todos os 6 formatos seguindo as especificações do sistema."""


# ─────────────────────────────────────────────
# CHAMADA À API
# ─────────────────────────────────────────────

def generate_social(client: anthropic.Anthropic, article: dict) -> dict:
    """Uma única chamada Claude → todos os 6 formatos."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(article)}]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


# ─────────────────────────────────────────────
# SALVAMENTO — cada formato em sua pasta
# ─────────────────────────────────────────────

def slug_date(article: dict) -> str:
    date = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r"[^a-z0-9\-]", "", article["slug"].lower())[:50]
    return f"{date}_{slug}"


def save_tiktok(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "tiktok"
    pasta.mkdir(parents=True, exist_ok=True)
    hashtags = " ".join(data.get("hashtags", []))
    content = f"""# 🎵 ROTEIRO TIKTOK / REELS

**Artigo:** {article['titulo']}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}

---

## ⚡ HOOK (primeiros 3 segundos)

> {data['hook']}

---

## 🎬 ROTEIRO (30-45 segundos)

{data['roteiro']}

---

## 📲 CTA FINAL

> {data['cta']}

---

## #️⃣ Hashtags

{hashtags}
"""
    (pasta / f"{prefix}.md").write_text(content, encoding="utf-8")


def save_instagram(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "instagram"
    pasta.mkdir(parents=True, exist_ok=True)
    hashtags = " ".join(data.get("hashtags", []))
    content = f"""# 📸 INSTAGRAM CAPTION

**Artigo:** {article['titulo']}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}

---

## Legenda

{data['caption']}

{data['cta']}

---

## #️⃣ Hashtags (cole abaixo da legenda ou no 1º comentário)

{hashtags}
"""
    (pasta / f"{prefix}.md").write_text(content, encoding="utf-8")


def save_carousel(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "carousel"
    pasta.mkdir(parents=True, exist_ok=True)

    # Salva JSON (para design tools como Canva/Figma via automação)
    json_path = pasta / f"{prefix}.json"
    json_path.write_text(
        json.dumps({"artigo": article['titulo'], "slides": data["slides"]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Salva também versão Markdown legível
    md_lines = [
        f"# 🎠 CAROUSEL INSTAGRAM\n",
        f"**Artigo:** {article['titulo']}  ",
        f"**Data:** {datetime.now().strftime('%d/%m/%Y')}\n",
        "---\n"
    ]
    for slide in data["slides"]:
        n     = slide["numero"]
        tipo  = slide["tipo"]
        emoji = slide.get("emoji", "")

        if tipo == "capa":
            md_lines.append(f"## SLIDE {n} — CAPA\n")
            md_lines.append(f"**Título:** {slide['titulo']}")
            if slide.get("subtitulo"):
                md_lines.append(f"**Subtítulo:** {slide['subtitulo']}")
        elif tipo == "cta":
            md_lines.append(f"## SLIDE {n} — CTA FINAL\n")
            md_lines.append(f"**Título:** {slide['titulo']}")
            md_lines.append(f"**CTA:** {slide['cta']}")
            md_lines.append(f"**Ação:** {slide.get('acao','')}")
        else:
            md_lines.append(f"## SLIDE {n} {emoji}\n")
            md_lines.append(f"**Título:** {slide['titulo']}")
            md_lines.append(f"**Texto:** {slide.get('texto','')}")

        md_lines.append("\n---\n")

    (pasta / f"{prefix}.md").write_text("\n".join(md_lines), encoding="utf-8")


def save_twitter(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "twitter"
    pasta.mkdir(parents=True, exist_ok=True)

    thread_md = "\n\n".join(
        f"**Tweet {i+1}/{len(data['thread'])}**\n\n{tweet}"
        for i, tweet in enumerate(data["thread"])
    )
    content = f"""# 🐦 X / TWITTER

**Artigo:** {article['titulo']}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}

---

## Post Único

{data['post_unico']}

*(chars: {len(data['post_unico'])} / 280)*

---

## Thread ({len(data['thread'])} tweets)

{thread_md}
"""
    (pasta / f"{prefix}.md").write_text(content, encoding="utf-8")


def save_linkedin(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "linkedin"
    pasta.mkdir(parents=True, exist_ok=True)
    hashtags = " ".join(data.get("hashtags", []))
    content = f"""# 💼 LINKEDIN POST

**Artigo:** {article['titulo']}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}  
**Chars:** {len(data['post'])} / 1300

---

{data['post']}

{hashtags}
"""
    (pasta / f"{prefix}.md").write_text(content, encoding="utf-8")


def save_newsletter(data: dict, article: dict, prefix: str):
    pasta = SOCIAL_DIR / "newsletter"
    pasta.mkdir(parents=True, exist_ok=True)
    content = f"""# 📧 NEWSLETTER SNIPPET

**Artigo:** {article['titulo']}  
**Data:** {datetime.now().strftime('%d/%m/%Y')}

---

**Assunto:** {data['assunto']}  
*(chars: {len(data['assunto'])} / 50)*

**Preview text:** {data['preview']}  
*(chars: {len(data['preview'])} / 90)*

---

## Snippet

{data['snippet']}

**[{data['cta_texto']}]({data['cta_url']})**
"""
    (pasta / f"{prefix}.md").write_text(content, encoding="utf-8")


SAVERS = {
    "tiktok":     save_tiktok,
    "instagram":  save_instagram,
    "carousel":   save_carousel,
    "twitter":    save_twitter,
    "linkedin":   save_linkedin,
    "newsletter": save_newsletter,
}

ICONS = {
    "tiktok":    "🎵",
    "instagram": "📸",
    "carousel":  "🎠",
    "twitter":   "🐦",
    "linkedin":  "💼",
    "newsletter":"📧",
}


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def process_article(client, article: dict):
    """Gera e salva todos os assets para um artigo."""
    print(f"\n   📰 {article['titulo'][:65]}")

    social = generate_social(client, article)
    prefix = slug_date(article)
    salvos = []

    for formato, saver in SAVERS.items():
        if formato in social:
            saver(social[formato], article, prefix)
            salvos.append(formato)

    return salvos, prefix


def run(arquivo: str = None, todos: bool = False, dry_run: bool = False):
    if not API_KEY and not dry_run:
        print("❌ ANTHROPIC_API_KEY não encontrada.")
        print("   Crie um arquivo .env com: ANTHROPIC_API_KEY=sk-ant-...")
        return

    print("=" * 60)
    print("📱  SOCIAL GENERATOR — Assets para Redes Sociais")
    print("=" * 60)

    # Descobre arquivos a processar
    if arquivo:
        arquivos = [Path(arquivo)]
    elif todos:
        arquivos = find_articles(todos=True)
    else:
        arquivos = find_articles(todos=False)

    if not arquivos:
        print("\nℹ️  Nenhum artigo encontrado em content/output/")
        print("   Rode primeiro: python content/blog_generator.py\n")
        return

    articles = [load_article(p) for p in arquivos if p.exists()]
    print(f"\n📋 {len(articles)} artigo(s) para processar:")
    for a in articles:
        print(f"   [{a['score']}] {a['titulo'][:60]}")

    if dry_run:
        print("\n✅ Dry-run. Nenhum arquivo gerado.")
        return

    print()
    client    = anthropic.Anthropic(api_key=API_KEY)
    gerados   = 0
    erros     = 0

    for article in articles:
        print(f"\n[{gerados+1}/{len(articles)}] Gerando assets...")
        try:
            salvos, prefix = process_article(client, article)
            gerados += 1

            print(f"\n   ✅ Assets salvos ({len(salvos)} formatos):")
            for fmt in salvos:
                ext  = "json+md" if fmt == "carousel" else "md"
                path = SOCIAL_DIR / fmt / f"{prefix}.{ext.split('+')[0]}"
                print(f"      {ICONS[fmt]} {fmt:<12} → {path.name}")

        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON inválido da API: {e}")
            erros += 1
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            erros += 1

    print("\n" + "=" * 60)
    print(f"✅  Geração concluída!")
    print(f"   Artigos processados : {gerados}")
    if erros:
        print(f"   Erros              : {erros}")
    print(f"   Pasta de saída     : {SOCIAL_DIR}")
    print("=" * 60)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera assets de redes sociais a partir de artigos Markdown."
    )
    parser.add_argument("--arquivo", type=str,  default=None,
                        help="Caminho para um arquivo .md específico")
    parser.add_argument("--todos",   action="store_true",
                        help="Processa todos os artigos em content/output/")
    parser.add_argument("--dry-run", action="store_true",
                        help="Lista artigos sem gerar assets")
    args = parser.parse_args()

    run(arquivo=args.arquivo, todos=args.todos, dry_run=args.dry_run)
