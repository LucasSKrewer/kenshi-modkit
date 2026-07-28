"""Leitor/gravador dos formatos binarios do Kenshi, em Python puro.

Suporta filetype 15 (saves: .save, .zone, .platoon), 16 (FCS antigo) e 17 (FCS
novo, nao coberto pela spec da comunidade -- ver FORMATO.md). Strings sao
mantidas como BYTES crus de proposito: e o que garante round-trip
byte-identico, sem risco de o encoding "consertar" algo e mudar o arquivo.

AVISO sobre saves: save corrompido e campanha perdida. Este modulo le save de
boa vontade, mas nunca grave por cima do original -- gere em copia.

Uso tipico:
    import kenshimod as km
    mod = km.ler("caminho/Foo.mod")
    ...mexe em mod["records"]...
    km.gravar("caminho/Bar.mod", mod)
"""
import re
import struct

FILETYPES_SUPORTADOS = (15, 16, 17)


class FloatFiel(float):
    """float que lembra os bytes originais.

    Os saves do Kenshi contem NaN SINALIZANTE (expoente todo-um com o bit alto
    da mantissa em 0). O Python quietiza esse NaN ao desempacotar e reempacotar
    -- liga o bit 0x400000 -- e o arquivo sai diferente por um byte. Guardar os
    bytes crus preserva a fidelidade sem abrir mao de usar o valor como float.
    """
    __slots__ = ("raw",)

    def __new__(cls, valor, raw):
        obj = super().__new__(cls, valor)
        obj.raw = raw
        return obj


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def f32(self):
        raw = self.d[self.p:self.p + 4]
        v = struct.unpack_from("<f", self.d, self.p)[0]
        self.p += 4
        # so embrulha quando reempacotar NAO reproduz os bytes (NaN sinalizante)
        return v if struct.pack("<f", v) == raw else FloatFiel(v, raw)

    def u8(self):
        v = self.d[self.p]
        self.p += 1
        return v

    def s(self):
        n = self.i32()
        if n < 0 or self.p + n > len(self.d):
            raise ValueError(f"string invalida len={n} em {self.p - 4:#x}")
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def ctx(self):
        lo = max(0, self.p - 24)
        return (f"offset {self.p:#x} de {len(self.d):#x} | "
                f"antes={self.d[lo:self.p].hex(' ')} | "
                f"aqui={self.d[self.p:self.p + 32].hex(' ')}")


class Writer:
    def __init__(self):
        self.out = bytearray()

    def i32(self, v):
        self.out += struct.pack("<i", v)

    def f32(self, v):
        self.out += v.raw if isinstance(v, FloatFiel) else struct.pack("<f", v)

    def u8(self, v):
        self.out.append(v)

    def s(self, b):
        self.i32(len(b))
        self.out += b

    def raw(self, b):
        self.out += b


# As 7 secoes de campos tipados, na ordem em que aparecem no arquivo.
SECOES = [
    ("bool", lambda r: r.u8(), lambda w, v: w.u8(v)),
    ("float", lambda r: r.f32(), lambda w, v: w.f32(v)),
    ("long", lambda r: r.i32(), lambda w, v: w.i32(v)),
    ("vec3", lambda r: (r.f32(), r.f32(), r.f32()),
     lambda w, v: [w.f32(x) for x in v]),
    ("vec4", lambda r: (r.f32(), r.f32(), r.f32(), r.f32()),
     lambda w, v: [w.f32(x) for x in v]),
    ("string", lambda r: r.s(), lambda w, v: w.s(v)),
    ("filename", lambda r: r.s(), lambda w, v: w.s(v)),
]

_LIMITE = 1000000  # contagens acima disso = dessincronizou, aborta cedo


def _ler_registro(r):
    rec = {
        "instance_count": r.i32(),
        "typecode": r.i32(),
        "id": r.i32(),
        "name": r.s(),
        "strid": r.s(),
        "mod_data_type": r.i32(),
    }
    for chave, rd, _ in SECOES:
        n = r.i32()
        if not 0 <= n <= _LIMITE:
            raise ValueError(f"contagem absurda na secao {chave}: {n} | {r.ctx()}")
        rec[chave] = [(r.s(), rd(r)) for _ in range(n)]
    cats = []
    n = r.i32()
    if not 0 <= n <= _LIMITE:
        raise ValueError(f"contagem absurda de extra data: {n} | {r.ctx()}")
    for _ in range(n):
        cat = r.s()
        m = r.i32()
        if not 0 <= m <= _LIMITE:
            raise ValueError(f"contagem absurda de itens: {m} | {r.ctx()}")
        cats.append((cat, [(r.s(), r.i32(), r.i32(), r.i32()) for _ in range(m)]))
    rec["extra"] = cats
    insts = []
    n = r.i32()
    if not 0 <= n <= _LIMITE:
        raise ValueError(f"contagem absurda de instances: {n} | {r.ctx()}")
    for _ in range(n):
        strid, target = r.s(), r.s()
        t = (r.f32(), r.f32(), r.f32())
        q = (r.f32(), r.f32(), r.f32(), r.f32())
        m = r.i32()
        if not 0 <= m <= _LIMITE:
            raise ValueError(f"contagem absurda de states: {m} | {r.ctx()}")
        insts.append((strid, target, t, q, [r.s() for _ in range(m)]))
    rec["instances"] = insts
    return rec


def _gravar_registro(w, rec):
    w.i32(rec["instance_count"])
    w.i32(rec["typecode"])
    w.i32(rec["id"])
    w.s(rec["name"])
    w.s(rec["strid"])
    w.i32(rec["mod_data_type"])
    for chave, _, wr in SECOES:
        w.i32(len(rec[chave]))
        for k, v in rec[chave]:
            w.s(k)
            wr(w, v)
    w.i32(len(rec["extra"]))
    for cat, items in rec["extra"]:
        w.s(cat)
        w.i32(len(items))
        for nome, v0, v1, v2 in items:
            w.s(nome)
            w.i32(v0)
            w.i32(v1)
            w.i32(v2)
    w.i32(len(rec["instances"]))
    for strid, target, t, q, states in rec["instances"]:
        w.s(strid)
        w.s(target)
        for x in t:
            w.f32(x)
        for x in q:
            w.f32(x)
        w.i32(len(states))
        for st in states:
            w.s(st)


def desserializar(data):
    r = Reader(data)
    mod = {"filetype": r.i32()}
    if mod["filetype"] not in FILETYPES_SUPORTADOS:
        raise ValueError(f"filetype {mod['filetype']} nao suportado "
                         f"(esperado {FILETYPES_SUPORTADOS})")
    if mod["filetype"] == 15:
        # save (.save/.zone/.platoon): cabecalho curto, sem strings, e uma
        # CAUDA depois dos registros que os filetypes 16/17 nao tem.
        mod["next_id"] = r.i32()
        mod["record_count"] = r.i32()
    elif mod["filetype"] == 17:
        # ft17: campo em offset 4 = deslocamento dos dados (+16). O miolo do
        # cabecalho (lista de mods relacionados) segue nao decodificado e vai
        # cru em mod["middle"]; o record_count e o ultimo int32 antes dos dados.
        inicio_dados = r.i32() + 16
        mod["mod_version"] = r.i32()
        mod["author"], mod["description"] = r.s(), r.s()
        mod["dependencies"], mod["references"] = r.s(), r.s()
        if inicio_dados - 4 < r.p or inicio_dados > len(data):
            raise ValueError(f"data_offset incoerente: {inicio_dados:#x}")
        mod["middle"] = data[r.p:inicio_dados - 4]
        mod["record_count"] = struct.unpack_from("<i", data, inicio_dados - 4)[0]
        r.p = inicio_dados
    else:
        mod["mod_version"] = r.i32()
        mod["author"], mod["description"] = r.s(), r.s()
        mod["dependencies"], mod["references"] = r.s(), r.s()
        mod["unknown"] = r.i32()
        mod["record_count"] = r.i32()
    recs = []
    for i in range(mod["record_count"]):
        try:
            recs.append(_ler_registro(r))
        except Exception as e:
            raise ValueError(f"registro #{i} de {mod['record_count']}: {e}") from e
    mod["records"] = recs
    if mod["filetype"] == 15:
        # cauda: sequencia de blocos [L contagem][L valor]*, listas de ids
        # (valores sequenciais 1,2,3...). Consome o arquivo exatamente.
        blocos = []
        while r.p + 4 <= len(data):
            cont = r.i32()
            if cont < 0 or r.p + cont * 4 > len(data):
                raise ValueError(f"bloco de cauda invalido: contagem={cont} "
                                 f"em {r.p - 4:#x}")
            blocos.append(list(struct.unpack_from(f"<{cont}i", data, r.p))
                          if cont else [])
            r.p += cont * 4
        mod["tail_blocks"] = blocos
    mod["tail"] = data[r.p:]  # vazio nos tres filetypes suportados
    return mod


def serializar(mod):
    w = Writer()
    w.i32(mod["filetype"])
    if mod["filetype"] == 15:
        w.i32(mod["next_id"])
        w.i32(len(mod["records"]))
    elif mod["filetype"] == 17:
        w.i32(0)  # placeholder do data_offset
        w.i32(mod["mod_version"])
        for campo in ("author", "description", "dependencies", "references"):
            w.s(mod[campo])
        w.raw(mod["middle"])
        w.i32(len(mod["records"]))
        # recalcula: mexer nas strings do cabecalho muda o deslocamento
        struct.pack_into("<i", w.out, 4, len(w.out) - 16)
    else:
        w.i32(mod["mod_version"])
        for campo in ("author", "description", "dependencies", "references"):
            w.s(mod[campo])
        w.i32(mod["unknown"])
        w.i32(len(mod["records"]))
    for rec in mod["records"]:
        _gravar_registro(w, rec)
    if mod["filetype"] == 15:
        for bloco in mod["tail_blocks"]:
            w.i32(len(bloco))
            for v in bloco:
                w.i32(v)
    w.raw(mod["tail"])
    return bytes(w.out)


def ler(caminho):
    with open(caminho, "rb") as f:
        return desserializar(f.read())


def gravar(caminho, mod):
    data = serializar(mod)
    with open(caminho, "wb") as f:
        f.write(data)
    return len(data)


# ---------------------------------------------------------------- utilidades

def b(x):
    """aceita str ou bytes e devolve bytes utf-8"""
    return x if isinstance(x, bytes) else x.encode("utf-8")


def t(x):
    """bytes -> str para exibicao (nunca usar pra gravar de volta)"""
    return x.decode("utf-8", "replace")


# id de registro tem a forma "<numero>-<arquivo de origem>"
RE_ID = re.compile(rb"^(\d+)-(.+\.(?:mod|base))$")


def substituir_em_ids(mod, de, para):
    """troca um trecho em TODO lugar que carrega id de registro: o strid do
    proprio registro, as referencias (extra data), campos string/filename e as
    instances. E assim que se deriva um mod de outro sem deixar id pendurado."""
    de, para = b(de), b(para)
    n = 0

    def tr(v):
        nonlocal n
        if isinstance(v, bytes) and de in v:
            n += 1
            return v.replace(de, para)
        return v

    for rec in mod["records"]:
        rec["strid"] = tr(rec["strid"])
        for chave in ("string", "filename"):
            rec[chave] = [(k, tr(v)) for k, v in rec[chave]]
        rec["extra"] = [(cat, [(tr(nome), v0, v1, v2) for nome, v0, v1, v2 in items])
                        for cat, items in rec["extra"]]
        rec["instances"] = [(tr(strid), tr(target), pos, rot, states)
                            for strid, target, pos, rot, states in rec["instances"]]
    return n


def clonar_registro(rec, novo_strid, novo_nome=None):
    """copia profunda de um registro com novo id. Nao precisa saber o typecode:
    herda o do original -- e o jeito de criar registro valido sem o mapa de
    typecodes."""
    novo = dict(rec)
    for chave, _, _ in SECOES:
        novo[chave] = list(rec[chave])
    novo["extra"] = [(cat, list(items)) for cat, items in rec["extra"]]
    novo["instances"] = list(rec["instances"])
    novo["strid"] = b(novo_strid)
    if novo_nome is not None:
        novo["name"] = b(novo_nome)
    return novo


def proximo_id_livre(mod, sufixo):
    """maior numero usado nos strids do proprio mod, + 1"""
    sufixo = b(sufixo)
    usados = [0]
    for rec in mod["records"]:
        m = RE_ID.match(rec["strid"])
        if m and m.group(2) == sufixo:
            usados.append(int(m.group(1)))
    return max(usados) + 1


def referencias(mod):
    """todo id referenciado pelos registros, com de onde veio"""
    saida = []
    for rec in mod["records"]:
        for cat, items in rec["extra"]:
            for nome, *_ in items:
                if RE_ID.match(nome):
                    saida.append((rec, t(cat), nome))
        for chave in ("string", "filename"):
            for k, v in rec[chave]:
                if isinstance(v, bytes) and RE_ID.match(v):
                    saida.append((rec, t(k), v))
    return saida


def campo(rec, secao, nome, default=None):
    for k, v in rec[secao]:
        if k == b(nome):
            return v
    return default


def set_campo(rec, secao, nome, valor):
    """altera um campo existente; devolve False se o campo nao existe (o FCS
    so grava no .mod os campos que o mod realmente sobrescreve)"""
    alvo = b(nome)
    for i, (k, _) in enumerate(rec[secao]):
        if k == alvo:
            rec[secao][i] = (k, b(valor) if secao in ("string", "filename") else valor)
            return True
    return False
