---
name: qa-visual
description: QA visual e funcional do cliente do repositório atual contra um serviço local isolado — roda o produto de verdade, dirige com input real pelo harness do repo, tira e lê prints, cruza com o backend e escreve um relatório de bugs com evidência (qa/RELATORIO_QA.md). Encontra e documenta, só; nunca corrige. Use para "rodar QA", "testar visualmente", "achar bugs de UI/UX", "QA da feature X" ou reteste. Harness, fixtures, tempos e armadilhas vêm de .claude/perfil/qa-visual.md.
---

# QA visual e funcional

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "qa-visual")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/qa-visual.md 2>/dev/null || echo PERFIL_AUSENTE`

Rode o produto de verdade, exercite as features, tire prints, **olhe cada print** e entregue um relatório de bugs com evidência. **Nada é corrigido**: só encontrado, reproduzido, evidenciado e documentado.

## Entrada

`/wh:qa-visual [features…] [--res=WxH,…] [--lang=a,b] [--autonomo]`

| Argumento | Padrão | Significado |
|---|---|---|
| `features` | todas as dadas como feitas no doc de status | nomes dos arquivos do mapa de features sem `.md` |
| `--res` | perfil § Entrada | resoluções (o retrato tem layout próprio) |
| `--lang` | perfil § Entrada | idiomas |
| `--autonomo` | ligado sem dono para responder (subagente) | o checkpoint (seção 6) vai para o relatório em vez de parar |

## Saída

Tudo em `<raiz>/qa/` (`<raiz>` = checkout testado: repositório ou worktree; já gitignored). Rodada longa: prefira uma worktree como `<raiz>` (outra sessão pode trocar a branch do checkout principal no meio). Layout de prints, logs, dados e cenários: perfil § Saída. Os cenários da rodada sobrevivem ao teardown na pasta que o perfil nomeia; o setup seguinte os reinstala (reteste).

## 0. Contexto

Os docs do perfil § Contexto (regras de camada, mapa de features, status): deles saem os critérios de "correto". Sem mockup, a UI se julga pelas regras desses docs, pela doc da feature e pela consistência entre telas. Status diz o que existe: o que ele não dá como feito não se testa; pendências conhecidas não viram bug novo. Código: `_comum § Navegação`; sem o índice, causa no backend vira hipótese.

## 1. Preparação

1. Mapa de features (índice + arquivos do escopo) e doc de status: monte a **checklist** (perfil § Checklist diz como ler os prints e o que não é bug): por feature, comportamentos esperados com os números concretos (tempos, limites, preços, capacidades), como verificar **na tela** e **no backend**, status, e o que exige nível, moeda ou espera longa.
2. Args de debug do cliente (perfil § Ambiente: onde está a lista canônica; variam por branch).
3. Setup do harness (perfil § Harness). Anote os valores de configuração que ele imprime: mudam fluxos.
4. Serviço do QA (perfil § Harness), na porta do `_comum § Portas`; confirme com uma chamada real.
5. Smoke: o cenário de fumaça do perfil § Harness. Abra o print e descreva-o. Erro de script aqui já é bug.

**Feito quando a checklist existe, o serviço responde e o print do smoke foi lido.**

## 2. Como testar

- Cenário: ops, scripts e armadilhas no doc do harness (perfil § Harness).
- **Ação testada sempre pela UI**, com input real. Consulta só-leitura para achar coordenadas é permitida.
- **Fixtures** (perfil § Fixtures): montar o estado de partida pela API local é permitido; o relatório registra qual cenário usou qual. O que ainda exige recurso sem caminho pela UI vira "Bloqueada (precisa de X)".
- **Usuário limpo por cenário** (o harness cria um por padrão); o mesmo id para encadear cenários.
- **Espere de verdade**: ops de espera por texto/estado; `sleep` só para animações.
- **Armadilhas conhecidas**: perfil § Armadilhas, antes de culpar o produto.
- **Tempo**: perfil § Tempos (ação mais curta, folga de espera); espera inviável = item "Parcial".
- **Backend**: estado antes e depois de todo passo que muda estado, comparado com a tela.

## 4. Regras

- Uma feature por vez; só avance com ela documentada no relatório.
- Todo bug reproduzido **pelo menos 2 vezes**; "reproduzido N/M".
- Todo bug tem print e/ou trecho de log. Sem evidência, não entra.
- Bug, não implementada e intencional são coisas diferentes. Não testável = "Bloqueada" com motivo; nada pulado em silêncio.
- Um bug por causa: sintomas da mesma raiz agrupados.
- Escrita só em `<raiz>/qa/` e nas pastas que o perfil § Saída lista (mais o estado do usuário local, que o teardown restaura). Código, projeto, catálogos e snapshots ficam como estão. **Sem commit.**
- `_comum § Limites`: produção e MCPs reais nunca. Processo que não foi a skill que subiu fica vivo.
- No fim, **sempre** o teardown do perfil § Harness (mesmo com a rodada quebrada no meio), e `git status` só com o que já estava antes.

## 5. Relatório (`qa/RELATORIO_QA.md`)

1. **Ambiente**: commit/branch, versão do cliente/engine, porta, resoluções, idiomas, data, configuração relevante.
2. **Resumo**: feature × status (OK / Com bugs / Parcial / Bloqueada / Não implementada) × bugs por severidade, mais o que foi verificado e funcionou (com os números medidos).
3. **Bugs** (BUG-001…), por severidade: feature, categoria (Asset / Mapa / UI / UX / Sistêmico), severidade (Crítico: trava ou impede usar; Alto: feature não funciona; Médio: funciona com defeito; Baixo: cosmético), resolução e idioma, passos (comando exato, id, fixture), esperado (citando a doc ou a regra) vs. obtido, reprodução N/M, evidência (print e/ou trecho curto de log), causa provável marcada como hipótese.
4. **Assets faltando** (placeholders conhecidos à parte).
5. **Não testados / parciais** e por quê.
6. **Top 5 correções**, em ordem, com o motivo.
7. **Reteste**: o comando de cada bug e onde estão os cenários.
8. **Melhorias para o harness**: ops que faltaram, suspeitas falsas recorrentes, armadilhas novas (candidatas ao perfil § Armadilhas).

O que precisa sobreviver à rodada vira linha no doc de pendências do perfil § Pendências (nenhum arquivo de pendências novo); plano de correção é temporário.

## 6. Checkpoint

Antes de testar as features: a checklist (seção 1), o plano dos cenários (arquivos, fixtures, ids encadeados) e o smoke (serviço respondendo e um print real, aberto e descrito). Interativo: mostre e aguarde o OK. `--autonomo`: numa seção do relatório, e siga.
