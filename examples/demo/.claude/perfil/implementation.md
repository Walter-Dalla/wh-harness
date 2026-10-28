# Perfil do /wh:implementation

## Build
`dotnet build 2>&1 | tail -30` (sem warning novo = verde). [inferido]

## Testes
Área: `dotnet test --filter "FullyQualifiedName~<filtro>" 2>&1 | grep -E "Passed!|Failed!|error"`. [inferido]
Suíte: `dotnet test 2>&1 | grep -E "Passed!|Failed!|error"`. [inferido]
Aceite de item = o teste de área que só fica verde com o item feito; teste novo quando não há.

## Checks
`dotnet format --verify-no-changes` (fim de faixa e QA final). [inferido]

## Serviço descartável
`ASPNETCORE_URLS=http://localhost:<porta> DB_NAME=bakery-<slug>-<porta> dotnet run --project src 2>&1 | tail -5`; pronto quando `curl -s localhost:<porta>/health` responde `ok`; parar: `kill <pid>`. [inferido]

## Contrato
DTOs de `src/*/Dto`, rotas HTTP e o formato persistido de `Order`. Fixture: snapshots em `tests/__snapshots__`, atualizados com `UPDATE_SNAPSHOTS=1 dotnet test` e revisados pelo `git diff tests/__snapshots__`. [inferido]

## Arquivos de união
`src/Shared/ErrorCodes.cs` `src/Shared/Messages.cs` (só acréscimo). [inferido]

## Arquivos protegidos
`CHANGELOG.md`, `docs/features/*`, `docs/GLOSSARY.md`, `.claude/perfil/*`, `docs/relatorios/*`.

## Leitura do enriquecedor
Sempre: `docs/features/README.md` e `docs/GLOSSARY.md`. Quando a tarefa toca a área: o arquivo da feature. Antes de qualquer grep: `codegraph explore`.

## QA visual ou e2e
—

## Docs de fim
Changelog: `CHANGELOG.md`. Mapa de features: `/wh:feature-docs`. Glossário: `docs/GLOSSARY.md`. Pendências: —. Convenções: —.

## Relatório
`docs/relatorios/<data>-<slug>.md`

## Modelos
—

## Comandos na worktree
—
