# Perfil comum

## Clone
— (o checkout atual) [inferido]

## Toolchain
Build e teste: `dotnet` nativo; HTTP local: `curl`; matar processo: `kill <pid>`. [inferido]

## Git
Principal: `main`. Remote de PR: `origin`. Protegidas: `main`. [inferido]

## Portas
Do dono: `5000`. Faixa dos agentes do `/wh:implementation`: `5100–5105`. QA visual/e2e: a partir de `5108`. [inferido]

## Navegação
`.codegraph/` presente (C#): `codegraph explore -p . "<símbolos ou pergunta>"` (worktree: `codegraph init -y .` uma vez; `codegraph sync .` depois de editar). Docs e configs: `grep`/`Read`. [contexto.json]

## Docs
`docs/GLOSSARY.md` — glossário (negócio × código × termos a evitar). [contexto.json]
`docs/features/README.md` — índice do mapa de features; um arquivo por feature ao lado. [contexto.json]

## Limites
Nenhum agente toca produção, segredos, a porta `5000` nem arquivos fora do repo e do scratchpad. [inferido]
