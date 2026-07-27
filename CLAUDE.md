# Instruções do projeto — kenshi-modkit

## O que é

Biblioteca Python que lê e grava o formato binário de mods do Kenshi, para
tratar mod como código em vez de cliques no FCS. Formato documentado em
`FORMATO.md`; estado atual e próximos passos no `README.md`.

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
- **Round-trip é o critério de verdade.** Qualquer mudança em `kenshimod.py`
  exige `python roundtrip.py --tudo` passando 23/23 antes de ser considerada
  pronta. Sem isso, não afirmar que funciona.
- **Não inventar semântica de campo.** Vários campos seguem desconhecidos
  (`instance count`, `mod data type`, typecodes). Se um teste contrariar uma
  hipótese, corrigir o `FORMATO.md` — já aconteceu duas vezes (o `id` não é o
  número do `strid`; o sufixo do `strid` não indica registro próprio).

## Commits

- Um commit = uma mudança lógica, e o repositório funciona em cada commit.
- Assunto em **imperativo**, minúsculo, sem ponto final, até ~50 caracteres
  ("adiciona detector de conflito", não "adicionado" nem "mudanças").
- Corpo (quando não for óbvio) explica **por que**, não o que — o diff já diz o
  que. Linhas até 72 colunas.
- Nada de arquivo gerado no commit, exceto `TYPECODES.md`, que é resultado de
  pesquisa e serve como documentação.
- Não commitar antes de `roundtrip.py --tudo` passar.

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
<steamapps>/workshop/content/233860   mods do Workshop
```

## Relação com o KenshiCoop

O [KenshiCoop](https://github.com/nhoral/KenshiCoop) é outro projeto: plugin
nativo em C++ para co-op, que depende do compilador VC++ 2010 (v100). Este
modkit é independente disso — mexe em dados, não em código do jogo. O
`KenshiCoop.mod` (game start "Multiplayer (Wanderer x2)") é a cobaia usada nos
testes por ser pequeno e de conteúdo conhecido.
