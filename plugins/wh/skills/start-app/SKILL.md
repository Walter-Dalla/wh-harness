---
name: start-app
description: Sobe, para ou reinicia o app do repositório atual (serviços e cliente) e confere que respondem. Use para rodar, iniciar, parar, reiniciar ou testar o app de ponta a ponta. Serviços, portas, cliente e estado vêm de .claude/perfil/start-app.md.
---

# Subir o app

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "start-app")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/start-app.md 2>/dev/null || echo PERFIL_AUSENTE`

Da raiz do checkout do `_comum § Clone`, com a toolchain do `_comum § Toolchain`. Esta skill é a interativa: usa as portas do dono (`_comum § Portas`); as outras skills sobem o próprio serviço em porta própria.

## 1. Serviços

Na ordem do perfil § Serviços: o comando `start` de cada um; pronto quando o health do perfil responde. Falha: as últimas linhas do log que o perfil nomeia, na resposta. Porta ocupada por processo que não é deste repo: pergunte antes de derrubar.

**Feito quando todo serviço do perfil responde ao health.**

## 2. Cliente

Perfil § Cliente: o comando, em background (`run_in_background: true`) quando abre janela. Sem janela (sessão sem display, só conferir render): a alternativa do perfil § Cliente.

## 3. Alternativa

Perfil § Alternativa (Docker ou outro), só quando pedida ou quando a toolchain nativa falta no checkout. Mesma porta que o nativo: pare um antes do outro.

## Parar

`stop` do perfil § Serviços e o processo do cliente que você subiu (`kill <pid>`; o `_comum § Toolchain` diz o equivalente por SO). Processo que não foi você que subiu: pergunte. Estado do dono (perfil § Estado) fica como está; comando que apaga estado pede confirmação.

## Responder

Uma linha por serviço vivo (URL, porta, PID, log), o cliente, o que foi pulado e por quê.
