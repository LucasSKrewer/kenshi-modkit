"""Levanta o mapa de typecodes correlacionando os campos dos registros reais
com as seções do `fcs.def` que o jogo instala.

A ideia: o `fcs.def` lista, para cada tipo de registro, os campos que ele tem.
Os registros do jogo carregam os nomes dos campos dentro do arquivo. Então dá
para casar um typecode numérico com um tipo do fcs.def por CONTENÇÃO: se todo
campo visto nos registros do typecode 64 existe na seção [GAME_START] do
fcs.def, e nenhuma outra seção contém todos, o typecode 64 é GAME_START.

    python typecodes.py                 (usa data/, escreve TYPECODES.md)
    python typecodes.py --ambiguos      (só os casos que não fecharam)
"""
import os
import re
import sys
from collections import defaultdict

import caminhos
import kenshimod as km

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TYPECODES.md")

RE_SECAO = re.compile(r"^\[([A-Z0-9_,]+)\]\s*$")

# O jogo usa famílias numeradas de campo (text1..text15, "line 3"...) enquanto o
# fcs.def lista o campo uma vez só; comparar sem o sufixo numérico evita contar
# isso como divergência. `REMOVED` é marcador de registro removido por um mod,
# não pertence a tipo nenhum.
RE_SUFIXO_NUM = re.compile(r"\s*\d+$")
IGNORAR = {"REMOVED"}


def normalizar(nome):
    return RE_SUFIXO_NUM.sub("", nome)


def ler_fcs_def(caminho=None):
    """seção do fcs.def -> conjunto de nomes de campo.

    Linha de campo é "nome: <default> ..."; linha que termina em ':' sem nada
    depois é só cabeçalho de grupo (ex: "movement:", "Audio:") e não é campo.
    """
    caminho = caminho or caminhos.fcs_def()
    tipos = {}
    atuais = []
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            m = RE_SECAO.match(linha)
            if m:
                atuais = m.group(1).split(",")
                for t in atuais:
                    tipos.setdefault(t, set())
                continue
            if not atuais or ":" not in linha:
                continue
            nome, _, resto = linha.partition(":")
            nome = nome.strip()
            if not nome or not resto.strip():
                continue  # cabeçalho de grupo
            for t in atuais:
                tipos[t].add(normalizar(nome))
    return tipos


def campos_por_typecode(arquivos):
    """typecode -> (conjunto de campos vistos, quantos registros, exemplo)"""
    campos = defaultdict(set)
    quantos = defaultdict(int)
    exemplo = {}
    for c in arquivos:
        if not os.path.exists(c):
            print(f"  aviso: sem {c}")
            continue
        mod = km.ler(c)
        for rec in mod["records"]:
            tc = rec["typecode"]
            quantos[tc] += 1
            exemplo.setdefault(tc, km.t(rec["name"]))
            for secao, _, _ in km.SECOES:
                for k, _v in rec[secao]:
                    campos[tc].add(normalizar(km.t(k)))
            for cat, _items in rec["extra"]:
                # referências também são campos no fcs.def
                campos[tc].add(normalizar(km.t(cat)))
            campos[tc] -= IGNORAR
    return campos, quantos, exemplo


def casar(vistos, tipos):
    """ranqueia tipos por contenção dos campos vistos; devolve lista ordenada"""
    if not vistos:
        return []
    placar = []
    for nome, campos in tipos.items():
        if not campos:
            continue
        cobertos = len(vistos & campos)
        recall = cobertos / len(vistos)          # quanto do visto o tipo explica
        precisao = cobertos / len(campos)        # quanto do tipo foi visto
        placar.append((recall, precisao, nome, cobertos))
    placar.sort(key=lambda x: (-x[0], -x[1]))
    return placar


def main(argv):
    tipos = ler_fcs_def()
    print(f"fcs.def: {len(tipos)} tipos de registro, "
          f"{sum(len(v) for v in tipos.values())} campos no total")
    campos, quantos, exemplo = campos_por_typecode(caminhos.arquivos_base())
    print(f"corpus: {sum(quantos.values())} registros em {len(campos)} typecodes\n")

    linhas, ambiguos, resolvidos = [], [], []
    for tc in sorted(campos):
        placar = casar(campos[tc], tipos)
        if not placar:
            continue
        recall, precisao, nome, _ = placar[0]
        empatados = [p[2] for p in placar if p[0] == recall and p[1] == precisao]
        confianca = "exato" if recall == 1.0 and len(empatados) == 1 else (
            "empate" if len(empatados) > 1 else "parcial")
        alt = ", ".join(empatados[1:4]) if len(empatados) > 1 else ""
        linhas.append([tc, nome, confianca, recall, precisao, quantos[tc],
                       len(campos[tc]), exemplo[tc], alt])

    # Se dois typecodes casam com o mesmo tipo, um deles está errado: o fcs.def
    # tem 74 tipos para 78 typecodes vistos, então há tipo real que não está lá
    # e o casamento cai no vizinho mais parecido. Marca o de recall menor.
    melhor_por_tipo = {}
    for linha in linhas:
        nome, recall = linha[1], linha[3]
        if nome not in melhor_por_tipo or recall > melhor_por_tipo[nome][3]:
            melhor_por_tipo[nome] = linha
    for linha in linhas:
        if melhor_por_tipo[linha[1]] is not linha:
            linha[2] = "duplicado"
    for tc, _n, conf, *_ in linhas:
        (resolvidos if conf == "exato" else ambiguos).append(tc)

    if "--detalhe" in argv:
        tc = int(argv[argv.index("--detalhe") + 1])
        placar = casar(campos[tc], tipos)
        print(f"typecode {tc}: {quantos[tc]} registros, "
              f"{len(campos[tc])} campos distintos vistos")
        for recall, precisao, nome, cobertos in placar[:5]:
            print(f"  {nome:<30} recall={recall:.0%} precisao={precisao:.0%} "
                  f"({cobertos}/{len(campos[tc])} campos)")
        melhor = placar[0][2]
        sobrando = sorted(campos[tc] - tipos[melhor])
        print(f"\ncampos vistos que [{melhor}] NAO tem ({len(sobrando)}):")
        for c in sobrando:
            print(f"  {c}")
        return 0

    if "--ambiguos" in argv:
        linhas = [l for l in linhas if l[0] in ambiguos]

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write("# Mapa de typecodes\n\n")
        f.write("Gerado por `python typecodes.py`, correlacionando os campos dos "
                "registros de `data/` com as seções do `fcs.def` do jogo.\n\n")
        f.write("`recall` = fração dos campos vistos que o tipo do fcs.def "
                "explica. `exato` = recall 100% e sem empate.\n\n")
        f.write("| typecode | tipo | confiança | recall | registros | exemplo |\n")
        f.write("|---|---|---|---|---|---|\n")
        for tc, nome, conf, rec, _pre, n, _nc, ex, alt in linhas:
            nome_txt = nome if not alt else f"{nome} *(ou {alt})*"
            f.write(f"| {tc} | `{nome_txt}` | {conf} | {rec:.0%} | {n} | "
                    f"{ex[:40]} |\n")
    print(f"gravado: {SAIDA}\n")

    print(f"{'tc':>5} {'tipo (fcs.def)':<28} {'conf':<8} {'recall':>6} "
          f"{'regs':>7}  exemplo / alternativas")
    for tc, nome, conf, rec, _pre, n, _nc, ex, alt in linhas:
        extra = f"   [empata com: {alt}]" if alt else ""
        print(f"{tc:>5} {nome:<28} {conf:<8} {rec:>6.0%} {n:>7}  {ex[:34]}{extra}")
    print(f"\nresolvidos com certeza: {len(resolvidos)} de {len(campos)} typecodes "
          f"vistos ({len(ambiguos)} ambíguos)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
