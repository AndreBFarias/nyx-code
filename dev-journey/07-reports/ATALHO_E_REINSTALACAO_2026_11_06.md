# Atalho do menu e reinstalação pendente

**Data**: 2026-11-06

## Estado atual: o Nyx não abre até reinstalar

`venv/` e `models/` foram apagados de propósito em 06/11/2026, por decisão de quem usa. Uma reinstalação começou e foi interrompida, e o que ela recriou foi apagado de novo. Sem o venv, `./run.sh` e o Gauntlet não rodam. Dados de `~/.nyx` não foram apagados.

## Causa do atalho

- **Falha do atalho não reproduzida.** `nyx.desktop` existe e `pop-launcher` o encontra. No COSMIC, `Terminal=true` vira `cosmic-term -e <Exec>`, e esse comando abriu a TUI em janela de verdade. O clique no menu em si não foi testado.
- A janela abre como "Novo terminal", com ícone de terminal e cerca de 11 s de spinner antes da TUI.
- **Defeito provado no instalador:** sem daemon na porta padrão, `install.sh` abortava na fase 5 (`ollama pull`, com `set -e`), antes da fase 12, que instala o atalho. Com daemon presente, os modelos iriam para a pasta dele, não para `models/`.

## O que foi corrigido

- `install.sh`: antes da fase 5, exporta `OLLAMA_MODELS` e `OLLAMA_HOST` iguais aos do `run.sh`, sobe um Ollama dedicado se preciso e o encerra ao sair. Na reinstalação interrompida, `qwen2.5-coder:3b` terminou em `models/`.
- `scripts/gauntlet/nyx_gauntlet.py`: teste D-03 confere essa ordem. Ainda não executado.

## Para reinstalar

```bash
./install.sh --no-prompt --no-kitty
```

Rode na raiz do projeto.

## Linha de base do Gauntlet (antes de apagar)

- `./run.sh --smoke`: `boot ok`.
- `./run.sh --gauntlet`: REPROVADO, parcial, 55/62 fases.
- Única falha: `GUARD-02 IDENTITY-ENFORCE`.

O Gauntlet não rodou depois das correções.
