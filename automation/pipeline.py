"""
pipeline.py
===========
Orquestra o sistema completo de produção de conteúdo de IA.

Fluxo:
  0. DISCOVER  → discovery/discovery_engine.py  — encontra notícias novas
  1. COLLECT   → collector/rss_collector.py     — coleta feeds RSS
  2. PROCESS   → processor/processor.py         — resume + classifica com Claude Haiku
  3. GENERATE  → content/blog_generator.py      — gera artigo SEO com Claude Opus
  4. SOCIAL    → content/social_generator.py    — gera assets de redes sociais

Status no banco ao longo do pipeline:
  raw → processed / rejected → generated → social_done

Como rodar:
  python automation/pipeline.py                         # pipeline completo
  python automation/pipeline.py --etapas collect process
  python automation/pipeline.py --etapas generate social --score 8
  python automation/pipeline.py --dry-run               # sem executar nada
"""

import argparse
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

ROOT    = Path(__file__).parent.parent
LOG_DIR = ROOT / "automation" / "logs"
DB_PATH = ROOT / "data" / "articles.db"

sys.path.insert(0, str(ROOT))

# ─────────────────────────────────────────────
# LOGGING ESTRUTURADO
# ─────────────────────────────────────────────

def setup_logging(log_file: Path) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ─────────────────────────────────────────────
# BANCO DE DADOS — STATUS
# ─────────────────────────────────────────────

def db_status() -> dict:
    if not DB_PATH.exists():
        return {}
    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM articles GROUP BY status"
        ).fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        return {}


def log_db_status(logger: logging.Logger, label: str = "STATUS DO BANCO"):
    status = db_status()
    logger.info(f"── {label} ──")
    if not status:
        logger.info("   banco ainda vazio")
        return
    ordem = ["raw", "processed", "rejected", "generated", "social_done"]
    icons = {"raw": "📥", "processed": "✅", "rejected": "🗑 ",
             "generated": "📝", "social_done": "📱"}
    for s in ordem:
        if s in status:
            logger.info(f"   {icons.get(s,'  ')} {s:<14} {status[s]} artigo(s)")
    for s, n in status.items():
        if s not in ordem:
            logger.info(f"   ❓ {s:<14} {n} artigo(s)")


# ─────────────────────────────────────────────
# RETRY COM BACKOFF
# ─────────────────────────────────────────────

def with_retry(fn, max_attempts: int = 3, base_delay: float = 5.0, logger=None):
    """
    Executa fn() até max_attempts vezes com espera exponencial entre tentativas.
    Levanta a última exceção se todas falharem.
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt < max_attempts:
                wait = base_delay * (2 ** (attempt - 1))
                if logger:
                    logger.warning(f"   tentativa {attempt}/{max_attempts} falhou: {e}")
                    logger.warning(f"   aguardando {wait:.0f}s antes de tentar novamente...")
                time.sleep(wait)
            else:
                if logger:
                    logger.error(f"   todas as {max_attempts} tentativas falharam: {e}")
    raise last_exc


# ─────────────────────────────────────────────
# DEFINIÇÃO DAS ETAPAS
# ─────────────────────────────────────────────

ETAPAS_DISPONIVEIS = ["discover", "collect", "process", "generate", "social"]

ETAPA_META = {
    "discover":  {"icon": "🔍", "label": "Descoberta automática",   "modulo": "discovery/discovery_engine.py"},
    "collect":   {"icon": "📡", "label": "Coleta RSS",              "modulo": "collector/rss_collector.py"},
    "process":   {"icon": "🤖", "label": "Processa + classifica",   "modulo": "processor/processor.py"},
    "generate":  {"icon": "✍️ ", "label": "Gera artigos de blog",   "modulo": "content/blog_generator.py"},
    "social":    {"icon": "📱", "label": "Gera assets sociais",     "modulo": "content/social_generator.py"},
}


def import_etapa(nome: str):
    """Importação lazy — só falha se a etapa for realmente usada."""
    if nome == "discover":
        from discovery.discovery_engine import DiscoveryEngine
        def _run_discover():
            engine = DiscoveryEngine()
            result = engine.run()
            sent   = engine.send_to_processor()
            return result["total"], result["inserted"], sent
        return _run_discover

    if nome == "collect":
        from collector.rss_collector import run
        return run

    if nome == "process":
        from processor.processor import run
        return run

    if nome == "generate":
        from content.blog_generator import run
        return run

    if nome == "social":
        from content.social_generator import run
        return run

    raise ValueError(f"Etapa desconhecida: {nome}")


# ─────────────────────────────────────────────
# EXECUÇÃO DE UMA ETAPA
# ─────────────────────────────────────────────

def run_etapa(
    nome: str,
    kwargs: dict,
    logger: logging.Logger,
    max_retries: int = 2,
) -> tuple[bool, float]:
    """
    Executa uma etapa do pipeline com retry automático.
    Retorna (sucesso: bool, duração_segundos: float).
    """
    meta  = ETAPA_META[nome]
    icon  = meta["icon"]
    label = meta["label"].upper()

    logger.info(f"")
    logger.info(f"{'─' * 55}")
    logger.info(f"{icon}  {label}")
    logger.info(f"{'─' * 55}")

    try:
        fn = import_etapa(nome)
    except ImportError as e:
        logger.error(f"   Importação falhou: {e}")
        logger.error(f"   Verifique: pip install -r requirements.txt")
        return False, 0.0

    inicio = time.time()
    try:
        with_retry(
            lambda: fn(**kwargs),
            max_attempts=max_retries,
            base_delay=5.0,
            logger=logger,
        )
        duracao = time.time() - inicio
        logger.info(f"   ✅ Etapa '{nome}' concluída em {duracao:.1f}s")
        return True, duracao

    except Exception as e:
        duracao = time.time() - inicio
        logger.error(f"   ❌ Etapa '{nome}' falhou definitivamente: {e}")
        logger.debug("", exc_info=True)
        return False, duracao


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run(
    etapas: list[str],
    score: float,
    limite: int,
    dry_run: bool,
    continuar_em_falha: bool = True,
):
    now      = datetime.now()
    log_file = LOG_DIR / f"pipeline_{now.strftime('%Y%m%d_%H%M%S')}.log"
    logger   = setup_logging(log_file)

    # ── Cabeçalho ────────────────────────────────────────────────────
    logger.info("═" * 55)
    logger.info("🤖  PIPELINE — Blog de IA em Português")
    logger.info(f"   Data/hora   : {now.strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"   Etapas      : {' → '.join(etapas)}")
    logger.info(f"   Score mín   : {score}/10")
    logger.info(f"   Limite      : {limite} artigo(s)")
    logger.info(f"   Em falha    : {'continua' if continuar_em_falha else 'para'}")
    if dry_run:
        logger.info("   Modo        : DRY RUN")
    logger.info("═" * 55)

    # ── Status inicial ────────────────────────────────────────────────
    log_db_status(logger, "STATUS INICIAL")

    if dry_run:
        logger.info("")
        logger.info("⚠️  Dry-run: nenhuma etapa será executada.")
        logger.info(f"   Etapas planejadas: {etapas}")
        logger.info(f"   Log salvo em: {log_file.name}")
        return

    # ── Kwargs por etapa ──────────────────────────────────────────────
    kwargs_map = {
        "discover": {},
        "collect":  {},
        "process":  {},
        "generate": {"score_min": score, "limite": limite},
        "social":   {"todos": False},
    }

    # ── Executa etapas ────────────────────────────────────────────────
    resultados: dict[str, tuple[bool, float]] = {}
    tempo_total = 0.0

    for etapa in etapas:
        if etapa not in ETAPAS_DISPONIVEIS:
            logger.warning(f"Etapa desconhecida ignorada: '{etapa}'")
            continue

        ok, dur = run_etapa(
            nome=etapa,
            kwargs=kwargs_map.get(etapa, {}),
            logger=logger,
            max_retries=2,
        )
        resultados[etapa] = (ok, dur)
        tempo_total += dur

        if not ok and not continuar_em_falha:
            logger.error(f"Pipeline interrompido na etapa '{etapa}' (--parar-em-falha).")
            break

    # ── Status final ──────────────────────────────────────────────────
    logger.info("")
    log_db_status(logger, "STATUS FINAL")

    # ── Resumo ────────────────────────────────────────────────────────
    logger.info("")
    logger.info("═" * 55)
    ok_count = sum(1 for ok, _ in resultados.values() if ok)
    total    = len(resultados)
    logger.info(f"Pipeline concluído: {ok_count}/{total} etapas OK  ({tempo_total:.1f}s total)")

    for etapa, (ok, dur) in resultados.items():
        status = "✅" if ok else "❌"
        logger.info(f"   {status} {etapa:<12} {dur:.1f}s")

    falhas = [e for e, (ok, _) in resultados.items() if not ok]
    if falhas:
        logger.warning(f"Etapas com falha: {', '.join(falhas)}")

    logger.info(f"Log completo: {log_file}")
    logger.info("═" * 55)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline completo: discover → collect → process → generate → social",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python automation/pipeline.py
  python automation/pipeline.py --etapas collect process
  python automation/pipeline.py --etapas generate social --score 8
  python automation/pipeline.py --dry-run
  python automation/pipeline.py --parar-em-falha
        """,
    )
    parser.add_argument(
        "--etapas", nargs="+",
        default=["collect", "process", "generate", "social"],
        choices=ETAPAS_DISPONIVEIS,
        help="Etapas a executar (padrão: collect process generate social)",
    )
    parser.add_argument(
        "--score", type=float, default=6.0,
        help="Score mínimo para gerar artigo (padrão: 6.0)",
    )
    parser.add_argument(
        "--limite", type=int, default=5,
        help="Máximo de artigos a gerar por rodada (padrão: 5)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra o plano sem executar nada",
    )
    parser.add_argument(
        "--parar-em-falha", action="store_true",
        help="Interrompe o pipeline se uma etapa falhar (padrão: continua)",
    )

    args = parser.parse_args()
    run(
        etapas=args.etapas,
        score=args.score,
        limite=args.limite,
        dry_run=args.dry_run,
        continuar_em_falha=not args.parar_em_falha,
    )
