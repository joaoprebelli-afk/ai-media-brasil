# Quickstart — Blog de IA em Português

Em 5 minutos você tem o sistema rodando.

---

## 1. Pré-requisitos

- Python 3.11+
- Uma chave da API da Anthropic → [console.anthropic.com](https://console.anthropic.com/settings/keys)
- Git (opcional, mas recomendado)

---

## 2. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 3. Configurar variáveis de ambiente

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Abra o arquivo `.env` e preencha:

```
ANTHROPIC_API_KEY=sk-ant-...sua_chave_aqui...
```

As outras variáveis são opcionais para o MVP.

---

## 4. Rodar o pipeline completo

```bash
python automation/pipeline.py
```

Isso executa na ordem:
1. Coleta RSS → `data/articles.db`
2. Processa com Claude Haiku → score + resumo
3. Gera artigos com Claude Opus → `content/output/`
4. Gera assets sociais → `content/social/`

---

## 5. Rodar a descoberta automática (opcional)

O discovery engine encontra notícias **antes** de aparecerem nos feeds oficiais:

```bash
python discovery/discovery_engine.py
```

Para descobrir e já enviar ao pipeline:

```bash
python discovery/discovery_engine.py --enviar
python automation/pipeline.py --etapas process generate social
```

---

## Comandos úteis

```bash
# Pipeline só com collect + process (sem gastar tokens de geração)
python automation/pipeline.py --etapas collect process

# Gerar apenas artigos com score alto
python automation/pipeline.py --etapas generate --score 8

# Ver o que seria feito sem executar
python automation/pipeline.py --dry-run

# Ver top discoveries salvos
python discovery/discovery_engine.py --listar

# Testar sem salvar nada
python discovery/discovery_engine.py --dry-run
```

---

## Localização dos outputs

| O quê | Onde |
|---|---|
| Artigos em Markdown | `content/output/` |
| Posts para TikTok | `content/social/tiktok/` |
| Captions para Instagram | `content/social/instagram/` |
| Slides do Carousel (JSON + MD) | `content/social/carousel/` |
| Thread do Twitter | `content/social/twitter/` |
| Post do LinkedIn | `content/social/linkedin/` |
| Snippet para Newsletter | `content/social/newsletter/` |
| Banco de artigos | `data/articles.db` |
| Banco de discoveries | `data/discoveries.db` |
| Logs de execução | `automation/logs/` |

---

## Solução de problemas comuns

**`ANTHROPIC_API_KEY não encontrada`**
→ Verifique se o arquivo `.env` existe na raiz do projeto e tem a chave correta.

**`disk I/O error` no SQLite**
→ O projeto está em pasta sincronizada (OneDrive, Google Drive). Mova para `C:\projetos\` ou similar.

**`feedparser retornou 0 entradas`**
→ Normal ocasionalmente; os feeds RSS podem estar lentos. Tente novamente em alguns minutos.

**GitHub API retorna 403**
→ Defina `GITHUB_TOKEN` no `.env`. Sem ele, o limite é 60 requests/hora.

**Erro de importação ao rodar pipeline**
→ Certifique-se de rodar sempre da raiz do projeto:
```bash
cd "C:\caminho\para\blog de ai em portugues"
python automation/pipeline.py
```
