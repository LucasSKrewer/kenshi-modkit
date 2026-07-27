"""Gera um mod de teste 100% por script, pra provar in-game que o jogo aceita
arquivo escrito por este modkit (e nao apenas que o binario esta coerente).

Deriva do KenshiCoop.mod e faz tres coisas de propositos diferentes:
  1. renomeia o namespace dos ids  -> testa reescrita de referencia em massa
  2. altera valores de um registro -> testa EDICAO
  3. clona o game start num registro novo -> testa CRIACAO de registro
     (clonar herda o typecode do original, entao nao precisa do mapa de
     typecodes, que ainda nao levantei)

Sinal esperado no jogo: na tela de novo jogo aparecem DOIS starts marcados
"[MODKIT]", um com 7777 gatos e outro com 3333. Se os dois aparecerem,
edicao e criacao funcionam.

    python teste_ingame.py              (gera em out/, nao toca no jogo)
    python teste_ingame.py --instalar   (copia pra pasta mods\\ do Kenshi)
"""
import os
import shutil
import sys

import caminhos as loc
import kenshimod as km
import validar

# Deriva do KenshiCoop.mod porque ele é pequeno e de conteúdo conhecido. Troque
# por qualquer .mod instalado (ou passe outro caminho no argv) se não tiver esse.
ORIGEM_PADRAO = os.path.join("KenshiCoop", "KenshiCoop.mod")
NOME = "ModkitTeste"
NS_ANTIGO = "-KenshiCoop-MultiplayerStart.mod"
NS_NOVO = f"-{NOME}.mod"
TYPECODE_GAME_START = 64


def gerar(origem=None):
    origem = origem or os.path.join(loc.mods_dir(), ORIGEM_PADRAO)
    if not os.path.exists(origem):
        raise SystemExit(f"nao achei o mod de origem: {origem}\n"
                         f"passe outro: python teste_ingame.py <caminho.mod>")
    mod = km.ler(origem)
    print(f"origem: {os.path.basename(origem)}, {len(mod['records'])} registros")

    n = km.substituir_em_ids(mod, NS_ANTIGO, NS_NOVO)
    print(f"1. namespace de ids reescrito em {n} lugares -> *{NS_NOVO}")

    mod["author"] = km.b("kenshi-modkit (gerado por script)")
    mod["description"] = km.b(
        "Mod de TESTE gerado por script, sem abrir o FCS. Serve so pra "
        "confirmar que o Kenshi carrega arquivo escrito pelo modkit. "
        "Nao usar pra jogar de verdade.")

    starts = [r for r in mod["records"] if r["typecode"] == TYPECODE_GAME_START]
    if len(starts) != 1:
        raise SystemExit(f"esperava 1 game start, achei {len(starts)}")
    start = starts[0]

    start["name"] = km.b("[MODKIT] editado por script")
    if not km.set_campo(start, "long", "money", 7777):
        raise SystemExit("campo 'money' nao existe nesse registro")
    km.set_campo(start, "string", "description",
                 "Start EDITADO por script: dinheiro trocado de 1000 para 7777. "
                 "Se voce esta lendo isso no jogo, a edicao funcionou.")
    print(f"2. registro editado: {km.t(start['name'])}, money -> 7777")

    num = km.proximo_id_livre(mod, f"{NOME}.mod")
    clone = km.clonar_registro(start, f"{num}-{NOME}.mod",
                               "[MODKIT] criado por script (clone)")
    clone["id"] = num          # registros novos de um mod usam id sequencial
    km.set_campo(clone, "long", "money", 3333)
    km.set_campo(clone, "string", "description",
                 "Start CRIADO por script (clone do anterior, 3333 gatos). "
                 "Se este aparece na lista, criar registro funciona.")
    mod["records"].append(clone)
    print(f"3. registro criado: {km.t(clone['name'])} (id {num}-{NOME}.mod)")

    destino_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", NOME)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, f"{NOME}.mod")
    tam = km.gravar(destino, mod)
    print(f"\ngravado: {destino} ({tam} bytes, {len(mod['records'])} registros)")

    # o arquivo tem que reler estavel antes de qualquer teste no jogo
    relido = km.ler(destino)
    if km.serializar(relido) != open(destino, "rb").read():
        raise SystemExit("ERRO: reserializacao do gerado nao e estavel")
    print("reparse estavel: ok")
    return destino


def instalar(origem):
    destino_dir = os.path.join(loc.mods_dir(), NOME)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, f"{NOME}.mod")
    shutil.copy2(origem, destino)
    print(f"\ninstalado em: {destino}")
    print("O mod aparece desativado na lista do launcher; e preciso marcar.")
    return destino


if __name__ == "__main__":
    passados = [a for a in sys.argv[1:] if not a.startswith("--")]
    arquivo = gerar(passados[0] if passados else None)
    print("\n--- validacao contra a ordem de load ---")
    idx = validar.indexar(loc.arquivos_base())
    if validar.validar(arquivo, idx):
        raise SystemExit("validacao falhou; nao instalando")
    if "--instalar" in sys.argv:
        instalar(arquivo)
    else:
        print("\n(rode com --instalar pra copiar pra pasta mods do Kenshi)")
