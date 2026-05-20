# Plano de Distribuição: Meta Ads AI Connectors

Pauta-mãe: artigo `2026-05-18-meta-ads-ai-connectors-interface-morrendo.md`

Status: 3 formatos em PRIORIDADE MÁXIMA, 4 em ALTA, 3 em MÉDIA/baixa.

---

## SPEC 1: Thread X (Prioridade Máxima)

### Tweet 1 (hook)
```
A Meta abriu um servidor MCP em mcp.facebook.com/ads com 29 ferramentas pra Claude, ChatGPT e qualquer agente operar conta de anúncio.

Sem credencial de developer. Sem setup de API. Login normal de Meta e pronto.

O detalhe que ninguém comentou é a salvaguarda.
```

### Tweet 2
```
Toda campanha criada via MCP fica pausada por padrão.

Não tem flag pra desligar. É arquitetura.

A Meta sabe que agente vai errar. Em vez de fingir que IA não erra, desenhou o sistema partindo do princípio de que erro é certo.

Erro vira rascunho, não gasto.
```

### Tweet 3
```
Por que isso é maior que o release diz:

A Meta acabou de declarar que a forma legítima de operar uma plataforma de anúncio bilionária inclui agente chamando tool.

O dashboard virou uma das saídas. Não a única.

O software começou a deixar a interface.
```

### Tweet 4
```
Próximas plataformas que vão fazer igual:

Google Ads
TikTok Ads
Stripe
Shopify
HubSpot
Salesforce
Linear
Notion

Quem expor MCP primeiro fica com o agente padrão. Quem expor depois vira commodity.
```

### Tweet 5
```
O que muda no Brasil:

O gestor de tráfego júnior que só aperta botão no Ads Manager perde valor. Agente faz isso.

O sênior que sabe estratégia, criativo e supervisão ganha leverage. Opera 25 contas em vez de 5.

O MEI/freela que nunca contratou agência agora opera sozinho.
```

### Tweet 6
```
Onde mora oportunidade prática:

1. Consultoria de implementação pra média/grande empresa BR. Janela curta, 12 a 18 meses.

2. Supervisor de agente como serviço. Cliente conecta agente, paga alguém pra revisar.

3. Produto digital: prompt pack curado + SOP + mini-curso.
```

### Tweet 7
```
O risco que os textos gringos não estão dizendo:

Paused-by-default protege do desastre instantâneo. Não protege da decisão burra repetida.

Agente sem briefing cria 10 campanhas que parecem boas. A pessoa ativa. Em duas semanas, R$ 30 mil sumiram em testes mal pensados.
```

### Tweet 8 (CTA)
```
Escrevi a análise completa no JOÃOGPT: o que a Meta declarou sem alarde, onde mora oportunidade pra builder BR, e por que approval layer vai virar primitivo de toda plataforma quando IA opera.

[link]
```

### Regras aplicadas
- nenhum tweet com 🧵, "tweet 1/8" ou hooks artificiais
- cada tweet sustenta sozinho
- opinião editorial no tweet 7 com fundo verificável
- CTA simples, sem pedir RT

---

## SPEC 2: Reels / Shorts vertical (Prioridade Máxima)

**Duração ideal**: 45 a 55s
**Plataforma principal**: Instagram Reels
**Plataforma secundária**: YouTube Shorts, TikTok

### Hook (0 a 3s)
**Visual**: tela do Claude aberta, prompt sendo digitado em tempo real
**Áudio**: voz própria, ritmo conversa rápida

> "A Meta deixou o Claude operar campanha de Meta Ads direto, em conversa. Mas tem um detalhe que muda o jogo."

### Roteiro completo

**Tempo 0 a 3s. Hook visual e verbal** (acima)

**Tempo 3 a 10s. Contexto mínimo**
> "29 de abril, Meta publicou um servidor MCP. 29 ferramentas. Claude, ChatGPT, qualquer agente entra direto. Login normal e pronto."

**Tempo 10 a 25s. Demo concreta**
*Visual*: screencast acelerado de "Claude, puxa o ROAS dos últimos 7 dias agrupado por criativo", tabela aparece, "duplica a campanha vencedora com budget de 200 por dia", campanha aparece no Ads Manager **com status PAUSED em destaque**.

> "Eu peço o relatório, ele puxa. Peço pra duplicar a vencedora com novo budget. Ele cria. Mas olha aqui."

**Tempo 25 a 35s. Payoff, a salvaguarda**
*Visual*: zoom no badge "PAUSED" da campanha
> "Toda campanha que o agente cria fica pausada. Não tem opção de desligar. A Meta entendeu que IA vai errar em campanha. Em vez de fingir, fez o erro virar rascunho, não gasto."

**Tempo 35 a 50s. Take editorial**
*Visual*: corte pra talking head (opcional) ou texto-flash em fundo dark mode JOÃOGPT
> "Isso aqui é maior que o release. É o primeiro grande SaaS declarando: o dashboard virou uma das saídas. Não a única. Quem opera ads no Brasil precisa entender o que sobra de trabalho quando a operação mecânica sai da mesa."

**Tempo 50 a 55s. CTA**
> "Análise completa no link da bio. Comenta META pra eu te mandar o tutorial de setup."

### Cortes sugeridos (com timecode)
- 0:00 tela do Claude com prompt
- 0:08 Ads Manager mostrando contas
- 0:15 pedido em texto sendo digitado, resposta aparecendo
- 0:22 campanha criada em PAUSED state
- 0:30 zoom no badge PAUSED
- 0:38 talking head ou texto-flash com tese
- 0:50 CTA com handle JOÃOGPT no canto

### B-roll
- screencast real do mcp.facebook.com/ads (interface de setup)
- Ads Manager mostrando campanhas com status paused
- terminal com prompts sendo executados (opcional)
- nenhum stock, nenhum cérebro digital

### Voice over
- voz própria, tom conversa rápida internet
- nenhuma trilha que cubra a voz
- background sutil opcional, low BPM

### Retenção
- corte a cada 1.5 a 2.5s
- texto na tela em 3 momentos (hook, "PAUSED" zoom, CTA)
- evitar narrar o que já está visível

### Prompt visual pra Higgsfield (se gerar abertura cinematográfica)
> "Dashboard interface dissolving into floating UI components against dark gradient background, soft green-lime glow accents, premium tech editorial aesthetic, minimal, Linear and Vercel inspired, 9:16 vertical"

### Ideia de thumbnail (caso Reels precise capa)
- fundo dark `#0a0a0b`
- texto grande em sans humanista: "A INTERFACE MORREU"
- abaixo, menor: "Meta Ads + Claude + MCP"
- chip pequeno verde-lime: "ANÁLISE"

---

## SPEC 3: YouTube Longform (Prioridade Máxima)

**Duração alvo**: 10 a 13 min
**Tipo**: tutorial + análise estrutural

### Ideia central
"Eu plugue Claude direto no Meta Ads. Aqui está o que aconteceu, o que mudou no mercado, e como o gestor de tráfego brasileiro deveria reagir."

### Título (tentativas, escolher um)

A. "A Meta abriu o Ads pra Claude. Eu testei. Aqui está o que ninguém te contou."
B. "Meta Ads dentro do Claude: o que muda pro gestor de tráfego brasileiro"
C. "Plugue o Claude no Meta Ads em 5 minutos. O detalhe que muda tudo."

Recomendação: opção A. Mais voz própria, gancho mais forte.

### Estrutura (capítulos com timestamps tentativos)

**0:00 a 0:15. Hook duro**
*Visual*: screencast acelerado de Claude operando Ads. Prompt digitado, resposta gerada, campanha criada em PAUSED.
*Fala*: "Eu peço pro Claude criar uma campanha de Meta Ads em conversa. Ele cria. Mas ela já nasce pausada. E essa pausa é declaração de princípio."

**0:15 a 1:00. Promessa do vídeo**
*Fala*: "Nesse vídeo eu te mostro três coisas. O que a Meta lançou e como plugar em 5 minutos. Por que isso é mudança estrutural maior do que o release diz. E o que muda pro gestor de tráfego, pro freela e pro pequeno empreendedor brasileiro."

**1:00 a 3:30. Capítulo 1: O que a Meta lançou**
- MCP server em `mcp.facebook.com/ads`
- 29 ferramentas em 4 áreas
- demo do setup: login Meta, autorização, primeiro prompt no Claude
- demo de reporting: "puxa ROAS dos últimos 30 dias"

**3:30 a 5:30. Capítulo 2: O paused-by-default**
- mostrar uma campanha sendo criada via Claude
- zoom no estado PAUSED
- explicação: por que isso é arquitetura, não feature
- demonstração do approval no Ads Manager

**5:30 a 8:00. Capítulo 3: A interface deixou o software**
- tese estrutural: dashboard como uma das saídas
- outras plataformas que vão fazer igual
- analogia com APIs antigas (REST) vs MCP

**8:00 a 10:30. Capítulo 4: O que muda no Brasil**
- mercado de gestor de tráfego (números, salários, fragmentação)
- júnior vs sênior
- MEI e pequeno empreendedor operando sozinho
- três bolsões de oportunidade

**10:30 a 12:00. Capítulo 5: O risco real**
- decisão burra repetida em escala
- 30 mil sumindo em testes mal pensados
- a salvaguarda real é o operador

**12:00 a 13:00. Fechamento + CTA**
- três caminhos pro operador BR
- "se você usa Meta Ads no Brasil, salva esse vídeo, vou voltar com a parte 2 mostrando os workflows reais que estou testando"
- CTA: inscrever + newsletter pro próximo da série

### Retenção
- pattern interrupt aos 0:15 (resultado final aparece antes do contexto)
- B-roll a cada 3 a 5 cortes longos
- marcador visual a cada 60s (chip do capítulo no canto)
- nenhum bloco de mais de 90s só falando

### Momentos fortes (para clips)
- 0:00 a 0:15 hook com campanha sendo criada em PAUSED
- 3:30 a 4:00 explicação do paused-by-default com zoom
- 5:30 a 6:00 tese "a interface deixou o software"
- 8:30 a 9:00 fragmentação do mercado BR
- 10:30 a 11:00 cenário dos 30 mil queimados

### Thumbnail direction

**Conceito A** (recomendado)
- fundo dark mode JOÃOGPT
- elemento dominante: badge gigante "PAUSED" em verde-lime com glow
- texto curto à esquerda: "META + CLAUDE"
- pequeno chip canto superior: "ANÁLISE BR"

**Conceito B**
- print do Ads Manager com campanha em PAUSED destacada
- overlay com texto: "A INTERFACE MORREU"
- accent verde-lime sutil

**Conceito C**
- split screen: dashboard à esquerda, conversa do Claude à direita
- seta verde-lime apontando da conversa pra um ad criado
- texto: "29 FERRAMENTAS"

Proibido: setas vermelhas, círculos amarelos, cara espantada de creator gringo.

### Capítulos do YouTube (description)
```
0:00 A campanha que nasce pausada
0:15 O que vou te mostrar
1:00 O que a Meta lançou em 29 de abril
3:30 Por que paused-by-default é declaração de princípio
5:30 A interface deixou de ser o software
8:00 O que muda pro gestor de tráfego BR
10:30 O risco que ninguém está dizendo
12:00 Três caminhos e o que vem na parte 2
```

### Ideia Higgsfield (sequência de abertura cinematográfica de 5s)
> "Cinematic intro: dashboards and UI components floating in dark space, slowly dissolving into floating tool icons, soft green-lime particles drifting, premium editorial aesthetic, Linear and Arc Browser inspired, slow camera dolly forward, 4 seconds, 16:9"

---

## Resumo executivo do plano

- **Hoje (18/05)**: publicar artigo + thread X
- **Amanhã (19/05)**: gravar e publicar Reels com screencast real
- **Esta semana (até 23/05)**: gravar e publicar YouTube longform; publicar tutorial escrito complementar
- **Próxima semana (semana de 25/05)**: carousel IG, TikTok talking head sobre o gestor de tráfego, validar produto digital
- **Após 7 dias de sinais**: decidir produto digital (prompt pack + SOP) com base em DMs e comentários
- **Daqui 2 a 3 semanas**: parte 2 da série (workflows reais), parte 3 (supervisor de agente)
