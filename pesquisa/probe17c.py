# Confirma a hipotese do cabecalho ft17:
#   [L filetype=17][L data_offset (+16 = inicio dos registros)][L mod_version]
#   [S author][S desc][S deps][S refs] ... ??? ... [L reccount]
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kenshimod as km


def main(path):
    data = open(path, "rb").read()
    ft, off4, off8 = struct.unpack_from("<iii", data, 0)
    r = km.Reader(data)
    r.p = 12
    author, desc, deps, refs = r.s(), r.s(), r.s(), r.s()
    start = off4 + 16
    gap = data[r.p:start]
    print(f"\n=== {path.rsplit(chr(92), 1)[-1]}  ({len(data)} bytes)")
    print(f"  filetype={ft}  campo@4={off4} (+16 = {start:#x})  campo@8={off8}")
    print(f"  author={author[:40]!r} deps={deps[:60]!r} refs={refs[:60]!r}")
    print(f"  fim das strings: {r.p:#x}   gap ate os registros: {len(gap)} bytes")
    print(f"  gap hex: {gap.hex(' ')}")
    # valida: cadeia de registros a partir de start consome tudo?
    rr = km.Reader(data)
    rr.p = start
    n = 0
    try:
        while rr.p < len(data):
            km._ler_registro(rr)
            n += 1
    except Exception as e:
        print(f"  !! parse quebrou no registro {n}: {e}")
        return
    fits = "EXATO" if rr.p == len(data) else f"sobrou {len(data) - rr.p}"
    print(f"  registros lidos: {n}  consumo: {fits}")
    # o reccount deve estar em algum lugar do gap
    for i in range(0, len(gap) - 3):
        if struct.unpack_from("<i", gap, i)[0] == n:
            print(f"  -> reccount={n} aparece no gap em +{i}"
                  f" (offset absoluto {r.p + i:#x}, {start - (r.p + i)} bytes antes dos dados)")


if __name__ == "__main__":
    for pat in sys.argv[1:]:
        for p in sorted(glob.glob(pat, recursive=True)):
            if struct.unpack_from("<i", open(p, "rb").read(4), 0)[0] == 17:
                main(p)



