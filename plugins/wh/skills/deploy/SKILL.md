---
name: deploy
description: Publica o repositório atual em produção e verifica a URL pública; também rollback, backup/restore, rotação de segredo e setup inicial do servidor. Use para deploy, publicar, release, "subir para produção/servidor", rollback. Alvo, registro, comandos e falhas conhecidas vêm de .claude/perfil/deploy.md.
---

# Deploy

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "deploy")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/deploy.md 2>/dev/null || echo PERFIL_AUSENTE`

Da raiz do checkout do `_comum § Clone`. Sua parte termina onde o perfil § Acesso diz: por padrão você publica o artefato e verifica a URL pública; tudo no servidor é do dono, em bloco copiável, e você espera o relato dele. Nada de `ssh`, `scp` ou chave quando o perfil não dá acesso.

Deploy muda o que os usuários veem: confirme antes de publicar, reiniciar ou fazer rollback, a menos que o dono tenha pedido o deploy nesta conversa. Tudo que toca volume de dados pede confirmação sempre. Segredos (perfil § Segredos): nunca lidos, impressos ou gerados por você.

## 1. Preflight

Perfil § Pré-condições, uma por uma: árvore commitada nos caminhos que o perfil nomeia (pergunte antes de commitar), daemons vivos, registro alcançável, templates e assets presentes. Falha aqui para o deploy.

**Feito quando toda pré-condição do perfil passou com a saída do comando lida.**

## 2. Publicar

O comando do perfil § Publicar, saída para um log no scratchpad (`> "$L" 2>&1; echo "exit=$?"`), depois `grep` das linhas de resultado que o perfil lista. Sem `| tail` no comando: esconde o exit code. Falhou: perfil § Falhas; só o push falhou com o build pronto = o comando de repush do perfil, sem rebuild.

**Feito quando o artefato está no registro com a tag do commit.**

## 3. Atualizar o alvo

Perfil § Atualizar: quem faz e como. Quando é o dono, entregue os passos exatos e espere o relato. Compose, env ou variável nova mudaram neste deploy: diga, e dê o conteúdo novo para colar.

## 4. Verificar

Cada linha do perfil § Verificar (URL → resposta esperada), sem criar dados em produção. Falha: perfil § Falhas (sintoma → causa → ação); sem causa listada, peça ao dono os logs que o perfil nomeia.

**Feito quando toda verificação do perfil respondeu o esperado.**

## Rollback

Perfil § Rollback, com confirmação. Tags disponíveis: o comando do perfil.

## Backup e restore

Perfil § Backup: agendamento, verificação do último backup, ensaio de restore antes do real.

## Setup inicial e configurações externas

Perfil § Setup inicial (o dono roda cada passo) e § Configurações externas (o que nunca ligar no provedor, e por quê).

## Responder

Tag publicada, o que o dono ainda precisa fazer, resultado de cada verificação, falhas e o que foi pulado.
