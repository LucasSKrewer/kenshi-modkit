"""Recomenda uma ordem de load para os mods instalados, com o motivo de cada
posição -- e aponta mod que está instalado sem fazer efeito.

Duas descobertas guiam a recomendação:

1. **Mod embutido em outro.** Um overhaul grande costuma trazer mods de
   terceiros já mesclados dentro dele. Dá para detectar: os registros que ele
   mesclou mantêm o `strid` com o sufixo do mod de origem
   (`2149-BackpacksExpanded.mod` dentro do Genesis). Se o overhaul já contém
   os registros daquele mod, rodar o mod separado é redundante -- e, dependendo
   da ordem, sobrescreve a versão ajustada do overhaul.

2. **Escopo.** Quem toca muitos registros deve carregar ANTES de quem toca
   poucos, senão o grande apaga o ajuste fino do pequeno. No Kenshi, o último
   da lista ganha.

    python ordem.py                 (relatório)
    python ordem.py --aplicar       (escreve o mods.cfg, com backup)
"""
import os
import shutil
import sys
from collections import Counter

import caminhos as loc
import conflitos
import kenshimod as km


def perfil(caminho):
    """resumo do que um mod faz: quantos registros, e de que origem eles são"""
    mod = km.ler(caminho)
    nome = os.path.basename(caminho)
    sufixos = Counter()
    for rec in mod["records"]:
        m = km.RE_ID.match(rec["strid"])
        if m:
            sufixos[km.t(m.group(2))] += 1
    return {
        "arquivo": nome,
        "caminho": caminho,
        "registros": len(mod["records"]),
        "recs": {rec["strid"]: rec for rec in mod["records"]},
        "strids": {rec["strid"] for rec in mod["records"]},
        "sufixos": sufixos,
        "deps": {d.strip() for d in km.t(mod["dependencies"]).split(",") if d.strip()},
    }


def sobreposicoes(perfis):
    """mod -> (mod maior, registros em comum, quantos com VALOR igual)

    Strid em comum não basta para dizer "redundante": o maior pode tocar o mesmo
    registro com outro valor, e aí é conflito, não redundância -- a ordem decide
    quem ganha. Só comparando os valores dá para separar as duas coisas.
    """
    saida = {}
    for p in perfis:
        if not p["registros"]:
            continue
        for maior in perfis:
            if maior is p or maior["registros"] < p["registros"] * 2:
                continue
            comuns = p["strids"] & maior["strids"]
            if len(comuns) / p["registros"] < 0.8:
                continue
            iguais = sum(1 for s in comuns
                         if conflitos.valores(p["recs"][s])
                         == conflitos.valores(maior["recs"][s]))
            saida[p["arquivo"]] = (maior["arquivo"], len(comuns), iguais)
            break
    return saida


def recomendar(perfis, redundantes):
    """ordena: maior escopo primeiro, tweaks por último; redundantes fora"""
    ativos = [p for p in perfis if p["arquivo"] not in redundantes]
    ativos.sort(key=lambda p: -p["registros"])
    return ativos


def main(argv):
    caminhos_mods = conflitos.todos_instalados()
    print(f"{len(caminhos_mods)} mods instalados\n")
    perfis = []
    for c in caminhos_mods:
        try:
            perfis.append(perfil(c))
        except Exception as e:
            print(f"  aviso: nao li {os.path.basename(c)}: {e}")

    sobrepostos = sobreposicoes(perfis)
    redundantes, disputados = {}, {}
    for mod, (maior, comuns, iguais) in sobrepostos.items():
        (redundantes if iguais / comuns >= 0.9 else disputados)[mod] = \
            (maior, comuns, iguais)

    if redundantes:
        print("REDUNDANTES -- mesmo conteudo, valores IGUAIS, ja vem no outro:")
        for mod, (maior, comuns, iguais) in sorted(redundantes.items()):
            print(f"  {mod:<38} {iguais}/{comuns} registros identicos aos de {maior}")
        print("  (pode desmarcar: nao muda nada no jogo)\n")

    if disputados:
        print("DISPUTA REAL -- mesmo registro, valor DIFERENTE, a ordem decide:")
        for mod, (maior, comuns, iguais) in sorted(disputados.items()):
            print(f"  {mod:<38} {comuns - iguais} de {comuns} registros diferem "
                  f"de {maior}")
        print("  (nao sao redundantes: quem carregar depois manda. Decida caso "
              "a caso)\n")

    ordem = recomendar(perfis, redundantes)
    print("ORDEM RECOMENDADA (o ultimo da lista sobrescreve os anteriores):")
    for i, p in enumerate(ordem, 1):
        if not p["registros"]:
            papel = "sem registros (UI/textura): a posicao nao importa"
        elif p["registros"] > 5000:
            papel = "overhaul: base de tudo, tem que vir primeiro"
        elif p["registros"] > 300:
            papel = "conteudo amplo"
        elif p["registros"] > 40:
            papel = "conteudo pontual"
        else:
            papel = "tweak: precisa vir depois pra valer"
        nota = ""
        if p["arquivo"] in disputados:
            nota = f"  <- disputa com {disputados[p['arquivo']][0]}"
        print(f"  {i:>2}. {p['arquivo']:<38} {p['registros']:>6} regs  "
              f"{papel}{nota}")

    faltando = set()
    for p in ordem:
        for d in p["deps"]:
            if d.endswith(".mod") and d not in {q["arquivo"] for q in perfis} \
                    and d not in {"rebirth.mod", "Newwworld.mod", "Dialogue.mod"}:
                faltando.add((p["arquivo"], d))
    if faltando:
        print("\nDEPENDENCIA DECLARADA QUE NAO ESTA INSTALADA:")
        for mod, dep in sorted(faltando):
            print(f"  {mod} depende de {dep}")

    if "--aplicar" in argv:
        destino = loc.mods_cfg()
        if os.path.exists(destino):
            backup = destino + ".bak"
            shutil.copy2(destino, backup)
            print(f"\nbackup do anterior: {backup}")
        with open(destino, "w", encoding="utf-8") as f:
            for p in ordem:
                f.write(p["arquivo"] + "\n")
        print(f"escrito: {destino} com {len(ordem)} mods")
        print("Confira no launcher antes de carregar um save antigo.")
    else:
        print("\n(rode com --aplicar pra escrever isso no mods.cfg, com backup)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
