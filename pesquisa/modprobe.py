# Explorador do formato .mod do Kenshi.
# Nao assume estrutura: le int32 e, quando o int32 parece tamanho de string
# imprimivel, consome como string. Objetivo: revelar o layout.
import struct
import sys


class Cursor:
    def __init__(self, data):
        self.d = data
        self.p = 0

    def left(self):
        return len(self.d) - self.p

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def peek_i32(self, off=0):
        if self.p + off + 4 > len(self.d):
            return None
        return struct.unpack_from("<i", self.d, self.p + off)[0]

    def raw(self, n):
        b = self.d[self.p:self.p + n]
        self.p += n
        return b


def looks_like_string(c):
    """int32 na posicao atual e um tamanho plausivel de string?"""
    n = c.peek_i32()
    if n is None or n < 0 or n > 4096 or c.p + 4 + n > len(c.d):
        return False
    if n == 0:
        return True
    body = c.d[c.p + 4:c.p + 4 + n]
    # heuristica: maioria imprimivel/utf-8, sem NUL
    if b"\x00" in body:
        return False
    printable = sum(1 for ch in body if 0x20 <= ch < 0x7F or ch >= 0x80)
    return printable / len(body) > 0.9


def main(path, limit=400):
    data = open(path, "rb").read()
    c = Cursor(data)
    print(f"# {path}  ({len(data)} bytes)")
    steps = 0
    while c.left() >= 4 and steps < limit:
        off = c.p
        if looks_like_string(c):
            n = c.i32()
            s = c.raw(n).decode("utf-8", "replace")
            print(f"{off:#08x} STR[{n}] {s!r}")
        else:
            v = c.i32()
            fbits = struct.unpack("<f", struct.pack("<i", v))[0]
            extra = f"  ~float={fbits:.4g}" if 1e-6 < abs(fbits) < 1e9 else ""
            print(f"{off:#08x} I32  {v}{extra}")
        steps += 1
    if c.left():
        print(f"# sobraram {c.left()} bytes a partir de {c.p:#08x}")
        print("# tail:", data[c.p:c.p + 64].hex(" "))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 400)


