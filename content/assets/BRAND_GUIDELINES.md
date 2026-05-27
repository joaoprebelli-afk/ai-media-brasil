# Brand Guidelines — Blog de IA em Português
**Versão:** 1.0 | **Tema:** AI Premium · Dark Mode · Moderno · Minimalista

---

## 1. FILOSOFIA DE MARCA

### Princípios visuais
- **Clareza antes de decoração** — cada elemento existe por uma razão funcional
- **Contraste como hierarquia** — o olho deve saber instantaneamente o que ler primeiro
- **Tecnologia com humanidade** — premium e técnico, mas acessível para brasileiros
- **Consistência sistêmica** — templates são sistemas, não layouts únicos

### Personalidade visual
Austero como um terminal. Atraente como um produto Apple. Confiável como um dashboard de empresa séria.

---

## 2. PALETA DE CORES

### Cores base (backgrounds)
| Nome         | Hex       | Uso                                      |
|--------------|-----------|------------------------------------------|
| Void         | `#080810` | Background mais escuro (thumbnails)      |
| Abyss        | `#0D0D1A` | Background padrão de cards               |
| Surface      | `#13131F` | Superfícies elevadas, painéis            |
| Surface High  | `#1C1C2E` | Cards, modais, elementos flutuantes      |
| Border       | `#2A2A42` | Bordas sutis, divisores                  |

### Cores de acento (brand colors)
| Nome         | Hex       | Uso                                      |
|--------------|-----------|------------------------------------------|
| Verde        | `#C4F55A` | Cor primária — CTAs, destaques, glow     |
| Verde Soft   | `#4ADE80` | Cor secundária — ícones, subtítulos      |
| Verde Deep   | `#22C55E` | Gradientes, elementos de ênfase          |
| Azul Suave   | `#6BA8FF` | Contraste ocasional, badges técnicos     |

### Gradientes (use sempre que precisar de energia visual)
```
Brand Gradient:    #C4F55A → #4ADE80  (diagonal 135°)
Green Shift:       #22C55E → #C4F55A  (vertical)
Green Glow:        #0A0A0B → #C4F55A  (radial, centro suave)
Dark Surface:      #080810 → #1C1C2E  (vertical, fundo)
Alert Gradient:    #FF6B6B → #FF8E53  (somente erros/urgência)
```

### Cores de texto
| Nome           | Hex       | Uso                                      |
|----------------|-----------|------------------------------------------|
| White          | `#FFFFFF` | Títulos principais, headlines            |
| Off-White      | `#F0F0FF` | Corpo de texto, parágrafos               |
| Muted          | `#A0A0C0` | Subtítulos, labels, metadata             |
| Ghost          | `#5A5A7A` | Placeholders, texto inativo              |

### Cores de status (badges e indicadores)
| Estado     | Hex       |
|------------|-----------|
| Sucesso    | `#10B981` |
| Alerta     | `#F59E0B` |
| Erro       | `#EF4444` |
| Info       | `#6BA8FF` |

---

## 3. TIPOGRAFIA

### Stack de fontes

**Headlines (Títulos principais)**
```
Font: Space Grotesk
Peso: 700 (Bold) e 800 (ExtraBold)
Fallback: Inter, system-ui, sans-serif
Google Fonts: https://fonts.google.com/specimen/Space+Grotesk
```

**Corpo de texto**
```
Font: Inter
Peso: 400 (Regular), 500 (Medium)
Fallback: -apple-system, system-ui, sans-serif
Google Fonts: https://fonts.google.com/specimen/Inter
```

**Labels e código**
```
Font: JetBrains Mono
Peso: 400, 500
Uso: percentuais, números de score, código, tags técnicas
Google Fonts: https://fonts.google.com/specimen/JetBrains+Mono
```

### Escala tipográfica

#### Para thumbnails (1280×720px)
| Elemento       | Fonte          | Peso | Tamanho | Line-height |
|----------------|----------------|------|---------|-------------|
| Headline       | Space Grotesk  | 800  | 72-88px | 1.0         |
| Subtítulo      | Inter          | 500  | 28-32px | 1.3         |
| Badge/tag      | JetBrains Mono | 500  | 18px    | 1.0         |
| Fonte/crédito  | Inter          | 400  | 14px    | 1.0         |

#### Para reels covers (1080×1920px)
| Elemento       | Fonte          | Peso | Tamanho | Line-height |
|----------------|----------------|------|---------|-------------|
| Hook (1ª linha)| Space Grotesk  | 800  | 64-80px | 1.0         |
| Corpo          | Inter          | 500  | 34-40px | 1.2         |
| CTA inferior   | Space Grotesk  | 700  | 28px    | 1.0         |
| Handle         | JetBrains Mono | 400  | 22px    | 1.0         |

#### Para carousel (1080×1080px)
| Elemento       | Fonte          | Peso | Tamanho | Line-height |
|----------------|----------------|------|---------|-------------|
| Número slide   | JetBrains Mono | 400  | 20px    | 1.0         |
| Título card    | Space Grotesk  | 700  | 48-56px | 1.05        |
| Corpo          | Inter          | 400  | 28-32px | 1.5         |
| CTA            | Space Grotesk  | 700  | 30px    | 1.0         |

---

## 4. ESPAÇAMENTO E GRID

### Grid base: múltiplos de 8px
```
4px   — micro espaçamento (padding interno de badges)
8px   — espaçamento mínimo entre elementos
16px  — espaçamento padrão
24px  — espaçamento médio
32px  — espaçamento grande
48px  — separação de seções
64px  — margens de segurança nos cantos
```

### Safe zones (área segura para texto)
```
Thumbnail (1280×720):   Margem 64px todos os lados
Reel Cover (1080×1920): Margem 80px lateral, 120px topo/base
Carousel (1080×1080):   Margem 72px todos os lados
```

---

## 5. ELEMENTOS VISUAIS RECORRENTES

### 5.1 Gradient Border (borda com gradiente)
Usar em cards e panels principais.
```
border: 1px solid transparent
background-clip: padding-box
background-image: linear-gradient(#13131F, #13131F),
                  linear-gradient(135deg, #C4F55A, #4ADE80)
```

### 5.2 Glow Effect (brilho de acento)
Sutil — apenas em elementos de destaque máximo.
```
box-shadow: 0 0 40px rgba(196, 245, 90, 0.25),
            0 0 80px rgba(196, 245, 90, 0.10)
```

### 5.3 Grid Overlay (malha técnica de fundo)
Opcional — adiciona sensação de precisão técnica.
```
background-image: linear-gradient(rgba(196,245,90,0.03) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(196,245,90,0.03) 1px, transparent 1px)
background-size: 40px 40px
```

### 5.4 Badge / Tag style
```
Background: rgba(196, 245, 90, 0.12)
Border: 1px solid rgba(196, 245, 90, 0.35)
Border-radius: 6px
Padding: 4px 12px
Font: JetBrains Mono 500 14-18px
Cor texto: #C4F55A ou #4ADE80
```

### 5.5 Texto gradiente
Para palavras-chave no título que precisam de máximo impacto:
```
background: linear-gradient(135deg, #C4F55A, #4ADE80)
-webkit-background-clip: text
-webkit-text-fill-color: transparent
```

---

## 6. TEMPLATES

### 6.1 Thumbnail (1280×720px — 16:9)
**Anatomia:**
```
┌─────────────────────────────────────────────┐
│  [badge top-left: fonte/empresa]            │
│                                             │
│  [HEADLINE GRANDE                           │
│   ATÉ 2 LINHAS]                             │
│                                             │
│  [subtítulo opcional — 1 linha]             │
│                                             │
│                     [elemento visual right] │
│  [@handle]           [logo blog]            │
└─────────────────────────────────────────────┘
```
**Regras:**
- Background: Void (`#080810`) com grid overlay sutil
- Headline: máximo 8 palavras, 2 linhas
- Elemento visual direito: ícone/glyph relacionado ao tema, em gradiente
- Badge top-left: fonte da notícia (ex: "ANTHROPIC • OFICIAL")
- Sempre incluir @handle e logo no rodapé

### 6.2 Reel Cover (1080×1920px — 9:16)
**Anatomia:**
```
┌─────────────────┐
│ [logo + handle] │ ← top-left
│                 │
│                 │
│  [HOOK em       │
│   letras        │
│   grandes]      │
│                 │
│  [subtítulo     │
│   1-2 linhas]   │
│                 │
│ [CTA → ASSISTE] │ ← bottom-center
└─────────────────┘
```
**Regras:**
- Background: gradiente vertical escuro com glow central
- Hook: máximo 6 palavras, centrado, tamanho máximo possível
- CTA inferior: pill com gradiente brand (ex: "▶ ASSISTE ATÉ O FINAL")
- Sem elementos visuais que concorram com o texto

### 6.3 Carousel (1080×1080px — 1:1)

**Slide Capa (slide 1):**
```
┌─────────────────────┐
│ [nº] ●●●●●●        │ ← indicador de slides top-right
│                     │
│  [TÍTULO EM         │
│   DESTAQUE]         │
│                     │
│  [subtítulo curto]  │
│                     │
│ [@handle]  [logo]   │
└─────────────────────┘
```

**Slides de Conteúdo (slides 2-N):**
```
┌─────────────────────┐
│ [02/07]             │ ← numeração JetBrains Mono
│                     │
│ [Título do          │
│  ponto]             │
│                     │
│ [Corpo explicativo  │
│  2-3 linhas]        │
│                     │
│ [detalhe visual     │
│  ou ícone]          │
└─────────────────────┘
```

**Slide CTA (último slide):**
```
┌─────────────────────┐
│                     │
│  [Gostou?           │
│   Salva e           │
│   compartilha]      │
│                     │
│  [→ Segue para      │
│    mais]            │
│                     │
│  [@handle]  [logo]  │
└─────────────────────┘
```

---

## 7. REGRAS DE COMPOSIÇÃO

### O que SEMPRE fazer
- ✅ Manter o texto na safe zone (64-80px das bordas)
- ✅ Usar gradiente no máximo em 1 elemento por slide
- ✅ Ter no máximo 2 fontes visíveis por asset
- ✅ Garantir contraste mínimo 4.5:1 texto/fundo (WCAG AA)
- ✅ Usar o número do slide (formato `01/07`) em JetBrains Mono
- ✅ Testar como fica em thumbnail pequeno (150px de largura)

### O que NUNCA fazer
- ❌ Fundo branco ou claro — sempre dark mode
- ❌ Mais de 3 cores de acento em um único asset
- ❌ Texto menor que 28px em qualquer formato final
- ❌ Imagens de banco de imagem (evitar ao máximo)
- ❌ Gradiente em texto E em borda no mesmo elemento
- ❌ Headline com mais de 10 palavras
- ❌ Emojis no meio do título de thumbnail

---

## 8. NOMENCLATURA DE ARQUIVOS

```
thumbnail_YYYYMMDD_[slug].png
reel-cover_YYYYMMDD_[slug].png
carousel_YYYYMMDD_[slug]_slide[N].png
carousel_YYYYMMDD_[slug].json     ← dados para automação
```

**Exemplo:**
```
thumbnail_20260508_xai-anthropic-parceria.png
reel-cover_20260508_xai-anthropic-parceria.png
carousel_20260508_xai-anthropic-parceria_slide01.png
carousel_20260508_xai-anthropic-parceria_slide07.png
carousel_20260508_xai-anthropic-parceria.json
```

---

## 9. PASTAS DO PROJETO

```
content/assets/
├── BRAND_GUIDELINES.md          ← este documento
├── thumbnails/
│   ├── template_base.json       ← prompt base para Higgsfield
│   └── YYYYMMDD_slug.png
├── reels/
│   ├── template_base.json
│   └── YYYYMMDD_slug.mp4
└── carousel/
    ├── template_base.json
    ├── YYYYMMDD_slug_slide01.png
    └── YYYYMMDD_slug.json
```

---

## 10. TOKENS PARA AUTOMAÇÃO (Higgsfield / Canva / Figma)

Use estes valores exatos nos prompts de geração de imagem:

```
STYLE_PROMPT_BASE = """
dark mode, premium AI aesthetic, minimalist, high contrast,
deep black background (#0A0A0B), lime green (#C4F55A) accent with subtle glow,
Space Grotesk typography, clean geometric composition,
subtle grid overlay, green neon glow effects, 8K quality, no noise
"""

STYLE_NEGATIVE = """
white background, light mode, cartoon, illustration, stock photo,
busy composition, serif fonts, gradients on text AND border simultaneously,
emoji, watermark, low contrast
"""
```

---

*Documento gerado automaticamente pelo sistema de conteúdo de IA — blog de ai em portugues*
*Atualizar sempre que novos formatos ou plataformas forem adicionados.*
