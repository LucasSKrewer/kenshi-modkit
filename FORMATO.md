# Formato binário `.mod` / `.base` do Kenshi

Tudo aqui foi verificado contra uma instalação real (Kenshi **1.0.65 x64**,
Steam), com o critério de **round-trip byte-idêntico**: ler e regravar tem que produzir exatamente os mesmos bytes.
Passam **52.445 arquivos**: os 23 mods e dados-base (`python roundtrip.py
--tudo`), incluindo `gamedata.base`, `Dialogue.mod` (39.077 registros) e
`Genesis.mod` (19,7 MB, 26.495 registros); e os 52.422 arquivos de save,
3,4 GB (`python roundtrip.py --saves-tudo`, 15,5 min).

Base de partida: o guia [Kenshi gamedata/mod/save file
format](https://steamcommunity.com/sharedfiles/filedetails/?id=797652627) do
usuário Weaver, no Steam. O `filetype 17` **não** está nesse guia — foi
levantado aqui (ver "Filetype 17" abaixo).

## Tipos

| Notação | Tamanho | O que é |
|---|---|---|
| `L` | 4 bytes | int32 little-endian |
| `F` | 4 bytes | float32 little-endian |
| `?` | 1 byte | bool |
| `S` | 4 + n | string: `L` com o tamanho, seguido de n bytes UTF-8, **sem** NUL final |

Detalhe que custou tempo: por o bool ocupar **1 byte**, qualquer leitor que
assuma campos de 4 bytes dessincroniza logo no primeiro registro e o resto do
arquivo vira lixo aparente.

Neste modkit as strings são mantidas como `bytes` crus, nunca `str`. É o que
garante o round-trip: decodificar e recodificar poderia "consertar" um byte
inválido e mudar o arquivo.

## Cabeçalho — filetype 15 (saves)

Um save do Kenshi não é um arquivo, é uma **pasta com milhares**: um `.save` com
o estado geral, um `.zone` por pedaço do mapa e um `.platoon` por esquadrão.
Todos filetype 15.

```
L  filetype = 15
L  next id           (próximo id livre; nos saves vistos chega à casa do milhão)
L  quantidade de registros
   ... registros, exatamente no mesmo formato dos filetypes 16/17 ...
   ... cauda: sequência de blocos, até o fim do arquivo ...
```

Cada bloco da cauda é `[L quantidade][L valor] *`, e os valores observados são
sequenciais (`1, 2, 3, ...`) — têm cara de pool de ids, mas o **significado não
foi levantado**; para round-trip não é preciso. Um `.zone` tinha 1 bloco, um
`quick.save` tinha 4 (o maior com 736 mil valores), e nos dois a cauda consome o
arquivo exatamente.

**O espaço de typecodes do save é outro.** Os saves usam typecodes que não
aparecem em `data/` — 34 (esquadrão vivo), 94 (estado de cidade), 37 (facção),
9, 39... São tipos de runtime, não as definições do FCS, então
[TYPECODES.md](TYPECODES.md) não vale para saves. Os `strid` também mudam: em
vez de `550-gamedata.base`, vêm como `Saqueadores Sangrentos_9`, e o
`mod data type` é 0.

**NaN sinalizante.** Os saves contêm floats que são NaN com o bit alto da
mantissa em zero. Desempacotar para `float` do Python e reempacotar **quietiza**
esse NaN (liga o bit `0x400000`) e muda o arquivo em um byte. Por isso
`kenshimod.FloatFiel` guarda os bytes originais quando o reempacote não os
reproduz. Sem isso, 4 dos 21 `.save` falhavam o round-trip por 1 byte cada.

⚠️ **Gravar save é outra conversa.** O formato está resolvido, mas save
corrompido é campanha perdida, e o jogo reescreve essa pasta sozinho. Leia à
vontade; grave só em cópia.

## Cabeçalho — filetype 16 (FCS antigo)

```
L  filetype = 16
L  mod version
S  autor
S  descrição
S  dependências   (separadas por vírgula, ex: "gamedata.base,rebirth.mod")
S  references     (separadas por vírgula; normalmente vazio)
L  desconhecido   (valores grandes, ex: 1535115, 5007293 — semântica não levantada)
L  quantidade de registros
```

## Cabeçalho — filetype 17 (FCS novo)

Aparece em `rebirth.mod`, `Dialogue.mod`, `Genesis.mod`, `No Mine Node Cap.mod`
e `DeadlandsClouds.mod`. **O corpo dos registros é idêntico ao do 16**; só o
cabeçalho mudou.

```
L  filetype = 17
L  deslocamento dos dados   <- somar 16 = offset onde o 1º registro começa
L  mod version
S  autor
S  descrição
S  dependências
S  references
   ... miolo NÃO DECODIFICADO ...
L  quantidade de registros  <- sempre os 4 bytes imediatamente antes dos dados
```

O miolo tem uma lista de mods relacionados no formato
`[?: quantidade] ( S nome + L + L ) *` mais alguns campos que não fecharam
contagem entre os três arquivos de amostra. Como o cabeçalho carrega o
deslocamento explícito dos dados, o modkit trata esse miolo como **blob opaco**
(`mod["middle"]`): preserva cru na gravação e recalcula o deslocamento. Isso
permite editar registros e até as strings do cabeçalho com round-trip exato —
só não permite mexer na lista de mods relacionados.

Como foi descoberto: o campo em offset 4 valia `0x177` no `No Mine Node Cap` e
os registros começavam em `0x187`; `0xc7` → `0xd7` no `DeadlandsClouds`.
Diferença constante de 16 nos três arquivos. O offset não alinhado a 4 bytes
(`0x187`) foi a pista de que havia campo de 1 byte no cabeçalho.

## Registro (igual nos filetypes 16 e 17)

```
L  instance count      (semântica incerta: valores como 1119, 891)
L  typecode            (tipo do registro — ver "typecodes" abaixo)
L  id                  (0 na maioria dos registros da base; sequencial nos
                        registros NOVOS de um mod: 1, 2, 3...)
S  nome                (o nome que aparece no FCS)
S  strid               ("<número>-<arquivo de origem>", ex: "550-gamedata.base")
L  mod data type       (16, 129, ou negativos grandes tipo -2147483646)

7 seções de campos tipados, nesta ordem, cada uma com a contagem na frente:
L  n  então n *  ( S chave  +  ? valor )     bool
L  n  então n *  ( S chave  +  F valor )     float
L  n  então n *  ( S chave  +  L valor )     long
L  n  então n *  ( S chave  +  F F F )       vec3
L  n  então n *  ( S chave  +  F F F F )     vec4
L  n  então n *  ( S chave  +  S valor )     string
L  n  então n *  ( S chave  +  S valor )     filename

extra data (as REFERÊNCIAS entre registros):
L  quantidade de categorias
   então, por categoria:  S nome  +  L quantidade de itens
      então, por item:    S strid do alvo  +  L val0  +  L val1  +  L val2

instances (posicionamento no mundo):
L  quantidade
   então, por instância: S strid + S alvo + F tx F ty F tz + F rw F rx F ry F rz
                         + L quantidade de estados + S estado *
```

**Os nomes dos campos estão dentro do arquivo.** Não é preciso schema nenhum
para ler um mod de forma legível — `armour grade`, `female chance`,
`start pos X` vêm como string no próprio `.mod`. O `fcs.def` que o jogo instala
(114 tipos de registro, com defaults e descrição de cada campo) serve para
validar e para saber o que existe, não para decodificar.

Um mod só grava os campos que ele **sobrescreve**; o resto é herdado da base.
Por isso `set_campo()` devolve `False` quando o campo não está no registro:
adicionar campo novo é diferente de alterar campo existente.

## Referências e ordem de load

O `strid` guarda o arquivo de **origem** do registro, não quem o modificou.
Quando o Genesis altera um personagem da base, o registro dele continua sendo
`997-gamedata.base`. Consequências práticas:

- não dá para saber se uma referência está pendurada olhando um mod isolado —
  precisa indexar a ordem de load (é o que `validar.py` faz);
- registros com sufixos como `clothes_v1.mod` existem **dentro** do
  `gamedata.base` (o jogo foi montado a partir de vários arquivos), então esse
  sufixo não significa que exista um mod `clothes_v1.mod` instalado.

## O que segue desconhecido

1. **Mapa de typecodes**: **70 dos 78** typecodes vistos estão identificados em
   [TYPECODES.md](TYPECODES.md), levantados por `typecodes.py` com três canais
   independentes (conjunto de campos × `fcs.def`; para onde as referências reais
   apontam; nome auto-gerado dos registros). Faltam 8, todos grupos minúsculos
   (1 a 3 registros). Note que o `fcs.def` **não lista todos os tipos**: o
   typecode 31, com 21 mil registros, é `DIALOG_ACTION` e não aparece lá — só o
   canal de nomes o alcança.
2. **`instance count`** no início do registro (1119, 891...): não é a
   quantidade de instances da seção final.
3. **`mod data type`** (16, 129, negativos grandes): provavelmente sinaliza
   "registro novo" vs "registro alterado" vs "registro removido".
4. **`desconhecido` do cabeçalho ft16** e o miolo do ft17.
5. **Significado da cauda do filetype 15** — listas de ids sequenciais, formato
   entendido, propósito não.
6. **Typecodes dos saves** (34, 94, 37, 9, 39...): identificados só por
   observação dos nomes. O `fcs.def` não descreve tipos de runtime, então os
   três canais do `typecodes.py` não alcançam esses.
