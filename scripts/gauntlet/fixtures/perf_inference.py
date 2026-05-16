"""Benchmark literal de latência por categoria (PERF-INFERENCE-01).

Mede P50/P95 contra o proxy já em execução. Grava logs/perf_baseline.json.

Uso:
    ./venv/bin/python scripts/gauntlet/fixtures/perf_inference.py --baseline

Pré-requisitos:
    - Proxy + Ollama no ar (`./run.sh &` em outro terminal, OU este script
      espera até 60s pelo /health responder).
    - 5 amostras por caso por padrão (configurar via --n).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from nyx.agent.intent import classify  # noqa: E402
from nyx.config.defaults import PROXY_V1_URL  # noqa: E402


PROXY_BASE = PROXY_V1_URL.rsplit("/v1", 1)[0]

# Tuplas (prompt, intent_esperado).
# Prompts deliberadamente sem acentuação — emulam digitação rápida real do usuário.
CASOS: list[tuple[str, str]] = [
    ("oi", "saudacao"),
    ("ola tudo bem", "saudacao"),
    ("/help", "comando"),
    ("liste arquivos no diretorio", "tool-needed"),  # noqa-acento
    ("leia o arquivo README.md", "tool-needed"),
    ("quanto e 5+3", "chat"),
    ("explique o que faz o arquivo cli.py", "tool-needed"),
]


# Test set para acuracia do classifier (>=50 entradas).
ACURACIA_FIXTURES: list[tuple[str, str]] = [
    # Saudacoes
    ("oi", "saudacao"),
    ("ola", "saudacao"),
    ("olá", "saudacao"),
    ("hi", "saudacao"),
    ("hello", "saudacao"),
    ("hey", "saudacao"),
    ("bom dia", "saudacao"),
    ("boa tarde", "saudacao"),
    ("boa noite", "saudacao"),
    ("tudo bem", "saudacao"),
    ("tudo bem?", "saudacao"),
    ("tudo bom", "saudacao"),
    ("e ai", "saudacao"),
    ("eai", "saudacao"),
    ("salve", "saudacao"),
    ("opa", "saudacao"),
    # Comandos slash
    ("/help", "comando"),
    ("/clear", "comando"),
    ("/exit", "comando"),
    ("/debug session", "comando"),
    ("/model", "comando"),
    # Tool-needed (verbos)
    ("leia o README", "tool-needed"),
    ("leia o arquivo main.py", "tool-needed"),
    ("escreva um hello world", "tool-needed"),
    ("edite o arquivo config.py", "tool-needed"),
    ("liste arquivos", "tool-needed"),
    ("liste o diretorio nyx/", "tool-needed"),  # noqa-acento
    ("busque por 'TODO' no codigo", "tool-needed"),
    ("grep TODO em src/", "tool-needed"),
    ("encontre o arquivo de testes", "tool-needed"),
    ("rode pytest", "tool-needed"),
    ("execute o linter", "tool-needed"),
    ("crie um arquivo novo", "tool-needed"),
    ("delete o arquivo temp.log", "tool-needed"),
    ("teste o modulo X", "tool-needed"),
    ("mostre o conteudo de cli.py", "tool-needed"),
    ("abra o README.md", "tool-needed"),
    ("baixe o arquivo da url X", "tool-needed"),
    ("pesquise sobre asyncio", "tool-needed"),
    ("compile o projeto", "tool-needed"),
    ("analise o codigo de prompt.py", "tool-needed"),
    # Tool-needed (referencia a arquivo/dir)
    ("o que tem em README.md?", "tool-needed"),
    ("conteudo do arquivo .gitignore", "tool-needed"),
    ("explique o que faz o arquivo cli.py", "tool-needed"),
    ("o diretorio scripts/ tem o que?", "tool-needed"),  # noqa-acento
    # Chat puro
    ("quanto e 5+3", "chat"),
    ("o que voce acha de python", "chat"),
    ("me conte uma piada", "chat"),
    ("qual a capital do brasil", "chat"),
    ("explique recursividade em uma frase", "chat"),
    ("quem inventou o C", "chat"),
    ("o ceu e azul porque", "chat"),
]


def wait_proxy(timeout: float = 60.0) -> bool:
    """Aguarda proxy responder /health."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{PROXY_BASE}/health", timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1.0)
    return False


def medir(prompt: str, model: str, n: int) -> dict:
    """Mede n requests sequenciais para prompt. Retorna p50/p95/min/max."""
    times: list[float] = []
    errors: list[str] = []
    for _ in range(n):
        t = time.monotonic()
        try:
            r = httpx.post(
                f"{PROXY_BASE}/v1/chat/completions",
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=120.0,
            )
            dur = time.monotonic() - t
            if r.status_code != 200:
                errors.append(f"http={r.status_code}")
                continue
            times.append(dur)
        except Exception as e:
            errors.append(f"{type(e).__name__}: {str(e)[:40]}")

    if not times:
        return {"p50": None, "p95": None, "n_ok": 0, "errors": errors}

    return {
        "p50": round(statistics.median(times), 3),
        "p95": round(max(times), 3) if len(times) < 20 else round(statistics.quantiles(times, n=20)[18], 3),
        "min": round(min(times), 3),
        "max": round(max(times), 3),
        "n_ok": len(times),
        "errors": errors,
    }


def medir_acuracia() -> dict:
    """Acuracia do classifier nas fixtures."""
    total = len(ACURACIA_FIXTURES)
    hits = 0
    erros: list[dict] = []
    for prompt, esperado in ACURACIA_FIXTURES:
        got = classify(prompt)
        if got == esperado:
            hits += 1
        else:
            erros.append({"prompt": prompt, "esperado": esperado, "got": got})
    return {
        "total": total,
        "hits": hits,
        "acuracia": round(hits / total, 4),
        "erros": erros,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Grava resultado em logs/perf_baseline.json")
    parser.add_argument("--n", type=int, default=3, help="Amostras por caso (default 3 -- VRAM 4GB e lenta)")
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--skip-proxy", action="store_true", help="So roda acuracia (sem chamar LLM)")
    args = parser.parse_args()

    out: dict = {
        "model": args.model,
        "n_amostras": args.n,
        "timestamp": int(time.time()),
        "acuracia_classifier": medir_acuracia(),
    }

    if args.skip_proxy:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if args.baseline:
            log_dir = _PROJECT_ROOT / "logs"
            log_dir.mkdir(exist_ok=True)
            (log_dir / "perf_baseline.json").write_text(
                json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"\n[ok] baseline gravado em {log_dir / 'perf_baseline.json'}")
        return 0

    print(f"[perf] aguardando proxy em {PROXY_BASE}/health ...", flush=True)
    if not wait_proxy(60.0):
        print("[err] proxy não respondeu em 60s; abandone.", file=sys.stderr)
        return 2

    print(f"[perf] medindo {len(CASOS)} casos x {args.n} amostras...", flush=True)
    cases_out: dict = {}
    for prompt, intent_esperado in CASOS:
        print(f"  -> {prompt!r:50} intent={intent_esperado}", end=" ", flush=True)
        m = medir(prompt, args.model, args.n)
        m["intent_esperado"] = intent_esperado
        m["intent_real"] = classify(prompt)
        cases_out[prompt] = m
        if m["p50"] is not None:
            print(f"p50={m['p50']}s p95={m['p95']}s n_ok={m['n_ok']}")
        else:
            print(f"FALHOU: {m['errors']}")

    out["casos"] = cases_out

    print()
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if args.baseline:
        log_dir = _PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        baseline_path = log_dir / "perf_baseline.json"
        baseline_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[ok] baseline gravado em {baseline_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
