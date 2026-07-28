"""Compara dois saves e mostra o que mudou -- registro a registro, campo a campo.

O jogo não conta isso: entre um autosave e o seguinte, o que de fato mudou no
mundo? Que esquadrão apareceu, que facção mudou de relação, que estado de cidade
virou. Como o formato é o mesmo dos mods, a comparação é a mesma ideia do
`conflitos.py`, só que entre dois momentos do mesmo mundo.

Só leitura -- nunca grava em save.

    python savediff.py <saveA> <saveB>            (pasta ou arquivo .save)
    python savediff.py autosave0 autosave1        (nomes dentro de save/)
    python savediff.py A B --campos 40            (mais detalhe de campo)
"""
import os
import sys
from collections import Counter

import caminhos as loc
import conflitos
import kenshimod as km


def resolver(alvo):
    """aceita caminho de arquivo, caminho de pasta, ou nome do save"""
    if os.path.isfile(alvo):
        return alvo
    pasta = alvo if os.path.isdir(alvo) else os.path.join(
        loc.kenshi_dir(), "save", alvo)
    if not os.path.isdir(pasta):
        raise SystemExit(f"nao achei save: {alvo}")
    saves = [f for f in os.listdir(pasta) if f.endswith(".save")]
    if not saves:
        raise SystemExit(f"pasta sem .save: {pasta}")
    # o quick.save e o principal; se nao houver, pega o maior
    escolha = "quick.save" if "quick.save" in saves else max(
        saves, key=lambda f: os.path.getsize(os.path.join(pasta, f)))
    return os.path.join(pasta, escolha)


def indexar(caminho):
    mod = km.ler(caminho)
    return mod, {rec["strid"]: rec for rec in mod["records"]}


def main(argv):
    alvos = [a for a in argv if not a.startswith("--")]
    if len(alvos) < 2:
        print(__doc__)
        return 1
    limite = int(argv[argv.index("--campos") + 1]) if "--campos" in argv else 12

    ca, cb = resolver(alvos[0]), resolver(alvos[1])
    print(f"A: {ca}")
    print(f"B: {cb}\n")
    moda, ia = indexar(ca)
    modb, ib = indexar(cb)
    print(f"A: {len(moda['records'])} registros, nextID {moda['next_id']}")
    print(f"B: {len(modb['records'])} registros, nextID {modb['next_id']}")

    so_a = set(ia) - set(ib)
    so_b = set(ib) - set(ia)
    comuns = set(ia) & set(ib)

    def por_tipo(strids, idx):
        return Counter(idx[s]["typecode"] for s in strids)

    print(f"\nSO EM A (sumiram em B): {len(so_a)}   {dict(por_tipo(so_a, ia))}")
    for s in sorted(so_a)[:8]:
        print(f"    [tc {ia[s]['typecode']}] {km.t(s)[:60]}")
    print(f"\nSO EM B (novos): {len(so_b)}   {dict(por_tipo(so_b, ib))}")
    for s in sorted(so_b)[:8]:
        print(f"    [tc {ib[s]['typecode']}] {km.t(s)[:60]}")

    mudados = []
    for s in comuns:
        va, vb = conflitos.valores(ia[s]), conflitos.valores(ib[s])
        if va != vb:
            difs = [(k, va.get(k), vb.get(k))
                    for k in set(va) | set(vb) if va.get(k) != vb.get(k)]
            mudados.append((s, ia[s]["typecode"], difs))
    print(f"\nMUDARAM: {len(mudados)} de {len(comuns)} registros em comum")
    campos_quentes = Counter()
    for _s, _tc, difs in mudados:
        for k, _a, _b in difs:
            campos_quentes[k] += 1
    if campos_quentes:
        print("  campos que mais mudaram:")
        for campo, n in campos_quentes.most_common(10):
            print(f"    {n:>6}x  {campo}")
    print(f"\n  detalhe dos primeiros {min(limite, len(mudados))}:")
    for s, tc, difs in mudados[:limite]:
        print(f"    [tc {tc}] {km.t(s)[:56]}")
        for k, a, b in difs[:4]:
            print(f"        {k:<26} {str(a)[:28]}  ->  {str(b)[:28]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
