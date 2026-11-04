# Ambiente e protocolo do `/wh:implementation`

Tudo roda no clone do `_comum` § Clone (a sessão do orquestrador abre nele) e nas worktrees de agente que nascem dele. Toolchain nativa do clone. Os limites do `_comum` § Limites valem para todo agente (portas do dono, produção, MCPs reais).

## Portas

Só se o perfil § Serviço descartável existir. Da faixa de portas do `_comum` § Portas, em ordem:

| Porta | Quem |
|---|---|
| 1ª | orquestrador: item de tarefa pequena que precise do serviço |
| 2ª–4ª | faixas `impl-dev`, uma por faixa (até 3 em paralelo) |
| 5ª | faixa de FIX ou reserva |
| 6ª | `impl-qa` modo `final` (o QA visual/e2e do perfil pode subir o próprio serviço; ele escolhe porta livre, sem derrubar o que já está numa porta) |

## Scripts (`${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/`)

| Script | Quem roda | Faz |
|---|---|---|
| `preflight.sh --base <hash> [--branch <b>] [--port <p>] [--lane <faixa.md>] [--protected <a,b>]` | `impl-dev` e `impl-qa`, antes de qualquer `git reset`/`branch` | confere worktree de agente, branch, worktree limpa, base existente, porta livre, faixa e quadro; `PREFLIGHT FALHOU` = `BLOQUEADO`, sem tocar em nada |
| `escopo.sh <faixa.md> <base> [<ref>]` | `impl-dev` no fim, orquestrador antes do merge | arquivos mudados × `Dono de:`/`Pode tocar`/`União:` da faixa (caminhos entre crases); `FORA:` = a faixa conserta antes do merge |

## Ferramentas (cada uma só se instalada; presente, obrigatória desde o primeiro passo)

### RTK (saída do Bash)

Com `rtk` instalado, toda saída do Bash chega condensada: o RTK guarda o sinal (erros, contagens, caminhos, exit code) e tira o ruído.

- Trate a saída como o resultado completo; não repita o comando "para ver inteiro".
- Junte comandos relacionados numa chamada (`cmd1 && cmd2`, ou `;`) em vez de uma chamada por comando: cada turno custa mais que a saída. Exceção, a worktree de agente com guard de isolamento: lá vale o perfil § Comandos na worktree (git pelo binário absoluto, `/usr/bin/git -C <worktree> …`, um comando por chamada; o RTK reescreve o `git` solto e o guard recusa).
- Saída truncada diz no próprio texto como recuperar o resto; siga esse caminho.
- `rtk proxy <cmd>` só quando a saída vier inutilizável: vazia quando devia ter algo, contradizendo o exit code, ou truncada sem caminho de recuperação.
- Mesmo com RTK, filtre na origem o que é grande (`2>&1 | tail -30`, `grep -E`): os comandos do perfil § Testes e § Checks já vêm filtrados.

Sem `rtk` no PATH: saída crua; os filtros do perfil continuam obrigatórios.

### CodeGraph (`codegraph` no PATH)

Repo com `.codegraph/`: na worktree, `codegraph init -y .` uma vez antes de editar (a verificar: em repo grande, copiar o `.codegraph/` do clone e rodar `codegraph sync .` pode ser mais barato que reindexar por faixa); no clone, `codegraph sync .`. `codegraph explore -p . "<símbolos ou pergunta>"` antes de afirmar qualquer coisa sobre código indexado, saída tratada como lida; `codegraph sync .` depois de editar. `grep`/`Read` para o que o índice não cobre (`_comum § Navegação`) e para todo repo sem índice.

## Estados

Toda resposta de agente e toda linha `FIM` do quadro termina num destes estados, com a evidência ao lado:

| Estado | Quando | Próxima ação |
|---|---|---|
| `CONCLUIDO` | todo item com commit e Aceite executado e verde | avançar |
| `PARCIAL` | parte dos itens pronta (contexto, tempo, item pulado) | retomar pelo checkpoint |
| `AGUARDANDO` | parado numa `PERGUNTA` sem item independente | a resposta retoma o agente |
| `DECISAO_HUMANA` | parte que só o dono faz ou decide (linha `HUMANO` no quadro) | registrar e seguir no resto |
| `BLOQUEADO` | ambiente ou ferramenta impede seguir (preflight, push recusado, build quebrado fora da faixa) | o orquestrador diagnostica |
| `REPROVADO` | verificação final vermelha (suíte, check, escopo) | consertar antes de entregar |

**Evidência** de um item: `item · commit · Aceite (comando) · exit code · o que o comando cobre`. Não é evidência: comando não executado, saída truncada ou interrompida, teste de outra área, ou o relatório de outro agente sem conferir o repositório. Exit 0 de um teste que não exercita o item também não é.

## Checkpoint

Em `<raiz>/.impl/<slug>/progress/<faixa>.md` (caminho do prompt; fora do git pelo exclude de `.impl/`), nunca dentro da worktree, que some ao fim do agente. Reescrito a cada item, para um agente novo continuar sem a memória do anterior:

```markdown
Faixa: <faixa> · base <hash> · ponta <hash>
Feitos: <id> <commit> <Aceite: exit> (um por linha)
Atual: <id> · não commitado: <arquivos ou "nada">
Testes: <comando> → <resultado>
Próxima ação: <exata>
Abertos: <PERGUNTA/HUMANO pendentes>
Consertos pedidos: <ids QA-… recebidos e não commitados, com o arquivo do QA, ou "nenhum">
```

## Arquivos fora da worktree

Retro, checkpoint, saída do QA e log de Aceite vão nos caminhos absolutos do prompt, em `<raiz>/.impl/<slug>/`. `Write`/`Edit` recusados ali: grave em `<scratchpad>/<faixa>/` (subpasta sua: o scratchpad é compartilhado entre agentes) e copie com `cp`; `cp` também recusado: o conteúdo vai na sua resposta final, marcado com o caminho de destino, e o orquestrador grava. O quadro aceita `printf … >> <quadro>`.

## Serviço descartável

Comando do perfil § Serviço descartável com a sua porta e um estado descartável (`<slug>-<porta>` no nome do banco ou pasta), na raiz da worktree, em background (`run_in_background`); pronto quando o health check do perfil responde. Pare no fim (`kill <pid>` do processo que você subiu). Nunca o estado de dados do dono.

## Testes e checagens

Comandos do perfil § Testes e § Checks, saída sempre filtrada. Escolha do teste por item: mudança localizada = teste da área; contrato = testes do produtor e do consumidor; infraestrutura compartilhada = testes das áreas dependentes; a suíte inteira só no fim da faixa e no QA final. Fixture de contrato: pelo perfil § Contrato, depois o `git diff` da pasta da fixture, campo a campo.

## Navegação

`_comum § Navegação`; CodeGraph: § Ferramentas acima. Sem índice: `grep`/`Read` por trecho.
