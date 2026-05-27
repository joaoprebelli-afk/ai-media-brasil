#!/usr/bin/env python3
"""
JOÃOGPT — Carousel Generator
-----------------------------
Lê um artigo markdown, chama Claude API, gera slides prontos para Instagram (1080x1350).
Exporta um HTML self-contained com botão de download PNG por slide.

Uso:
    python content/generate_carousel.py <slug-do-artigo>

Exemplo:
    python content/generate_carousel.py google-io-play-store-tiktok-software

Requisito:
    pip install anthropic
    Variável ANTHROPIC_API_KEY no ambiente (ou .env)
"""

import anthropic
import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
POSTS_DIR    = PROJECT_ROOT / "posts"
OUTPUT_DIR   = PROJECT_ROOT / "posts"

BRAND = {
    "name":    "JOÃOGPT",
    "handle":  "@joaogptbr",
    "url":     "joaogpt.com",
    "green":   "#C4F55A",
    "dark":    "#0A0A0B",
    "surface": "#111117",
    "muted":   "#4A4A62",
}

# ── Find article ──────────────────────────────────────────────────────────────

def find_article(slug: str) -> tuple[Path, str]:
    """Find markdown file matching the slug."""
    for f in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        if slug in f.name:
            return f, f.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Nenhum artigo encontrado com slug '{slug}' em {POSTS_DIR}\n"
        f"Arquivos disponíveis: {[f.name for f in POSTS_DIR.glob('*.md')]}"
    )

def extract_title(content: str) -> str:
    """Extract title from markdown frontmatter or first heading."""
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Artigo JOÃOGPT"

# ── Claude call ───────────────────────────────────────────────────────────────

SLIDE_SYSTEM = """Você é o assistente editorial do JOÃOGPT, mídia tech brasileira sobre IA.
Seu trabalho é transformar artigos em carrosséis para Instagram/Reels.

Estilo JOÃOGPT:
- Frases curtas e diretas. Sem rodeios.
- Contexto Brasil sempre: o que isso significa PRO BRASILEIRO.
- Sem travessões (—). Use ponto, vírgula ou dois-pontos.
- Linguagem acessível mas não simplória. Tom: amigo inteligente.
- Números concretos quando existirem. Generalizações só quando necessário."""

SLIDE_PROMPT = """Leia o artigo abaixo e crie 8 slides para um carrossel Instagram (1080x1350).

ARTIGO:
{article}

Retorne APENAS um JSON array com exatamente 8 objetos. Cada objeto:

{{
  "type": "hook" | "body" | "stat" | "quote" | "list" | "cta",
  "headline": "texto principal (curto, impactante)",
  "subtext": "texto de apoio (opcional, mais curto que headline)",
  "items": ["item 1", "item 2", "item 3"],   // só para type="list", máx 4 items
  "stat_number": "47%",                       // só para type="stat"
  "stat_label": "dos devs já usam IA"         // só para type="stat"
}}

REGRAS OBRIGATÓRIAS:
- Slide 1: type="hook". Frase que para o scroll. Máx 10 palavras.
- Slide 8: type="cta". Chamada para seguir @joaogptbr e assinar newsletter.
- Slides 2-7: mix de body, stat, quote, list. Mínimo 1 stat e 1 list.
- Todo texto em português do Brasil.
- Sem travessões.
- headline sempre presente. subtext opcional.

Output: SOMENTE o JSON array. Zero texto adicional."""


def generate_slides(article: str, client: anthropic.Anthropic) -> list[dict]:
    """Call Claude to generate slide content."""
    print("  Chamando Claude API...")
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SLIDE_SYSTEM,
        messages=[{
            "role": "user",
            "content": SLIDE_PROMPT.format(article=article[:8000])  # truncate if huge
        }]
    )
    raw = msg.content[0].text.strip()
    # Strip markdown code block if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    slides = json.loads(raw)
    print(f"  {len(slides)} slides gerados.")
    return slides

# ── HTML renderer ─────────────────────────────────────────────────────────────

def render_slide_html(slide: dict, index: int, total: int) -> str:
    """Render a single slide as HTML."""
    t = slide.get("type", "body")
    headline = slide.get("headline", "")
    subtext  = slide.get("subtext", "")
    items    = slide.get("items", [])
    stat_num = slide.get("stat_number", "")
    stat_lbl = slide.get("stat_label", "")

    content_html = ""

    if t == "hook":
        content_html = f"""
        <div class="slide-hook">
          <div class="slide-hook-label">O que você precisa saber</div>
          <h2 class="slide-headline hook-headline">{headline}</h2>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
        </div>"""

    elif t == "stat":
        content_html = f"""
        <div class="slide-stat">
          <div class="stat-number">{stat_num}</div>
          <div class="stat-label">{stat_lbl}</div>
          <h2 class="slide-headline stat-headline">{headline}</h2>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
        </div>"""

    elif t == "quote":
        content_html = f"""
        <div class="slide-quote">
          <div class="quote-mark">"</div>
          <h2 class="slide-headline quote-headline">{headline}</h2>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
        </div>"""

    elif t == "list":
        items_html = "".join(
            f'<li class="list-item"><span class="list-dot"></span>{item}</li>'
            for item in items[:4]
        )
        content_html = f"""
        <div class="slide-list">
          <h2 class="slide-headline list-headline">{headline}</h2>
          <ul class="slide-items">{items_html}</ul>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
        </div>"""

    elif t == "cta":
        content_html = f"""
        <div class="slide-cta">
          <div class="cta-logo">JOÃO<span>GPT</span></div>
          <h2 class="slide-headline cta-headline">{headline}</h2>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
          <div class="cta-actions">
            <div class="cta-pill">Seguir @joaogptbr</div>
            <div class="cta-pill cta-pill-outline">joaogpt.com</div>
          </div>
        </div>"""

    else:  # body
        content_html = f"""
        <div class="slide-body">
          <h2 class="slide-headline">{headline}</h2>
          {"<p class='slide-subtext'>" + subtext + "</p>" if subtext else ""}
        </div>"""

    # Slide counter dots
    dots_html = "".join(
        f'<span class="dot {"dot-active" if i == index else ""}"></span>'
        for i in range(1, total + 1)
    )

    return f"""
    <div class="slide" id="slide-{index}" data-index="{index}">
      <!-- Header -->
      <div class="slide-header">
        <span class="slide-logo">JOÃO<span class="slide-logo-accent">GPT</span></span>
        <span class="slide-counter">{index}/{total}</span>
      </div>

      <!-- Content -->
      <div class="slide-content">
        {content_html}
      </div>

      <!-- Footer -->
      <div class="slide-footer">
        <div class="slide-dots">{dots_html}</div>
        <span class="slide-handle">@joaogptbr</span>
      </div>

      <!-- Export button (hidden in export mode) -->
      <button class="slide-export-btn" onclick="exportSlide({index})" title="Download PNG">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
        </svg>
      </button>
    </div>"""


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carousel — {title} | JOÃOGPT</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

  <style>
    /* ── Reset ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #060609;
      color: #E8E8F0;
      font-family: 'Space Grotesk', sans-serif;
      min-height: 100vh;
      padding: 40px 20px 80px;
    }}

    /* ── Page header ── */
    .page-header {{
      max-width: 560px;
      margin: 0 auto 40px;
      text-align: center;
    }}
    .page-logo {{
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #E8E8F0;
      margin-bottom: 8px;
    }}
    .page-logo span {{ color: #C4F55A; }}
    .page-title {{
      font-size: clamp(1rem, 3vw, 1.2rem);
      color: #4A4A62;
      margin-bottom: 24px;
      font-weight: 400;
    }}
    .page-actions {{
      display: flex;
      gap: 10px;
      justify-content: center;
      flex-wrap: wrap;
    }}
    .btn-dl-all {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 10px 20px;
      background: #C4F55A;
      color: #080810;
      border: none;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      transition: opacity 0.15s;
    }}
    .btn-dl-all:hover {{ opacity: 0.88; }}
    .btn-copy-json {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 10px 20px;
      background: transparent;
      color: #8B8B9E;
      border: 1px solid #2A2A42;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: color 0.15s, border-color 0.15s;
    }}
    .btn-copy-json:hover {{ color: #E8E8F0; border-color: #4A4A62; }}

    /* ── Slides grid ── */
    .slides-grid {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 32px;
    }}

    /* ── Single slide ── */
    /* Real dimensions: 1080x1350 — displayed at 50% scale for usability */
    .slide {{
      position: relative;
      width: 540px;
      height: 675px;
      background: linear-gradient(160deg, #0D0D12 0%, #111117 100%);
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #1C1C2A;
      /* This div represents a 1080x1350 slide at 50% scale */
      transform-origin: top center;
      flex-shrink: 0;
    }}
    .slide::before {{
      content: '';
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 70% 40% at 50% 0%, rgba(196,245,90,0.07), transparent 60%),
        radial-gradient(ellipse 40% 40% at 100% 100%, rgba(196,245,90,0.04), transparent 60%);
      pointer-events: none;
    }}

    /* ── Slide header ── */
    .slide-header {{
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      padding: 20px 24px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 2;
    }}
    .slide-logo {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #E8E8F0;
    }}
    .slide-logo-accent {{ color: #C4F55A; }}
    .slide-counter {{
      font-size: 11px;
      font-weight: 600;
      color: #4A4A62;
      letter-spacing: 0.05em;
    }}

    /* ── Slide content ── */
    .slide-content {{
      position: absolute;
      inset: 60px 24px 80px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    /* ── Hook slide ── */
    .slide-hook {{ text-align: left; width: 100%; }}
    .slide-hook-label {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #C4F55A;
      margin-bottom: 14px;
    }}
    .hook-headline {{
      font-size: clamp(1.4rem, 4vw, 2rem);
      font-weight: 700;
      letter-spacing: -0.03em;
      line-height: 1.15;
      color: #FFFFFF;
      margin-bottom: 14px;
    }}

    /* ── Stat slide ── */
    .slide-stat {{ text-align: center; width: 100%; }}
    .stat-number {{
      font-size: clamp(3rem, 12vw, 5rem);
      font-weight: 700;
      letter-spacing: -0.04em;
      color: #C4F55A;
      line-height: 1;
      margin-bottom: 8px;
    }}
    .stat-label {{
      font-size: 0.9rem;
      color: #8B8B9E;
      margin-bottom: 20px;
      font-weight: 500;
    }}
    .stat-headline {{
      font-size: clamp(1rem, 3vw, 1.4rem);
      font-weight: 600;
      letter-spacing: -0.02em;
      line-height: 1.3;
      color: #E8E8F0;
    }}

    /* ── Quote slide ── */
    .slide-quote {{ text-align: left; width: 100%; }}
    .quote-mark {{
      font-size: 5rem;
      color: #C4F55A;
      line-height: 0.8;
      margin-bottom: 8px;
      font-family: Georgia, serif;
    }}
    .quote-headline {{
      font-size: clamp(1.1rem, 3.5vw, 1.6rem);
      font-weight: 600;
      font-style: italic;
      letter-spacing: -0.02em;
      line-height: 1.4;
      color: #E8E8F0;
    }}

    /* ── List slide ── */
    .slide-list {{ text-align: left; width: 100%; }}
    .list-headline {{
      font-size: clamp(1.1rem, 3vw, 1.5rem);
      font-weight: 700;
      letter-spacing: -0.025em;
      color: #FFFFFF;
      margin-bottom: 20px;
      line-height: 1.3;
    }}
    .slide-items {{ list-style: none; display: flex; flex-direction: column; gap: 12px; }}
    .list-item {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      font-size: 0.9rem;
      color: #C8C8D4;
      line-height: 1.5;
    }}
    .list-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #C4F55A;
      flex-shrink: 0;
      margin-top: 6px;
    }}

    /* ── CTA slide ── */
    .slide-cta {{ text-align: center; width: 100%; }}
    .cta-logo {{
      font-size: 1.3rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #E8E8F0;
      margin-bottom: 20px;
    }}
    .cta-logo span {{ color: #C4F55A; }}
    .cta-headline {{
      font-size: clamp(1.2rem, 4vw, 1.8rem);
      font-weight: 700;
      letter-spacing: -0.025em;
      line-height: 1.25;
      color: #FFFFFF;
      margin-bottom: 10px;
    }}
    .cta-actions {{
      display: flex;
      gap: 10px;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 24px;
    }}
    .cta-pill {{
      display: inline-flex;
      align-items: center;
      padding: 8px 18px;
      background: #C4F55A;
      color: #080810;
      border-radius: 99px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .cta-pill-outline {{
      background: transparent;
      color: #C4F55A;
      border: 1px solid rgba(196, 245, 90, 0.4);
    }}

    /* ── Body slide (default) ── */
    .slide-body {{ text-align: left; width: 100%; }}
    .slide-headline {{
      font-size: clamp(1.1rem, 3.5vw, 1.6rem);
      font-weight: 700;
      letter-spacing: -0.025em;
      line-height: 1.3;
      color: #FFFFFF;
      margin-bottom: 14px;
    }}
    .slide-subtext {{
      font-size: 0.9rem;
      color: #8B8B9E;
      line-height: 1.6;
      font-weight: 400;
    }}

    /* ── Slide footer ── */
    .slide-footer {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 0 24px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid rgba(255,255,255,0.04);
      padding-top: 14px;
    }}
    .slide-dots {{
      display: flex;
      gap: 4px;
      align-items: center;
    }}
    .dot {{
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: #2A2A42;
      transition: background 0.2s;
    }}
    .dot-active {{ background: #C4F55A; }}
    .slide-handle {{
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.06em;
      color: #4A4A62;
    }}

    /* ── Export button (per slide) ── */
    .slide-export-btn {{
      position: absolute;
      top: 16px;
      right: 60px;
      width: 32px;
      height: 32px;
      border-radius: 6px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.08);
      color: #8B8B9E;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-family: inherit;
      transition: color 0.15s, background 0.15s;
      opacity: 0;
      transition: opacity 0.2s;
    }}
    .slide:hover .slide-export-btn {{ opacity: 1; }}
    .slide-export-btn:hover {{ color: #C4F55A; background: rgba(196,245,90,0.1); }}

    /* ── Export mode ── */
    .exporting .slide-header,
    .exporting .slide-footer,
    .exporting .slide-export-btn {{ display: none !important; }}
    .exporting .slide-content {{ inset: 24px; }}

    /* ── Progress ── */
    #progress {{
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1C1C2A;
      border: 1px solid #2A2A42;
      border-radius: 8px;
      padding: 10px 16px;
      font-size: 0.8rem;
      color: #8B8B9E;
      display: none;
    }}
    #progress.visible {{ display: block; }}
  </style>
</head>
<body>

  <div class="page-header">
    <div class="page-logo">JOÃO<span>GPT</span></div>
    <p class="page-title">{title}</p>
    <div class="page-actions">
      <button class="btn-dl-all" onclick="exportAll()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
        </svg>
        Baixar todos ({total} slides)
      </button>
      <button class="btn-copy-json" onclick="copyJson()">
        Copiar JSON
      </button>
    </div>
  </div>

  <div class="slides-grid" id="slides-grid">
    {slides_html}
  </div>

  <div id="progress">Exportando slides...</div>

  <script>
    const SLIDES_JSON = {slides_json};

    function sleep(ms) {{
      return new Promise(resolve => setTimeout(resolve, ms));
    }}

    async function exportSlide(index) {{
      const slide = document.getElementById('slide-' + index);
      if (!slide) return;

      // Temporarily upscale to real dimensions
      slide.style.width  = '1080px';
      slide.style.height = '1350px';
      slide.style.fontSize = '2em';

      const canvas = await html2canvas(slide, {{
        width: 1080,
        height: 1350,
        scale: 1,
        useCORS: true,
        backgroundColor: null,
        logging: false
      }});

      // Restore display size
      slide.style.width  = '';
      slide.style.height = '';
      slide.style.fontSize = '';

      const link = document.createElement('a');
      link.download = `joaogpt-carousel-slide-${{}}{index}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }}

    async function exportAll() {{
      const progress = document.getElementById('progress');
      progress.classList.add('visible');

      for (let i = 1; i <= {total}; i++) {{
        progress.textContent = `Exportando slide ${{}}{i}/{total}...`;
        await exportSlide(i);
        await sleep(800);
      }}

      progress.textContent = 'Pronto!';
      await sleep(2000);
      progress.classList.remove('visible');
    }}

    function copyJson() {{
      navigator.clipboard.writeText(JSON.stringify(SLIDES_JSON, null, 2));
      const btn = document.querySelector('.btn-copy-json');
      btn.textContent = 'Copiado!';
      setTimeout(() => {{ btn.textContent = 'Copiar JSON'; }}, 2000);
    }}
  </script>

</body>
</html>
"""


def build_html(slides: list[dict], title: str, slug: str) -> str:
    slides_html = "\n".join(
        render_slide_html(s, i + 1, len(slides))
        for i, s in enumerate(slides)
    )
    return HTML_TEMPLATE.format(
        title=title,
        slug=slug,
        slides_html=slides_html,
        slides_json=json.dumps(slides, ensure_ascii=False),
        total=len(slides),
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    slug = sys.argv[1].strip()
    print(f"\n🟢 JOÃOGPT Carousel Generator")
    print(f"   Slug: {slug}\n")

    # 1. Find article
    print("1. Buscando artigo...")
    article_path, article_content = find_article(slug)
    title = extract_title(article_content)
    print(f"   Encontrado: {article_path.name}")
    print(f"   Título: {title}")

    # 2. Generate slides
    print("\n2. Gerando slides via Claude API...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("   ⚠️  ANTHROPIC_API_KEY não encontrada no ambiente.")
        print("   Configure com: set ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    slides  = generate_slides(article_content, client)

    # Show preview
    print("\n   Preview dos slides:")
    for i, s in enumerate(slides, 1):
        t = s.get("type", "?").upper()
        h = s.get("headline", "")[:60]
        print(f"   [{i}] {t:<8} {h}")

    # 3. Render HTML
    print("\n3. Renderizando HTML...")
    html = build_html(slides, title, slug)

    # 4. Save
    out_dir = OUTPUT_DIR / f"carousel-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")

    # Also save the JSON for reuse
    json_path = out_dir / "slides.json"
    json_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Pronto!")
    print(f"   HTML:  {out_path}")
    print(f"   JSON:  {json_path}")
    print(f"\n   Próximos passos:")
    print(f"   1. Abra o HTML no Chrome: start {out_path}")
    print(f"   2. Clique 'Baixar todos ({len(slides)} slides)' para exportar os PNGs")
    print(f"   3. Publique no Instagram como carrossel")
    print()


if __name__ == "__main__":
    main()
