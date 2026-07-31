"""Cria um recruta único, contratável em bar, sem abrir o FCS.

Como um recruta de bar funciona no Kenshi (levantado dos dados, não da
documentação): um CHARACTER com `unique`/`named`, referências de raça, stats,
personalidade e equipamento, mais um `dialogue` -- e é o diálogo que carrega o
PREÇO (o registro chama-se literalmente `hire me 5000`). O personagem entra no
mundo porque alguma `Recruits list <região>` o lista em `choosefrom list`, e as
cidades apontam para essa lista em `bar squads`.

Duas decisões de projeto, ambas para reduzir risco:

- O personagem é **clonado** de um recruta que já existe e funciona, em vez de
  montado do zero. Herda typecode, pacotes de diálogo e a fiação toda.
- A lista de recrutas é modificada a partir da **lista efetiva** (já com os
  mods ativos). Categoria de referência é SUBSTITUÍDA na mesclagem, não somada:
  escrever só o recruta novo apagaria os do Genesis.

    python recruta.py               (gera em out/)
    python recruta.py --instalar    (copia pra pasta mods do Kenshi)
"""
import os
import shutil
import sys

import caminhos as loc
import kenshimod as km
import ordemload as ol

NOME_MOD = "TENSOx"

RECRUTA = {
    "nome": "TENSOx",
    # doador: já está na lista do Império, katana + horse chopper, diálogo de
    # 5000 gatos. É o arquétipo pedido; só sobe o nível.
    "doador": (1, "Sword for hire 15"),
    "stats": "40",              # doador vem com '15'; ver tc25 para as opções
    "lista": (52, "Recruits list Empire"),
    "peso": 10,                 # chance relativa dele aparecer na lista
    # O doador é um recruta GENÉRICO e traz a configuração errada para alguém
    # único. Estes valores são os que Beep e Ruka usam (conferido nos dados):
    "campos": {
        # contraintuitivo: no fcs.def, `named` = "nome sorteado da lista de
        # nomes". Deixar 1 faz o jogo IGNORAR "TENSOx" e sortear outro.
        ("bool", "named"): 0,
        # "só vai existir uma vez no mundo" -- é o que faz dele único
        ("bool", "unique"): 1,
        # 0 = sempre homem, 100 = sempre mulher, valor intermediário = sorteio.
        # O doador vem com 35 (sorteia), o que não faz sentido para personagem
        # fixo. Beep usa 0, Ruka usa 100. Trocar aqui é uma linha.
        ("long", "female chance"): 0,
        ("long", "stats randomise"): 0,
    },
}


def clonar_para_novo(base_rec, novo_strid, novo_nome):
    """cópia com id próprio: registro NOVO do mod (mod data type 16)"""
    novo = km.clonar_registro(base_rec, novo_strid, novo_nome)
    novo["mod_data_type"] = 16          # 16 = registro novo; -2147483647 = alterado
    novo["id"] = int(novo_strid.split("-", 1)[0])
    return novo


def trocar_ref(rec, categoria, novo_alvo, vals=(0, 0, 0)):
    """substitui a lista de uma categoria de referência por um alvo só"""
    alvo = km.b(categoria)
    itens = [(km.b(novo_alvo), *vals)]
    for i, (cat, _it) in enumerate(rec["extra"]):
        if cat == alvo:
            rec["extra"][i] = (cat, itens)
            return True
    rec["extra"].append((alvo, itens))
    return False


def gerar():
    arquivos = ol.arquivos(excluir={f"{NOME_MOD}.mod"})
    idx = ol.indexar(arquivos)
    nomes = ol.por_nome(idx)
    print(f"índice efetivo: {len(idx)} registros de {len(arquivos)} arquivos")

    if RECRUTA["doador"] not in nomes:
        raise SystemExit(f"não achei o doador {RECRUTA['doador']}")
    doador_strid, doador, _arq = nomes[RECRUTA["doador"]]
    print(f"doador: {km.t(doador['name'])} ({km.t(doador_strid)})")

    novo_strid = f"1-{NOME_MOD}.mod"
    personagem = clonar_para_novo(doador, novo_strid, RECRUTA["nome"])

    for (secao, campo), valor in RECRUTA["campos"].items():
        antes = km.campo(personagem, secao, campo)
        if not km.set_campo(personagem, secao, campo, valor):
            raise SystemExit(f"o doador não tem o campo {campo!r} em {secao} — "
                             f"sem ele o clone fica com a configuração de "
                             f"recruta genérico")
        print(f"  {campo}: {antes} -> {valor}")

    chave_stats = (25, RECRUTA["stats"])
    if chave_stats not in nomes:
        raise SystemExit(f"não achei o registro de stats {RECRUTA['stats']!r}")
    stats_strid = nomes[chave_stats][0]
    trocar_ref(personagem, "stats", km.t(stats_strid))
    antes = [km.t(idx[a][0]["name"]) if a in idx else km.t(a)
             for a, *_ in ol.refs(doador, "stats")]
    print(f"stats: {antes} -> ['{RECRUTA['stats']}']")

    dialogo = [km.t(idx[a][0]["name"]) if a in idx else km.t(a)
               for a, *_ in ol.refs(personagem, "dialogue")]
    print(f"diálogo de contratação (é o preço): {dialogo}")

    # a lista de recrutas, partindo da EFETIVA e acrescentando o novo
    if RECRUTA["lista"] not in nomes:
        raise SystemExit(f"não achei a lista {RECRUTA['lista']}")
    lista_strid, lista_rec, _a = nomes[RECRUTA["lista"]]
    atuais = ol.refs(lista_rec, "choosefrom list")
    if any(km.t(a) == novo_strid for a, *_ in atuais):
        atuais = [i for i in atuais if km.t(i[0]) != novo_strid]
    mod_lista = ol.modificacao(lista_rec)
    mod_lista["extra"] = [(km.b("choosefrom list"),
                           atuais + [(km.b(novo_strid), RECRUTA["peso"], 0, 0)])]
    print(f"lista '{RECRUTA['lista'][1]}': {len(atuais)} recrutas -> "
          f"{len(atuais) + 1} (preservando os existentes)")

    registros = [personagem, mod_lista]
    mod = ol.cabecalho(
        NOME_MOD,
        f"{RECRUTA['nome']} - recruta unico contratavel nos bares do Imperio "
        f"Unido. Espadachim veterano. Gerado por script com o kenshi-modkit. "
        f"Carregue depois dos overhauls.",
        registros, idx)
    # o personagem é registro NOVO: não tem origem na base, então a dependência
    # dele vem do que ele referencia (raça, stats, diálogo...), já coberto pelos
    # arquivos do índice
    origens = set(km.t(mod["dependencies"]).split(",")) if mod["dependencies"] else set()
    for cat, itens in personagem["extra"]:
        for alvo, *_ in itens:
            if alvo in idx:
                origens.add(idx[alvo][1])
    origens.discard("")
    mod["dependencies"] = km.b(",".join(sorted(origens)))

    destino_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "out", NOME_MOD)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, f"{NOME_MOD}.mod")
    tam = km.gravar(destino, mod)
    print(f"\ngravado: {destino} ({tam:,} bytes, {len(registros)} registros)")
    print(f"dependências: {km.t(mod['dependencies'])}")

    relido = km.ler(destino)
    with open(destino, "rb") as f:
        if km.serializar(relido) != f.read():
            raise SystemExit("ERRO: o arquivo gerado não relê estável")
    print("reparse estável: ok")
    return destino


if __name__ == "__main__":
    arquivo = gerar()
    if "--instalar" in sys.argv:
        pasta = os.path.join(loc.mods_dir(), NOME_MOD)
        os.makedirs(pasta, exist_ok=True)
        shutil.copy2(arquivo, os.path.join(pasta, f"{NOME_MOD}.mod"))
        print(f"\ninstalado: {os.path.join(pasta, f'{NOME_MOD}.mod')}")
        print("Marque no launcher, depois dos overhauls.")
    else:
        print("\n(rode com --instalar pra copiar pra pasta mods do Kenshi)")
