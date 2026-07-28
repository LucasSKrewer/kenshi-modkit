"""Mostra o conteudo de um .mod em texto legivel (ou JSON).

Os nomes dos campos vem dentro do proprio arquivo, entao nao e preciso schema
nenhum pra ler -- o fcs.def serve pra validar/defaults, nao pra decodificar.

    python dump.py "...\\KenshiCoop.mod"
    python dump.py "...\\Genesis.mod" --tipos          (so o resumo por typecode)
    python dump.py "...\\Foo.mod" --json > foo.json    (pra diff/versionamento)
    python dump.py "...\\quick.save" --tipo 34 --n 2   (so registros de um tipo)
"""
import base64
import json
import sys
from collections import Counter

import kenshimod as km

SECOES_MOSTRAR = ("bool", "float", "long", "vec3", "vec4", "string", "filename")


def para_json(mod):
    def conv(v):
        if isinstance(v, bytes):
            try:
                return v.decode("utf-8")
            except UnicodeDecodeError:
                return {"__b64": base64.b64encode(v).decode()}
        if isinstance(v, tuple):
            return list(v)
        return v

    # tail_blocks fica de fora: em save grande sao milhoes de ids, e o JSON
    # aqui serve pra diff de conteudo, nao pra reconstruir o arquivo.
    saida = {k: conv(v) for k, v in mod.items()
             if k not in ("records", "tail_blocks")}
    saida["records"] = [
        {
            "typecode": rec["typecode"],
            "id": rec["id"],
            "name": conv(rec["name"]),
            "strid": conv(rec["strid"]),
            "mod_data_type": rec["mod_data_type"],
            "instance_count": rec["instance_count"],
            **{sec: {conv(k): conv(v) for k, v in rec[sec]} for sec in SECOES_MOSTRAR},
            "extra": {conv(cat): [[conv(n), a, b_, c] for n, a, b_, c in items]
                      for cat, items in rec["extra"]},
            "instances": [[conv(s), conv(tg), list(p), list(r), [conv(x) for x in st]]
                          for s, tg, p, r, st in rec["instances"]],
        }
        for rec in mod["records"]
    ]
    return saida


def texto(mod, limite_refs=6):
    if mod["filetype"] == 15:
        blocos = mod.get("tail_blocks", [])
        print(f"filetype 15 (save)  nextID {mod['next_id']}  "
              f"{len(mod['records'])} registros")
        print(f"cauda: {len(blocos)} bloco(s), "
              f"{sum(len(b) for b in blocos):,} ids")
    else:
        print(f"filetype {mod['filetype']}  versao {mod['mod_version']}  "
              f"{len(mod['records'])} registros")
        print(f"autor: {km.t(mod['author'])!r}")
        print(f"deps : {km.t(mod['dependencies'])}")
        print(f"refs : {km.t(mod['references'])}")
        if mod["description"]:
            print(f"desc : {km.t(mod['description'])[:300]}")
    for rec in mod["records"]:
        print(f"\n[typecode {rec['typecode']}] {km.t(rec['name'])}"
              f"  (id {km.t(rec['strid'])}, modtype {rec['mod_data_type']})")
        for sec in SECOES_MOSTRAR:
            for k, v in rec[sec]:
                if isinstance(v, bytes):
                    if not v:
                        continue          # campo vazio = herdado da base
                    v = km.t(v)
                print(f"    {sec:<8} {km.t(k):<26} = {v!r}")
        for cat, items in rec["extra"]:
            mostra = ", ".join(f"{km.t(n)}({a},{b_},{c})"
                               for n, a, b_, c in items[:limite_refs])
            resto = f"  +{len(items) - limite_refs}" if len(items) > limite_refs else ""
            print(f"    ref      {km.t(cat):<26} -> {mostra}{resto}")
        for strid, target, pos, _rot, states in rec["instances"]:
            st = f" estados={[km.t(x) for x in states]}" if states else ""
            print(f"    inst     {km.t(strid):<26} -> {km.t(target)} "
                  f"em ({pos[0]:.0f},{pos[1]:.0f},{pos[2]:.0f}){st}")


def tipos(mod):
    c = Counter(rec["typecode"] for rec in mod["records"])
    exemplo = {}
    for rec in mod["records"]:
        exemplo.setdefault(rec["typecode"], km.t(rec["name"]))
    print(f"{len(mod['records'])} registros em {len(c)} typecodes:")
    for tc, n in c.most_common():
        print(f"  typecode {tc:<5} {n:>6} registros   ex: {exemplo[tc][:50]}")


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    mod = km.ler(argv[0])
    if "--tipo" in argv:
        alvo = int(argv[argv.index("--tipo") + 1])
        limite = int(argv[argv.index("--n") + 1]) if "--n" in argv else 3
        mod["records"] = [r for r in mod["records"]
                          if r["typecode"] == alvo][:limite]
    if "--json" in argv:
        json.dump(para_json(mod), sys.stdout, indent=1, ensure_ascii=False)
    elif "--tipos" in argv:
        tipos(mod)
    else:
        texto(mod)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
