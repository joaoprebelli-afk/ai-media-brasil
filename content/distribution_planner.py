"""
distribution_planner.py
=======================
PASSO 1 do pipeline editorial — ANTES de gerar qualquer conteúdo.

Analisa uma notícia/tópico e decide onde publicar, com razão editorial
para cada plataforma. Evita gerar conteúdo genérico para todo lugar.

Como usar:

  # Descreva a notícia interativamente
  python content/distribution_planner.py

  # Passe o tópico direto
  python content/distribution_planner.py --topico "Meta abriu Ads para Claude via MCP com 29 ferramentas"

  # Analisa um artigo .md já escrito
  python content/distribution_planner.py --arquivo content/output/20260518_meta-ads.md

  # Após decidir, gera conteúdo só para as plataformas recomendadas
  python content/distribution_planner.py --topico "..." --gerar

Plataformas avaliadas:
  X/Twitter   → análise, opinião, threads, breaking news
  TikTok      → gancho visual, viral, explicação simples
  Instagram   → carrossel, ferramentas, conteúdo visual
  LinkedIn    → impacto profissional, negócios, agências
  Newsletter  → análise profunda, evergreen, semana em resumo
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

try:
    import anthropic
except ModuleNotFoundError:
    anthropic = None

load_dotenv()

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "content" / "output"
SOCIAL_DIR = BASE_DIR / "content" / "social"
API_KEY    = os.getenv("ANTHROPIC_API_KEY")
MODEL      = "claude-opus-4-6"

BLOG_URL        = os.getenv("BLOG_URL",        "https://joaogpt.com")
NEWSLETTER_URL  = os.getenv("NEWSLETTER_URL",  "https://joaogpt.com/newsletter")

# ─────────────────────────────────────────────
# ANÁLISE EDITORIAL
# ─────────────────────────────────────────────

SYSTEM_ANALISE = """Você é o editor do JOÃOGPT — mídia tech brasileira sobre IA.

Sua função é decidir WHERE e HOW publicar uma notícia/tópico de IA.
Não gera conteúdo ainda. Só avalia fit editorial por plataforma.

Critérios por plataforma:

X/TWITTER
- Funciona: análise com opinião, threads explicativas, breaking news,
  revelações ("o que o release não disse"), dados concretos, crítica inteligente
- Não funciona: conteúdo sem opinião, tutoriais longos, lifestyle

TIKTOK / REELS
- Funciona: gancho emocional forte nos 3 primeiros segundos, explicação visual,
  "você sabia que?", comparações antes/depois, demos de ferramentas, urgência
- Não funciona: análise técnica densa, muitos termos, sem apelo visual

INSTAGRAM CARROSSEL
- Funciona: listas "X coisas", passo-a-passo, comparativos, ferramentas úteis,
  conteúdo que as pessoas salvam, visual atraente possível
- Não funciona: notícia efêmera, análise muito técnica

LINKEDIN
- Funciona: impacto em profissões, oportunidades de carreira/negócio,
  mudanças de mercado, cases, aprendizados práticos para PMEs e agências
- Não funciona: hype de tecnologia, notícia sem aplicação profissional

NEWSLETTER
- Funciona: análise profunda, contexto que leva tempo para explicar,
  conteúdo evergreen, melhor da semana
- Não funciona: notícia muito rápida que vai envelhecer em horas

Retorne EXATAMENTE este JSON:
{
  "resumo": "Uma linha descrevendo o que é essa notícia/tópico",
  "tipo": "analise | breaking | tutorial | ferramenta | viral | comportamento",
  "complexidade": "simples | media | densa",
  "plataformas": [
    {
      "plataforma": "x_twitter | tiktok | instagram | linkedin | newsletter",
      "fit": "alto | medio | baixo",
      "postar": true,
      "razao": "Por que funciona ou não nessa plataforma. 1-2 frases diretas.",
      "angulo": "Se postar=true: qual ângulo/gancho específico usar aqui. 1 frase.",
      "prioridade": 1
    }
  ],
  "ordem_publicacao": ["x_twitter", "linkedin"],
  "observacao_editorial": "Algo importante sobre como tratar esse tópico. Máximo 2 frases."
}

A lista plataformas deve ter TODAS as 5 plataformas, mas postar=false para as que não encaixam.
ordem_publicacao: só as que têm postar=true, ordenadas da mais para menos urgente.
RETORNE SOMENTE O JSON."""


def analisar_fit(topico: str, corpo_artigo: str = "") -> dict:
    """Chama Claude para analisar fit editorial por plataforma."""
    client = anthropic.Anthropic(api_key=API_KEY)

    contexto = f"TÓPICO / NOTÍCIA:\n{topico}"
    if corpo_artigo:
        contexto += f"\n\nCORPO DO ARTIGO (primeiros 1500 chars):\n{corpo_artigo[:1500]}"

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_ANALISE,
        messages=[{"role": "user", "content": contexto}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────

ICONS = {
    "x_twitter":  "𝕏  X/Twitter ",
    "tiktok":     "🎵 TikTok     ",
    "instagram":  "📸 Instagram  ",
    "linkedin":   "💼 LinkedIn   ",
    "newsletter": "📧 Newsletter ",
}

FIT_ICONS = {
    "alto":  "🟢",
    "medio": "🟡",
    "baixo": "🔴",
}


def exibir_analise(analise: dict):
    print("\n" + "=" * 60)
    print("📊  ANÁLISE EDITORIAL — ONDE PUBLICAR")
    print("=" * 60)

    print(f"\n📌 {analise['resumo']}")
    print(f"   Tipo: {analise['tipo']}  |  Complexidade: {analise['complexidade']}")

    print("\n" + "─" * 60)
    print("  PLATAFORMAS (por prioridade)")
    print("─" * 60)

    plataformas = sorted(analise["plataformas"], key=lambda p: p["prioridade"])

    for p in plataformas:
        icone    = ICONS.get(p["plataforma"], p["plataforma"])
        fit_icon = FIT_ICONS.get(p["fit"], "⚪")
        status   = "✅ POSTAR" if p["postar"] else "⏭  SKIP  "

        print(f"\n  {icone} {fit_icon} {p['fit'].upper():5}  [{status}]")
        print(f"  └─ {p['razao']}")
        if p["postar"] and p.get("angulo"):
            print(f"     Ângulo: {p['angulo']}")

    print("\n" + "─" * 60)
    ordem = " → ".join(analise.get("ordem_publicacao", []))
    print(f"  Ordem de publicação: {ordem}")

    if analise.get("observacao_editorial"):
        print(f"\n  ⚡ {analise['observacao_editorial']}")

    print("=" * 60)


def salvar_plano(analise: dict, topico: str):
    """Salva o plano de distribuição como JSON para uso posterior."""
    pasta = SOCIAL_DIR / "planos"
    pasta.mkdir(parents=True, exist_ok=True)

    data = datetime.now().strftime("%Y%m%d_%H%M")
    slug = re.sub(r"[^a-z0-9]", "_", topico.lower())[:40]
    nome = f"{data}_{slug}.json"

    payload = {
        "topico":     topico,
        "data":       datetime.now().isoformat(),
        "analise":    analise,
    }

    caminho = pasta / nome
    caminho.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  💾 Plano salvo: {caminho}")
    return caminho


# ─────────────────────────────────────────────
# GERAÇÃO DE CONTEÚDO (só para plataformas aprovadas)
# ─────────────────────────────────────────────

SYSTEM_CONTEUDO = """Você é o estrategista de conteúdo do JOÃOGPT — mídia tech brasileira sobre IA.

Voz: humana, moderna, internet-native, analítica, levemente opinativa. Frases curtas. Sem corporativês.
NUNCA usar: travessões (— –), "nesse contexto", "vale destacar", "isso representa", "mudança de paradigma".
SEMPRE: contexto brasileiro, opinião editorial real, frases curtas, agradável no celular.

Gere conteúdo APENAS para as plataformas indicadas, com o ângulo especificado.

Retorne SOMENTE um JSON com as plataformas solicitadas como chaves. Exemplo:
{
  "x_twitter": { "post_unico": "...", "thread": ["tweet1", "tweet2", ...] },
  "linkedin":  { "post": "...", "hashtags": ["#IA", ...] }
}

Especificações:

X_TWITTER:
{
  "post_unico": "Tweet único até 280 chars com link e 2-3 hashtags.",
  "thread": ["Tweet 1/N abre sem dizer 'thread'", "Tweet 2/N ...", "Tweet final com link"]
}
Thread de 5-6 tweets. Cada um max 280 chars.

TIKTOK:
{
  "hook": "Frase de 3-5 segundos. Máximo 12 palavras.",
  "roteiro": "Roteiro 30-45 segundos com [PAUSA] [MOSTRAR TELA] [TEXTO NA TELA: ...]",
  "cta": "Chamada final 1 frase.",
  "hashtags": ["#ia", ...]
}

INSTAGRAM:
{
  "caption": "Legenda. Começa com gancho sem emoji. Parágrafos curtos. Máx 300 palavras.",
  "cta": "Última linha CTA.",
  "hashtags": ["#ia", ...] 20-25 hashtags
}
+ slides de carousel se for carrossel:
{
  "slides": [
    {"numero":1,"tipo":"capa","titulo":"...","subtitulo":"..."},
    {"numero":2,"tipo":"ponto","titulo":"...","texto":"...","emoji":"..."},
    ...
    {"numero":7,"tipo":"cta","titulo":"...","cta":"...","acao":"Salve!"}
  ]
}

LINKEDIN:
{
  "post": "Post profissional. 1ª linha aparece antes do 'ver mais'. Termina com pergunta. Máx 1300 chars.",
  "hashtags": ["#InteligenciaArtificial", ...]
}

NEWSLETTER:
{
  "assunto": "Linha de assunto. Máx 50 chars.",
  "preview": "Preview text. 80-90 chars.",
  "snippet": "Parágrafo 3-4 linhas apresentando a notícia.",
  "cta_texto": "Texto do botão CTA",
  "cta_url": "URL do artigo"
}"""


def gerar_conteudo_selecionado(analise: dict, topico: str, corpo: str = "") -> dict:
    """Gera conteúdo só para plataformas aprovadas, com ângulo específico."""
    aprovadas = [p for p in analise["plataformas"] if p["postar"]]

    if not aprovadas:
        print("\n⚠️  Nenhuma plataforma aprovada para publicação.")
        return {}

    specs = []
    for p in aprovadas:
        specs.append(f"- {p['plataforma'].upper()}: {p['angulo']}")

    blog_url = f"{BLOG_URL}/artigos"

    prompt = f"""Tópico: {topico}

Gere conteúdo APENAS para estas plataformas com os ângulos indicados:
{chr(10).join(specs)}

URL do blog: {blog_url}
URL newsletter: {NEWSLETTER_URL}

Corpo do artigo (contexto):
{corpo[:2000] if corpo else "(sem artigo — gere baseado no tópico)"}"""

    client = anthropic.Anthropic(api_key=API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_CONTEUDO,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return json.loads(raw)


def salvar_conteudo(conteudo: dict, topico: str):
    """Salva cada formato em sua pasta."""
    data = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r"[^a-z0-9]", "-", topico.lower())[:50]
    prefix = f"{data}_{slug}"

    mapa_pastas = {
        "x_twitter":  "twitter",
        "tiktok":     "tiktok",
        "instagram":  "instagram",
        "linkedin":   "linkedin",
        "newsletter": "newsletter",
    }

    for plataforma, dados in conteudo.items():
        pasta_nome = mapa_pastas.get(plataforma, plataforma)
        pasta = SOCIAL_DIR / pasta_nome
        pasta.mkdir(parents=True, exist_ok=True)

        caminho = pasta / f"{prefix}.json"
        caminho.write_text(
            json.dumps({"topico": topico, "plataforma": plataforma, "conteudo": dados},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  ✅ {plataforma:<12} → {caminho.name}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def run(topico: str = None, arquivo: str = None, gerar: bool = False):
    if anthropic is None:
        print("❌ Pacote anthropic não instalado. Rode: pip install -r requirements.txt")
        return
    if not API_KEY:
        print("❌ ANTHROPIC_API_KEY não encontrada no .env")
        return

    corpo = ""

    # Carrega artigo se passado
    if arquivo:
        caminho = Path(arquivo)
        if not caminho.exists():
            print(f"❌ Arquivo não encontrado: {arquivo}")
            return
        texto = caminho.read_text(encoding="utf-8")
        # Extrai corpo sem frontmatter
        if texto.startswith("---"):
            partes = texto.split("---", 2)
            corpo = partes[2].strip() if len(partes) >= 3 else texto
        else:
            corpo = texto

        if not topico:
            # Extrai título do frontmatter como tópico
            for linha in texto.split("\n"):
                if linha.startswith("titulo:"):
                    topico = linha.split(":", 1)[1].strip().strip('"')
                    break
            if not topico:
                topico = caminho.stem

    # Pergunta interativamente se não passou tópico
    if not topico:
        print("\n📰 DISTRIBUTION PLANNER — JOÃOGPT")
        print("─" * 40)
        print("Descreva a notícia/tópico em 1-3 frases:")
        print("(Ex: 'Meta abriu o Ads pra Claude via MCP. 29 ferramentas. Interface pode morrer.')\n")
        topico = input("> ").strip()
        if not topico:
            print("❌ Tópico vazio.")
            return

    print(f"\n🔍 Analisando fit editorial...")
    analise = analisar_fit(topico, corpo)
    exibir_analise(analise)
    salvar_plano(analise, topico)

    if gerar:
        aprovadas = [p for p in analise["plataformas"] if p["postar"]]
        if not aprovadas:
            print("\n⚠️  Nenhuma plataforma aprovada. Conteúdo não gerado.")
            return

        nomes = [p["plataforma"] for p in aprovadas]
        print(f"\n✍️  Gerando conteúdo para: {', '.join(nomes)}...")
        conteudo = gerar_conteudo_selecionado(analise, topico, corpo)

        print("\n📁 Salvando arquivos:")
        salvar_conteudo(conteudo, topico)
        print("\n✅ Pronto!")
    else:
        print("\n  💡 Para gerar o conteúdo das plataformas aprovadas:")
        cmd = f'python content/distribution_planner.py --topico "{topico}" --gerar'
        if arquivo:
            cmd = f'python content/distribution_planner.py --arquivo "{arquivo}" --gerar'
        print(f"  {cmd}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Decide onde publicar uma notícia antes de gerar conteúdo."
    )
    parser.add_argument("--topico",  type=str, default=None,
                        help="Descrição da notícia/tópico em 1-3 frases")
    parser.add_argument("--arquivo", type=str, default=None,
                        help="Caminho para um artigo .md já escrito")
    parser.add_argument("--gerar",   action="store_true",
                        help="Após analisar, gera o conteúdo das plataformas aprovadas")
    args = parser.parse_args()

    run(topico=args.topico, arquivo=args.arquivo, gerar=args.gerar)
