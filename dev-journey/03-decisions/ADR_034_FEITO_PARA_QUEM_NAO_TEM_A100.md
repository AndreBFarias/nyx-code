# ADR-034 — FEITO PARA QUEM NÃO TEM A100

**Status:** ACEITO
**Data:** 2026-06-01
**Onda:** 36 (RESSURREIÇÃO)

## Contexto

O dono definiu, em 2026-05-31, para quem o Nyx-Code é feito:

> "É algo que vamos entregar pras pessoas sem condições de ter uma A100 pra rodar
> um modelo bom."

Um agente de código offline, gratuito, para quem não tem grana nem hardware de
ponta. Esse público é a razão de existir do projeto — e a régua que decide o que
é sucesso. Uma decisão técnica que melhora o produto para quem TEM hardware bom,
mas piora ou ignora quem não tem, é uma decisão errada para o Nyx.

## Decisão

**O sucesso do Nyx-Code se mede no pior hardware razoável com o desktop cheio,
não no melhor caso com a máquina dedicada.**

Implicações:

1. O cenário de referência para testes e validação é: RTX 3050 4GB com Chrome +
   Spotify + Discord (e a própria sessão de trabalho) abertos ao mesmo tempo.
   Rodar bem nesse cenário é REQUISITO, não bônus.
2. "Funciona na minha máquina (livre)" não é prova. Proof runtime real é com o
   ambiente realista do usuário (VRAM disputada).
3. Gratuito e offline são inegociáveis ([[ADR-001]]): zero custo, zero dependência
   de internet ou de conta paga.
4. Acessibilidade vence pureza técnica: entre uma solução elegante que exige mais
   hardware e uma solução mais trabalhosa que cabe no hardware ruim, escolhemos a
   segunda.

## Consequências

### Positivas
- O projeto permanece fiel a quem se propôs a servir.
- Decisões de escopo ganham um critério claro de desempate (o do hardware ruim).

### Negativas / custo aceito
- Otimizar para o pior caso é mais difícil e mais lento. É o trabalho que importa.

## Enforcement

- Critérios de aceitação de sprints de UX/performance citam o cenário "desktop
  cheio na RTX 3050 4GB".
- Nenhuma feature assume VRAM/CPU/disco abundantes sem degradação graciosa.

## Referências
- [[ADR-001]] (Local First) — gratuito e offline.
- [[ADR-032]] (A infra carrega o modelo) — como honramos isso na prática.
- [[ADR-033]] (A cadeia nunca quebra) — robustez como respeito ao usuário.
- Memória do projeto: `project_alma_infra_sobre_hardware`.

---

*"O benchmark que importa não é a A100 ociosa: é o notebook com o Chrome aberto."*
