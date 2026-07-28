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
from collections import Counter, defaultdict

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


RE_CAMPO_REF = re.compile(r"^([^:]+):\s+([A-Z][A-Z0-9_]{2,})(?:\s|\(|$)")


def campos_de_referencia(caminho=None, tipos=None):
    """campo -> tipo apontado, segundo o fcs.def.

    Linhas como `clothing:  ARMOUR (1, 100) "..."` dizem que o campo `clothing`
    referencia registros do tipo ARMOUR. Isso dá um canal INDEPENDENTE do
    casamento por conjunto de campos: se nos dados as refs de `clothing`
    apontam para registros de typecode 3, então typecode 3 = ARMOUR.

    Campos definidos em mais de um tipo com alvos diferentes são descartados
    (ambíguos por construção).
    """
    caminho = caminho or caminhos.fcs_def()
    alvos = defaultdict(set)
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        for linha in f:
            if RE_SECAO.match(linha):
                continue
            m = RE_CAMPO_REF.match(linha.rstrip())
            if not m:
                continue
            campo, alvo = m.group(1).strip(), m.group(2)
            if tipos is None or alvo in tipos:
                alvos[normalizar(campo)].add(alvo)
    return {c: next(iter(s)) for c, s in alvos.items() if len(s) == 1}


def por_referencia(arquivos, alvos_por_campo):
    """typecode -> (tipo deduzido, quantas refs sustentam, pureza)

    Percorre as referências reais: para cada categoria de ref, olha o typecode
    dos registros apontados. Se as refs de um campo caem quase todas no mesmo
    typecode, e o fcs.def diz que aquele campo aponta para o tipo Y, então esse
    typecode é Y.
    """
    tipo_de = {}          # strid -> typecode
    refs = defaultdict(Counter)   # campo -> Counter de typecodes apontados
    total_refs = Counter()        # typecode -> total de refs recebidas
    registros = []
    for c in arquivos:
        if not os.path.exists(c):
            continue
        mod = km.ler(c)
        registros.append(mod)
        for rec in mod["records"]:
            tipo_de[rec["strid"]] = rec["typecode"]
    for mod in registros:
        for rec in mod["records"]:
            for cat, items in rec["extra"]:
                campo = normalizar(km.t(cat))
                for alvo, *_ in items:
                    if alvo not in tipo_de:
                        continue
                    total_refs[tipo_de[alvo]] += 1
                    if campo in alvos_por_campo:
                        refs[campo][tipo_de[alvo]] += 1

    # consolida: cada campo vota no par (typecode dominante, tipo do fcs.def)
    votos = defaultdict(Counter)
    for campo, contagem in refs.items():
        total = sum(contagem.values())
        if not total:
            continue
        tc, n = contagem.most_common(1)[0]
        if n / total >= 0.9:      # refs de um campo devem ser homogêneas
            votos[tc][alvos_por_campo[campo]] += n
    # Trava contra colisão de nome de campo: o mesmo nome pode existir em tipos
    # diferentes, e um campo cujo tipo real está AUSENTE do fcs.def empresta a
    # declaração do homônimo. Só concluímos se as refs declaradas forem maioria
    # de TODAS as refs que aquele typecode recebe.
    saida = {}
    for tc, contagem in votos.items():
        tipo, n = contagem.most_common(1)[0]
        recebidas = total_refs.get(tc, n)
        if n / recebidas < 0.5:
            continue
        saida[tc] = (tipo, n, n / recebidas)
    return saida


# Exige o número no fim: nome AUTO-GERADO é "<TIPO><numero>" (DIALOG_ACTION4205).
# Sem essa exigência, registro de nome próprio em maiúsculas entra como se fosse
# nome de tipo -- foi o que aconteceu com WORD_SWAPS ("DANG") e com um
# BIOME_GROUP chamado "NONE".
RE_NOME_TIPO = re.compile(r"^([A-Z][A-Z0-9_]*[A-Z_])(\d+)$")


def por_nome(arquivos):
    """typecode -> nome de tipo sugerido pelos NOMES dos registros.

    Terceiro canal, independente dos outros dois: o jogo nomeia registro sem
    nome próprio como "<TIPO><numero>" (DIALOGUE_LINE6071, DIALOG_ACTION4205).
    É o único jeito de nomear tipo que nem existe no fcs.def.
    """
    palpite = defaultdict(Counter)
    for c in arquivos:
        if not os.path.exists(c):
            continue
        for rec in km.ler(c)["records"]:
            m = RE_NOME_TIPO.match(km.t(rec["name"]).strip())
            if m:
                palpite[rec["typecode"]][m.group(1)] += 1
    saida = {}
    for tc, contagem in palpite.items():
        nome, n = contagem.most_common(1)[0]
        if n >= 3:      # um nome solto não sustenta nada
            saida[tc] = (nome, n)
    return saida


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
    # Canal independente: para onde as referências reais apontam.
    alvos_por_campo = campos_de_referencia(tipos=tipos)
    por_ref = por_referencia(caminhos.arquivos_base(), alvos_por_campo)
    print(f"canal de referência: {len(alvos_por_campo)} campos com tipo de alvo "
          f"declarado no fcs.def, deduziram {len(por_ref)} typecodes\n")
    nomes = por_nome(caminhos.arquivos_base())
    print(f"canal de nomes: {len(nomes)} typecodes com nome de tipo embutido "
          f"no nome dos registros\n")
    for linha in linhas:
        tc = linha[0]
        tipo_ref = por_ref[tc][0] if tc in por_ref else None
        tipo_nome = nomes[tc][0] if tc in nomes else None
        rotulo = []
        if tipo_ref:
            rotulo.append(f"ref: {tipo_ref} ({por_ref[tc][1]})")
        if tipo_nome:
            rotulo.append(f"nome: {tipo_nome}")
        linha.append(" | ".join(rotulo))
        # O canal de nomes é o único que alcança tipo ausente do fcs.def, então
        # ele ganha -- mas nunca contra os outros dois já concordando entre si.
        concordam = tipo_ref and tipo_ref == linha[1]
        if tipo_nome and tipo_nome not in tipos and not concordam:
            linha[1] = tipo_nome
            linha[2] = "POR NOME"
        elif tipo_ref and tipo_ref == linha[1]:
            linha[2] = "CONFIRMADO"      # dois métodos independentes concordam
        elif tipo_ref:
            linha[2] = "CONFLITO"

    # "duplicado" e o unico estado que significa DESCONHECIDO: outro typecode
    # reivindica melhor aquele tipo, entao o tipo real deste nao esta no
    # fcs.def. Recall alto sem confirmacao por referencia e "provavel", nao
    # ambiguo -- so quer dizer que ninguem aponta refs para aquele tipo.
    provaveis = []
    for linha in linhas:
        tc, conf, recall = linha[0], linha[2], linha[3]
        if conf in ("exato", "CONFIRMADO", "POR NOME"):
            resolvidos.append(tc)
        elif conf == "duplicado":
            ambiguos.append(tc)
        elif recall >= 0.9:
            linha[2] = "provavel"
            provaveis.append(tc)
        else:
            ambiguos.append(tc)

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

    if "--refs" in argv:
        alvo_tc = int(argv[argv.index("--refs") + 1])
        print(f"quais campos apontam para registros de typecode {alvo_tc}:")
        tipo_de, contagem = {}, Counter()
        mods = [km.ler(c) for c in caminhos.arquivos_base() if os.path.exists(c)]
        for mod in mods:
            for rec in mod["records"]:
                tipo_de[rec["strid"]] = rec["typecode"]
        for mod in mods:
            for rec in mod["records"]:
                for cat, items in rec["extra"]:
                    for a, *_ in items:
                        if tipo_de.get(a) == alvo_tc:
                            contagem[normalizar(km.t(cat))] += 1
        for campo, n in contagem.most_common(12):
            declara = alvos_por_campo.get(campo, "(sem tipo declarado no fcs.def)")
            print(f"  {n:>7} refs  campo {campo!r}  -> fcs.def declara: {declara}")
        return 0

    if "--ambiguos" in argv:
        linhas = [l for l in linhas if l[0] in ambiguos]

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write("# Mapa de typecodes\n\n")
        f.write("Gerado por `python typecodes.py`. Dois métodos independentes:\n\n")
        f.write("1. **campos** — casa o conjunto de campos dos registros de "
                "`data/` com as seções do `fcs.def`. `recall` é a fração dos "
                "campos vistos que o tipo explica.\n")
        f.write("2. **referências** — o `fcs.def` diz qual tipo cada campo de "
                "referência aponta (`clothing: ARMOUR`); seguindo as refs reais "
                "até o typecode do registro apontado, o tipo sai sem depender "
                "do método 1.\n\n")
        f.write("`CONFIRMADO` = os dois métodos concordam. `exato` = recall 100% "
                "sem empate, mas sem confirmação por referência. `duplicado` = "
                "outro typecode casa melhor com esse mesmo tipo, logo o tipo real "
                "deste provavelmente não está no `fcs.def`.\n\n")
        f.write("| typecode | tipo | confiança | recall | por referência | "
                "registros | exemplo |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for tc, nome, conf, rec, _pre, n, _nc, ex, alt, ref in linhas:
            nome_txt = nome if not alt else f"{nome} *(ou {alt})*"
            f.write(f"| {tc} | `{nome_txt}` | {conf} | {rec:.0%} | {ref or '—'} | "
                    f"{n} | {ex[:40]} |\n")
    print(f"gravado: {SAIDA}\n")

    print(f"{'tc':>5} {'tipo (fcs.def)':<28} {'conf':<11} {'recall':>6} "
          f"{'regs':>7}  por referência / alternativas")
    for tc, nome, conf, rec, _pre, n, _nc, ex, alt, ref in linhas:
        extra = f"   [ref: {ref}]" if ref else (f"   [empata: {alt}]" if alt else "")
        print(f"{tc:>5} {nome:<28} {conf:<11} {rec:>6.0%} {n:>7}  {extra}")
    print(f"\nde {len(campos)} typecodes vistos: {len(resolvidos)} com certeza, "
          f"{len(provaveis)} provaveis (recall >= 90%, sem refs que confirmem), "
          f"{len(ambiguos)} desconhecidos")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
