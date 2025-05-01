# ADR-011: Gauntlet Obrigatório para Toda Feature

**Status:** Aceito
**Data:** 2026-04-05

## Contexto

Código sem teste validado é código que não existe. Cada feature nova
precisa de evidência concreta de que funciona, não apenas a afirmação
de quem escreveu. O Gauntlet (ADR-007) é o único mecanismo de teste
do projeto.

## Decisão

**Toda feature, tool, command ou service deve ter pelo menos 1 teste
no Gauntlet antes de ser considerada concluída.**

Regras:
1. Sprint sem teste no Gauntlet = sprint não concluída
2. Cada tool nova -> 1 teste na fase correspondente do Gauntlet
3. Cada command novo -> 1 teste na fase correspondente
4. Cada service novo -> 1 teste na fase correspondente
5. O conteúdo gerado deve ser analisado no teste (não apenas "retornou algo")
6. `./run.sh --gauntlet` deve passar 100% antes de push na main
7. Testes usam dados reais, nunca mocks (ADR-010)

## Evidência antes de Afirmação

O teste deve verificar o **conteúdo** da resposta, não apenas se houve
resposta. Exemplos:
- WebFetch: verificar que o HTTP status está no output
- WebSearch: verificar que há resultados com títulos e URLs
- TodoWrite: verificar contagem de tarefas no output
- /commit: verificar que git commit foi criado
- /diff: verificar que diff contém linhas +/-

## Consequências

- Gauntlet cresce com o projeto (36 -> 73 -> 89+ testes)
- CI bloqueia push se Gauntlet falha
- Features não testáveis ficam em UNMAPPED_FEATURES até terem infra

---

*"Confiança sem verificação é credulidade." -- Ronald Reagan*
