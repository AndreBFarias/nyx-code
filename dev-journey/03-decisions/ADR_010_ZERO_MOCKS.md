# ADR-010: Zero Mocks

**Status:** Aceito
**Data:** 2026-04-05

## Contexto

Testes com mocks mascaram falhas reais. O projeto já sofreu com isso quando
mocks passavam mas a integração real falhava. Mocks criam uma falsa sensação
de cobertura e divergem do comportamento de produção ao longo do tempo.

## Decisão

**Proibido usar mocks, stubs ou fakes em qualquer teste do projeto.**

Todo teste deve executar contra a infraestrutura real:
- **Ollama**: servidor real respondendo na porta 11435
- **Proxy**: servidor real na porta 11436 com think=false
- **DuckDuckGo**: busca web real via ddgs
- **httpx**: requests HTTP reais
- **Git**: operações git reais no repositório
- **Filesystem**: leitura/escrita real de arquivos
- **Sessões**: persistência real em ~/.nyx/

Se uma dependência externa está indisponível (ex: rede offline), o teste
deve falhar honestamente em vez de simular sucesso.

## Consequências

- Testes são mais lentos (rede, GPU, I/O) mas 100% confiáveis
- Gauntlet requer Ollama + Proxy rodando para fases que dependem deles
- Testes que não podem rodar sem infra são marcados em NEEDS_OLLAMA
- Falha no Gauntlet = falha real, nunca falso negativo por mock desatualizado

## Exceções

Nenhuma. Se algo não pode ser testado sem mock, a arquitetura precisa mudar.

---

*"A realidade é aquilo que, quando paramos de acreditar, não desaparece." -- Philip K. Dick*
