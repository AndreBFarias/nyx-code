# Nyx-Code - Guia de Identidade Visual e UX

## Filosofia

Nyx vive no terminal. Cada interação é precisa, direta, sem desperdício.
A estética é cyberpunk de terminal: escuro, elegante, funcional.

Zero emojis. Zero verbosidade. Zero linguagem corporativa.

## Paleta de Cores (Entidade Nyx)

Cores extraídas do config.json da Nyx no panteão Luna.
Tema: cinza cirúrgico + cyan/teal técnico.

```
BACKGROUND
  background:       #2A2C39   (cinza-azul escuro)
  background-alt:   #232530   (mais escuro)
  background-input: #3D3F4E   (inputs)
  background-code:  #1A1B26   (ultra-escuro para código)

FOREGROUND
  text-primary:     #E8E8E8   (cinza claro)
  text-secondary:   #6C7A89   (cinza muted)
  text-user:        #00D4AA   (cyan/teal - input do usuário)

ACCENT
  primary:          #00D4AA   (cyan/teal - cor principal Nyx)
  glow:             #00D4AA   (efeito glow)
  success:          #00D4AA   (= primary)
  warning:          #FFB86C   (laranja)
  error:            #FF6B6B   (vermelho Nyx)
```

## Sistema de Temas por Entidade

Cada tema corresponde a uma entidade do panteão Luna.
JSONs em `nyx/themes/entities/`.

| Tema | Cor Principal | Descrição |
|------|--------------|-----------|
| **nyx** (padrão) | #00D4AA cyan | Codificadora silenciosa |
| luna | #BD93F9 roxo | Dracula Gothic original |
| mars | #FF5555 vermelho | Agressivo sobre negro |
| eris | #FF5555 vermelho | Caos púrpura |
| juno | #A4CB58 verde | Natureza digital |
| lars | #50FA7B verde | Terminal clássico |
| somn | #8BE9FD azul | Noturno profundo |

## Tom de Voz

- Técnico, direto, preciso
- Frases curtas
- PT-BR sem formalismos
- Formato: diagnóstico -> solução -> verificação

## Tags de Output

| Tag | Cor | Uso |
|-----|-----|-----|
| `[nyx]` | #00D4AA cyan | Mensagens do sistema |
| `[nyx]` | #00D4AA cyan | Sucesso |
| `[nyx]` | #FFB86C laranja | Avisos |
| `[nyx]` | #FF6B6B vermelho | Erros |

## Interface

- Banner com ASCII art no boot (cores Nyx)
- Informações de status: modelo, portas, VRAM
- Mensagens curtas em PT-BR
- Citação de filósofo no fim de cada script
- Bordas e comentários em #6C7A89 (secundário)
