"""Mostra quais mods brigam pelo mesmo registro, e qual valor ganha.

O launcher do Kenshi não conta isso: ele só ordena. Quando dois mods alteram o
mesmo registro, o que vem depois na ordem de load sobrescreve — silenciosamente,
campo por campo. Com Genesis instalado (que toca 26 mil registros) isso deixa de
ser detalhe.

Sobrescrever não é necessariamente problema: dois mods podem mexer em campos
diferentes do mesmo registro e conviver. Conflito de verdade é quando mexem no
MESMO campo com valores diferentes -- é o que a saída separa.

    python conflitos.py                (ordem real, lida do data/mods.cfg)
    python conflitos.py --todos        (e se eu ativasse todos os instalados?)
    python conflitos.py --campos       (mostra campo a campo cada conflito)
    python conflitos.py --strid "997-gamedata.base"    (investiga um registro)
"""
import glob
import os
import sys
from collections import Counter, defaultdict

import caminhos as loc
import kenshimod as km


def achar_mod(nome):
    """acha o .mod pelo nome, na pasta mods/ ou no workshop"""
    candidatos = [os.path.join(loc.mods_dir(), os.path.splitext(nome)[0], nome)]
    workshop = loc.workshop_dir()
    if workshop:
        candidatos += glob.glob(os.path.join(workshop, "**", nome), recursive=True)
    for c in candidatos:
        if os.path.exists(c):
            return c
    return None


def ordem_real():
    """a ordem de load de verdade, do data/mods.cfg"""
    if not os.path.exists(loc.mods_cfg()):
        return []
    with open(loc.mods_cfg(), "r", encoding="utf-8", errors="replace") as f:
        nomes = [l.strip() for l in f if l.strip()]
    fora = [n for n in nomes if not achar_mod(n)]
    if fora:
        print(f"  aviso: no mods.cfg mas não achei o arquivo: {fora}")
    return [c for c in (achar_mod(n) for n in nomes) if c]


def todos_instalados():
    """todos os mods instalados, ordem alfabética (a real depende do mods.cfg)"""
    achados = glob.glob(os.path.join(loc.mods_dir(), "**", "*.mod"), recursive=True)
    workshop = loc.workshop_dir()
    if workshop:
        achados += glob.glob(os.path.join(workshop, "**", "*.mod"), recursive=True)
    return sorted(set(achados), key=lambda p: os.path.basename(p).lower())


def indexar_base():
    """strid -> arquivo, para saber o que é registro da base"""
    idx = {}
    for caminho in loc.arquivos_base():
        if os.path.exists(caminho):
            for rec in km.ler(caminho)["records"]:
                idx[rec["strid"]] = os.path.basename(caminho)
    return idx


def valores(rec):
    """campo -> valor, achatando as seções tipadas e as referências"""
    saida = {}
    for secao, _, _ in km.SECOES:
        for k, v in rec[secao]:
            saida[f"{km.t(k)}"] = km.t(v) if isinstance(v, bytes) else v
    for cat, items in rec["extra"]:
        saida[f"{km.t(cat)} (refs)"] = [km.t(n) for n, *_ in items]
    return saida


def analisar(arquivos, base_idx):
    """strid -> [(nome do mod, registro)] na ordem de load"""
    tocados = defaultdict(list)
    for caminho in arquivos:
        nome = os.path.basename(caminho)
        try:
            mod = km.ler(caminho)
        except Exception as e:
            print(f"  aviso: não li {nome}: {e}")
            continue
        for rec in mod["records"]:
            tocados[rec["strid"]].append((nome, rec))
    return tocados


def main(argv):
    base_idx = indexar_base()
    print(f"base indexada: {len(base_idx)} registros")

    if "--todos" in argv:
        caminhos = todos_instalados()
        print(f"modo --todos: {len(caminhos)} mods instalados, em ordem "
              f"alfabética (a ordem real depende do mods.cfg, então o "
              f"'ganha' abaixo é hipotético)")
    else:
        caminhos = ordem_real()
        print(f"ordem real do mods.cfg: {len(caminhos)} mod(s) ativo(s)")
        if len(caminhos) < 2:
            print("  (menos de 2 mods ativos: nada pode conflitar. Use --todos "
                  "para ver o que aconteceria com todos os instalados.)")
    if not caminhos:
        return 0
    for i, c in enumerate(caminhos, 1):
        print(f"  {i:>2}. {os.path.basename(c)}")

    tocados = analisar(caminhos, base_idx)
    disputados = {s: v for s, v in tocados.items() if len(v) > 1}
    print(f"\n{len(tocados)} registros tocados, {len(disputados)} por 2+ mods")

    if "--strid" in argv:
        alvo = km.b(argv[argv.index("--strid") + 1])
        if alvo not in tocados:
            print(f"nenhum mod ativo toca {km.t(alvo)}")
            return 0
        print(f"\n=== {km.t(alvo)} "
              f"(base: {base_idx.get(alvo, 'não é da base')})")
        for nome, rec in tocados[alvo]:
            print(f"\n-- {nome}: {km.t(rec['name'])}")
            for k, v in sorted(valores(rec).items()):
                print(f"     {k:<28} = {v!r}")
        return 0

    # campo a campo: mesmo campo, valores diferentes = conflito de verdade
    conflitos_campo = []
    for strid, lista in disputados.items():
        acumulado = {}
        for nome, rec in lista:
            for k, v in valores(rec).items():
                if k in acumulado and acumulado[k][1] != v:
                    conflitos_campo.append((strid, k, acumulado[k], (nome, v)))
                acumulado[k] = (nome, v)

    pares = Counter()
    for strid, lista in disputados.items():
        nomes = sorted({n for n, _ in lista})
        for i in range(len(nomes)):
            for j in range(i + 1, len(nomes)):
                pares[(nomes[i], nomes[j])] += 1

    print(f"{len(conflitos_campo)} conflitos de campo (mesmo campo, valor diferente)\n")
    if pares:
        print("mods que se sobrepõem (quantidade de registros em comum):")
        for (a, b_), n in pares.most_common(15):
            print(f"  {n:>6}  {a}  x  {b_}")

    if conflitos_campo:
        limite = len(conflitos_campo) if "--campos" in argv else 15
        print(f"\nconflitos de campo (mostrando {min(limite, len(conflitos_campo))} "
              f"de {len(conflitos_campo)}; o último da ordem ganha):")
        for strid, campo, (mod_a, val_a), (mod_b, val_b) in conflitos_campo[:limite]:
            print(f"  {km.t(strid)}  campo {campo!r}")
            print(f"      {mod_a} = {str(val_a)[:60]}")
            print(f"      {mod_b} = {str(val_b)[:60]}   <- ganha")
        if not "--campos" in argv and len(conflitos_campo) > limite:
            print(f"  ... use --campos para ver todos os {len(conflitos_campo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
