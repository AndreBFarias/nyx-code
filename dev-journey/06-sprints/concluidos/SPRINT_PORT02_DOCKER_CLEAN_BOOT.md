## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PORT-02
  title: "Teste de máquina limpa via Docker"
  touches:
    - path: docker/Dockerfile.clean-boot
      reason: "Imagem mínima Ubuntu para simular máquina nova"
    - path: docker/test-clean-boot.sh
      reason: "Script que builda imagem, roda install.sh e Gauntlet"
    - path: install.sh
      reason: "Adicionar flag --no-prompt para modo não-interativo"
    - path: README.md
      reason: "Seção de portabilidade documentando o harness"
    - path: scripts/gauntlet/fases/portabilidade.py
      reason: "Nova fase com 2 testes"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Registrar fase portabilidade"
  n_to_n_pairs:
    - ["install.sh", "docker/test-clean-boot.sh"]
  forbidden:
    - "Empacotar Nyx-Code como imagem de produção (este Docker é só harness)"
    - "Dockerfile que pré-baixe modelos (pesado demais, sai do escopo)"
    - "Alterar comportamento interativo default do install.sh"
  tests:
    - cmd: "./run.sh --gauntlet --only portabilidade"
      timeout: 600
  acceptance_criteria:
    - "docker/test-clean-boot.sh sai com code 0 em máquina host com Docker + NVIDIA runtime"
    - "install.sh --no-prompt completa sem interação do usuário"
    - "Dentro do container, coverage Gauntlet passa 6/6"
    - "Seção 'Portabilidade' adicionada ao README"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: verificar que Docker está instalado no host e que o NVIDIA Container Toolkit funciona (`docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi`).

---

# Sprint PORT-02 -- Teste de máquina limpa via Docker

**Status:** CONCLUIDA
**Data:** 2026-04-16
**Prioridade:** ALTA
**Tipo:** Infra
**Dependências:** PORT-01
**Desbloqueia:** PORT-03

---

## Problema / Contexto

O projeto nunca foi validado em máquina limpa. A máquina do desenvolvedor pode ter dependências implícitas (curl, tar, build-essential, driver NVIDIA, glibc versão X) que estão ausentes em outras distros ou em instalações novas. Em caso de falha, o usuário de destino só descobre no primeiro `./install.sh`.

Docker com `--gpus all` permite simular "máquina limpa" repetidamente e validar o boot completo sem contaminar a máquina real.

O Docker aqui NÃO é distribuição oficial — é harness de teste.

## Implementação

### Fase 1: Modo não-interativo em install.sh

Adicionar parsing de flag `--no-prompt`:

```bash
NO_PROMPT=0
for arg in "$@"; do
    case "$arg" in
        --no-prompt) NO_PROMPT=1 ;;
    esac
done
```

Trocar os `read -rp` existentes por:

```bash
if [ "$NO_PROMPT" = "1" ]; then
    REDOWNLOAD="n"   # default conservador
else
    read -rp "  Baixar novamente? [s/N] " REDOWNLOAD
fi
```

Default no modo não-interativo: sempre "não" para perguntas de sobrescrita (mais seguro em CI/container).

### Fase 2: Dockerfile (`docker/Dockerfile.clean-boot`)

```dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3-pip \
    curl ca-certificates tar lsof netcat-openbsd \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.10 /usr/bin/python3

WORKDIR /nyx
COPY . /nyx

ENTRYPOINT ["/bin/bash"]
```

Notas:
- Imagem NÃO pré-baixa modelos (muito pesado; install.sh baixa na execução)
- Imagem NÃO instala Ollama (o install.sh baixa o binário)
- nvidia-container-toolkit roda do host, não precisa estar na imagem

### Fase 3: Script de teste (`docker/test-clean-boot.sh`)

```bash
#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

IMAGE="nyx-clean-boot:test"

echo "[test] Buildando imagem..."
docker build -t "$IMAGE" -f docker/Dockerfile.clean-boot .

echo "[test] Rodando install.sh não-interativo..."
docker run --rm --gpus all "$IMAGE" -c "./install.sh --no-prompt"

echo "[test] Rodando Gauntlet coverage dentro do container..."
docker run --rm --gpus all "$IMAGE" -c "./run.sh --gauntlet --only coverage"

echo "[test] OK"
```

### Fase 4: Documentação no README

Adicionar seção logo após "Validação":

```markdown
## Portabilidade

Para validar que o projeto funciona em máquina limpa:

    ./docker/test-clean-boot.sh

Isso buildar uma imagem Ubuntu 22.04 mínima, roda ./install.sh --no-prompt
e executa ./run.sh --gauntlet --only coverage. Requer Docker com
NVIDIA Container Toolkit instalado no host.
```

### Fase 5: Testes Gauntlet (fase `portabilidade`)

Estes testes rodam no host (não dentro do container) e apenas validam o harness:

| ID | Nome | Validação |
|----|------|-----------|
| PORT-01 | Dockerfile builda | `docker build -f docker/Dockerfile.clean-boot .` exit 0 |
| PORT-02 | install.sh --no-prompt não trava | subprocess.run com stdin=/dev/null termina sem hang |

O teste E2E completo (`test-clean-boot.sh`) é manual ou em CI dedicado — pesado demais para rodar no Gauntlet regular.

## Verificação

- [ ] `docker/Dockerfile.clean-boot` builda limpo
- [ ] `install.sh --no-prompt` roda sem interação
- [ ] `docker/test-clean-boot.sh` completa com sucesso no host
- [ ] README seção "Portabilidade" presente
- [ ] Gauntlet fase `portabilidade` passa 2/2

---

*"O que não é testado, não funciona." -- Anônimo da engenharia*
