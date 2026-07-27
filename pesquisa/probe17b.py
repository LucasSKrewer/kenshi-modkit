# Procura o layout de registro do filetype 17 testando variantes:
#  - quantidade de secoes tipadas (7 no ft16, talvez 8+)
#  - ints extras no cabecalho do registro
# Criterio: uma cadeia de registros a partir de algum offset consome
# o arquivo EXATAMENTE.
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kenshimod as km

# candidatos de secao extra para inserir/apendar
CAND = {
    "bool": lambda r: r.u8(),
    "float": lambda r: r.f32(),
    "long": lambda r: r.i32(),
    "vec2": lambda r: (r.f32(), r.f32()),
    "vec3": lambda r: (r.f32(), r.f32(), r.f32()),
    "vec4": lambda r: (r.f32(), r.f32(), r.f32(), r.f32()),
    "string": lambda r: r.s(),
}


def make_reader(sections, pre_ints, post_ints):
    def read_rec(r):
        for _ in range(pre_ints):
            r.i32()
        r.i32(); r.i32(); r.i32()          # instcount, typecode, id
        r.s(); r.s()                        # name, strid
        r.i32()                             # moddatatype
        for _ in range(post_ints):
            r.i32()
        for rd in sections:
            n = r.i32()
            if n < 0 or n > 100000:
                raise ValueError("secao absurda")
            for _ in range(n):
                r.s()
                rd(r)
        n = r.i32()                         # extra data
        if n < 0 or n > 100000:
            raise ValueError("extra absurdo")
        for _ in range(n):
            r.s()
            m = r.i32()
            if m < 0 or m > 1000000:
                raise ValueError("itens absurdo")
            for _ in range(m):
                r.s(); r.i32(); r.i32(); r.i32()
        n = r.i32()                         # instances
        if n < 0 or n > 1000000:
            raise ValueError("instances absurdo")
        for _ in range(n):
            r.s(); r.s()
            for _ in range(7):
                r.f32()
            m = r.i32()
            if m < 0 or m > 100000:
                raise ValueError("states absurdo")
            for _ in range(m):
                r.s()
        return True
    return read_rec


BASE = [CAND[k] for k in ("bool", "float", "long", "vec3", "vec4", "string", "string")]


def variants():
    yield "ft16 puro (7 secoes)", BASE, 0, 0
    # uma secao extra em cada posicao possivel, para cada tipo candidato
    for name, rd in CAND.items():
        for pos in range(len(BASE) + 1):
            secs = BASE[:pos] + [rd] + BASE[pos:]
            yield f"secao extra '{name}' na posicao {pos}", secs, 0, 0
    for n in (1, 2):
        yield f"{n} int extra apos moddatatype", BASE, 0, n
        yield f"{n} int extra antes do registro", BASE, n, 0


def chain_fits(data, start, read_rec):
    r = km.Reader(data)
    r.p = start
    count = 0
    while r.p < len(data):
        read_rec(r)
        count += 1
        if count > 300000:
            return None
    return count if r.p == len(data) else None


def main(paths):
    for label, secs, pre, post in variants():
        results = []
        for path in paths:
            data = open(path, "rb").read()
            found = None
            for start in range(12, min(len(data), 800), 1):  # byte a byte
                try:
                    c = chain_fits(data, start, make_reader(secs, pre, post))
                except Exception:
                    continue
                if c:
                    found = (start, c)
                    break
            results.append(found)
        if all(results):
            print(f"CANDIDATO: {label}")
            for path, res in zip(paths, results):
                print(f"    {res[1]:>6} registros a partir de {res[0]:#x}"
                      f"  {path.rsplit(chr(92), 1)[-1]}")


if __name__ == "__main__":
    paths = []
    for pat in sys.argv[1:]:
        for p in glob.glob(pat, recursive=True):
            if struct.unpack_from("<i", open(p, "rb").read(4), 0)[0] == 17:
                paths.append(p)
    print("arquivos ft17:", len(paths))
    main(paths)



