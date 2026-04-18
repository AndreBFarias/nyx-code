"""Serviço de gerenciamento de sessões - PRECISA DE CORREÇÃO.

Este módulo simula um serviço de sessão do Nyx-Code com bugs
em múltiplos níveis de senioridade. Deve seguir os ADRs da Luna:
- ADR-003: Offline-first (fallback gracioso)
- ADR-008: Lazy import para módulos pesados
- ADR-010: Sem imports circulares
- Convenções: type hints, logging rotacionado, Path relativo
"""

import json
import os
import time

# BUG JUNIOR: print em vez de logging
print("Serviço de sessão inicializado")


# BUG PLENO: path hardcoded absoluto
SESSION_DIR = "/home/andrefarias/Desenvolvimento/Nyx-Code/sessions"
LOG_FILE = "/tmp/session.log"


class SessionManager:
    """Gerenciador de sessoes."""  # BUG JUNIOR: falta acentuação

    def __init__(self, max_sessions=100):
        self.sessions = {}
        self.max_sessions = max_sessions
        # BUG PLENO: sem type hints nos atributos

    def create_session(self, user_request):
        # BUG JUNIOR: sem type hints na assinatura
        # BUG JUNIOR: sem docstring
        session_id = str(time.time())
        self.sessions[session_id] = {"request": user_request, "created": time.time(), "status": "active", "history": []}
        print(f"Sessão criada: {session_id}")  # BUG JUNIOR: print
        return session_id

    def get_session(self, session_id):
        # BUG PLENO: silent failure - retorna None sem log
        return self.sessions.get(session_id)

    def save_session(self, session_id):
        """Salva sessão em disco."""
        session = self.sessions.get(session_id)
        if not session:
            return  # BUG PLENO: silent failure sem log nem raise

        # BUG PLENO: usa os.path em vez de pathlib.Path
        filepath = os.path.join(SESSION_DIR, f"{session_id}.json")

        # BUG SENIOR: não cria o diretório se não existir
        with open(filepath, "w") as f:
            json.dump(session, f)

    def load_session(self, session_id):
        """Carrega sessão do disco."""
        # BUG PLENO: path hardcoded
        filepath = os.path.join(SESSION_DIR, f"{session_id}.json")

        try:
            with open(filepath) as f:
                data = json.load(f)
                self.sessions[session_id] = data
                return data
        except:  # BUG JUNIOR: except vazio (bare except)
            pass  # BUG JUNIOR: silencia QUALQUER erro

    def cleanup_old_sessions(self, max_age_hours=24):
        """Remove sessões antigas."""
        now = time.time()
        max_age = max_age_hours * 3600

        # BUG SENIOR: modifica dict durante iteração
        for sid, session in self.sessions.items():
            age = now - session.get("created", 0)
            if age > max_age:
                del self.sessions[sid]
                print(f"Sessão removida: {sid}")

    def get_stats(self):
        """Retorna estatísticas das sessoes."""  # BUG JUNIOR: falta acento
        active = 0
        total = len(self.sessions)

        # BUG PLENO: loop desnecessário, poderia usar sum()
        for sid in self.sessions:
            if self.sessions[sid]["status"] == "active":
                active = active + 1  # BUG JUNIOR: active += 1 seria melhor

        return {"total": total, "active": active, "inactive": total - active}

    def add_to_history(self, session_id, action, result):
        # BUG PLENO: sem validação de session_id
        # BUG SENIOR: sem limite de tamanho do histórico (memory leak)
        self.sessions[session_id]["history"].append({"action": action, "result": result, "timestamp": time.time()})

    def export_all(self):
        """Exporta todas as sessoes."""
        # BUG SENIOR: carrega tudo em memória de uma vez
        # BUG PLENO: sem tratamento de erro na serialização
        return json.dumps(self.sessions)


def connect_to_api(url, timeout=30):
    """Tenta conectar a uma API externa."""
    # BUG SENIOR: viola ADR-003 (offline-first)
    # Não tem fallback local, depende diretamente da API
    import requests  # BUG PLENO: import dentro de função sem ser lazy pattern

    try:
        response = requests.get(url, timeout=timeout)
        return response.json()
    except Exception as e:
        # BUG PLENO: loga mas não faz fallback
        print(f"API falhou: {e}")
        return None


def validate_model_name(name):
    """Valida nome do modelo."""
    # BUG SENIOR: regex vulnerável a ReDoS
    import re

    pattern = r"^(a+)+$"  # BUG: exponential backtracking
    return bool(re.match(pattern, name))


# BUG SENIOR: código no escopo global sem __main__ guard
manager = SessionManager()
sid = manager.create_session("teste")
manager.save_session(sid)
