# PROMPTS JOÃOGPT
**Regras permanentes de fluxo editorial, formato de vídeo e produção de conteúdo.**
Leia antes de produzir qualquer conteúdo. Complementa `OPERACAO_JOAOGPT.md`.

---

## Fluxo Padrão Quando João Envia Curadoria Bruta

Quando João mandar uma curadoria bruta vinda do Grok, X, GitHub, site oficial ou pesquisa manual:

1. Primeiro fazer análise editorial.
2. Avaliar relevância, urgência, risco de hype e formatos recomendados.
3. Se nota for 7 ou mais, produzir no mesmo pacote todos os formatos recomendados.
4. Se nota for 5-6, produzir apenas os formatos com fit alto.
5. Se nota for abaixo de 5, não produzir conteúdo final. Explicar se é melhor guardar, ignorar ou monitorar.
6. Nunca produzir todos os formatos por obrigação.
7. Separar fatos confirmados, opinião e especulação.
8. Nunca inventar link, preço, disponibilidade no Brasil ou acesso que não foi confirmado.

---

## Regra De Vídeo JoãoGPT

**Talking head:**
Usar para notícia, análise, opinião, tese forte, alerta, "isso muda tudo".
João aparece como foco principal.
Pouca edição.
Linguagem direta.
Construir autoridade e conexão com o rosto do JoãoGPT.

**Screencast + rosto pequeno:**
Usar para tutorial, instalação, demo de ferramenta, MCP, repositório GitHub, automação, passo a passo.
Tela é o conteúdo principal.
João aparece pequeno no canto guiando o processo.

---

## Conteúdo De Tutorial Com Prompts

Quando João quiser ensinar algo prático, como:
- criar modelo realista e consistente com IA
- gerar vídeo com IA
- recriar trend de vídeo, exemplo: câmera focando pessoa na torcida
- usar ferramenta nova
- instalar MCP
- analisar repositório GitHub

A entrega padrão deve incluir:

1. Roteiro screencast + rosto pequeno.
2. Lista de prompts prontos para copiar e colar.
3. Passo a passo simples.
4. Erros comuns.
5. Resultado esperado.
6. Artigo tutorial para o blog.
7. Legenda para Instagram/TikTok/Shorts.
8. Se fizer sentido, carrossel resumindo o passo a passo.

**Regra:**
Tutorial bom do JoãoGPT precisa gerar algo que a pessoa consiga replicar.

---

## Regra Do Blog Para Tutoriais

Se o conteúdo for tutorial forte, também criar artigo para o blog com:

- título SEO
- slug
- meta description
- pré-requisitos
- prompts usados
- passo a passo
- resultado esperado
- problemas comuns
- CTA para newsletter

---

## Papéis Das Ferramentas

**Grok/X/Web:**
Faz curadoria bruta, coleta links, posts, fontes e sinais.
Não dá nota final.
Não cria conteúdo final.
Não decide formatos finais.

**Claude/Cowork:**
Faz análise editorial.
Dá nota, urgência, risco e formatos.
Produz o pacote recomendado quando a pauta passa no filtro.
Executa no repositório quando aprovado.

**Codex/ChatGPT:**
Define prompts, prioridades e validações.
Revisa riscos.
Protege o deploy e o fluxo técnico.

**João:**
Aprova a pauta.
Grava os vídeos.
Decide visão, marca e estratégia final.

---

## Regras De Carrossel

- Carrossel é asset para Instagram.
- Não é página do blog.
- Deve ficar em `posts/` ou `content/social/`.
- Não linkar carrossel em `website/`.
- Deve ser mobile-first, pouco texto, forte e compartilhável.

---

## Regra Do Blog

- Blog público vive em `website/artigos/[slug]/index.html`.
- `posts/` e `content/output/` são rascunho/content-bank.
- Não existe bridge automática Markdown para HTML de produção ainda.
- Artigo público precisa ser criado/editado manualmente em `website/`.

---

*Documento criado em 2026-05-27. Atualizar sempre que novas regras de fluxo editorial forem definidas.*
*Não deletar. Não resumir. Não simplificar sem aprovação.*
