"""
higgsfield_generator.py
=======================
Lê prompts de content/assets/ e gera assets visuais via Higgsfield API.

Assets gerados:
  thumbnails/  → imagens 16:9 para blog  (modelo: nano_banana_2)
  reels/       → vídeos 9:16 para TikTok (modelo: kling3_0)
  carousel/    → imagens 1:1 por slide   (modelo: nano_banana_flash)

Outputs salvos em:
  content/generated_assets/thumbnails/
  content/generated_assets/reels/
  content/generated_assets/carousel/

Como rodar:
  1. Adicione HIGGSFIELD_API_KEY no .env
  2. pip install requests python-dotenv
  3. python content/higgsfield_generator.py

  Opções:
    --tipo thumbnail        só thumbnails
    --tipo reels            só vídeos de reels
    --tipo carousel         só slides de carousel
    --slug gpt-5-chegou     processa só um artigo específico
    --dry-run               lista prompts sem chamar a API
    --listar-modelos        mostra modelos disponíveis e sai
"""

import os
import sys
import json
import time
import argparse
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

BASE_DIR       = Path(__file__).parent.parent
ASSETS_DIR     = BASE_DIR / "content" / "assets"
OUTPUT_DIR     = BASE_DIR / "content" / "generated_assets"
LOG_DIR        = BASE_DIR / "automation" / "logs"

API_KEY        = os.getenv("HIGGSFIELD_API_KEY")
API_BASE       = "https://api.higgsfield.ai/v1"
HEADERS        = lambda: {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Polling
POLL_INTERVAL  = 5    # segundos entre verificações de status
POLL_MAX       = 120  # máximo de tentativas (~10 minutos)
RETRY_MAX      = 3    # retentativas em erros de rede
RETRY_DELAY    = 8    # segundos entre retentativas

# Modelos padrão por tipo (podem ser sobrescritos no JSON do prompt)
DEFAULT_MODELS = {
    "thumbnail": "nano_banana_2",
    "reels":     "kling3_0",
    "carousel":  "nano_banana_flash",
}

DEFAULT_ASPECTS = {
    "thumbnail": "16:9",
    "reels":     "9:16",
    "carousel":  "1:1",
}

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logger(slug: str = "geral") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"higgsfield_{slug}_{ts}"
    log  = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s",
                             datefmt="%H:%M:%S")

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)

    # Arquivo
    fh = logging.FileHandler(LOG_DIR / f"{name}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)

    return log


LOG = setup_logger()


# ─────────────────────────────────────────────
# CLIENTE HIGGSFIELD API
# ─────────────────────────────────────────────

class HiggsFieldError(Exception):
    pass


def _request(method: str, endpoint: str, log: logging.Logger,
             payload: dict = None, stream: bool = False) -> requests.Response:
    """
    Faz uma requisição HTTP com retry automático em erros de rede.
    Lança HiggsFieldError em erros da API.
    """
    url = f"{API_BASE}/{endpoint.lstrip('/')}"

    for tentativa in range(1, RETRY_MAX + 1):
        try:
            resp = requests.request(
                method, url,
                headers=HEADERS(),
                json=payload,
                stream=stream,
                timeout=30,
            )

            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", RETRY_DELAY * tentativa))
                log.warning(f"Rate limit atingido. Aguardando {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code >= 500:
                log.warning(f"Erro servidor {resp.status_code}. "
                            f"Tentativa {tentativa}/{RETRY_MAX}...")
                time.sleep(RETRY_DELAY * tentativa)
                continue

            if resp.status_code >= 400:
                raise HiggsFieldError(
                    f"API retornou {resp.status_code}: {resp.text[:300]}"
                )

            return resp

        except requests.exceptions.ConnectionError as e:
            log.warning(f"Erro de conexão (tentativa {tentativa}/{RETRY_MAX}): {e}")
            if tentativa == RETRY_MAX:
                raise HiggsFieldError(f"Falha de conexão após {RETRY_MAX} tentativas.")
            time.sleep(RETRY_DELAY * tentativa)

        except requests.exceptions.Timeout:
            log.warning(f"Timeout (tentativa {tentativa}/{RETRY_MAX})")
            if tentativa == RETRY_MAX:
                raise HiggsFieldError("Timeout após múltiplas tentativas.")
            time.sleep(RETRY_DELAY)

    raise HiggsFieldError("Máximo de tentativas atingido.")


def submit_image(prompt_cfg: dict, log: logging.Logger) -> str:
    """Submete geração de imagem. Retorna job_id."""
    payload = {
        "model":        prompt_cfg.get("model", DEFAULT_MODELS["thumbnail"]),
        "prompt":       prompt_cfg["prompt"],
        "aspect_ratio": prompt_cfg.get("aspect_ratio", "16:9"),
        "count":        prompt_cfg.get("count", 1),
    }
    if "resolution" in prompt_cfg:
        payload["resolution"] = prompt_cfg["resolution"]

    log.debug(f"Submetendo imagem: model={payload['model']} ratio={payload['aspect_ratio']}")
    resp = _request("POST", "/images/generate", log, payload)
    data = resp.json()

    job_id = data.get("job_id") or data.get("id")
    if not job_id:
        raise HiggsFieldError(f"job_id não encontrado na resposta: {data}")
    return job_id


def submit_video(prompt_cfg: dict, log: logging.Logger) -> str:
    """Submete geração de vídeo. Retorna job_id."""
    payload = {
        "model":        prompt_cfg.get("model", DEFAULT_MODELS["reels"]),
        "prompt":       prompt_cfg["prompt"],
        "aspect_ratio": prompt_cfg.get("aspect_ratio", "9:16"),
        "duration":     prompt_cfg.get("duration", 5),
        "count":        prompt_cfg.get("count", 1),
    }
    if "mode" in prompt_cfg:
        payload["mode"] = prompt_cfg["mode"]

    log.debug(f"Submetendo vídeo: model={payload['model']} dur={payload['duration']}s")
    resp = _request("POST", "/videos/generate", log, payload)
    data = resp.json()

    job_id = data.get("job_id") or data.get("id")
    if not job_id:
        raise HiggsFieldError(f"job_id não encontrado: {data}")
    return job_id


def poll_job(job_id: str, tipo: str, log: logging.Logger) -> list[str]:
    """
    Faz polling até o job completar.
    Retorna lista de URLs dos arquivos gerados.
    """
    endpoint = f"/jobs/{job_id}"
    log.info(f"Aguardando job {job_id[:8]}...")

    for i in range(POLL_MAX):
        time.sleep(POLL_INTERVAL)

        resp = _request("GET", endpoint, log)
        data = resp.json()
        status = data.get("status", "").lower()

        if i % 6 == 0:  # loga a cada ~30s
            log.info(f"  Status: {status} ({i * POLL_INTERVAL}s decorridos)")

        if status in ("completed", "succeeded", "done"):
            urls = []
            # Diferentes campos possíveis dependendo do modelo
            for campo in ("results", "outputs", "urls", "images", "videos"):
                if campo in data and data[campo]:
                    items = data[campo]
                    if isinstance(items, list):
                        for item in items:
                            url = item.get("url") or item if isinstance(item, str) else None
                            if url:
                                urls.append(url)
                    break
            if not urls:
                raise HiggsFieldError(f"Job completo mas sem URLs: {data}")
            log.info(f"  ✅ Job completo: {len(urls)} arquivo(s)")
            return urls

        if status in ("failed", "error", "cancelled"):
            motivo = data.get("error") or data.get("message", "desconhecido")
            raise HiggsFieldError(f"Job falhou: {motivo}")

    raise HiggsFieldError(
        f"Timeout: job {job_id[:8]} não completou em {POLL_MAX * POLL_INTERVAL}s"
    )


def download_file(url: str, destino: Path, log: logging.Logger) -> Path:
    """Faz download de um arquivo gerado e salva localmente."""
    log.debug(f"Baixando: {url[:80]}...")
    resp = _request("GET", url, log, stream=True) if url.startswith(API_BASE) \
        else requests.get(url, stream=True, timeout=60)

    resp.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resp.content)
    log.info(f"  💾 Salvo: {destino.name} ({len(resp.content) // 1024}KB)")
    return destino


def save_metadata(slug: str, tipo: str, job_id: str,
                  urls: list[str], arquivos: list[Path], log: logging.Logger):
    """Salva JSON de metadados ao lado dos arquivos gerados."""
    meta = {
        "slug":         slug,
        "tipo":         tipo,
        "job_id":       job_id,
        "gerado_em":    datetime.now().isoformat(),
        "urls_originais": urls,
        "arquivos_locais": [str(p) for p in arquivos],
    }
    pasta  = OUTPUT_DIR / tipo
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest   = pasta / f"{slug}_{ts}_meta.json"
    dest.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log.debug(f"Metadados: {dest.name}")


# ─────────────────────────────────────────────
# PROCESSADORES POR TIPO
# ─────────────────────────────────────────────

def process_thumbnail(prompt_file: Path, log: logging.Logger) -> bool:
    """Gera thumbnail de blog (16:9) a partir de prompt JSON."""
    cfg  = json.loads(prompt_file.read_text(encoding="utf-8"))
    slug = cfg.get("slug", prompt_file.stem)

    log.info(f"🖼️  Thumbnail: {slug}")
    log.info(f"   Prompt: {cfg['prompt'][:80]}...")

    cfg.setdefault("model",        DEFAULT_MODELS["thumbnail"])
    cfg.setdefault("aspect_ratio", DEFAULT_ASPECTS["thumbnail"])

    job_id  = submit_image(cfg, log)
    urls    = poll_job(job_id, "image", log)

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta   = OUTPUT_DIR / "thumbnails"
    salvos  = []
    for i, url in enumerate(urls):
        ext  = url.split(".")[-1].split("?")[0] or "png"
        dest = pasta / f"{slug}_{ts}_{i+1}.{ext}"
        download_file(url, dest, log)
        salvos.append(dest)

    save_metadata(slug, "thumbnails", job_id, urls, salvos, log)
    return True


def process_reel(prompt_file: Path, log: logging.Logger) -> bool:
    """Gera vídeo 9:16 para TikTok/Reels a partir de prompt JSON."""
    cfg  = json.loads(prompt_file.read_text(encoding="utf-8"))
    slug = cfg.get("slug", prompt_file.stem)

    log.info(f"🎬 Reel: {slug}")
    log.info(f"   Modelo: {cfg.get('model', DEFAULT_MODELS['reels'])} | "
             f"Duração: {cfg.get('duration', 5)}s")

    cfg.setdefault("model",        DEFAULT_MODELS["reels"])
    cfg.setdefault("aspect_ratio", DEFAULT_ASPECTS["reels"])

    job_id  = submit_video(cfg, log)
    urls    = poll_job(job_id, "video", log)

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta   = OUTPUT_DIR / "reels"
    salvos  = []
    for i, url in enumerate(urls):
        ext  = url.split(".")[-1].split("?")[0] or "mp4"
        dest = pasta / f"{slug}_{ts}_{i+1}.{ext}"
        download_file(url, dest, log)
        salvos.append(dest)

    save_metadata(slug, "reels", job_id, urls, salvos, log)
    return True


def process_carousel(prompt_file: Path, log: logging.Logger) -> bool:
    """Gera um asset por slide do carousel a partir de prompt JSON."""
    cfg    = json.loads(prompt_file.read_text(encoding="utf-8"))
    slug   = cfg.get("slug", prompt_file.stem)
    slides = cfg.get("slides", [])

    if not slides:
        log.warning(f"Nenhum slide encontrado em {prompt_file.name}")
        return False

    log.info(f"🎠 Carousel: {slug} ({len(slides)} slides)")
    pasta  = OUTPUT_DIR / "carousel" / slug
    pasta.mkdir(parents=True, exist_ok=True)

    todos_ok = True
    for slide in slides:
        n      = slide.get("numero", "?")
        tipo_s = slide.get("tipo", "ponto")

        log.info(f"   Slide {n} ({tipo_s})...")

        slide.setdefault("model",        DEFAULT_MODELS["carousel"])
        slide.setdefault("aspect_ratio", DEFAULT_ASPECTS["carousel"])

        try:
            job_id = submit_image(slide, log)
            urls   = poll_job(job_id, "image", log)

            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, url in enumerate(urls):
                ext  = url.split(".")[-1].split("?")[0] or "png"
                dest = pasta / f"slide_{n:02d}_{tipo_s}_{ts}.{ext}"
                download_file(url, dest, log)
                save_metadata(f"{slug}_slide{n}", "carousel",
                              job_id, urls, [dest], log)
        except HiggsFieldError as e:
            log.error(f"   ❌ Slide {n} falhou: {e}")
            todos_ok = False
            continue

        time.sleep(2)  # pequena pausa entre slides

    return todos_ok


# ─────────────────────────────────────────────
# DESCOBERTA DE PROMPTS
# ─────────────────────────────────────────────

def find_prompts(tipo: str, slug_filter: str = None) -> list[Path]:
    """Encontra arquivos de prompt JSON na pasta do tipo."""
    pasta = ASSETS_DIR / tipo
    if not pasta.exists():
        return []
    arquivos = sorted(pasta.glob("*.json"))
    if slug_filter:
        arquivos = [f for f in arquivos if slug_filter in f.stem]
    return arquivos


PROCESSADORES = {
    "thumbnails": process_thumbnail,
    "reels":      process_reel,
    "carousel":   process_carousel,
}


# ─────────────────────────────────────────────
# LISTAGEM DE MODELOS
# ─────────────────────────────────────────────

def listar_modelos(log: logging.Logger):
    """Consulta a API e lista modelos disponíveis."""
    log.info("Consultando modelos disponíveis...")
    for tipo in ("images", "videos"):
        try:
            resp = _request("GET", f"/models?type={tipo}", log)
            modelos = resp.json().get("items", [])
            log.info(f"\n{'─'*40}")
            log.info(f"MODELOS DE {tipo.upper()}: {len(modelos)}")
            for m in modelos:
                log.info(f"  {m['id']:<30} {m.get('name','')}")
        except Exception as e:
            log.error(f"Erro ao listar modelos {tipo}: {e}")


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────

def run(tipos: list[str], slug: str = None, dry_run: bool = False,
        listar: bool = False):

    print("=" * 60)
    print("🎨  HIGGSFIELD GENERATOR — Assets Visuais")
    print("=" * 60)

    if not API_KEY and not dry_run:
        print("❌ HIGGSFIELD_API_KEY não encontrada no .env")
        print("   Obtenha sua chave em: https://higgsfield.ai")
        return

    # Verifica saldo
    if API_KEY and not dry_run:
        try:
            resp = requests.get(f"{API_BASE}/account/balance",
                                headers=HEADERS(), timeout=10)
            if resp.ok:
                bal = resp.json()
                creditos = bal.get("credits", "?")
                plano    = bal.get("subscription_plan_type", "?")
                print(f"\n💳 Créditos: {creditos} | Plano: {plano}")
                if isinstance(creditos, (int, float)) and creditos < 1:
                    print("⚠️  Créditos baixos. Verifique em higgsfield.ai")
        except Exception:
            pass

    if listar:
        listar_modelos(LOG)
        return

    # Descobre prompts
    fila = []
    for tipo in tipos:
        prompts = find_prompts(tipo, slug)
        for p in prompts:
            fila.append((tipo, p))

    if not fila:
        print(f"\nℹ️  Nenhum prompt encontrado em content/assets/{tipos}")
        print(f"   Crie arquivos .json em content/assets/thumbnails/, reels/, carousel/")
        return

    print(f"\n📋 {len(fila)} prompt(s) encontrado(s):\n")
    for tipo, caminho in fila:
        cfg = json.loads(caminho.read_text(encoding="utf-8"))
        print(f"   [{tipo}] {caminho.name}")
        if "slides" in cfg:
            print(f"           {len(cfg['slides'])} slides")
        else:
            print(f"           {cfg.get('prompt','')[:60]}...")

    if dry_run:
        print("\n✅ Dry-run. Nenhuma geração executada.")
        return

    print()
    ok = err = 0

    for tipo, prompt_file in fila:
        log = setup_logger(prompt_file.stem)
        fn  = PROCESSADORES[tipo]
        log.info(f"{'─'*50}")
        log.info(f"Processando: {tipo}/{prompt_file.name}")
        try:
            sucesso = fn(prompt_file, log)
            if sucesso:
                ok += 1
            else:
                err += 1
        except HiggsFieldError as e:
            log.error(f"❌ Falha Higgsfield: {e}")
            err += 1
        except Exception as e:
            log.error(f"❌ Erro inesperado: {e}", exc_info=True)
            err += 1

    print("\n" + "=" * 60)
    print(f"✅  Concluído! {ok} sucesso(s) | {err} erro(s)")
    print(f"📁  Outputs: {OUTPUT_DIR}")
    print("=" * 60)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera assets visuais com Higgsfield AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python content/higgsfield_generator.py
  python content/higgsfield_generator.py --tipo thumbnails
  python content/higgsfield_generator.py --tipo reels --slug gpt-5
  python content/higgsfield_generator.py --dry-run
  python content/higgsfield_generator.py --listar-modelos
        """
    )
    parser.add_argument(
        "--tipo", nargs="+",
        choices=["thumbnails", "reels", "carousel"],
        default=["thumbnails", "reels", "carousel"],
        help="Tipo(s) de asset a gerar (padrão: todos)"
    )
    parser.add_argument(
        "--slug", type=str, default=None,
        help="Filtra por slug de artigo específico"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Lista prompts sem chamar a API"
    )
    parser.add_argument(
        "--listar-modelos", action="store_true",
        help="Lista modelos disponíveis e sai"
    )
    args = parser.parse_args()

    run(
        tipos=args.tipo,
        slug=args.slug,
        dry_run=args.dry_run,
        listar=args.listar_modelos,
    )
