# Descobre o layout do cabecalho no filetype 17: assume que o corpo (registros)
# e igual ao do filetype 16 e procura o offset onde os registros comecam,
# exigindo consumo EXATO do arquivo. Tambem tenta secoes extras por registro.
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kenshimod as km


def try_align(data, start, reccount):
    """tenta parsear reccount registros a partir de start; retorna pos final"""
    r = km.Reader(data)
    r.p = start
    for _ in range(reccount):
        km._ler_registro(r)
    return r.p


def main(path):
    data = open(path, "rb").read()
    print(f"\n=== {path}  ({len(data)} bytes)")
    print("filetype =", struct.unpack_from("<i", data, 0)[0])
    # varre offsets plausiveis de inicio dos registros; o int32 imediatamente
    # anterior deve ser a contagem de registros
    hits = []
    for start in range(12, 600, 4):
        if start + 4 > len(data):
            break
        reccount = struct.unpack_from("<i", data, start - 4)[0]
        if reccount < 0 or reccount > 200000:
            continue
        try:
            end = try_align(data, start, reccount)
        except Exception:
            continue
        if end == len(data):
            hits.append((start, reccount))
            print(f"  ENCAIXE EXATO: registros comecam em {start:#x}, "
                  f"reccount={reccount}, consumiu tudo")
    if not hits:
        print("  nenhum encaixe: o corpo tambem mudou, nao so o cabecalho")
        return
    # mostra os ints do cabecalho e as strings, pro layout ficar explicito
    start = hits[0][0]
    r = km.Reader(data)
    print("  cabecalho campo a campo:")
    while r.p < start:
        off = r.p
        n = struct.unpack_from("<i", data, off)[0]
        if 0 <= n <= 4096 and off + 4 + n <= len(data) and n > 0 and \
                b"\x00" not in data[off + 4:off + 4 + n]:
            s = r.s().decode("utf-8", "replace")
            print(f"    {off:#06x} STR[{n}] {s[:70]!r}")
        else:
            r.i32()
            print(f"    {off:#06x} I32  {n}")


if __name__ == "__main__":
    for pat in sys.argv[1:]:
        for p in glob.glob(pat, recursive=True):
            if struct.unpack_from("<i", open(p, "rb").read(4), 0)[0] == 17:
                main(p)



