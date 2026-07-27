"""Teste de fidelidade: le e regrava cada arquivo, exigindo bytes identicos.

E o unico teste que importa antes de confiar o parser a um mod de verdade:
se a regravacao nao bate byte a byte, alguma coisa nao foi entendida.

    python roundtrip.py "<Kenshi>/data/*.mod"
    python roundtrip.py --tudo        (mods + workshop + dados base do jogo)

O caminho da instalação é detectado (ver caminhos.py); não precisa editar nada.
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
