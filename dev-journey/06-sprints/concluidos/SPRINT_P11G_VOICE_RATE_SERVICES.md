## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-G
  title: "Voz + Rate services -- voice, voiceStreamSTT, voiceKeyterms, rateLimitMessages, rateLimitMocking, mockRateLimits"
  touches:
    - path: nyx/agent/services/voice.py
    - path: nyx/agent/services/voice_stt.py
    - path: nyx/agent/services/voice_keyterms.py
    - path: nyx/agent/services/rate_limit.py
  origin:
    primary: "openclaud/src/services/voice.ts"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_voice"
      timeout: 30
```

---

# Sprint P11-G -- Voz & Rate Limiting Services

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P11-C

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| voice | voice.ts | Integração voz via whisper.cpp local |
| voice_stt | voiceStreamSTT.ts | Speech-to-text streaming |
| voice_keyterms | voiceKeyterms.ts | Detecção de termos-chave em voz |
| rate_limit | rateLimitMessages.ts + mocking | Rate limiting local + mensagens + mocking para testes |

---

*"A voz é o espelho da alma." -- Sófocles*
