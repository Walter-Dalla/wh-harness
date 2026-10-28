---
name: feature-docs
description: Cria ou atualiza o mapa de features do repositório (como cada feature funciona, suas regras e interações): classifica a entrada num arquivo existente ou novo e mantém o índice e os dois lados de cada interação em sincronia. Use quando uma feature é adicionada, muda ou sai, quando pedirem "documentar/atualizar a doc da feature", "adicionar ao mapa de features", ou no fim de uma tarefa de feature. Pasta, modelo e verificação vêm de .claude/perfil/feature-docs.md.
---

# Mapa de features

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "feature-docs")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/feature-docs.md 2>/dev/null || echo PERFIL_AUSENTE`

O mapa é um dicionário sob demanda para agentes: um índice + um arquivo por feature (perfil § Pasta). Agentes leem o índice e só o arquivo de que precisam, então cada arquivo fica curto, exato e autocontido. Idioma e formato: perfil § Formato.

O mapa descreve **comportamento**: fluxo, regras, quem é dono de cada regra. Onde o código mora fica com o código (`_comum § Navegação`): nenhuma seção "Código"/"Endpoints", nenhuma lista de arquivos ou rotas (apodrecem em silêncio). Classe, função ou constante entra só inline, quando é dona de uma regra que um agente precisa achar.

## 1. Entender a entrada

Feature nova, mudada ou removida; diff; intervalo de commits; ou descrição. Só um tema: descubra o que mudou (`git diff`, `git log`, changelog, status de features). Leia o índice; os outros arquivos ainda não.

## 2. Categorizar

Compare com a tabela do índice (ids, palavras-chave, serviços) e decida:

- **Arquivo existente** (o padrão): a entrada muda regra, fluxo, endpoint ou dependência de uma feature listada, ou acrescenta variação dela.
- **Arquivo novo**: só quando a entrada tem loop próprio para o usuário **e** dono próprio no código (serviço/entidade/endpoints ou painel). Helper, regra ou campo novo nunca é arquivo novo.
- **Vários arquivos**: mudança transversal; o arquivo dono por completo e só a linha de "Interações" dos afetados.
- **Remoção**: seção/arquivo sai com todo link e linha do índice que apontava para ele.

Dois arquivos igualmente plausíveis, ou arquivo novo que dividiria um existente: pergunte antes de escrever. Depois leia os arquivos-alvo e os vizinhos de "Interações" que a mudança toca.

**Feito quando cada parte da entrada tem um arquivo-alvo e uma categoria.**

## 3. Colher fatos do código

Cada afirmação sai do código aberto agora, não da memória nem do texto do pedido, pela camada (perfil § Camadas): o fluxo e as regras com o dono de cada uma; chamadas para outras features e delas; o que o usuário vê no cliente; números citando a constante, com o valor só quando ele explica o comportamento.

**Feito quando toda regra que você vai escrever tem o símbolo dono lido.**

## 4. Escrever

Modelo do arquivo: perfil § Modelo (20–50 linhas; corte detalhe antes de passar). Regras:

- **Fonte única.** Regra transversal fica nos docs de regras do perfil § Fontes de regra: aponte a seção em vez de copiar. Regra de uma feature só vive em `## Invariantes` do arquivo dela; movê-la para lá a partir do doc transversal é o caminho normal. Status e roadmap no doc de status; histórico no changelog. O mapa descreve só o estado atual: nenhum "antes era".
- **Interações nos dois lados.** Dependência criada ou removida em A aparece também em "Interações" de B.
- **Índice** em sincronia: perfil § Índice diz quais partes (tabela, quem chama quem, diagrama, moedas) e quando cada uma muda.
- Nome de arquivo: perfil § Formato. Renomear = corrigir todo link (grep).

## 5. Verificar

Os comandos do perfil § Verificação. Pronto quando: todos saem 0 e sem linha `MISSING`/`NO-PROPERTIES`; todo arquivo dentro do limite do perfil; todo símbolo citado que você não abriu no passo 3 existe (grep); nenhuma seção "Código"/"Endpoints" nem lista de arquivos ou rotas.

## 6. Relatar

Quais arquivos mudaram e por que a entrada foi para lá (a categorização), e o que não deu para confirmar no código. Commit só se pedirem.
