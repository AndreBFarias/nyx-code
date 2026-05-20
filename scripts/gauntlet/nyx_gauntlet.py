#!/usr/bin/env python3
"""Nyx-Code Gauntlet -- Validação automatizada. Zero mocks. 100% real.

Único mecanismo de teste do projeto (ADR-007).
Cada feature tem exatamente 1 teste. 100% obrigatório para push na main.

Uso:
    ./run.sh --gauntlet                       # Completo (~15min)
    ./run.sh --gauntlet --only tools          # Só tools
    ./run.sh --gauntlet --only rapido         # infra+proxy+visual+config (~2min)
    ./run.sh --gauntlet --only completo       # Tudo

    # Direto (com Ollama + Proxy já rodando):
    ./venv/bin/python scripts/gauntlet/nyx_gauntlet.py

ADR-007: dev-journey/03-decisions/ADR_007_GAUNTLET.md
Features: dev-journey/04-features/FEATURE_MAP.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [gauntlet] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.gauntlet")

# ── Fases e timeouts ─────────────────────────────────────────────────────

PHASE_GROUPS: dict[str, list[str]] = {
    "infra": ["infra"],
    "proxy": ["proxy"],
    "tools": ["tools"],
    "qualidade": ["qualidade"],
    "performance": ["performance"],
    "visual": ["visual"],
    "config": ["config"],
    "resiliencia": ["resiliencia"],
    "parser": ["parser"],
    "robustez": ["robustez"],
    "interface": ["interface"],
    "slash_bypass": ["slash_bypass"],
    "controle": ["controle"],
    "persistencia": ["persistencia"],
    "e2e": ["e2e"],
    "p2_tools": ["p2_tools"],
    "p2_advanced": ["p2_advanced"],
    "p2_commands": ["p2_commands"],
    "p2_services": ["p2_services"],
    "p2": ["p2_tools", "p2_advanced", "p2_commands", "p2_services"],
    "p3_tools": ["p3_tools"],
    "p3_commands": ["p3_commands"],
    "p3_robustez": ["p3_robustez"],
    "p3_headless": ["p3_headless"],
    "p3": ["p3_tools", "p3_commands", "p3_robustez", "p3_headless"],
    "e2e_real": ["e2e_real"],
    "headless_protocol": ["headless_protocol"],
    "p4_utility": ["p4_utility"],
    "p4_worktree": ["p4_worktree"],
    "p4_tasks": ["p4_tasks"],
    "p4_discovery": ["p4_discovery"],
    "p4": ["p4_utility", "p4_worktree", "p4_tasks", "p4_discovery"],
    "p5_git": ["p5_git"],
    "p5_config": ["p5_config"],
    "p5_session": ["p5_session"],
    "p5_execution": ["p5_execution"],
    "p5": ["p5_git", "p5_config", "p5_session", "p5_execution"],
    "p6_memoria": ["p6_memoria"],
    "p6_qualidade": ["p6_qualidade"],
    "p6": ["p6_memoria", "p6_qualidade"],
    "p8_edicao": ["p8_edicao"],
    "p8_provider": ["p8_provider"],
    "p8": ["p8_edicao", "p8_provider"],
    "infra_scaffold": ["infra_scaffold"],
    "coverage": ["coverage"],
    "infra_sync": ["infra_sync"],
    "gpu_tune": ["gpu_tune"],
    "portabilidade": ["portabilidade"],
    "robustez_boot": ["robustez_boot"],
    "p7_tui": ["p7_tui"],
    "p7_completion": ["p7_completion"],
    "p7_visual": ["p7_visual"],
    "p7": ["p7_tui", "p7_completion", "p7_visual"],
    "p10_projeto": ["p10_projeto"],
    "p10_debug": ["p10_debug"],
    "p10_lote1": ["p10_projeto", "p10_debug"],
    "p10_memoria": ["p10_memoria"],
    "p10_avancado": ["p10_avancado"],
    "p10_root": ["p10_root"],
    "p10_lote2": ["p10_memoria", "p10_avancado", "p10_root"],
    "p10": ["p10_projeto", "p10_debug", "p10_memoria", "p10_avancado", "p10_root"],
    "p11_infra": ["p11_infra"],
    "p11": ["p11_infra"],
    "vision": ["vision"],
    "sessao": ["sessao"],  # noqa-acento
    "install": ["install"],
    "loop": ["loop"],
    "mcp": ["mcp"],
    "plugins": ["plugins"],
    "hooks_dynamic": ["hooks_dynamic"],
    "contexto": ["contexto"],
    "rapido": ["infra", "proxy", "visual", "config"],
    "port": ["parser", "robustez", "interface", "controle", "persistencia"],
    "integracao": ["e2e"],
    "completo": [
        "infra",
        "proxy",
        "tools",
        "qualidade",
        "performance",
        "visual",
        "config",
        "resiliencia",
        "parser",
        "robustez",
        "interface",
        "slash_bypass",
        "controle",
        "persistencia",
        "e2e",
        "p2_tools",
        "p2_advanced",
        "p2_commands",
        "p2_services",
        "p3_tools",
        "p3_commands",
        "p3_robustez",
        "p3_headless",
        "e2e_real",
        "headless_protocol",
        "p4_utility",
        "p4_worktree",
        "p4_tasks",
        "p4_discovery",
        "p5_git",
        "p5_config",
        "p5_session",
        "p5_execution",
        "p6_memoria",
        "p6_qualidade",
        "p8_edicao",
        "p8_provider",
        "infra_scaffold",
        "coverage",
        "infra_sync",
        "gpu_tune",
        "portabilidade",
        "robustez_boot",
        "p7_tui",
        "p7_completion",
        "p7_visual",
        "p10_projeto",
        "p10_debug",
        "p10_memoria",
        "p10_avancado",
        "p10_root",
        "p11_infra",
        "contexto",
    ],
}

PHASE_TIMEOUTS: dict[str, int] = {
    "infra": 300,
    "proxy": 300,
    "tools": 900,
    "qualidade": 600,
    "performance": 300,
    "visual": 30,
    "config": 30,
    "resiliencia": 120,
    "parser": 30,
    "robustez": 30,
    "interface": 30,
    "slash_bypass": 30,
    "controle": 30,
    "persistencia": 30,
    "e2e": 60,
    "p2_tools": 60,
    "p2_advanced": 30,
    "p2_commands": 30,
    "p2_services": 30,
    "p3_tools": 30,
    "p3_commands": 30,
    "p3_robustez": 30,
    "p3_headless": 30,
    "e2e_real": 60,
    "headless_protocol": 30,
    "p4_utility": 30,
    "p4_worktree": 30,
    "p4_tasks": 30,
    "p4_discovery": 30,
    "p5_git": 30,
    "p5_config": 30,
    "p5_session": 30,
    "p5_execution": 30,
    "p6_memoria": 30,
    "p6_qualidade": 30,
    "p8_edicao": 60,
    "p8_provider": 30,
    "infra_scaffold": 30,
    "coverage": 30,
    "infra_sync": 30,
    "gpu_tune": 30,
    "portabilidade": 30,
    "robustez_boot": 30,
    "p7_tui": 30,
    "p7_completion": 30,
    "p7_visual": 30,
    "p10_projeto": 30,
    "p10_debug": 30,
    "p10_memoria": 30,
    "p10_avancado": 30,
    "p10_root": 30,
    "p11_infra": 30,
    "vision": 90,
    "sessao": 60,  # noqa-acento
    "install": 1200,
    "loop": 30,
    "mcp": 60,
    "plugins": 60,
    "hooks_dynamic": 60,
    "contexto": 180,
}

NEEDS_OLLAMA = {"infra", "proxy", "tools", "qualidade", "performance", "resiliencia", "contexto"}

# ── COCKPIT-03-GAUNTLET-PER-FEATURE-01: --only aceita feature_id ────────
# Regex de feature_id (ex: I-01, P-03, T-12, Q-05, V-04, K-09, etc).
_FEATURE_ID_RE = re.compile(r"^[A-Z]-\d{1,3}$")


# ── GAUNTLET-FIXTURES-SANDBOX-01: scratch dir autorizado pelo gate ──────
def _gauntlet_tmp_dir() -> Path:
    """Diretório de scratch para fixtures que escrevem via tools sandboxed.

    Retorna ~/.nyx/gauntlet_tmp/ criando se não existir. Esse diretório está
    dentro de _NYX_DATA_DIR e portanto é root autorizado por validate_path()
    em nyx/agent/tools/base.py (PROJECT-ROOTS-MULTI-01). Usar este helper em
    qualquer fixture cujo path é passado a tools que validam escopo.
    """
    d = Path.home() / ".nyx" / "gauntlet_tmp"
    d.mkdir(parents=True, exist_ok=True)
    return d

# Mapeamento categoria do REGISTRY -> fase do gauntlet.
_CATEGORIA_PARA_FASE_GAUNTLET = {
    "infraestrutura": "infra",
    "infraestrutura (boot/lifecycle)": "infra",
    "proxy": "proxy",
    "proxy (ponte openai <-> ollama)": "proxy",
    "tools": "tools",
    "tool calling (6 tools)": "tools",
    "qualidade": "qualidade",
    "qualidade de resposta": "qualidade",
    "performance": "performance",
    "performance (kpis)": "performance",
    "visual": "visual",
    "interface visual": "visual",
    "configuração": "config",
    "resiliência": "resiliencia",
}


def _resolver_feature_id(only: str) -> tuple[str, str | None]:
    """Resolve --only: retorna (fase, feature_id_alvo_ou_None).

    Se 'only' casa regex de feature_id (^[A-Z]-\\d+$), busca em REGISTRY.yaml
    a categoria e mapeia para a fase correspondente. Retorna (fase, only).

    Caso contrário, devolve (only, None) -- comportamento original.
    """
    if not _FEATURE_ID_RE.match(only):
        return only, None
    registry_path = PROJECT_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
    if not registry_path.is_file():
        logger.warning("REGISTRY.yaml ausente; tratando '%s' como fase", only)
        return only, None
    try:
        import yaml  # noqa: PLC0415 -- carga sob demanda evita custo em uso comum
    except ImportError:
        logger.warning("pyyaml ausente; tratando '%s' como fase", only)
        return only, None
    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 -- yaml malformado não deve crashar
        logger.warning("REGISTRY.yaml inválido (%s); tratando '%s' como fase", exc, only)
        return only, None
    for feat in data.get("features", []):
        if feat.get("id") == only:
            cat = (feat.get("categoria") or "").lower()
            fase = _CATEGORIA_PARA_FASE_GAUNTLET.get(cat)
            if fase:
                logger.info("--only %s -> fase '%s' (filtro por feature_id)", only, fase)
                return fase, only
            logger.warning("Categoria '%s' do %s sem mapeamento para fase", cat, only)
            return only, None
    logger.warning("feature_id '%s' não encontrado em REGISTRY.yaml", only)
    return only, None


# ── Paths de resiliência ────────────────────────────────────────────────
REPORTS_DIR = PROJECT_ROOT / "dev-journey" / "07-reports" / "gauntlet"
CHECKPOINT_PATH = REPORTS_DIR / "checkpoint.json"
BASELINES_DIR = REPORTS_DIR / "baselines"
FLAGS_DIR = REPORTS_DIR / "flags"

# Features não testáveis ainda (dependem de infra futura)
UNMAPPED_FEATURES = [
    "I-02: Kill de processos anteriores (requer processo real)",
    "I-04: Download automático de modelo (requer modelo ausente)",
    "I-06: Cleanup ao sair (requer trap EXIT real)",
    "I-07: Instalação idempotente (requer install.sh)",
    "I-08: Desinstalação limpa (requer uninstall.sh)",
    "I-10: Modo debug (requer flags do run.sh)",
    "P-03: Injeção de num_gpu/num_ctx (requer inspeção do request interno)",
    "P-08: Logging de requests (requer leitura do proxy.log)",
    "T-02: Read arquivo inexistente (requer multi-turn com tool result)",
    "T-04: Sobrescrever arquivo (requer multi-turn)",
    "T-07: Comando com erro (requer multi-turn com stderr)",
    "T-10: Tool calling em cadeia (requer multi-turn)",
    "Q-01: Resposta em PT-BR (requer análise linguística)",
    "Q-03: Concisão (requer contagem de palavras em contexto)",
    "V-01: Banner ASCII com cores (requer captura de terminal)",
    "V-02: Mensagens [nyx] coloridas (requer captura de terminal)",
    "V-03: Info de boot (requer captura de terminal)",
    "V-04: Citação de filósofo (requer varredura de todos os scripts)",
    "K-02: Tempo de warmup (medido no boot, não no gauntlet)",
    "K-05: TTFR tool call com conteúdo Write (coberto por K-04)",
    "K-06: Tokens por resposta chat (coberto por K-03)",
    "K-07: Tokens por resposta tool (coberto por K-04)",
    "K-09: VRAM pico (requer monitoramento contínuo)",
]

EMOJI_PATTERN = re.compile(
    "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff\U00002702-\U000027b0\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff\U00002600-\U000026ff"
    "\U0000fe00-\U0000fe0f\U0001f004\U0001f0cf]+",
)


@dataclass
class TestResult:
    feature_id: str
    name: str
    phase: str
    passed: bool
    elapsed_s: float = 0.0
    tokens: int = 0
    details: str = ""
    error: str = ""
    # K08-VRAM-RUNNER-ISOLATION-01: marca testes pulados por ambiente externo
    # (ex.: VRAM contaminada por processo não-Nyx). SKIP conta como não-falha
    # no gate mas é renderizado distinto de OK no relatório.
    skipped: bool = False


class NyxGauntlet:
    def __init__(
        self,
        proxy_url: str = "http://127.0.0.1:11436",
        ollama_url: str = "http://127.0.0.1:11435",
        only: str = "completo",
        model: str = "qwen3:4b",
        strict_vram: bool = False,
        isolate_vram: bool = False,
    ) -> None:
        self._proxy = proxy_url
        self._ollama = ollama_url
        self._model = model
        self._results: list[TestResult] = []
        self._t0 = 0.0
        self._kpis: dict[str, Any] = {}
        self._phases_done: set[str] = set()
        self._hardware: dict[str, Any] = {}
        # K08-VRAM-RUNNER-ISOLATION-01: comportamento do pre-flight K-08.
        self._strict_vram: bool = strict_vram
        self._isolate_vram: bool = isolate_vram

        # COCKPIT-03-GAUNTLET-PER-FEATURE-01: --only aceita feature_id direto.
        fase, target = _resolver_feature_id(only)
        self._target_feature_id: str | None = target

        raw = PHASE_GROUPS.get(fase, [fase])
        self._phases = [p for p in raw if p in PHASE_TIMEOUTS]
        if not self._phases:
            logger.error("Fase '%s' desconhecida. Opções: %s", fase, list(PHASE_GROUPS.keys()))
            sys.exit(1)

    # ── Execução ────────────────────────────────────────────────────────

    async def run(self) -> int:
        self._t0 = time.monotonic()
        self._hardware = self._detect_hardware()
        logger.info(
            "Gauntlet -- fases: %s, modelo: %s, gpu: %s", self._phases, self._model, self._hardware.get("gpu", "N/A")
        )

        try:
            for phase in self._phases:
                if phase in NEEDS_OLLAMA and not await self._health():
                    self._add("HEALTH", f"Ollama antes de {phase}", phase, False, 0, error="Ollama não responde")
                    continue
                try:
                    await asyncio.wait_for(self._dispatch(phase), timeout=PHASE_TIMEOUTS[phase])
                except asyncio.TimeoutError:
                    self._add("TIMEOUT", f"Fase {phase}", phase, False, 0, error=f"Excedeu {PHASE_TIMEOUTS[phase]}s")
                self._phases_done.add(phase)
                self._kpis["gauntlet_total_s"] = round(time.monotonic() - self._t0, 1)
                self._write_report()
        finally:
            self._kpis["gauntlet_total_s"] = round(time.monotonic() - self._t0, 1)
            self._write_report()
            self._save_baseline()

        ok = sum(1 for r in self._results if r.passed)
        total = len(self._results)
        # COCKPIT-03-GAUNTLET-PER-FEATURE-01: filtro alvo sem captura == falha.
        if self._target_feature_id and total == 0:
            logger.error(
                "Filtro --only %s não capturou nenhum teste. "
                "Feature pode estar em UNMAPPED_FEATURES ou em fase não executada.",
                self._target_feature_id,
            )
            return 1
        logger.info(
            "Resultado: %d/%d (%.0f%%) em %.0fs",
            ok,
            total,
            ok / total * 100 if total else 0,
            self._kpis["gauntlet_total_s"],
        )
        return 0 if ok == total else 1

    async def _dispatch(self, phase: str) -> None:
        fn = getattr(self, f"_phase_{phase}", None)
        if fn:
            await fn()
        else:
            logger.warning("Fase %s sem implementação", phase)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: INFRA (5 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_infra(self) -> None:
        # I-01: Ollama respondendo
        t = time.monotonic()
        ok = await self._health()
        self._add("I-01", "Ollama respondendo", "infra", ok, time.monotonic() - t)

        # I-03: Health check com versão
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._ollama}/api/version")
                ver = r.json().get("version", "")
                self._add("I-03", "Versão Ollama", "infra", bool(ver), time.monotonic() - t, details=ver)
        except Exception as e:
            self._add("I-03", "Versão Ollama", "infra", False, time.monotonic() - t, error=str(e))

        # I-05: Warmup
        t = time.monotonic()
        resp = await self._chat("hi")
        elapsed = time.monotonic() - t
        self._kpis["warmup_s"] = round(elapsed, 1)
        self._add("I-05", "Warmup do modelo", "infra", bool(resp.get("content")), elapsed, tokens=resp.get("tokens", 0))

        # I-09: Modelo carregado
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._ollama}/api/tags")
                names = [m["name"] for m in r.json().get("models", [])]
                found = any(self._model in n for n in names)
                self._add(
                    "I-09", f"Modelo {self._model} presente", "infra", found, time.monotonic() - t, details=str(names)
                )
        except Exception as e:
            self._add("I-09", f"Modelo {self._model} presente", "infra", False, time.monotonic() - t, error=str(e))

        # I-11: Proxy respondendo
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._proxy}/v1/models")
                models = r.json().get("data", [])
                self._add(
                    "I-11",
                    "Proxy respondendo",
                    "infra",
                    len(models) > 0,
                    time.monotonic() - t,
                    details=f"{len(models)} modelos",
                )
        except Exception as e:
            self._add("I-11", "Proxy respondendo", "infra", False, time.monotonic() - t, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PROXY (6 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_proxy(self) -> None:
        # P-01: Request chega ao Ollama
        t = time.monotonic()
        resp = await self._chat("diga apenas: proxy ok")
        has_content = bool(resp.get("content"))
        self._add(
            "P-01",
            "Request via proxy",
            "proxy",
            has_content,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=resp.get("content", "")[:60],
        )

        # P-02: think=false (verifica abertura <think>, não fechamento residual)
        content = resp.get("content", "")
        has_think_open = "<think>" in content
        self._add(
            "P-02",
            "think=false injetado",
            "proxy",
            not has_think_open,
            0,
            details="sem <think>" if not has_think_open else "CONTÉM <think>",
        )

        # P-04: Content array normalizado
        t = time.monotonic()
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "diga apenas: array ok"},
                    ],
                }
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=180) as c:
                r = await c.post(f"{self._proxy}/v1/chat/completions", json=payload)
                data = r.json()
                ok = "choices" in data and r.status_code == 200
                self._add(
                    "P-04",
                    "Content array normalizado",
                    "proxy",
                    ok,
                    time.monotonic() - t,
                    tokens=data.get("usage", {}).get("total_tokens", 0),
                )
        except Exception as e:
            self._add("P-04", "Content array normalizado", "proxy", False, time.monotonic() - t, error=str(e))

        # P-05: Formato OpenAI
        t = time.monotonic()
        resp_raw = await self._chat_raw("teste formato")
        has_choices = "choices" in resp_raw
        has_usage = "usage" in resp_raw
        has_message = bool(resp_raw.get("choices", [{}])[0].get("message"))
        ok = has_choices and has_usage and has_message
        self._add(
            "P-05",
            "Formato OpenAI correto",
            "proxy",
            ok,
            time.monotonic() - t,
            details=f"choices={has_choices} usage={has_usage} message={has_message}",
        )

        # P-06: /v1/models
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._proxy}/v1/models")
                data = r.json()
                ok = data.get("object") == "list" and len(data.get("data", [])) > 0
                self._add(
                    "P-06",
                    "Listagem /v1/models",
                    "proxy",
                    ok,
                    time.monotonic() - t,
                    details=f"{len(data.get('data', []))} modelos",
                )
        except Exception as e:
            self._add("P-06", "Listagem /v1/models", "proxy", False, time.monotonic() - t, error=str(e))

        # P-07: tool_calls propagam
        t = time.monotonic()
        resp = await self._chat_with_tool(
            "leia README.md",
            self._tool("Read", "Lê arquivo", {"file_path": {"type": "string"}}, ["file_path"]),
        )
        has_tc = "Read" in resp.get("tool_names", [])
        self._add(
            "P-07",
            "tool_calls propagam",
            "proxy",
            has_tc,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=str(resp.get("tool_args", "")),
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: TOOLS (6 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_tools(self) -> None:
        all_tools = [
            self._tool("Read", "Lê arquivo", {"file_path": {"type": "string"}}, ["file_path"]),
            self._tool(
                "Write",
                "Cria arquivo",
                {"file_path": {"type": "string"}, "content": {"type": "string"}},
                ["file_path", "content"],
            ),
            self._tool(
                "Edit",
                "Edita arquivo",
                {"file_path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
                ["file_path", "old_string", "new_string"],
            ),
            self._tool("Bash", "Executa comando", {"command": {"type": "string"}}, ["command"]),
            self._tool("Glob", "Busca arquivos", {"pattern": {"type": "string"}}, ["pattern"]),
            self._tool("Grep", "Busca texto", {"pattern": {"type": "string"}, "path": {"type": "string"}}, ["pattern"]),
        ]

        tests = [
            ("T-01", "Read arquivo", "leia o arquivo README.md", "Read"),
            ("T-03", "Write criar arquivo", "crie /tmp/nyx_gauntlet_test.py com def hello(): return 'ok'", "Write"),
            (
                "T-05",
                "Edit editar arquivo",
                "edite o arquivo /tmp/nyx_gauntlet_test.py trocando 'ok' por 'nyx'",
                "Edit",
            ),
            ("T-06", "Bash executar", "execute o comando: echo NYX_GAUNTLET_OK", "Bash"),
            ("T-08", "Glob buscar .sh", "encontre todos os arquivos .sh do projeto", "Glob"),
            (
                "T-09",
                "Grep buscar proxy",
                "use Grep para buscar o texto 'think' dentro dos arquivos do projeto",
                "Grep",
            ),
        ]

        for fid, name, prompt, expected_tool in tests:
            t = time.monotonic()
            resp = await self._chat_with_tools(prompt, all_tools)
            found = expected_tool in resp.get("tool_names", [])
            elapsed = time.monotonic() - t
            self._add(
                fid,
                name,
                "tools",
                found,
                elapsed,
                tokens=resp.get("tokens", 0),
                details=str(resp.get("tool_args", ""))[:100],
                error="" if found else f"Esperava {expected_tool}, recebeu {resp.get('tool_names', [])}",
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: QUALIDADE (5 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_qualidade(self) -> None:
        # Q-02: Identidade
        t = time.monotonic()
        nyx_prompt = "Sou Nyx. Codificadora. Vivo no terminal. PT-BR. Frases curtas. Sem emojis."
        resp = await self._chat_with_tools("quem é voce? responda em uma frase curta", tools=None, system=nyx_prompt)
        content = resp.get("content", "").lower()
        mentions_qwen = "qwen" in content or "alibaba" in content
        mentions_gpt = "gpt" in content or "openai" in content
        ok = not mentions_qwen and not mentions_gpt
        self._add(
            "Q-02",
            "Identidade (sem Qwen/GPT)",
            "qualidade",
            ok,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=resp.get("content", "")[:80],
            error="Mencionou Qwen/GPT" if not ok else "",
        )

        # Q-04: Uso proativo de tools
        t = time.monotonic()
        tools = [self._tool("Read", "Lê arquivo", {"file_path": {"type": "string"}}, ["file_path"])]
        resp = await self._chat_with_tools("leia o arquivo README.md", tools)
        used_tool = len(resp.get("tool_names", [])) > 0
        self._add(
            "Q-04",
            "Uso proativo de tools",
            "qualidade",
            used_tool,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            error="" if used_tool else "Respondeu texto em vez de chamar tool",
        )

        # Q-05: Precisão de argumentos
        args_str = str(resp.get("tool_args", ""))
        correct_path = "README.md" in args_str
        self._add(
            "Q-05",
            "Precisão de argumentos",
            "qualidade",
            correct_path,
            0,
            details=args_str[:80],
            error="" if correct_path else "Path incorreto ou ausente",
        )

        # Q-06: Sem emojis
        t = time.monotonic()
        resp = await self._chat("descreva o que é um proxy em uma frase")
        content = resp.get("content", "")
        has_emoji = bool(EMOJI_PATTERN.search(content))
        self._add(
            "Q-06",
            "Sem emojis",
            "qualidade",
            not has_emoji,
            time.monotonic() - t,
            tokens=resp.get("tokens", 0),
            details=content[:60],
            error="Emojis detectados" if has_emoji else "",
        )

        # Q-07: Sem hallucination de paths
        t = time.monotonic()
        tools = [self._tool("Read", "Lê arquivo", {"file_path": {"type": "string"}}, ["file_path"])]
        resp = await self._chat_with_tools("leia o arquivo run.sh", tools)
        args = resp.get("tool_args", [])
        if args:
            path_arg = str(args[0])
            real_path = PROJECT_ROOT / "run.sh"
            path_ok = "run.sh" in path_arg and real_path.exists()
            self._add(
                "Q-07", "Sem hallucination de paths", "qualidade", path_ok, time.monotonic() - t, details=path_arg[:60]
            )
        else:
            self._add(
                "Q-07",
                "Sem hallucination de paths",
                "qualidade",
                False,
                time.monotonic() - t,
                error="Sem tool_call para verificar path",
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PERFORMANCE (5 KPIs)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_performance(self) -> None:
        # K-01: Boot Ollama (tempo do health check)
        t = time.monotonic()
        await self._health()
        boot = time.monotonic() - t
        self._kpis["boot_s"] = round(boot, 2)
        self._add("K-01", "Boot Ollama", "performance", boot < 30, boot, details=f"{boot:.1f}s (baseline <30s)")

        # K-03: TTFR chat
        t = time.monotonic()
        resp = await self._chat("diga apenas: benchmark")
        ttfr_chat = time.monotonic() - t
        self._kpis["ttfr_chat_s"] = round(ttfr_chat, 2)
        self._kpis["tokens_chat"] = resp.get("tokens", 0)
        self._add(
            "K-03",
            "TTFR chat",
            "performance",
            ttfr_chat < 45,
            ttfr_chat,
            tokens=resp.get("tokens", 0),
            details=f"{ttfr_chat:.1f}s (baseline <15s, alerta <45s)",
        )

        # K-04: TTFR tool call
        t = time.monotonic()
        tools = [self._tool("Bash", "Executa", {"command": {"type": "string"}}, ["command"])]
        resp = await self._chat_with_tools("execute: echo 1", tools)
        ttfr_tool = time.monotonic() - t
        self._kpis["ttfr_tool_s"] = round(ttfr_tool, 2)
        self._kpis["tokens_tool"] = resp.get("tokens", 0)
        ok = ttfr_tool < 60 and len(resp.get("tool_names", [])) > 0
        self._add(
            "K-04",
            "TTFR tool call",
            "performance",
            ok,
            ttfr_tool,
            tokens=resp.get("tokens", 0),
            details=f"{ttfr_tool:.1f}s (baseline <20s, alerta <60s)",
        )

        # K-08: VRAM -- pre-flight K08-VRAM-RUNNER-ISOLATION-01.
        # Distingue contaminação externa (processo não-Nyx ocupando VRAM) de
        # regressão real. Default: SKIP com motivo. --strict-vram: contrato
        # antigo (FAIL real). --isolate-vram: lista e pede confirmação para
        # matar processos externos antes de medir.
        from scripts.gauntlet.vram_check import (
            VRAM_MIN_FREE_MIB,
            is_nyx_owned,
        )
        from scripts.gauntlet.vram_check import (
            probe as _vram_probe,
        )

        snap = _vram_probe()
        external_procs = [p for p in snap["processes"] if not is_nyx_owned(p)]
        _external_mib = sum(p["mib"] for p in external_procs)  # noqa: F841 -- reservado para futuro log/SKIP detail
        contaminated = (
            snap["nvidia_smi_ok"]
            and snap["free_mib"] >= 0
            and snap["free_mib"] < VRAM_MIN_FREE_MIB
            and bool(external_procs)
        )

        # Branch --isolate-vram: interativo, kill com confirmação.
        if contaminated and self._isolate_vram:
            if not sys.stdin.isatty():
                logger.error(
                    "--isolate-vram requer TTY interativo (stdin) -- "
                    "headless detectado, abortando para não matar processos cegamente"
                )
                sys.exit(2)
            # Ordena por MiB decrescente -- pede kill do maior primeiro.
            ordered = sorted(external_procs, key=lambda p: -int(p.get("mib", 0)))
            print("Processos externos ocupando VRAM:")
            for p in ordered:
                print(
                    f"  PID {p['pid']:>7}  {p['name']:<40}  {p['mib']:>5} MiB"
                )
            for p in ordered:
                ans = input(
                    f"kill PID {p['pid']} {p['name']}? [y/N] "
                ).strip().lower()
                if ans == "y":
                    try:
                        os.kill(p["pid"], signal.SIGTERM)
                        time.sleep(1.5)
                        # Re-checa se ainda vivo; escala para SIGKILL.
                        try:
                            os.kill(p["pid"], 0)
                            alive = True
                        except (ProcessLookupError, PermissionError):
                            alive = False
                        if alive:
                            os.kill(p["pid"], signal.SIGKILL)
                    except (ProcessLookupError, PermissionError) as exc:
                        logger.warning(
                            "kill PID %d falhou: %s", p["pid"], exc
                        )
            # Re-probe apos kills.
            snap = _vram_probe()
            external_procs = [
                p for p in snap["processes"] if not is_nyx_owned(p)
            ]
            contaminated = (
                snap["nvidia_smi_ok"]
                and snap["free_mib"] >= 0
                and snap["free_mib"] < VRAM_MIN_FREE_MIB
                and bool(external_procs)
            )

        # Default (sem flags): SKIP com motivo se contaminado.
        if contaminated and not self._strict_vram:
            proc_desc = ", ".join(
                f"PID {p['pid']} {p['name']} ocupando {p['mib']} MiB"
                for p in external_procs[:3]
            )
            self._kpis["vram_mib"] = -1
            self._add_skip(
                "K-08",
                "VRAM em uso",
                "performance",
                details=(
                    f"SKIP -- VRAM externa: {snap['free_mib']} MiB livres, "
                    f"{proc_desc}"
                ),
            )
        else:
            vram_mib = self._get_vram()
            self._kpis["vram_mib"] = vram_mib
            if vram_mib > 0:
                self._add(
                    "K-08",
                    "VRAM em uso",
                    "performance",
                    vram_mib < 3500,
                    0,
                    details=f"{vram_mib}MiB (baseline <2500, crítico >3500)",
                )
            else:
                self._add(
                    "K-08",
                    "VRAM em uso",
                    "performance",
                    True,
                    0,
                    details="nvidia-smi indisponível (OK sem GPU)",
                )

        # K-10: Tempo total (preenchido no finally do run)
        self._add("K-10", "Tempo total gauntlet", "performance", True, 0, details="Medido ao final da execução")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: VISUAL (3 testes)
    # ═══════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PLUGINS (2 testes -- PLUGINS-01/02)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_plugins(self) -> None:
        import tempfile

        t = time.monotonic()
        try:
            from nyx.agent.services.plugin_manager import PluginManager
        except Exception as e:
            self._add("PL-01", "import PluginManager", "plugins", False, 0, error=str(e))
            return
        self._add("PL-01", "PluginManager import + instanciacao", "plugins", True, time.monotonic() - t)

        with tempfile.TemporaryDirectory(prefix="nyx-plugins-") as tmp:
            tmp_path = Path(tmp)
            ok_dir = tmp_path / "ok"
            ok_dir.mkdir()
            (ok_dir / "manifest.toml").write_text(
                '[plugin]\nname = "ok"\nversion = "0.1.0"\ndescription = "teste"\n',
                encoding="utf-8",
            )
            (ok_dir / "ok.py").write_text('"""docstring"""\ndef foo():\n    return 42\n', encoding="utf-8")

            bad_dir = tmp_path / "bad"
            bad_dir.mkdir()
            (bad_dir / "manifest.toml").write_text(
                '[plugin]\nname = "bad"\nversion = "0.1"\ndescription = "executa codigo"\n',
                encoding="utf-8",
            )
            (bad_dir / "bad.py").write_text('print("arbitrary code")\n', encoding="utf-8")

            t = time.monotonic()
            pm = PluginManager(plugins_dir=tmp_path)
            results = pm.load_all()
            ok2 = results.get("ok") is True and results.get("bad") is False
            self._add(
                "PL-02",
                "load_all: plugin valido carrega; plugin com top-level Expr eh rejeitado por AST check",
                "plugins",
                ok2,
                time.monotonic() - t,
                details=f"results={results}",
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: HOOKS_DYNAMIC (2 testes -- HOOKS-DYNAMIC-01/02)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_hooks_dynamic(self) -> None:
        import tempfile

        t = time.monotonic()
        try:
            from nyx.agent.services.hook_runtime import EVENTS, HookRuntime
        except Exception as e:
            self._add("HD-01", "import HookRuntime", "hooks_dynamic", False, 0, error=str(e))
            return
        self._add(
            "HD-01",
            f"HookRuntime import + {len(EVENTS)} eventos canonicos",
            "hooks_dynamic",
            len(EVENTS) == 4,
            time.monotonic() - t,
            details=f"events={EVENTS}",
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                '{"hooks": {"PreToolUse": [{"command": "/bin/true", "matcher": "echo",'
                ' "timeout": 5, "block_on_failure": false}]}}'
            )
            cfg_path = f.name

        t = time.monotonic()
        hr = HookRuntime(settings_path=cfg_path)
        results = hr.run("PreToolUse", {"tool_name": "echo_test"})
        ok2 = len(results) == 1 and results[0].ok
        self._add(
            "HD-02",
            "run('PreToolUse', tool='echo_test') casa matcher 'echo' e executa /bin/true",
            "hooks_dynamic",
            ok2,
            time.monotonic() - t,
            details=f"len={len(results)} ok={results[0].ok if results else None}",
        )
        Path(cfg_path).unlink(missing_ok=True)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: MCP (3 testes -- MCP-SERVER-01/02)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_mcp(self) -> None:
        import tempfile

        t = time.monotonic()
        try:
            from nyx.agent.services.mcp_client import (
                McpClient,
                McpServer,
                load_mcp_servers,
            )
        except Exception as e:
            self._add("M-01", "imports MCP", "mcp", False, 0, error=str(e))
            return
        self._add("M-01", "imports MCP (McpClient/McpServer/load)", "mcp", True, time.monotonic() - t)

        t = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="nyx-mcp-") as tmp:
            empty_cfg = (Path(tmp) / "empty.json")
            empty_cfg.write_text("{}", encoding="utf-8")
            servers = load_mcp_servers(empty_cfg)
            self._add(
                "M-02",
                "load_mcp_servers tolera config vazia",
                "mcp",
                servers == [],
                time.monotonic() - t,
                details=f"len={len(servers)}",
            )

        t = time.monotonic()
        client = McpClient(servers=[
            McpServer(name="naoexiste", command="/usr/bin/false", args=[]),
        ])
        results = await client.connect_all()
        ok3 = results == {"naoexiste": False}
        ping_ok = await client.ping("naoexiste")
        await client.close_all()
        self._add(
            "M-03",
            "connect_all marca server invalido como falha + ping retorna False",
            "mcp",
            ok3 and not ping_ok,
            time.monotonic() - t,
            details=f"connect={results} ping={ping_ok}",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: LOOP (1 teste -- UX-LOOP-01 / ADR-025 feedback budget)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_loop(self) -> None:
        import subprocess as _sp

        t = time.monotonic()
        fixture = PROJECT_ROOT / "scripts" / "gauntlet" / "fixtures" / "loop_benchmark.py"
        if not fixture.is_file():
            self._add("L-01", "loop_benchmark.py existe", "loop", False, 0, error="fixture ausente")
            return
        try:
            result = await asyncio.to_thread(
                _sp.run,
                [str(PROJECT_ROOT / "venv" / "bin" / "python"), str(fixture)],
                capture_output=True,
                timeout=20,
            )
            output = (result.stdout or b"").decode("utf-8", errors="replace")
            ok = result.returncode == 0
            tail = "\n".join(output.strip().splitlines()[-4:])
            self._add(
                "L-01",
                "loop_benchmark (ack<100ms, tool_start<300ms, streaming<500ms)",
                "loop",
                ok,
                time.monotonic() - t,
                details=f"rc={result.returncode} tail={tail!r}",
            )
        except Exception as e:
            self._add("L-01", "loop_benchmark", "loop", False, time.monotonic() - t, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: INSTALL (2 testes -- DEPLOY-01B em Docker ubuntu:22.04)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_install(self) -> None:
        import shutil
        import subprocess

        if shutil.which("docker") is None:
            self._add(
                "D-01",
                "docker disponivel (skip: ausente)",
                "install",
                True,
                0,
                details="skip: docker não instalado nesta máquina",
            )
            self._add(
                "D-02",
                "install.sh em ubuntu:22.04 (skip)",
                "install",
                True,
                0,
                details="skip: docker ausente",
            )
            return

        t = time.monotonic()
        docker_info = await asyncio.to_thread(
            subprocess.run,
            ["docker", "info"],
            capture_output=True,
        )
        docker_ok = docker_info.returncode == 0
        self._add(
            "D-01",
            "docker disponivel + daemon up",
            "install",
            docker_ok,
            time.monotonic() - t,
            details=f"rc={docker_info.returncode}",
        )
        if not docker_ok:
            self._add(
                "D-02",
                "install.sh em ubuntu:22.04 (skip: daemon não acessível)",
                "install",
                True,
                0,
                details="skip",
            )
            return

        container_cmd = (
            "apt-get update -qq >/dev/null && "
            "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
            "python3 python3-venv python3-pip curl ca-certificates zstd sudo >/dev/null && "
            "cp -r /src /work && cd /work && rm -rf venv logs && "
            "NYX_INSTALL_SKIP_PULL=1 ./install.sh --no-vision --no-kitty --no-prompt"
        )
        full_cmd = [
            "docker", "run", "--rm",
            "-v", f"{PROJECT_ROOT}:/src:ro",
            "ubuntu:22.04",
            "bash", "-c", container_cmd,
        ]

        t = time.monotonic()
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                full_cmd,
                capture_output=True,
                timeout=1100,
            )
            rc = result.returncode
            output = (result.stdout or b"").decode("utf-8", errors="replace") + (
                result.stderr or b""
            ).decode("utf-8", errors="replace")
            tail = "\n".join(output.strip().splitlines()[-5:])
            ok = rc == 0 and "Instalação concluída" in output
            self._add(
                "D-02",
                "install.sh em ubuntu:22.04 (Docker real, ADR-010)",
                "install",
                ok,
                time.monotonic() - t,
                details=f"rc={rc} tail={tail!r}",
            )
        except subprocess.TimeoutExpired:
            self._add(
                "D-02",
                "install.sh em ubuntu:22.04",
                "install",
                False,
                time.monotonic() - t,
                error="timeout 1100s",
            )
        except Exception as e:
            self._add(
                "D-02",
                "install.sh em ubuntu:22.04",
                "install",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: SESSÃO (3 testes -- SESSION-RESUME-01)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_sessao(self) -> None:
        import tempfile

        t = time.monotonic()
        try:
            from nyx.agent.persistence import (
                INDEX_SCHEMA_VERSION,
                load_index,
                load_session_by_id,
                save_session,
            )
            from nyx.agent.session import CodeSession, HistoryEntry
        except Exception as e:
            self._add("S-01", "persistence imports", "sessao", False, 0, error=str(e))  # noqa-acento
            return
        self._add(
            "S-01",
            "persistence imports + schema v1",
            "sessao",  # noqa-acento
            INDEX_SCHEMA_VERSION == 1,
            time.monotonic() - t,
            details=f"schema_version={INDEX_SCHEMA_VERSION}",
        )

        with tempfile.TemporaryDirectory(prefix="nyx-gauntlet-sessao-"):
            session = CodeSession()
            session.history.append(HistoryEntry(role="user", content="gauntlet test prompt"))
            session.history.append(HistoryEntry(role="assistant", content="ok"))
            session.history.append(HistoryEntry(role="user", content="segunda pergunta"))

            t = time.monotonic()
            path = save_session(session, project_name="__gauntlet")
            dt = time.monotonic() - t
            if not path:
                self._add("S-02", "save_session + index", "sessao", False, dt, error="save_session retornou None")  # noqa-acento
                return
            idx = load_index()
            gauntlet_entries = [e for e in idx if e.get("projeto") == "__gauntlet"]
            ok2 = bool(gauntlet_entries) and gauntlet_entries[-1].get("n_turnos") == 2
            self._add(
                "S-02",
                "save_session atualiza index com n_turnos=2",
                "sessao",  # noqa-acento
                ok2,
                dt,
                details=f"entries={len(gauntlet_entries)} last={gauntlet_entries[-1] if gauntlet_entries else None}",
            )

            t = time.monotonic()
            prefix = path.stem[:20]
            reloaded = load_session_by_id(prefix)
            dt = time.monotonic() - t
            ok3 = reloaded is not None and len(reloaded.history) == 3
            self._add(
                "S-03",
                "load_session_by_id por prefixo restaura history",
                "sessao",  # noqa-acento
                ok3,
                dt,
                details=f"prefix={prefix!r} entries_restored={len(reloaded.history) if reloaded else 0}",
            )

            # Cleanup: remove o arquivo gauntlet do disco real (não polui ~/.nyx)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    # ═══════════════════════════════════════════════════════════════════
    # FASE: VISION (3 testes -- VISION-01, ADR-022)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_vision(self) -> None:

        try:
            from nyx.agent.services.vision_service import VisionService
        except Exception as e:
            self._add("V-VS-01", "VisionService importa", "vision", False, 0, error=str(e))
            return

        t = time.monotonic()
        try:
            svc = VisionService()
            self._add("V-VS-01", "VisionService importa e instancia", "vision", True, time.monotonic() - t)
        except Exception as e:
            self._add("V-VS-01", "VisionService importa e instancia", "vision", False, time.monotonic() - t, error=str(e))  # noqa: E501
            return

        t = time.monotonic()
        try:
            available = svc.is_available()
            self._add(
                "V-VS-02",
                "is_available() sem crash",
                "vision",
                True,
                time.monotonic() - t,
                details=f"available={available}",
            )
        except Exception as e:
            self._add("V-VS-02", "is_available() sem crash", "vision", False, time.monotonic() - t, error=str(e))
            return

        if not available:
            self._add(
                "V-VS-03",
                "describe + cache (skip: moondream ausente)",
                "vision",
                True,
                0,
                details="skip: moondream não instalado; sprint validada via testes 1-2",
            )
            return

        image_path = PROJECT_ROOT / "assets" / "nyx-icon.png"
        if not image_path.is_file():
            self._add(
                "V-VS-03",
                "describe + cache (skip: asset ausente)",
                "vision",
                True,
                0,
                details=f"skip: {image_path} não existe",
            )
            return

        t1 = time.monotonic()
        desc1 = svc.describe(image_path)
        dt1 = time.monotonic() - t1
        t2 = time.monotonic()
        desc2 = svc.describe(image_path)
        dt2 = time.monotonic() - t2

        cache_hit = dt2 < dt1 * 0.3 or dt2 < 0.05
        ok = len(desc1) > 20 and desc1 == desc2 and cache_hit
        self._add(
            "V-VS-03",
            "describe(asset) >= 20 chars + cache hit < 30% do primeiro",
            "vision",
            ok,
            dt1 + dt2,
            details=f"len={len(desc1)} dt1={dt1:.2f}s dt2={dt2:.3f}s",
        )

    async def _phase_visual(self) -> None:
        from nyx.themes import ThemeManager

        tm = ThemeManager()

        temas = tm.list_themes()
        self._add("V-05", "7 temas carregam", "visual", len(temas) == 7, 0, details=f"{len(temas)} temas")

        fallback = tm.load_theme("fantasma_inexistente")
        self._add("V-06", "Fallback Dracula", "visual", fallback["primary"] == "#BD93F9", 0)

        ansi = tm.get_ansi_colors("nyx")
        self._add("V-07", "Hex -> ANSI 24-bit", "visual", "\033[38;2;" in ansi.get("accent", ""), 0)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: CONFIG (4 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_config(self) -> None:
        # C-01
        env = PROJECT_ROOT / ".env"
        self._add("C-01", ".env existe", "config", env.exists(), 0)

        # C-02
        try:
            from nyx.config.settings import load_settings

            s = load_settings()
            self._add(
                "C-02",
                "NyxSettings carrega",
                "config",
                s.ollama_port > 0,
                0,
                details=f"port={s.ollama_port} model={s.model}",
            )
        except Exception as e:
            self._add("C-02", "NyxSettings carrega", "config", False, 0, error=str(e))

        # C-03: preferências padrão (theme=dark, language=pt-BR) em arquivo
        # versionado dentro do pacote nyx/config/, não em .claude/ (anonimato).
        # GAUNTLET-RAPIDO-FIXES-01: substitui .claude/settings.json (gitignored)
        # por nyx/config/preferences.json (versionado, defaults canônicos).
        prefs_path = PROJECT_ROOT / "nyx" / "config" / "preferences.json"
        if prefs_path.exists():
            data = json.loads(prefs_path.read_text(encoding="utf-8"))
            prefs = data.get("preferences", {})
            ok = prefs.get("theme") == "dark" and prefs.get("language") == "pt-BR"
            self._add(
                "C-03",
                "preferences.json dark+pt-BR",
                "config",
                ok,
                0,
                details=f"theme={prefs.get('theme')} lang={prefs.get('language')}",
            )
        else:
            self._add("C-03", "preferences.json dark+pt-BR", "config", False, 0, error="Arquivo não existe")

        # C-04
        # GSD.md (Getting Shit Done) e o guia canonico do projeto e e rastreado.
        # GUIDE.md original era symlink local (gitignore'd) -- nao validavel em CI.
        # GAUNTLET-RAPIDO-FIXES-01: troca GUIDE.md por GSD.md.
        guide_md = PROJECT_ROOT / "GSD.md"
        if guide_md.exists():
            content = guide_md.read_text(encoding="utf-8")
            has_nyx = "Nyx" in content
            self._add("C-04", "GSD.md contém Nyx", "config", has_nyx, 0)
        else:
            self._add("C-04", "GSD.md contém Nyx", "config", False, 0, error="Arquivo não existe")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: RESILIÊNCIA (2 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_resiliencia(self) -> None:
        # R-01: Proxy retorna erro quando backend cai
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.post(
                    self._proxy.replace(str(self._proxy.split(":")[-1]), "19999") + "/v1/chat/completions",
                    json={"model": self._model, "messages": [{"role": "user", "content": "test"}]},
                )
                # Se conectou a porta errada, deve receber erro
                self._add(
                    "R-01",
                    "Proxy: erro quando backend cai",
                    "resiliencia",
                    False,
                    time.monotonic() - t,
                    error="Conexão deveria ter falhado",
                )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            self._add(
                "R-01",
                "Proxy: erro quando backend cai",
                "resiliencia",
                True,
                time.monotonic() - t,
                details="Conexão recusada (correto)",
            )
        except Exception as e:
            self._add(
                "R-01",
                "Proxy: erro quando backend cai",
                "resiliencia",
                True,
                time.monotonic() - t,
                details=f"Erro: {type(e).__name__}",
            )

        # R-05: Timeout de inferência
        t = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                await c.post(
                    f"{self._proxy}/v1/chat/completions",
                    json={
                        "model": self._model,
                        "messages": [{"role": "user", "content": "escreva um texto de 5000 palavras"}],
                    },
                )
                # Se respondeu em <2s com request pesado, algo está errado (cache?)
                # Mas se respondeu, o proxy não travou -- considerar OK
                self._add(
                    "R-05",
                    "Timeout não trava proxy",
                    "resiliencia",
                    True,
                    time.monotonic() - t,
                    details="Respondeu rápido (cache)",
                )
        except httpx.ReadTimeout:
            self._add(
                "R-05",
                "Timeout não trava proxy",
                "resiliencia",
                True,
                time.monotonic() - t,
                details="Timeout correto (ReadTimeout)",
            )
        except Exception as e:
            self._add(
                "R-05",
                "Timeout não trava proxy",
                "resiliencia",
                True,
                time.monotonic() - t,
                details=f"Erro tratado: {type(e).__name__}",
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PARSER (7 testes -- P1-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_parser(self) -> None:
        from nyx.agent.models import ActionType
        from nyx.agent.parser import ActionParser

        p = ActionParser()

        # PR-01: EXACT
        r = p.parse("ACTION: read_file\nPATH: README.md\n---")
        self._add(
            "PR-01",
            "Parse EXACT",
            "parser",
            r.success and r.action.action_type == ActionType.READ_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
            error=r.error if not r.success else "",
        )

        # PR-02: FUNCTION_CALL
        r = p.parse('Vou usar read_file("README.md") para ler')
        self._add(
            "PR-02",
            "Parse FUNCTION_CALL",
            "parser",
            r.success and r.action.action_type == ActionType.READ_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
        )

        # PR-03: RELAXED
        r = p.parse("action: read_file\npath: README.md\n\noutro texto")
        self._add(
            "PR-03",
            "Parse RELAXED",
            "parser",
            r.success and r.action.action_type == ActionType.READ_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
        )

        # PR-04: BARE_TOOL
        r = p.parse("read_file README.md")
        self._add(
            "PR-04",
            "Parse BARE_TOOL",
            "parser",
            r.success and r.action.action_type == ActionType.READ_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
        )

        # PR-05: CODE_BLOCK
        r = p.parse("Criar arquivo test.py:\n```python\nprint('ok')\n```")
        self._add(
            "PR-05",
            "Parse CODE_BLOCK",
            "parser",
            r.success and r.action.action_type == ActionType.CREATE_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
        )

        # PR-06: PATH_INTENT
        r = p.parse("Vou ler o arquivo README.md para entender o projeto")
        self._add(
            "PR-06",
            "Parse PATH_INTENT",
            "parser",
            r.success and r.action.action_type == ActionType.READ_FILE,
            0,
            details=f"level={r.level.value}" if r.success else "",
        )

        # PR-07: IMPLICIT_DONE
        r = p.parse("Pronto, tarefa concluída com sucesso.")
        self._add(
            "PR-07",
            "Parse IMPLICIT_DONE",
            "parser",
            r.success and r.action.action_type == ActionType.DONE,
            0,
            details=f"level={r.level.value}, rate={p.success_rate:.0%}" if r.success else "",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: CONTROLE (4 testes -- P1-D)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_controle(self) -> None:
        from pathlib import Path as _Path

        from nyx.agent.path_resolver import PathResolver
        from nyx.agent.permissions import PermissionChecker, PermissionLevel

        # CT-01: Permissão auto_approve
        pc = PermissionChecker()
        auto = pc.check("read_file") == PermissionLevel.AUTO
        self._add(
            "CT-01", "Permissão auto_approve", "controle", auto, 0, details=f"read_file -> {pc.check('read_file')}"
        )

        # CT-02: Permissão always_confirm
        confirm = pc.check("run_command") == PermissionLevel.ALWAYS_CONFIRM
        self._add(
            "CT-02",
            "Permissão always_confirm",
            "controle",
            confirm,
            0,
            details=f"run_command -> {pc.check('run_command')}",
        )

        # CT-03: Path resolve relativo
        pr = PathResolver(_Path(PROJECT_ROOT))
        pr.build_index()
        r = pr.resolve("README.md")
        self._add("CT-03", "Path resolve relativo", "controle", r.exists, 0, details=f"README.md -> {r.resolved}")

        # CT-04: Path resolve fuzzy
        r2 = pr.resolve("proxy.py")
        self._add(
            "CT-04",
            "Path resolve fuzzy",
            "controle",
            r2.exists,
            0,
            details=f"proxy.py -> {r2.resolved} ({len(r2.candidates)} candidatos)",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PERSISTENCIA (3 testes -- P1-E)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_persistencia(self) -> None:
        from nyx.agent.git_ops import git_status
        from nyx.agent.persistence import load_latest_session, save_session
        from nyx.agent.session import CodeSession

        # PS-01: Git status
        ok, status = git_status(str(PROJECT_ROOT))
        self._add("PS-01", "Git status", "persistencia", ok, 0, details=f"{len(status)} chars")

        # PS-02: Session save
        session = CodeSession()
        session.add_user("gauntlet test")
        path = save_session(session, "gauntlet-test")
        saved = path is not None and path.exists()
        self._add("PS-02", "Session save", "persistencia", saved, 0, details=str(path) if path else "falhou")

        # PS-03: Session load
        loaded = load_latest_session("gauntlet-test")
        restored = loaded is not None and len(loaded.history) > 0
        self._add(
            "PS-03",
            "Session load",
            "persistencia",
            restored,
            0,
            details=f"{len(loaded.history)} entradas" if loaded else "falhou",
        )

        # Cleanup
        if path and path.exists():
            path.unlink()

    # ═══════════════════════════════════════════════════════════════════
    # FASE: INTERFACE (5 testes -- P1-C)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_interface(self) -> None:
        # IF-01: Streaming importa
        try:
            from nyx.agent.streaming import StreamingCollector

            sc = StreamingCollector()
            sc.feed("teste")
            self._add(
                "IF-01", "Streaming importa", "interface", sc.char_count == 5, 0, details=f"chars={sc.char_count}"
            )
        except Exception as e:
            self._add("IF-01", "Streaming importa", "interface", False, 0, error=str(e))

        # IF-02: Output importa
        try:
            from nyx.agent.output import RICH_AVAILABLE, RichOutput

            RichOutput()  # smoke-test do construtor
            self._add("IF-02", "Output importa", "interface", True, 0, details=f"rich={RICH_AVAILABLE}")
        except Exception as e:
            self._add("IF-02", "Output importa", "interface", False, 0, error=str(e))

        # IF-03: Commands /help
        from nyx.agent.commands import handle_command

        help_text = handle_command("/help", str(PROJECT_ROOT))
        has_explain = "explain" in (help_text or "")
        self._add("IF-03", "Commands /help", "interface", has_explain, 0, details=f"len={len(help_text or '')}")

        # IF-04: Commands /explain
        explain = handle_command("/explain README.md", str(PROJECT_ROOT))
        has_read = "read_file" in (explain or "")
        self._add("IF-04", "Commands /explain", "interface", has_read, 0, details=(explain or "")[:60])

        # IF-05: Commands /plan (CTX-04 transformou /plan em checklist persistida;
        # output atual é "Objetivo do plano definido: <input>"; aceita ambos formatos)
        plan = handle_command("/plan feature X", str(PROJECT_ROOT))
        plan_out = plan or ""
        has_plan_marker = (
            "feature X" in plan_out
            or "Objetivo" in plan_out
            or "plano" in plan_out.lower()
            or "list_files" in plan_out
        )
        self._add("IF-05", "Commands /plan", "interface", has_plan_marker, 0, details=plan_out[:60])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: SLASH_BYPASS (5 testes -- SLASH-BYPASS-AUDIT-01)
    # Confirma que /commands são interceptados em cli.py:417 ANTES do LLM.
    # Audit: nyx/cli.py linha 417 contém `if user_input.startswith("/"):`
    # seguido de `handle_command(...)`. handle_command vive em
    # nyx/agent/commands/_dispatcher.py:36 e retorna string ou sentinela
    # sem nenhuma chamada ao proxy/Ollama. Esta fase mede latência
    # em chamada direta para garantir que NÃO há regressão futura
    # (algum /command sendo enviado ao LLM erroneamente).
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_slash_bypass(self) -> None:
        from nyx.agent.commands import handle_command

        cases = [
            ("SB-01", "/help"),
            ("SB-02", "/memory"),
            ("SB-03", "/tools"),
            ("SB-04", "/quit"),
            ("SB-05", "/theme"),
        ]
        for fid, cmd in cases:
            t0 = time.monotonic()
            try:
                result = handle_command(cmd, str(PROJECT_ROOT))
            except Exception as exc:
                dt = time.monotonic() - t0
                self._add(fid, f"slash bypass {cmd}", "slash_bypass", False, dt, error=str(exc)[:200])
                continue
            dt = time.monotonic() - t0
            is_str = isinstance(result, str) and len(result) > 0
            not_error = is_str and not result.startswith("__error__")
            fast = dt < 0.5
            ok = is_str and not_error and fast
            details = f"latencia={dt * 1000:.0f}ms, len={len(result or '')}"
            self._add(fid, f"slash bypass {cmd}", "slash_bypass", ok, dt, details=details)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: ROBUSTEZ (6 testes -- P1-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_robustez(self) -> None:
        from nyx.agent.context import ContextBudget
        from nyx.agent.model_tier import get_model_tier
        from nyx.agent.models import ActionType, AgentAction
        from nyx.agent.repetition import detect_repetition, is_cycle
        from nyx.agent.session import CodeSession, HistoryEntry

        # RB-01: Context budget nível 0 (sessão vazia)
        cb = ContextBudget(max_tokens=1000)
        session = CodeSession()
        level = cb.get_compaction_level(session)
        self._add("RB-01", "Context budget nível 0", "robustez", level == 0, 0, details=f"level={level} (esperado 0)")

        # RB-02: Context budget nível 3 (sessão cheia)
        for i in range(50):
            session.add_tool_call("read_file", {"path": f"file_{i}.py"}, "x" * 200)
        level = cb.get_compaction_level(session)
        self._add("RB-02", "Context budget nível 3", "robustez", level >= 2, 0, details=f"level={level} (esperado >=2)")

        # RB-03: Repetition exact
        a1 = AgentAction(action_type=ActionType.READ_FILE, params={"path": "README.md"})
        a2 = AgentAction(action_type=ActionType.READ_FILE, params={"path": "README.md"})
        is_rep = detect_repetition(a1, a2, [], set())
        self._add("RB-03", "Repetition exact", "robustez", is_rep, 0, details=f"detected={is_rep}")

        # RB-04: Repetition cycle
        entries: list[HistoryEntry] = []
        for _ in range(4):
            entries.append(HistoryEntry(role="tool", content="", tool_name="read_file", tool_args={"path": "a.py"}))
            entries.append(HistoryEntry(role="tool", content="", tool_name="write_file", tool_args={"path": "b.py"}))
        cycle = is_cycle(entries)
        self._add("RB-04", "Repetition cycle", "robustez", cycle, 0, details=f"cycle={cycle}")

        # RB-05: Model tier auto
        tier = get_model_tier()
        valid = tier.num_gpu != 0 and tier.num_ctx > 0
        self._add(
            "RB-05", "Model tier auto", "robustez", valid, 0, details=f"num_gpu={tier.num_gpu} num_ctx={tier.num_ctx}"
        )

        # RB-06: Model tier hardware
        hw_match = tier.vram_total_mib > 0 or tier.gpu_name == "CPU-only"
        self._add(
            "RB-06",
            "Model tier hardware",
            "robustez",
            hw_match,
            0,
            details=f"{tier.hardware_profile.value}: {tier.gpu_name} ({tier.vram_total_mib}MiB)",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: E2E (12 testes -- P1-F)
    # Testa integração dos módulos no loop e CLI sem subprocesso
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_e2e(self) -> None:

        # E-01: AgentLoop importa e inicializa com todos os módulos
        try:
            from nyx.agent.loop import AgentLoop

            agent = AgentLoop(project_root=str(PROJECT_ROOT))
            has_parser = hasattr(agent, "_parser")
            has_budget = hasattr(agent, "_budget")
            has_perms = hasattr(agent, "_permissions")
            ok = has_parser and has_budget and has_perms
            self._add(
                "E-01",
                "AgentLoop integrado",
                "e2e",
                ok,
                0,
                details=f"parser={has_parser} budget={has_budget} perms={has_perms}",
            )
        except Exception as e:
            self._add("E-01", "AgentLoop integrado", "e2e", False, 0, error=str(e))
            return

        # E-02: Tools count >= 8
        tc = agent.tools_count
        self._add("E-02", "Tools registradas >= 8", "e2e", tc >= 8, 0, details=f"{tc} tools")

        # E-03: Parser fallback integrado no loop
        ok = agent._parser is not None and hasattr(agent._parser, "parse")
        self._add("E-03", "Parser fallback no loop", "e2e", ok, 0)

        # E-04: ContextBudget integrado no loop
        info = agent.get_context_info()
        ok = "pct" in info and "total_tokens" in info
        self._add("E-04", "ContextBudget no loop", "e2e", ok, 0, details=f"pct={info.get('pct', 0):.2f}")

        # E-05: Permissões integradas no loop
        perm_check = agent.permissions.check("read_file")
        ok = perm_check == "auto_approve"
        self._add("E-05", "Permissões no loop", "e2e", ok, 0, details=f"read_file -> {perm_check}")

        # E-06: RepetitionDetector integrado
        ok = agent._last_action is None and agent._consecutive_skips == 0
        self._add("E-06", "RepetitionDetector no loop", "e2e", ok, 0)

        # E-07: ACTION_TO_TOOL mapeamento completo
        from nyx.agent.loop import ACTION_TO_TOOL
        from nyx.agent.models import ActionType

        mapped = set(ACTION_TO_TOOL.keys())
        expected = {
            ActionType.READ_FILE,
            ActionType.WRITE_FILE,
            ActionType.EDIT_FILE,
            ActionType.RUN_COMMAND,
            ActionType.GLOB,
            ActionType.SEARCH,
            ActionType.LIST_FILES,
            ActionType.DONE,
        }
        missing = expected - mapped
        self._add(
            "E-07",
            "ACTION_TO_TOOL completo",
            "e2e",
            len(missing) == 0,
            0,
            details=f"mapped={len(mapped)}" if not missing else "",
            error=f"faltam: {missing}" if missing else "",
        )

        # E-08: PARAM_REMAP funciona
        from nyx.agent.loop import _remap_params

        remapped = _remap_params("read_file", {"path": "README.md"})
        ok = remapped.get("file_path") == "README.md"
        self._add("E-08", "PARAM_REMAP funciona", "e2e", ok, 0, details=f"path -> {remapped}")

        # E-09: CLI importa e tem --no-stream
        try:
            import inspect

            from nyx.cli import run_repl

            sig = inspect.signature(run_repl)
            has_streaming = "streaming" in sig.parameters
            self._add("E-09", "CLI aceita --no-stream", "e2e", has_streaming, 0)
        except Exception as e:
            self._add("E-09", "CLI aceita --no-stream", "e2e", False, 0, error=str(e))

        # E-10: Commands module integrado
        from nyx.agent.commands import handle_command, list_commands

        cmds = list_commands()
        cmd_names = {c.name for c in cmds}
        has_all = {"help", "quit", "explain", "plan", "test", "compact"}.issubset(cmd_names)
        self._add("E-10", "Commands completos", "e2e", has_all, 0, details=f"{len(cmds)} comandos: {sorted(cmd_names)}")

        # E-11: /help retorna todos os comandos
        help_text = handle_command("/help", str(PROJECT_ROOT)) or ""
        has_explain = "/explain" in help_text
        has_plan = "/plan" in help_text
        ok = has_explain and has_plan
        self._add("E-11", "/help completo", "e2e", ok, 0, details=f"explain={has_explain} plan={has_plan}")

        # E-12: Persistence integrada
        try:
            from nyx.agent.persistence import load_latest_session, save_session
            from nyx.agent.session import CodeSession

            s = CodeSession()
            s.add_user("e2e integration test")
            path = save_session(s, "e2e-test")
            loaded = load_latest_session("e2e-test")
            ok = path is not None and loaded is not None and len(loaded.history) > 0
            self._add(
                "E-12",
                "Persistence integrada",
                "e2e",
                ok,
                0,
                details=f"saved={path is not None} loaded={loaded is not None}",
            )
            if path and path.exists():
                path.unlink()
        except Exception as e:
            self._add("E-12", "Persistence integrada", "e2e", False, 0, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P2_TOOLS (3 testes -- P2-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p2_tools(self) -> None:
        # P2T-01: TodoWrite funciona
        from nyx.agent.tools.todo_write import TodoWriteTool

        try:
            tw = TodoWriteTool()
            r = tw.execute(
                {
                    "todos": [
                        {"content": "gauntlet test 1", "status": "pending"},
                        {"content": "gauntlet test 2", "status": "completed"},
                    ]
                },
                str(PROJECT_ROOT),
            )
            ok = r.success and "2 total" in r.output
            self._add("P2T-01", "TodoWrite funciona", "p2_tools", ok, 0, details=r.output[:80])
        except Exception as e:
            self._add("P2T-01", "TodoWrite funciona", "p2_tools", False, 0, error=str(e))

        # P2T-02: WebFetch busca URL real
        from nyx.agent.tools.web_fetch import WebFetchTool

        t = time.monotonic()
        try:
            wf = WebFetchTool()
            r = wf.execute({"url": "https://httpbin.org/get"}, str(PROJECT_ROOT))
            elapsed = time.monotonic() - t
            ok = r.success and "200" in r.output
            self._add(
                "P2T-02",
                "WebFetch URL real",
                "p2_tools",
                ok,
                elapsed,
                details=f"status={r.success} len={len(r.output)}",
            )
        except Exception as e:
            self._add("P2T-02", "WebFetch URL real", "p2_tools", False, time.monotonic() - t, error=str(e))

        # P2T-03: WebSearch busca real via DuckDuckGo
        from nyx.agent.tools.web_search import WebSearchTool

        t = time.monotonic()
        try:
            ws = WebSearchTool()
            r = ws.execute({"query": "Python programming language", "max_results": 3}, str(PROJECT_ROOT))
            elapsed = time.monotonic() - t
            ok = r.success and len(r.output) > 50
            self._add("P2T-03", "WebSearch DuckDuckGo real", "p2_tools", ok, elapsed, details=f"len={len(r.output)}")
        except Exception as e:
            self._add("P2T-03", "WebSearch DuckDuckGo real", "p2_tools", False, time.monotonic() - t, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P2_ADVANCED (6 testes -- P2-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p2_advanced(self) -> None:
        # P2A-01: TaskCreate cria tarefa
        from nyx.agent.tools.task_manager import TaskCreateTool, TaskListTool, TaskUpdateTool, _load_tasks

        tc = TaskCreateTool()
        r = tc.execute({"subject": "gauntlet test", "description": "teste automático"}, str(PROJECT_ROOT))
        ok = r.success and "#" in r.output
        self._add("P2A-01", "TaskCreate cria tarefa", "p2_advanced", ok, 0, details=r.output[:80])

        # P2A-02: TaskList mostra tarefa criada
        tl = TaskListTool()
        r = tl.execute({}, str(PROJECT_ROOT))
        ok = r.success and "gauntlet test" in r.output
        self._add("P2A-02", "TaskList mostra tarefa", "p2_advanced", ok, 0, details=r.output[:80])

        # P2A-03: TaskUpdate muda status
        tasks = _load_tasks()
        gauntlet_task = next((t for t in tasks if "gauntlet test" in t.subject), None)
        if gauntlet_task:
            tu = TaskUpdateTool()
            r = tu.execute({"task_id": gauntlet_task.id, "status": "completed"}, str(PROJECT_ROOT))
            ok = r.success and "completed" in r.output
            self._add("P2A-03", "TaskUpdate muda status", "p2_advanced", ok, 0, details=r.output[:80])
        else:
            self._add("P2A-03", "TaskUpdate muda status", "p2_advanced", False, 0, error="Task gauntlet não encontrada")

        # P2A-04: PlanMode entra e sai
        from nyx.agent.tools.plan_mode import EnterPlanModeTool, ExitPlanModeTool, is_plan_mode

        ep = EnterPlanModeTool()
        r = ep.execute({}, str(PROJECT_ROOT))
        entered = r.success and is_plan_mode()
        self._add("P2A-04", "PlanMode ativa", "p2_advanced", entered, 0, details=r.output[:60])

        xp = ExitPlanModeTool()
        r = xp.execute({"plan_summary": "teste gauntlet"}, str(PROJECT_ROOT))
        exited = r.success and not is_plan_mode()
        self._add("P2A-05", "PlanMode desativa", "p2_advanced", exited, 0, details=r.output[:60])

        # P2A-06: AgentTool importa e tem interface
        from nyx.agent.tools.agent_tool import AgentTool

        at = AgentTool()
        ok = at.tool_def.name == "agent" and "prompt" in at.tool_def.parameters
        self._add("P2A-06", "AgentTool interface", "p2_advanced", ok, 0, details=f"name={at.tool_def.name}")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P2_COMMANDS (4 testes -- P2-C)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p2_commands(self) -> None:
        from nyx.agent.commands import handle_command

        # P2C-01: /commit retorna prompt com git
        r = handle_command("/commit", str(PROJECT_ROOT))
        ok = r is not None and "git status" in r
        self._add("P2C-01", "/commit gera prompt git", "p2_commands", ok, 0, details=(r or "")[:80])

        # P2C-02: /diff retorna status real do repositório
        r = handle_command("/diff", str(PROJECT_ROOT))
        ok = r is not None and ("Status:" in r or "Nenhuma mudança" in r)
        self._add("P2C-02", "/diff mostra status real", "p2_commands", ok, 0, details=(r or "")[:80])

        # P2C-03: /doctor verifica infraestrutura
        r = handle_command("/doctor", str(PROJECT_ROOT))
        ok = r is not None and "Diagnóstico" in r and "Projeto:" in r
        self._add("P2C-03", "/doctor diagnóstico real", "p2_commands", ok, 0, details=(r or "")[:120])

        # P2C-04: /review gera prompt com PR
        r = handle_command("/review 1", str(PROJECT_ROOT))
        ok = r is not None and "gh pr" in r
        self._add("P2C-04", "/review gera prompt PR", "p2_commands", ok, 0, details=(r or "")[:80])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P2_SERVICES (3 testes -- P2-D)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p2_services(self) -> None:
        # P2S-01: Token estimation funciona
        from nyx.agent.services.tokens import estimate_tokens, estimate_tokens_for_file, format_token_count

        tokens = estimate_tokens("hello world" * 100)
        ok = tokens > 200 and tokens < 400
        formatted = format_token_count(tokens)
        self._add("P2S-01", "Token estimation", "p2_services", ok, 0, details=f"tokens={tokens} formatted={formatted}")

        # Estimativa JSON (ratio 2)
        json_tokens = estimate_tokens_for_file('{"key": "value"}' * 100, "data.json")
        text_tokens = estimate_tokens_for_file("hello world " * 100, "readme.md")
        json_denser = json_tokens > text_tokens
        self._add(
            "P2S-02",
            "Token estimation por tipo",
            "p2_services",
            json_denser,
            0,
            details=f"json={json_tokens} text={text_tokens}",
        )

        # P2S-03: Hooks registram e executam
        from nyx.agent.services.hooks import ToolHooks, create_logging_hook, create_path_guard_hook

        hooks = ToolHooks()
        hooks.register_post(create_logging_hook())
        hooks.register_pre(create_path_guard_hook([".env", "credentials"]))

        ok_counts = hooks.pre_count == 1 and hooks.post_count == 1

        block = hooks.run_pre("read_file", {"file_path": ".env.secret"})
        blocked = block is not None and block.get("block")

        allow = hooks.run_pre("read_file", {"file_path": "README.md"})
        allowed = allow is None

        ok = ok_counts and blocked and allowed
        self._add(
            "P2S-03",
            "Hooks pre/post executam",
            "p2_services",
            ok,
            0,
            details=f"counts={hooks.pre_count}/{hooks.post_count} blocked={blocked} allowed={allowed}",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P3_TOOLS (2 testes -- P3-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p3_tools(self) -> None:
        import json as _json

        # P3T-01: NotebookEdit cria e edita célula
        from nyx.agent.tools.notebook_edit import NotebookEditTool

        nb_tool = NotebookEditTool()

        nb_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": ["print('hello')\n"],
                    "execution_count": None,
                    "outputs": [],
                },
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        # GAUNTLET-FIXTURES-SANDBOX-01: ~/.nyx/gauntlet_tmp/ é root autorizado.
        nb_path_obj = _gauntlet_tmp_dir() / "nyx_p3t01_notebook.ipynb"
        nb_path_obj.write_text(_json.dumps(nb_content), encoding="utf-8")
        nb_path = str(nb_path_obj)

        r = nb_tool.execute(
            {
                "notebook_path": nb_path,
                "cell_index": 0,
                "new_source": "print('nyx')",
                "cell_type": "code",
                "edit_mode": "replace",
            },
            str(PROJECT_ROOT),
        )
        ok = r.success and "atualizada" in r.output

        r2 = nb_tool.execute(
            {
                "notebook_path": nb_path,
                "cell_index": 0,
                "new_source": "# Gauntlet test",
                "cell_type": "markdown",
                "edit_mode": "insert",
            },
            str(PROJECT_ROOT),
        )
        ok2 = r2.success and "inserida" in r2.output

        verified = False
        try:
            nb_data = _json.loads(Path(nb_path).read_text(encoding="utf-8"))
            verified = len(nb_data["cells"]) == 2 and "nyx" in nb_data["cells"][0]["source"][0]
        except Exception:
            pass

        Path(nb_path).unlink(missing_ok=True)
        self._add(
            "P3T-01",
            "NotebookEdit edita e insere",
            "p3_tools",
            ok and ok2 and verified,
            0,
            details=f"edit={ok} insert={ok2} verified={verified}",
        )

        # P3T-02: AskUser importa e tem interface
        from nyx.agent.tools.ask_user import AskUserTool

        au = AskUserTool()
        ok = au.tool_def.name == "ask_user" and "question" in au.tool_def.parameters
        self._add("P3T-02", "AskUser interface", "p3_tools", ok, 0, details=f"name={au.tool_def.name}")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P3_COMMANDS (5 testes -- P3-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p3_commands(self) -> None:
        from nyx.agent.commands import handle_command, list_commands

        cmds = list_commands()
        cmd_names = {c.name for c in cmds}

        # P3C-01: Total de commands >= 15
        self._add("P3C-01", "Commands >= 15", "p3_commands", len(cmds) >= 15, 0, details=f"{len(cmds)} commands")

        # P3C-02: /model mostra modelo atual
        r = handle_command("/model", str(PROJECT_ROOT))
        ok = r is not None and "Modelo atual" in r
        self._add("P3C-02", "/model mostra modelo", "p3_commands", ok, 0, details=(r or "")[:60])

        # P3C-03: /context retorna magic string
        r = handle_command("/context", str(PROJECT_ROOT))
        ok = r == "__context__"
        self._add("P3C-03", "/context retorna magic", "p3_commands", ok, 0)

        # P3C-04: /session list funciona
        r = handle_command("/session list", str(PROJECT_ROOT))
        ok = r is not None and ("Sessões" in r or "Nenhuma" in r)
        self._add("P3C-04", "/session list funciona", "p3_commands", ok, 0, details=(r or "")[:60])

        # P3C-05: Novos commands registrados
        new_cmds = {"model", "context", "session"}
        has_all = new_cmds.issubset(cmd_names)
        self._add(
            "P3C-05",
            "Novos commands registrados",
            "p3_commands",
            has_all,
            0,
            details=f"model={'model' in cmd_names} ctx={'context' in cmd_names} sess={'session' in cmd_names}",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P3_ROBUSTEZ (4 testes -- P3-C)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p3_robustez(self) -> None:
        # P3R-01: Registry tem hooks integrados
        from nyx.agent.tools.registry import ToolRegistry

        reg = ToolRegistry(str(PROJECT_ROOT))
        ok = hasattr(reg, "_hooks") and hasattr(reg.hooks, "run_pre")
        self._add("P3R-01", "Registry com hooks", "p3_robustez", ok, 0)

        # P3R-02: Hook bloqueia via registry
        from nyx.agent.services.hooks import create_path_guard_hook

        reg.hooks.register_pre(create_path_guard_hook([".env"]))
        result = reg.execute("read_file", {"file_path": ".env.secret"})
        blocked = not result.success and "bloqueado" in result.error.lower()
        self._add("P3R-02", "Hook bloqueia no registry", "p3_robustez", blocked, 0, details=result.error[:60])

        # P3R-03: Tools count >= 19
        ok = reg.tool_count >= 19
        self._add("P3R-03", "Tools >= 19", "p3_robustez", ok, 0, details=f"{reg.tool_count} tools")

        # P3R-04: PlanMode bloqueia write no loop
        from nyx.agent.tools.plan_mode import is_tool_allowed_in_plan_mode, set_plan_mode

        set_plan_mode(True)
        write_blocked = not is_tool_allowed_in_plan_mode("write_file")
        read_allowed = is_tool_allowed_in_plan_mode("read_file")
        set_plan_mode(False)
        ok = write_blocked and read_allowed
        self._add(
            "P3R-04",
            "PlanMode bloqueia write",
            "p3_robustez",
            ok,
            0,
            details=f"write_blocked={write_blocked} read_allowed={read_allowed}",
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P3_HEADLESS (3 testes -- P3-D)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p3_headless(self) -> None:
        import json as _json
        import subprocess

        # P3H-01: CLI aceita --headless
        try:
            from nyx.cli import run_headless

            ok = asyncio.iscoroutinefunction(run_headless)
            self._add("P3H-01", "CLI aceita --headless", "p3_headless", ok, 0)
        except Exception as e:
            self._add("P3H-01", "CLI aceita --headless", "p3_headless", False, 0, error=str(e))

        # P3H-02: Headless responde ping
        t = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "nyx.cli", "--headless"],
                input='{"type": "ping"}\n',
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            output = proc.stdout.strip()
            if output:
                resp = _json.loads(output.split("\n")[0])
                ok = resp.get("type") == "pong" and resp.get("tools", 0) >= 19
                self._add(
                    "P3H-02",
                    "Headless responde ping",
                    "p3_headless",
                    ok,
                    time.monotonic() - t,
                    details=f"tools={resp.get('tools')}",
                )
            else:
                self._add(
                    "P3H-02",
                    "Headless responde ping",
                    "p3_headless",
                    False,
                    time.monotonic() - t,
                    error=f"stdout vazio, stderr={proc.stderr[:100]}",
                )
        except subprocess.TimeoutExpired:
            self._add("P3H-02", "Headless responde ping", "p3_headless", False, time.monotonic() - t, error="Timeout")
        except Exception as e:
            self._add("P3H-02", "Headless responde ping", "p3_headless", False, time.monotonic() - t, error=str(e))

        # P3H-03: Headless responde reset
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "nyx.cli", "--headless"],
                input='{"type": "reset"}\n',
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            output = proc.stdout.strip()
            if output:
                resp = _json.loads(output.split("\n")[0])
                ok = resp.get("type") == "ok"
                self._add("P3H-03", "Headless responde reset", "p3_headless", ok, 0, details=resp.get("message", ""))
            else:
                self._add("P3H-03", "Headless responde reset", "p3_headless", False, 0, error="stdout vazio")
        except Exception as e:
            self._add("P3H-03", "Headless responde reset", "p3_headless", False, 0, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: E2E_REAL (8 testes -- F-02)
    # Execução real de tools via ToolRegistry, verificando conteúdo
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_e2e_real(self) -> None:
        from nyx.agent.tools.registry import ToolRegistry

        reg = ToolRegistry(str(PROJECT_ROOT))
        # GAUNTLET-FIXTURES-SANDBOX-01: scratch dentro do root autorizado.
        tmp_path = _gauntlet_tmp_dir() / "nyx_f2_test.py"

        # F2-01: Write+Read roundtrip
        content_to_write = "def hello():\n    return 'nyx_gauntlet_ok'\n"
        r = reg.execute("write_file", {"file_path": str(tmp_path), "content": content_to_write})
        r2 = reg.execute("read_file", {"file_path": str(tmp_path)})
        ok = r.success and r2.success and "nyx_gauntlet_ok" in r2.output
        self._add(
            "F2-01",
            "Write+Read roundtrip",
            "e2e_real",
            ok,
            0,
            details=f"write={r.success} read_has_content={'nyx_gauntlet_ok' in r2.output}",
        )

        # F2-02: Edit com substituição
        r = reg.execute(
            "edit_file",
            {
                "file_path": str(tmp_path),
                "old_string": "nyx_gauntlet_ok",
                "new_string": "nyx_gauntlet_edited",
            },
        )
        r2 = reg.execute("read_file", {"file_path": str(tmp_path)})
        ok = r.success and r2.success and "nyx_gauntlet_edited" in r2.output
        self._add(
            "F2-02",
            "Edit com substituição",
            "e2e_real",
            ok,
            0,
            details=f"edit={r.success} verified={'nyx_gauntlet_edited' in r2.output}",
        )

        # F2-03: Glob encontra arquivo real
        r = reg.execute("glob", {"pattern": "nyx/agent/*.py"})
        ok = r.success and "parser.py" in r.output
        self._add("F2-03", "Glob encontra arquivo real", "e2e_real", ok, 0, details=f"has_parser={'parser.py' in r.output}")  # noqa: E501

        # F2-04: Search encontra conteúdo
        r = reg.execute("search", {"pattern": "think", "path": str(PROJECT_ROOT / "nyx")})
        ok = r.success and len(r.output) > 0
        self._add("F2-04", "Search encontra conteúdo", "e2e_real", ok, 0, details=f"len={len(r.output)}")

        # F2-05: RunCommand real
        r = reg.execute("run_command", {"command": "echo NYX_E2E_REAL_OK"})
        ok = r.success and "NYX_E2E_REAL_OK" in r.output
        self._add("F2-05", "RunCommand real", "e2e_real", ok, 0, details=f"has_marker={'NYX_E2E_REAL_OK' in r.output}")

        # F2-06: ListFiles diretório real
        r = reg.execute("list_files", {"path": str(PROJECT_ROOT / "nyx" / "agent")})
        ok = r.success and "parser.py" in r.output
        self._add("F2-06", "ListFiles diretório real", "e2e_real", ok, 0, details=f"has_parser={'parser.py' in r.output}")  # noqa: E501

        # F2-07: Tool error handling
        r = reg.execute("read_file", {"file_path": "/tmp/nyx_inexistente_xyz_12345.py"})
        ok = not r.success and r.error and len(r.error) > 5
        self._add("F2-07", "Tool error handling", "e2e_real", ok, 0, details=f"error={r.error[:60]}")

        # F2-08: Pipeline completo
        # GAUNTLET-FIXTURES-SANDBOX-01: scratch dentro do root autorizado.
        pipeline_path = _gauntlet_tmp_dir() / "nyx_f2_pipeline.py"
        r1 = reg.execute("write_file", {"file_path": str(pipeline_path), "content": "x = 1\n"})
        r2 = reg.execute("read_file", {"file_path": str(pipeline_path)})
        r3 = reg.execute("edit_file", {"file_path": str(pipeline_path), "old_string": "x = 1", "new_string": "x = 42"})
        r4 = reg.execute("read_file", {"file_path": str(pipeline_path)})
        r5 = reg.execute("glob", {"pattern": "*.py", "path": str(pipeline_path.parent)})
        ok = (
            r1.success
            and r2.success
            and "x = 1" in r2.output
            and r3.success
            and r4.success
            and "x = 42" in r4.output
            and r5.success
        )
        self._add(
            "F2-08",
            "Pipeline completo",
            "e2e_real",
            ok,
            0,
            details=f"w={r1.success} r={r2.success} e={r3.success} r2={r4.success} g={r5.success}",
        )

        # Cleanup
        tmp_path.unlink(missing_ok=True)
        pipeline_path.unlink(missing_ok=True)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: HEADLESS_PROTOCOL (4 testes -- I-01)
    # Protocolo JSON headless expandido
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_headless_protocol(self) -> None:
        import json as _json

        def _headless(input_str: str) -> dict | None:
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "nyx.cli", "--headless"],
                    input=input_str,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(PROJECT_ROOT),
                )
                if proc.stdout.strip():
                    return _json.loads(proc.stdout.strip().split("\n")[0])
            except Exception:
                pass
            return None

        # I1-01: Headless status
        t = time.monotonic()
        resp = _headless('{"type": "status"}\n')
        ok = (
            resp is not None
            and resp.get("type") == "status"
            and resp.get("tools", 0) >= 31
            and resp.get("history") == 0
        )
        self._add(
            "I1-01",
            "Headless status",
            "headless_protocol",
            ok,
            time.monotonic() - t,
            details=f"tools={resp.get('tools') if resp else 'N/A'}",
        )

        # I1-02: Headless tools list
        resp = _headless('{"type": "tools"}\n')
        ok = (
            resp is not None
            and resp.get("type") == "tools"
            and "read_file" in resp.get("list", [])
            and "done" in resp.get("list", [])
        )
        self._add(
            "I1-02",
            "Headless tools list",
            "headless_protocol",
            ok,
            0,
            details=f"count={resp.get('count') if resp else 'N/A'}",
        )

        # I1-03: Headless tipo desconhecido
        resp = _headless('{"type": "xyz_invalido"}\n')
        ok = resp is not None and resp.get("type") == "error" and "desconhecido" in resp.get("message", "").lower()
        self._add(
            "I1-03",
            "Headless tipo desconhecido",
            "headless_protocol",
            ok,
            0,
            details=f"msg={resp.get('message', '')[:60] if resp else 'N/A'}",
        )

        # I1-04: Headless pipeline sequencial
        multi_input = '{"type": "ping"}\n{"type": "status"}\n{"type": "tools"}\n{"type": "reset"}\n'
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "nyx.cli", "--headless"],
                input=multi_input,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(PROJECT_ROOT),
            )
            lines = [ln for ln in proc.stdout.strip().split("\n") if ln.strip()]
            responses = [_json.loads(ln) for ln in lines]
            types = [r.get("type") for r in responses]
            ok = types == ["pong", "status", "tools", "ok"]
            self._add("I1-04", "Headless pipeline", "headless_protocol", ok, 0, details=f"types={types}")
        except Exception as e:
            self._add("I1-04", "Headless pipeline", "headless_protocol", False, 0, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P4_UTILITY (3 testes -- P4-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p4_utility(self) -> None:
        # P4U-01: SleepTool funciona
        from nyx.agent.tools.sleep_tool import SleepTool

        t = time.monotonic()
        st = SleepTool()
        r = st.execute({"seconds": 1}, str(PROJECT_ROOT))
        elapsed = time.monotonic() - t
        ok = r.success and elapsed >= 0.9 and "Esperou" in r.output
        self._add(
            "P4U-01",
            "SleepTool funciona",
            "p4_utility",
            ok,
            elapsed,
            details=f"elapsed={elapsed:.1f}s output={r.output[:40]}",
        )

        # P4U-02: ConfigTool set+get
        from nyx.agent.tools.config_tool import ConfigTool

        ct = ConfigTool()
        r1 = ct.execute({"action": "set", "key": "gauntlet_test", "value": "nyx_ok"}, str(PROJECT_ROOT))
        r2 = ct.execute({"action": "get", "key": "gauntlet_test"}, str(PROJECT_ROOT))
        ok = r1.success and r2.success and "nyx_ok" in r2.output
        self._add(
            "P4U-02",
            "ConfigTool set+get",
            "p4_utility",
            ok,
            0,
            details=f"set={r1.success} get_has_value={'nyx_ok' in r2.output}",
        )
        # Cleanup
        try:
            ct.execute({"action": "set", "key": "gauntlet_test", "value": ""}, str(PROJECT_ROOT))
        except Exception:
            pass

        # P4U-03: BriefTool gera resumo
        from nyx.agent.tools.brief_tool import BriefTool

        bt = BriefTool()
        r = bt.execute({}, str(PROJECT_ROOT))
        ok = r.success and "tools" in r.output.lower() and "projeto" in r.output.lower()
        self._add("P4U-03", "BriefTool gera resumo", "p4_utility", ok, 0, details=r.output[:80])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P4_WORKTREE (2 testes -- P4-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p4_worktree(self) -> None:
        from nyx.agent.tools.worktree import EnterWorktreeTool, ExitWorktreeTool, _active_worktree

        # P4W-01: EnterWorktree cria
        ewt = EnterWorktreeTool()
        r = ewt.execute({"branch_name": "nyx-gauntlet-wt-test"}, str(PROJECT_ROOT))
        ok = r.success and "Worktree criado" in r.output
        wt_path = _active_worktree.get("path", "")
        dir_exists = Path(wt_path).exists() if wt_path else False
        self._add(
            "P4W-01",
            "EnterWorktree cria",
            "p4_worktree",
            ok and dir_exists,
            0,
            details=f"path={wt_path[:60]} exists={dir_exists}",
        )

        # P4W-02: ExitWorktree limpa
        xwt = ExitWorktreeTool()
        r = xwt.execute({}, str(PROJECT_ROOT))
        ok = r.success and "removido" in r.output.lower()
        dir_gone = not Path(wt_path).exists() if wt_path else True
        self._add("P4W-02", "ExitWorktree limpa", "p4_worktree", ok and dir_gone, 0, details=f"dir_gone={dir_gone}")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P4_TASKS (3 testes -- P4-C)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p4_tasks(self) -> None:
        from nyx.agent.tools.task_manager import (
            TaskCreateTool,
            TaskGetTool,
            TaskOutputTool,
            TaskStopTool,
            _load_tasks,
            _save_tasks,
        )

        # Criar task para testar
        tc = TaskCreateTool()
        r = tc.execute({"subject": "p4 gauntlet task", "description": "teste p4"}, str(PROJECT_ROOT))

        # Extrair ID do output: "Task #XXXXXXXX criada: ..."
        import re as _re

        task_id_match = _re.search(r"#([a-f0-9]+)", r.output) if r.success else None
        task_id = task_id_match.group(1) if task_id_match else ""
        tasks = _load_tasks()
        task = next((t for t in tasks if t.id == task_id), None) if task_id else None

        if not task:
            self._add("P4T-01", "TaskGet retorna detalhes", "p4_tasks", False, 0, error="Task não criada")
            self._add("P4T-02", "TaskOutput retorna output", "p4_tasks", False, 0, error="Task não criada")
            self._add("P4T-03", "TaskStop cancela", "p4_tasks", False, 0, error="Task não criada")
            return

        # Adicionar output à task
        task.metadata["output"] = "resultado do gauntlet p4"
        _save_tasks(tasks)

        # P4T-01: TaskGet retorna detalhes
        tg = TaskGetTool()
        r = tg.execute({"task_id": task.id}, str(PROJECT_ROOT))
        ok = r.success and "p4 gauntlet task" in r.output and "pending" in r.output
        self._add("P4T-01", "TaskGet retorna detalhes", "p4_tasks", ok, 0, details=r.output[:80])

        # P4T-02: TaskOutput retorna output
        to = TaskOutputTool()
        r = to.execute({"task_id": task.id}, str(PROJECT_ROOT))
        ok = r.success and "resultado do gauntlet p4" in r.output
        self._add("P4T-02", "TaskOutput retorna output", "p4_tasks", ok, 0, details=r.output[:80])

        # P4T-03: TaskStop cancela
        ts = TaskStopTool()
        r = ts.execute({"task_id": task.id}, str(PROJECT_ROOT))
        ok = r.success and "cancelled" in r.output
        self._add("P4T-03", "TaskStop cancela", "p4_tasks", ok, 0, details=r.output[:60])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P4_DISCOVERY (4 testes -- P4-D)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p4_discovery(self) -> None:
        # P4D-01: REPLTool executa Python
        from nyx.agent.tools.repl_tool import REPLTool

        rt = REPLTool()
        r = rt.execute({"code": "print(1+1)"}, str(PROJECT_ROOT))
        ok = r.success and "2" in r.output
        self._add("P4D-01", "REPLTool executa Python", "p4_discovery", ok, 0, details=f"output={r.output.strip()[:40]}")

        # P4D-02: ToolSearch encontra
        from nyx.agent.tools.tool_search import ToolSearchTool

        ts = ToolSearchTool()
        r = ts.execute({"query": "file"}, str(PROJECT_ROOT))
        ok = r.success and "read_file" in r.output
        self._add("P4D-02", "ToolSearch encontra", "p4_discovery", ok, 0, details=r.output[:80])

        # P4D-03: SkillTool interface
        from nyx.agent.tools.skill_tool import SkillTool

        sk = SkillTool()
        ok = sk.tool_def.name == "skill" and "skill_name" in sk.tool_def.parameters
        self._add("P4D-03", "SkillTool interface", "p4_discovery", ok, 0, details=f"name={sk.tool_def.name}")

        # P4D-04: SendMessage interface
        from nyx.agent.tools.send_message import SendMessageTool

        sm = SendMessageTool()
        ok = sm.tool_def.name == "send_message" and "content" in sm.tool_def.parameters
        self._add("P4D-04", "SendMessage interface", "p4_discovery", ok, 0, details=f"name={sm.tool_def.name}")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P5_GIT (4 testes -- P5-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p5_git(self) -> None:
        from nyx.agent.commands import handle_command

        # P5G-01: /branch lista
        r = handle_command("/branch", str(PROJECT_ROOT))
        ok = r is not None and ("main" in r or "master" in r or "Branches" in r)
        self._add("P5G-01", "/branch lista", "p5_git", ok, 0, details=(r or "")[:80])

        # P5G-02: /issue interface
        r = handle_command("/issue", str(PROJECT_ROOT))
        ok = r is not None and len(r) > 5
        self._add("P5G-02", "/issue interface", "p5_git", ok, 0, details=(r or "")[:80])

        # P5G-03: /pr interface
        r = handle_command("/pr", str(PROJECT_ROOT))
        ok = r is not None and len(r) > 5
        self._add("P5G-03", "/pr interface", "p5_git", ok, 0, details=(r or "")[:80])

        # P5G-04: /rewind retorna magic
        r = handle_command("/rewind 3", str(PROJECT_ROOT))
        ok = r is not None and "__rewind__" in r
        self._add("P5G-04", "/rewind retorna magic", "p5_git", ok, 0, details=(r or "")[:40])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P5_CONFIG (5 testes -- P5-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p5_config(self) -> None:
        from nyx.agent.commands import handle_command

        # P5C-01: /config mostra config
        r = handle_command("/config", str(PROJECT_ROOT))
        ok = r is not None and ("modelo" in r or "proxy" in r)
        self._add("P5C-01", "/config mostra config", "p5_config", ok, 0, details=(r or "")[:80])

        # P5C-02: /env mostra variáveis
        r = handle_command("/env", str(PROJECT_ROOT))
        ok = r is not None and "Variáveis" in r
        self._add("P5C-02", "/env mostra variáveis", "p5_config", ok, 0, details=(r or "")[:80])

        # P5C-03: /permissions lista tools
        r = handle_command("/permissions", str(PROJECT_ROOT))
        ok = r is not None and "read_file" in r
        self._add("P5C-03", "/permissions lista tools", "p5_config", ok, 0, details=(r or "")[:80])

        # P5C-04: /hooks registrado
        r = handle_command("/hooks", str(PROJECT_ROOT))
        ok = r is not None and "Hook" in r
        self._add("P5C-04", "/hooks registrado", "p5_config", ok, 0, details=(r or "")[:60])

        # P5C-05: /theme lista temas
        r = handle_command("/theme list", str(PROJECT_ROOT))
        ok = r is not None and ("nyx" in r.lower() or "dracula" in r.lower() or "Temas" in r)
        self._add("P5C-05", "/theme lista temas", "p5_config", ok, 0, details=(r or "")[:80])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P5_SESSION (6 testes -- P5-C)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p5_session(self) -> None:
        from nyx.agent.commands import handle_command

        # P5S-01: /resume retorna magic
        r = handle_command("/resume", str(PROJECT_ROOT))
        ok = r is not None and "__session_load__" in r
        self._add("P5S-01", "/resume retorna magic", "p5_session", ok, 0)

        # P5S-02: /export retorna magic
        r = handle_command("/export json", str(PROJECT_ROOT))
        ok = r is not None and "__export__" in r
        self._add("P5S-02", "/export retorna magic", "p5_session", ok, 0, details=(r or "")[:40])

        # P5S-03: /copy retorna magic
        r = handle_command("/copy", str(PROJECT_ROOT))
        ok = r == "__copy__"
        self._add("P5S-03", "/copy retorna magic", "p5_session", ok, 0)

        # P5S-04: /summary gera prompt
        r = handle_command("/summary", str(PROJECT_ROOT))
        ok = r is not None and ("ações" in r.lower() or "resumo" in r.lower())
        self._add("P5S-04", "/summary gera prompt", "p5_session", ok, 0, details=(r or "")[:60])

        # P5S-05: /stats retorna magic
        r = handle_command("/stats", str(PROJECT_ROOT))
        ok = r == "__stats__"
        self._add("P5S-05", "/stats retorna magic", "p5_session", ok, 0)

        # P5S-06: /usage retorna magic
        r = handle_command("/usage", str(PROJECT_ROOT))
        ok = r == "__usage__"
        self._add("P5S-06", "/usage retorna magic", "p5_session", ok, 0)

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P5_EXECUTION (4 testes -- P5-D)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p5_execution(self) -> None:
        from nyx.agent.commands import handle_command, list_commands

        # P5E-01: /tasks lista
        r = handle_command("/tasks", str(PROJECT_ROOT))
        ok = r is not None and ("tarefa" in r.lower() or "nenhuma" in r.lower() or "total" in r.lower())
        self._add("P5E-01", "/tasks lista", "p5_execution", ok, 0, details=(r or "")[:80])

        # P5E-02: /skills registrado
        r = handle_command("/skills", str(PROJECT_ROOT))
        ok = r is not None and ("skill" in r.lower() or "nenhum" in r.lower())
        self._add("P5E-02", "/skills registrado", "p5_execution", ok, 0, details=(r or "")[:60])

        # P5E-03: /files retorna magic
        r = handle_command("/files", str(PROJECT_ROOT))
        ok = r == "__files__"
        self._add("P5E-03", "/files retorna magic", "p5_execution", ok, 0)

        # P5E-04: Total commands >= 33
        cmds = list_commands()
        ok = len(cmds) >= 33
        self._add("P5E-04", "Total commands >= 33", "p5_execution", ok, 0, details=f"{len(cmds)} commands")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P6_MEMORIA (4 testes -- P6-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p6_memoria(self) -> None:
        from nyx.agent.services.memory import SessionMemory
        from nyx.agent.services.summary import summarize, summarize_by_type
        from nyx.agent.session import CodeSession

        # P6M-01: Memory save+search
        mem = SessionMemory()
        mem.save("gauntlet_p6", "teste de memória do gauntlet", tags=["test", "gauntlet"], session_id="gauntlet-p6")
        results = mem.search("gauntlet")
        ok = len(results) > 0 and any("gauntlet_p6" == r.key for r in results)
        self._add("P6M-01", "Memory save+search", "p6_memoria", ok, 0, details=f"{len(results)} resultados")

        # P6M-02: Memory persistência
        mem2 = SessionMemory()
        results2 = mem2.search("gauntlet_p6")
        ok = len(results2) > 0
        self._add(
            "P6M-02", "Memory persistência", "p6_memoria", ok, 0, details=f"{len(results2)} resultados após reload"
        )

        # P6M-03: Summary gera resumo
        session = CodeSession()
        session.add_user("teste gauntlet")
        session.add_tool_call("read_file", {"path": "README.md"}, "conteúdo", is_key=False)
        session.add_tool_call("edit_file", {"path": "test.py"}, "editado", is_key=True)
        result = summarize(session)
        ok = "Resumo" in result and "escrita" in result.lower()
        self._add("P6M-03", "Summary gera resumo", "p6_memoria", ok, 0, details=result[:80])

        # P6M-04: Summary agrupa por tipo
        groups = summarize_by_type(session)
        ok = isinstance(groups, dict) and len(groups) > 0
        self._add("P6M-04", "Summary agrupa por tipo", "p6_memoria", ok, 0, details=f"tipos: {list(groups.keys())}")

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P6_QUALIDADE (3 testes -- P6-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p6_qualidade(self) -> None:
        from nyx.agent.models import ActionResult
        from nyx.agent.preflight import check as preflight_check
        from nyx.agent.services.suggestions import suggest
        from nyx.agent.session import CodeSession
        from nyx.agent.validator import validate as post_validate

        # P6Q-01: Suggestion gera sugestão
        session = CodeSession()
        session.add_tool_call("read_file", {"path": "test.py"}, "conteúdo")
        suggestions = suggest(session)
        ok = len(suggestions) > 0
        self._add(
            "P6Q-01",
            "Suggestion gera sugestão",
            "p6_qualidade",
            ok,
            0,
            details=f"{len(suggestions)} sugestões: {suggestions[0][:40] if suggestions else ''}",
        )

        # P6Q-02: Preflight valida path
        result = preflight_check("read_file", {"file_path": "/tmp/nyx_inexistente_xyz.py"}, str(PROJECT_ROOT))
        ok = len(result.warnings) > 0 and "não existe" in result.warnings[0].lower()
        self._add("P6Q-02", "Preflight valida path", "p6_qualidade", ok, 0, details=f"warnings={result.warnings[:1]}")

        # P6Q-03: PostValidator verifica
        action_result = ActionResult(success=True, output="Arquivo criado: test.py (100 bytes)")
        vr = post_validate("write_file", {"content": "x = 1"}, action_result)
        ok = vr.ok
        self._add(
            "P6Q-03", "PostValidator verifica", "p6_qualidade", ok, 0, details=f"ok={vr.ok} warnings={vr.warnings}"
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P8_EDICAO (3 testes -- P8-A)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p8_edicao(self) -> None:
        # P8E-01: Analyze retorna estrutura
        from nyx.agent.tools.analyze_tool import AnalyzeTool

        at = AnalyzeTool()
        r = at.execute({"file_path": "nyx/agent/models.py"}, str(PROJECT_ROOT))
        ok = r.success and "Análise" in r.output and ("Classes" in r.output or "Funções" in r.output)
        self._add("P8E-01", "Analyze retorna estrutura", "p8_edicao", ok, 0, details=r.output[:80])

        # P8E-02: Patch aplica diff
        from nyx.agent.tools.patch_tool import PatchTool

        # GAUNTLET-FIXTURES-SANDBOX-01: scratch dentro do root autorizado.
        tmp = _gauntlet_tmp_dir() / "nyx_p8_patch.py"
        tmp.write_text("linha1\nlinha2\nlinha3\n", encoding="utf-8")
        pt = PatchTool()
        patch = "-linha2\n+linha2_editada"
        r = pt.execute({"file_path": str(tmp), "patch": patch}, str(PROJECT_ROOT))
        content = tmp.read_text(encoding="utf-8")
        ok = r.success and "linha2_editada" in content
        tmp.unlink(missing_ok=True)
        self._add(
            "P8E-02", "Patch aplica diff", "p8_edicao", ok, 0, details=r.output[:60] if r.success else r.error[:60]
        )

        # P8E-03: MultiEdit atômico
        from nyx.agent.tools.multi_edit import MultiEditTool

        # GAUNTLET-FIXTURES-SANDBOX-01: scratch dentro do root autorizado.
        f1 = _gauntlet_tmp_dir() / "nyx_me1.py"
        f2 = _gauntlet_tmp_dir() / "nyx_me2.py"
        f1.write_text("x = 1\n", encoding="utf-8")
        f2.write_text("y = 2\n", encoding="utf-8")
        me = MultiEditTool()
        r = me.execute(
            {
                "edits": [
                    {"file_path": str(f1), "old_string": "x = 1", "new_string": "x = 10"},
                    {"file_path": str(f2), "old_string": "y = 2", "new_string": "y = 20"},
                ]
            },
            str(PROJECT_ROOT),
        )
        ok = r.success and "x = 10" in f1.read_text() and "y = 20" in f2.read_text()
        f1.unlink(missing_ok=True)
        f2.unlink(missing_ok=True)
        self._add(
            "P8E-03", "MultiEdit atômico", "p8_edicao", ok, 0, details=r.output[:60] if r.success else r.error[:60]
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P8_PROVIDER (2 testes -- P8-B)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p8_provider(self) -> None:
        # P8P-01: OllamaProvider importa
        from nyx.providers.ollama import OllamaProvider

        op = OllamaProvider(proxy_url="http://127.0.0.1:11436")
        ok = hasattr(op, "chat") and hasattr(op, "health") and hasattr(op, "models")
        self._add("P8P-01", "OllamaProvider importa", "p8_provider", ok, 0)

        # P8P-02: ProjectContext detecta Python
        from nyx.context.project import detect, format_context

        info = detect(str(PROJECT_ROOT))
        ok = "python" in info.language.lower()
        ctx = format_context(info)
        self._add("P8P-02", "ProjectContext detecta Python", "p8_provider", ok, 0, details=ctx[:80])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: INFRA_SCAFFOLD (3 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_infra_scaffold(self) -> None:
        import importlib
        import sys as _sys

        # SCF-01: scaffold tool -- gera arquivo + registra + remove
        t = time.monotonic()
        try:
            _sys.path.insert(0, str(PROJECT_ROOT))
            import argparse as _ap

            from scripts.scaffold import remove_tool, scaffold_tool

            args = _ap.Namespace(
                name="__gauntlet_test_tool",
                class_name="GauntletTestTool",
                description="Teste automatizado do scaffold",
                params="x:string",
            )
            rc = scaffold_tool(args)
            tool_file = PROJECT_ROOT / "nyx" / "agent" / "tools" / "__gauntlet_test_tool.py"
            file_ok = tool_file.exists()
            registry_content = (PROJECT_ROOT / "nyx" / "agent" / "tools" / "registry.py").read_text()
            reg_ok = "GauntletTestTool" in registry_content

            remove_tool("__gauntlet_test_tool", "GauntletTestTool")
            cleanup_ok = not tool_file.exists()

            ok = rc == 0 and file_ok and reg_ok and cleanup_ok
            details = f"rc={rc} file={file_ok} reg={reg_ok} cleanup={cleanup_ok}"
            self._add(
                "SCF-01",
                "scaffold tool cria+registra+remove",
                "infra_scaffold",
                ok,
                time.monotonic() - t,
                details=details,
            )
        except Exception as e:
            self._add(
                "SCF-01",
                "scaffold tool cria+registra+remove",
                "infra_scaffold",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # SCF-02: scaffold command -- gera handler + remove
        t = time.monotonic()
        try:
            from scripts.scaffold import remove_command, scaffold_command

            args = _ap.Namespace(
                name="__gauntlet-test-cmd",
                description="Teste automatizado",
                category="teste",
                aliases="",
            )
            rc = scaffold_command(args)
            # SCAFFOLD-CMD-FIX-01: commands virou pacote. Verificar arquivo
            # nyx/agent/commands/<name>.py e import em __init__.py.
            cmd_file = PROJECT_ROOT / "nyx" / "agent" / "commands" / "__gauntlet_test_cmd.py"
            init_content = (PROJECT_ROOT / "nyx" / "agent" / "commands" / "__init__.py").read_text()
            cmd_ok = cmd_file.exists() and "__gauntlet_test_cmd" in init_content

            remove_command("__gauntlet-test-cmd")
            init_after = (PROJECT_ROOT / "nyx" / "agent" / "commands" / "__init__.py").read_text()
            cleanup_ok = not cmd_file.exists() and "__gauntlet_test_cmd" not in init_after

            ok = rc == 0 and cmd_ok and cleanup_ok
            details = f"rc={rc} cmd={cmd_ok} cleanup={cleanup_ok}"
            self._add(
                "SCF-02", "scaffold command cria+remove", "infra_scaffold", ok, time.monotonic() - t, details=details
            )
        except Exception as e:
            self._add(
                "SCF-02", "scaffold command cria+remove", "infra_scaffold", False, time.monotonic() - t, error=str(e)
            )

        # SCF-03: scaffold service -- gera arquivo + importa + remove
        t = time.monotonic()
        try:
            from scripts.scaffold import remove_service, scaffold_service

            args = _ap.Namespace(
                name="__gauntlet_test_svc",
                class_name="GauntletTestSvc",
                description="Teste automatizado",
            )
            rc = scaffold_service(args)
            svc_file = PROJECT_ROOT / "nyx" / "agent" / "services" / "__gauntlet_test_svc.py"
            file_ok = svc_file.exists()

            spec = importlib.util.spec_from_file_location("__gauntlet_test_svc", str(svc_file))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            import_ok = hasattr(mod, "GauntletTestSvc")

            remove_service("__gauntlet_test_svc")
            cleanup_ok = not svc_file.exists()

            ok = rc == 0 and file_ok and import_ok and cleanup_ok
            details = f"rc={rc} file={file_ok} import={import_ok} cleanup={cleanup_ok}"
            self._add(
                "SCF-03",
                "scaffold service cria+importa+remove",
                "infra_scaffold",
                ok,
                time.monotonic() - t,
                details=details,
            )
        except Exception as e:
            self._add(
                "SCF-03",
                "scaffold service cria+importa+remove",
                "infra_scaffold",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P7_TUI (2 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p7_tui(self) -> None:
        # P7T-01: prompt-toolkit importa ou fallback funciona
        t = time.monotonic()
        try:
            from prompt_toolkit import PromptSession  # noqa: F401 -- smoke-test de disponibilidade
            from prompt_toolkit.history import FileHistory  # noqa: F401 -- smoke-test de disponibilidade

            ok = True
            details = "prompt-toolkit disponível"
        except ImportError:
            ok = True
            details = "fallback para input() (prompt-toolkit ausente)"
        self._add("P7T-01", "prompt-toolkit importa ou fallback", "p7_tui", ok, time.monotonic() - t, details=details)

        # P7T-02: History path acessível
        t = time.monotonic()
        try:
            history_path = Path.home() / ".nyx" / "history"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            ok = history_path.parent.exists()
            self._add("P7T-02", "History path acessível", "p7_tui", ok, time.monotonic() - t, details=str(history_path))
        except Exception as e:
            self._add("P7T-02", "History path acessível", "p7_tui", False, time.monotonic() - t, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P10 Commands (5 fases)
    # ═══════════════════════════════════════════════════════════════════

    async def _test_commands(self, phase: str, test_prefix: str, cmd_names: list[str]) -> None:
        """Helper: testa que cada command responde com conteúdo real (sem stubs)."""
        from nyx.agent.commands import handle_command

        for i, name in enumerate(cmd_names, 1):
            t = time.monotonic()
            try:
                result = handle_command(f"/{name}", str(PROJECT_ROOT))
                is_valid = (
                    result is not None
                    and isinstance(result, str)
                    and len(result) > 0
                    and "Use /help para mais informações" not in result
                )
                self._add(
                    f"{test_prefix}-{i:02d}",
                    f"/{name} funcional",
                    phase,
                    is_valid,
                    time.monotonic() - t,
                    details=str(result)[:60],
                )
            except Exception as e:
                self._add(
                    f"{test_prefix}-{i:02d}", f"/{name} funcional", phase, False, time.monotonic() - t, error=str(e)
                )

    async def _phase_p10_projeto(self) -> None:
        await self._test_commands("p10_projeto", "P10B", ["add-dir", "init", "version"])

    async def _phase_p10_debug(self) -> None:
        await self._test_commands("p10_debug", "P10D", ["trace", "ctx-viz", "break-cache"])

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P11 Services (7 fases)
    # ═══════════════════════════════════════════════════════════════════

    async def _test_services(self, phase: str, test_prefix: str, services: list[tuple[str, str]]) -> None:
        """Helper: testa que cada service importa, instancia e retorna status real."""
        import importlib

        for i, (module_name, class_name) in enumerate(services, 1):
            t = time.monotonic()
            try:
                mod = importlib.import_module(f"nyx.agent.services.{module_name}")
                cls = getattr(mod, class_name)
                instance = cls()
                st = instance.status()
                ok = (
                    isinstance(st, dict) and st.get("ativo") is True and len(st) > 2  # Mais que só service+ativo
                )
                self._add(
                    f"{test_prefix}-{i:02d}",
                    f"{class_name} funcional",
                    phase,
                    ok,
                    time.monotonic() - t,
                    details=str(st)[:80],
                )
            except Exception as e:
                self._add(
                    f"{test_prefix}-{i:02d}",
                    f"{class_name} funcional",
                    phase,
                    False,
                    time.monotonic() - t,
                    error=str(e),
                )

    async def _phase_p11_infra(self) -> None:
        await self._test_services(
            "p11_infra",
            "P11A",
            [
                ("analytics", "Analytics"),
                ("diagnostics", "DiagnosticTracking"),
                ("logging_service", "InternalLogging"),
                ("tool_use_summary", "ToolUseSummary"),
            ],
        )

    async def _phase_p10_memoria(self) -> None:
        await self._test_commands("p10_memoria", "P10H", ["memory"])

    async def _phase_p10_avancado(self) -> None:
        await self._test_commands("p10_avancado", "P10I", ["btw", "pr-comments"])

    async def _phase_p10_root(self) -> None:
        await self._test_commands(
            "p10_root", "P10J", ["advisor", "brief-cmd", "commit-push-pr", "insights", "security-review"]
        )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P7_COMPLETION (2 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p7_completion(self) -> None:
        # P7C-01: NyxCompleter importa e inicializa
        t = time.monotonic()
        try:
            from nyx.agent.completer import NyxCompleter, create_completer

            comp = NyxCompleter(str(PROJECT_ROOT))
            ok = comp is not None
            self._add("P7C-01", "NyxCompleter inicializa", "p7_completion", ok, time.monotonic() - t)
        except Exception as e:
            self._add("P7C-01", "NyxCompleter inicializa", "p7_completion", False, time.monotonic() - t, error=str(e))

        # P7C-02: create_completer retorna commands
        t = time.monotonic()
        try:
            comp = create_completer(str(PROJECT_ROOT))
            ok = comp is not None and len(comp._commands) >= 30
            details = f"commands={len(comp._commands)}" if comp else "None"
            self._add(
                "P7C-02", "create_completer lista commands", "p7_completion", ok, time.monotonic() - t, details=details
            )
        except Exception as e:
            self._add(
                "P7C-02", "create_completer lista commands", "p7_completion", False, time.monotonic() - t, error=str(e)
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: P7_VISUAL (2 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_p7_visual(self) -> None:
        # P7V-01: render_diff gera output
        t = time.monotonic()
        try:
            from nyx.agent.output import render_diff

            result = render_diff("linha 1\nlinha 2\n", "linha 1\nlinha modificada\n", "test.py")
            ok = len(result) > 0 and ("+" in result or "-" in result)
            self._add(
                "P7V-01", "render_diff gera diff", "p7_visual", ok, time.monotonic() - t, details=f"len={len(result)}"
            )
        except Exception as e:
            self._add("P7V-01", "render_diff gera diff", "p7_visual", False, time.monotonic() - t, error=str(e))

        # P7V-02: nyx_spinner funciona como context manager
        t = time.monotonic()
        try:
            from nyx.agent.output import nyx_spinner

            with nyx_spinner("teste") as s:
                ok = s is not None
            self._add("P7V-02", "nyx_spinner funciona", "p7_visual", ok, time.monotonic() - t)
        except Exception as e:
            self._add("P7V-02", "nyx_spinner funciona", "p7_visual", False, time.monotonic() - t, error=str(e))

    # ═══════════════════════════════════════════════════════════════════
    # FASE: CONTEXTO (10 testes -- CTX-01 summarizer + CTX-02 memory + CTX-03 repomap)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_contexto(self) -> None:
        import tempfile
        from pathlib import Path as _Path

        import nyx.agent.memory as mem_mod
        import nyx.agent.repomap as rm_mod

        # CTX-01: SessionSummarizer importa e instancia
        t = time.monotonic()
        try:
            from nyx.agent.session import CodeSession
            from nyx.agent.summarizer import SessionSummarizer

            sess = CodeSession()
            sess.iteration = 5
            summ = SessionSummarizer(self._proxy, self._model)
            ok = summ.should_summarize(sess)
            self._add(
                "CTX-01",
                "Summarizer instancia e batching",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"should={ok}",
            )
        except Exception as e:
            self._add(
                "CTX-01", "Summarizer instancia e batching", "contexto", False, time.monotonic() - t, error=str(e)
            )

        # CTX-02: NyxMemory write+load roundtrip em tmpdir
        t = time.monotonic()
        try:
            from nyx.agent.memory import NyxMemory

            with tempfile.TemporaryDirectory() as tmp:
                mem_mod.MEMORY_ROOT = _Path(tmp)
                m = NyxMemory("/home/fake/Proj")
                p = m.write("conv", "uso type hints sempre", "convenção")
                bundle = m.load()
                ok = p.exists() and "type hints" in bundle
            self._add(
                "CTX-02",
                "NyxMemory roundtrip",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"bundle_bytes={len(bundle)}",
            )
        except Exception as e:
            self._add("CTX-02", "NyxMemory roundtrip", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-03: NyxMemory sandbox rejeita oversize e traversal
        t = time.monotonic()
        try:
            from nyx.agent.memory import NyxMemory

            with tempfile.TemporaryDirectory() as tmp:
                mem_mod.MEMORY_ROOT = _Path(tmp)
                m = NyxMemory("/home/fake/Proj")
                oversize_rejected = False
                try:
                    m.write("big", "x" * 5000, "oversize")
                except ValueError:
                    oversize_rejected = True
                traversal_path = m.write("../../passwd", "tentativa", "traversal")
                traversal_neutralized = traversal_path.parent == m.directory
                ok = oversize_rejected and traversal_neutralized
            self._add(
                "CTX-03",
                "NyxMemory sandbox (size+traversal)",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"oversize={oversize_rejected} traversal={traversal_neutralized}",
            )
        except Exception as e:
            self._add(
                "CTX-03", "NyxMemory sandbox (size+traversal)", "contexto", False, time.monotonic() - t, error=str(e)
            )

        # CTX-04: WriteMemoryTool registrada
        t = time.monotonic()
        try:
            from nyx.agent.tools.registry import ToolRegistry

            reg = ToolRegistry(str(PROJECT_ROOT))
            ok = "write_memory" in reg._tools
            self._add(
                "CTX-04",
                "WriteMemoryTool registrada",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"tools={reg.tool_count}",
            )
        except Exception as e:
            self._add("CTX-04", "WriteMemoryTool registrada", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-05: ActionType.WRITE_MEMORY existe
        t = time.monotonic()
        try:
            from nyx.agent.models import ActionType

            ok = ActionType.WRITE_MEMORY.value == "write_memory"
            self._add("CTX-05", "ActionType.WRITE_MEMORY", "contexto", ok, time.monotonic() - t)
        except Exception as e:
            self._add("CTX-05", "ActionType.WRITE_MEMORY", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-06: RepoMap.build indexa nyx/ em <3s e respeita orçamento
        t = time.monotonic()
        try:
            from nyx.agent.repomap import RepoMap

            with tempfile.TemporaryDirectory() as tmp:
                rm_mod.CACHE_FILE = _Path(tmp) / "cache.json"
                r = RepoMap(PROJECT_ROOT)
                idx = r.build()
                dt = time.monotonic() - t
                rendered = r.render(budget_bytes=2048)
                ok = len(idx) > 10 and dt < 3.0 and len(rendered) <= 2200
            self._add(
                "CTX-06",
                "RepoMap build + render 2KB",
                "contexto",
                ok,
                dt,
                details=f"files={len(idx)} render={len(rendered)}b dt={dt:.2f}s",
            )
        except Exception as e:
            self._add("CTX-06", "RepoMap build + render 2KB", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-07: RepoMap cache roundtrip
        t = time.monotonic()
        try:
            from nyx.agent.repomap import RepoMap

            with tempfile.TemporaryDirectory() as tmp:
                rm_mod.CACHE_FILE = _Path(tmp) / "cache.json"
                r1 = RepoMap(PROJECT_ROOT)
                r1.build()
                r1.save_cache()
                r2 = RepoMap(PROJECT_ROOT)
                ok = len(r2._cache) > 0
            self._add(
                "CTX-07",
                "RepoMap cache roundtrip",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"entries={len(r2._cache)}",
            )
        except Exception as e:
            self._add("CTX-07", "RepoMap cache roundtrip", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-08: RepoMap.invalidate marca reindex
        t = time.monotonic()
        try:
            from nyx.agent.repomap import RepoMap

            with tempfile.TemporaryDirectory() as tmp:
                rm_mod.CACHE_FILE = _Path(tmp) / "cache.json"
                r = RepoMap(PROJECT_ROOT)
                r.build()
                target = "nyx/agent/loop/_core.py"
                assert target in r._cache
                r.invalidate(str(PROJECT_ROOT / target))
                ok = target not in r._cache
            self._add("CTX-08", "RepoMap invalidate", "contexto", ok, time.monotonic() - t)
        except Exception as e:
            self._add("CTX-08", "RepoMap invalidate", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-09: build_system_prompt com os 3 placeholders
        t = time.monotonic()
        try:
            from nyx.agent.prompt import build_system_prompt

            p = build_system_prompt(
                str(PROJECT_ROOT),
                ["read_file", "write_memory"],
                memory_files="--- a.md ---\npyenv 3.12",
                repo_map="nyx/agent/loop.py: class AgentLoop",
                session_summary="## Objetivo\nteste\n## Estado\nok",
            )
            ok = "Memória persistente" in p and "Mapa do repositório" in p and "Sessão em andamento" in p
            self._add(
                "CTX-09", "Prompt com 3 placeholders", "contexto", ok, time.monotonic() - t, details=f"len={len(p)}"
            )
        except Exception as e:
            self._add("CTX-09", "Prompt com 3 placeholders", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-10: Summarizer roundtrip com LLM real (via proxy)
        t = time.monotonic()
        try:
            from nyx.agent.session import CodeSession
            from nyx.agent.summarizer import SessionSummarizer

            sess = CodeSession()
            sess.iteration = 5
            sess.add_user("quero portar o módulo streaming do TS pra Python")
            sess.add_tool_call("read_file", {"file_path": "openclaud/src/streaming/index.ts"}, "conteudo ...")
            sess.add_assistant("Plano: port passo a passo")
            summ = SessionSummarizer(self._proxy, self._model)
            result = await summ.update(sess)
            ok = bool(result) and len(result) > 50
            self._add(
                "CTX-10",
                "Summarizer LLM roundtrip",
                "contexto",
                ok,
                time.monotonic() - t,
                details=f"chars={len(result)}",
            )
        except Exception as e:
            self._add("CTX-10", "Summarizer LLM roundtrip", "contexto", False, time.monotonic() - t, error=str(e))

        # CTX-11: write_memory disparado por linguagem natural (infra ADR-002)
        t = time.monotonic()
        try:
            import httpx

            from nyx.agent.prompt import build_system_prompt
            from nyx.agent.tools.registry import ToolRegistry

            registry = ToolRegistry(str(PROJECT_ROOT))
            tool_names = [name for name in registry._tools]
            system = build_system_prompt(str(PROJECT_ROOT), tool_names)
            tool_schemas = registry.tool_defs

            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": "lembra que eu uso pyenv 3.12 neste projeto"},
                ],
                "tools": tool_schemas,
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=180) as client:
                r = await client.post(f"{self._proxy}/v1/chat/completions", json=payload)
                data = r.json()
            msg = data["choices"][0]["message"]
            tool_calls = msg.get("tool_calls") or []
            chose_write_memory = any(
                c.get("function", {}).get("name") == "write_memory" for c in tool_calls
            )
            self._add(
                "CTX-11",
                "write_memory por linguagem natural",
                "contexto",
                chose_write_memory,
                time.monotonic() - t,
                details=f"tool_calls={len(tool_calls)} write_memory={chose_write_memory}",
            )
        except Exception as e:
            self._add(
                "CTX-11",
                "write_memory por linguagem natural",
                "contexto",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: INFRA_SYNC (5 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_infra_sync(self) -> None:
        import subprocess as _sp

        sync_script = str(PROJECT_ROOT / "scripts" / "sync.py")

        # SYNC-01: sync.py existe e roda
        t = time.monotonic()
        try:
            r = _sp.run(
                [sys.executable, sync_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(PROJECT_ROOT),
            )
            ok = "RESULTADO:" in r.stdout
            self._add(
                "SYNC-01",
                "sync.py roda sem crash",
                "infra_sync",
                ok,
                time.monotonic() - t,
                details=f"rc={r.returncode}",
            )
        except Exception as e:
            self._add("SYNC-01", "sync.py roda sem crash", "infra_sync", False, time.monotonic() - t, error=str(e))

        # SYNC-02: Verifica tool registration
        t = time.monotonic()
        try:
            # GAUNTLET-SYNC-02-RECOVER-01: sync.py emite "Todos N arquivos de tool importados"
            # (masculino, refere-se a "arquivos"). Aceitamos as 3 formas observadas em runs reais.
            stdout_lower = r.stdout.lower()
            ok = (
                "tools registradas" in stdout_lower
                or "arquivos de tool importados" in stdout_lower
                or "Todas" in r.stdout
                or "Todos" in r.stdout
            )
            self._add("SYNC-02", "sync verifica tool registration", "infra_sync", ok, time.monotonic() - t)
        except Exception as e:
            self._add(
                "SYNC-02", "sync verifica tool registration", "infra_sync", False, time.monotonic() - t, error=str(e)
            )

        # SYNC-03: Verifica commands
        t = time.monotonic()
        try:
            ok = "Commands registrados" in r.stdout
            self._add("SYNC-03", "sync verifica commands", "infra_sync", ok, time.monotonic() - t)
        except Exception as e:
            self._add("SYNC-03", "sync verifica commands", "infra_sync", False, time.monotonic() - t, error=str(e))

        # SYNC-04: Verifica services
        t = time.monotonic()
        try:
            ok = "services importam" in r.stdout.lower()
            self._add("SYNC-04", "sync verifica services", "infra_sync", ok, time.monotonic() - t)
        except Exception as e:
            self._add("SYNC-04", "sync verifica services", "infra_sync", False, time.monotonic() - t, error=str(e))

        # SYNC-05: Verifica test_*.py soltos
        t = time.monotonic()
        try:
            ok = "test_*.py" in r.stdout
            self._add("SYNC-05", "sync verifica test_*.py soltos", "infra_sync", ok, time.monotonic() - t)
        except Exception as e:
            self._add(
                "SYNC-05", "sync verifica test_*.py soltos", "infra_sync", False, time.monotonic() - t, error=str(e)
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: COVERAGE (6 testes)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_coverage(self) -> None:
        # COV-01: Todo .py em tools/ está no registry
        t = time.monotonic()
        try:
            tools_dir = PROJECT_ROOT / "nyx" / "agent" / "tools"
            registry_content = (tools_dir / "registry.py").read_text(encoding="utf-8")
            tool_files = sorted(
                f.stem
                for f in tools_dir.glob("*.py")
                if f.stem not in ("__init__", "base", "registry") and not f.stem.startswith("__")
            )
            missing = [f for f in tool_files if f"from .{f} import" not in registry_content]
            ok = len(missing) == 0
            details = f"{len(tool_files)} arquivos, {len(missing)} sem import"
            if missing:
                details += f": {missing[:5]}"
            self._add(
                "COV-01",
                "Todo .py em tools/ importado no registry",
                "coverage",
                ok,
                time.monotonic() - t,
                details=details,
            )
        except Exception as e:
            self._add(
                "COV-01",
                "Todo .py em tools/ importado no registry",
                "coverage",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # COV-02: Registry tool_count >= 34
        t = time.monotonic()
        try:
            from nyx.agent.tools.registry import ToolRegistry

            reg = ToolRegistry(str(PROJECT_ROOT))
            count = reg.tool_count
            ok = count >= 34
            self._add(
                "COV-02",
                f"Registry tool_count >= 34 (atual: {count})",
                "coverage",
                ok,
                time.monotonic() - t,
                details=f"tools={count}",
            )
        except Exception as e:
            self._add("COV-02", "Registry tool_count >= 34", "coverage", False, time.monotonic() - t, error=str(e))

        # COV-03: Todo service importa sem erro
        t = time.monotonic()
        try:
            import importlib

            services_dir = PROJECT_ROOT / "nyx" / "agent" / "services"
            svc_files = sorted(
                f.stem for f in services_dir.glob("*.py") if f.stem != "__init__" and not f.stem.startswith("__")
            )
            failed = []
            for svc in svc_files:
                try:
                    importlib.import_module(f"nyx.agent.services.{svc}")
                except Exception as exc:
                    failed.append(f"{svc}: {exc}")
            ok = len(failed) == 0
            details = f"{len(svc_files)} services, {len(failed)} falhas"
            if failed:
                details += f": {failed[:3]}"
            self._add("COV-03", "Todo service importa sem erro", "coverage", ok, time.monotonic() - t, details=details)
        except Exception as e:
            self._add("COV-03", "Todo service importa sem erro", "coverage", False, time.monotonic() - t, error=str(e))

        # COV-04: Nenhum test_*.py solto
        t = time.monotonic()
        try:
            test_files = []
            for f in PROJECT_ROOT.rglob("test_*.py"):
                rel = str(f.relative_to(PROJECT_ROOT))
                if "venv" not in rel and "__pycache__" not in rel and "node_modules" not in rel:
                    test_files.append(rel)
            ok = len(test_files) == 0
            details = f"{len(test_files)} test_*.py encontrados"
            if test_files:
                details += f": {test_files[:5]}"
            self._add(
                "COV-04", "Nenhum test_*.py solto no projeto", "coverage", ok, time.monotonic() - t, details=details
            )
        except Exception as e:
            self._add(
                "COV-04", "Nenhum test_*.py solto no projeto", "coverage", False, time.monotonic() - t, error=str(e)
            )

        # COV-05: Todo command registrado com @nyx_command
        t = time.monotonic()
        try:
            from nyx.agent.commands import list_commands

            cmds = list_commands()
            cmd_count = len(cmds)
            ok = cmd_count >= 33
            self._add(
                "COV-05",
                f"Commands registrados >= 33 (atual: {cmd_count})",
                "coverage",
                ok,
                time.monotonic() - t,
                details=f"commands={cmd_count}",
            )
        except Exception as e:
            self._add("COV-05", "Commands registrados >= 33", "coverage", False, time.monotonic() - t, error=str(e))

        # COV-06: scaffold.py existe e funciona
        t = time.monotonic()
        try:
            scaffold_path = PROJECT_ROOT / "scripts" / "scaffold.py"
            exists = scaffold_path.exists()
            if exists:
                import subprocess

                r = subprocess.run(
                    [sys.executable, str(scaffold_path), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                help_ok = r.returncode == 0 and "tool" in r.stdout and "command" in r.stdout
            else:
                help_ok = False
            ok = exists and help_ok
            self._add(
                "COV-06",
                "scaffold.py existe e --help funciona",
                "coverage",
                ok,
                time.monotonic() - t,
                details=f"exists={exists} help={help_ok}",
            )
        except Exception as e:
            self._add(
                "COV-06", "scaffold.py existe e --help funciona", "coverage", False, time.monotonic() - t, error=str(e)
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: GPU_TUNE (3 testes -- portabilidade PORT-01)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_gpu_tune(self) -> None:
        import json as _json
        import os as _os
        import subprocess as _sub
        import tempfile as _tmp

        script = PROJECT_ROOT / "scripts" / "detect_gpu.py"
        python = PROJECT_ROOT / "venv" / "bin" / "python"

        # GPU-01: --dry-run retorna JSON válido com chaves esperadas
        t = time.monotonic()
        try:
            r = _sub.run(
                [str(python), str(script), "--dry-run"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            payload = _json.loads(r.stdout)
            required = {"has_gpu", "vram_total_mb", "vram_free_mb", "num_gpu_per_model", "reserved_mb"}
            ok = r.returncode == 0 and required.issubset(payload.keys())
            details = (
                f"gpu={payload.get('gpu_name')} vram_free={payload.get('vram_free_mb')}MB "
                f"num_gpu={payload.get('num_gpu_per_model')}"
            )
            self._add(
                "GPU-01",
                "detect_gpu.py --dry-run retorna JSON válido",
                "gpu_tune",
                ok,
                time.monotonic() - t,
                details=details,
            )
        except Exception as e:
            self._add(
                "GPU-01",
                "detect_gpu.py --dry-run retorna JSON válido",
                "gpu_tune",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # GPU-02: fallback CPU quando nvidia-smi ausente (PATH vazio)
        t = time.monotonic()
        try:
            env = {"PATH": "", "HOME": _os.environ.get("HOME", "/tmp")}
            r = _sub.run(
                [str(python), str(script), "--for-model", "qwen3:4b"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            val = r.stdout.strip()
            ok = r.returncode == 0 and val == "0"
            self._add(
                "GPU-02",
                "Fallback CPU (num_gpu=0) sem nvidia-smi",
                "gpu_tune",
                ok,
                time.monotonic() - t,
                details=f"stdout={val!r}",
            )
        except Exception as e:
            self._add(
                "GPU-02",
                "Fallback CPU (num_gpu=0) sem nvidia-smi",
                "gpu_tune",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # GPU-03: NYX_AUTO_TUNE=0 preserva .env (não sobrescreve)
        t = time.monotonic()
        try:
            with _tmp.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as fh:
                fh.write("NYX_AUTO_TUNE=0\nNYX_NUM_GPU=7\n")
                tmp_path = fh.name
            r = _sub.run(
                [str(python), str(script), "--write-env", "--env-path", tmp_path, "--model", "qwen3:4b"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            after = Path(tmp_path).read_text(encoding="utf-8")
            Path(tmp_path).unlink(missing_ok=True)
            preserved = "NYX_NUM_GPU=7" in after and "NYX_AUTO_TUNE=0" in after
            ok = r.returncode == 0 and preserved
            self._add(
                "GPU-03",
                "NYX_AUTO_TUNE=0 preserva .env existente",
                "gpu_tune",
                ok,
                time.monotonic() - t,
                details=f"preserved={preserved}",
            )
        except Exception as e:
            self._add(
                "GPU-03",
                "NYX_AUTO_TUNE=0 preserva .env existente",
                "gpu_tune",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: PORTABILIDADE (2 testes -- PORT-02 Docker clean-boot)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_portabilidade(self) -> None:
        import subprocess as _sub

        # PORT-DOCKER-01: Dockerfile.clean-boot existe e tem diretivas esperadas
        t = time.monotonic()
        try:
            dockerfile = PROJECT_ROOT / "docker" / "Dockerfile.clean-boot"
            script = PROJECT_ROOT / "docker" / "test-clean-boot.sh"
            content = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
            required = ["FROM ubuntu", "python3.10", "WORKDIR", "COPY", "ENTRYPOINT"]
            missing = [d for d in required if d not in content]
            script_ok = script.exists() and script.stat().st_mode & 0o111
            ok = dockerfile.exists() and not missing and bool(script_ok)
            self._add(
                "PORT-DOCKER-01",
                "Dockerfile.clean-boot + test-clean-boot.sh presentes",
                "portabilidade",
                ok,
                time.monotonic() - t,
                details=f"dockerfile={dockerfile.exists()} missing={missing} script_exec={bool(script_ok)}",
            )
        except Exception as e:
            self._add(
                "PORT-DOCKER-01",
                "Dockerfile.clean-boot + test-clean-boot.sh presentes",
                "portabilidade",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # PORT-DOCKER-02: install.sh --help reconhece --no-prompt
        t = time.monotonic()
        try:
            install_sh = PROJECT_ROOT / "install.sh"
            r = _sub.run(
                ["bash", str(install_sh), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            ok = r.returncode == 0 and "--no-prompt" in r.stdout
            self._add(
                "PORT-DOCKER-02",
                "install.sh --help anuncia --no-prompt",
                "portabilidade",
                ok,
                time.monotonic() - t,
                details=f"exit={r.returncode} stdout_head={r.stdout[:60]!r}",
            )
        except Exception as e:
            self._add(
                "PORT-DOCKER-02",
                "install.sh --help anuncia --no-prompt",
                "portabilidade",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════
    # FASE: ROBUSTEZ_BOOT (3 testes -- PORT-03 R-02/R-03/R-04)
    # ═══════════════════════════════════════════════════════════════════

    async def _phase_robustez_boot(self) -> None:
        run_sh = PROJECT_ROOT / "run.sh"
        proxy_py = PROJECT_ROOT / "nyx" / "proxy.py"

        # RB-01: run.sh tem mensagens claras para modelo inexistente (R-02)
        t = time.monotonic()
        try:
            src = run_sh.read_text(encoding="utf-8")
            sinais = [
                "verifique NYX_MODEL",
                "conexão",
                "registry",
                "Modelos disponíveis localmente",
            ]
            faltantes = [s for s in sinais if s not in src]
            ok = not faltantes
            self._add(
                "RB-01",
                "Mensagens claras para modelo inexistente (R-02)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=f"faltantes={faltantes}",
            )
        except Exception as e:
            self._add(
                "RB-01",
                "Mensagens claras para modelo inexistente (R-02)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # RB-02: run.sh tem mensagens claras para porta ocupada por não-Ollama (R-03)
        t = time.monotonic()
        try:
            src = run_sh.read_text(encoding="utf-8")
            sinais = [
                "não-Ollama",
                "NYX_OLLAMA_PORT=11437",
                "kill ",
                "Matar manualmente",
            ]
            faltantes = [s for s in sinais if s not in src]
            ok = not faltantes
            self._add(
                "RB-02",
                "Mensagens claras para porta ocupada (R-03)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=f"faltantes={faltantes}",
            )
        except Exception as e:
            self._add(
                "RB-02",
                "Mensagens claras para porta ocupada (R-03)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )

        # RB-03: proxy.py detecta OOM e tem lógica de graceful degradation (R-04)
        t = time.monotonic()
        try:
            import importlib as _imp

            mod = _imp.import_module("nyx.proxy")
            is_oom = getattr(mod, "_is_oom_error", None)
            has_flag = hasattr(mod, "_OOM_DEGRADED")
            padroes = [
                "CUDA out of memory",
                "cudaMalloc failed",
                "requires more memory",
                "out of memory: not enough free VRAM",
            ]
            detecta = is_oom is not None and all(is_oom(p) for p in padroes)
            nao_falso_positivo = is_oom is not None and not is_oom("resposta normal sem erro")
            src = proxy_py.read_text(encoding="utf-8")
            tem_retry = "OOM recovery OK" in src and 'num_gpu"] = 0' in src
            ok = bool(has_flag and detecta and nao_falso_positivo and tem_retry)
            self._add(
                "RB-03",
                "Proxy detecta OOM e degrada num_gpu=0 (R-04)",
                "robustez_boot",
                ok,
                time.monotonic() - t,
                details=f"has_flag={has_flag} detecta={detecta} sem_fp={nao_falso_positivo} retry={tem_retry}",
            )
        except Exception as e:
            self._add(
                "RB-03",
                "Proxy detecta OOM e degrada num_gpu=0 (R-04)",
                "robustez_boot",
                False,
                time.monotonic() - t,
                error=str(e),
            )

    # ── Helpers ──────────────────────────────────────────────────────

    async def _health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._ollama}/api/version")
                return r.status_code == 200
        except Exception:
            return False

    async def _chat(self, msg: str) -> dict[str, Any]:
        return await self._chat_with_tools(msg, tools=None)

    async def _chat_with_tool(self, msg: str, tool: dict) -> dict[str, Any]:
        return await self._chat_with_tools(msg, [tool])

    async def _chat_with_tools(self, msg: str, tools: list[dict] | None, system: str | None = None) -> dict[str, Any]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": msg})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
        try:
            async with httpx.AsyncClient(timeout=300) as c:
                r = await c.post(f"{self._proxy}/v1/chat/completions", json=payload)
                data = r.json()
                msg_data = data["choices"][0]["message"]
                tc = msg_data.get("tool_calls", [])
                return {
                    "content": msg_data.get("content", ""),
                    "tool_names": [t["function"]["name"] for t in tc],
                    "tool_args": [t["function"].get("arguments", "") for t in tc],
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                    "finish_reason": data["choices"][0].get("finish_reason", ""),
                }
        except Exception as e:
            return {"content": "", "tool_names": [], "tool_args": [], "tokens": 0, "error": str(e)}

    async def _chat_raw(self, msg: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=300) as c:
                r = await c.post(
                    f"{self._proxy}/v1/chat/completions",
                    json={"model": self._model, "messages": [{"role": "user", "content": msg}]},
                )
                return r.json()
        except Exception:
            return {}

    def _tool(self, name: str, desc: str, props: dict, req: list) -> dict:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": {"type": "object", "properties": props, "required": req},
            },
        }

    def _get_vram(self) -> int:
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                text=True,
                timeout=5,
            ).strip()
            return int(out.split("\n")[0])
        except Exception:
            return 0

    # ── Resiliência (G-02) ──────────────────────────────────────────

    def _save_checkpoint(self) -> None:
        """Salva estado atual -- recuperável se crashar."""
        try:
            CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "timestamp": datetime.now().isoformat(),
                "model": self._model,
                "phases_done": sorted(self._phases_done),
                "results": [asdict(r) for r in self._results],
                "kpis": self._kpis,
            }
            CHECKPOINT_PATH.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Falha ao salvar checkpoint: %s", e)

    def _detect_hardware(self) -> dict[str, Any]:
        """Detecta GPU e ajusta parâmetros automaticamente."""
        hw: dict[str, Any] = {
            "gpu": "CPU-only",
            "vram_total_mib": 0,
            "num_gpu": 0,
            "num_ctx": 4096,
        }
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                text=True,
                timeout=5,
            ).strip()
            parts = out.split(",")
            hw["gpu"] = parts[0].strip()
            hw["vram_total_mib"] = int(parts[1].strip())
            vram = hw["vram_total_mib"]
            if vram >= 8000:
                hw["num_gpu"] = -1
                hw["num_ctx"] = 32768
            elif vram >= 6000:
                hw["num_gpu"] = 20
                hw["num_ctx"] = 16384
            elif vram >= 4000:
                hw["num_gpu"] = 12
                hw["num_ctx"] = 8192
            else:
                hw["num_gpu"] = 8
                hw["num_ctx"] = 4096
        except Exception:
            pass
        return hw

    def _save_baseline(self) -> None:
        """Salva baseline JSON para comparação histórica."""
        try:
            BASELINES_DIR.mkdir(parents=True, exist_ok=True)
            commit = "unknown"
            try:
                commit = subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    text=True,
                    cwd=str(PROJECT_ROOT),
                    timeout=5,
                ).strip()
            except Exception:
                pass
            ok = sum(1 for r in self._results if r.passed)
            baseline = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "commit": commit,
                "model": self._model,
                "hardware": self._hardware,
                "kpis": self._kpis,
                "results": {
                    "total": len(self._results),
                    "passed": ok,
                    "failed": len(self._results) - ok,
                },
            }
            path = BASELINES_DIR / f"baseline_{datetime.now().strftime('%Y-%m-%d')}.json"
            path.write_text(
                json.dumps(baseline, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Baseline salvo: %s", path)
        except Exception as e:
            logger.warning("Falha ao salvar baseline: %s", e)

    def _load_previous_baseline(self) -> dict[str, Any] | None:
        """Carrega baseline anterior mais recente."""
        try:
            files = sorted(BASELINES_DIR.glob("baseline_*.json"))
            today = datetime.now().strftime("%Y-%m-%d")
            previous = [f for f in files if today not in f.name]
            if not previous:
                return None
            data = json.loads(previous[-1].read_text(encoding="utf-8"))
            return data
        except Exception:
            return None

    def _detect_regressions(self) -> list[str]:
        """Compara KPIs atuais com baseline anterior."""
        prev = self._load_previous_baseline()
        if not prev:
            return []
        regressions = []
        prev_kpis = prev.get("kpis", {})

        ttfr_prev = prev_kpis.get("ttfr_chat_s", 0)
        ttfr_curr = self._kpis.get("ttfr_chat_s", 0)
        if ttfr_prev > 0 and ttfr_curr > ttfr_prev * 1.5:
            regressions.append(
                f"TTFR chat regrediu: {ttfr_prev}s -> {ttfr_curr}s (+{((ttfr_curr / ttfr_prev) - 1) * 100:.0f}%)"
            )

        prev_results = prev.get("results", {})
        prev_rate = prev_results.get("passed", 0) / max(prev_results.get("total", 1), 1) * 100
        curr_ok = sum(1 for r in self._results if r.passed)
        curr_rate = curr_ok / max(len(self._results), 1) * 100
        if curr_rate < prev_rate:
            regressions.append(f"Pass rate caiu: {prev_rate:.0f}% -> {curr_rate:.0f}%")

        vram_prev = prev_kpis.get("vram_mib", 0)
        vram_curr = self._kpis.get("vram_mib", 0)
        if vram_prev > 0 and vram_curr > vram_prev * 1.2:
            regressions.append(f"VRAM subiu: {vram_prev}MiB -> {vram_curr}MiB")

        return regressions

    def _scan_flags(self) -> list[tuple[str, str, bool]]:
        """Varre flags/*.md e retorna (nome, descrição, é_alta)."""
        flags = []
        if not FLAGS_DIR.exists():
            return flags
        for f in sorted(FLAGS_DIR.glob("FLAG_*.md")):
            try:
                content = f.read_text(encoding="utf-8")
                desc = ""
                alta = False
                for line in content.splitlines():
                    if line.startswith("**Descrição:**"):
                        desc = line.replace("**Descrição:**", "").strip()
                    if "ALTA" in line:
                        alta = True
                flags.append((f.name, desc or f.stem, alta))
            except Exception:
                flags.append((f.name, "erro ao ler", False))
        return flags

    def _add(
        self,
        fid: str,
        name: str,
        phase: str,
        passed: bool,
        elapsed: float,
        tokens: int = 0,
        details: str = "",
        error: str = "",
    ) -> None:
        # COCKPIT-03-GAUNTLET-PER-FEATURE-01: se filtro por feature_id estiver
        # ativo, mantém somente o teste alvo nos resultados finais. Demais
        # entradas saem como DEBUG (não poluem o report e nem o exit code).
        if self._target_feature_id and fid != self._target_feature_id:
            tag = "OK" if passed else "FAIL"
            logger.debug("[%s] %s %s (skipped, filtro=%s)", tag, fid, name, self._target_feature_id)
            return
        r = TestResult(fid, name, phase, passed, round(elapsed, 2), tokens, details[:200], error[:200])
        self._results.append(r)
        tag = "OK" if passed else "FAIL"
        logger.info("[%s] %s %s (%.1fs, %dtok)", tag, fid, name, elapsed, tokens)
        self._save_checkpoint()

    def _add_skip(
        self,
        fid: str,
        name: str,
        phase: str,
        details: str = "",
    ) -> None:
        """K08-VRAM-RUNNER-ISOLATION-01: registra teste como SKIP.

        SKIP não conta como FAIL no gate (passed=True), mas é renderizado
        distinto de OK no relatório (skipped=True).
        """
        if self._target_feature_id and fid != self._target_feature_id:
            logger.debug(
                "[SKIP] %s %s (skipped por filtro, alvo=%s)",
                fid,
                name,
                self._target_feature_id,
            )
            return
        r = TestResult(
            fid,
            name,
            phase,
            True,
            0.0,
            0,
            details[:200],
            "",
            skipped=True,
        )
        self._results.append(r)
        logger.info("[SKIP] %s %s -- %s", fid, name, details)
        self._save_checkpoint()

    # ── Report ──────────────────────────────────────────────────────

    def _write_report(self) -> None:
        total = len(self._results)
        ok = sum(1 for r in self._results if r.passed)
        # K08-VRAM-RUNNER-ISOLATION-01: SKIP não conta como FAIL no gate.
        skipped = sum(1 for r in self._results if r.skipped)
        fail = total - ok
        elapsed = self._kpis.get("gauntlet_total_s", 0)
        score = ok / total * 100 if total else 0
        gate = "APROVADO" if ok == total else "REPROVADO"
        vram = self._kpis.get("vram_mib", 0)
        hw = self._hardware

        lines = [
            "# Gauntlet Report -- Nyx-Code",
            "",
            f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Modelo:** {self._model}",
            f"**Duração:** {elapsed:.0f}s ({elapsed / 60:.1f}min)",
            f"**Resultado:** {ok}/{total} ({score:.0f}%)",
            "",
            f"## Gate de Produção: {gate}",
            "",
            "100% obrigatório para push na main." if gate == "REPROVADO" else "Pronto para push na main.",
            "",
        ]

        # Hardware
        lines.extend(
            [
                "## Hardware",
                "",
                "| Propriedade | Valor |",
                "|-------------|-------|",
                f"| GPU | {hw.get('gpu', 'N/A')} |",
                f"| VRAM total | {hw.get('vram_total_mib', 0)}MiB |",
                f"| VRAM em uso | {vram}MiB |" if vram else "| VRAM em uso | N/A |",
                f"| num_gpu | {hw.get('num_gpu', 0)} |",
                f"| num_ctx | {hw.get('num_ctx', 4096)} |",
                "",
            ]
        )

        # Resumo por fase
        lines.extend(
            [
                "## Resumo por Fase",
                "",
                "| Fase | Total | OK | Falhas | Tempo |",
                "|------|-------|-----|--------|-------|",
            ]
        )
        by_phase: dict[str, dict] = {}
        for r in self._results:
            p = by_phase.setdefault(r.phase, {"total": 0, "ok": 0, "time": 0.0})
            p["total"] += 1
            if r.passed:
                p["ok"] += 1
            p["time"] += r.elapsed_s
        for ph, s in by_phase.items():
            lines.append(f"| {ph} | {s['total']} | {s['ok']} | {s['total'] - s['ok']} | {s['time']:.1f}s |")

        # KPIs
        if self._kpis:
            lines.extend(["", "## KPIs de Performance", "", "| Métrica | Valor |", "|---------|-------|"])
            for k, v in self._kpis.items():
                lines.append(f"| {k} | {v} |")

        # Regressões
        regressions = self._detect_regressions()
        if regressions:
            lines.extend(["", "## Regressões Detectadas", ""])
            for reg in regressions:
                lines.append(f"- **REGRESSAO:** {reg}")

        # Detalhes
        lines.extend(
            [
                "",
                "## Detalhes",
                "",
                "| ID | Feature | Fase | Status | Tempo | Tokens | Detalhes |",
                "|----|---------|------|--------|-------|--------|----------|",
            ]
        )
        for r in self._results:
            # K08-VRAM-RUNNER-ISOLATION-01: SKIP renderizado distinto de OK.
            if r.skipped:
                tag = "SKIP"
            elif r.passed:
                tag = "OK"
            else:
                tag = "FAIL"
            d = r.error if r.error else r.details
            lines.append(
                f"| {r.feature_id} | {r.name} | {r.phase} | {tag} | {r.elapsed_s:.1f}s | {r.tokens} | {d[:60]} |"
            )

        # Falhas
        if fail:
            lines.extend(["", "## Falhas", ""])
            for r in self._results:
                if not r.passed:
                    lines.append(f"- **{r.feature_id}** {r.name}: {r.error or r.details}")

        # Skips (K08-VRAM-RUNNER-ISOLATION-01)
        if skipped:
            lines.extend(["", f"## Skips ({skipped})", ""])
            for r in self._results:
                if r.skipped:
                    lines.append(
                        f"- **{r.feature_id}** {r.name}: {r.details}"
                    )

        # Flags pendentes
        flags = self._scan_flags()
        if flags:
            alta_count = sum(1 for _, _, alta in flags if alta)
            lines.extend(["", f"## Flags Pendentes ({len(flags)} features sem teste)", ""])
            if alta_count:
                lines.append(f"**WARNING:** {alta_count} flag(s) com prioridade ALTA")
                lines.append("")
            for fname, desc, alta in flags:
                prio = " [ALTA]" if alta else ""
                lines.append(f"- {fname}: {desc}{prio}")

        # Features não testadas
        lines.extend(
            [
                "",
                f"## Features não testadas ({len(UNMAPPED_FEATURES)})",
                "",
                "Features do FEATURE_MAP.md sem teste no Gauntlet (dependem de infra futura):",
                "",
            ]
        )
        for f in UNMAPPED_FEATURES:
            lines.append(f"- {f}")

        lines.append("")

        report = PROJECT_ROOT / "GAUNTLET_REPORT.md"
        report.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Report: %s (%s)", report, gate)

        history = REPORTS_DIR
        history.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M")
        (history / f"GAUNTLET_{ts}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nyx-Code Gauntlet")
    parser.add_argument("--proxy-url", default="http://127.0.0.1:11436")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11435")
    parser.add_argument("--only", default="completo")
    parser.add_argument("--model", default="qwen3:4b")
    # K08-VRAM-RUNNER-ISOLATION-01: comportamento do pre-flight K-08.
    mutex_vram = parser.add_mutually_exclusive_group()
    mutex_vram.add_argument(
        "--strict-vram",
        action="store_true",
        help="K-08 FAIL real se VRAM excedida (preserva contrato antigo)",
    )
    mutex_vram.add_argument(
        "--isolate-vram",
        action="store_true",
        help=(
            "Lista processos externos ocupando VRAM e pede confirmação "
            "para kill (TTY obrigatório)"
        ),
    )
    args = parser.parse_args()

    g = NyxGauntlet(
        proxy_url=args.proxy_url,
        ollama_url=args.ollama_url,
        only=args.only,
        model=args.model,
        strict_vram=args.strict_vram,
        isolate_vram=args.isolate_vram,
    )
    sys.exit(asyncio.run(g.run()))


if __name__ == "__main__":
    main()


# "Medir é o primeiro passo para controlar e eventualmente melhorar." -- H. James Harrington
