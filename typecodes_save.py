"""Identifica os typecodes de RUNTIME, os que só aparecem em save.

O `fcs.def` descreve as definições do FCS, não o que o jogo cria em partida.
Então os três canais do `typecodes.py` não alcançam typecodes como 34 ou 94.
Aqui o canal é outro, e é semântico: **para onde o registro aponta**. Um
registro que referencia um SQUAD_TEMPLATE, uma FACTION e uma TOWN só pode ser
um esquadrão vivo. Somando a isso em que tipo de arquivo ele mora (`.platoon`,
`.zone`, `.save`) e como se chama, dá pra nomear com evidência.

Nada aqui é autoridade do jogo: são rótulos inferidos, marcados como tais.

    python typecodes_save.py            (analisa e escreve TYPECODES-SAVE.md)
    python typecodes_save.py --tc 34    (detalha um typecode)
"""
import glob
import os
import sys
from collections import Counter, defaultdict

import caminhos
import kenshimod as km
import typecodes as tc_mod

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "TYPECODES-SAVE.md")

# Rótulos INFERIDOS a partir da evidência que a própria ferramenta imprime
# (campos, nomes, para onde aponta, em que arquivo mora). Não são nomes oficiais
# do jogo -- o fcs.def não descreve tipo de runtime. Onde não há evidência
# suficiente, fica de fora de propósito.
ROTULOS = {
    34: ("esquadrão vivo", "nomes `<Facção>_<n>`; campos `intact`, `dead`, "
         "`imprisoned`, `squad index`, `hometownCS`"),
    94: ("estado de cidade + estoque das lojas", "nomes literais "
         "`Town state <cidade>`; 175 mil refs `trade goods` apontando para ITEM"),
    37: ("estado de facção", "aponta para FACTION; um por facção"),
    9: ("controle de facção em runtime", "campos `num plats`, `num poss`, "
        "`num requests`, `num actives`, `fwc id`, `faction`"),
    35: ("objeto colocado no mundo (prédio/mobília)", "campos `foliage`, "
         "`is inside building`, `destroyed`, `world Y pos`; só em `.zone`"),
    66: ("dados de raça do personagem", "um por `.platoon`, aponta para RACE"),
    4: ("ITEM", "mesmo typecode das definições: instância de item no mundo"),
    25: ("STATS", "mesmo typecode das definições: stats em runtime"),
}


def nomes_das_definicoes():
    """typecode de definição -> nome, reaproveitando o mapa já levantado"""
    tipos = tc_mod.ler_fcs_def()
    campos, _quantos, _ex = tc_mod.campos_por_typecode(caminhos.arquivos_base())
    saida = {}
    for tc, vistos in campos.items():
        placar = tc_mod.casar(vistos, tipos)
        if placar:
            saida[tc] = placar[0][2]
    return saida


def indexar_definicoes():
    """strid -> typecode, para saber o que um save está referenciando"""
    idx = {}
    for c in caminhos.arquivos_base():
        if os.path.exists(c):
            for rec in km.ler(c)["records"]:
                idx[rec["strid"]] = rec["typecode"]
    return idx


def amostra_de_saves(por_tipo=6):
    raiz = os.path.join(caminhos.kenshi_dir(), "save")
    escolhidos = []
    for ext in ("save", "zone", "platoon"):
        achados = sorted(glob.glob(os.path.join(raiz, "**", f"*.{ext}"),
                                   recursive=True),
                         key=os.path.getsize, reverse=True)
        escolhidos += [(ext, c) for c in achados[:por_tipo]]
    return escolhidos


def analisar():
    idx_def = indexar_definicoes()
    nomes_def = nomes_das_definicoes()
    dados = defaultdict(lambda: {
        "n": 0, "arquivos": Counter(), "campos": Counter(),
        "aponta_def": Counter(), "aponta_save": Counter(), "exemplos": [],
    })
    for ext, caminho in amostra_de_saves():
        mod = km.ler(caminho)
        locais = {rec["strid"]: rec["typecode"] for rec in mod["records"]}
        for rec in mod["records"]:
            d = dados[rec["typecode"]]
            d["n"] += 1
            d["arquivos"][ext] += 1
            if len(d["exemplos"]) < 4:
                nome = km.t(rec["name"]).strip()
                if nome and nome not in d["exemplos"]:
                    d["exemplos"].append(nome)
            for secao, _, _ in km.SECOES:
                for k, _v in rec[secao]:
                    d["campos"][km.t(k)] += 1
            for cat, items in rec["extra"]:
                d["campos"][km.t(cat) + " (ref)"] += len(items)
                for alvo, *_ in items:
                    if alvo in idx_def:
                        alvo_tc = idx_def[alvo]
                        d["aponta_def"][nomes_def.get(alvo_tc, f"tc{alvo_tc}")] += 1
                    elif alvo in locais:
                        d["aponta_save"][locais[alvo]] += 1
    return dados


def main(argv):
    dados = analisar()
    if "--tc" in argv:
        alvo = int(argv[argv.index("--tc") + 1])
        d = dados.get(alvo)
        if not d:
            print(f"typecode {alvo} não aparece na amostra")
            return 1
        print(f"typecode {alvo}: {d['n']} registros")
        print(f"  arquivos: {dict(d['arquivos'])}")
        print(f"  exemplos de nome: {d['exemplos']}")
        print("  campos mais comuns:")
        for c, n in d["campos"].most_common(15):
            print(f"    {n:>8}x  {c}")
        print("  aponta para definições:")
        for t, n in d["aponta_def"].most_common(10):
            print(f"    {n:>8}x  {t}")
        print(f"  aponta para outros registros de save: "
              f"{dict(d['aponta_save'].most_common(6))}")
        return 0

    linhas = sorted(dados.items(), key=lambda kv: -kv[1]["n"])
    print(f"{'tc':>5} {'regs':>8}  {'onde':<22} aponta para (definições)")
    for tc, d in linhas:
        onde = ",".join(f"{k}:{v}" for k, v in d["arquivos"].most_common())
        aponta = ", ".join(f"{t}({n})" for t, n in d["aponta_def"].most_common(3))
        print(f"{tc:>5} {d['n']:>8}  {onde[:22]:<22} {aponta[:60]}")

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write("# Typecodes de runtime (saves)\n\n")
        f.write("Gerado por `python typecodes_save.py`. Estes typecodes **não** "
                "aparecem em `data/` e **não** estão no `fcs.def`: são o que o "
                "jogo cria em partida. Os nomes aqui são **inferidos** do que "
                "cada registro referencia, de em que arquivo ele mora e de como "
                "se chama — não são autoridade do jogo.\n\n")
        f.write("| typecode | o que é (inferido) | registros | onde mora | "
                "exemplos de nome | campos típicos |\n")
        f.write("|---|---|---|---|---|---|\n")
        for tc, d in linhas:
            onde = ", ".join(f"`.{k}`" for k, _ in d["arquivos"].most_common())
            ex = "; ".join(e[:26] for e in d["exemplos"][:2]) or "—"
            campos = ", ".join(f"`{c}`" for c, _ in d["campos"].most_common(4))
            rotulo = ROTULOS.get(tc, ("não identificado", ""))[0]
            f.write(f"| {tc} | **{rotulo}** | {d['n']} | {onde} | {ex} | "
                    f"{campos} |\n")
        f.write("\n## Por que cada rótulo\n\n")
        for tc, (rotulo, prova) in sorted(ROTULOS.items()):
            f.write(f"- **{tc} — {rotulo}**: {prova}.\n")
        f.write("\n## Como os registros de save se ligam\n\n")
        f.write("Diferente dos mods, um registro de save **não** referencia "
                "outro pelo `strid`: usa **handles numéricos** (`handC`, "
                "`handS`, `handI`, `handCS`, mais `handTYPE`). É por isso que a "
                "coluna de referências fica quase toda vazia aqui, e é o que "
                "liga esses registros aos pools de id da cauda do arquivo "
                "(ver FORMATO.md).\n")
    print(f"\ngravado: {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
