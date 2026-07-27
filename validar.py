"""Checagens de sanidade de um .mod resolvendo contra a ordem de load.

Por que precisa da ordem de load: um mod que SOBRESCREVE um registro mantem o
sufixo de origem dele ("997-gamedata.base"), nao o nome do proprio mod. Entao
so da pra dizer se uma referencia esta pendurada olhando tambem os arquivos de
onde ela vem -- por padrao os 4 de data/ (gamedata.base, rebirth.mod,
Newwworld.mod, Dialogue.mod).

    python validar.py "Foo.mod"
    python validar.py "Foo.mod" --contra "Genesis.mod"
    python validar.py "Foo.mod" --sem-base     (nao carrega data/, mais rapido)

O caminho da instalacao e detectado (ver caminhos.py); nao precisa editar nada.

Checagens: strid duplicado, referencia que nao resolve em ninguem, e o resumo
de quantas referencias caem em cada arquivo (util pra descobrir dependencia
que faltou declarar).
"""
import os
import sys
from collections import Counter

import caminhos as loc
import kenshimod as km


def indexar(arquivos):
    """strid -> arquivo que o define (o ultimo a definir ganha, como no jogo)"""
    idx = {}
    for c in arquivos:
        if not os.path.exists(c):
            print(f"  aviso: nao achei {c}, seguindo sem ele")
            continue
        mod = km.ler(c)
        nome = os.path.basename(c)
        for rec in mod["records"]:
            idx[rec["strid"]] = nome
    return idx


def sufixo(strid):
    m = km.RE_ID.match(strid)
    return km.t(m.group(2)) if m else "?"


def validar(caminho, idx_externo):
    mod = km.ler(caminho)
    proprios = {rec["strid"] for rec in mod["records"]}
    deps = {d.strip() for d in km.t(mod["dependencies"]).split(",") if d.strip()}
    print(f"\n=== {os.path.basename(caminho)}: {len(mod['records'])} registros, "
          f"ft{mod['filetype']}")
    print(f"    deps declaradas: {sorted(deps) or '(nenhuma)'}")
    problemas = []

    dup = [s for s, n in Counter(rec["strid"] for rec in mod["records"]).items() if n > 1]
    if dup:
        problemas.append(f"{len(dup)} strid duplicado: {[km.t(s) for s in dup[:5]]}")

    penduradas, por_arquivo, sem_dep = [], Counter(), Counter()
    for rec, campo, alvo in km.referencias(mod):
        if alvo in proprios:
            por_arquivo["(este mod)"] += 1
            continue
        onde = idx_externo.get(alvo)
        if onde:
            por_arquivo[onde] += 1
            suf = sufixo(alvo)
            if onde not in deps and suf not in deps:
                sem_dep[onde] += 1
        else:
            penduradas.append((km.t(rec["strid"]), campo, km.t(alvo)))
    if penduradas:
        problemas.append(f"{len(penduradas)} referencia(s) que nao resolvem em "
                         f"ninguem: {penduradas[:5]}")

    print("    referencias resolvidas por arquivo:")
    for arq, n in por_arquivo.most_common(10):
        print(f"      {n:>7}  {arq}")
    if sem_dep:
        print(f"    resolvem em arquivo NAO declarado como dependencia: {dict(sem_dep)}")
    for p in problemas:
        print(f"    PROBLEMA: {p}")
    if not problemas:
        print("    sem problemas")
    return problemas


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    alvos = [a for a in argv if not a.startswith("--")]
    contra = []
    if "--sem-base" not in argv:
        contra += loc.arquivos_base()
    if "--contra" in argv:
        i = argv.index("--contra")
        contra += [a for a in argv[i + 1:] if not a.startswith("--")]
        alvos = [a for a in alvos if a not in contra]
    print(f"indexando {len(contra)} arquivo(s) da ordem de load...")
    idx = indexar(contra)
    print(f"{len(idx)} registros indexados")
    falhou = sum(bool(validar(a, idx)) for a in alvos)
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
