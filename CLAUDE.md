# Instruções do projeto — kenshi-modkit

## O que é

Biblioteca Python que lê e grava os formatos binários do Kenshi — mods
(filetypes 16/17) e saves (filetype 15) — para tratar mod como código em vez de
cliques no FCS. Formato documentado em `FORMATO.md`, typecodes em
`TYPECODES.md` (definições) e `TYPECODES-SAVE.md` (runtime); estado atual e
próximos passos no `README.md`.

## Regras

- **Repositório público, MIT** (`LucasSKrewer/kenshi-modkit`). Nada de caminho
  pessoal desnecessário, credencial, nem menção ao trabalho do Lucas nos
  arquivos versionados. Push por **HTTPS**, nunca SSH.
- **Só biblioteca padrão.** Python 3.12, zero dependências. Windows/PowerShell.
- **Strings são `bytes`, nunca `str`.** Decodificar e recodificar pode alterar
  o arquivo e quebrar o round-trip. Use `km.t()` só para exibir e `km.b()` só
  para converter entrada do usuário.
- **Nunca gravar sobre arquivo do jogo.** Gerar em `out/` e copiar para
  `Kenshi\mods\<Nome>\` só de forma explícita (é o que `--instalar` faz).
  `data/`, `gamedata.base` e os mods do Workshop são somente leitura.
- **Save é intocável para escrita.** Ler à vontade; nunca gravar em
  `<Kenshi>/save/`, nem "só pra testar". Save corrompido é campanha perdida e o
  jogo reescreve essa pasta sozinho. Se um dia houver escrita, é em cópia.
  Exceção já autorizada e feita: `ordem.py --aplicar` escreve `data/mods.cfg`,
  e mesmo assim com backup `.bak`.
- **Round-trip é o critério de verdade.** Qualquer mudança em `kenshimod.py`
  exige `python roundtrip.py --tudo` **e** `--saves` passando antes de ser
  considerada pronta (referência: 23/23 mods, 261/261 na amostra de saves,
  52.422/52.422 em `--saves-tudo`, que leva ~15 min). Sem isso, não afirmar que
  funciona.
- **Não inventar semântica de campo.** Vários seguem desconhecidos
  (`instance count`, `mod data type`, os 3 typecodes de mod restantes, a
  semântica fina da cauda do ft15). Se um teste contrariar uma hipótese,
  corrigir o `FORMATO.md` — já aconteceu quatro vezes: o `id` não é o número do
  `strid`; o sufixo do `strid` não indica registro próprio; strid em comum não
  é redundância entre mods; e a cauda do ft15 não é `1..N` sequencial.
- **Rótulo inferido é marcado como inferido.** Os nomes em `TYPECODES-SAVE.md`
  vêm de evidência (o que o registro aponta, onde mora, como se chama), não do
  jogo. Manter a prova ao lado do rótulo.

## Commits

- Um commit = uma mudança lógica, e o repositório funciona em cada commit.
- Assunto em **imperativo**, minúsculo, sem ponto final, até ~50 caracteres
  ("adiciona detector de conflito", não "adicionado" nem "mudanças").
- Corpo (quando não for óbvio) explica **por que**, não o que — o diff já diz o
  que. Linhas até 72 colunas.
- Nada de arquivo gerado no commit, exceto `TYPECODES.md` e
  `TYPECODES-SAVE.md`, que são resultado de pesquisa e servem como documentação.
- Não commitar antes de `roundtrip.py --tudo` passar.
- Mensagem longa quebra o here-string do PowerShell quando tem aspas: escrever
  em arquivo e usar `git commit -F <arquivo>`.

## Caminhos

**Nunca hardcode caminho de instalação em script nem em doc.** Todo acesso ao
jogo passa por `caminhos.py`, que detecta via `KENSHI_DIR`, `kenshi_dir.txt`
(local, ignorado pelo git), registro da Steam + `libraryfolders.vdf`, e por fim
os locais padrão. Nos exemplos de documentação use `<Kenshi>` como placeholder.

Estrutura relevante dentro da instalação:

```
<Kenshi>/data/          gamedata.base + rebirth.mod, Newwworld.mod, Dialogue.mod
<Kenshi>/data/mods.cfg  lista de mods ativos, na ordem de load
<Kenshi>/mods/          mods locais, em <Nome>/<Nome>.mod
<Kenshi>/fcs.def        schema dos tipos de registro (usado pelo typecodes.py)
<Kenshi>/save/<nome>/   um save: quick.save + milhares de .zone e .platoon
<steamapps>/workshop/content/233860   mods do Workshop
```

**Ordem de load: o FIM da lista tem prioridade** (verificado; há descrição de
mod na Steam afirmando o contrário, e está errada). A mesclagem é **por campo**,
não por registro: um mod que só grava `max num attack slots` sobrescreve apenas
esse campo.

## Relação com o KenshiCoop

O [KenshiCoop](https://github.com/nhoral/KenshiCoop) é outro projeto: plugin
nativo em C++ para co-op, que depende do compilador VC++ 2010 (v100). Este
modkit é independente disso — mexe em dados, não em código do jogo. O
`KenshiCoop.mod` (game start "Multiplayer (Wanderer x2)") é a cobaia usada nos
testes por ser pequeno e de conteúdo conhecido.
