"""
pipeline.py
===========
Orquestra o sistema completo de produção de conteúdo de IA.

Fluxo completo:
  1. COLLECT  → rss_collector.py    — busca notícias dos feeds RSS
  2. PROCESS  → processor.py        — resume + classifica com Claude Haiku
  3. GENERATE → blog_generator.py   — gera artigo SEO com Claude Opus
  4. SOCIAL   → social_generator.py — gera 6 assets de redes sociais

Como rodar:
  # Pipeline completo
  python automation/pipeline.py

  # Só algumas etapas
  python automation/pipeline.py --etapas collect process
  python automation/pipeline.py --etapas generate social

  # Controles extras
  python automation/pipeline.py --score 8 --limite 3 --dry-run

Status do banco ao longo do pipeline:
  raw → processed/rejected → generated → social_done
"""

import sys
import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# Adiciona a raiz ao path para importar os módulos
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ─────────────────────────────────────────────
# IMPORTS DOS MÓDULOS
# ─────────────────────────────────────────────

def import_modules():
    """Importa os módulos do projeto (lazy, para não quebrar no dry-run)."""
    from collector.rss_collector      import run as collect_run
    from processor.processor          import run as process_run
    from content.blog_generator       import run as blog_run
    from content.social_generator     import run as social_run
    return collect_run, process_run, blog_run, social_run


# ─────────────────────────────────────────────
# LOG
# ─────────────────────────────────────────────

LOG_DIR  = ROOT / "automation" / "logs"
LOG_DIR.mkdir(exist_ok=True)

def log(msg: str, arquivo_log=None):
    ts  = datetime.now().strftime("%H:%M:%S")
    linha = f"[{ts}] {msg}"
    print(linha)
    if arquivo_log:
        arquivo_log.write(linha + "\n")
        arquivo_log.flush()


def separator(label: str = "", arquivo_log=None):
    linha = "─" * 55
    if label:
        padding = (53 - len(label)) // 2
        linha = "─" * padding + f"  {label}  " + "─" * padding
    log(linha, arquivo_log)


# ─────────────────────────────────────────────
# STATUS DO BANCO
# ─────────────────────────────────────────────

DB_PATH = ROOT / "data" / "articles.db"

def db_status() -> dict:
    """Retorna contagem de artigos por status."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM articles GROUP BY status"
        ).fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        conn.close()
        return {}


def print_db_status(arquivo_log=None):
    status = db_status()
    if not status:
        log("   Banco ainda vazio.", arquivo_log)
        return
    ordem = ["raw", "processed", "rejected", "generated", "social_done"]
    icons = {
        "raw":         "📥",
        "processed":   "✅",
        "rejected":    "🗑️ ",
        "generated":   "📝",
        "social_done": "📱",
    }
    for s in ordem:
        if s in status:
            log(f"   {icons.get(s,'  ')} {s:<14} → {status[s]} artigo(s)", arquivo_log)
    outros = {k:v for k,v in status.items() if k not in ordem}
    for s, n in outros.items():
        log(f"   ❓ {s:<14} → {n} artigo(s)", arquivo_log)


def mark_social_done(filepath: str):
    """Marca artigos gerados como social_done após geração de assets."""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        UPDATE articles SET status = 'social_done'
        WHERE status = 'generated' AND filepath = ?
    """, (filepath,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# ETAPAS
# ─────────────────────────────────────────────

ETAPAS_DISPONIVEIS = ["collect", "process", "generate", "social"]

ETAPA_INFO = {
    "collect":  ("📡", "Coleta RSS",               "collector/rss_collector.py"),
    "process":  ("🔍", "Processa + classifica",     "processor/processor.py"),
    "generate": ("✍️ ", "Gera artigos de blog",      "content/blog_generator.py"),
    "social":   ("📱", "Gera assets sociais",        "content/social_generator.py"),
}


def run_etapa(nome: str, fn, kwargs: dict, arquivo_log) -> bool:
    """Executa uma etapa do pipeline e retorna True se bem-sucedida."""
    icon, label, _ = ETAPA_INFO[nome]
    separator(f"{icon} {label.upper()}", arquivo_log)

    inicio = time.time()
    try:
        fn(**kwargs)
        duracao = time.time() - inicio
        log(f"\n   ✅ Etapa '{nome}' concluída em {duracao:.1f}s", arquivo_log)
        return True
    except Exception as e:
        log(f"\n   ❌ Etapa '{nome}' falhou: {e}", arquivo_log)
        return False


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run(etapas: list[str], score: float, limite: int, dry_run: bool):
    now       = datetime.now()
    log_file  = LOG_DIR / f"pipeline_{now.strftime('%Y%m%d_%H%M%S')}.log"
    arq_log   = open(log_file, "w", encoding="utf-8")

    # ── Cabeçalho ────────────────────────────────────────────────────
    separator("", arq_log)
    log("🤖  PIPELINE — Blog de IA em Português", arq_log)
    log(f"   Data/hora : {now.strftime('%d/%m/%Y %H:%M:%S')}", arq_log)
    log(f"   Etapas    : {' → '.join(etapas)}", arq_log)
    log(f"   Score min : {score}/10", arq_log)
    log(f"   Limite    : {limite} artigo(s)", arq_log)
    if dry_run:
        log("   Modo      : DRY RUN", arq_log)
    separator("", arq_log)

    # ── Status inicial do banco ───────────────────────────────────────
    log("\n📊 STATUS INICIAL DO BANCO:", arq_log)
    print_db_status(arq_log)
    log("", arq_log)

    if dry_run:
        log("\n⚠️  Dry-run ativo: nenhuma etapa será executada.", arq_log)
        log(f"   Etapas que seriam executadas: {etapas}", arq_log)
        arq_log.close()
        return

    # ── Importa módulos ───────────────────────────────────────────────
    try:
        collect_run, process_run, blog_run, social_run = import_modules()
    except ImportError as e:
        log(f"❌ Erro ao importar módulos: {e}", arq_log)
        log("   Verifique se as dependências estão instaladas:", arq_log)
        log("   pip install feedparser anthropic python-dotenv", arq_log)
        arq_log.close()
        return

    # ── Executa cada etapa ────────────────────────────────────────────
    resultados = {}
    kwargs_por_etapa = {
        "collect":  {},
        "process":  {},
        "generate": {"score_min": score, "limite": limite},
        "social":   {"todos": False},
    }

    for etapa in etapas:
        if etapa not in ETAPA_DISPONIVEIS:
            log(f"⚠️  Etapa desconhecida ignorada: '{etapa}'", arq_log)
            continue

        fn = {"collect": collect_run, "process": process_run,
              "generate": blog_run,   "social": social_run}[etapa]

        ok = run_etapa(etapa, fn, kwargs_por_etapa[etapa], arq_log)
        resultados[etapa] = ok
        log("", arq_log)

    # ── Status final do banco ─────────────────────────────────────────
    separator("", arq_log)
    log("📊 STATUS FINAL DO BANCO:", arq_log)
    print_db_status(arq_log)

    # ── Resumo ────────────────────────────────────────────────────────
    separator("", arq_log)
    total    = len(resultados)
    ok_count = sum(1 for v in resultados.values() if v)
    log(f"✅  Pipeline concluído: {ok_count}/{total} etapas com sucesso", arq_log)

    if ok_count < total:
        falhas = [e for e, v in resultados.items() if not v]
        log(f"❌  Falhas: {', '.join(falhas)}", arq_log)

    log(f"📋  Log salvo em: {log_file.name}", arq_log)
    separator("", arq_log)

    arq_log.close()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline completo: coleta → processa → gera blog → gera social",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python automation/pipeline.py
  python automation/pipeline.py --etapas collect process
  python automation/pipeline.py --etapas generate social --score 8
  python automation/pipeline.py --dry-run
        """
    )
    parser.add_argument(
        "--etapas", nargs="+",
        default=ETAPAS_DISPONIVEIS,
        choices=ETAPAS_DISPONIVEIS,
        help="Etapas a executar (padrão: todas)"
    )
    parser.add_argument(
        "--score",  type=float, default=6.0,
        help="Score mínimo para gerar artigo (padrão: 6.0)"
    )
    parser.add_argument(
        "--limite", type=int, default=5,
        help="Máximo de artigos a gerar por rodada (padrão: 5)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra o plano sem executar nada"
    )

    args = parser.parse_args()
    run(
        etapas=args.etapas,
        score=args.score,
        limite=args.limite,
        dry_run=args.dry_run,
    )
