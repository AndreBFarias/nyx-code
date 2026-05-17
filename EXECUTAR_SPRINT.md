# Executar próxima sprint — UX-EXTRA-01

> **Este arquivo é auto-atualizado por `scripts/update_next_sprint.py` após cada sprint concluída.**
> Copie o bloco abaixo e cole em uma session nova de Claude Opus 4.7.
> Restam **27** sprints PENDENTE(S) na fila.

---

## Prompt para colar na session

```
Execute /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/SPRINT_UX_EXTRA_01.md.

Modelo obrigatório: claude-opus-4-7 (sem subagentes).
Protocolo obrigatório (GUIDE.md seção "próxima sprint" + workflow anti-gambiarra):

1. Leia o arquivo da sprint inteiro.
2. Leia a seção correspondente em dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md.
3. Rode `bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1` e me mostre FAIL_BEFORE.
4. Apresente plano e me pergunte dúvidas ANTES de mexer em código.
5. Implemente seguindo literalmente o arquivo da sprint.
6. Rode `bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1` e me mostre FAIL_AFTER.
7. Cole o diff de /tmp/inv_before.txt /tmp/inv_after.txt.
8. Cole o output bruto dos comandos de verificação da sprint.
9. Só marque CONCLUIDA se TODOS os critérios binários + invariantes passarem.
   Regra binária: FAIL_AFTER <= FAIL_BEFORE. Caso contrário, regressão: `git reset --hard HEAD~1` e refazer.
10. Após CONCLUIDA: commit atômico, move sprint file para concluidos/, roda `python scripts/update_next_sprint.py` para atualizar este arquivo.

Se qualquer passo falhar, reporte:
    [SPRINT UX-EXTRA-01] BLOQUEADA: <motivo objetivo>

ID desta sprint: UX-EXTRA-01
Arquivo: dev-journey/06-sprints/producao/SPRINT_UX_EXTRA_01.md
```

---

<!-- GAMBIARRAS_INJECT -->

## Gambiarras específicas (recorte auto-injetado)

> Fonte canônica: `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` §UX-EXTRA-01. O bloco abaixo é renovado a cada `python scripts/update_next_sprint.py`.

### UX-EXTRA-01 (editar último input)

- **Ctrl+Up insere literal `\x1b[1;5A`:** keybinding não capturou.
  - **Detectar:** pexpect: envia Ctrl+Up, buffer deve ter conteúdo anterior, não escape sequence.
- **`/edit` retorna placeholder sem prefill:**
  - **Detectar:** teste: digitar `oi`, enviar; digitar `/edit`; prompt seguinte deve pré-popular `oi`.

<!-- /GAMBIARRAS_INJECT -->

---

## Após concluída esta sprint

```bash
# Marcar no master como CONCLUIDA, mover arquivo, re-rodar este script
python scripts/update_next_sprint.py
git add EXECUTAR_SPRINT.md dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
# incluir no mesmo commit da sprint ou em commit separado
```

O arquivo acima será atualizado com o próximo ID automaticamente.
