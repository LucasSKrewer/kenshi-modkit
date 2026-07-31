"""Gera um mod de QoL a partir de um ajuste declarado aqui, sem abrir o FCS.

A ideia é ter os números em um lugar legível e versionável, e o `.mod` sair
disso — em vez de clicar no FCS e depois não lembrar o que foi mexido.

Cada registro gerado é uma **modificação** de um registro da base: leva só os
campos alterados, com `mod data type = -2147483647`, exatamente como os mods
publicados fazem. Isso importa porque o Kenshi mescla **por campo**: alterar
`vendor money` não desfaz o que outro mod fez no resto daquele registro.

Este mod tem que carregar POR ÚLTIMO para valer (no Kenshi, o fim da lista tem
prioridade). Rode `python ordem.py` depois de instalar.

    python qol.py                (gera em out/, mostra o que mudou)
    python qol.py --instalar     (copia pra pasta mods do Kenshi)
"""
import os
import shutil
import sys

import caminhos as loc
import kenshimod as km
import ordemload as ol

NOME = "Smooth Sands"

# De onde sair o valor de partida dos multiplicadores. Com um overhaul ativo
# (Genesis), o valor que vale no jogo NÃO é o vanilla: multiplicar o vanilla
# sobrescreveria o rebalanceamento do overhaul. Então o padrão é ler a ordem de
# load ativa (data/mods.cfg), menos este próprio mod e menos os que ele
# substitui -- senão multiplicaríamos valores já multiplicados.
USAR_ORDEM_ATIVA = True
SUBSTITUIDOS = [
    "shops have more items +.mod",
    "shops have more money.mod",
    "No Mine Node Cap.mod",
    "Attack Slots x2.mod",
]

AJUSTES = {
    # nós de mineração: quanto minério cabe antes de parar de produzir
    "mineracao": {
        "ativo": True,
        "estoque": 999,          # vanilla: 5 (cobre/ferro), 10 (pedra)
        "alvos": ["copper mine", "Ore mine", "Stone mine"],
    },
    # lojas: só as que de fato vendem (têm lista de vendedores)
    "lojas": {
        "ativo": True,
        "dinheiro_mult": 5,      # multiplica o dinheiro do comerciante
        "estoque_mult": 2,       # multiplica a quantidade de itens
        "teto_dinheiro": 500000,
    },
    # quantos inimigos podem atacar ao mesmo tempo.
    # É um MÍNIMO, não um valor absoluto: se a sua ordem de load já dá mais
    # (o Genesis dá 5), o ajuste não mexe. Ajuste de QoL não pode piorar o que
    # já está melhor.
    "slots_ataque": {
        "ativo": True,
        "minimo": 2,             # vanilla: 1
    },
    # ganho de experiência global
    "treino": {
        "ativo": True,
        "mult": 1.5,             # multiplica o "exp gain multiplier" (vanilla 3.0)
    },
}

# O campo desconhecido do cabeçalho ft16 (ver FORMATO.md) não tem semântica
# levantada; usamos o valor de um mod publicado que o jogo aceita.
CABECALHO_DESCONHECIDO = 1535115


def arquivos_de_partida():
    """os arquivos cujos valores servem de base para os multiplicadores"""
    if not USAR_ORDEM_ATIVA:
        return list(loc.arquivos_base())
    return ol.arquivos(excluir={f"{NOME}.mod", *SUBSTITUIDOS})


# a visão efetiva do jogo (índice mesclado, registro de modificação, cabeçalho)
# vive em ordemload.py, compartilhada com os outros geradores
indexar_base = ol.indexar
modificacao = ol.modificacao


def gerar():
    arquivos = arquivos_de_partida()
    idx = indexar_base(arquivos)
    print(f"valores de partida: {len(idx)} registros de {len(arquivos)} arquivo(s)")
    if USAR_ORDEM_ATIVA:
        print(f"  ordem usada: {', '.join(os.path.basename(a) for a in arquivos)}")
    idx_vanilla = indexar_base(loc.arquivos_base()) if USAR_ORDEM_ATIVA else idx

    def vanilla(strid, secao, campo):
        par = idx_vanilla.get(strid)
        return km.campo(par[0], secao, campo) if par else None

    divergentes, exemplos = 0, []
    registros, relato = [], []

    m = AJUSTES["mineracao"]
    if m["ativo"]:
        n = 0
        for (base_rec, _arq) in idx.values():
            if base_rec["typecode"] != 62:
                continue
            if km.t(base_rec["name"]) not in m["alvos"]:
                continue
            for cat, itens in base_rec["extra"]:
                if km.t(cat) != "produces" or not itens:
                    continue
                if itens[0][1] >= m["estoque"]:
                    relato.append(f"  {km.t(base_rec['name'])}: sua ordem já dá "
                                  f"{itens[0][1]} — não mexo")
                    continue
                rec = modificacao(base_rec)
                rec["extra"] = [(cat, [(alvo, m["estoque"], v1, v2)
                                       for alvo, _v0, v1, v2 in itens])]
                registros.append(rec)
                n += 1
                relato.append(f"  {km.t(base_rec['name'])}: estoque do nó "
                              f"{itens[0][1]} -> {m['estoque']}")
        print(f"mineração: {n} registros")

    lj = AJUSTES["lojas"]
    if lj["ativo"]:
        n = 0
        for (base_rec, _arq) in idx.values():
            if base_rec["typecode"] != 52:
                continue
            tem_loja = any(km.t(c) == "vendors" and it for c, it in base_rec["extra"])
            if not tem_loja:
                continue
            dinheiro = km.campo(base_rec, "long", "vendor money") or 0
            estoque = km.campo(base_rec, "long", "vendors fill total amount") or 0
            if dinheiro <= 0 and estoque <= 0:
                continue
            van = vanilla(base_rec["strid"], "long", "vendor money") or 0
            if van != dinheiro:
                divergentes += 1
                if len(exemplos) < 4:
                    exemplos.append(f"    {km.t(base_rec['name'])[:26]:<26} "
                                    f"vanilla {van} -> na sua ordem {dinheiro} "
                                    f"-> gerado {min(dinheiro * lj['dinheiro_mult'], lj['teto_dinheiro'])}")
            rec = modificacao(base_rec)
            if dinheiro > 0:
                rec["long"].append((km.b("vendor money"),
                                    min(dinheiro * lj["dinheiro_mult"],
                                        lj["teto_dinheiro"])))
            if estoque > 0:
                rec["long"].append((km.b("vendors fill total amount"),
                                    estoque * lj["estoque_mult"]))
            registros.append(rec)
            n += 1
        print(f"lojas: {n} registros")
        relato.append(f"  lojas: dinheiro x{lj['dinheiro_mult']} (teto "
                      f"{lj['teto_dinheiro']:,}), estoque x{lj['estoque_mult']}")

    sa, tr = AJUSTES["slots_ataque"], AJUSTES["treino"]
    if sa["ativo"] or tr["ativo"]:
        for (base_rec, _arq) in idx.values():
            if base_rec["typecode"] != 27:
                continue
            if km.campo(base_rec, "long", "max num attack slots") is None:
                continue
            rec = modificacao(base_rec)
            if sa["ativo"]:
                atual = km.campo(base_rec, "long", "max num attack slots")
                if atual is not None and atual >= sa["minimo"]:
                    relato.append(f"  slots de ataque: sua ordem já dá {atual} "
                                  f"(mínimo pedido: {sa['minimo']}) — não mexo")
                else:
                    rec["long"].append((km.b("max num attack slots"),
                                        sa["minimo"]))
                    relato.append(f"  slots de ataque: {atual} -> {sa['minimo']}")
            if tr["ativo"]:
                atual = km.campo(base_rec, "float", "exp gain multiplier")
                if atual is not None:
                    novo = round(float(atual) * tr["mult"], 3)
                    rec["float"].append((km.b("exp gain multiplier"), novo))
                    relato.append(f"  ganho de XP: {atual} -> {novo}")
            registros.append(rec)
            print("constantes globais: 1 registro")
            break

    # Dependências são os ARQUIVOS de onde vieram os registros que tocamos --
    # não o sufixo do strid, que guarda a origem histórica do registro (nomes
    # como "__Fixes.mod" que existem dentro do gamedata.base e não são arquivo.)
    origens = {idx[rec["strid"]][1] for rec in registros if rec["strid"] in idx}
    mod = {
        "filetype": 16,
        "mod_version": 1,
        "author": km.b("kenshi-modkit"),
        "description": km.b(
            f"{NOME} - ajustes de qualidade de vida gerados por script "
            f"(kenshi-modkit). Mexe so nos campos listados: estoque de no de "
            f"mineracao, dinheiro e estoque de loja, slots de ataque e ganho "
            f"de XP. Carregue por ULTIMO para os valores valerem."),
        "dependencies": km.b(",".join(sorted(origens))),
        "references": b"",
        "unknown": CABECALHO_DESCONHECIDO,
        "records": registros,
        "tail": b"",
    }
    destino_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "out", NOME)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, f"{NOME}.mod")
    tam = km.gravar(destino, mod)
    print(f"\ngravado: {destino} ({tam:,} bytes, {len(registros)} registros)")
    print(f"dependências: {km.t(mod['dependencies'])}")
    print("\no que muda:")
    for linha in relato[:12]:
        print(linha)
    if USAR_ORDEM_ATIVA:
        print(f"\nvalores que a sua ordem de load já tinha mudado em relação ao "
              f"vanilla: {divergentes}")
        for e in exemplos:
            print(e)
        if not divergentes:
            print("    (nenhum: nos alvos deste mod, a sua ordem usa os valores "
                  "vanilla, então calcular sobre a base dava no mesmo)")

    relido = km.ler(destino)
    with open(destino, "rb") as f:
        if km.serializar(relido) != f.read():
            raise SystemExit("ERRO: o arquivo gerado não relê estável")
    print("\nreparse estável: ok")
    return destino


if __name__ == "__main__":
    arquivo = gerar()
    if "--instalar" in sys.argv:
        pasta = os.path.join(loc.mods_dir(), NOME)
        os.makedirs(pasta, exist_ok=True)
        shutil.copy2(arquivo, os.path.join(pasta, f"{NOME}.mod"))
        print(f"instalado: {os.path.join(pasta, f'{NOME}.mod')}")
        print("Marque no launcher e deixe por ÚLTIMO na lista.")
    else:
        print("\n(rode com --instalar pra copiar pra pasta mods do Kenshi)")
