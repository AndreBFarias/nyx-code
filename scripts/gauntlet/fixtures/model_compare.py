"""Benchmark comparativo de modelos para MODEL-SWAP-01.

Roda os 7 prompts canônicos de perf_inference.py contra N modelos Ollama
distintos. Mede:

- P50/P95 latência (s)
- lang_pt_br_rate (via is_pt_br)
- tool_call_success_rate (1 caso "leia README" com tool Read)
- VRAM pico (MiB) via nvidia-smi durante inferência

Saída: logs/model_compare.json e tabela markdown stdout.

Premissa: bate direto na API Ollama nativa (/api/chat) — sem proxy. Isolando
custo bruto do modelo (sem retry LANG-ENFORCE, sem overhead do proxy).
Tool calling testado com think=true (qwen3-thinking exige; qwen2.5-coder
honra a flag mesmo non-thinking).

Uso:
    ./venv/bin/python scripts/gauntlet/fixtures/model_compare.py
    ./venv/bin/python scripts/gauntlet/fixtures/model_compare.py --models qwen3:4b,qwen2.5-coder:3b
    ./venv/bin/python scripts/gauntlet/fixtures/model_compare.py --n 3 --skip-7b

Pré-requisitos:
    - Ollama dedicado rodando em 127.0.0.1:11435 com OLLAMA_MODELS pointing
      para o path local do Nyx (./models). Script faz health check.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from nyx.agent.intent import classify  # noqa: E402
from nyx.agent.lang_check import is_pt_br  # noqa: E402
from nyx.config.defaults import OLLAMA_URL  # noqa: E402

# 7 prompts canonicos (mesma lista de perf_inference.py).
CASOS: list[tuple[str, str]] = [
    ("oi", "saudacao"),
    ("ola tudo bem", "saudacao"),
    ("/help", "comando"),
    ("liste arquivos no diretorio", "tool-needed"),  # noqa-acento
    ("leia o arquivo README.md", "tool-needed"),
    ("quanto e 5+3", "chat"),
    ("explique o que faz o arquivo cli.py", "tool-needed"),
]

# Schema mínimo Read pra teste de tool calling.
TOOL_READ_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Le conteudo de um arquivo do projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Caminho absoluto do arquivo a ler.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
]

NYX_OLLAMA_URL = OLLAMA_URL  # 127.0.0.1:11435


def health_check() -> bool:
    """Confere se Ollama dedicado esta respondendo."""
    try:
        r = httpx.get(f"{NYX_OLLAMA_URL}/api/version", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


def vram_used_mib() -> int:
    """VRAM usada agora, em MiB. -1 se nvidia-smi indisponivel."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=3.0,
        )
        if out.returncode == 0:
            return int(out.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return -1


def supports_thinking(model: str) -> bool:
    """Retorna True se o modelo suporta think=true.

    Ollama retorna HTTP 400 "does not support thinking" para modelos
    non-thinking quando think=true e bate na /api/chat. Lista mantida
    enxuta: qwen3:* sao thinking; qwen2.5-coder:*, qwen2.5:*, llama3.2:*
    sao non-thinking.
    """
    m = model.lower()
    if m.startswith("qwen3"):
        return True
    return False


def call_ollama(
    model: str,
    prompt: str,
    *,
    think: bool,
    num_predict: int,
    num_gpu: int,
    tools: list | None = None,
    timeout: float = 180.0,
) -> tuple[float | None, dict | None, str]:
    """Chama /api/chat. Retorna (latencia, payload, erro_str).

    payload sempre tem keys: message.content, message.tool_calls (se houver).

    think=true so e enviado se supports_thinking(model)==True; senao usa
    think=false (Ollama rejeita com HTTP 400 caso contrario).
    """
    effective_think = think and supports_thinking(model)
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "think": effective_think,
        "stream": False,
        "keep_alive": "5m",
        "options": {
            "num_gpu": num_gpu,
            "num_ctx": 4096,
            "num_predict": num_predict,
        },
    }
    if tools:
        body["tools"] = tools
    t = time.monotonic()
    try:
        r = httpx.post(f"{NYX_OLLAMA_URL}/api/chat", json=body, timeout=timeout)
        dur = time.monotonic() - t
    except Exception as e:
        return None, None, f"{type(e).__name__}: {str(e)[:80]}"
    if r.status_code != 200:
        return None, None, f"http={r.status_code} {r.text[:120]}"
    return dur, r.json(), ""


def measure_model(
    model: str,
    n_amostras: int,
    num_gpu: int,
    verbose: bool = True,
) -> dict:
    """Mede um modelo nos 7 casos + 1 caso tool. Retorna dict de metricas."""
    result: dict = {
        "model": model,
        "num_gpu": num_gpu,
        "n_amostras_por_caso": n_amostras,
        "thinking_supported": supports_thinking(model),
        "casos": {},
        "tool_call": {},
    }

    all_lat: list[float] = []
    lang_hits = 0
    lang_total = 0
    # Metrica refinada: exclui intent=comando (slash commands sao interceptados
    # pelo CLI antes de chegar no LLM, ver nyx/agent/commands/). lang_rate "real"
    # = o que o usuario percebe em chat real.
    lang_hits_chat = 0
    lang_total_chat = 0
    vram_max = vram_used_mib()

    if verbose:
        print(f"\n[{model}] medindo {len(CASOS)} casos x {n_amostras} amostras...")

    for prompt, intent in CASOS:
        cls = classify(prompt)
        case_lats: list[float] = []
        case_errors: list[str] = []
        case_lang_hits = 0
        case_lang_total = 0
        last_content = ""
        # think adaptativo: chat puro -> false; tool-needed -> true (modelo
        # pode optar por não chamar tool e responder texto).
        think_flag = intent == "tool-needed"
        num_predict = 512 if think_flag else 256

        for _ in range(n_amostras):
            lat, payload, err = call_ollama(
                model,
                prompt,
                think=think_flag,
                num_predict=num_predict,
                num_gpu=num_gpu,
            )
            v = vram_used_mib()
            if v > vram_max:
                vram_max = v
            if err:
                case_errors.append(err)
                continue
            case_lats.append(lat)
            all_lat.append(lat)
            content = (payload or {}).get("message", {}).get("content", "") or ""
            if content:
                case_lang_total += 1
                if is_pt_br(content):
                    case_lang_hits += 1
                if not last_content:
                    last_content = content[:200]

        lang_hits += case_lang_hits
        lang_total += case_lang_total
        if intent != "comando":
            lang_hits_chat += case_lang_hits
            lang_total_chat += case_lang_total

        case_data = {
            "intent": cls,
            "intent_esperado": intent,
            "n_ok": len(case_lats),
            "errors": case_errors,
            "p50": round(statistics.median(case_lats), 3) if case_lats else None,
            "p95": round(max(case_lats), 3) if case_lats else None,
            "lang_pt_br_rate": (
                round(case_lang_hits / case_lang_total, 4) if case_lang_total else None
            ),
            "last_content": last_content,
        }
        result["casos"][prompt] = case_data
        if verbose:
            lat_str = f"p50={case_data['p50']}s" if case_data["p50"] else "FAIL"
            lang_str = (
                f"lang={case_data['lang_pt_br_rate']}"
                if case_data["lang_pt_br_rate"] is not None
                else "lang=?"
            )
            print(f"  -> {prompt!r:50} {lat_str:14} {lang_str}")

    # Tool call test: 1 prompt, 1 amostra, think=true, tools=[Read]
    if verbose:
        print("  -> tool call test (Read README.md, 1 amostra)")
    tool_prompt = "Leia o arquivo README.md e me diga em uma linha do que fala."
    lat, payload, err = call_ollama(
        model,
        tool_prompt,
        think=True,
        num_predict=512,
        num_gpu=num_gpu,
        tools=TOOL_READ_SCHEMA,
        timeout=180.0,
    )
    v = vram_used_mib()
    if v > vram_max:
        vram_max = v

    tool_ok = False
    tool_via_native = False
    tool_via_content_json = False
    tool_calls_emitted = []
    if not err and payload:
        msg = payload.get("message", {})
        tcs = msg.get("tool_calls") or []
        for tc in tcs:
            fn = (tc.get("function") or {}).get("name", "")
            tool_calls_emitted.append(fn)
            if fn.lower() == "read":
                tool_ok = True
                tool_via_native = True
        # Fallback nyx/agent/parser.py: extrai JSON do content quando o
        # campo tool_calls nativo do Ollama vem vazio (qwen2.5-coder em
        # non-thinking mode).
        if not tool_ok:
            content = msg.get("content", "") or ""
            try:
                start = content.find("{")
                if start >= 0:
                    candidate = content[start:]
                    depth = 0
                    for i, ch in enumerate(candidate):
                        if ch == "{":
                            depth += 1
                        elif ch == "}":
                            depth -= 1
                            if depth == 0:
                                blob = json.loads(candidate[: i + 1])
                                name = (
                                    blob.get("name")
                                    or blob.get("tool")
                                    or blob.get("function")
                                    or ""
                                )
                                if name.lower() == "read":
                                    tool_ok = True
                                    tool_via_content_json = True
                                    tool_calls_emitted.append(f"{name}(content_json)")
                                break
            except (json.JSONDecodeError, ValueError):
                pass

    result["tool_call"] = {
        "prompt": tool_prompt,
        "latency_s": round(lat, 3) if lat else None,
        "error": err or None,
        "tool_calls_emitted": tool_calls_emitted,
        "tool_call_ok": tool_ok,
        "tool_via_native_field": tool_via_native,
        "tool_via_content_json": tool_via_content_json,
        "tool_content_preview": (payload or {}).get("message", {}).get("content", "")[:200]
        if payload
        else "",
    }
    if verbose:
        if tool_ok:
            origem = "native" if tool_via_native else "content-json"
            status = f"OK[{origem}]"
        else:
            status = "MISS"
        print(f"     {status}: tools={tool_calls_emitted} lat={result['tool_call']['latency_s']}s")

    # Agregados.
    result["aggregate"] = {
        "n_lat_samples": len(all_lat),
        "p50_overall": round(statistics.median(all_lat), 3) if all_lat else None,
        "p95_overall": (
            round(statistics.quantiles(all_lat, n=20)[18], 3)
            if len(all_lat) >= 20
            else round(max(all_lat), 3) if all_lat else None
        ),
        "lang_pt_br_hits": lang_hits,
        "lang_pt_br_total": lang_total,
        "lang_pt_br_rate": round(lang_hits / lang_total, 4) if lang_total else None,
        # Metrica realistica: exclui intent=comando (interceptado pelo CLI).
        "lang_pt_br_hits_chat": lang_hits_chat,
        "lang_pt_br_total_chat": lang_total_chat,
        "lang_pt_br_rate_chat": (
            round(lang_hits_chat / lang_total_chat, 4) if lang_total_chat else None
        ),
        "tool_call_ok": tool_ok,
        "vram_pico_mib": vram_max,
    }
    return result


def score_model(agg: dict) -> dict:
    """Matriz de decisao ponderada (35/25/25/15).

    Retorna pontuacoes 0-100 por criterio + total. Usa lang_pt_br_rate_chat
    (exclui intent=comando, que e interceptado pelo CLI antes do LLM).
    """
    lang_rate = agg.get("lang_pt_br_rate_chat") or agg.get("lang_pt_br_rate") or 0.0
    p50 = agg["p50_overall"] or 9999.0
    tool_ok = bool(agg["tool_call_ok"])
    vram = agg["vram_pico_mib"] or 0

    # Lang: linear de 0->90% (0pts) ate 90%->100% (100pts -- meta).
    lang_pts = max(0.0, min(1.0, (lang_rate - 0.0) / 1.0)) * 100
    # Latencia P50: meta 8s. >=8s = 0 pts; <=2s = 100 pts; linear.
    if p50 <= 2:
        lat_pts = 100
    elif p50 >= 8:
        lat_pts = 0
    else:
        lat_pts = 100 * (8 - p50) / 6
    # Tool: binario 100/0.
    tool_pts = 100 if tool_ok else 0
    # VRAM: meta <= 4096 MiB. <=2GB=100pts; >=4GB=0pts.
    vram_gb = vram / 1024
    if vram_gb <= 2:
        vram_pts = 100
    elif vram_gb >= 4:
        vram_pts = 0
    else:
        vram_pts = 100 * (4 - vram_gb) / 2

    total = lang_pts * 0.35 + lat_pts * 0.25 + tool_pts * 0.25 + vram_pts * 0.15

    return {
        "lang_pts": round(lang_pts, 1),
        "lat_pts": round(lat_pts, 1),
        "tool_pts": round(tool_pts, 1),
        "vram_pts": round(vram_pts, 1),
        "total": round(total, 1),
    }


def render_table(results: list[dict]) -> str:
    """Tabela markdown literal pra colar no ADR."""
    head = (
        "| Modelo | P50 (s) | P95 (s) | lang_rate_chat | tool_ok | VRAM pico | Score |\n"
        "|---|---:|---:|---:|:---:|---:|---:|\n"
    )
    rows = []
    for r in results:
        agg = r["aggregate"]
        sc = r["score"]
        lang = agg.get("lang_pt_br_rate_chat", agg.get("lang_pt_br_rate"))
        rows.append(
            f"| `{r['model']}` "
            f"| {agg['p50_overall']} "
            f"| {agg['p95_overall']} "
            f"| {lang} "
            f"| {'OK' if agg['tool_call_ok'] else 'não'} "
            f"| {agg['vram_pico_mib']} MiB "
            f"| **{sc['total']}** |"
        )
    return head + "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        default="qwen3:4b,qwen2.5-coder:3b,qwen2.5-coder:7b",
        help="Lista CSV de modelos a benchmarkar.",
    )
    parser.add_argument("--n", type=int, default=3, help="Amostras por prompt (default 3).")
    parser.add_argument(
        "--num-gpu-3b", type=int, default=-1, help="num_gpu para modelos pequenos (default -1=auto)."
    )
    parser.add_argument(
        "--num-gpu-7b", type=int, default=12, help="num_gpu para 7b (default 12=cap run.sh)."
    )
    parser.add_argument(
        "--skip-7b", action="store_true", help="Pula qwen2.5-coder:7b se VRAM apertada."
    )
    parser.add_argument(
        "--out", default=None, help="Path de saida JSON (default logs/model_compare.json)."
    )
    args = parser.parse_args()

    if not health_check():
        print(f"[err] Ollama não responde em {NYX_OLLAMA_URL}/api/version", file=sys.stderr)
        return 2

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.skip_7b:
        models = [m for m in models if "7b" not in m]

    print(f"[model_compare] modelos: {models}, n_amostras={args.n}")
    print(f"[model_compare] VRAM antes: {vram_used_mib()} MiB")

    results: list[dict] = []
    for model in models:
        # Heuristica num_gpu: 7b apertado, demais auto.
        ngpu = args.num_gpu_7b if "7b" in model else args.num_gpu_3b
        try:
            r = measure_model(model, args.n, ngpu, verbose=True)
        except Exception as e:
            print(f"[err] modelo {model} falhou: {type(e).__name__}: {e}", file=sys.stderr)
            r = {
                "model": model,
                "num_gpu": ngpu,
                "error": f"{type(e).__name__}: {str(e)[:200]}",
                "aggregate": {
                    "p50_overall": None,
                    "p95_overall": None,
                    "lang_pt_br_rate": None,
                    "tool_call_ok": False,
                    "vram_pico_mib": vram_used_mib(),
                },
            }
        r["score"] = score_model(r["aggregate"])
        results.append(r)

        # Descarrega modelo antes do próximo (libera VRAM).
        try:
            httpx.post(
                f"{NYX_OLLAMA_URL}/api/generate",
                json={"model": model, "keep_alive": 0},
                timeout=5.0,
            )
        except Exception:
            pass
        time.sleep(2)
        print(f"[model_compare] VRAM apos {model}: {vram_used_mib()} MiB")

    out_payload = {
        "timestamp": int(time.time()),
        "ollama_url": NYX_OLLAMA_URL,
        "n_amostras": args.n,
        "models": results,
    }

    # Ranking textual.
    print("\n" + "=" * 60)
    print("TABELA COMPARATIVA (matriz de decisao 35/25/25/15)")
    print("=" * 60)
    print(render_table(results))

    sorted_by_score = sorted(
        results,
        key=lambda x: x["score"]["total"],
        reverse=True,
    )
    print("Ranking:")
    for i, r in enumerate(sorted_by_score, 1):
        print(
            f"  {i}. {r['model']}: total={r['score']['total']} "
            f"(lang={r['score']['lang_pts']}, lat={r['score']['lat_pts']}, "
            f"tool={r['score']['tool_pts']}, vram={r['score']['vram_pts']})"
        )

    out_path = (
        Path(args.out)
        if args.out
        else _PROJECT_ROOT / "logs" / "model_compare.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[ok] resultado em {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


# "Comparar modelos sem benchmark literal e fe; com benchmark e engenharia."
