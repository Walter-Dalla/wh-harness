# Perfil do `/wh:deploy`: `.claude/perfil/deploy.md`

Gerado pela skill `perfil`. Uma linha por fato, fonte entre colchetes, `—` na seção sem resposta. O porquê (modelo de ameaça, histórico) fica num doc do repo apontado aqui, não no perfil.

```markdown
# Perfil do /wh:deploy

## Alvo
URL pública, onde roda (servidor, PaaS, região), quem orquestra (compose, Komodo, k8s, systemd), rede e túnel/proxy na frente. Doc do porquê: `docs/deploy.md`.

## Acesso
O que o agente pode tocar: `nenhum acesso ao servidor` (padrão) ou o comando/MCP permitido e a condição (confirmação do dono a cada chamada).

## Artefato
O que se publica (imagem, pacote, bundle), registro (endereço, auth, insecure-registries), tags (`latest`, `sha-<commit>`, versão), o que vai dentro e o que fica fora do CI (assets não versionados).

## Pré-condições
Uma por linha, com o comando que confere: árvore commitada em `<caminhos>`, daemon vivo (`docker.exe version …`), registro alcançável (`curl … /v2/` → 200/401), templates de export, assets locais. Como commitar/push neste checkout (`_comum § Git`).

## Publicar
`<script> [versão]`: o que ele faz (testes, export, build, push), quanto demora, linhas de resultado a filtrar (`grep -E "…"`), repush sem rebuild quando só o push falhou.

## Atualizar
Quem (dono/agente) e como o alvo pega o artefato novo (botão no orquestrador, `pull && up -d`), onde compose e env moram no alvo, como fixar uma tag (`IMAGE_TAG=…`), sinal de pronto (`healthy`).

## Verificar
Uma por linha: `curl … <URL>` → código esperado e o que prova (site, API no ar, cache não-stale). O que nunca chamar em produção (login com rate limit, criação de dados). Logs que o dono manda quando falha.

## Falhas
Sintoma → causa → ação, uma por linha (502 do proxy, `permission denied` no socket, `HTTP response to HTTPS client`, `denied` no pull, cliente web quebrado por cache).

## Rollback
Como apontar o alvo para a tag anterior, como listar tags, o que não é rollback (volume de dados).

## Backup
Comando/cron de backup, verificação (`tail` do log, arquivo por dia), retenção, cópia off-host, ensaio de restore e restore real (confirmação; o que nunca rodar: `down -v`).

## Segredos
Variáveis do alvo (nome e onde se obtém, nunca o valor), rotação (passos e janela), credenciais que o agente nunca lê.

## Configurações externas
Regras no provedor (DNS, CDN, WAF): o que está ligado, o que nunca ligar e por quê.

## Clientes extras
Builds distribuídos fora do alvo (desktop, mobile): comando de export, requisitos (SDK, keystore), saída.

## Setup inicial
Passos de um servidor do zero (o dono roda), na ordem, com data em que foi feito.
```
