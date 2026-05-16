# Blog de IA em Português — Sistema Automatizado de Mídia

Sistema Python para descoberta, curadoria e publicação automatizada de conteúdo sobre inteligência artificial para o público brasileiro.

> **Status:** MVP funcional · Pronto para uso com API key da Anthropic

---

## O que o sistema faz

1. **Descobre** notícias de IA automaticamente (RSS, Hacker News, GitHub)
2. **Filtra** usando IA (Claude Haiku) para avaliar relevância para brasileiros
3. **Gera** artigos completos em português, otimizados para SEO
4. **Produz** assets para 6 plataformas sociais em uma única chamada de API
5. **Salva** tudo localmente em Markdown + SQLite

---

## Arquitetura

```
blog de ai em portugues/
│
├── discovery/                    ← NOVO: descoberta automática de oportunidades
│   └── discovery_engine.py       RSS + Hacker News + GitHub Trending AI
│                                  Virality score: recency · authority · AI relevance · engagement
│
├── collector/
│   └── rss_collector.py          Coleta feeds RSS de empresas oficiais de IA
│
├── processor/
│   └── processor.py              Claude Haiku: resume + score 0-10 por relevância BR
│
├── content/
│   ├── blog_generator.py         Claude Opus: artigo SEO completo em PT-BR
│   ├── social_generator.py       6 formatos sociais em 1 chamada de API
│   ├── higgsfield_generator.py   Geração de thumbnails e reels via Higgsfield AI
│   ├── output/                   Artigos gerados (.md com frontmatter YAML)
│   ├── social/                   Assets por plataforma (tiktok/ instagram/ etc.)
│   └── assets/                   Thumbnails, reels, carousel (imagens/vídeos)
│
├── automation/
│   ├── pipeline.py               Orquestra todas as etapas com retry e logging
│   └── logs/                     Log de cada execução (pipeline_YYYYMMDD.log)
│
├── data/
│   ├── articles.db               SQLite: artigos (status: raw→processed→generated→social_done)
│   └── discoveries.db            SQLite: discoveries com virality score
│
├── .env.example                  Template de variáveis de ambiente
├── .gitignore                    Ignora .env, *.db, outputs gerados
├── requirements.txt              Dependências Python
├── QUICKSTART.md                 Setup em 5 minutos
└── README_FINAL.md               Este arquivo
```

---

## Fluxo de dados

```
Discovery Engine          Pipeline Principal
─────────────────         ──────────────────────────────────────────────
RSS (9 feeds)  ─┐
Hacker News    ─┼─▶ score ─▶ discoveries.db ─▶ articles.db (raw)
GitHub AI      ─┘                                     │
                                                       ▼
                                             processor.py (Haiku)
                                             score 0-10 · resumo PT-BR
                                                       │
                                           ┌──────────┴────────────┐
                                        rejected              processed
                                        (score<4)             (score≥4)
                                                                   │
                                                                   ▼
                                                       blog_generator.py (Opus)
                                                       título · meta · corpo · CTA
                                                                   │
                                                                   ▼
                                                       social_generator.py (Opus)
                                                       TikTok · Instagram · Carousel
                                                       Twitter · LinkedIn · Newsletter
```

---

## Módulos em detalhe

### discovery_engine.py

Encontra notícias **antes** de você precisar enviá-las manualmente.

**Fontes:**
- 9 blogs oficiais via RSS (OpenAI, Anthropic, Google AI, DeepMind, NVIDIA, Meta AI, HuggingFace, Mistral, Cohere)
- Hacker News Top Stories (Firebase API — sem autenticação)
- Hacker News AI Search (Algolia — busca por "AI", "LLM", "GPT" nas últimas 48h)
- GitHub Trending AI (repositórios criados recentemente com stars altas nos topics `llm`, `ai-agent`)

**Virality Score (0.0 → 1.0):**

| Componente | Peso | Descrição |
|---|---|---|
| Recency | 30% | Decaimento exponencial `e^(-0.025 × horas)` |
| Authority | 25% | Blog oficial (1.0) > HN (0.82) > GitHub (0.70) |
| AI Relevance | 25% | Presença de keywords de IA no título |
| Engagement | 20% | Upvotes/stars normalizados por fonte |
| Boost | +20% | Se título contém sinal de alto impacto |

### processor.py

- Modelo: **Claude Haiku** (rápido e barato para triagem)
- Prompt: retorna JSON estruturado com `resumo`, `score`, `relevancia`, `motivo`
- Score ≥ 4 → status `processed` | Score < 4 → status `rejected`

### blog_generator.py

- Modelo: **Claude Opus** (qualidade máxima para conteúdo publicável)
- Gera: título SEO, título chamativo, meta description, slug, tags, corpo completo
- Estrutura do artigo: Hook → O que aconteceu → Por que importa → O que muda → Vale ficar de olho → CTA → Fechamento
- Output: arquivo `.md` com frontmatter YAML (compatível com WordPress, Ghost, Hugo)

### social_generator.py

- **1 chamada** à API por artigo gera todos os 6 formatos simultaneamente
- Formatos: TikTok/Reels (hook + roteiro 60s), Instagram (caption + hashtags), Carousel (7 slides JSON + MD), Twitter (thread 6 tweets), LinkedIn (post profissional 1300 chars), Newsletter (snippet HTML)

### pipeline.py

- Execução modular: escolha quais etapas rodar
- Logging estruturado em arquivo + terminal
- Retry automático com backoff exponencial (2 tentativas por etapa)
- Fallback: se uma etapa falha, as próximas continuam (configurável)
- Status do banco antes e depois de cada execução

---

## Comandos de referência

```bash
# ── Setup ──────────────────────────────────────────────────────────
pip install -r requirements.txt
cp .env.example .env          # edite e coloque ANTHROPIC_API_KEY

# ── Discovery ──────────────────────────────────────────────────────
python discovery/discovery_engine.py              # coleta todas as fontes
python discovery/discovery_engine.py --fonte rss  # só RSS
python discovery/discovery_engine.py --fonte hn   # só Hacker News
python discovery/discovery_engine.py --listar     # mostra top discoveries
python discovery/discovery_engine.py --enviar     # envia ao articles.db
python discovery/discovery_engine.py --dry-run    # preview sem salvar

# ── Pipeline ───────────────────────────────────────────────────────
python automation/pipeline.py                            # pipeline completo
python automation/pipeline.py --etapas collect process  # só coleta + triagem
python automation/pipeline.py --etapas generate social  # só geração
python automation/pipeline.py --score 8 --limite 3      # só score alto
python automation/pipeline.py --dry-run                 # simula sem executar
python automation/pipeline.py --parar-em-falha          # para se uma etapa falhar

# ── Módulos individuais ────────────────────────────────────────────
python collector/rss_collector.py          # só coleta RSS
python processor/processor.py             # só processa artigos raw
python content/blog_generator.py          # só gera artigos
python content/social_generator.py --todos # gera social para todos os artigos
python content/higgsfield_generator.py --tipo thumbnails --dry-run
```

---

## Variáveis de ambiente (.env)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Sim** | Chave da API da Anthropic |
| `GITHUB_TOKEN` | Não | Aumenta rate limit GitHub de 60→5000 req/h |
| `WORDPRESS_URL` | Não | Para publicação automática futura |
| `WORDPRESS_USER` | Não | Usuário do WordPress |
| `WORDPRESS_APP_PASSWORD` | Não | App password do WordPress |
| `HIGGSFIELD_API_KEY` | Não | Para gerar thumbnails e reels com IA |

---

## Status do banco de dados

O sistema usa dois bancos SQLite locais:

**`data/articles.db`** — artigos no pipeline principal
```
raw → processed / rejected → generated → social_done
```

**`data/discoveries.db`** — notícias descobertas automaticamente
```
discoveries (id, titulo, url, fonte, virality_score, enviado)
discovery_runs (data, coletados, salvos)
```

---

## Custos estimados (API Anthropic)

| Etapa | Modelo | Custo por artigo |
|---|---|---|
| Triagem (processor) | Claude Haiku | ~$0.001 |
| Blog (generator) | Claude Opus | ~$0.08 |
| Social (6 formatos) | Claude Opus | ~$0.06 |
| **Total por artigo** | | **~$0.14** |

10 artigos/dia = ~$1.40/dia = ~$42/mês.

---

## Próximos passos sugeridos (pós-MVP)

- [ ] Integração com WordPress REST API para publicação automática
- [ ] Agendamento com `cron` (Linux) ou Task Scheduler (Windows)
- [ ] Reddit como fonte adicional no discovery (subreddits de IA)
- [ ] Geração de thumbnails via Higgsfield AI (já implementado, falta API key)
- [ ] Dashboard simples para revisar artigos antes de publicar

---

*Sistema desenvolvido com Python + Claude API · MVP v1.0*
