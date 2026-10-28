# Perfil do `/wh:start-app`: `.claude/perfil/start-app.md`

Gerado pela skill `perfil`. Uma linha por fato, fonte entre colchetes, `—` na seção sem resposta. Clone, toolchain, portas e limites ficam no `_comum.md`.

```markdown
# Perfil do /wh:start-app

## Serviços
Na ordem de subida, um por linha: nome — `start` · `stop` · `status` · health (URL e resposta esperada) · log. Ex.: `scripts/dev.sh start` (espera `/api/health`; log `.dev/dev.log`). Dependência entre eles (build do pacote compartilhado antes, etc.).

## Cliente
Como abrir o cliente (binário, comando, URL no navegador), o que ele chama (`http://127.0.0.1:<porta>`), e a alternativa sem janela (flag de screenshot, teste por socket, `curl`).

## Alternativa
Docker ou outro jeito de subir o mesmo app (comando, `.env` mínimo, health, logs, `down`), e o que ele compartilha com o nativo (porta, volume).

## Estado
Bancos, volumes e arquivos de estado do dono (caminho), o que `stop` apaga, o que um `down -v` apagaria (confirmação), estado descartável para teste manual (`--db <arquivo>`, pasta temporária).

## Credenciais de dev
Jogador/usuário de desenvolvimento, variáveis opcionais (login social), Swagger ou console de admin local.

## Sinais
Sintoma → causa → ação, um por linha: `bin/` travado por processo vivo, porta ocupada, lockfile mudou (`install` antes).
```
