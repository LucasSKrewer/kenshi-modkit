"""Teste de fidelidade: le e regrava cada arquivo, exigindo bytes identicos.

E o unico teste que importa antes de confiar o parser a um mod de verdade:
se a regravacao nao bate byte a byte, alguma coisa nao foi entendida.

    python roundtrip.py "<Kenshi>/data/*.mod"
    python roundtrip.py --tudo        (mods + workshop + dados base do jogo)
    python roundtrip.py --saves       (amostra dos saves: .save, .zone, .platoon)
    python roundtrip.py --saves-tudo  (TODOS os saves; sao dezenas de milhares)

O caminho da instalação é detectado (ver caminhos.py); não precisa editar nada.
Nada aqui grava: só lê, regrava em memória e compara.
"""
import glob
import os
import sys

import caminhos
import kenshimod as km


def padroes_tudo():
    padroes = [
        os.path.join(caminhos.data_dir(), "*.base"),
        os.path.join(caminhos.data_dir(), "*.mod"),
        os.path.join(caminhos.mods_dir(), "**", "*.mod"),
    ]
    workshop = caminhos.workshop_dir()
    if workshop:
        padroes.append(os.path.join(workshop, "**", "*.mod"))
    return padroes


def arquivos_de_save(amostra=None):
    """os saves: .save, .zone e .platoon. São dezenas de milhares, então por
    padrão pega uma amostra espalhada (os maiores de cada tipo + fatia regular),
    que é o que dá cobertura sem levar meia hora."""
    raiz = os.path.join(caminhos.kenshi_dir(), "save")
    if not os.path.isdir(raiz):
        return []
    saida = []
    for ext in ("save", "zone", "platoon"):
        achados = glob.glob(os.path.join(raiz, "**", f"*.{ext}"), recursive=True)
        achados.sort(key=os.path.getsize, reverse=True)
        if amostra is None or len(achados) <= amostra:
            saida += achados
            continue
        # os 10 maiores (mais chance de exercitar caso raro) + fatia regular
        passo = max(1, len(achados) // (amostra - 10))
        saida += achados[:10] + achados[10::passo][:amostra - 10]
    return saida


def primeira_diferenca(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b)) if len(a) != len(b) else None


def checar(caminho):
    with open(caminho, "rb") as f:
        data = f.read()
    try:
        mod = km.desserializar(data)
    except Exception as e:
        return False, f"FALHOU LER {len(data):>10} B  {caminho}\n    {e}"
    saida = km.serializar(mod)
    d = primeira_diferenca(data, saida)
    resumo = (f"{len(data):>10} B  ft{mod['filetype']}  "
              f"recs={len(mod['records']):<6}  {os.path.basename(caminho)}")
    if d is None:
        return True, f"OK   {resumo}"
    return False, (f"DIFERE em {d:#x}  {resumo}\n"
                   f"    orig: {data[d:d + 16].hex(' ')}\n"
                   f"    novo: {saida[d:d + 16].hex(' ')}")


def main(argv):
    if argv and argv[0] in ("--saves", "--saves-tudo"):
        arquivos = arquivos_de_save(None if argv[0] == "--saves-tudo" else 120)
        arquivos = sorted(set(arquivos), key=os.path.getsize)
        print(f"{len(arquivos)} arquivo(s) de save"
              f"{'' if argv[0] == '--saves-tudo' else ' (amostra)'}")
    else:
        padroes = padroes_tudo() if (not argv or argv[0] == "--tudo") else argv
        arquivos = []
        for p in padroes:
            arquivos += glob.glob(p, recursive=True)
        arquivos = sorted(set(arquivos), key=os.path.getsize)
    if not arquivos:
        print("nenhum arquivo encontrado")
        return 1
    ok = 0
    for c in arquivos:
        passou, linha = checar(c)
        print(linha)
        ok += passou
    print(f"\n{ok}/{len(arquivos)} round-trip byte-identico")
    return 0 if ok == len(arquivos) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
