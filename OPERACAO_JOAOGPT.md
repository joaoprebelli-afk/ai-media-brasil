# OPERAÇÃO JOÃOGPT
**Fonte da verdade operacional do repositório.**
Leia antes de tocar em qualquer arquivo. Atualizar sempre que a arquitetura mudar.

---

## 1. Visão do projeto

JoãoGPT é uma mídia tech brasileira sobre inteligência artificial.
Não é blog pessoal. Não é newsletter genérica. É cobertura editorial de IA com contexto para o Brasil.

Formato: 1 análise por semana. 100% em português.

Formatos disponíveis por notícia (quais publicar depende da análise do `distribution_planner.py`):
- Artigo no blog (`website/artigos/`)
- Thread para X/Twitter
- Roteiro para TikTok/Reels
- Carrossel para Instagram
- Post para LinkedIn
- Snippet para newsletter Beehiiv

Nem toda notícia justifica todos os formatos. O `distribution_planner.py` decide onde há fit editorial real.

---

## 2. Papéis da equipe

| Papel | Responsabilidade |
|---|---|
| **João** | Rosto, visão editorial, aprovação final de tudo |
| **Codex / ChatGPT** | Direção técnica e estratégica, arquitetura de pipeline |
| **Claude / Cowork** | Execução no repo: código, edição, auditoria, commits com aprovação |
| **Namorada** | Edição de vídeo e publicação no TikTok/Reels |

**Regra de aprovação:** nenhum commit, nenhum push, nenhuma mudança de deploy sem aprovação explícita de João.

---

## 3. Estrutura atual do repositório

```
/
├── website/                  ← PRODUÇÃO — servido pela Vercel
│   ├── index.html            ← homepage
│   ├── artigos/              ← artigos publicados
│   │   └── [slug]/
│   │       └── index.html
│   ├── styles/
│   │   ├── main.css          ← design system JoãoGPT (#C4F55A)
│   │   └── article.css
│   └── fonts/ ...
│
├── api/
│   └── subscribe.js          ← Vercel serverless function (Beehiiv)
│
├── posts/                    ← CONTENT-BANK — rascunhos e material editorial
│   └── [slug]/
│       ├── slides.json       ← dados para carrossel Instagram
│       └── index.html        ← viewer local (NÃO é página do blog)
│
├── content/                  ← PIPELINE — scripts Python locais
│   ├── social_generator.py   ← NÃO ALTERAR SEM APROVAÇÃO
│   ├── distribution_planner.py
│   ├── generate_carousel.py
│   ├── article_generator.py
│   ├── blog_generator.py
│   ├── tiktok_script.py
│   ├── twitter_post.py
│   ├── higgsfield_generator.py
│   ├── output/               ← artigos .md gerados
│   ├── social/               ← JSONs por plataforma
│   │   ├── twitter/
│   │   ├── tiktok/
│   │   ├── instagram/
│   │   ├── linkedin/
│   │   ├── newsletter/
│   │   ├── carousel/
│   │   └── planos/           ← planos de distribuição
│   └── assets/
│       └── BRAND_GUIDELINES.md
│
├── collector/                ← RSS, Reddit
├── processor/                ← filtro, scoring
├── publisher/                ← WordPress publisher (futuro)
├── automation/               ← scheduler, pipeline
├── discovery/                ← discovery engine
│
├── data/
│   └── articles.db           ← banco SQLite — NUNCA COMMITAR
│
├── vercel.json               ← { "outputDirectory": "website" }
├── .gitignore
├── OPERACAO_JOAOGPT.md       ← este documento
│
└── [Astro pausado — ignorado no .gitignore]
    ├── astro.config.mjs
    ├── tsconfig.json
    ├── src/
    └── public/
```

---

## 4. O que é produção

**Produção = o que está em `website/` e é servido publicamente pela Vercel.**

- `website/index.html` — homepage
- `website/artigos/[slug]/index.html` — artigos publicados
- `website/styles/` — design system
- `api/subscribe.js` — função serverless de newsletter

**Regra:** só entra em produção o que João aprovou. Nenhum arquivo vai para `website/` automaticamente.

---

## 5. O que é rascunho / content-bank

**`posts/` é o banco de conteúdo editorial. Nada aqui é publicado automaticamente.**

- `posts/carousel-[slug]/slides.json` — dados do carrossel para Instagram
- `posts/carousel-[slug]/index.html` — viewer HTML para montar o carrossel localmente

O viewer em `posts/` **não é uma página do blog**. É ferramenta interna para visualizar e exportar slides antes de postar no Instagram. Não criar link para ele no `website/`.

---

## 6. O que é pipeline editorial

Scripts Python em `content/` que rodam localmente para gerar e distribuir conteúdo.

**Fluxo recomendado:**

```
1. distribution_planner.py   → decide em quais plataformas publicar e com qual ângulo
2. article_generator.py      → gera rascunho do artigo em .md (content/output/)
3. social_generator.py       → gera formatos sociais aprovados a partir do artigo
4. generate_carousel.py      → gera HTML viewer do carrossel em posts/
5. blog_generator.py         → gera base HTML do artigo (rascunho — requer edição manual antes de ir para website/)
```

Nenhum script faz push automático. Todos os outputs precisam de revisão manual.

**Não existe bridge automática Markdown → HTML de produção.** O HTML final em `website/artigos/[slug]/index.html` é criado e editado manualmente. Ver seção 9.

---

## 7. O que é social / carrossel

- Carrosséis existem em `posts/carousel-[slug]/` e em `content/social/carousel/`
- São **material para Instagram**, não páginas do blog
- O viewer HTML em `posts/` é interno — serve para montar os slides e exportar imagens
- Nunca linkar carrossel de `posts/` na homepage ou em artigos do blog
- Identidade visual: fundo `#080810`, verde `#C4F55A`, fontes Space Grotesk + Inter

---

## 8. O que é legacy / experimento

Arquivos que existem no repo mas ainda não têm status definitivo:

| Arquivo/Pasta | Status | Ação recomendada |
|---|---|---|
| `astro.config.mjs` | Migração pausada | Ignorado no `.gitignore`, não commitar |
| `tsconfig.json` | Migração pausada | Ignorado no `.gitignore`, não commitar |
| `src/` | Migração pausada | Ignorado no `.gitignore`, não commitar |
| `public/` | Migração pausada | Ignorado no `.gitignore`, não commitar |
| `publisher/wordpress_publisher.py` | Futuro | Manter, não integrar ainda |
| `collector/reddit_collector.py` | Futuro | Manter, não integrar ainda |

**Regra:** não apagar arquivos legacy sem aprovação explícita de João.

---

## 9. Como publicar artigo hoje

Processo 100% manual. Não existe automação Markdown → HTML de produção ainda.

```
1. Escrever ou revisar artigo base em content/output/YYYYMMDD_slug.md
2. Criar manualmente website/artigos/[slug]/index.html
   - Usar artigo existente como referência de estrutura HTML
   - Copiar cabeçalho, nav, footer, classes CSS do template
   - Preencher título, meta tags, canonical, og:, conteúdo do artigo
   - blog_generator.py pode gerar um rascunho de base, mas o HTML final
     precisa ser revisado e editado manualmente antes de ir para produção
3. Atualizar website/artigos/index.html adicionando card do novo artigo
4. Atualizar website/index.html se o artigo deve aparecer na homepage
5. Revisar tudo localmente antes de qualquer git add
6. git add website/artigos/[slug]/index.html
7. git add website/artigos/index.html   (se atualizado)
8. git add website/index.html           (se atualizado)
9. git commit -m "feat: artigo [slug]"
10. git push origin main   ← Vercel deploya automaticamente
```

**Canonical URL:** sempre `https://joaogpt.com/artigos/[slug]`

**Atenção:** `content/output/` e `posts/` são rascunho/base editorial. Só `website/artigos/` é produção.

---

## 10. Como criar carrossel Instagram

```
1. Rodar distribution_planner.py --topico "..." para confirmar que Instagram tem fit alto
2. Rodar social_generator.py para gerar content/social/carousel/[slug].json
3. Rodar generate_carousel.py para gerar posts/carousel-[slug]/
4. Abrir posts/carousel-[slug]/index.html no browser para revisar slides
5. Exportar imagens (html2canvas ou screenshot manual)
6. Postar no Instagram
```

O HTML do carrossel **não vai para `website/`**. Fica só em `posts/` como ferramenta interna.

---

## 11. Como decidir formatos de uma notícia

Usar `distribution_planner.py` antes de gerar qualquer coisa.

```bash
python content/distribution_planner.py --topico "descrição da notícia em 1-3 frases"
```

O script analisa fit editorial por plataforma e diz onde publicar e com qual ângulo. Só depois rodar os geradores.

**Regra geral de fit:**

| Plataforma | Funciona para |
|---|---|
| X/Twitter | Análise com opinião, breaking news, threads, dados concretos |
| TikTok/Reels | Gancho visual forte, explicação simples, demo de ferramenta |
| Instagram | Carrossel com lista, passo-a-passo, comparativo, conteúdo que se salva |
| LinkedIn | Impacto em carreira/negócio, oportunidades para PMEs e agências |
| Newsletter | Análise profunda, contexto que precisa de espaço, evergreen |

---

## 12. Regra de vídeo (TikTok / Reels)

**Talking head — João em foco, sem tela:**
- Notícia com impacto emocional ou surpresa
- Análise de tendência, opinião editorial
- Tese forte que João defende
- "Você não vai acreditar o que o X fez"
- Conteúdo onde a credibilidade do rosto vale mais que a demonstração

**Screencast + rosto pequeno (picture-in-picture):**
- Tutorial de ferramenta
- Demo de MCP, agente, plugin
- Instalação ou configuração de software
- Exploração de repositório GitHub
- Qualquer "deixa eu te mostrar na tela"

**Regra rápida:** se precisa de tela para fazer sentido → screencast. Se o argumento é o conteúdo → talking head.

---

## 13. Checklist antes de commit

Rodar mentalmente antes de qualquer `git add`:

- [ ] `vercel.json` tem `"outputDirectory": "website"` — não `"framework": "astro"`
- [ ] Nenhum arquivo de `data/` (`.db`, `.sqlite`) está sendo adicionado
- [ ] Nenhum arquivo Astro (`astro.config.mjs`, `tsconfig.json`, `src/`, `public/`) está sendo adicionado
- [ ] `content/social_generator.py` não foi alterado sem aprovação
- [ ] `.env` não está sendo adicionado
- [ ] Carrossel de `posts/` não está sendo linkado como página do blog
- [ ] Arquivos de `content/social/` (JSONs gerados) foram revisados antes de commitar
- [ ] `git diff --cached` foi lido antes de confirmar o commit

---

## 14. Comandos Git seguros

```bash
# Ver estado atual
git status

# Ver o que mudou em um arquivo específico
git diff [arquivo]

# Adicionar arquivo por arquivo (NUNCA git add .)
git add website/artigos/[slug]/index.html
git add website/index.html

# Revisar o que está staged antes de commitar
git diff --cached

# Commitar
git commit -m "tipo: descrição curta em português"

# Push (só após aprovação de João)
git push origin main

# Ver histórico recente
git log --oneline -10

# Desfazer staged sem perder alterações locais
git reset HEAD [arquivo]

# Ver qual commit está no remote
git fetch && git log --oneline origin/main -5
```

**Prefixos de commit:**
- `feat:` — nova funcionalidade ou artigo
- `fix:` — correção de bug ou erro
- `chore:` — manutenção, configs, dependências
- `style:` — visual, CSS, identidade
- `docs:` — documentação

---

## 15. Coisas proibidas

**Nunca fazer sem aprovação explícita de João:**

- `git add .` — proibido. Sempre adicionar arquivo por arquivo
- Alterar `vercel.json` para apontar para Astro ou outro framework
- Commitar qualquer arquivo de `data/` (`.db`, `.sqlite`, `.sqlite3`)
- Commitar `astro.config.mjs`, `tsconfig.json`, `src/`, `public/`
- Alterar `content/social_generator.py`
- Apagar qualquer arquivo legacy ou de experimento
- Fazer push direto sem mostrar o `git diff --cached` primeiro
- Expor `ANTHROPIC_API_KEY` ou `BEEHIIV_API_KEY` em qualquer arquivo commitado
- Publicar carrossel de `posts/` como página do blog em `website/`
- Criar links da homepage para arquivos em `posts/`

---

## 16. Próximas etapas recomendadas

Ordenadas por impacto e segurança:

**Imediato (sem risco de deploy):**
- [ ] Testar `distribution_planner.py` com um tópico real local
- [ ] Validar `generate_carousel.py` com `slides.json` do Google I/O
- [ ] Documentar `requirements.txt` com todas as dependências Python

**Curto prazo:**
- [ ] Criar página `/artigos` listando todos os artigos (atualmente só acessível por URL direta)
- [ ] Automatizar geração do card da homepage ao publicar novo artigo
- [ ] Testar `api/subscribe.js` end-to-end com email real

**Médio prazo:**
- [ ] Retomar migração Astro em branch separada (`feat/astro-migration`)
- [ ] Integrar `publisher/wordpress_publisher.py` para publicação alternativa
- [ ] Adicionar `sitemap.xml` e `robots.txt` em `website/`

**Quando Astro for retomado:**
- Criar branch `feat/astro-migration` a partir do `main`
- Nunca misturar código Astro com o deploy estático no `main`
- Remover as entradas do `.gitignore` só quando a migração for finalizada e aprovada

---

*Documento criado em 2026-05-27. Atualizar sempre que arquitetura, papéis ou fluxos mudarem.*
*Não deletar. Não resumir. Não simplificar sem aprovação.*
