# Blog de IA em Português 🤖

Sistema automatizado para coletar, filtrar e publicar notícias sobre IA para brasileiros.

## Estrutura

```
├── collector/        # Coleta notícias (RSS, Reddit)
├── processor/        # Filtra e pontua artigos
├── content/          # Gera artigos, scripts TikTok e posts Twitter
├── publisher/        # Publica no WordPress
├── automation/       # Pipeline e agendamento
└── data/             # Banco SQLite com os artigos
```

## Como rodar o MVP

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Configure o .env:
   ```
   cp .env.example .env
   # edite o .env com sua chave da Anthropic
   ```

3. Rode o pipeline completo:
   ```
   python automation/pipeline.py
   ```

## Status dos artigos no banco

- `raw` → recém coletado
- `filtered` → passou no filtro de relevância
- `rejected` → não é sobre IA
- `scored` → pontuado e pronto para geração
- `generated` → artigo em português já foi criado
- `published` → publicado no WordPress
