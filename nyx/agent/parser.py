"""ActionParser -- Extrai ações estruturadas da resposta do LLM.

7 níveis de fallback (port da Luna src/skills/code_agent/parser.py):
  Nível 1 (EXACT): Parse dos blocos ACTION/PATH/etc com separador ---
  Nível 2 (FUNCTION_CALL): tool_name("path") ou tool_name(path="value")
  Nível 3 (RELAXED): Regex relaxado (minúsculas, sem ---)
  Nível 4 (BARE_TOOL): tool_name path/to/file (sem parênteses)
  Nível 5 (CODE_BLOCK): Extrai code blocks markdown como create_file
  Nível 6 (PATH_INTENT): "Vou ler o arquivo X" -> read_file
  Nível 7 (IMPLICIT_DONE): "pronto", "concluído", etc
"""

from __future__ import annotations

import json
import logging
import re

from .models import ActionType, AgentAction, ParseLevel, ParseResult

logger = logging.getLogger("nyx.parser")

_ACTION_ALIASES: dict[str, ActionType] = {
    "read_file": ActionType.READ_FILE,
    "read": ActionType.READ_FILE,
    "ler": ActionType.READ_FILE,
    "ler_arquivo": ActionType.READ_FILE,
    "search": ActionType.SEARCH,
    "grep": ActionType.SEARCH,
    "find": ActionType.SEARCH,
    "buscar": ActionType.SEARCH,
    "busca": ActionType.SEARCH,
    "list_files": ActionType.LIST_FILES,
    "list": ActionType.LIST_FILES,
    "ls": ActionType.LIST_FILES,
    "listar": ActionType.LIST_FILES,
    "listar_arquivos": ActionType.LIST_FILES,
    "edit_file": ActionType.EDIT_FILE,
    "edit": ActionType.EDIT_FILE,
    "editar": ActionType.EDIT_FILE,
    "editar_arquivo": ActionType.EDIT_FILE,
    "create_file": ActionType.CREATE_FILE,
    "create": ActionType.CREATE_FILE,
    "criar": ActionType.CREATE_FILE,
    "criar_arquivo": ActionType.CREATE_FILE,
    "write_file": ActionType.WRITE_FILE,
    "write": ActionType.WRITE_FILE,
    "escrever": ActionType.WRITE_FILE,
    "sobrescrever": ActionType.WRITE_FILE,
    "run_command": ActionType.RUN_COMMAND,
    "run": ActionType.RUN_COMMAND,
    "execute": ActionType.RUN_COMMAND,
    "executar": ActionType.RUN_COMMAND,
    "rodar": ActionType.RUN_COMMAND,
    "comando": ActionType.RUN_COMMAND,
    "done": ActionType.DONE,
    "finish": ActionType.DONE,
    "concluido": ActionType.DONE,
    "concluído": ActionType.DONE,
    "concluir": ActionType.DONE,
    "pronto": ActionType.DONE,
    "feito": ActionType.DONE,
    "analyze": ActionType.ANALYZE,
    "analyse": ActionType.ANALYZE,
    "analisar": ActionType.ANALYZE,
    "glob": ActionType.GLOB,
    "glob_files": ActionType.GLOB,
    "find_files": ActionType.GLOB,
    "patch": ActionType.PATCH,
    "apply_patch": ActionType.PATCH,
    "aplicar_patch": ActionType.PATCH,
    "todo_write": ActionType.TODO_WRITE,
    "todo": ActionType.TODO_WRITE,
    "tarefas": ActionType.TODO_WRITE,
    "web_fetch": ActionType.WEB_FETCH,
    "fetch": ActionType.WEB_FETCH,
    "buscar_url": ActionType.WEB_FETCH,
    "web_search": ActionType.WEB_SEARCH,
    "pesquisar": ActionType.WEB_SEARCH,
    "buscar_web": ActionType.WEB_SEARCH,
}

_EXACT_BLOCK = re.compile(
    r"ACTION:\s*(\w+)\s*([^\n]*)\n(.*?)(?:^---\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)

_RELAXED_BLOCK = re.compile(
    r"(?:action|Action|ACTION)\s*[:=]\s*(\w+)\s*([^\n]*)\n(.*?)(?:\n\s*\n|\n---\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)

_INLINE_PATH = re.compile(
    r"((?:src|tests|scripts|app|lib|utils|config|nyx)[\w/]*\.[\w]+|"
    r"[\w./]+\.(?:py|js|ts|json|yaml|toml|md|sh)|"
    r"(?:src|tests|scripts|app|lib|utils|config|nyx)/[\w/]*)",
)

_FUNCTION_CALL = re.compile(
    r"\b(\w+)\s*\(\s*"
    r"(?:(?:path|file|arquivo)\s*=\s*)?"
    r'["\']?([^\s"\'\),]+\.[\w]+)["\']?'
    r"\s*\)",
    re.IGNORECASE,
)

_FUNCTION_CALL_CMD = re.compile(
    r"\b(run_command|run|executar|rodar|comando)\s*\(\s*"
    r'["\']?(.+?)["\']?\s*\)',
    re.IGNORECASE,
)

_FUNCTION_CALL_DONE = re.compile(
    r"\b(done|pronto|feito|concluido|concluído)\s*\(\s*"
    r'["\']?(.+?)["\']?\s*\)',
    re.IGNORECASE,
)

_BARE_TOOL_NAMES = (
    "read_file|read|ler|search|grep|buscar|list_files|list|ls|listar|"
    "edit_file|edit|create_file|create|write_file|write|"
    "glob|analyze|analisar|run_command|run|done"
)
_BARE_TOOL = re.compile(
    rf"^\s*({_BARE_TOOL_NAMES})\s+(\S.+?)$",
    re.MULTILINE | re.IGNORECASE,
)

_PATH_INTENT_READ = re.compile(
    r"(?:vou|preciso|quero|vamos|deixa|let me|i will|i need to)\s+"
    r"(?:ler|verificar|abrir|olhar|checar|examinar|read|check|open|look at)\s+"
    r"(?:o\s+)?(?:arquivo\s+)?(?:em\s+)?"
    r"(\S+\.(?:py|js|ts|json|yaml|yml|toml|cfg|txt|md|sh))",
    re.IGNORECASE,
)

_PATH_INTENT_CREATE = re.compile(
    r"(?:vou|preciso|quero|vamos|let me|i will)\s+"
    r"(?:criar|escrever|gerar|create|write|generate)\s+"
    r"(?:o\s+)?(?:arquivo\s+)?(?:em\s+)?"
    r"(\S+\.(?:py|js|ts|json|yaml|yml|toml|cfg|txt|md|sh))",
    re.IGNORECASE,
)

_PARAM_LINE = re.compile(
    r"^(PATH|PATTERN|CMD|SEARCH|REPLACE|CONTENT|SUMMARY|MAX_DEPTH|DIFF|START_LINE|END_LINE)"
    r"\s*:\s*(.*?)$",
    re.MULTILINE,
)

_PARAM_LINE_RELAXED = re.compile(
    r"^(path|pattern|cmd|search|replace|content|summary|max_depth|diff|start_line|end_line)"
    r"\s*[:=]\s*(.*?)$",
    re.MULTILINE | re.IGNORECASE,
)

_MULTILINE_PARAMS = {"SEARCH", "REPLACE", "CONTENT", "SUMMARY", "DIFF"}

_CODE_BLOCK = re.compile(
    r"```(\w*)\n(.*?)```",
    re.DOTALL,
)

_DONE_KEYWORDS = re.compile(
    r"\b(pronto|concluido|concluída|concluído|tarefa completa|corrigi|arquivo criado|"
    r"arquivos criados|feito|terminei|implementei|resolvi|corrigido|"
    r"completo|completei|finalizado|finalizada)\b",
    re.IGNORECASE,
)

_QUESTION_PATTERNS = re.compile(
    r"\?\s*$|"
    r"\b(preciso|devo|posso|qual|quais|como|onde|quando)\b.*\?",
    re.IGNORECASE | re.MULTILINE,
)

_CONTINUATION_PATTERNS = re.compile(
    r"\b(mas ainda|porem|falta|preciso|antes disso|agora vou|"
    r"proximo passo|em seguida|depois|tambem preciso|"
    r"resta|faltam|nao terminei|incompleto)\b",
    re.IGNORECASE,
)

_STARTS_CONCLUSIVE = re.compile(
    r"^(pronto|concluido|concluído|concluida|concluída|feito|terminei|completo|completei|"
    r"finalizado|finalizada)\b",
    re.IGNORECASE,
)


class ActionParser:
    def __init__(self) -> None:
        self._parse_counts: dict[ParseLevel, int] = {level: 0 for level in ParseLevel}
        self._total_attempts = 0
        self._total_failures = 0

    def parse(self, llm_response: str) -> ParseResult:
        self._total_attempts += 1

        for method, level in [
            (self._parse_exact, ParseLevel.EXACT),
            (self._parse_json_tool_call, ParseLevel.FUNCTION_CALL),
            (self._parse_function_call, ParseLevel.FUNCTION_CALL),
            (self._parse_relaxed, ParseLevel.RELAXED),
            (self._parse_bare_tool, ParseLevel.BARE_TOOL),
            (self._parse_code_block, ParseLevel.CODE_BLOCK),
            (self._parse_path_intent, ParseLevel.PATH_INTENT),
            (self._parse_implicit_done, ParseLevel.IMPLICIT_DONE),
        ]:
            result = method(llm_response)
            if result.success:
                self._parse_counts[level] += 1
                return result

        self._total_failures += 1
        logger.warning("Parse falhou em todos os níveis. Resposta: %s", llm_response[:200])

        return ParseResult(
            action=None,
            level=ParseLevel.EXACT,
            success=False,
            error="Nenhuma ação encontrada na resposta do modelo",
            raw_text=llm_response,
        )

    def _parse_json_tool_call(self, text: str) -> ParseResult:
        """Modelo emitiu tool_call como JSON no content.

        Aceita variações:
        - {"name":"read_file","arguments":{"path":"..."}}
        - {"tool":"read_file","args":{"path":"..."}}
        - {"function":"read_file","parameters":{"path":"..."}}
        """
        _fail = ParseResult(action=None, level=ParseLevel.FUNCTION_CALL, success=False)
        stripped = text.strip()

        # Encontrar JSON no texto -- extrair substring e tentar parsear
        data = None
        start = stripped.find("{")
        if start == -1:
            return _fail
        # Tentar parsear do início do JSON até vários pontos de fechamento
        candidate = stripped[start:]
        depth = 0
        for i, ch in enumerate(candidate):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(candidate[:i + 1])
                        break
                    except json.JSONDecodeError:
                        continue
        if data is None or not isinstance(data, dict):
            return _fail

        name = data.get("name") or data.get("tool") or data.get("function") or ""
        args = data.get("arguments") or data.get("args") or data.get("parameters") or {}

        # Modelo pode ter omitido o nome e mandado só os args -- inferir pela estrutura
        if not name:
            if "file_path" in data and "old_string" in data and "new_string" in data:
                name = "edit_file"
                args = data
            elif "file_path" in data and "content" in data:
                name = "write_file"
                args = data
            elif "file_path" in data or "path" in data:
                name = "read_file"
                args = data
            elif "command" in data or "cmd" in data:
                name = "run_command"
                args = data
            elif "pattern" in data:
                name = "search"
                args = data
            elif "summary" in data:
                name = "done"
                args = data
            else:
                return _fail
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"raw": args}
        if not isinstance(args, dict):
            args = {}

        action_type = _ACTION_ALIASES.get(name)
        if not action_type:
            return _fail

        params = {}
        for k, v in args.items():
            params[k] = str(v) if not isinstance(v, str) else v

        logger.info("JSON tool_call parse: %s(%s)", name, str(params)[:60])
        return ParseResult(
            action=AgentAction(action_type=action_type, params=params, raw_block=json.dumps(data)),
            level=ParseLevel.FUNCTION_CALL,
            success=True,
            raw_text=text,
        )

    def _parse_exact(self, text: str) -> ParseResult:
        match = _EXACT_BLOCK.search(text)
        if not match:
            return ParseResult(action=None, level=ParseLevel.EXACT, success=False)

        action_name = match.group(1).lower().strip()
        inline_extra = match.group(2).strip()
        body = match.group(3)

        action_type = _ACTION_ALIASES.get(action_name)
        if not action_type:
            return ParseResult(action=None, level=ParseLevel.EXACT, success=False,
                               error=f"Ação desconhecida: {action_name}")

        params = self._extract_params(body, strict=True)
        if "path" not in params and inline_extra:
            path_match = _INLINE_PATH.search(inline_extra)
            if path_match:
                params["path"] = path_match.group(1)

        return ParseResult(
            action=AgentAction(action_type=action_type, params=params, raw_block=match.group(0)),
            level=ParseLevel.EXACT,
            success=True,
            raw_text=text,
        )

    def _parse_function_call(self, text: str) -> ParseResult:
        _fail = ParseResult(action=None, level=ParseLevel.FUNCTION_CALL, success=False)

        for regex, param_key in [
            (_FUNCTION_CALL, "path"),
            (_FUNCTION_CALL_CMD, "cmd"),
            (_FUNCTION_CALL_DONE, "summary"),
        ]:
            match = regex.search(text)
            if not match:
                continue
            tool_name = match.group(1).lower().strip()
            action_type = _ACTION_ALIASES.get(tool_name)
            if not action_type:
                continue
            value = match.group(2).strip().strip("\"'")
            params = {param_key: value}
            logger.info("Function-call parse: %s(%s)", tool_name, value[:60])
            return ParseResult(
                action=AgentAction(action_type=action_type, params=params, raw_block=match.group(0)),
                level=ParseLevel.FUNCTION_CALL,
                success=True,
                raw_text=text,
            )
        return _fail

    def _parse_relaxed(self, text: str) -> ParseResult:
        match = _RELAXED_BLOCK.search(text)
        if not match:
            return ParseResult(action=None, level=ParseLevel.RELAXED, success=False)

        action_name = match.group(1).lower().strip()
        inline_extra = match.group(2).strip()
        body = match.group(3)

        action_type = _ACTION_ALIASES.get(action_name)
        if not action_type:
            return ParseResult(action=None, level=ParseLevel.RELAXED, success=False,
                               error=f"Ação desconhecida: {action_name}")

        params = self._extract_params(body, strict=False)
        if "path" not in params and inline_extra:
            path_match = _INLINE_PATH.search(inline_extra)
            if path_match:
                params["path"] = path_match.group(1)

        return ParseResult(
            action=AgentAction(action_type=action_type, params=params, raw_block=match.group(0)),
            level=ParseLevel.RELAXED,
            success=True,
            raw_text=text,
        )

    def _parse_bare_tool(self, text: str) -> ParseResult:
        _fail = ParseResult(action=None, level=ParseLevel.BARE_TOOL, success=False)
        match = _BARE_TOOL.search(text)
        if not match:
            return _fail

        tool_name = match.group(1).lower().strip()
        argument = match.group(2).strip()
        action_type = _ACTION_ALIASES.get(tool_name)
        if not action_type:
            return _fail

        if action_type == ActionType.DONE:
            params = {"summary": argument}
        elif action_type == ActionType.RUN_COMMAND:
            params = {"cmd": argument}
        elif action_type == ActionType.SEARCH:
            parts = argument.split(maxsplit=1)
            params = {"pattern": parts[0]}
            if len(parts) > 1:
                params["path"] = parts[1]
        else:
            params = {"path": argument}

        logger.info("Bare-tool parse: %s %s", tool_name, argument[:60])
        return ParseResult(
            action=AgentAction(action_type=action_type, params=params, raw_block=match.group(0)),
            level=ParseLevel.BARE_TOOL,
            success=True,
            raw_text=text,
        )

    def _parse_code_block(self, text: str) -> ParseResult:
        block_matches = list(_CODE_BLOCK.finditer(text))
        if not block_matches:
            return ParseResult(action=None, level=ParseLevel.CODE_BLOCK, success=False)

        _path_re = re.compile(
            r"(?:arquivo|file|path|em|criar|create)\s*[`:]?\s*([^\s`\n]+\.\w+)",
            re.IGNORECASE,
        )

        best_block = None
        best_path = ""

        for m in reversed(block_matches):
            preceding = text[max(0, m.start() - 200): m.start()]
            path_match = _path_re.search(preceding)
            if path_match:
                best_block = m
                best_path = path_match.group(1)
                break

        if not best_block:
            path_match = _path_re.search(text)
            best_path = path_match.group(1) if path_match else ""
            best_block = block_matches[-1]

        if not best_path:
            return ParseResult(action=None, level=ParseLevel.CODE_BLOCK, success=False,
                               error="Code block encontrado mas sem caminho de arquivo")

        lang = best_block.group(1)
        code = best_block.group(2)
        params = {"path": best_path, "content": code.strip()}

        return ParseResult(
            action=AgentAction(action_type=ActionType.CREATE_FILE, params=params,
                               raw_block=f"```{lang}\n{code}```"),
            level=ParseLevel.CODE_BLOCK,
            success=True,
            raw_text=text,
        )

    def _parse_path_intent(self, text: str) -> ParseResult:
        _fail = ParseResult(action=None, level=ParseLevel.PATH_INTENT, success=False)

        match_read = _PATH_INTENT_READ.search(text)
        if match_read:
            path = match_read.group(1).strip()
            logger.info("Path-intent read: %s", path)
            return ParseResult(
                action=AgentAction(action_type=ActionType.READ_FILE, params={"path": path},
                                   raw_block=match_read.group(0)),
                level=ParseLevel.PATH_INTENT,
                success=True,
                raw_text=text,
            )

        match_create = _PATH_INTENT_CREATE.search(text)
        if match_create:
            path = match_create.group(1).strip()
            logger.info("Path-intent create: %s", path)
            return ParseResult(
                action=AgentAction(action_type=ActionType.CREATE_FILE, params={"path": path, "content": ""},
                                   raw_block=match_create.group(0)),
                level=ParseLevel.PATH_INTENT,
                success=True,
                raw_text=text,
            )
        return _fail

    def _parse_implicit_done(self, text: str) -> ParseResult:
        stripped = text.strip()
        _fail = ParseResult(action=None, level=ParseLevel.IMPLICIT_DONE, success=False)

        if not stripped:
            return _fail
        if _QUESTION_PATTERNS.search(stripped):
            return _fail
        if _CONTINUATION_PATTERNS.search(stripped):
            return _fail
        if _PATH_INTENT_READ.search(stripped) or _PATH_INTENT_CREATE.search(stripped):
            return _fail
        if re.search(r"\bACTION\s*[:=]", stripped, re.IGNORECASE):
            return _fail

        done_matches = list(_DONE_KEYWORDS.finditer(stripped))
        if not done_matches:
            return _fail

        starts_conclusive = bool(_STARTS_CONCLUSIVE.match(stripped))
        if not starts_conclusive and len(stripped) >= 100 and len(done_matches) < 2:
            return _fail

        summary = stripped[:300]
        logger.info("Implicit done detectado: %s", summary[:80])
        return ParseResult(
            action=AgentAction(action_type=ActionType.DONE, params={"summary": summary},
                               raw_block=stripped),
            level=ParseLevel.IMPLICIT_DONE,
            success=True,
            raw_text=text,
        )

    def _extract_params(self, body: str, strict: bool = True) -> dict[str, str]:
        params: dict[str, str] = {}
        pattern = _PARAM_LINE if strict else _PARAM_LINE_RELAXED
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = pattern.match(line)
            if m:
                key = m.group(1).upper()
                raw_value = m.group(2)

                if key in _MULTILINE_PARAMS:
                    first_line = raw_value.rstrip("\n") if raw_value.strip() else ""
                    multiline_parts = [first_line] if first_line else []
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if pattern.match(next_line) or next_line.strip() == "---":
                            break
                        multiline_parts.append(next_line)
                        i += 1
                    value = "\n".join(multiline_parts)
                else:
                    value = raw_value.strip()

                params[key.lower()] = value
            else:
                i += 1
                continue
            if key not in _MULTILINE_PARAMS:
                i += 1
        return params

    def reset_stats(self) -> None:
        self._parse_counts = {level: 0 for level in ParseLevel}
        self._total_attempts = 0
        self._total_failures = 0

    @property
    def success_rate(self) -> float:
        if self._total_attempts == 0:
            return 0.0
        return 1.0 - (self._total_failures / self._total_attempts)

    @property
    def stats(self) -> dict[str, int | float]:
        return {
            "total_attempts": self._total_attempts,
            "total_failures": self._total_failures,
            "success_rate": self.success_rate,
            **{f"{level.value}_parses": self._parse_counts[level] for level in ParseLevel},
        }


# "A arte de ouvir é tão importante quanto a arte de falar." -- Epicteto
