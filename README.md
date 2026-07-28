# kenshi-modkit

Ler, editar e **gravar** mods do Kenshi (`.mod` / `.base`) por script Python, sem
abrir o Forgotten Construction Set. Python 3.12, **zero dependências** além da
biblioteca padrão.

Motivo de existir: o FCS é GUI. Com o formato binário mapeado, mod passa a ser
código — diff legível, edição em massa, geração de variantes e, o que nenhuma
ferramenta existente faz, **detecção de conflito entre os mods instalados**.

O formato está documentado em [FORMATO.md](FORMATO.md), incluindo o
`filetype 17`, que a especificação pública da comunidade não cobre.

## Estado

| | |
|---|---|
| Ler / gravar filetype 16 e 17 | ✅ **24/24 arquivos** round-trip byte-idêntico |
| Editar campo, referência, strings do cabeçalho | ✅ |
| Criar registro por clonagem | ✅ validado in-game |
| Kenshi carregar mod gerado por script | ✅ validado in-game (2026-07-27) |
| Mapa de typecodes | ✅ **70 de 78** com certeza ([TYPECODES.md](TYPECODES.md)) |
| Detector de conflito | ✅ |
| Criar registro do zero | ❌ depende dos typecodes que faltam |
| Filetype 15 (saves) | ❌ não implementado |

O round-trip byte-idêntico é o critério de verdade do projeto: ler um arquivo e
regravá-lo tem que produzir exatamente os mesmos bytes. Sem isso, gravar mod por
script é chute. Passa em 24 arquivos, incluindo `gamedata.base`, `Dialogue.mod`
(39.077 registros) e o **Genesis.mod** — 19,7 MB, **26.495 registros**.

O teste in-game (`teste_ingame.py`) gerou um mod com um game start **editado**
(1000 → 7777 gatos) e outro **criado por clonagem**, e os dois apareceram na tela
de novo jogo.

## Ferramentas

| | |
|---|---|
| `kenshimod.py` | a biblioteca: `ler`, `gravar`, `clonar_registro`, `substituir_em_ids`, `campo`/`set_campo` |
| `caminhos.py` | detecta a instalação do Kenshi (nada de caminho fixo) |
| `roundtrip.py` | o teste de fidelidade — o que autoriza confiar no parser |
| `dump.py` | `.mod` → texto legível, `--json` (versionável), `--tipos` |
| `validar.py` | referência pendurada / strid duplicado, resolvendo contra a ordem de load |
| `conflitos.py` | quais mods brigam pelo mesmo registro e qual valor ganha |
| `ordem.py` | recomenda ordem de load justificada; `--aplicar` escreve o `mods.cfg` (com backup) |
| `typecodes.py` | levanta o mapa de typecodes correlacionando registros com o `fcs.def` |
| `teste_ingame.py` | gera um mod que edita **e** cria registro, para validar no jogo |
| `pesquisa/` | as sondas da engenharia reversa ([método](pesquisa/LEIA.md)) |

## Instalação

Não tem. Clone e rode com Python 3.12 — nenhuma dependência.

A pasta do Kenshi é **detectada** (`caminhos.py`): variável `KENSHI_DIR`, arquivo
`kenshi_dir.txt` ao lado dos scripts, registro da Steam + `libraryfolders.vdf`, e
por fim os locais padrão. Para conferir o que ele achou:

```bash
python caminhos.py
```

## Uso

```bash
python roundtrip.py --tudo
python dump.py "<Kenshi>/mods/KenshiCoop/KenshiCoop.mod"
python validar.py "<Kenshi>/mods/KenshiCoop/KenshiCoop.mod"
python conflitos.py --todos          # e se eu ativasse todos os instalados?
python typecodes.py
python teste_ingame.py --instalar
```

```python
import kenshimod as km

import caminhos

mod = km.ler(os.path.join(caminhos.mods_dir(), "Foo", "Foo.mod"))
for rec in mod["records"]:
    if km.campo(rec, "long", "money") is not None:
        km.set_campo(rec, "long", "money", 5000)
km.gravar(r"out\Foo\Foo.mod", mod)
```

Convenção do jogo: o mod tem que estar em `Kenshi\mods\<Nome>\<Nome>.mod` para
aparecer no launcher, e a ordem de load ativa vive em `data\mods.cfg`.

## Exemplo de saída do detector de conflito

Sobrescrever não é necessariamente problema — dois mods podem mexer em campos
diferentes do mesmo registro. Conflito de verdade é mesmo campo, valor diferente,
e é isso que a ferramenta separa:

```
28902 registros tocados, 856 por 2+ mods
578 conflitos de campo (mesmo campo, valor diferente)

mods que se sobrepõem (quantidade de registros em comum):
     508  Genesis.mod  x  Slopeless.mod
     131  Genesis.mod  x  shops have more items +.mod
      43  AnimationOverhaul.mod  x  Genesis.mod
```

## Aviso

Ferramenta de terceiros, sem relação com a Lo-Fi Games. Escreve mod na pasta do
jogo apenas quando você pede explicitamente (`--instalar`); `data/`,
`gamedata.base` e os mods do Workshop são tratados como somente leitura. Ainda
assim, faça backup do que importa antes de gravar em cima.

## Créditos

- Especificação dos filetypes 15 e 16: guia
  [Kenshi gamedata/mod/save file format](https://steamcommunity.com/sharedfiles/filedetails/?id=797652627)
  do usuário **Weaver**, no Steam. O `filetype 17` foi levantado neste projeto.
- Trabalho anterior em Python:
  [Superfly-Johnson/kenshi-mod-tools](https://github.com/Superfly-Johnson/kenshi-mod-tools) (MIT).

MIT — ver [LICENSE](LICENSE).
